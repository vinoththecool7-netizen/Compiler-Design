#include "lr.h"
#include "graph.h"
#include "mini.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define CHECK(x) do { if (!(x)) { fprintf(stderr,"%s:%d: %s\n",__FILE__,__LINE__,#x); exit(1); } } while (0)
#define LENGTH(a) (sizeof(a)/sizeof *(a))

static FILE *capture(const char *name) {
    char path[256];
    snprintf(path,sizeof path,"evidence/%s",name);
    FILE *f=fopen(path,"w");
    if (!f) { perror(path); exit(2); }
    return f;
}

static void csv_text(FILE *f, const char *s) {
    fputc('"',f);
    for (;*s;++s) { if (*s=='"') fputc('"',f); fputc(*s,f); }
    fputc('"',f);
}

static void expression_checks(void) {
    const struct { const char *s; double value; const char *error; } cases[]={
        {"7",7,NULL},{"((2))",2,NULL},{"8-3-2",3,NULL},{"8/4/2",1,NULL},
        {"2+3*4",14,NULL},{"(2+3)*4",20,NULL},{"3*(4+5)-6/2",24,NULL},{"3/2",1.5,NULL},
        {"2+*3",0,"unexpected"},{"1/(2-2)",0,"division by zero"}
    };
    FILE *csv=capture("q1-tests.csv"), *log=capture("q1-trees.txt");
    fputs("input,expected,observed,nodes,height,attribute_instances\n",csv);
    for (size_t i=0;i<LENGTH(cases);++i) {
        LR lr;
        bool ok=exercise(&lr,EVALUATE,cases[i].s,NULL);
        csv_text(csv,cases[i].s);
        if (cases[i].error) {
            CHECK(!ok && strstr(lr.error,cases[i].error));
            fprintf(csv,",%s,",cases[i].error);
            csv_text(csv,lr.error);
            fputs(",,,\n",csv);
        } else {
            CHECK(ok && lr.root->has_value && lr.root->value==cases[i].value);
            fprintf(csv,",%.10g,%.10g,%zu,%zu,%zu\n",cases[i].value,lr.root->value,
                    lr.root->nodes,lr.root->height,lr.root->attributes);
            fprintf(log,"%s → %.10g; postfix",cases[i].s,lr.root->value);
            for (size_t j=0;j<lr.actions;++j) fprintf(log," %s",lr.postfix[j]);
            fputc('\n',log); tree(log,lr.root,0); fputc('\n',log);
        }
        release(&lr.arena);
    }
    fclose(csv); fclose(log);
    const struct { const char *s,*want; } postfix[]={
        {"a+b*(c-d)","a b c d - * +"},{"a+b*c","a b c * +"},{"a-b-c","a b - c -"},
        {"a/b/c","a b / c /"},{"(a+b)*c","a b + c *"},{"a*(b+c/d)","a b c d / + *"}
    };
    log=capture("q4-postfix.txt");
    for (size_t i=0;i<LENGTH(postfix);++i) {
        LR lr;
        CHECK(exercise(&lr,POSTFIX,postfix[i].s,NULL));
        char output[100]={0};
        size_t len=0;
        for (size_t j=0;j<lr.actions;++j) {
            int wrote=snprintf(output+len,sizeof output-len,"%s%s",j ? " " : "",lr.postfix[j]);
            CHECK(wrote>=0 && (size_t)wrote<sizeof output-len);
            len+=(size_t)wrote;
        }
        CHECK(!strcmp(output,postfix[i].want));
        fprintf(log,"%s → %s (%zu actions)\n",postfix[i].s,output,lr.actions);
        release(&lr.arena);
    }
    fclose(log);
    csv=capture("growth.csv");
    fputs("operands,expr_tokens,parse_nodes,attrs,left_height,right_height,postfix_actions,"
          "assignment_parse_nodes,assignment_ast_nodes\n",csv);
    for (size_t n=1;n<=64;n*=2) {
        char s[132]="a=";
        for (size_t i=0;i<n;++i) { s[2+2*i]='1'; if (i+1<n) s[3+2*i]='+'; }
        LR left,right,assignment;
        CHECK(exercise(&left,EVALUATE,s+2,NULL));
        CHECK(exercise(&right,RIGHT_ASSOC,s+2,NULL));
        CHECK(exercise(&assignment,BUILD_AST,s,NULL));
        CHECK(left.root->value==(double)n && right.root->value==(double)n && left.actions==2*n-1);
        size_t count=ast_nodes(assignment.root->ast);
        CHECK(count==2*n+1);
        fprintf(csv,"%zu,%zu,%zu,%zu,%zu,%zu,%zu,%zu,%zu\n",n,2*n-1,left.root->nodes,
            left.root->attributes,left.root->height,right.root->height,left.actions,assignment.root->nodes,count);
        release(&left.arena); release(&right.arena); release(&assignment.arena);
    }
    fclose(csv);
    LR left,right,assignment;
    CHECK(exercise(&left,EVALUATE,"2*3+4+5+6",NULL) && exercise(&right,RIGHT_ASSOC,"2*3+4+5+6",NULL));
    log=capture("q1-recursion.txt");
    fprintf(log,"2*3+4+5+6: left height=%zu, right height=%zu\n",left.root->height,right.root->height);
    fclose(log); release(&left.arena); release(&right.arena);
    CHECK(exercise(&assignment,BUILD_AST,"a=b+c*d",NULL));
    Ast *a=assignment.root->ast;
    CHECK(!strcmp(a->text,"=") && !strcmp(a->left->text,"a") && !strcmp(a->right->text,"+") &&
          !strcmp(a->right->left->text,"b") && !strcmp(a->right->right->text,"*") &&
          !strcmp(a->right->right->left->text,"c") && !strcmp(a->right->right->right->text,"d"));
    log=capture("q5-tree.txt"); tree(log,assignment.root,0); ast(log,a);
    fprintf(log,"\nparse nodes=%zu, AST nodes=%zu\n",assignment.root->nodes,ast_nodes(a));
    fclose(log); release(&assignment.arena);
}

