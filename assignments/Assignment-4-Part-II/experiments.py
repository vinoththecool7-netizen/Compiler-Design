from pathlib import Path
import json, sys
from dataclasses import replace
from tac import Compiler,execute,validate
from layout import layout
from switch import dispatch

E=Path(__file__).resolve().parent/'evidence'; E.mkdir(exist_ok=True)
def save(name,data): (E/name).write_text(json.dumps(data,indent=2)+'\n')

DECL='char ch; int a, b; float c[10]; record { int x; float y; } r; float *p; boolean done; int m[2][3];'
PROGRAMS={
'factorial':('''def fact(n: int) -> int:
    if n <= 1:
        return 1
    return n * fact(n-1)
out: int = fact(5)
''',120),
'array_sum':('''a: array[int,2,2]
a[0][0] = 2
a[0][1] = 3
a[1][0] = 4
a[1][1] = 5
out: int = 0
i: int
j: int
for i in count(0,1,1):
    for j in count(0,1,1):
        out = out + a[i][j]
''',14),
'short_circuit':('''out: int = 0
while out < 3 and (out < 2 or tick() == 1):
    out = out + 1
''',3),
'switch':('''k: int = 3
out: int
match k:
    case 1:
        out = 10
    case 3:
        out = 30
    case _:
        out = 0
''',30),
'calls':('''def g(a):
    return a * 2
def f(a,b):
    return a * 10 + b
def zero():
    return 0
def noop() -> void:
    return
noop()
out: int = f(g(3), 3+1) + zero()
''',64),
'do_while':('''out: int = 0
with do(out < 3):
    out = out + 1
''',3),
'negative_loop':('''out: int = 0
i: int
j: int
s: int = -1
for i in count(3,1,s):
    for j in count(1,3,1):
        if j == 1:
            continue
        out = out + i
        break
    if i == 2:
        continue
    out = out + 10
''',26),
}
ARITH='''a: int = 3
b: int = 2
p: ptr[int] = addr(b)
A: array[float,2,2]
v: array[int,2]
A[1][0] = 2.0
v[0] = 20
x: float = (a + b) * (a + b) + A[1][0] * 2.0
x = x + -deref(p) + v[0] / (a + b)
'''
COND=['a < b or c < d and e < f','not (a < b and c < d) or e < f']
PREFIX='a: int = 1\nb: int = 2\nc: int = 3\nd: int = 2\ne: int = 0\nf: int = 1\nx: int = 0\n'
ORDER='''def pair(a,b):
    return a * 10 + b
out: int = pair(tick(),tick())
'''
def optimize(code):
    q=[x.copy() for x in code.quads]; rewrites=0
    for ins in q:
        if ins[0]=='jump' or ins[0].startswith('if'):
            old=ins[3]; target=old;seen=set()
            while q[target][0]=='jump' and target not in seen:
                seen.add(target);target=q[target][3]
            if target!=old:ins[3]=target;rewrites+=1
    reachable=set();todo=[0,*[x[0] for x in code.functions.values()]]
    while todo:
        i=todo.pop()
        if i in reachable:continue
        reachable.add(i)
        op,_,_,target=q[i]
        if op=='jump':todo.append(target)
        elif op not in ('halt','trap','return'):
            todo.append(i+1)
            if op.startswith('if'):todo.append(target)
    mapping={old:i for i,old in enumerate(sorted(reachable))}
    reduced=[]
    for i in sorted(reachable):
        ins=q[i]
        if ins[0]=='jump' or ins[0].startswith('if'):ins[3]=mapping[ins[3]]
        reduced.append(ins)
    validate(reduced)
    funcs={k:(mapping[v[0]],*v[1:]) for k,v in code.functions.items()}
    return replace(code,quads=reduced,functions=funcs),rewrites

def representations(q):
    temp={}; triples=[]; moves=[]
    for i,(op,a,b,d) in enumerate(q):
        ref=lambda x:f'({temp[x]})' if isinstance(x,str) and x in temp else x
        triples.append((op,ref(a),ref(b),d if not isinstance(d,str) or not d.startswith('%t') else None))
        if isinstance(d,str) and d.startswith('%t'):temp[d]=i
        moves.append(i)
    return {'quadruples':q,'triples':triples,'indirect_order':moves}

