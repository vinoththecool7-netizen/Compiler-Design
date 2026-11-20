%{
#include "lr.h"
#include <string.h>
static int yylex(void *value, LR *lr);
static void yyerror(LR *lr, const char *message);
%}
%pure-parser
%parse-param {LR *lr}
%lex-param {LR *lr}
%union { Node *n; }
%token ARITH ASSIGN RIGHT DECL MARK
%token <n> ID NUM INT_T FLOAT_T PLUS MINUS TIMES DIV LP RP EQ COMMA SEMI BAD
%type <n> E T F RE RT RF D Ty L MD M ML S
%start Input
%%
Input: ARITH E { lr->root=$2; }
     | ASSIGN S { lr->root=$2; }
     | RIGHT RE { lr->root=$2; }
     | DECL D { lr->root=$2; }
     | DECL D SEMI { lr->root=$2; }
     | MARK MD { lr->root=$2; }
     | MARK MD SEMI { lr->root=$2; }
     ;
S: ID EQ E { $$=binary(lr,"S",$1,$2,$3); };
E: E PLUS T { $$=binary(lr,"E",$1,$2,$3); }
 | E MINUS T { $$=binary(lr,"E",$1,$2,$3); }
 | T { $$=forward(lr,"E",$1); }
 ;
T: T TIMES F { $$=binary(lr,"T",$1,$2,$3); }
 | T DIV F { $$=binary(lr,"T",$1,$2,$3); }
 | F { $$=forward(lr,"T",$1); }
 ;
F: LP E RP { $$=group(lr,$1,$2,$3); }
 | NUM { $$=factor(lr,$1); }
 | ID { $$=factor(lr,$1); }
 ;
RE: RT PLUS RE { $$=binary(lr,"E",$1,$2,$3); }
  | RT MINUS RE { $$=binary(lr,"E",$1,$2,$3); }
  | RT { $$=forward(lr,"E",$1); }
  ;
RT: RF TIMES RT { $$=binary(lr,"T",$1,$2,$3); }
  | RF DIV RT { $$=binary(lr,"T",$1,$2,$3); }
  | RF { $$=forward(lr,"T",$1); }
  ;
RF: LP RE RP { $$=group(lr,$1,$2,$3); }
  | NUM { $$=factor(lr,$1); }
  | ID { $$=factor(lr,$1); }
  ;
D: Ty L { $$=node(lr,"D",$1,$2,NULL); };
Ty: INT_T { $$=forward(lr,"T",$1); $$->type=TY_INT; }
  | FLOAT_T { $$=forward(lr,"T",$1); $$->type=TY_FLOAT; }
  ;
L: L COMMA ID { $$=node(lr,"L",$1,$2,$3); }
 | ID { $$=node(lr,"L",$1,NULL,NULL); }
 ;
MD: Ty M ML {
    $$=node(lr,"D",$1,$2,$3);
    if (lr->trace) fprintf(lr->trace,"reduce D -> T M L         [T M L:%s] -> [D]\n",
                           type_name($3->type));
};
/* $0 is the preceding semantic stack entry, Ty, in this sole context. */
M: /* empty */ {
    $$=node(lr,"M",NULL,NULL,NULL);
    $$->type=$<n>0->type;
    if (lr->trace) fprintf(lr->trace,"reduce M -> epsilon       [T:%s] -> [T M:%s]\n",
                           type_name($$->type),type_name($$->type));
};
/* In ML -> ID, $0 is the marker immediately below the RHS. */
ML: ID {
    $$=add_name(lr,NULL,NULL,$1,$<n>0->type);
    if (lr->trace) fprintf(lr->trace,"reduce L -> id            [T M id:%s] -> [T M L:%s]\n",
                           $1->text,type_name($$->type));
}
| ML COMMA ID {
    $$=add_name(lr,$1,$2,$3,$1->type);
    if (lr->trace) fprintf(lr->trace,"reduce L -> L , id        [T M L , id:%s] -> [T M L:%s]\n",
                           $3->text,type_name($$->type));
}
;
%%
static int yylex(void *value, LR *lr) {
    YYSTYPE *y=value;
    if (!lr->started) {
        lr->started=true;
        switch (lr->mode) {
            case BUILD_AST: return ASSIGN;
            case RIGHT_ASSOC: return RIGHT;
            case DECLARE: return DECL;
            case MARKER: return MARK;
            default: return ARITH;
        }
    }
    Token t=lex(&lr->lexer);
    if (!t.kind) return 0;
    const char *label=t.text;
    int symbol;
    switch (t.kind) {
        case NAME: label="id"; symbol=ID; break;
        case NUMBER: label="num"; symbol=NUM; break;
        case INT: symbol=INT_T; break;
        case FLOAT: symbol=FLOAT_T; break;
        case '+': symbol=PLUS; break;
        case '-': symbol=MINUS; break;
        case '*': symbol=TIMES; break;
        case '/': symbol=DIV; break;
        case '(': symbol=LP; break;
        case ')': symbol=RP; break;
        case '=': symbol=EQ; break;
        case ',': symbol=COMMA; break;
        case ';': symbol=SEMI; break;
        default: symbol=BAD; break;
    }
    y->n=leaf(lr,label,t.text);
    return symbol;
}
static void yyerror(LR *lr, const char *message) {
    if (!lr->error) lr->error=format(&lr->arena,"unexpected token near byte %zu (%s)",lr->lexer.pos,message);
}
