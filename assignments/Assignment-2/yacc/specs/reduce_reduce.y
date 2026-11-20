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
%type <text> stmt a b
%destructor { free($$); } ID NUM stmt a b

%%
program: stmt { puts($1); free($1); };
stmt: a { $$=$1; } | b { $$=$1; };
a: ID { $$=node("first",$1,NULL,NULL); };
b: ID { $$=node("second",$1,NULL,NULL); };

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
