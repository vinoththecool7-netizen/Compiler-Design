# Task 2 Compiler Phase Outputs

## Source and lexical output

```text
RULE ssh_attack IF src_ip == 10.0.0.5 AND port == 22 AND attempts > 5
THEN ALERT "SSH brute force" ;
```

```text
RULE  ID(ssh_attack)  IF  ID(src_ip)  RELOP(==)  IPV4(10.0.0.5)
AND  ID(port)  RELOP(==)  PORT(22)  AND  ID(attempts)  RELOP(>)
INTEGER(5)  THEN  ALERT  STRING("SSH brute force")  SEMI
```

## Syntax and semantics

```text
Rule ssh_attack
├─ Condition: AND
│  ├─ AND
│  │  ├─ EQ(src_ip, 10.0.0.5)
│  │  └─ EQ(port, 22)
│  └─ GT(attempts, 5)
└─ Action: ALERT("SSH brute force")
```

The parser makes AND left associative and builds the tree above. Semantic analysis checks that the rule name is unique; src_ip is IPv4, port is a 16-bit port and attempts is an unsigned count; comparison operands agree; and ALERT takes a string. The validated condition is Boolean. The scanner interns four identifier spellings; the semantic table would add their bindings and types. A diagnostic handler attaches source locations to lexer, parser and type errors and prevents publishing any invalid package.

## Intermediate code and optimization

```text
t1 = EQ_IP(src_ip, 0x0A000005); IF_FALSE t1 GOTO end
t2 = EQ_PORT(port, 22);        IF_FALSE t2 GOTO end
t3 = GT_U64(attempts, 5);      IF_FALSE t3 GOTO end
EMIT_ALERT "SSH brute force"
end: RETURN
```

This three-address form preserves short-circuit order. The optimizer removes the temporary Boolean assignments by combining each comparison with its failure branch. The message is interned once in the constant pool.

```text
Optimized IR: BR_NE_IP src_ip, 0x0A000005, end
              BR_NE_U16 port, 22, end
              BR_LE_U64 attempts, 5, end
              EMIT_ALERT k0; end: RETURN
```

## Target code for an illustrative rule VM

```text
0 TEST_IP_EQ src_ip, 0x0A000005, 4
1 TEST_U16_EQ port, 22, 4
2 TEST_U64_GT attempts, 5, 4
3 ALERT_CONST 0
4 RETURN                 ; constant 0 = "SSH brute force"
```

Each TEST jumps to instruction 4 on failure and otherwise falls through. The tree, IR and VM listing are design outputs; the token stream is also exercised by the scanner test.