static void declaration_checks(void) {
    const struct { const char *s,*error; size_t count; Type a,x; } cases[]={
        {"float a,b,c;",NULL,3,TY_FLOAT,TY_ERROR},{"int x,y;",NULL,2,TY_ERROR,TY_INT},
        {"int a,a;","duplicate a",1,TY_INT,TY_ERROR},{"float a,;","unexpected",0,TY_ERROR,TY_ERROR}
    };
    FILE *f=capture("q2-declarations.txt");
    for (size_t i=0;i<LENGTH(cases);++i) {
        LR lr;
        bool ok=exercise(&lr,DECLARE,cases[i].s,NULL);
        CHECK(ok==!cases[i].error && lr.symbols.count==cases[i].count);
        CHECK(lookup(&lr.symbols,"a")==cases[i].a && lookup(&lr.symbols,"x")==cases[i].x);
        if (i==0) CHECK(lookup(&lr.symbols,"b")==TY_FLOAT && lookup(&lr.symbols,"c")==TY_FLOAT);
        if (i==1) CHECK(lookup(&lr.symbols,"y")==TY_INT);
        if (ok) tree(f,lr.root,0);
        else { CHECK(strstr(lr.error,cases[i].error)); fprintf(f,"%s\n",lr.error); }
        fprintf(f,"%s => ",cases[i].s); print_symbols(f,&lr.symbols); fputs("\n\n",f);
        release(&lr.arena);
    }
    fclose(f);
    LR lr;
    f=capture("q6-marker.txt");
    CHECK(exercise(&lr,MARKER,"int x,y",f));
    CHECK(lookup(&lr.symbols,"x")==TY_INT && lookup(&lr.symbols,"y")==TY_INT);
    fclose(f); release(&lr.arena);
    CHECK(exercise(&lr,POSTFIX,"a+b*c-d",NULL));
    const char *stack[16];
    size_t depth=0, temps=0;
    const char *expected[]={"t1 = b * c","t2 = a + t1","t3 = t2 - d","x = t3"};
    f=capture("q6-tac.txt");
    for (size_t i=0;i<lr.actions;++i) {
        const char *s=lr.postfix[i];
        if (strlen(s)==1 && strchr("+-*/",*s)) {
            CHECK(depth>=2);
            const char *r=stack[--depth], *l=stack[--depth];
            const char *temp=format(&lr.arena,"t%zu",++temps);
            const char *line=format(&lr.arena,"%s = %s %s %s",temp,l,s,r);
            CHECK(temps<4 && !strcmp(line,expected[temps-1]));
            fprintf(f,"%s\n",line);
            stack[depth++]=temp;
        } else { CHECK(depth<LENGTH(stack)); stack[depth++]=s; }
    }
    CHECK(depth==1 && temps==3);
    const char *line=format(&lr.arena,"x = %s",stack[0]);
    CHECK(!strcmp(line,expected[3]));
    fprintf(f,"%s\n",line);
    fclose(f); release(&lr.arena);
}

