"""Construct parsing tables and run the assignment's trace experiments."""
from collections import defaultdict
from pathlib import Path
import csv, re, time, statistics, sys

OUT=Path(__file__).parent/'evidence'
EXPR={'E':[('T','R')],'R':[('+','T','R'),('-','T','R'),()],
      'T':[('F','U')],'U':[('*','F','U'),('/','F','U'),()],
      'F':[('(','E',')'),('id',),('num',)]}
BASE={'E':[('E','+','T'),('E','-','T'),('T',)],
      'T':[('T','*','F'),('T','/','F'),('F',)],'F':[('(','E',')'),('id',),('num',)]}

def write(name, rows):
    (OUT/name).write_text('\n'.join(map(str,rows))+'\n')

def csvfile(name, headers, rows):
    with (OUT/name).open('w',newline='') as f:
        w=csv.writer(f); w.writerow(headers);w.writerows(rows)

def sets(g,start):
    first={a:set() for a in g}
    follow={a:({'$'} if a==start else set()) for a in g}
    def seq(xs):
        result=set()
        for x in xs:
            fs=first.get(x,{x})
            result |= fs-{'ε'}
            if 'ε' not in fs: return result
        return result|{'ε'}
    history=[]
    while True:
        nf={a:first[a]|set().union(*(seq(b) for b in bs)) for a,bs in g.items()}
        nh={a:set(v) for a,v in follow.items()}
        for a,bs in g.items():
            for b in bs:
                for i,x in enumerate(b):
                    if x in g:
                        f=seq(b[i+1:])
                        nh[x] |= f-{'ε'}
                        if 'ε' in f: nh[x] |= follow[a]
        if nf==first and nh==follow: break
        first,follow=nf,nh
        history.append((first,follow))
    return first,follow,seq,history

FIRST,FOLLOW,seq,HISTORY=sets(EXPR,'E')
LL={}
for a,bs in EXPR.items():
    for b in bs:
        f=seq(b)
        for t in f-{'ε'}|(FOLLOW[a] if 'ε' in f else set()):
            assert (a,t) not in LL
            LL[a,t]=b

def lex(s):
    raw=re.findall(r'[A-Za-z_]\w*|\d+|[^\s]',s)
    return [(('id' if x[0].isalpha() or x[0]=='_' else 'num' if x.isdecimal() else x),x)
            for x in raw]+[('$','$')]

def predictive(ts,trace=False):
    stack=['$','E']; i=j=peak=0; rows=[]
    while stack:
        a=stack.pop(); t=ts[i][0]; j+=1
        before=f'{" ".join(stack+[a])} | {" ".join(s for _,s in ts[i:])} | ' if trace else ''
        if a==t:
            action=f'match {t}';i+=1
        elif (a,t) in LL:
            b=LL[a,t]; stack.extend(reversed(b))
            action=f'{a} → {" ".join(b) or "ε"}'
        else:
            action=f'error at {a} on {ts[i][1]}'
            if trace: rows.append(before+action)
            return False,j,peak,rows,i
        if trace: rows.append(before+action)
        peak=max(peak,len(stack))
    return True,j,max(2,peak),rows,i

def recursive(ts, trace=False, cap=600):
    i=0; depth=0; peak=0; rows=[]
    def enter(a):
        nonlocal depth,peak
        depth+=1;peak=max(depth,peak)
        if trace: rows.append(f'enter {a} at {ts[i][1]}')
        if depth>cap: raise ValueError('depth budget exceeded')
    def match(a):
        nonlocal i
        if ts[i][0]!=a: raise ValueError(f'expected {a} at {ts[i][1]}')
        if trace: rows.append(f'match {ts[i][1]}')
        s=ts[i][1];i+=1
        return s
    def E():
        nonlocal depth
        enter('E'); left=T(); left=R(left);depth-=1;return left
    def R(left):
        while ts[i][0] in ('+','-'):
            op=match(ts[i][0]);left=(op,left,T()) if trace else (T(),None)[1]
        if ts[i][0] not in FOLLOW['R']: raise ValueError(f'R on {ts[i][1]}')
        return left
    def T():
        nonlocal depth
        enter('T'); left=F();left=U(left);depth-=1;return left
    def U(left):
        while ts[i][0] in ('*','/'):
            op=match(ts[i][0]);left=(op,left,F()) if trace else (F(),None)[1]
        if ts[i][0] not in FOLLOW['U']: raise ValueError(f'U on {ts[i][1]}')
        return left
    def F():
        nonlocal depth
        enter('F');t=ts[i][0]
        if t=='(':
            match('('); value=E();match(')')
        elif t in ('id','num'): value=match(t)
        else: raise ValueError(f'F on {ts[i][1]}')
        depth-=1
        return value
    try:
        ast=E();match('$')
        return True,peak,rows,ast
    except ValueError as exc:
        return False,peak,rows,str(exc)

