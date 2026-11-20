%{
int nmacro, nheader;
%}

%%
^#define                       { nmacro++; }
^#include                      { nheader++; }
.|\n                           {}
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
    printf("Number of macros defined = %d\n", nmacro);
    printf("Number of header files included = %d\n", nheader);
    fclose(yyin);
}
