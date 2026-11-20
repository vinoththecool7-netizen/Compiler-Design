"""Compile an explicitly restricted Python-shaped source language into quadruples."""
import ast
from dataclasses import dataclass
from operator import add,sub,mul,truediv,lt,le,gt,ge,eq,ne

OPS=dict(zip((ast.Add,ast.Sub,ast.Mult,ast.Div,ast.Lt,ast.LtE,ast.Gt,ast.GtE,ast.Eq,ast.NotEq),
             ('+','-','*','/','<','<=','>','>=','==','!=')))
RUN=dict(zip(OPS.values(),(add,sub,mul,truediv,lt,le,gt,ge,eq,ne)))

@dataclass
class Code:
    quads:list
    trace:list
    functions:dict
    temps:int

class Compiler:
    def __init__(self,cse=False,checks=False,reverse=False,broken=False):
        self.q=[];self.log=[];self.functions={};self.types={};self.loops=[]
        self.cse=cse;self.cache={};self.checks=checks;self.reverse=reverse
        self.broken=broken;self.n=0
    def fail(self,node,msg): raise ValueError(f'line {node.lineno}: {msg}')
    def emit(self,op,a=None,b=None,d=None):
        self.q.append([op,a,b,d])
        return len(self.q)-1
    def patch(self,indices,target):
        if not indices:return
        self.log.append(('patch before',tuple(indices),target,repr(self.q)))
        for i in indices:
            assert self.q[i][3] is None
            self.q[i][3]=target
        self.log.append(('patch after',tuple(indices),target,repr(self.q)))
    def temp(self):
        self.n+=1;return f'%t{self.n}'
    def compute(self,op,a,b=None,cached=True):
        key=(op,a,b)
        if self.cse and cached and key in self.cache:return self.cache[key]
        d=self.temp();self.emit(op,a,b,d)
        if self.cse and cached:self.cache[key]=d
        return d
    def widen(self,a,t):return self.compute('float',a) if t=='int' else a
    def ident(self,n):
        if n.id not in self.types:self.fail(n,'undeclared '+n.id)
        return self.types[n.id]
    def indexed(self,n):
        indices=[];node=n
        while isinstance(node,ast.Subscript):
            indices.append(node.slice);node=node.value
        if not isinstance(node,ast.Name):self.fail(n,'invalid array base')
        t=self.ident(node)
        if not isinstance(t,tuple) or t[0]!='array' or len(t[2])!=len(indices):self.fail(n,'array rank mismatch')
        idx=0
        for dim,x in zip(t[2],reversed(indices)):
            a,u=self.expr(x)
            if u!='int':self.fail(n,'integer index required')
            if self.checks:self.emit('check',a,dim)
            idx=self.compute('+',self.compute('*',idx,dim),a)
        width=8 if t[1]=='float' else 4
        return node.id,self.compute('*',idx,width),t[1]
    def expr(self,n):
        if isinstance(n,ast.Constant) and type(n.value) in (int,float,bool):
            return n.value,{int:'int',float:'float',bool:'bool'}[type(n.value)]
        if isinstance(n,ast.Name):return n.id,self.ident(n)
        if isinstance(n,ast.Subscript):
            a,b,t=self.indexed(n);return self.compute('load',a,b),t
        if isinstance(n,ast.UnaryOp) and isinstance(n.op,ast.USub):
            a,t=self.expr(n.operand)
            if t not in ('int','float'):self.fail(n,'invalid negation')
            return self.compute('neg',a),t
        if isinstance(n,ast.BinOp) and type(n.op) in OPS:
            a,t=self.expr(n.left);b,u=self.expr(n.right)
            if t not in ('int','float') or u not in ('int','float'):self.fail(n,'arithmetic type mismatch')
            op=OPS[type(n.op)]
            if 'float' in (t,u) or op=='/':a,b,t=self.widen(a,t),self.widen(b,u),'float'
            return self.compute(op,a,b),t
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and not n.keywords:
            name=n.func.id
            if name in ('addr','deref') and len(n.args)==1:
                a,t=self.expr(n.args[0])
                if name=='addr' and isinstance(n.args[0],ast.Name):return self.compute('addr',a,cached=False),('ptr',t)
                if name=='deref' and isinstance(t,tuple) and t[0]=='ptr':return self.compute('deref',a,cached=False),t[1]
                self.fail(n,'invalid pointer operand')
            if name not in self.functions and name!='tick':self.fail(n,'unknown procedure '+name)
            args,result=self.functions[name][1:] if name!='tick' else ((), 'int')
            if len(args)!=len(n.args):self.fail(n,'wrong number of arguments')
            stash=[None]*len(args)
            indexes=range(len(args)-1,-1,-1) if self.reverse else range(len(args))
            for i in indexes:
                a,t=self.expr(n.args[i]);dst=self.temp();self.emit('copy',a,None,dst);stash[i]=dst
                self.log.append(('argument evaluated',name,i,dst))
            for a in stash:self.emit('param',a)
            self.log.append(('argument queue',name,stash,len(stash)))
            d=self.temp() if result!='void' else None
            self.emit('call',name,len(stash),d);self.cache.clear();return d,result
        self.fail(n,'unsupported expression')
    def boolean(self,n):
        self.cache.clear()
        if isinstance(n,ast.UnaryOp) and isinstance(n.op,ast.Not):
            t,f=self.boolean(n.operand); t,f=f,t
        elif isinstance(n,ast.BoolOp):
            t,f=self.boolean(n.values[0])
            for rhs in n.values[1:]:
                is_and=isinstance(n.op,ast.And)
                if not (self.broken and not is_and):self.patch(t if is_and else f,len(self.q))
                u,v=self.boolean(rhs)
                t,f=(u,f+v) if is_and else (t+u,v)
        elif isinstance(n,ast.Compare) and len(n.ops)==1 and type(n.ops[0]) in OPS:
            a,_=self.expr(n.left);b,_=self.expr(n.comparators[0])
            t=[self.emit('if'+OPS[type(n.ops[0])],a,b)]
            f=[self.emit('jump')]
        else:
            a,u=self.expr(n)
            if u!='bool':self.fail(n,'Boolean condition required')
            t=[self.emit('if',a)];f=[self.emit('jump')]
        self.log.append(('boolean lists',n.lineno,t,f)); return t,f
    def block(self,body):
        for n in body:
            self.cache.clear()
            before=len(self.q);self.stmt(n)
            self.log.append(('statement nextlist',n.lineno,before,[]))
    def stmt(self,n):
        if isinstance(n,ast.AnnAssign) and isinstance(n.target,ast.Name):
            name=n.target.id;t=annotation(n.annotation)
            if name in self.types:self.fail(n,'duplicate '+name)
            self.types[name]=t
            self.emit('array' if isinstance(t,tuple) and t[0]=='array' else 'copy', {} if isinstance(t,tuple) and t[0]=='array' else 0,None,name)
            if n.value is not None:self.store(n.target,n.value)
        elif isinstance(n,ast.Assign) and len(n.targets)==1:self.store(n.targets[0],n.value)
        elif isinstance(n,ast.If):
            t,f=self.boolean(n.test);self.patch(t,len(self.q));self.block(n.body)
            if n.orelse:
                exit=[self.emit('jump')];self.patch(f,len(self.q));self.block(n.orelse)
                self.patch(exit,len(self.q))
            else:self.patch(f,len(self.q))
        elif isinstance(n,ast.While) and not n.orelse:
            head=len(self.q);t,f=self.boolean(n.test);self.patch(t,len(self.q))
            self.loop(n.body,head)
            self.emit('jump',d=head);self.patch(f,len(self.q));self.endloop()
        elif isinstance(n,ast.With) and len(n.items)==1:
            ctx=n.items[0].context_expr
            if not isinstance(ctx,ast.Call) or not isinstance(ctx.func,ast.Name) or ctx.func.id!='do' or len(ctx.args)!=1:self.fail(n,'expected with do(condition)')
            head=len(self.q);self.loop(n.body,None)
            self.patch(self.loops[-1][1],len(self.q))
            t,f=self.boolean(ctx.args[0]);self.patch(t,head);self.patch(f,len(self.q));self.endloop()
        elif isinstance(n,ast.For) and not n.orelse and isinstance(n.target,ast.Name):
            it=n.iter
            if not isinstance(it,ast.Call) or not isinstance(it.func,ast.Name) or it.func.id!='count' or len(it.args)!=3:self.fail(n,'expected count(start,end,step)')
            if self.ident(n.target)!='int':self.fail(n,'integer counter required')
            vals=[]
            for atom in it.args:
                x,t=self.expr(atom)
                if t!='int':self.fail(n,'integer loop parameter required')
                temp=self.temp();self.emit('copy',x,None,temp);vals.append(temp)
            lo,hi,step=vals;i=n.target.id
            self.emit('nonzero',step);self.emit('copy',lo,None,i)
            head=len(self.q);neg=[self.emit('if<',step,0)]
            done=[self.emit('if>',i,hi)];run=[self.emit('jump')]
            self.patch(neg,len(self.q));done+=[self.emit('if<',i,hi)]
            self.patch(run,len(self.q));self.loop(n.body,None)
            self.patch(self.loops[-1][1],len(self.q))
            self.emit('+',i,step,i);self.emit('jump',d=head)
            self.patch(done,len(self.q));self.endloop()
        elif isinstance(n,(ast.Break,ast.Continue)):
            if not self.loops:self.fail(n,'loop control outside loop')
            j=self.emit('jump');self.loops[-1][isinstance(n,ast.Continue)].append(j)
        elif isinstance(n,ast.Match):
            a,_=self.expr(n.subject);beg=self.emit('jump');table={};default=None;ends=[]
            for case in n.cases:
                k=case.pattern
                if case.guard:self.fail(n,'case guard unsupported')
                if isinstance(k,ast.MatchValue):
                    try:v=ast.literal_eval(k.value)
                    except ValueError:self.fail(n,'integer case required')
                    if type(v)!=int or v in table:self.fail(n,'invalid or duplicate case')
                    table[v]=len(self.q)
                elif isinstance(k,ast.MatchAs) and k.name is None and default is None:default=len(self.q)
                else:self.fail(n,'invalid case')
                self.block(case.body);ends.append(self.emit('jump'))
            if default is None:self.fail(n,'missing default')
            self.patch([beg],len(self.q))
            for v,d in table.items():self.emit('if==',a,v,d)
            self.emit('jump',d=default);self.patch(ends,len(self.q))
        elif isinstance(n,ast.Return):
            a,t=self.expr(n.value) if n.value else (None,'void')
            if t=='int' and self.return_type=='float':a,t=self.widen(a,t),'float'
            if self.return_type!=t:self.fail(n,'return type mismatch')
            self.emit('return',a)
        elif isinstance(n,ast.Expr) and isinstance(n.value,ast.Call):self.expr(n.value)
        elif isinstance(n,ast.Pass):pass
        else:self.fail(n,'unsupported statement')
    def store(self,d,n):
        a,t=self.expr(n)
        if isinstance(d,ast.Name): target=self.ident(d)
        elif isinstance(d,ast.Subscript): base,idx,target=self.indexed(d)
        else:self.fail(d,'invalid assignment target')
        if target=='float' and t=='int':a,t=self.widen(a,t),'float'
        if t!=target or isinstance(t,tuple) and t[0]=='array':self.fail(n,'assignment type mismatch')
        if isinstance(d,ast.Name):self.emit('copy',a,None,d.id)
        else:self.emit('store',a,idx,base)
    def loop(self,body,continue_target):
        self.loops.append(([],[]));self.block(body)
        if continue_target is not None:self.patch(self.loops[-1][1],continue_target)
    def endloop(self):
        b,c=self.loops.pop();self.patch(b,len(self.q));self.log.append(('loop lists',b,c))
    def compile(self,source):
        try:body=ast.parse(source).body
        except SyntaxError as e:raise ValueError(f'line {e.lineno}: {e.msg}') from e
        defs=[n for n in body if isinstance(n,ast.FunctionDef)]
        for n in defs:
            if n.name in self.functions:self.fail(n,'duplicate procedure')
            if n.args.defaults or n.args.kwonlyargs or n.args.vararg or n.args.kwarg or n.args.posonlyargs or n.decorator_list:
                self.fail(n,'fixed positional parameters required')
            self.functions[n.name]=(None,tuple(a.arg for a in n.args.args),annotation(n.returns) if n.returns else 'int')
        main=[n for n in body if not isinstance(n,ast.FunctionDef)]
        if any(isinstance(n,ast.Return) for n in main):self.fail(main[0],'return outside procedure')
        self.return_type='void';self.block(main);self.emit('halt')
        saved=self.types
        for n in defs:
            _,params,r=self.functions[n.name]
            self.functions[n.name]=(len(self.q),params,r)
            self.types={a.arg:annotation(a.annotation) if a.annotation else 'int' for a in n.args.args}
            self.return_type=r;self.block(n.body)
            self.emit('return' if r=='void' else 'trap')
        self.types=saved
        validate(self.q)
        return Code(self.q,self.log,self.functions,self.n)

