"""Execute the Part I desk checks using the included quadruple model."""
import ast,json
from pathlib import Path
from tac import Compiler,Code,execute,validate
from layout import layout

def lower(source,types,initial):
    c=Compiler();c.types=types.copy()
    c.block(ast.parse(source).body);c.emit('halt');validate(c.q)
    program=Code(c.q,c.log,{},c.n)
    out=execute(program,initial)
    quads=[(i+100,o,a,b,d+100 if o=='jump' or o.startswith('if') else d)
           for i,(o,a,b,d) in enumerate(c.q)]
    trace=[]
    for rec in c.log:
        if rec[0].startswith('patch'):
            event,indices,target,snapshot=rec
            rows=ast.literal_eval(snapshot)
            trace.append((event,[i+100 for i in indices],target+100,
                          [(i+100,o,a,b,d+100 if (o=='jump' or o.startswith('if')) and d is not None else d)
                           for i,(o,a,b,d) in enumerate(rows)]))
        elif rec[0]=='boolean lists':trace.append((rec[0],rec[1],[i+100 for i in rec[2]],[i+100 for i in rec[3]]))
        elif rec[0]=='statement nextlist':trace.append((rec[0],rec[1],rec[2]+100,[]))
        elif rec[0]=='loop lists':trace.append((rec[0],[i+100 for i in rec[1]],[i+100 for i in rec[2]]))
        else:trace.append(rec)
    return {'source':source,'quadruples_from_100':quads,'trace_from_100':trace,
            'result':{k:v for k,v in out.items() if not k.startswith('%')}}
base='int a,b; float c[10]; record { int x; float y; } r; float *p;'
condition='a < b or c < d and e < f'
values=dict(zip('abcdefx',[0,1,2,1,0,1,0]))
types={n:'int' for n in values}
# Mutate a in this executable while test to terminate after one pass.
while_code=lower(f'while {condition}:\n    x = x + 1\n    a = 9\n',types,values)
desk_loop=lower(f'if {condition}:\n    x = x + 1\n',types,values)
neg=lower('if not (a < b and c < d):\n    x = 1\n',types,values)
kernel='''for i in count(0,n-1,2):
    if A[i][0] < 0 and not done:
        continue
    total = total + A[i][1] * scale
    if total > 1000 or i == n-1:
        break
'''
kt={'A':('array','float',(10,20)),'i':'int','n':'int','total':'float','scale':'float','done':'bool'}
k=lower(kernel,kt,{'A':{0:-1,8:9,328:4},'i':0,'n':3,'total':0.0,'scale':2.0,'done':False})
assert k['result']['total']==8.0 and while_code['result']['x']==neg['result']['x']==1
# Wrong OR patch redirects the true branch and leaves the false branch open.
original=[[ 'if<',1,2,None],['jump',None,None,None],
          ['if<',4,3,None],['jump',None,None,None],
          ['copy',True,None,'out'],['jump',None,None,7],
          ['copy',False,None,'out'],['halt',None,None,None]]
def faulty(wrong,left=True):
    q=[x.copy() for x in original]
    q[0][1]=1 if left else 5
    choices={0:2 if wrong else 4,1:6 if wrong else 2,2:4,3:6}
    for i,d in choices.items():q[i][3]=d
    return execute(Code(q,[],{},0))['out'],q
bad,qbad=faulty(True);good,qgood=faulty(False)
assert bad is False and good is True
assert faulty(False,False)[0] is False
# Nested loop adversary: inner break must not consume the outer continue.
adversary = lower("""sum = 0
for i in count(3,1,-1):
    if i == 2:
        continue
    for j in count(1,3,1):
        sum = sum + 1
        if j == 2:
            break
    sum = sum + 10
""", {'sum':'int','i':'int','j':'int'}, {'sum':0,'i':0,'j':0})
assert adversary['result']['sum'] == 24
try:
    lower('break\n', {}, {})
    raise AssertionError('break outside loop was accepted')
except ValueError as exc:
    assert 'outside loop' in str(exc)
try:
    lower('for i in count(1,2,step):\n    i = i + 1\n',
          {'i':'int','step':'int'}, {'i':0,'step':0})
    raise AssertionError('zero step was accepted')
except ValueError as exc:
    assert 'zero STEP' in str(exc)
report={'layout':layout(base),'changed_layout':layout(base.replace('[10]','[12]')),
        'while_executable':while_code,'condition':desk_loop,'negation':neg,'kernel':k,
        'nested_adversary':adversary,
        'defect':{'bad_with_fallback':qbad,'correct':qgood,'results':[bad,good]}}
Path('desk-checks.json').write_text(json.dumps(report,indent=2,default=str)+'\n')
print('Checked layout, negation, OR defect, sample kernel, nested loops, and loop errors.')
