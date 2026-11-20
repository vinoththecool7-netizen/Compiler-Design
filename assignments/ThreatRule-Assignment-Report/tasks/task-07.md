# Task 7 Token Recognition

The diagrams describe the logical recognizers. Start is S. Brackets mark accepting states, and ↶ means leave the first unmatched lookahead byte available to the next token. EOF can end an accepted token without retraction. Flex performs maximal munch with its generated DFA; no manual unput is needed.

## Relational operators

```text
S ── < or > ──▶ [A1] ── = ──▶ [A2]  emit <= or >=
                   └── other ↶       emit < or >
S ── = or ! ──▶ N ────── = ──▶ [A2]  emit == or !=
                   └── other ↶       diagnose lone = or !
```

## Identifiers and keywords

```text
S ── L ──▶ [I] ── L or D ──▶ [I]  (loop)
            └── other ↶ ──▶ exact keyword lookup, otherwise ID
```

## Unsigned integers and ports

```text
S ── D ──▶ [N] ── D ──▶ [N]  (loop)
            ├── . ──▶ dotted candidate path below
            └── other ↶ ──▶ numeric range check and INTEGER or PORT
```

## Dotted candidates and IPv4 validation

```text
S ─ D+ ─▶ [N] ─ . ─▶ [P] ─ D or . ─▶ [P]  (loop)
                        └── other ↶ ──▶ validate whole candidate

Validator: S ─ OCTET ─▶ O1 ─ . OCTET ─▶ O2
                           ─ . OCTET ─▶ O3 ─ . OCTET ─▶ [O4]
Accept at O4 only if the entire candidate was consumed.
```

At P, the accepting state is for a dotted candidate, so a short or out-of-range address is reported once. The separate validator enforces one to three digits per component and checks the numeric range. These diagrams are applied alongside other token rules; for example, a feed hash can outrank the numeric or identifier path.

## Hand traces

| Input | Transitions and result |
| --- | --- |
| ssh_attack followed by space | S takes s to I; the remaining letters and underscore loop at I. Space is left for whitespace handling. The spelling is not a keyword, so return ID with a symbol ID. |
| 10.0.0.5 followed by space | Digits 10 reach N; the first dot enters P. Continue through 0.0.5, leave the space and validate octets 10, 0, 0, 5. Return IPV4 with 0x0A000005. |
| < compared with <= | Both start at A1. If the next byte is =, move to A2 and emit <=; otherwise keep the lookahead and emit <. |
