"""Lower the teaching backend to destructive two-operand register instructions."""
# Source variables are strings; the tagged tuple cannot alias a source name.
SCRATCH=('compiler_scratch',)

def lower(code,k):
    out=[];labels={};fix=[]
    def emit(*s):out.append(s)
    def ld(r,x):
        if x!=('r',r):emit('LD',r,x)
    def op(name,r,x):emit('OP',name,r,x)
    for i,s in enumerate(code):
        labels[i]=len(out);kind=s[0]
        if kind=='LD':emit('LD',s[1],('mem',s[2]))
        elif kind=='ST':emit('ST',s[1],s[2])
        elif kind=='OP':
            _,o,r,x,y=s
            if o=='load':
                # The memory address is evaluated before the destination write.
                emit('LD',r,('indexed',x,y))
            elif o=='=':ld(r,x)
            else:
                if y==('r',r) and x!=('r',r):
                    if o in ('+','*'):x,y=y,x
                    else:
                        emit('ST',SCRATCH,r);y=('mem',SCRATCH)
                ld(r,x);op(o,r,y)
        elif kind=='J':
            fix.append((len(out),s[-1]));emit('J',None)
        elif kind=='B':
            _,o,x,y,target=s
            # Registers are dead across block boundaries; values were flushed.
            r=x[1] if x[0]=='r' else next(t for t in range(k) if y!=('r',t))
            ld(r,x);op('-',r,y)
            for condition in (('LT','EQ') if o=='le' else ('GT','EQ') if o=='ge' else ('EQ',)):
                fix.append((len(out),target));emit('B',condition,r,None)
        else:raise ValueError(kind)
    labels[len(code)]=len(out)
    for i,dest in fix:out[i]=(*out[i][:-1],labels[dest])
    return out

def cost(code):
    def mem(x):return x[0] in ('mem','indexed')
    n=0
    for s in code:
        if s[0]=='ST':n+=2
        elif s[0]=='LD':n+=1+int(mem(s[2]))
        elif s[0]=='OP':n+=1+int(mem(s[3]))
        else:n+=1
    return n

def run(code,initial):
    env=initial.copy();reg={};pc=0;steps=0
    def val(v):
        kind,x,*rest=v
        if kind=='r':return reg[x]
        if kind=='imm':return x
        if kind=='mem':return env[x]
        if kind=='indexed':return val(x)[val(rest[0])//4]
        raise ValueError(kind)
    while pc<len(code):
        if steps==100000:raise ValueError('execution limit')
        s=code[pc];pc+=1;steps+=1
        if s[0]=='LD':reg[s[1]]=val(s[2])
        elif s[0]=='ST':env[s[1]]=reg[s[2]]
        elif s[0]=='OP':
            _,op,r,v=s;x,y=reg[r],val(v)
            reg[r]={'+':lambda:x+y,'-':lambda:x-y,'*':lambda:x*y,'/':lambda:x//y}[op]()
        elif s[0]=='J':pc=s[1]
        elif s[0]=='B':
            _,op,r,target=s;x=reg[r]
            if (x<0 if op=='LT' else x>0 if op=='GT' else x==0):pc=target
    return env,steps
