#include "mini.h"
#include "lr.h"
#include <stdlib.h>
#include <string.h>

int checks(void);

static char *read_file(const char *path) {
    FILE *f=fopen(path,"rb");
    if (!f) { perror(path); return NULL; }
    if (fseek(f,0,SEEK_END)) { perror(path); fclose(f); return NULL; }
    long n=ftell(f);
    if (n<0 || fseek(f,0,SEEK_SET)) { perror(path); fclose(f); return NULL; }
    char *text=malloc((size_t)n+1);
    if (!text) { fputs("out of memory\n",stderr); fclose(f); return NULL; }
    if (fread(text,1,(size_t)n,f)!=(size_t)n || memchr(text,0,(size_t)n)) {
        fprintf(stderr,"cannot read text file %s\n",path);
        free(text); fclose(f); return NULL;
    }
    text[n]=0;
    fclose(f);
    return text;
}

int main(int argc, char **argv) {
    if (argc==2 && !strcmp(argv[1],"check")) return checks();
    if (argc==3 && (!strcmp(argv[1],"mini") || !strcmp(argv[1],"two-pass"))) {
        char *source=read_file(argv[2]);
        if (!source) return 2;
        Mini m;
        bool ok=translate(&m,source,!strcmp(argv[1],"mini"));
        print_translation(stdout,&m);
        release(&m.arena);
        free(source);
        return ok ? 0 : 1;
    }
    if (argc==3) {
        const char *const modes[]={"expr","postfix","ast","right","decl","marker"};
        for (size_t i=0;i<sizeof modes/sizeof *modes;++i) {
            if (strcmp(argv[1],modes[i])) continue;
            LR lr;
            bool ok=exercise(&lr,(Exercise)i,argv[2],i==MARKER ? stdout : NULL);
            if (ok) {
                tree(stdout,lr.root,0);
                if (i==BUILD_AST) { ast(stdout,lr.root->ast); puts(""); }
                if (i==POSTFIX) {
                    for (size_t j=0;j<lr.actions;++j)
                        printf("%s%s",j ? " " : "",lr.postfix[j]);
                    puts("");
                }
            } else fprintf(stderr,"%s\n",lr.error);
            if (i==DECLARE || i==MARKER) { print_symbols(stdout,&lr.symbols); puts(""); }
            release(&lr.arena);
            return ok ? 0 : 1;
        }
    }
    fputs("usage: assignment3 check | (mini|two-pass) FILE\n"
          "       assignment3 (expr|postfix|ast|right|decl|marker) INPUT\n",stderr);
    return 2;
}
