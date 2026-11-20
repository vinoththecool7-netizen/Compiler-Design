%%
[0-9]+                         { printf("\nValid digit \n"); }
.+                             { printf("\nInvalid digit\n"); }
%%

int yywrap(void) { return 1; }
int main(void) {
    yylex();
    return 0;
}