static Value forward_value(Value c, const Value *args) { (void)c; return args[0]; }
static Value plus(Value c, const Value *args) { (void)c; return (Value){args[0].number+args[1].number,NULL}; }
static Value times(Value c, const Value *args) { (void)c; return (Value){args[0].number*args[1].number,NULL}; }
static Value binding(Value c, const Value *args) { (void)c; return (Value){args[1].number,args[0].text}; }
static void print_graph(FILE *f, const Equation *eq, size_t n, Value *values) {
    Value reverse[16];
    size_t order[16], completed;
    CHECK(n<=LENGTH(order));
    for (size_t mode=0;mode<2;++mode) {
        Value *v=mode ? reverse : values;
        CHECK(evaluate(eq,n,mode!=0,v,order,&completed)==GRAPH_OK && completed==n);
        fprintf(f,"Order %zu:",mode+1);
        for (size_t i=0;i<n;++i) fprintf(f,"%s%s",i ? " → " : " ",eq[order[i]].name);
        fputc('\n',f);
    }
    for (size_t i=0;i<n;++i) {
        CHECK(values[i].number==reverse[i].number && values[i].text==reverse[i].text);
        fprintf(f,"%s = %.10g%s%s\n",eq[i].name,values[i].number,values[i].text ? " " : "",
            values[i].text ? values[i].text : "");
    }
}

static void graph_checks(void) {
    const Equation expr[]={
        {"d2",0,NULL,NULL,{2,NULL}},{"d3",0,NULL,NULL,{3,NULL}},{"d4",0,NULL,NULL,{4,NULL}},
        {"F2",1,(size_t[]){0},forward_value,{0}},{"F3",1,(size_t[]){1},forward_value,{0}},
        {"F4",1,(size_t[]){2},forward_value,{0}},{"T2",1,(size_t[]){3},forward_value,{0}},
        {"T3",1,(size_t[]){4},forward_value,{0}},{"E2",1,(size_t[]){6},forward_value,{0}},
        {"T34",2,(size_t[]){7,5},times,{0}},{"E234",2,(size_t[]){8,9},plus,{0}}
    };
    const Equation decl[]={
        {"float",0,NULL,NULL,{TY_FLOAT,"float"}},{"T.type",1,(size_t[]){0},forward_value,{0}},
        {"Louter.in",1,(size_t[]){1},forward_value,{0}},
        {"Linner.in",1,(size_t[]){2},forward_value,{0}},
        {"a.entry",0,NULL,NULL,{0,"a"}},{"b.entry",0,NULL,NULL,{0,"b"}},
        {"install a",2,(size_t[]){4,3},binding,{0}},
        {"install b",3,(size_t[]){5,2,6},binding,{0}}
    };
    const Equation cycle[]={
        {"X.in",1,(size_t[]){1},forward_value,{0}},{"Y.out",1,(size_t[]){0},forward_value,{0}}
    };
    FILE *f=capture("q3-graphs.txt");
    Value v[16]; size_t order[2], done;
    print_graph(f,expr,LENGTH(expr),v); CHECK(v[10].number==14);
    fputc('\n',f);
    print_graph(f,decl,LENGTH(decl),v);
    CHECK(v[6].number==TY_FLOAT && !strcmp(v[6].text,"a"));
    CHECK(v[7].number==TY_FLOAT && !strcmp(v[7].text,"b"));
    CHECK(evaluate(cycle,LENGTH(cycle),false,v,order,&done)==GRAPH_CYCLE && done==0);
    fputs("\ncycle blocks X.in and Y.out\n",f);
    fclose(f);
}

