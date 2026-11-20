#ifndef GRAPH_H
#define GRAPH_H
#include "common.h"

typedef struct { double number; const char *text; } Value;
typedef Value (*Compute)(Value constant, const Value *args);
typedef struct {
    const char *name;
    size_t count;
    const size_t *dependencies;
    Compute compute;
    Value constant;
} Equation;
typedef enum { GRAPH_OK, GRAPH_CYCLE, GRAPH_BAD_EDGE } GraphResult;
GraphResult evaluate(const Equation *eq, size_t n, bool reverse, Value *values,
                     size_t *order, size_t *completed);
#endif
