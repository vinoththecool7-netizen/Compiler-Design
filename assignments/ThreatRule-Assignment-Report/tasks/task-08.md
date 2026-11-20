# Task 8 Flex Implementation

## The three sections of threatrule.l

| Section | Contents |
| --- | --- |
| Declarations | Options, token enumeration, yylval union, helper prototypes, regular definitions and inclusive FEED start condition. |
| Translation rules | Pattern and action pairs between %% markers. Accepted tokens return their kind; whitespace and diagnostics fall through so scanning continues. |
| Auxiliary C | Symbol interning, numeric and IPv4 validators, diagnostics and the scanner driver. |

yytext points to the matched spelling and yyleng gives its byte length. The scanner sets yylval.symbol for ID, yylval.number for INTEGER and PORT, yylval.ip for IPv4, and yylval.text for strings, operators and feed literals. The driver consumes text before the next yylex call; a future parser that retains it must copy it. The %option yylineno setting tracks LF bytes, including those in CRLF. Recovery patterns exclude newline so a diagnostic uses the line on which its lexeme began.

Identifier names are copied into a resizable hash table. Equal spellings reuse an ID; rehashing changes bucket positions but retains IDs. With ordinary names the expected lookup time is constant after hashing the spelling. Unique identifier storage grows with the number and total size of those names.

## Conflict resolution and generation

Flex prefers the match that consumes most input; a tie goes to the earlier rule. This handles <= before < by length, exact keywords before ID by order, and valid literals before equal-length recovery patterns. For example, the valid IPv4 check runs on the entire dotted lexeme; a bad octet cannot quietly become a sequence of integers.

Flex converts the regular rules into automaton tables and writes the yylex implementation and C actions into lex.yy.c. The C compiler links that generated code with the auxiliary driver in the same translation unit. noyywrap removes the need for a separate yywrap function or Flex runtime library.

```text
mkdir -p build
flex -o build/lex.yy.c threatrule.l
cc -std=c11 -D_POSIX_C_SOURCE=200809L -O2 -Wall -Wextra \
   build/lex.yy.c -o build/scanner
python3 verify.py
```

The captured runs used Flex 2.6.4 and Apple clang 21.0.0. Appendix A contains the same complete specification as the source package. The verifier generates input files before running the compiled scanner, so the report figures are based on Flex output.