typedef struct { const char *name; double number; } RuntimeValue;
typedef struct { RuntimeValue slots[128]; size_t count; } Runtime;
static void set_runtime(Runtime *r, const char *name, double number) {
    for (size_t i=0;i<r->count;++i)
        if (!strcmp(r->slots[i].name,name)) { r->slots[i].number=number; return; }
    CHECK(r->count<LENGTH(r->slots));
    r->slots[r->count++]=(RuntimeValue){name,number};
}
static double get_runtime(const Runtime *r, const char *operand) {
    for (size_t i=0;i<r->count;++i)
        if (!strcmp(r->slots[i].name,operand)) return r->slots[i].number;
    char *end;
    double value=strtod(operand,&end);
    CHECK(end!=operand && !*end);
    return value;
}
static double apply(const char *op, double a, double b) {
    if (!strcmp(op,"+")) return a+b;
    if (!strcmp(op,"-")) return a-b;
    if (!strcmp(op,"*")) return a*b;
    if (!strcmp(op,"/")) { CHECK(b!=0); return a/b; }
    if (!strcmp(op,"<")) return a<b;
    if (!strcmp(op,">")) return a>b;
    if (!strcmp(op,"<=")) return a<=b;
    if (!strcmp(op,">=")) return a>=b;
    if (!strcmp(op,"==")) return a==b;
    CHECK(!strcmp(op,"!="));
    return a!=b;
}
static Runtime execute(const Mini *m) {
    size_t locations[64]={0};
    Runtime r={0};
    for (size_t i=0;i<m->length;++i) {
        const Instruction *op=&m->code[i];
        CHECK(op->label<LENGTH(locations));
        if (op->op==LABEL) locations[op->label]=i+1;
    }
    size_t pc=0, steps=0;
    while (pc<m->length) {
        CHECK(++steps<10000);
        Instruction op=m->code[pc++];
        switch (op.op) {
            case LABEL: break;
            case SET: case CAST: set_runtime(&r,op.dst,get_runtime(&r,op.a)); break;
            case BIN:
                set_runtime(&r,op.dst,apply(op.operator,get_runtime(&r,op.a),get_runtime(&r,op.b)));
                break;
            case BRANCH:
                if (!apply(op.operator,get_runtime(&r,op.a),get_runtime(&r,op.b))) break;
                /* fall through */
            case GOTO: CHECK(locations[op.label]); pc=locations[op.label]; break;
        }
    }
    return r;
}

static void mini_checks(void) {
    FILE *example=fopen("examples/example.mini","r");
    CHECK(example);
    char sample[1024];
    size_t n=fread(sample,1,sizeof sample-1,example);
    CHECK(feof(example) && !ferror(example));
    sample[n]=0; fclose(example);
    const struct {
        const char *name,*input,*error,*second;
        size_t instructions;
        RuntimeValue expected[3];
    } cases[]={
        {"sample",sample,NULL,NULL,23,{{"x",3},{"y",3},{"z",6}}},
        {"nested","int x; x=0; while(x<3){if(x==1){x=x+2;}else{x=x+1;}}",NULL,NULL,17,{{"x",3}}},
        {"false arm","int x; x=0; if(x!=0){x=1;}else{x=2;}",NULL,NULL,9,{{"x",2}}},
        {"typed division","float z; z=3/2;",NULL,NULL,4,{{"z",1.5}}},
        {"narrowing","int x; x=1.5;","cannot narrow float to int for x",NULL,0,{{0}}},
        {"undeclared","int x; x=y; z=1;","undeclared y","undeclared z",0,{{0}}},
        {"duplicate","int x,x; float x;","duplicate x","duplicate x",0,{{0}}},
        {"syntax","int x; x=(1+2;","expected",NULL,0,{{0}}}
    };
    FILE *f=capture("q7-checks.txt");
    for (size_t i=0;i<LENGTH(cases);++i) {
        Mini a,b;
        bool ok=translate(&a,cases[i].input,true);
        CHECK(translate(&b,cases[i].input,false)==ok);
        CHECK(identical(&a,&b) && a.length==cases[i].instructions);
        CHECK(ok==!cases[i].error);
        fprintf(f,"%s: %zu instructions",cases[i].name,a.length);
        if (ok) {
            Runtime r=execute(&a);
            for (size_t j=0;j<LENGTH(cases[i].expected) && cases[i].expected[j].name;++j) {
                RuntimeValue v=cases[i].expected[j];
                CHECK(get_runtime(&r,v.name)==v.number);
                fprintf(f,", %s=%.10g",v.name,v.number);
            }
        } else if (a.syntax_error) {
            CHECK(strstr(a.syntax_error,cases[i].error));
            fprintf(f,", %s",a.syntax_error);
        } else {
            CHECK(a.error_count==(cases[i].second ? 2u : 1u));
            CHECK(!strcmp(a.errors->message,cases[i].error));
            if (cases[i].second) CHECK(!strcmp(a.errors->next->message,cases[i].second));
            for (const Diagnostic *d=a.errors;d;d=d->next) fprintf(f,", %s",d->message);
        }
        fputc('\n',f);
        if (i==0) {
            FILE *out=capture("q7-example.txt");
            print_translation(out,&a);
            fputs("Final: x=3, y=3, z=6.0\n",out);
            fclose(out);
        }
        release(&a.arena); release(&b.arena);
    }
    fclose(f);
}

