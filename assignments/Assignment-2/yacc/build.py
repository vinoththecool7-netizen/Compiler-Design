"""Emit and compile three YACC variants and two isolated conflict examples."""
from pathlib import Path
import os,re,subprocess
root=Path(__file__).resolve().parent
e=root.parent/'evidence'; build=root/'build'
build.mkdir(exist_ok=True)

header=r'''%{
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int yylex(void);
static void yyerror(const char *s);
static int errors;
static char *node(const char *op,char *a,char *b,char *c);
%}
%union { char *text; }
%token <text> ID NUM
%token LET IF ELSE AND OR EQ
%type <text> stmt expr
%destructor { free($$); } ID NUM stmt expr
'''
body=r'''
%%
program: /* empty */ | program stmt { if ($2) { puts($2); free($2); } };
stmt: LET ID ';' { $$=node("let",$2,NULL,NULL); }
    | ID '=' expr ';' { $$=node("assign",$1,$3,NULL); }
    | IF '(' expr ')' stmt ELSE stmt { $$=node("if",$3,$5,$7); }
    | error ';' { yyerrok; $$=NULL; }
    ;
'''
end=r'''
%%
static char *node(const char *op,char *a,char *b,char *c) {
    int n=snprintf(NULL,0,"(%s%s%s%s%s%s%s)",op,a?" ":"",a?a:"",
                   b?" ":"",b?b:"",c?" ":"",c?c:"");
    char *p=malloc((size_t)n+1);
    if (!p) exit(2);
    snprintf(p,(size_t)n+1,"(%s%s%s%s%s%s%s)",op,a?" ":"",a?a:"",
              b?" ":"",b?b:"",c?" ":"",c?c:"");
    free(a); free(b); free(c); return p;
}
static void yyerror(const char *s) { ++errors; fprintf(stderr,"%s\n",s); }
int main(void) { int r=yyparse(); printf("messages=%d\n",errors); return r || errors; }
'''
ops=[('OR','||'),('AND','&&'),('EQ','=='),("'<'",'<'),("'+'",'+'),("'-'",'-'),("'*'",'*'),("'/'",'/')]
def action(tok,op, a='expr',b='expr'):
    return f'{a} {tok} {b} {{ $$=node("{op}",$1,$3,NULL); }}'
atom="""atom: ID { $$=$1; } | NUM { $$=$1; } | '(' expr ')' { $$=$2; };\n"""
left=header+body+'expr: '+ '\n | '.join(action(t,o) for t,o in ops)+"\n | '(' expr ')' { $$=$2; } | ID { $$=$1; } | NUM { $$=$1; };\n"+end
prec=header+"""%left OR
%left AND
%nonassoc EQ '<'
%left '+' '-'
%left '*' '/'
%right UMINUS
"""+body+'expr: '+ '\n | '.join(action(t,o) for t,o in ops)+"""\n | '-' expr %prec UMINUS { $$=node("neg",$2,NULL,NULL); }
 | '(' expr ')' { $$=$2; } | ID { $$=$1; } | NUM { $$=$1; };\n"""+end
levels=[('expr','andexpr',ops[:1]),('andexpr','cmp',ops[1:2]),('cmp','sum',ops[2:4]),
        ('sum','product',ops[4:6]),('product','unary',ops[6:])]
rules=''
for a,b,choices in levels:
    rules+=a+f': {b} {{ $$=$1; }} | '+' | '.join(
        action(t,o,b if a=='cmp' else a,b) for t,o in choices)+';\n'
rewrite=header.replace("ID NUM stmt expr\n","ID NUM stmt expr andexpr cmp sum product unary atom\n")+'%type <text> andexpr cmp sum product unary atom\n'+body+rules+"""unary: '-' unary { $$=node("neg",$2,NULL,NULL); } | atom { $$=$1; };\n"""+atom+end
# Isolate dangling else without arithmetic conflicts.
dang=rewrite.replace("    | IF '(' expr ')' stmt ELSE stmt",'''    | IF '(' expr ')' stmt { $$=node("if",$3,$5,NULL); }
    | IF '(' expr ')' stmt ELSE stmt''')
rr=header.replace("ID NUM stmt expr","ID NUM stmt a b").replace('%type <text> stmt expr','%type <text> stmt a b')+'''
%%
program: stmt { puts($1); free($1); };
stmt: a { $$=$1; } | b { $$=$1; };
a: ID { $$=node("first",$1,NULL,NULL); };
b: ID { $$=node("second",$1,NULL,NULL); };
'''+end
variants={'ambiguous':left,'precedence':prec,'rewritten':rewrite,'dangling':dang,'reduce_reduce':rr}
def run(args,cwd,**opts):
    return subprocess.run(args,cwd=cwd,text=True,capture_output=True,**opts)
for name,source in variants.items():
    d=build/name;d.mkdir(exist_ok=True)
    (d/'parser.y').write_text(source)
    y=run(['bison','-dv','-o','parser.c','parser.y'],d,check=True)
    (e/f'q6-{name}.output').write_text((d/'parser.output').read_text())
    x=run(['flex','-o','scanner.c',str(root/'scanner.l')],d,check=True)
    run(['cc','-D_POSIX_C_SOURCE=200809L','parser.c','scanner.c','-o','billing'],d,check=True)
    states=len(re.findall(r'^state [0-9]+$',(d/'parser.output').read_text(),re.M | re.I))
    ntab=re.search(r'#define YYLAST\s+(\d+)',(d/'parser.c').read_text())[1]
    print(f'{name}: states={states}; YYLAST+1={int(ntab)+1}; {y.stderr.strip() or "no conflicts reported"}')
    if name=='ambiguous':assert re.search(r'64 shift/reduce',y.stderr)
    if name=='dangling':assert re.search(r'1 shift/reduce',y.stderr)
    if name=='reduce_reduce':assert re.search(r'1 reduce/reduce',y.stderr)
samples={
'precedence':['x = a * b + c;', 'let charge; charge = base + units * rate - discount;',
              'x = -2 * 3; if (x < 0 && x == 1 || n) x = 2; else x = 3;',
              'x = + ; y = ; let ; good = 4;'],
'rewritten':['let charge; charge = base + units * rate - discount;',
             'x = -2 * 3; if (x < 0 && x == 1 || n) x = 2; else x = 3;'],
'ambiguous':['x = a * b + c;'],
'dangling':['if (a) if (b) x=1; else x=2;'],
'reduce_reduce':['rate'],
}
results={}
for name,ss in samples.items():
    for s in ss:
        r=run(['./billing'],build/name,input=s)
        print(f'\n{name} input: {s}\n{r.stdout}{r.stderr}',end='')
        results[name,s]=r.stdout
        if s.startswith('x = +'):
            assert r.returncode and 'messages=3' in r.stdout and '(assign good 4)' in r.stdout
        else:assert not r.returncode
assert '(assign x (* a (+ b c)))' in results['ambiguous','x = a * b + c;']
for s in samples['rewritten']:assert results['precedence',s]==results['rewritten',s]
