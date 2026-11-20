# Lab programs

- `01-20` contains the 20 C++ exercises, numbered `Ex-01.cpp` through `Ex-20.cpp`.
- `21-40` contains the 18 supplied Lex exercises, their original screenshots, and the sample C input file. The source repository has no files for exercises 33 and 34.

The programs and screenshots come from [CSA-1410-192424319](https://github.com/yogi8121660800/CSA-1410-192424319/tree/0bf28f1b25b7a022dd7f35de9996e142bd14490c). Exercises 05 and 17 share the same implementation in the source and retain their separate exercise numbers.

Compile each C++ exercise separately. From the repository root, for example:

```sh
c++ -std=c++17 "lab programs/01-20/Ex-01.cpp" -o /tmp/ex01
/tmp/ex01
```

Exercise 03 reads `flex_input.txt` from the working directory. Exercise 16 reads a
space-delimited assignment such as `x = a + b - c` from `sum.txt` and writes
three-address code to `out.txt`. Exercises 07 and 08 use simplified FIRST and FOLLOW
algorithms whose results can be incomplete for some nullable or recursive grammars.
