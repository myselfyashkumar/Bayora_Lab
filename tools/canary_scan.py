"""Search files for secrets that must never reach them.

  python tools/canary_scan.py SECRETS_DIR NAME[,NAME...] FILE [FILE...]
  python tools/canary_scan.py --self-test SECRETS_DIR
Looks for each secret raw, base64 (all three alignments), hex and reversed.
"""
import base64
import os
import sys
import tempfile


def forms(s):
    b = s.encode()
    out = {"raw": b, "hex": b.hex().encode(), "reversed": b[::-1]}
    for i in range(3):  # base64 depends on alignment; take a middle slice of each
        enc = base64.b64encode(b"x" * i + b)
        out[f"base64_{i}"] = enc[4:-4]
    return out


def scan(secrets_dir, names, files):
    hits = []
    for name in names:
        value = open(os.path.join(secrets_dir, name)).read().strip()
        for form, needle in forms(value).items():
            for path in files:
                if needle in open(path, "rb").read():
                    hits.append((name, form, path))
    return hits


if __name__ == "__main__":
    if sys.argv[1] == "--self-test":
        d = sys.argv[2]
        planted = open(os.path.join(d, "canary_b")).read().strip()
        with tempfile.NamedTemporaryFile("wb", delete=False) as f:
            f.write(b"noise " + base64.b64encode(b"yy" + planted.encode()) + b" noise")
        found = scan(d, ["canary_b"], [f.name])
        print("SELF-TEST", "PASS" if found else "FAIL", found)
        sys.exit(0 if found else 1)
    d, names, files = sys.argv[1], sys.argv[2].split(","), sys.argv[3:]
    hits = scan(d, names, files)
    for h in hits:
        print("LEAK:", *h)
    print(f"scanned {len(files)} files for {len(names)} secrets: {len(hits)} leaks")
    sys.exit(1 if hits else 0)
