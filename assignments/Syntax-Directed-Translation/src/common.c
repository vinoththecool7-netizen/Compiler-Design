#include "common.h"
#include <ctype.h>
#include <stdalign.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

struct Chunk { Chunk *next; size_t used, size; max_align_t alignment; unsigned char data[]; };

void *allocate(Arena *a, size_t n) {
    size_t alignment = alignof(max_align_t);
    if (n > SIZE_MAX - alignment - sizeof(Chunk)) abort();
    n = (n + alignment - 1) / alignment * alignment;
    Chunk *c = a->head;
    if (!c || n > c->size - c->used) {
        size_t capacity = n > 16384 ? n : 16384;
        c = malloc(sizeof *c + capacity);
        if (!c) { fputs("out of memory\n", stderr); exit(2); }
        c->next = a->head;
        c->used = 0;
        c->size = capacity;
        a->head = c;
    }
    void *p = c->data + c->used;
    c->used += n;
    memset(p, 0, n);
    return p;
}

void release(Arena *a) {
    while (a->head) {
        Chunk *c = a->head;
        a->head = c->next;
        free(c);
    }
}

char *copy(Arena *a, const char *s, size_t n) {
    char *p = allocate(a, n+1);
    memcpy(p,s,n);
    return p;
}

char *format(Arena *a, const char *fmt, ...) {
    va_list ap, duplicate;
    va_start(ap,fmt);
    va_copy(duplicate,ap);
    int n = vsnprintf(NULL,0,fmt,duplicate);
    va_end(duplicate);
    if (n < 0) abort();
    char *s = allocate(a,(size_t)n+1);
    vsnprintf(s,(size_t)n+1,fmt,ap);
    va_end(ap);
    return s;
}

Token lex(Lexer *l) {
    const char *s=l->source;
    size_t i=l->pos;
    for (;;) {
        while (isspace((unsigned char)s[i])) ++i;
        if (s[i]!='/' || s[i+1]!='/') break;
        while (s[i] && s[i]!='\n') ++i;
    }
    size_t start=i;
    int kind=INVALID;
    unsigned char c=(unsigned char)s[i];
    if (!c) {
        l->pos=i;
        return (Token){END,"",i};
    }
    ++i;
    if (isalpha(c) || c=='_') {
        while (isalnum((unsigned char)s[i]) || s[i]=='_') ++i;
        kind=NAME;
    } else if (isdigit(c)) {
        while (isdigit((unsigned char)s[i])) ++i;
        if (s[i]=='.' && isdigit((unsigned char)s[i+1])) {
            do { ++i; } while (isdigit((unsigned char)s[i]));
        }
        kind=NUMBER;
    } else if (strchr("<>=!",c) && s[i]=='=') {
        ++i;
        kind=REL;
    } else if (c=='<' || c=='>') kind=REL;
    else if (strchr("+-*/(){};,=",c)) kind=c;
    const char *text=copy(l->arena,s+start,i-start);
    if (kind==NAME) {
        static const char *const words[]={"int","float","if","else","while"};
        for (size_t j=0;j<sizeof words/sizeof *words;++j)
            if (!strcmp(text,words[j])) { kind=INT+(int)j; break; }
    }
    l->pos=i;
    return (Token){kind,text,start};
}

const char *type_name(Type type) {
    switch (type) {
        case TY_INT: return "int";
        case TY_FLOAT: return "float";
        default: return "error";
    }
}

struct Binding { const char *name; Type type; };
static size_t bucket(Binding **slots, size_t capacity, const char *name) {
    uint64_t hash=UINT64_C(14695981039346656037);
    for (const unsigned char *p=(const unsigned char *)name;*p;++p)
        hash=(hash^*p)*UINT64_C(1099511628211);
    size_t i=(size_t)hash&(capacity-1);
    while (slots[i] && strcmp(slots[i]->name,name)) i=(i+1)&(capacity-1);
    return i;
}

Type lookup(const Symbols *s, const char *name) {
    if (!s->capacity) return TY_ERROR;
    Binding *b=s->slots[bucket(s->slots,s->capacity,name)];
    return b ? b->type : TY_ERROR;
}

bool insert(Arena *a, Symbols *s, const char *name, Type t) {
    if (lookup(s,name)!=TY_ERROR) return false;
    if (!s->capacity || s->count+1 > s->capacity/2) {
        size_t new_capacity=s->capacity ? 2*s->capacity : 16;
        Binding **new_slots=allocate(a,new_capacity*sizeof *new_slots);
        for (size_t i=0;i<s->capacity;++i) {
            Binding *b=s->slots[i];
            if (b) new_slots[bucket(new_slots,new_capacity,b->name)]=b;
        }
        s->capacity=new_capacity;
        s->slots=new_slots;
    }
    Binding *b=allocate(a,sizeof *b);
    *b=(Binding){name,t};
    s->slots[bucket(s->slots,s->capacity,name)]=b;
    ++s->count;
    return true;
}

void print_symbols(FILE *f, const Symbols *s) {
    fputc('{',f);
    const char *separator="";
    for (size_t i=0;i<s->capacity;++i) {
        Binding *b=s->slots[i];
        if (!b) continue;
        fprintf(f,"%s%s:%s",separator,b->name,type_name(b->type));
        separator=", ";
    }
    fputc('}',f);
}
