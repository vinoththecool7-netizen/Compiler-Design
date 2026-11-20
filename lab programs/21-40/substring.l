%%
[a-z A-Z]+                     {
    for (size_t i = 0; i + 2 < (size_t)yyleng; ++i) {
        if ((yytext[i] == 'a') && (yytext[i + 1] == 'b') && (yytext[i + 2] == 'c')) {
            yytext[i] = 'A';
            yytext[i + 1] = 'B';
            yytext[i + 2] = 'C';
        }
    }
    printf("%s", yytext);
}
.                              { ECHO; }
\n                             { printf("%s", yytext); }
%%

int main(void) { yylex(); }
int yywrap(void) { return 1; }
