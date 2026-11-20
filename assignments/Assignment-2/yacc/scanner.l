%option noyywrap noinput nounput
%{
#include <stdlib.h>
#include <string.h>
#include "parser.h"
%}
%%
"let"                 return LET;
"if"                  return IF;
"else"                return ELSE;
"&&"                  return AND;
"||"                  return OR;
"=="                  return EQ;
[0-9]+|[A-Za-z_][A-Za-z_0-9]* {
    yylval.text = strdup(yytext);
    return yytext[0]>='0' && yytext[0]<='9' ? NUM : ID;
}
[ \t\r\n]+            ;
.                      return (unsigned char)yytext[0];
%%