class SLR:
    def __init__(self,g,start):
        _,follow,_,_=sets(g,start)
        self.rules=[("S'",(start,))]+[(a,b) for a,bs in g.items() for b in bs]
        def close(items):
            out=set(items)
            while True:
                found=set()
                for i,j in out:
                    b=self.rules[i][1]
                    if j<len(b) and b[j] in g:
                        found.update((k,0) for k,(a,_) in enumerate(self.rules) if a==b[j])
                if found<=out: return frozenset(out)
                out |= found
        self.states=[close({(0,0)})];self.go={};self.actions=defaultdict(set)
        for i,state in enumerate(self.states):
            symbols={self.rules[k][1][j] for k,j in state if j<len(self.rules[k][1])}
            for x in sorted(symbols,key=lambda x:(x.isupper(),x)):
                target=close((k,j+1) for k,j in state if j<len(self.rules[k][1]) and self.rules[k][1][j]==x)
                if target not in self.states: self.states.append(target)
                n=self.states.index(target);self.go[i,x]=n
                if x not in g: self.actions[i,x].add(('s',n))
            for k,j in state:
                a,b=self.rules[k]
                if j!=len(b):continue
                if k==0: self.actions[i,'$'].add(('acc',0))
                else:
                    for t in follow[a]:self.actions[i,t].add(('r',k))
    def trace(self,ts):
        stack=[0];i=0;rows=[]
        while True:
            t=ts[i]; opts=self.actions.get((stack[-1],t),set())
            begin=f'{" ".join(map(str,stack))} | {" ".join(ts[i:])} | '
            if len(opts)!=1:
                rows.append(begin+('error' if not opts else f'conflict {sorted(opts)}'));return rows
            a,n=next(iter(opts))
            if a=='acc':rows.append(begin+'accept');return rows
            if a=='s':stack.extend([t,n]);i+=1;rows.append(begin+f'shift {n}')
            else:
                lhs,rhs=self.rules[n]
                rows.append(begin+f'reduce {lhs} → {" ".join(rhs)}')
                if rhs:del stack[-2*len(rhs):]
                stack.extend([lhs,self.go[stack[-1],lhs]])
    def describe(self):
        rows=[]
        for i,s in enumerate(self.states):
            items=[]
            for k,j in sorted(s):
                a,b=self.rules[k]
                items.append(a+' → '+' '.join((*b[:j],'·',*b[j:])))
            rows.append(f'I{i}: '+ ' | '.join(items))
        rows+=['',*(f'I{i} --{s}--> I{j}' for (i,s),j in self.go.items())]
        rows+=['',*(f'{i}, {s}: '+str(sorted(a)) for (i,s),a in sorted(self.actions.items()))]
        return rows

def main():
    nominal=lex('rate * ( p + f ) - d')
    bad=lex('rate * ( p + ) - d')
    rd=recursive(nominal,True); ll=predictive(nominal,True); err=predictive(bad,True)
    assert rd[0] and ll[0] and not err[0]
    write('q2-recursive.txt',rd[2]+[f'AST: {rd[3]}'])
    write('q2-predictive.txt',ll[3]+['','Rejected input',*err[3]])
    show=lambda x:' '.join(sorted(x)) or '∅'
    write('q2-first-follow.txt',[f'Round {i} {a}: FIRST={show(f[a])}, FOLLOW={show(h[a])}'
        for i,(f,h) in enumerate(HISTORY,1) for a in EXPR])
    csvfile('q2-table.csv',['NT','id','num','(','+','-','*','/',')','$'],
        [[a,*[(' '.join(LL[a,t]) or 'ε') if (a,t) in LL else '—'
              for t in ('id','num','(','+','-','*','/',')','$')]] for a in EXPR])
    simple=SLR({'E':[('E','+','T'),('T',)],'T':[('T','*','F'),('F',)],
                'F':[('(','E',')'),('id',)]},'E')
    write('q3-shift-reduce.txt',simple.trace('id + id * id $'.split()))
    q=SLR({'S':[('C','C')],'C':[('c','C'),('d',)]},'S')
    assert len(q.states)==7
    write('q4-machine.txt',q.describe())
    write('q4-traces.txt',q.trace('c d d $'.split())+['']+q.trace('c d $'.split()))
    x=SLR({'S':[('L','=','R'),('R',)],'L':[('*','R'),('id',)],'R':[('L',)]},'S')
    conflicts=[(i,t,z) for (i,t),z in x.actions.items() if len(z)>1]
    assert len(conflicts)==1 and conflicts[0][1]=='='
    write('q4-non-slr.txt',x.describe())
    sys.setrecursionlimit(4000)
    rows=[]
    for n in (0,10,100,199,200,1000,10000):
        ts=lex('('*n+'x'+')'*n); times=[[],[]]
        for j in range(9):
            now=time.perf_counter_ns(); a=recursive(ts);times[0].append(time.perf_counter_ns()-now)
            now=time.perf_counter_ns(); b=predictive(ts);times[1].append(time.perf_counter_ns()-now)
        assert b[0] and a[0]==(3*n+3<=600) and a[1]==min(3*n+3,601)
        rows.append([n,len(ts)-1,'accept' if a[0] else 'depth limit',a[1],
                      b[1],b[2],*[f'{statistics.median(t)/1e6:.4f}' for t in times]])
    csvfile('q7-depth.csv',['nesting','tokens','recursive','active_frames','LL_steps','LL_peak',
                            'recursive_ms','LL_ms'],rows)
    print('LL and SLR traces generated, and seven depth comparisons passed.')

if __name__=='__main__': main()
