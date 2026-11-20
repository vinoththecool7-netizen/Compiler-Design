"""Reproduce code generation and optimization experiments."""
import json
from pathlib import Path
from backend import *
import strict

LOOP=[('=',0,None,'s'),('=',0,None,'i'),('ge','i','n',10),('*',4,'i','t1'),
      ('load','a','t1','t2'),('le','t2',0,8),('+','s','t2','t3'),('=','t3',None,'s'),
      ('+','i',1,'i'),('j',None,None,2),('/','s','n','avg')]
BLOCK=[('-','a','b','t1'),('-','a','c','t2'),('+','t1','t2','t3'),('+','t3','t2','d')]
REDEF=[('+','i',1,'i'),('*','i',2,'out')]
SINGLE=[('=',7,None,'out')]
BRANCH=[('le','x',0,3),('=',3,None,'z'),('j',None,None,4),('=',3,None,'z'),
        ('+','z',2,'out')]
DAG1=[('+','b','c','a'),('-','a','d','b'),('+','b','c','c'),('-','a','d','d')]
DAG2=[('*','x',1,'t1'),('+','t1',0,'t2'),('*',2,'y','t3'),('*','x',1,'t4'),('+','t2','t4','z')]
LOW=[('+','a','b','p'),('+','p',1,'q'),('+','q',1,'r'),('+','r',1,'out')]
HIGH=[('+','a','b','p'),('+','c','d','q'),('+','p','q','r'),('+','r','p','out')]
REORDERED=[('+','a','b','p'),('+','p','c','q'),('+','q','d','r'),('+','r','p','out')]

def local(q):
    code=list(q);effort=0
    for a,b in cfg(q)[0]:
        ids={}; reps=defaultdict(set); nodes={}; serial=0
        def value(x):
            nonlocal serial
            if x not in ids:
                serial+=1;ids[x]=serial
                if var(x):reps[serial].add(x)
            return ids[x]
        for i in range(a,b):
            o,x,y,d=q[i];effort+=1
            if o not in {*OPS,'='}:
                # A load redefines its destination even though we do not
                # value-number the memory read or eliminate its effects.
                if data(q[i])[0] and d in ids:
                    reps[ids[d]].discard(d);del ids[d]
                continue
            if o in {'+','-','*'} and ((o=='*' and y==1) or (o in '+-' and y==0)):
                o,y='=',None
            elif o=='*' and x==1:o,x,y='=',y,None
            if o in OPS and isinstance(x,int) and isinstance(y,int) and (o!='/' or y):
                o,x,y='=',OPS[o](x,y),None
            if o=='*' and x==2:o,x,y='+',y,y
            if o=='*' and y==2:o,y='+',x
            if o=='=':v=value(x)
            else:
                key=o,value(x),value(y)
                if o in ('+','*'):key=(o,*sorted(key[1:]))
                if key not in nodes:serial+=1;nodes[key]=serial
                v=nodes[key]
                if reps[v]:o,x,y='=',min(reps[v]),None
            if d in ids:reps[ids[d]].discard(d)
            ids[d]=v;reps[v].add(d)
            code[i]=(o,x,y,d)
    return code,effort

def global_opt(q,outputs):
    q=list(q);I,_,_,effort,_=analyze(q,'rd','flow')
    blocks,succ,pred=cfg(q)
    # A reaching definition alone does not rule out an incoming initial value.
    # Compute names defined on every reachable entry path before using RD facts.
    reachable=set(); todo=[0] if blocks else []
    while todo:
        j=todo.pop()
        if j not in reachable:
            reachable.add(j);todo.extend(succ[j])
    universe={data(s)[0] for s in q if data(s)[0] is not None}
    gen=[{data(q[i])[0] for i in range(a,b)}-{None} for a,b in blocks]
    must_in=[set(universe) for _ in blocks]; must_out=[set(universe) for _ in blocks]
    changed=True
    while changed:
        changed=False
        for j in sorted(reachable):
            incoming=[must_out[p] for p in pred[j] if p in reachable]
            new_in=set() if j==0 or not incoming else set.intersection(*incoming)
            new_out=new_in|gen[j]
            if new_in!=must_in[j] or new_out!=must_out[j]:
                must_in[j],must_out[j]=new_in,new_out;changed=True
            effort+=1+len(incoming)
    for j,(a,b) in enumerate(blocks):
        reach=I[j]
        defined=set(must_in[j]) if j in reachable else set()
        for i in range(a,b):
            o,x,y,d=q[i]
            def constant(v):
                if not var(v):return v
                defs=[(d,o,x) for k,(o,x,_,d) in enumerate(q) if reach>>k&1 and data(q[k])[0]==v]
                if v not in defined:return v
                if defs and len({x for _,o,x in defs if o=='=' and type(x)==int})==1 and all(o=='=' and type(x)==int for _,o,x in defs):
                    return defs[0][2]
                return v
            if o in {*OPS,'=','le','ge','eq'}:q[i]=(o,constant(x),constant(y),d)
            if data(q[i])[0]:
                reach&=~sum(1<<k for k,s in enumerate(q) if data(s)[0]==d)
                reach|=1<<i;defined.add(d)
            effort+=1
    q,n=local(q);effort+=n
    _,out,_,ops,bits=analyze(q,'live','flow',outputs);effort+=ops
    for j,(a,b) in enumerate(cfg(q)[0]):
        live={x for x,v in bits.items() if out[j]&v}
        for i in range(b-1,a-1,-1):
            d,uses=data(q[i]);effort+=1
            if d and d not in live and q[i][0] in ('=','+','-','*'):
                q[i]=('nop',None,None,None)
            else:
                if d:live.discard(d)
                live.update(uses)
    return q,effort

