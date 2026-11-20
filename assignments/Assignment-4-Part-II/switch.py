"""Build and execute three switch-dispatch representations."""
def dispatch(values,mode,default=True,fallthrough=False):
    if not default:raise ValueError('missing default')
    if len(values)!=len(set(values)):raise ValueError('duplicate case')
    if fallthrough:raise ValueError('fall-through is unsupported')
    tests={v:f'case_{i}' for i,v in enumerate(values)}
    code=[];slots=0
    if mode=='linear':
        code=[('eq',n,d) for n,d in tests.items()]+[('goto','default')]
    elif mode=='binary':
        def build(keys):
            if not keys:return
            m=len(keys)//2; n=keys[m]; left,right=keys[:m],keys[m+1:]
            code.extend([('label',n),('eq',n,tests[n]),('lt',n,left[len(left)//2] if left else 'default'),
                         ('goto',right[len(right)//2] if right else 'default')])
            build(left);build(right)
        build(sorted(values))
        if not values:code=[('goto','default')]
    elif mode=='table':
        lo=min(values,default=0); hi=max(values,default=-1);slots=hi-lo+1
        code=[('range',lo,hi),('dispatch',[tests.get(n,'default') for n in range(lo,hi+1)])] if slots else [('goto','default')]
    else:raise ValueError('unknown switch strategy')
    def execute(x):
        count=0
        if mode=='table':
            if not slots:return 'default',0
            if x<lo:return 'default',1
            if x>hi:return 'default',2
            return code[1][1][x-lo],2
        if mode=='linear':
            for n,d in tests.items():
                count+=1
                if x==n:return d,count
        else:
            keys=sorted(values)
            while keys:
                m=len(keys)//2;n=keys[m];count+=1
                if n==x:return tests[n],count
                count+=1;keys=keys[:m] if x<n else keys[m+1:]
        return 'default',count
    probes=[values[0],values[len(values)//2],values[-1],max(values)+1] if values else [0]
    actual=[execute(x) for x in probes]
    assert [d for d,_ in actual]==[tests.get(x,'default') for x in probes]
    return {'strategy':mode,'code':code,'tests':tests,'instructions':sum(c[0]!='label' for c in code),
            'slots':slots,'bytes':4*slots,'probes':probes,'comparisons':[n for _,n in actual]}
