# Part I desk checks

Run from this directory with Python 3 (standard library only):

```sh
python3 deskcheck.py
```

The script checks declaration offsets, Boolean lists and negation, a faulty OR action with an explicitly modelled fallback, the sample kernel, nested loops with negative STEP and inner BREAK, rejection of BREAK outside a loop, and rejection of a zero STEP. It overwrites `desk-checks.json` with the resulting quadruples, patch events and selected runtime values. A successful run prints a confirmation and exits with status 0. The nested-loop test asserts a final sum of 24.

`layout.py` implements a small declaration layout model with independent record scopes. `tac.py` compiles and executes a restricted Python-shaped notation; `count(start, end, step)` represents an inclusive counting loop. `deskcheck.py` drives these checks, rather than parsing the assignment's source syntax. This is a test model, not a complete compiler for the report's pseudocode. In particular, its sample uses unchecked array accesses by default and does not insert numeric widening for relational comparisons; the report's full translation scheme explicitly includes both. The OR-defect example shows the unresolved or multiply patched state inherent in the defective rule; a fallback destination is supplied solely to illustrate one possible wrong runtime result. Do not treat that fallback as part of the original rule.

[Word report](docs/Report.docx) · [Download project ZIP](docs/Project.zip)
