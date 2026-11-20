# Compiler Design Assignment 2

The report covers grammar design, LL(1), shift/reduce and operator precedence,
SLR(1), error recovery, Flex/Bison, and an iterative parser for deep inputs.

Run from this directory with Python 3, Flex, GNU Bison, and a C compiler:

```sh
python3 parsing.py
python3 precedence.py
python3 recovery.py > evidence/q5-restart.txt
python3 yacc/build.py > evidence/q6-runs.txt
```

The experiments overwrite their corresponding evidence files. Bison generates
C code and the build script compiles and tests each variant. The five complete
YACC specifications are in `yacc/specs/`, and the shared Flex lexer is
`yacc/scanner.l`. From the project directory after building, try:

```sh
printf '%s\n' 'let charge; charge = base + units * rate - discount;' |
  yacc/build/precedence/billing
```

The depth cap for recursive descent is an experimental policy of 600 active
grammar calls. The iterative prototype measures heap-backed list entries,
which are different units from recursive grammar calls.

[Download the project ZIP](docs/Project.zip)
