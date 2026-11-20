# Assignment 3 in C

Requires a C17 compiler, GNU Bison, Make, and POSIX clock support. From this
directory:

```sh
make check
./build/assignment3 expr '3*(4+5)-6/2'
./build/assignment3 decl 'float a,b,c;'
./build/assignment3 postfix 'a+b*(c-d)'
./build/assignment3 ast 'a=b+c*d'
./build/assignment3 marker 'int x,y'
./build/assignment3 mini examples/example.mini
./build/assignment3 two-pass examples/example.mini
```

The generated parser, object files and executable go in `build/`. All exercise and test
logic is in C. `make check` replaces the captured results in `evidence/`.
The shipped `environment.txt` describes the original measured run.

- `grammar/parser.y` and `src/lr.c` implement reduction actions for Q1, Q2, Q4, Q5 and
  the Q6 marker. `src/graph.c` is the Q3 dependency scheduler.
- `src/mini.c` implements the Q7 predictive parser and the separate AST walk.
  Both schedules share the semantic actions and emit annotated ASTs, symbol
  tables and three-address code. `src/common.c` supplies lexing and allocation.
- `tests/check.c` generates Q1–Q7 evidence, interprets selected TAC, and measures both
  schedules. The release measurements time translation through return,
  excluding deallocation, output, and TAC execution.

Q1 computes values using C double arithmetic. MiniLang allows declarations at
file scope before statements, mandatory braced if/else arms, and braced while
bodies. Division yields float. int widens to float, and implicit narrowing is
rejected. The translator collects semantic diagnostics for syntactically valid
input and withholds TAC on errors. Definite assignment and compile-time
division-by-zero analysis are outside the implemented MiniLang subset.

## Repository layout

| Folder | Contents |
| --- | --- |
| `src/` | C implementations and command-line entry point |
| `include/` | C headers |
| `grammar/` | Bison grammar and reduction actions |
| `tests/` | C verification and benchmark harness |
| `examples/` | MiniLang example program |
| `docs/` | Word report, question write-ups and figures |
| `evidence/` | Captured test output and benchmarks |

## Report by question

- [Q1](docs/questions/q1.md)
- [Q2](docs/questions/q2.md)
- [Q3](docs/questions/q3.md)
- [Q4](docs/questions/q4.md)
- [Q5](docs/questions/q5.md)
- [Q6](docs/questions/q6.md)
- [Q7](docs/questions/q7.md)

[Complete Word report](docs/Assignment%203%20Syntax%20Directed%20Translation%20Report%20in%20C.docx)