def main():
    results={}
    for name,(source,expected) in PROGRAMS.items():
        c=Compiler(checks=True).compile(source)
        after,threads=optimize(c)
        assert execute(c)['out']==execute(after)['out']==expected
        results[name]={'expected':expected,'actual':execute(c)['out'],'before':len(c.quads),
            'after':len(after.quads),'threads':threads}
        save(name,{'source':source,'quadruples':c.quads,'patches_and_lists':c.trace,'result':results[name]})
    save('integration',results)
    layouts={}
    for k,kw in [('base',{}),('float4',{'float_width':4}),('align4',{'alignment':4}),
                 ('record8',{'record_alignment':8})]:
        layouts[k]=layout(DECL,**kw)
    try:layout('int a[0];')
    except ValueError as ex:layouts['boundary']=str(ex)
    save('layout',layouts)
    a=Compiler().compile(ARITH);b=Compiler(cse=True).compile(ARITH);c=Compiler(cse=True,checks=True).compile(ARITH)
    assert execute(a)['x']==execute(b)['x']==execute(c)['x']==31.0
    bad=Compiler(omit_widening=True).compile(ARITH)
    assert execute(a,strict_numeric=True)['x']==31.0
    try:execute(bad,strict_numeric=True)
    except ValueError as ex:conversion_error=str(ex)
    else:raise AssertionError('mixed operation unexpectedly passed strict numeric validation')
    save('naive-arithmetic',{'source':ARITH,'quadruples':bad.quads,'strict_error':conversion_error})
    save('arithmetic',{'source':ARITH,'baseline':representations(a.quads),'cse':representations(b.quads),
          'checked':representations(c.quads),'counts':[[len(x.quads),x.temps] for x in (a,b,c)]})
    for i,s in enumerate(COND):
        c=Compiler().compile(PREFIX+f'if {s}:\n    x = 1\n')
        assert execute(c)['x']==1
        save(f'boolean-{i}',{'condition':s,'quadruples':c.quads,'trace':c.trace})
    errors={}
    for n,s,kw in [('omitted patch',PREFIX+'if '+COND[0]+':\n    x = 1\n',{'broken':True}),
                     ('break','break',{}),('type','x: int = 1.5',{}),('undeclared','x = 1',{}),
                     ('arity','def f(a):\n    return a\nx: int = f()\n',{}),
                     ('bounds','a: array[int,2]\nx: int = a[2]',{'checks':True})]:
        try:execute(Compiler(**kw).compile(s))
        except ValueError as ex:errors[n]=str(ex)
        else:raise AssertionError(n)
    save('errors',errors)
    order=[]
    for reverse in (False,True):
        x=Compiler(reverse=reverse).compile(ORDER)
        order.append((execute(x)['out'],x.quads,x.trace))
    assert [x[0] for x in order]==[12,21]
    save('order',order)
    switches={}
    for name,values in [('few',[1,3,5]),('dense',list(range(1,17))),('sparse',[1,100,400,1000]),
                        ('before gap',[1,2,3,4]),('after gap',[1,2,3,1000]),('negative',[-4,-2,3]),('default',[])]:
        switches[name]=[dispatch(values,mode) for mode in ('linear','binary','table')]
    for name,args in [('duplicate',([1,1],'linear')),('empty',([],'linear',False)),
                      ('fallthrough',([1],'linear',True,True))]:
        try:dispatch(*args)
        except ValueError as ex:switches[name]=str(ex)
        else:raise AssertionError(name)
    save('switch-strategies',switches)
    stress={}
    for name,s in [('nested',PREFIX+'if '+'('*300+'a<b'+')'*300+':\n    x = 1\n'),
                 ('or',PREFIX+'if '+' or '.join(['a<b']*400)+':\n    x = 1\n'),
                 ('cases','k: int = 399\nx: int\nmatch k:\n'+''.join(f'    case {i}:\n        x = {i}\n' for i in range(400))+'    case _:\n        x = 0\n'),
                 ('expression','x: int = '+'+'.join(['1']*1200))]:
        try:
            c=Compiler().compile(s);stress[name]={'quads':len(c.quads),'x':execute(c)['x']}
        except (ValueError,RecursionError) as ex:stress[name]=str(ex)
    assert stress['expression']['x']==1200
    save('stress',stress)
    print('Seven execution results, six rejection cases, argument order and switch dispatch verified.')

if __name__=='__main__':main()
