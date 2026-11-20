"""Additional tests with predictions recorded before execution."""
import json
from pathlib import Path
from experiments import PREFIX
from layout import layout
from switch import dispatch
from tac import Compiler,execute,validate

def main():
    source='char tag; int k; float a[3]; record { int x; boolean y; } r; int *p;'
    results={}
    variants=[
        ({},[0,1,5,29,34],38),
        ({'float_width':4},[0,1,5,17,22],26),
        ({'alignment':4},[0,4,8,32,40],44),
        ({'record_alignment':8},[0,1,5,32,40],44)
    ]
    layout_runs=[]
    for options,offsets,end in variants:
        r,total,trace=layout(source,**options)
        assert [x[4] for x in r if x[0]=='global']==offsets
        assert total==end
        layout_runs.append([options,r,total,trace])
    results['layout']=layout_runs
    positive,negative=(Compiler().compile(PREFIX+f'if {cond}:\n    x = 1\n')
                       for cond in ('a < b and c < d','not (a < b and c < d)'))
    assert len(positive.quads)==len(negative.quads)==20
    assert [execute(c)['x'] for c in (positive,negative)]==[0,1]
    lists=lambda c:[x[2:] for x in c.trace if x[0]=='boolean lists']
    assert lists(positive)[-1]==tuple(reversed(lists(negative)[-1]))
    results['boolean']=[{'lists':lists(c),'quads':c.quads} for c in (positive,negative)]
    q=[x.copy() for x in positive.quads]
    invalid=len(q); branch=next(i for i,x in enumerate(q) if x[0].startswith('if'))
    q[branch][3]=invalid
    try:validate(q)
    except ValueError as ex:results['out_of_range']=str(ex)
    else:raise AssertionError('bad branch target accepted')
    a,b=([dispatch(v,m) for m in ('linear','binary','table')] for v in ([10,11,12],[10,11,510]))
    assert (a[2]['slots'],b[2]['slots'])==(3,501)
    assert [x['instructions'] for x in a[:2]]==[x['instructions'] for x in b[:2]]
    results['switch']=[a,b]
    src='def pair(a,b):\n    return 10*a+b\nout: int = pair(tick(),tick()+100)\n'
    order=[execute(Compiler(reverse=x).compile(src))['out'] for x in (False,True)]
    assert order==[112,121]
    results['order']=order
    (Path(__file__).parent/'evidence'/'followup.json').write_text(json.dumps(results,indent=2)+'\n')
    print('Follow-up layout, Boolean, target validation, switch and argument-order checks passed.')

if __name__=='__main__':main()
