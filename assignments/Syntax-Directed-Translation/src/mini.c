#include "mini.h"
#include <string.h>

typedef struct {
    Mini *m;
    Lexer lexer;
    Token current;
    bool online;
    unsigned nesting;
} Parser;

static Tree *make(Mini *m, Kind kind, const char *text) {
    Tree *n=allocate(&m->arena,sizeof *n);
    *n=(Tree){.kind=kind,.text=text};
    return n;
}

static void append(Tree *parent, Tree *child) {
    if (parent->last) parent->last->next=child;
    else parent->child=child;
    parent->last=child;
}

static void diagnostic(Mini *m, const char *prefix, const char *name) {
    Diagnostic *d=allocate(&m->arena,sizeof *d);
    d->message=format(&m->arena,"%s %s",prefix,name);
    if (m->last_error) m->last_error->next=d;
    else m->errors=d;
    m->last_error=d;
    ++m->error_count;
}

static void emit(Mini *m, Instruction ins) {
    if (m->length==m->capacity) {
        size_t capacity=m->capacity ? 2*m->capacity : 32;
        Instruction *p=allocate(&m->arena,capacity*sizeof *p);
        if (m->length) memcpy(p,m->code,m->length*sizeof *p);
        m->code=p;
        m->capacity=capacity;
    }
    m->code[m->length++]=ins;
}

static const char *temporary(Mini *m) {
    return format(&m->arena,"%%t%u",++m->temp_count);
}

static unsigned label(Mini *m) { return ++m->label_count; }

static Type require_type(Mini *m, const char *name) {
    Type t=lookup(&m->symbols,name);
    if (t==TY_ERROR) diagnostic(m,"undeclared",name);
    return t;
}

static void lower_declaration(Mini *m, Tree *n) {
    Type t=!strcmp(n->text,"int") ? TY_INT : TY_FLOAT;
    for (Tree *name=n->child;name;name=name->next) {
        name->type=t;
        if (!insert(&m->arena,&m->symbols,name->text,t))
            diagnostic(m,"duplicate",name->text);
    }
}

static void lower_leaf(Mini *m, Tree *n) {
    if (n->kind==VARIABLE) n->type=require_type(m,n->text);
    else n->type=strchr(n->text,'.') ? TY_FLOAT : TY_INT;
    n->address=n->text;
}

static const char *widen(Mini *m, const Tree *value, Type to) {
    if (value->type==TY_INT && to==TY_FLOAT) {
        const char *dst=temporary(m);
        emit(m,(Instruction){.op=CAST,.dst=dst,.a=value->address});
        return dst;
    }
    return value->address;
}

static void lower_binary(Mini *m, Tree *n) {
    const Tree *l=n->child, *r=l->next;
    n->address="?";
    if (!l->type || !r->type) return;
    n->type=*n->text=='/' || l->type==TY_FLOAT || r->type==TY_FLOAT ? TY_FLOAT : TY_INT;
    const char *a=widen(m,l,n->type), *b=widen(m,r,n->type);
    n->address=temporary(m);
    emit(m,(Instruction){.op=BIN,.dst=n->address,.operator=n->text,.a=a,.b=b});
}

static void lower_assignment(Mini *m, Tree *n) {
    n->type=require_type(m,n->text);
    const Tree *rhs=n->child;
    if (!n->type || !rhs->type) return;
    if (n->type==TY_INT && rhs->type==TY_FLOAT) {
        diagnostic(m,"cannot narrow float to int for",n->text);
        return;
    }
    const char *address=widen(m,rhs,n->type);
    emit(m,(Instruction){.op=SET,.dst=n->text,.a=address});
}

