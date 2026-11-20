%%
[\t ]+                         {}
[0-9]+|[0-9]*\.[0-9]+          { printf("\n%s is NUMBER", yytext); }
#.*                            { printf("\n%s is COMMENT", yytext); }
[a-zA-Z]+                      { printf("\n%s is WORD", yytext); }
\n                             { ECHO; }
%%

int main(void) {
    while (yylex())
        ;
}

int yywrap(void) { return 1; }
