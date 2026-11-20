# Task 4 Compiler Construction Tools

| Tool category | Place in ThreatRule |
| --- | --- |
| Scanner generator | Flex converts token patterns into a C scanner. |
| Parser generator | A Bison grammar can check rule structure and Boolean precedence. |
| Syntax directed translation | Grammar actions can construct AST nodes and typed IR. |
| Code generator generator | An instruction selection tool can map IR patterns to a VM or branch target. |
| Data flow analysis engine | Tracks constants and reachability through branches for optimization. |
| Compiler construction toolkit | Provides reusable IR, diagnostics and passes if the backend grows. |

Flex keeps regular patterns and conflict priority in one place. A manual scanner would offer tighter control of chunking and buffers but would also need its own lookahead, recovery and regression tests.
