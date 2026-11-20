# Task 6 Token Specification

An alphabet is a set of symbols; a string is a finite sequence over it, including the empty string ε. A language is a set of strings. Union A | B accepts either language, concatenation AB joins one string from each, and A* repeats A zero or more times. A+ repeats one or more times, and A? denotes optionality. Flex evaluates these definitions over input bytes.

```text
D       [0-9]
L       [A-Za-z_]
IDENT   L(L|D)*
KW      RULE|IF|AND|OR|THEN|ALERT|BLOCK
DEC     D+
OCTET   D{1,3} and value 0 through 255
IPV4    OCTET[.]OCTET[.]OCTET[.]OCTET
IPLIKE  D+([.]D*)+
BODY    ([^"\\\r\n]|\\["\\nrt])
STRING  "{BODY}*"  (opening and closing quotes are literal)
RELOP   ==|!=|<=|>=|<|>
SEMI    ;
COMMENT #[^\r\n]*
HSPACE  [ \t\f\v]+
NEWLINE \r?\n
```

| Token | Pattern and sample | Returned attribute |
| --- | --- | --- |
| Keywords | KW · RULE, ALERT | Token kind |
| ID | IDENT · ssh_attack | Interned symbol ID |
| INTEGER | DEC · 5 | Unsigned 64-bit numeric value |
| PORT | DEC after port RELOP · 22 | Value 0 through 65535 |
| IPV4 | IPV4 · 10.0.0.5 | Packed value 0x0A000005 |
| STRING | STRING · "SSH brute force" | Raw quoted spelling |
| RELOP | RELOP · <= | Operator spelling |
| SEMI | SEMI · ; | Token kind |
| Skipped | COMMENT / HSPACE / NEWLINE | None; newline resets port context |

A dotted candidate is consumed as a unit with IPLIKE, then validated as exactly four octets. Leading zeroes are read in decimal. Integer and port spellings overlap, so the same-line port field and following operator supply context; port is otherwise an ID. The parser must reject an inappropriate token in a port comparison. Exact keyword rules appear before IDENT: RULE matches both equally, while RULEbook is a longer IDENT. The scanner accepts LF and CRLF line endings.
