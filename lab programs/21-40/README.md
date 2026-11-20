# Lex exercises 21–40

| Exercise | Scanner |
| --- | --- |
| 21 | `count_line.l` |
| 22 | `countconstants.l` |
| 23 | `count_macro.l` |
| 24 | `html.l` |
| 25 | `addlinenos.l` |
| 26 | `comment.l` |
| 27 | `capital.l` |
| 28 | `email_valid.l` |
| 29 | `substring.l` |
| 30 | `mobile.l` |
| 31 | `token.l` |
| 32 | `vowels.l` |
| 35 | `numbers_words.l` |
| 36 | `positive_neg_nums.l` |
| 37 | `url.l` |
| 38 | `dob.l` |
| 39 | `digit_or_not.l` |
| 40 | `cal.l` |

For example, generate, compile, and run exercise 21 from the repository root:

```sh
flex -o /tmp/ex21.c "lab programs/21-40/count_line.l"
cc /tmp/ex21.c -o /tmp/ex21
/tmp/ex21 "lab programs/21-40/input.c"
```

Exercises 21, 23, 25, and 31 take an input-file argument. Exercise 26 takes
input- and output-file arguments. Exercises 22 and 24 prompt for a filename.