static void lower_condition(Mini *m, Tree *n, unsigned yes, unsigned no) {
    n->first_label=yes;
    n->second_label=no;
    const Tree *l=n->child, *r=l->next;
    if (l->type && r->type) {
        Type t=l->type==TY_FLOAT || r->type==TY_FLOAT ? TY_FLOAT : TY_INT;
        const char *a=widen(m,l,t), *b=widen(m,r,t);
        emit(m,(Instruction){.op=BRANCH,.operator=n->text,.a=a,.b=b,.label=yes});
    }
    emit(m,(Instruction){.op=GOTO,.label=no});
}

static Token take(Parser *p) {
    Token t=p->current;
    p->current=lex(&p->lexer);
    return t;
}

static void syntax(Parser *p, const char *wanted) {
    if (!p->m->syntax_error)
        p->m->syntax_error=format(&p->m->arena,"expected %s at byte %zu, got '%s'",
            wanted,p->current.offset,p->current.kind ? p->current.text : "EOF");
}

static bool expect(Parser *p, int kind, const char *text) {
    if (p->current.kind!=kind) { syntax(p,text); return false; }
    take(p);
    return true;
}

static Tree *expression(Parser *p);
static Tree *statement(Parser *p);
static bool enter(Parser *p) {
    if (p->nesting==256) { syntax(p,"nesting depth below 256"); return false; }
    ++p->nesting;
    return true;
}

static Tree *factor(Parser *p) {
    int token=p->current.kind;
    if (token=='(') {
        if (!enter(p)) return NULL;
        take(p);
        Tree *inside=expression(p);
        --p->nesting;
        if (!inside || !expect(p,')',"')'")) return NULL;
        return inside;
    }
    if (token!=NAME && token!=NUMBER) { syntax(p,"identifier, literal or '('"); return NULL; }
    Tree *n=make(p->m,token==NAME ? VARIABLE : CONSTANT,take(p).text);
    if (p->online) lower_leaf(p->m,n);
    return n;
}

static Tree *fold(Parser *p, Tree *(*child)(Parser *), int op1, int op2) {
    Tree *left=child(p);
    while (left && (p->current.kind==op1 || p->current.kind==op2)) {
        const char *op=take(p).text;
        Tree *right=child(p);
        if (!right) return NULL;
        Tree *result=make(p->m,BINARY,op);
        append(result,left);
        append(result,right);
        if (p->online) lower_binary(p->m,result);
        left=result;
    }
    return left;
}

static Tree *term(Parser *p) { return fold(p,factor,'*','/'); }
static Tree *expression(Parser *p) { return fold(p,term,'+','-'); }

static Tree *condition(Parser *p, unsigned yes, unsigned no) {
    Tree *l=expression(p);
    if (!l) return NULL;
    if (p->current.kind!=REL) { syntax(p,"relational operator"); return NULL; }
    const char *rel=take(p).text;
    Tree *r=expression(p);
    if (!r) return NULL;
    Tree *b=make(p->m,CONDITION,rel);
    append(b,l);
    append(b,r);
    if (p->online) lower_condition(p->m,b,yes,no);
    return b;
}

static Tree *block(Parser *p) {
    if (!expect(p,'{',"'{'") || !enter(p)) return NULL;
    Tree *n=make(p->m,BLOCK,NULL);
    while (p->current.kind && p->current.kind!='}') {
        Tree *s=statement(p);
        if (!s) { --p->nesting; return NULL; }
        append(n,s);
    }
    --p->nesting;
    return expect(p,'}',"'}'") ? n : NULL;
}

