%%
[A-Z]+                         { printf("%s is a capital word\n", yytext); }
[A-Za-z]+                      {}
.|\n                           {}
%%

int main(void) {
    printf("Enter String :\n");
    yylex();
}
int yywrap(void) { return 1; }
