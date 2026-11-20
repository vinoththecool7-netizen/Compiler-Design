#ifndef COMMON_H
#define COMMON_H
#include <stdbool.h>
#include <stddef.h>
#include <stdio.h>

typedef struct Chunk Chunk;
typedef struct { Chunk *head; } Arena;
void *allocate(Arena *a, size_t bytes);
void release(Arena *a);
char *copy(Arena *a, const char *s, size_t n);
char *format(Arena *a, const char *fmt, ...);

enum { END=0, NAME=256, NUMBER, INT, FLOAT, IF, ELSE, WHILE, REL, INVALID };
typedef struct { int kind; const char *text; size_t offset; } Token;
typedef struct { const char *source; size_t pos; Arena *arena; } Lexer;
Token lex(Lexer *l);

typedef enum { TY_ERROR, TY_INT, TY_FLOAT } Type;
const char *type_name(Type type);
typedef struct Binding Binding;
typedef struct { Binding **slots; size_t capacity, count; } Symbols;
Type lookup(const Symbols *s, const char *name);
bool insert(Arena *a, Symbols *s, const char *name, Type t);
void print_symbols(FILE *f, const Symbols *s);
#endif
