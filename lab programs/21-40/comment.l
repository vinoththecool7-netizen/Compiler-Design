%{
int com = 0;
%}
%x COMMENT

%%
"/*"                           { BEGIN COMMENT; }
<COMMENT>"*/"                  {
    BEGIN 0;
    com++;
}
<COMMENT>\n                    { ECHO; }
<COMMENT>.                     {}
\/\/.*                         { com++; }
.|\n                           { fprintf(yyout, "%s", yytext); }
%%

int main(int argc, char *argv[]) {
    if (argc != 3) {
        printf("usage : a.exe input.c output.c\n");
        return 1;
    }
    yyin = fopen(argv[1], "r");
    if (!yyin) {
        perror(argv[1]);
        return 1;
    }
    yyout = fopen(argv[2], "w");
    if (!yyout) {
        perror(argv[2]);
        fclose(yyin);
        return 1;
    }
    yylex();
    printf("\n number of comments are = %d\n", com);
    fclose(yyin);
    fclose(yyout);
    return 0;
}
int yywrap(void) { return 1; }