static Tree *control(Parser *p, bool is_while) {
    Mini *m=p->m;
    take(p);
    if (!expect(p,'(',"'('")) return NULL;
    unsigned a=0,b=0,end=0;
    if (p->online) {
        a=label(m); b=label(m); end=label(m);
        if (is_while) emit(m,(Instruction){.op=LABEL,.label=a});
    }
    Tree *test=condition(p,is_while ? b : a,is_while ? end : b);
    if (!test || !expect(p,')',"')'")) return NULL;
    if (p->online) emit(m,(Instruction){.op=LABEL,.label=is_while ? b : a});
    Tree *first=block(p);
    if (!first) return NULL;
    Tree *n=make(m,is_while ? WHILE_STMT : IF_STMT,NULL);
    n->first_label=a;
    n->second_label=end;
    append(n,test);
    append(n,first);
    if (p->online) emit(m,(Instruction){.op=GOTO,.label=is_while ? a : end});
    if (!is_while) {
        if (!expect(p,ELSE,"'else'")) return NULL;
        if (p->online) emit(m,(Instruction){.op=LABEL,.label=b});
        Tree *second=block(p);
        if (!second) return NULL;
        append(n,second);
    }
    if (p->online) emit(m,(Instruction){.op=LABEL,.label=end});
    return n;
}

static Tree *statement(Parser *p) {
    int kind=p->current.kind;
    if (kind==IF || kind==WHILE) return control(p,kind==WHILE);
    if (kind!=NAME) { syntax(p,"assignment, if or while"); return NULL; }
    const char *name=take(p).text;
    if (!expect(p,'=',"'='")) return NULL;
    Tree *rhs=expression(p);
    if (!rhs || !expect(p,';',"';'")) return NULL;
    Tree *n=make(p->m,ASSIGNMENT,name);
    append(n,rhs);
    if (p->online) lower_assignment(p->m,n);
    return n;
}

static Tree *declaration(Parser *p) {
    Tree *n=make(p->m,DECL,take(p).text);
    do {
        if (p->current.kind!=NAME) { syntax(p,"declaration identifier"); return NULL; }
        append(n,make(p->m,DECL_NAME,take(p).text));
        if (p->current.kind!=',') break;
        take(p);
    } while (true);
    if (!expect(p,';',"';'")) return NULL;
    if (p->online) lower_declaration(p->m,n);
    return n;
}

static Tree *program(Parser *p) {
    Tree *root=make(p->m,PROGRAM,NULL);
    while (p->current.kind==INT || p->current.kind==FLOAT) {
        Tree *n=declaration(p);
        if (!n) return NULL;
        append(root,n);
    }
    while (p->current.kind) {
        Tree *n=statement(p);
        if (!n) return NULL;
        append(root,n);
    }
    return root;
}

static void replay_expr(Mini *m, Tree *n) {
    if (n->kind!=BINARY) { lower_leaf(m,n); return; }
    replay_expr(m,n->child);
    replay_expr(m,n->child->next);
    lower_binary(m,n);
}

static void replay(Mini *m, Tree *n) {
    switch (n->kind) {
        case PROGRAM: case BLOCK:
            for (Tree *c=n->child;c;c=c->next) replay(m,c);
            return;
        case DECL:
            lower_declaration(m,n);
            return;
        case ASSIGNMENT:
            replay_expr(m,n->child);
            lower_assignment(m,n);
            return;
        case IF_STMT: case WHILE_STMT: {
            bool loop=n->kind==WHILE_STMT;
            unsigned a=label(m), b=label(m), end=label(m);
            n->first_label=a; n->second_label=end;
            Tree *cond=n->child, *first=cond->next;
            if (loop) emit(m,(Instruction){.op=LABEL,.label=a});
            replay_expr(m,cond->child);
            replay_expr(m,cond->child->next);
            lower_condition(m,cond,loop ? b : a,loop ? end : b);
            emit(m,(Instruction){.op=LABEL,.label=loop ? b : a});
            replay(m,first);
            emit(m,(Instruction){.op=GOTO,.label=loop ? a : end});
            if (!loop) {
                emit(m,(Instruction){.op=LABEL,.label=b});
                replay(m,first->next);
            }
            emit(m,(Instruction){.op=LABEL,.label=end});
            return;
        }
        default: return;
    }
}

bool translate(Mini *m, const char *source, bool online) {
    *m=(Mini){0};
    Parser p={.m=m,.lexer={source,0,&m->arena},.online=online};
    p.current=lex(&p.lexer);
    m->tree=program(&p);
    if (m->tree && !online) replay(m,m->tree);
    if (!m->tree || m->errors) m->length=0;
    return m->tree && !m->errors;
}