def annotation(n):
    if isinstance(n,ast.Name) and n.id in ('int','float','bool','void'):return n.id
    if isinstance(n,ast.Subscript) and isinstance(n.value,ast.Name):
        kind=n.value.id
        if kind=='ptr': return ('ptr',annotation(n.slice))
        if kind=='array' and isinstance(n.slice,ast.Tuple):
            t,*dims=n.slice.elts
            if annotation(t) in ('int','float') and dims and all(isinstance(x,ast.Constant) and type(x.value)==int and x.value>0 for x in dims):
                return ('array',annotation(t),tuple(x.value for x in dims))
    raise ValueError(f'line {getattr(n,"lineno",0)}: invalid type')

def validate(q):
    for i,(o,a,b,d) in enumerate(q):
        if o=='jump' or o.startswith('if'):
            if type(d)!=int or not 0<=d<len(q):raise ValueError(f'invalid target at Q{i}: {d}')

def execute(code,initial=None):
    ticks=0; pc=0; env=dict(initial or {}); frames=[]; args=[]
    def get(x):return env[x] if isinstance(x,str) else x
    for _ in range(1000000):
        o,a,b,d=code.quads[pc];pc+=1
        if o=='halt':return env
        if o=='jump':pc=d
        elif o=='if':
            if get(a):pc=d
        elif o.startswith('if'):
            if RUN[o[2:]](get(a),get(b)):pc=d
        elif o in RUN:env[d]=RUN[o](get(a),get(b))
        elif o=='copy':env[d]=get(a)
        elif o=='float':env[d]=float(get(a))
        elif o=='neg':env[d]=-get(a)
        elif o=='array':env[d]={}
        elif o=='load':env[d]=get(a).get(get(b),0)
        elif o=='store':env[d][get(b)]=get(a)
        elif o=='addr':env[d]=(env,a)
        elif o=='deref': frame,name=get(a);env[d]=frame[name]
        elif o=='check':
            if not 0<=get(a)<b:raise ValueError('array bounds')
        elif o=='nonzero':
            if not get(a):raise ValueError('zero STEP')
        elif o=='param':args.append(get(a))
        elif o=='call':
            argv=args[-b:] if b else []
            if b:del args[-b:]
            if a=='tick':ticks+=1;env[d]=ticks
            else:
                target,params,_=code.functions[a]
                frames.append((pc,env,d)); pc=target;env=dict(zip(params,argv))
        elif o=='return':
            v=get(a);pc,env,d=frames.pop()
            if d is not None:env[d]=v
        elif o=='trap':raise ValueError('missing return')
        else:raise AssertionError(o)
    raise ValueError('execution step limit')
