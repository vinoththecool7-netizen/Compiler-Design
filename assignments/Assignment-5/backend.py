"""TAC flow analysis, allocator and instruction interpreter for a small target."""
from collections import Counter, defaultdict
from operator import add,sub,mul,floordiv
OPS={'+':add,'-':sub,'*':mul,'/':floordiv}
COST={'LD':2,'ST':2,'OP':1,'J':1,'B':1}
def var(x):return isinstance(x,str)
def data(ins):
    o,a,b,d=ins
    return (d if o in {*OPS,'=' ,'load'} else None,
            tuple(x for x in ((a,b) if o in {*OPS,'load','ge','le','eq'} else (a,) if o=='=' else ()) if var(x)))
def cfg(q):
    if not q:return [],[],[]
    leaders={0}
    for i,(o,a,b,d) in enumerate(q):
        if o in ('j','ge','le','eq'):
            if not 0<=d<len(q):raise ValueError('invalid jump')
            leaders.add(d)
            if i+1<len(q):leaders.add(i+1)
    starts=sorted(leaders);blocks=list(zip(starts,starts[1:]+[len(q)]))
    who={start:j for j,start in enumerate(starts)}
    succ=[];pred=[[] for _ in blocks]
    for j,(_,e) in enumerate(blocks):
        o,a,b,d=q[e-1]
        s=[who[d]] if o in ('j','ge','le','eq') else []
        if o!='j' and j+1<len(blocks) and j+1 not in s:s.append(j+1)
        for k in s:pred[k].append(j)
        succ.append(s)
    return blocks,succ,pred
def analyze(q,mode,order,outputs=()):
    blocks,succ,pred=cfg(q); n=len(blocks)
    ds=defaultdict(int)
    for i,s in enumerate(q):
        d,_=data(s)
        if d:ds[d]|=1<<i
    names={x for s in q for x in ((data(s)[0],)+data(s)[1]) if x is not None}|set(outputs)
    bits={x:1<<i for i,x in enumerate(sorted(names))}
    gen=[];kill=[]
    for a,b in blocks:
        g=k=0
        for i in range(a,b):
            d,u=data(q[i])
            if mode=='rd' and d:
                g=(g&~ds[d]) | 1<<i;k|=ds[d]
            elif mode=='live':
                for x in u:g|=bits[x]&~k
                if d:k|=bits[d]
        gen.append(g);kill.append(k)
    seq=list(range(n))
    if order=='flow':
        seen=set();post=[]
        def visit(root):
            todo=[(root,False)]
            while todo:
                k,done=todo.pop()
                if done:post.append(k)
                elif k not in seen:
                    seen.add(k);todo.append((k,True));todo.extend((x,False) for x in reversed(succ[k]))
        for i in seq:visit(i)
        seq=post[::-1] if mode=='rd' else post
    I=[0]*n;O=[0]*n; history=[];operations=0
    boundary=sum(bits.get(x,0) for x in set(outputs))
    while n:
        change=False
        for j in seq:
            adj=pred[j] if mode=='rd' else succ[j]
            # A terminal conditional has both a branch successor and a
            # fall-through exit. Outputs are observable on that exit path.
            falls_out=(j==n-1 and q[blocks[j][1]-1][0]!='j')
            s=boundary if mode=='live' and (not adj or falls_out) else 0
            for k in adj:s|=(O if mode=='rd' else I)[k];operations+=1
            t=gen[j]|(s&~kill[j]);operations+=3
            u,v=(s,t) if mode=='rd' else (t,s)
            if (u,v)!=(I[j],O[j]):I[j],O[j]=u,v;change=True
        history.append((I.copy(),O.copy()))
        if not change:break
    return I,O,history,operations,bits
def nextuse(q,a,b,out):
    state={x:float('inf') for x in out};result={}
    for i in range(b-1,a-1,-1):
        result[i]=state.copy()
        d,u=data(q[i])
        if d:state.pop(d,None)
        for x in u:state[x]=i
    return result

