%{
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
%destructor { free($$); } ID NUM stmt expr andexpr cmp sum product unary atom
%type <text> andexpr cmp sum product unary atom

%%
program: /* empty */ | program stmt { if ($2) { puts($2); free($2); } };
stmt: LET ID ';' { $$=node("let",$2,NULL,NULL); }
    | ID '=' expr ';' { $$=node("assign",$1,$3,NULL); }
    | IF '(' expr ')' stmt { $$=node("if",$3,$5,NULL); }
    | IF '(' expr ')' stmt ELSE stmt { $$=node("if",$3,$5,$7); }
    | error ';' { yyerrok; $$=NULL; }
    ;
expr: andexpr { $$=$1; } | expr OR andexpr { $$=node("||",$1,$3,NULL); };
andexpr: cmp { $$=$1; } | andexpr AND cmp { $$=node("&&",$1,$3,NULL); };
cmp: sum { $$=$1; } | sum EQ sum { $$=node("==",$1,$3,NULL); } | sum '<' sum { $$=node("<",$1,$3,NULL); };
sum: product { $$=$1; } | sum '+' product { $$=node("+",$1,$3,NULL); } | sum '-' product { $$=node("-",$1,$3,NULL); };
product: unary { $$=$1; } | product '*' unary { $$=node("*",$1,$3,NULL); } | product '/' unary { $$=node("/",$1,$3,NULL); };
unary: '-' unary { $$=node("neg",$2,NULL,NULL); } | atom { $$=$1; };
atom: ID { $$=$1; } | NUM { $$=$1; } | '(' expr ')' { $$=$2; };

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
