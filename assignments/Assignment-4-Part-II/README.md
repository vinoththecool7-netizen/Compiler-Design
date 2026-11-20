# Assignment 4 Part II: Intermediate code generation

Tested with Python 3.14.6; only the Python standard library is required. From this directory run:

```sh
python3 experiments.py
python3 followup.py
```

This regenerates the JSON files in `evidence/`, runs the generated code in the interpreter, checks results before and after optimisation, and verifies switch dispatch on the specified probes. A successful run prints `Seven execution results, six rejection cases, argument order and switch dispatch verified.` The evidence files contain inputs, quadruples, branch lists, patch snapshots, measurements and results. Run `python3 -m py_compile tac.py switch.py layout.py experiments.py` for a syntax check.

`layout.py` processes its own small declaration syntax, with scalar types, pointers, arrays and nested records. `tac.py` compiles a restricted Python-shaped language using Python's AST parser: annotated int/float/bool, pointer and fixed-dimension array declarations, assignments, arithmetic, short-circuit Boolean conditions, if/else, while, inclusive `count(start,end,step)` for loops, `with do(condition)` loops, match/case without fall-through, fixed-arity functions, calls, return, break and continue. It is not a general Python implementation. The compiler predeclares function signatures, checks argument count but does not validate argument types at call sites, and keeps the declaration-layout demonstration separate. `switch.py` compares three switch dispatch representations. `experiments.py` contains reproducible examples and optimisation passes.

Current limitations include unsupported fall-through, parser nesting limits and limits on deeply nested non-binary ASTs. Physical activation records and triple memory sizes discussed in the report are illustrative models; the interpreter uses Python objects.

[Download project ZIP](docs/Project.zip)
