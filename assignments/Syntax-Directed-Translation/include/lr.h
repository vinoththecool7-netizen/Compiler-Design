#ifndef LR_H
#define LR_H
#include "common.h"

typedef enum { EVALUATE, POSTFIX, BUILD_AST, RIGHT_ASSOC, DECLARE, MARKER } Exercise;
typedef struct Ast Ast;
struct Ast { const char *text; Ast *left, *right; };

typedef struct Node Node;
struct Node {
    const char *label, *text;
    Node *child[3];
    Ast *ast;
    double value;
    Type type;
    bool has_value;
    size_t height, nodes, attributes;
};
typedef struct {
    Arena arena;
    Lexer lexer;
    Exercise mode;
    bool started;
    Node *root;
    const char *error;
    const char **postfix;
    size_t actions, capacity;
    Symbols symbols;
    FILE *trace;
} LR;

bool exercise(LR *lr, Exercise mode, const char *source, FILE *trace);
Node *leaf(LR *lr, const char *label, const char *text);
Node *node(LR *lr, const char *label, Node *a, Node *b, Node *c);
Node *binary(LR *lr, const char *label, Node *a, Node *op, Node *b);
Node *forward(LR *lr, const char *label, Node *a);
Node *group(LR *lr, Node *a, Node *e, Node *b);
Node *factor(LR *lr, Node *a);
Node *add_name(LR *lr, Node *list, Node *comma, Node *id, Type type);
void tree(FILE *f, const Node *n, unsigned depth);
void ast(FILE *f, const Ast *n);
size_t ast_nodes(const Ast *n);
#endif
