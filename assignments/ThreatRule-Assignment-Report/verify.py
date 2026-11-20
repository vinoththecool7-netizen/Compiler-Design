"""Build the Flex scanner, assert token/diagnostic behavior, and benchmark it."""
import csv
import os
from pathlib import Path
import statistics
import subprocess

os.chdir(Path(__file__).resolve().parent)
build, evidence = Path("build"), Path("evidence")
build.mkdir(exist_ok=True)
evidence.mkdir(exist_ok=True)
flex = os.environ.get("FLEX", "flex")
cc = os.environ.get("CC", "cc")
flags = ["-std=c11", "-D_POSIX_C_SOURCE=200809L", "-O2", "-Wall", "-Wextra"]
subprocess.run([flex, "-o", "build/lex.yy.c", "threatrule.l"], check=True)
subprocess.run([cc, *flags, "build/lex.yy.c", "-o", "build/scanner"], check=True)
versions = [subprocess.check_output([x, "--version"], text=True).splitlines()[0]
            for x in (flex, cc)]
(evidence / "environment.txt").write_text("\n".join([*versions, " ".join(flags)])+"\n")

sample = 'RULE ssh_attack IF src_ip == 10.0.0.5 AND port == 22 AND attempts > 5 THEN ALERT "SSH brute force" ;'
hashes = ["ab"*16, "de"*20, "f0"*32]
url = "https://feeds.example/item?q=1#part"
checks = []
def check(name, source, want, diagnostics=(), feed=False, attrs=()):
    path = build / (name+".tr")
    path.write_bytes(source.encode("ascii"))
    cmd = ["build/scanner", "--dump"] + (["--feed"] if feed else []) + [str(path)]
    p = subprocess.run(cmd, text=True, capture_output=True)
    lines = p.stdout.splitlines()
    observed = [x.split("\t")[1] for x in lines[:-1]]
    assert observed == want.split(), (name, observed, want, p.stderr)
    assert p.returncode == bool(diagnostics), (name, p.returncode, p.stderr)
    errors = p.stderr.splitlines()
    assert len(errors) == len(diagnostics), (name, errors, diagnostics)
    assert all(line.startswith(prefix) for line, prefix in zip(errors, diagnostics)), errors
    for fragment in attrs:
        assert fragment in p.stdout, (name, fragment, p.stdout)
    checks.append("$ "+" ".join(cmd)+"\n"+p.stdout+p.stderr+f"exit={p.returncode}\n")

check("sample",sample+"\n",
      "RULE ID IF ID RELOP IPV4 AND ID RELOP PORT AND ID RELOP INTEGER THEN ALERT STRING SEMI",
      attrs=("value=0x0A000005","PORT\t22\tvalue=22"))
check("bounds", "0.0.0.0 255.255.255.255 port == 0\r\nport == 65535",
      "IPV4 IPV4 ID RELOP PORT ID RELOP PORT",
      attrs=("value=0x00000000","value=0xFFFFFFFF","PORT\t65535\tvalue=65535"))
check("operators", 'RULE RULEbook IF AND OR THEN ALERT BLOCK <= < >= > != == ;\n'
      '# skipped\nname name "escaped \\"quote\\""',
      "RULE ID IF AND OR THEN ALERT BLOCK RELOP RELOP RELOP RELOP RELOP RELOP SEMI ID ID STRING",
      attrs=("3\tID\tname\tid=2","RULEbook"))
check("faults", 'src_ip == 10.0.300.5\nALERT "Login failed ;\nport == 22 @ attempts > 5\n'+sample,
      "ID RELOP ALERT ID RELOP PORT ID RELOP INTEGER "
      "RULE ID IF ID RELOP IPV4 AND ID RELOP PORT AND ID RELOP INTEGER THEN ALERT STRING SEMI",
      ("line 1: invalid IPv4","line 2: unterminated string","line 3: unexpected character"),
      attrs=("4\tRULE\tRULE",))
check("limits", 'port == 65536\n1.2.3\n1..2.3\n1234.2.3.4\n18446744073709551615\n'
      '18446744073709551616\n"bad\\q" ;\nALERT "unfinished\\',
      "ID RELOP INTEGER SEMI ALERT",
      ("line 1: port outside","line 2: invalid IPv4","line 3: invalid IPv4",
       "line 4: invalid IPv4","line 6: integer outside","line 7: invalid string escape",
       "line 8: unterminated string"),attrs=("value=18446744073709551615",))
check("feed_valid"," ".join(hashes+["CVE-2024-3400","CVE-2026-12345",url,";"]),
      "HASH HASH HASH CVE CVE URL SEMI",feed=True,attrs=("hash=3 cve=2 url=1",url))
check("feed_faults",'CVE-2024-123 https://bad @\nCVE-2024-3400 ;\n'+url+' ;',
      "CVE SEMI URL SEMI",("line 1: invalid CVE","line 1: invalid URL",
      "line 1: unexpected character"),feed=True,attrs=("3\tURL",))
check("feed_base", hashes[0]+' CVE-2024-3400 https://feeds.example/i ;',
      "ID ID INTEGER INTEGER ID ID ID ID SEMI",
      ("line 1: unexpected character",)*7)
(evidence / "test-runs.txt").write_text("\n".join(checks))

def data(name, n, feed=False):
    path = build / (name+".tr")
    with path.open("w") as f:
        for i in range(n):
            if feed:
                key, literal = [("file_hash", hashes[(i // 3) % len(hashes)]),
                                ("vuln", "CVE-2024-3400"), ("ref", url)][i%3]
                f.write(f'RULE partner_{i} IF {key} == {literal} THEN ALERT "Partner match" ;\n')
            else:
                f.write(sample.replace("ssh_attack",f"ssh_{i}")+"\n")
    return path

def bench(path,n,mode,dataset):
    cmd = ["build/scanner","--quiet-errors"] + (["--feed"] if mode=="feed" else []) + [str(path)]
    runs = []
    for i in range(10):  # warm once, then retain nine timed scans
        p = subprocess.run(cmd,capture_output=True,text=True)
        row = dict(pair.split("=") for pair in p.stdout.split())
        assert not p.stderr and p.returncode == bool(int(row["errors"])), p
        ms = float(row.pop("ms"))
        if i == 0:
            first = row
        else:
            assert row == first
            runs.append(ms)
    counts = {k:int(v) for k,v in first.items()}
    if dataset == "legacy":
        assert counts["tokens"] == n*18 and counts["errors"] == 0
    if dataset == "partner" and mode == "feed":
        assert counts["tokens"] == n*10 and counts["errors"] == 0
        assert [counts[x] for x in ("hash","cve","url")] == [1667,1667,1666]
    if dataset == "partner" and mode == "base":
        assert all(counts[x]==0 for x in ("hash","cve","url")) and counts["errors"]>0
    return dict(dataset=dataset,mode=mode,rules=n,lines=n,bytes=path.stat().st_size,
                **counts,median_ms=f"{statistics.median(runs):.3f}",
                min_ms=f"{min(runs):.3f}",max_ms=f"{max(runs):.3f}",
                samples_ms=" ".join(f"{x:.6f}" for x in runs))
rows = []
for n in (100,1000,10000,100000):
    path = data(f"rules_{n}",n)
    rows.append(bench(path,n,"base","legacy"))
rows.append(bench(path,n,"feed","legacy"))
path = data("partner_5000",5000,True)
for mode in ("base","feed"):
    rows.append(bench(path,5000,mode,"partner"))
with (evidence/"benchmark.csv").open("w",newline="") as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
print(f"{len(checks)} functional cases passed; {len(rows)} benchmark rows recorded.")
