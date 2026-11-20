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
%destructor { free($$); } ID NUM stmt expr
%left OR
%left AND
%nonassoc EQ '<'
%left '+' '-'
%left '*' '/'
%right UMINUS

%%
program: /* empty */ | program stmt { if ($2) { puts($2); free($2); } };
stmt: LET ID ';' { $$=node("let",$2,NULL,NULL); }
    | ID '=' expr ';' { $$=node("assign",$1,$3,NULL); }
    | IF '(' expr ')' stmt ELSE stmt { $$=node("if",$3,$5,$7); }
    | error ';' { yyerrok; $$=NULL; }
    ;
expr: expr OR expr { $$=node("||",$1,$3,NULL); }
 | expr AND expr { $$=node("&&",$1,$3,NULL); }
 | expr EQ expr { $$=node("==",$1,$3,NULL); }
 | expr '<' expr { $$=node("<",$1,$3,NULL); }
 | expr '+' expr { $$=node("+",$1,$3,NULL); }
 | expr '-' expr { $$=node("-",$1,$3,NULL); }
 | expr '*' expr { $$=node("*",$1,$3,NULL); }
 | expr '/' expr { $$=node("/",$1,$3,NULL); }
 | '-' expr %prec UMINUS { $$=node("neg",$2,NULL,NULL); }
 | '(' expr ')' { $$=$2; } | ID { $$=$1; } | NUM { $$=$1; };

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
