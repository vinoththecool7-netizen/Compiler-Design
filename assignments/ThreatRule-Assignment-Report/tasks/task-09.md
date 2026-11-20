# Task 9 Verification Results

The verifier checks full token kind sequences, selected attribute values, diagnostic counts and line numbers, and process exit status. Cases with lexical errors must still produce the expected tokens after the fault. The verifier also asserts that each baseline load produces 18 tokens per rule and that the adapted scanner produces 10 tokens per partner rule.

| Case | Expected behavior checked | Observed |
| --- | --- | --- |
| Sample rule | 18 tokens, packed IPv4 and port value 22 | Pass |
| Boundaries | IPv4 endpoints, ports 0 and 65535; CRLF and final EOF | Pass |
| Keywords and operators | All seven keywords and six comparisons, longer ID, comments, escape and reused symbol | Pass |
| Three brief faults | Bad IPv4, open quote and @ on lines 1–3; full rule continues on line 4 | Pass |
| Other malformed input | Port overflow, malformed IPv4, uint64 overflow, invalid escape and EOF quote | Pass |
| Valid partner literals | Three digest lengths, two CVE shapes, URL query and fragment | Pass |
| Partner recovery | Three diagnostics on line 1; good CVE and URL on later lines | Pass |
| Partner input in base mode | New spellings split into ordinary tokens; seven diagnostics in small fixture | Pass |

## Excerpt from the actual scanner run

```text
line 1: invalid IPv4 address near `10.0.300.5`
line 2: unterminated string near `"Login failed ;`
line 3: unexpected character near `@`
```

After the @ on line 3, the dump still reports attempts, > and 5. Line 4 starts with RULE and yields the full sample rule. That run returned status 1 after EOF. The full trace and the other seven cases are preserved in evidence/test-runs.txt.

## Reproducing the run

Run python3 verify.py from the project directory. It builds the scanner, generates the fixtures under build/, executes each case and writes the environment, token dumps and timing records under evidence/. Run build/scanner --dump build/sample.tr to see one complete token trace; add --feed for the extended cases.