static double elapsed(struct timespec a, struct timespec b) {
    return (double)(b.tv_sec-a.tv_sec)*1000.0+(double)(b.tv_nsec-a.tv_nsec)/1e6;
}
static int compare_double(const void *a,const void *b) {
    double x=*(const double *)a, y=*(const double *)b;
    return (x>y)-(x<y);
}
static void timings(void) {
    FILE *f=capture("q7-timing.csv");
    fputs("statements_including_decl_and_init,tokens,instructions,online_ms,two_pass_ms,"
          "online_samples,two_pass_samples\n",f);
    size_t sizes[]={10,100,1000,5000};
    const char base[]="int x; x=0; ", stmt[]="x=x+1; ";
    for (size_t i=0;i<LENGTH(sizes);++i) {
        size_t n=sizes[i], start=sizeof base-1, len=sizeof stmt-1;
        char *s=malloc(start+n*len+1);
        CHECK(s);
        memcpy(s,base,start);
        for (size_t j=0;j<n;++j) memcpy(s+start+j*len,stmt,len);
        s[start+n*len]=0;
        Arena lexmem={0};
        Lexer l={s,0,&lexmem};
        size_t tokens=0;
        while (lex(&l).kind) ++tokens;
        release(&lexmem);
        Mini a,b;
        CHECK(translate(&a,s,true) && translate(&b,s,false) && identical(&a,&b));
        size_t count=a.length;
        CHECK(count==2*n+1);
        release(&a.arena); release(&b.arena);
        double runs[2][9], sorted[9], median[2];
        for (size_t sample=0;sample<9;++sample) {
            for (size_t k=0;k<2;++k) {
                size_t mode=(sample+k)%2;
                Mini m;
                struct timespec begin,end;
                CHECK(clock_gettime(CLOCK_MONOTONIC,&begin)==0);
                bool ok=translate(&m,s,mode==0);
                CHECK(clock_gettime(CLOCK_MONOTONIC,&end)==0);
                CHECK(ok && m.length==count);
                runs[mode][sample]=elapsed(begin,end);
                release(&m.arena);
            }
        }
        for (size_t mode=0;mode<2;++mode) {
            memcpy(sorted,runs[mode],sizeof sorted);
            qsort(sorted,LENGTH(sorted),sizeof *sorted,compare_double);
            median[mode]=sorted[4];
        }
        fprintf(f,"%zu,%zu,%zu,%.3f,%.3f",n+2,tokens,count,median[0],median[1]);
        for (size_t mode=0;mode<2;++mode) {
            fputc(',',f);
            for (size_t j=0;j<9;++j) fprintf(f,"%s%.6f",j ? " " : "",runs[mode][j]);
        }
        fputc('\n',f);
        free(s);
    }
    fclose(f);
}

int checks(void) {
    expression_checks();
    declaration_checks();
    graph_checks();
    mini_checks();
    timings();
    puts("All Q1–Q7 checks passed. Evidence is in evidence/.");
    return 0;
}
