# ThreatRule lexical analyzer

Single submission for Compiler Design Assignment 1 (CO1), Tasks 1–12.
The report presents the full compiler design; the executable implements the
lexical analyzer only. It never evaluates rules, queries CVEs, or accesses URLs.

## Build and run

Requires Flex, a C11 compiler with POSIX clock support, and Python 3 for verification.
From this directory:

```sh
mkdir -p build
flex -o build/lex.yy.c threatrule.l
cc -std=c11 -D_POSIX_C_SOURCE=200809L -O2 -Wall -Wextra build/lex.yy.c -o build/scanner
printf '%s\n' 'RULE ssh_attack IF src_ip == 10.0.0.5 AND port == 22 AND attempts > 5 THEN ALERT "SSH brute force" ;' | build/scanner --dump
printf '%s\n' 'CVE-2024-3400 https://feeds.example/item ;' | build/scanner --feed --dump
python3 verify.py
```

Without a file the scanner reads stdin. Use a positional file path for batch
input. Baseline is the default; `--feed` enables the extended token classes.
`--dump` displays accepted tokens and attributes. Lexical diagnostics appear
on stderr, and the scanner continues through EOF. Exit status: 0 for a clean
scan, 1 for lexical diagnostics, 2 for command, file, or allocation failures.
`--quiet-errors` suppresses diagnostic printing while preserving counts.

The verifier builds the Flex-generated executable, creates the fixtures under
`build/`, checks eight functional cases, and measures four baseline file sizes
plus feed comparisons. It overwrites the three captures in `evidence/`; keep a
copy of the supplied evidence if you want to compare machines. The benchmark
records nine warm-cache measurements after one warm-up per row. Reported times
are from inside the executable, with token and error printing disabled.

## Scope

Case-sensitive keywords, ASCII identifiers, unsigned decimal integers, dotted
IPv4 literals, double-quoted strings, comparisons, semicolon terminators and
hash-sign comments. Decimal values after `port RELOP` on the same line are
classified as ports. The extended mode adds bare fixed-length hex digests,
CVE-shaped IDs, and a restricted HTTP(S) URL format. Grammar and field types
beyond numeric port classification are a later parser/semantic phase.

## Report by task

- [Task 1](tasks/task-01.md) — Compare language processors
- [Task 2](tasks/task-02.md) — Trace the compiler phases
- [Task 3](tasks/task-03.md) — Group phases into front and back ends
- [Task 4](tasks/task-04.md) — Choose compiler construction tools
- [Task 5](tasks/task-05.md) — Explain lexical analysis and recovery
- [Task 6](tasks/task-06.md) — Specify ThreatRule tokens
- [Task 7](tasks/task-07.md) — Document token recognition
- [Task 8](tasks/task-08.md) — Add Flex scanner implementation
- [Task 9](tasks/task-09.md) — Verify scanner behavior
- [Task 10](tasks/task-10.md) — Record scanner performance
- [Task 11](tasks/task-11.md) — Recommend the scanner design
- [Task 12](tasks/task-12.md) — Evaluate partner feeds and publish the report

[Complete Word report](ThreatRule%20Assignment%20Report.docx)