def peephole(machine):
    targets={s[-1] for s in machine if s[0] in ('J','B')}
    discard=set()
    for i,(a,b) in enumerate(zip(machine,machine[1:])):
        if a[0]=='ST' and b[0]=='LD' and a[1:]==b[1:][::-1] and i+1 not in targets:
            discard.add(i+1)
    mapping={i:i-sum(k<i for k in discard) for i in range(len(machine))}
    return [(*s[:-1],mapping[s[-1]]) if s[0] in ('J','B') else s for i,s in enumerate(machine) if i not in discard]

def nested(depth):
    q=[]
    def loop(i):
        key=f'i{i}'
        q.append(('=',0,None,key)); start=len(q)
        q.append(('ge',key,2,None))
        if i+1<depth:loop(i+1)
        else:q.append(('+','out',1,'out'))
        q.append(('+',key,1,key));q.append(('j',None,None,start))
        q[start]=('ge',key,2,len(q))
    q.append(('=',0,None,'out'));loop(0);q.append(('=','out',None,'result'))
    return q

def main():
    cases={'positive_marks':(LOOP,{'a':[2,-5,10,4],'n':4},'avg',4),
           'register_block':(BLOCK,{'a':9,'b':3,'c':2},'d',20),
           'redefinition':(REDEF,{'i':3},'out',8),'single':(SINGLE,{},'out',7)}
    alloc=[]
    for name,(q,env,result,want) in cases.items():
        assert run(q,env)[0][result]==want
        for k in (2,3,4,8):
            for v in ('first','next'):
                m,stats=generate(q,k,v,[result]);r,steps=run(m,env,True)
                assert r[result]==want,(name,k,v,m,r)
                sm=strict.lower(m,k);sr,ss=strict.run(sm,env);assert sr[result]==want
                strictstats=dict(instructions=len(sm),loads=sum(s[0]=='LD' and s[2][0] in ('mem','indexed') for s in sm),
                    stores=sum(s[0]=='ST' for s in sm),spills=stats['spills']+sum(s[0]=='ST' and s[1]==strict.SCRATCH for s in sm),
                    cost=strict.cost(sm),steps=ss,machine=sm)
                alloc.append(dict(case=name,k=k,policy=v,**stats,steps=steps,machine=m,strict=strictstats))
    adversarial=[]
    for q in (LOW,HIGH,REORDERED):
        m,s=generate(q,2,'next',['out']);f=nextuse(q,0,len(q),['out'])
        before=[(set(f[i])-{data(q[i])[0]})|set(data(q[i])[1]) for i in range(len(q))]
        sm=strict.lower(m,2);env=dict(a=2,b=3,c=4,d=5)
        strictstats=dict(instructions=len(sm),loads=sum(s[0]=='LD' and s[2][0] in ('mem','indexed') for s in sm),
            stores=sum(s[0]=='ST' for s in sm),spills=s['spills']+sum(t[0]=='ST' and t[1]==strict.SCRATCH for t in sm),
            cost=strict.cost(sm),steps=strict.run(sm,env)[1])
        assert strict.run(sm,env)[0]['out']==run(q,env)[0]['out']
        adversarial.append(dict(**s,strict=strictstats,peak_live=max([len(x) for x in f.values()]+[len(x) for x in before]),
                                tac=q,machine=m,value=run(m,env,True)[0]['out']))
    assert adversarial[1]['value']==adversarial[2]['value']==19
    small=[]
    for name,q,input_sets,out in [('straight',REDEF,[{'i':1},{'i':4}],'out'),
        ('branch',BRANCH,[{'x':-1},{'x':4}],'out'),
        ('loop',LOOP,[{'a':[2,-2,5],'n':3},{'a':[1,3],'n':2}],'avg')]:
        facts={}
        for mode in ('rd','live'):
            v=analyze(q,mode,'linear',[out]);w=analyze(q,mode,'flow',[out]);assert v[:2]==w[:2]
            facts[mode]=[v[0],v[1],v[4],v[2]]
        r,effort=global_opt(q,[out]); vals=[]
        for env in input_sets:
            want=run(q,env)[0][out];got=run(r,env)[0][out]
            assert got==want;vals.append(got)
        small.append(dict(case=name,facts=facts,optimized=r,values=vals,effort=effort))
    # Same constant on both paths can cross a join; an input on one path cannot.
    propagated,_=global_opt(BRANCH,['out'])
    assert propagated[-1]==('=',5,None,'out'),propagated
    partial=[('le','x',0,3),('=',3,None,'z'),('j',None,None,4),
             ('=',0,None,'unused'),('+','z',2,'out')]
    safe,_=global_opt(partial,['out'])
    for env in ({'x':-1,'z':9},{'x':1,'z':9}):
        assert run(partial,env)[0]['out']==run(safe,env)[0]['out']
    terminal=[('=',3,None,'out'),('eq','x',0,0)]
    optimized,_=global_opt(terminal,['out'])
    for code in (terminal,optimized):
        machine,_=generate(code,2,'next',['out'])
        assert run(code,{'x':1})[0]['out']==3
        assert run(machine,{'x':1},True)[0]['out']==3
    loaded=[('+','x',1,'a'),('load','xs',0,'x'),('+','x',1,'out')]
    for optimized in (local(loaded)[0],global_opt(loaded,['out'])[0]):
        assert run(optimized,{'x':2,'xs':[5]})[0]['out']==6
    end_target=[('eq','x',1,2),('=',4,None,'out'),('=',9,None,'dead')]
    optimized,_=global_opt(end_target,['out'])
    m,_=generate(optimized,2,'next',['out'])
    lowered=strict.lower(m,2)
    for env in ({'x':0},{'x':1,'out':8}):
        assert strict.run(lowered,env)[0]['out']==run(end_target,env)[0]['out']
    growth=[]
    for depth in (1,2,4,8,16,32,64):
        q=nested(depth)
        rec={'depth':depth,'blocks':len(cfg(q)[0]),'definitions':sum(data(s)[0] is not None for s in q)}
        for mode in ('rd','live'):
            for order in ('linear','flow'):
                v=analyze(q,mode,order,['result']);rec[f'{mode}_{order}']=[len(v[2]),v[3]]
        growth.append(rec)
    levels=[]
    for name,q,env,out in [('dag1',DAG1,dict(b=1,c=2,d=9),'d'),('dag2',DAG2,dict(x=4,y=2),'z'),
        ('branch',BRANCH,{'x':5},'out'),('single',SINGLE,{},'out')]:
        for mode in ('none','fast','full'):
            r,effort=(q,0) if mode=='none' else local(q) if mode=='fast' else global_opt(q,[out])
            m,s=generate(r,4,'next',[out])
            if mode!='none':effort+=max(0,len(m)-1);m=peephole(m)
            want=run(q,env)[0][out];got=run(m,env,True)[0][out]
            assert got==want
            sm=strict.lower(m,4);assert strict.run(sm,env)[0][out]==want
            levels.append(dict(case=name,level=mode,tac_before=len(q),tac_after=sum(x[0]!='nop' for x in r),
                               target=len(m),cost=sum(COST[x[0]] for x in m),strict_target=len(sm),strict_cost=strict.cost(sm),
                               effort=effort,result=got,optimized=r))
    Path('results.json').write_text(json.dumps(dict(alloc=alloc,adversarial=adversarial,small=small,
        growth=growth,levels=levels,loop_cfg=cfg(LOOP),rd_history=analyze(LOOP,'rd','linear',['avg'])[2]),indent=2)+'\n')
    print('Validated 32 machine-code comparisons, analysis orders and all optimization levels.')

if __name__=='__main__':main()
