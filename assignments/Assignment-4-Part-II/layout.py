"""Declaration layout with inherited base type, isolated record scopes and policy rules."""
import re

def layout(source, float_width=8, alignment=1, record_alignment=1):
    ts=re.findall(r'\w+|[^\s]',source); i=0; rows=[]; trace=[]
    base={'int':4,'float':float_width,'boolean':1,'char':1}
    def peek(): return ts[i] if i<len(ts) else None
    def take(expected=None):
        nonlocal i
        x=peek()
        if x is None or expected is not None and x!=expected:
            raise ValueError(f'expected {expected or "token"}, found {x}')
        i+=1
        return x
    def aligned(n,a): return (n+a-1)//a*a
    def scope(path):
        offset=0; names=set()
        while peek() not in (None,'}'):
            kind=take()
            if kind=='record':
                take('{'); w=scope(path+'.record'+str(i)); take('}')
                if w==0: raise ValueError('empty record')
                w=aligned(w,record_alignment)
                trace.append(f'record storage after tail padding: {w}')
            else:
                if kind not in base: raise ValueError(f'unknown type {kind}')
                w=base[kind]
            while True:
                t,width=kind,w
                trace.append(f'inherit {path}: t={t} w={width}')
                while peek()=='*': take(); t='pointer('+t+')';width=4
                name=take()
                if not re.fullmatch(r'[A-Za-z_]\w*',name): raise ValueError('expected identifier')
                dims=[]
                while peek()=='[':
                    take(); n=take()
                    if not n.isdecimal() or int(n)==0: raise ValueError('array bound must be positive')
                    dims.append(int(n));take(']')
                for n in reversed(dims):t=f'array({n},{t})';width*=n
                if name in names:raise ValueError('duplicate '+name)
                names.add(name)
                a=max(alignment,record_alignment) if kind=='record' and t=='record' else alignment
                start=aligned(offset,a); rows.append((path,name,t,width,start))
                trace.append(f'enter({name},{t},{width},{start}); offset {offset} -> {start+width}')
                offset=start+width
                if peek()!=',':break
                take(',')
            take(';')
        trace.append(f'scope {path} fields occupy {offset} bytes')
        return offset
    total=scope('global')
    if peek() is not None: raise ValueError('unexpected closing brace')
    return rows,total,trace
