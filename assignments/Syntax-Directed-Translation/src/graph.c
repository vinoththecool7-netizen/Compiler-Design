#include "graph.h"
#include <stdint.h>

typedef struct Edge Edge;
struct Edge { size_t target; Edge *next; };

GraphResult evaluate(const Equation *eq, size_t n, bool reverse, Value *values,
                     size_t *order, size_t *completed) {
    Arena a={0};
    size_t *pending=allocate(&a,n*sizeof *pending);
    Edge **first=allocate(&a,n*sizeof *first);
    Edge **last=allocate(&a,n*sizeof *last);
    size_t max_inputs=0, head=0, tail=0;
    *completed=0;
    for (size_t i=0;i<n;++i) {
        pending[i]=eq[i].count;
        if (max_inputs<pending[i]) max_inputs=pending[i];
        for (size_t j=0;j<eq[i].count;++j) {
            size_t parent=eq[i].dependencies[j];
            if (parent>=n) { release(&a); return GRAPH_BAD_EDGE; }
            Edge *edge=allocate(&a,sizeof *edge);
            edge->target=i;
            if (last[parent]) last[parent]->next=edge;
            else first[parent]=edge;
            last[parent]=edge;
        }
    }
    for (size_t j=0;j<n;++j) {
        size_t i=reverse ? n-1-j : j;
        if (!pending[i]) order[tail++]=i;
    }
    Value *args=allocate(&a,(max_inputs ? max_inputs : 1)*sizeof *args);
    while (head<tail) {
        size_t i=order[head++];
        for (size_t j=0;j<eq[i].count;++j) args[j]=values[eq[i].dependencies[j]];
        values[i]=eq[i].compute ? eq[i].compute(eq[i].constant,args) : eq[i].constant;
        for (Edge *e=first[i];e;e=e->next)
            if (--pending[e->target]==0) order[tail++]=e->target;
    }
    *completed=head;
    release(&a);
    return head==n ? GRAPH_OK : GRAPH_CYCLE;
}
