"""Operator-precedence recognizer for the seven-terminal exercise."""
from parsing import csvfile, write

TERMS=['id','+','*','^','(',')','$']
MATRIX=[
    '— > > > — > >',
    '< > < < < > >',
    '< > > < < > >',
    '< > > < < > >',
    '< < < < < = —',
    '— > > > — > >',
    '< < < < < — =',
]
REL={(a,b):c for a,row in zip(TERMS,MATRIX) for b,c in zip(TERMS,row.split())}

def parse(source):
    tokens=source.split()+['$']
    stack=['$']; i=0; trace=[]
    display=lambda n: 'N' if isinstance(n,tuple) else n
    while True:
        t=tokens[i]
        a=next(x for x in reversed(stack) if isinstance(x,str))
        before=f'{" ".join(map(display,stack))} | {" ".join(tokens[i:])} | {a} {REL[a,t]} {t} | '
        if t=='$' and a=='$':
            assert len(stack)==2 and isinstance(stack[1],tuple)
            return trace+[before+'accept',str(stack[1])]
        if REL[a,t] in ('<','='):
            stack.append(t); i+=1;trace.append(before+'shift')
        elif REL[a,t]=='>':
            positions=[i for i,x in enumerate(stack) if isinstance(x,str)]
            j=len(positions)-1
            while REL[stack[positions[j-1]],stack[positions[j]]] != '<': j-=1
            k=positions[j-1]+1; h=stack[k:]
            if h==['id']: n=('id',)
            elif len(h)==3 and h[0]=='(' and h[2]==')': n=h[1]
            elif len(h)==3 and h[1] in ('+','*','^') and isinstance(h[0],tuple) and isinstance(h[2],tuple):
                n=(h[1],h[0],h[2])
            else: raise ValueError('invalid handle')
            stack[k:]=[n];trace.append(before+'reduce '+' '.join(map(display,h)))
        else: raise ValueError('invalid terminal relation')

if __name__=='__main__':
    csvfile('q3-precedence.csv',['stack/input',*TERMS],[[a,*r.split()] for a,r in zip(TERMS,MATRIX)])
    a=parse('id + id * id');b=parse('id ^ id ^ id')
    assert a[-1]=="('+', ('id',), ('*', ('id',), ('id',)))"
    assert b[-1]=="('^', ('id',), ('^', ('id',), ('id',)))"
    write('q3-precedence.txt',a+['']+b)
