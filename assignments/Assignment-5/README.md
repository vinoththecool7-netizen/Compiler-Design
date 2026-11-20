# Assignment 5: code generation and optimisation

Run from this project folder with Python 3 (tested with Python 3.14.6):

```sh
python3 verify.py
```

The script runs 32 comparisons between the TAC interpreter, the three-operand intermediate target, and the destructive two-operand target in `strict.py`. It checks analysis traversal orders, cross-block constant propagation, and optimisation outputs, and writes measurements to `results.json`. Inputs are embedded in `verify.py`.

`backend.py` defines TAC, control flow, data-flow analysis, allocation and interpreters. `verify.py` implements local and global optimisers, peepholes and experiments. `strict.py` lowers the extended intermediate target to destructive operations and interprets it independently. The cost is one plus one per memory operand. Register and immediate sources to LD, indexed memory operands, and unbounded arithmetic are assumptions for aspects not defined by the target description. The optimizer does not implement general pointer or array stores, procedure calls, loop transformation, a production target or a stack bytecode target. Reported optimization effort counts selected operations, not compile time.

[Download project ZIP](docs/Project.zip)