void print_tree(FILE *f, const Tree *n, unsigned depth) {
    static const char *const names[]={"program","decl","id","literal","binary","assign",
                                      "condition","if","while","block","name"};
    fprintf(f,"%*s%s",(int)(depth*2),"",names[n->kind]);
    if (n->text) fprintf(f," %s",n->text);
    switch (n->kind) {
        case VARIABLE: case CONSTANT: case BINARY:
            fprintf(f," [addr=%s, type=%s]",n->address,type_name(n->type)); break;
        case ASSIGNMENT: fprintf(f," [target=%s]",type_name(n->type)); break;
        case DECL_NAME: fprintf(f," [in=%s]",type_name(n->type)); break;
        case CONDITION: fprintf(f," [true=L%u, false=L%u]",n->first_label,n->second_label); break;
        case IF_STMT: fprintf(f," [join=L%u]",n->second_label); break;
        case WHILE_STMT: fprintf(f," [head=L%u, exit=L%u]",n->first_label,n->second_label); break;
        default: break;
    }
    fputc('\n',f);
    for (const Tree *child=n->child;child;child=child->next) print_tree(f,child,depth+1);
}

void print_instruction(FILE *f, Instruction i) {
    switch (i.op) {
        case BIN: fprintf(f,"%s = %s %s %s\n",i.dst,i.a,i.operator,i.b); break;
        case SET: fprintf(f,"%s = %s\n",i.dst,i.a); break;
        case CAST: fprintf(f,"%s = intToFloat %s\n",i.dst,i.a); break;
        case LABEL: fprintf(f,"L%u:\n",i.label); break;
        case GOTO: fprintf(f,"goto L%u\n",i.label); break;
        case BRANCH: fprintf(f,"if %s %s %s goto L%u\n",i.a,i.operator,i.b,i.label); break;
    }
}

void print_translation(FILE *f, const Mini *m) {
    if (m->syntax_error) { fprintf(f,"Syntax error: %s\n",m->syntax_error); return; }
    print_tree(f,m->tree,0);
    fputs("Symbols: ",f); print_symbols(f,&m->symbols); fputc('\n',f);
    for (size_t i=0;i<m->length;++i) print_instruction(f,m->code[i]);
    for (const Diagnostic *d=m->errors;d;d=d->next) fprintf(f,"Semantic error: %s\n",d->message);
}

static bool equal_text(const char *a, const char *b) {
    return (a && b) ? !strcmp(a,b) : a==b;
}

static bool equal_tree(const Tree *a, const Tree *b) {
    while (a && b) {
        if (a->kind!=b->kind || a->type!=b->type || a->first_label!=b->first_label ||
            a->second_label!=b->second_label || !equal_text(a->text,b->text) ||
            !equal_text(a->address,b->address) || !equal_tree(a->child,b->child)) return false;
        a=a->next; b=b->next;
    }
    return a==b;
}

bool identical(const Mini *a, const Mini *b) {
    if (!equal_text(a->syntax_error,b->syntax_error)) return false;
    if (a->syntax_error) return true;
    if (a->length!=b->length || a->error_count!=b->error_count ||
        a->symbols.count!=b->symbols.count || !equal_tree(a->tree,b->tree)) return false;
    const Diagnostic *x=a->errors, *y=b->errors;
    for (;x && y;x=x->next,y=y->next) if (strcmp(x->message,y->message)) return false;
    for (size_t i=0;i<a->length;++i) {
        Instruction l=a->code[i], r=b->code[i];
        if (l.op!=r.op || l.label!=r.label || !equal_text(l.dst,r.dst) ||
            !equal_text(l.a,r.a) || !equal_text(l.b,r.b) ||
            !equal_text(l.operator,r.operator)) return false;
    }
    return true;
}
