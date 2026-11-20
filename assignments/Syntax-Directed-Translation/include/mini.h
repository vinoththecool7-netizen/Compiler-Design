#ifndef MINI_H
#define MINI_H
#include "common.h"

typedef enum { PROGRAM, DECL, VARIABLE, CONSTANT, BINARY, ASSIGNMENT, CONDITION,
               IF_STMT, WHILE_STMT, BLOCK, DECL_NAME } Kind;
typedef struct Tree Tree;
struct Tree {
    Kind kind;
    const char *text, *address;
    Type type;
    Tree *child, *last, *next;
    unsigned first_label, second_label;
};
typedef enum { BIN, SET, CAST, LABEL, GOTO, BRANCH } Opcode;
typedef struct {
    Opcode op;
    const char *dst, *operator, *a, *b;
    unsigned label;
} Instruction;
typedef struct Diagnostic Diagnostic;
struct Diagnostic { const char *message; Diagnostic *next; };
typedef struct {
    Arena arena;
    Tree *tree;
    Symbols symbols;
    Instruction *code;
    size_t length, capacity, error_count;
    Diagnostic *errors, *last_error;
    const char *syntax_error;
    unsigned temp_count, label_count;
} Mini;

bool translate(Mini *m, const char *source, bool online);
void print_tree(FILE *out, const Tree *n, unsigned depth);
void print_instruction(FILE *out, Instruction i);
void print_translation(FILE *out, const Mini *m);
bool identical(const Mini *a, const Mini *b);
#endif
