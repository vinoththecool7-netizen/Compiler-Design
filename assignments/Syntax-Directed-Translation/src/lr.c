#include "lr.h"
#include "parser.h"
int yyparse(LR *lr);
#include <math.h>
#include <stdlib.h>
#include <string.h>

static void emit(LR *lr, const char *text) {
    if (lr->actions==lr->capacity) {
        size_t capacity=lr->capacity ? 2*lr->capacity : 16;
        const char **p=allocate(&lr->arena,capacity*sizeof *p);
        if (lr->actions) memcpy(p,lr->postfix,lr->actions*sizeof *p);
        lr->postfix=p;
        lr->capacity=capacity;
    }
    lr->postfix[lr->actions++]=text;
}

static Ast *make_ast(LR *lr, const char *text, Ast *a, Ast *b) {
    Ast *n=allocate(&lr->arena,sizeof *n);
    *n=(Ast){text,a,b};
    return n;
}

Node *node(LR *lr, const char *label, Node *a, Node *b, Node *c) {
    Node *n=allocate(&lr->arena,sizeof *n);
    *n=(Node){.label=label,.child={a,b,c},.nodes=1,.attributes=1};
    for (size_t i=0;i<3;++i) {
        Node *child=n->child[i];
        if (!child) continue;
        if (n->height<=child->height) n->height=1+child->height;
        n->nodes+=child->nodes;
        n->attributes+=child->attributes;
    }
    return n;
}

static void value(Node *n, double v) {
    n->value=v;
    n->has_value=true;
    ++n->attributes;
}

Node *leaf(LR *lr, const char *label, const char *text) {
    Node *n=node(lr,label,NULL,NULL,NULL);
    n->text=text;
    if (!strcmp(label,"num")) {
        double v=strtod(text,NULL);
        if (!isfinite(v) && !lr->error) lr->error="numeric literal out of range";
        value(n,v);
        n->ast=make_ast(lr,text,NULL,NULL);
    }
    if (!strcmp(label,"id")) n->ast=make_ast(lr,text,NULL,NULL);
    return n;
}

static void transfer(Node *to, Node *from) {
    to->ast=from->ast;
    if (from->has_value) value(to,from->value);
}

Node *forward(LR *lr, const char *label, Node *a) {
    Node *n=node(lr,label,a,NULL,NULL);
    transfer(n,a);
    return n;
}

Node *group(LR *lr, Node *a, Node *e, Node *b) {
    Node *n=node(lr,"F",a,e,b);
    transfer(n,e);
    return n;
}

Node *factor(LR *lr, Node *a) {
    Node *n=forward(lr,"F",a);
    if (!a->has_value && (lr->mode==EVALUATE || lr->mode==RIGHT_ASSOC) && !lr->error)
        lr->error="identifier has no numeric value";
    emit(lr,a->text);
    return n;
}

Node *binary(LR *lr, const char *label, Node *a, Node *op, Node *b) {
    Node *n=node(lr,label,a,op,b);
    n->ast=make_ast(lr,op->text,a->ast,b->ast);
    if ((lr->mode==EVALUATE || lr->mode==RIGHT_ASSOC) && a->has_value && b->has_value && !lr->error) {
        double v=0;
        switch (*op->text) {
            case '+': v=a->value+b->value; break;
            case '-': v=a->value-b->value; break;
            case '*': v=a->value*b->value; break;
            case '/':
                if (b->value==0) { lr->error="division by zero"; break; }
                v=a->value/b->value;
                break;
            default: abort();
        }
        if (!isfinite(v)) lr->error="numeric result out of range";
        if (!lr->error) value(n,v);
    }
    if (*op->text!='=') emit(lr,op->text);
    return n;
}

static void bind(LR *lr, Node *id, Type type) {
    if (!insert(&lr->arena,&lr->symbols,id->text,type) && !lr->error)
        lr->error=format(&lr->arena,"duplicate %s",id->text);
}

Node *add_name(LR *lr, Node *list, Node *comma, Node *id, Type type) {
    Node *n=list ? node(lr,"L",list,comma,id) : node(lr,"L",id,NULL,NULL);
    n->type=type;
    bind(lr,id,type);
    return n;
}

static void inherit(LR *lr, Node *n, Type type) {
    n->type=type;
    if (n->child[2]) {
        inherit(lr,n->child[0],type);
        bind(lr,n->child[2],type);
    } else bind(lr,n->child[0],type);
}

bool exercise(LR *lr, Exercise mode, const char *source, FILE *trace) {
    *lr=(LR){.mode=mode,.trace=trace};
    lr->lexer=(Lexer){source,0,&lr->arena};
    if (yyparse(lr)!=0) return false;
    if (mode==DECLARE) inherit(lr,lr->root->child[1],lr->root->child[0]->type);
    return !lr->error;
}

void tree(FILE *f, const Node *n, unsigned depth) {
    fprintf(f,"%*s%s",(int)(2*depth),"",n->label);
    if (n->text) fprintf(f," '%s'",n->text);
    fprintf(f," [h=%zu",n->height);
    if (n->has_value) fprintf(f,", val=%.10g",n->value);
    if (n->type) fprintf(f,", %s=%s",!strcmp(n->label,"L") ? "in" : "type",type_name(n->type));
    fputs("]\n",f);
    for (size_t i=0;i<3;++i)
        if (n->child[i]) tree(f,n->child[i],depth+1);
}

void ast(FILE *f, const Ast *n) {
    fputs(n->text,f);
    if (n->left) {
        fputc('(',f); ast(f,n->left); fputs(", ",f); ast(f,n->right); fputc(')',f);
    }
}

size_t ast_nodes(const Ast *n) {
    return n ? 1+ast_nodes(n->left)+ast_nodes(n->right) : 0;
}
