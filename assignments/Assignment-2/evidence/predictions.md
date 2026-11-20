# Predictions recorded before implementation and testing

- The recursive arithmetic grammar calls E again without consuming a token. Left-recursion elimination should allow both top-down parsers to accept the same valid expressions.
- Eight ambiguous binary operators should produce 64 shift/reduce pairs. In the separate conditional grammar one dangling-else conflict should default to shifting. Two unit productions accepting the same identifier should give one reduce/reduce conflict.
- In the recursive formula parser, n enclosing parentheses should require 3n+3 simultaneously active E/T/F calls. With a 600-call experimental budget, depth 200 should exceed it. The heap-backed predictive stack should accept 10,000 levels and retain linear steps. It need not be faster on small inputs.
- Without recovery, either a missing semicolon or a missing operand should stop at the first diagnostic. Restarting from individual tokens after the error can reinterpret the suffix as new statements and increase the message count.