def generate(q,k,policy,outputs):
    if k<2:raise ValueError('at least two registers')
    blocks,succ,_=cfg(q);_,out,_,_,bits=analyze(q,'live','flow',outputs)
    target=[]; labels={}; spills=0; maxreg=0
    def emit(*s):target.append(s)
    for j,(a,b) in enumerate(blocks):
        labels[a]=len(target)
        liveout={x for x,v in bits.items() if out[j]&v}
        future=nextuse(q,a,b,liveout)
        regs=[None]*k;dirty=set()
        def write(r):
            x=regs[r]
            if x in dirty:emit('ST',x,r);dirty.remove(x)
        def pick(x,after,lock=(),load=True):
            nonlocal spills,maxreg
            if x in regs:return regs.index(x)
            choice=[r for r in range(k) if r not in lock]
            free=[r for r in choice if regs[r] is None]
            r=free[0] if free else choice[0] if policy=='first' else max(choice,key=lambda r:after.get(regs[r],-1))
            old=regs[r]
            if old in dirty:
                if old in after:write(r);spills+=1
                else:dirty.remove(old)
            regs[r]=x;maxreg=max(maxreg,r+1)
            if load:emit('LD',r,x)
            return r
        def operand(x,after,lock=()):
            return ('r',pick(x,after,lock)) if var(x) else ('imm',x)
        def flush():
            for r,x in enumerate(regs):
                if x in liveout:write(r)
        for i in range(a,b):
            op,x,y,d=q[i];after=future[i]
            if op=='nop':continue
            before=after.copy()
            # Keep input values while registers for the current instruction are being acquired.
            dest,uses=data(q[i]);before.update({u:i for u in uses})
            first=operand(x,before) if op!='j' else None
            second=operand(y,before,(first[1],) if first and first[0]=='r' else ())
            if op in ('j','ge','le','eq'):
                flush()
                if op=='j':emit('J',d)
                else:emit('B',op,first,second,d)
                continue
            dead=[z[1] for z in (first,second) if z[0]=='r' and (regs[z[1]] not in after or regs[z[1]]==d)]
            if d in regs:r=regs.index(d)
            elif dead:
                r=dead[0];dirty.discard(regs[r]);regs[r]=d
            else:r=pick(d,after,load=False)
            emit('OP',op,r,first,second);dirty.add(d)
        if q[b-1][0] not in ('j','ge','le','eq'):flush()
    target=[(*s[:-1],labels[s[-1]]) if s[0] in ('J','B') else s for s in target]
    counts=Counter(x[0] for x in target)
    return target,dict(blocks=len(blocks),edges=sum(map(len,succ)),instructions=len(target),
                       loads=counts['LD'],stores=counts['ST'],spills=spills,registers=maxreg,
                       cost=sum(COST[s[0]] for s in target))

def test(op,a,b):return a>=b if op=='ge' else a<=b if op=='le' else a==b
def calculate(op,a,b):
    if op=='=':return a
    if op=='load':return a[b//4]
    return OPS[op](a,b)
def run(code,initial,target=False):
    env=initial.copy();reg={};pc=0;steps=0
    val=lambda x:env[x] if var(x) else x
    operand=lambda x:reg[x[1]] if x[0]=='r' else x[1]
    while pc<len(code):
        if steps==100000:raise ValueError('execution limit')
        s=code[pc];pc+=1;steps+=1
        if target:
            o,*a=s
            if o=='LD':r,x=a;reg[r]=env[x]
            elif o=='ST':x,r=a;env[x]=reg[r]
            elif o=='OP':op,d,x,y=a;reg[d]=calculate(op,operand(x),operand(y))
            elif o=='J':pc=a[0]
            elif o=='B':
                op,x,y,d=a
                if test(op,operand(x),operand(y)):pc=d
        else:
            o,a,b,d=s
            if o=='j':pc=d
            elif o in ('ge','le','eq'):
                if test(o,val(a),val(b)):pc=d
            elif o!='nop':env[d]=calculate(o,val(a),val(b))
    return env,steps
