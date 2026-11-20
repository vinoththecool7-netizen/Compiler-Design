"""Compare error recovery policies on a common statement grammar."""
from parsing import BASE, EXPR, SLR, sets, lex, write, csvfile

PREFIX={'P':[('S','P'),()], 'S':[('water','E',';'),('if','(','E','==','E',')','water','E',';')]}
G={**PREFIX,**EXPR}
first,follow,seq,_=sets(G,'P')
table={}
for a,bs in G.items():
    for b in bs:
        f=seq(b)
        for t in (f-{'ε'}) | (follow[a] if 'ε' in f else set()):
            assert (a,t) not in table
            table[a,t]=b
lr=SLR({**PREFIX,**BASE},'P')

def tokens(source):
    out=[]
    for kind,word in lex(source):
        if word in {'if','water',';'}:kind=word
        if out and out[-1][0]=='=' and word=='=':
            out.pop();kind=word='=='
        out.append((kind,word))
    return out

def parse(ts, policy, trace=False):
    stack=['$','P'];i=0; messages=[]; rows=[]
    while stack:
        a=stack[-1]; t,word=ts[i]
        before=f'{" ".join(stack)} | {word} | ' if trace else ''
        if a==t: stack.pop();i+=1; act='match'
        elif (a,t) in table:
            stack.pop()
            stack.extend(reversed(table[a,t]))
            act=f'expand {a}'
        else:
            messages.append((i,a,word))
            if policy=='stop':
                rows.append(before+'stop');break
            if policy in ('phrase','island') and t=='water' and a in {'R','U'} and ';' in follow[a]:
                # Missing final statement terminator also prevents nullable-tail reductions.
                ts=[*ts[:i],(';','<inserted ;>'),*ts[i:]]
                act='insert ; before statement starter'
            elif policy in ('phrase','island') and a in {'F','T'} and t in {')',';'}:
                stack.pop()
                act='insert error operand and pop the offending nonterminal'
            elif policy=='island':
                # Model S -> error ';' by unwinding to the next P frame.
                while stack and stack[-1]!='P':stack.pop()
                while ts[i][0] not in {';','$'}:i+=1
                if ts[i][0]==';':i+=1
                act='recover statement at delimiter'
            elif a in G:
                if t in follow[a] or t=='$':
                    stack.pop();act=f'sync pop {a}'
                else:
                    i+=1;act='discard lookahead'
            elif t=='$' or a==';' and t in {'water','if'}:
                stack.pop();act=f'insert {a}'
            else:
                i+=1;act='discard lookahead'
        if trace:rows.append(before+act)
    return messages,rows

CASES=[
('missing semicolon','water 1 water 2;',2),
('missing operand','water (x+); water 2;',4),
('extra closing parenthesis','water x); water 2;',2),
('assignment in condition','if (x = 1) water 2; water 3;',3),
('misspelt keyword','watr 1; water 2;',0),
('missing closing parenthesis','water (x; water 2;',3),
]

def main():
    rows=[]; traces=[]
    for name,source,expected in CASES:
        ts=tokens(source); stop, _=parse(ts,'stop')
        l=lr.trace([x for x,_ in ts]); tail=l[-1].split(' | ')
        lr_at=len(ts)-len(tail[1].split())
        for policy in ('panic','phrase','island'):
            messages, trace=parse(ts,policy,True)
            assert messages
            rows.append([name,source,expected,stop[0][0],lr_at,stop[0][1],tail[0].split()[-1],policy,len(messages),
                         len(messages)-1, 'yes' if messages[0][0]==expected else 'no'])
            traces.extend([name+' / '+policy,*trace,''])
    csvfile('q5-results.csv',['case','source','fault_index','LL_index','LR_index','LL_expected','LR_state',
              'mode','messages','cascades','first_at_fault'],rows)
    write('q5-traces.txt',traces)
    write('q5-sync.txt',[f'{a}: {" ".join(sorted(follow[a]))}' for a in G])
    for name,s,_ in CASES[:2]:
        ts=tokens(s); bad=parse(ts,'stop')[0][0][0]
        restart=1+sum(bool(parse(ts[i:],'stop')[0]) for i in range(bad+1,len(ts)-1))
        print(f'{name}: stop=1; naive per-token restarts={restart}')

    stream='water '+'('*10000+'x'+')'*10000+'; water (x+); watr 1; water 2;'
    ts=tokens(stream)
    errors,_=parse(ts,'island')
    assert [(a,w) for _,a,w in errors]==[('T',')'),('P','watr')]
    write('q7-mixed.txt',[f'Tokens excluding EOF: {len(ts)-1}',f'Errors: {errors}',
                          'Consumed the entire stream with two reported faults.'])

if __name__=='__main__':main()
