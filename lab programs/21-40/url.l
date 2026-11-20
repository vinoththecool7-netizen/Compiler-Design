%%
((http)|(ftp))s?:\/\/[a-zA-Z0-9](.[a-z])+(.[a-zA-Z0-9+=?]*)* { printf("\nURL Valid\n"); }
.+                             { printf("\nURL Invalid\n"); }
%%

int main(void) {
    printf("\nEnter URL : ");
    yylex();
    printf("\n");
}
int yywrap(void) { return 1; }
