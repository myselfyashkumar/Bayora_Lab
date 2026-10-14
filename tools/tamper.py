"""Make a tampered copy of the evidence for the audit tests.

  python tools/tamper.py MODE EVIDENCE_DIR OUT_DIR
MODE: edit | delete | swap | truncate | rechain | forge
"""
import hashlib
import json
import os
import shutil
import sqlite3
import sys

from nacl.signing import SigningKey

mode, src, out = sys.argv[1:4]
shutil.rmtree(out, ignore_errors=True)
shutil.copytree(src, out)
db = sqlite3.connect(os.path.join(out, "audit.db"))
rows = db.execute("SELECT seq, body, prev, hash FROM events ORDER BY seq").fetchall()
mid = len(rows) // 2


def edited(body):
    e = json.loads(body)
    e["decision"] = "allow" if e["decision"] != "allow" else "block"
    return json.dumps(e, sort_keys=True, separators=(",", ":"))


if mode == "edit":
    db.execute("UPDATE events SET body=? WHERE seq=?", (edited(rows[mid][1]), mid))
elif mode == "delete":
    db.execute("DELETE FROM events WHERE seq=?", (mid,))
elif mode == "swap":
    a, b = rows[mid], rows[mid + 1]
    db.execute("UPDATE events SET body=?, prev=?, hash=? WHERE seq=?", (b[1], b[2], b[3], a[0]))
    db.execute("UPDATE events SET body=?, prev=?, hash=? WHERE seq=?", (a[1], a[2], a[3], b[0]))
elif mode == "truncate":
    db.execute("DELETE FROM events WHERE seq >= ?", (len(rows) - 3,))
elif mode in ("rechain", "forge"):
    # Edit one event, then recompute every later hash so the chain looks valid.
    prev = rows[mid][2]
    for seq, body, _, _ in rows[mid:]:
        body = edited(body) if seq == mid else body
        h = hashlib.sha256(bytes.fromhex(prev) + body.encode()).hexdigest()
        db.execute("UPDATE events SET body=?, prev=?, hash=? WHERE seq=?", (body, prev, h, seq))
        prev = h
    if mode == "forge":
        # Re-sign every checkpoint with a key we invent (we do not have the notary's).
        heads = dict(db.execute("SELECT seq, hash FROM events").fetchall())
        fake = SigningKey.generate()
        path = os.path.join(out, "checkpoints.jsonl")
        cps = [json.loads(line) for line in open(path)]
        with open(path, "w") as f:
            for c in cps:
                c["head"] = heads[c["seq"]]
                c["sig"] = fake.sign(f"{c['exp']}|{c['seq']}|{c['head']}".encode()).signature.hex()
                f.write(json.dumps(c) + "\n")
db.commit()
print("tampered:", mode)
