%{
int tags;
%}

%%
"<"[^>]*>                      {
    tags++;
    printf("%s \n", yytext);
}
.|\n                           {}
%%

int yywrap(void) { return 1; }
int main(void) {
    FILE *f;
    char file[256];
    printf("Enter File Name : ");
    if (scanf("%255s", file) != 1) {
        return 1;
    }
    f = fopen(file, "r");
    if (!f) {
        perror(file);
        return 1;
    }
    yyin = f;
    yylex();
    printf("\n Number of html tags: %d", tags);
    fclose(yyin);
}
