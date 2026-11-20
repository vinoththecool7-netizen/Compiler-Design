%{
int line_number;
%}

%%
.*\n                           { printf("%4d\t%s", ++line_number, yytext); }
.+                             { printf("%4d\t%s", ++line_number, yytext); }
%%

int yywrap(void) { return 1; }
int main(int argc, char *argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s INPUT_FILE\n", argv[0]);
        return 1;
    }
    yyin = fopen(argv[1], "r");
    if (!yyin) {
        perror(argv[1]);
        return 1;
    }
    yylex();
    fclose(yyin);
}
