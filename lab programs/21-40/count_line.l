%{
int nchar, nword, nline;
%}

%%
\n                             {
    nline++;
    nchar++;
}
[^ \t\n]+                      { nword++, nchar += yyleng; }
.                              { nchar++; }
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
    printf("Number of characters = %d\n", nchar);
    printf("Number of words = %d\n", nword);
    printf("Number of lines = %d\n", nline);
    fclose(yyin);
}
