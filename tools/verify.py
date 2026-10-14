"""Independent audit verifier. Needs only Python and PyNaCl.

  python tools/verify.py AUDIT_DB CHECKPOINTS_JSONL NOTARY_PUB_FILE
Exit code 0 = intact, 1 = tampering detected.
"""
import hashlib
import json
import sqlite3
import sys

from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey


def fail(msg):
    print("FAIL:", msg)
    sys.exit(1)


def main(db_path, ckpt_path, pub_path):
    vk = VerifyKey(bytes.fromhex(open(pub_path).read().strip()))
    rows = sqlite3.connect(db_path).execute(
        "SELECT seq, body, prev, hash FROM events ORDER BY seq").fetchall()
    prev, heads = "00" * 32, {}
    for i, (seq, body, p, h) in enumerate(rows):
        if seq != i:
            fail(f"sequence gap: expected {i}, found {seq}")
        if json.loads(body)["seq"] != seq:
            fail(f"event {seq} carries the wrong sequence number")
        if p != prev:
            fail(f"broken link at event {seq}")
        if hashlib.sha256(bytes.fromhex(p) + body.encode()).hexdigest() != h:
            fail(f"hash mismatch at event {seq}")
        heads[seq], prev = h, h
    checked = 0
    for line in open(ckpt_path):
        c = json.loads(line)
        try:
            vk.verify(f"{c['exp']}|{c['seq']}|{c['head']}".encode(), bytes.fromhex(c["sig"]))
        except BadSignatureError:
            fail(f"checkpoint at event {c['seq']} has an invalid signature")
        if c["seq"] not in heads:
            fail(f"chain is shorter than signed checkpoint {c['seq']}")
        if heads[c["seq"]] != c["head"]:
            fail(f"chain does not match signed checkpoint {c['seq']}")
        checked += 1
    if checked == 0:
        fail("no signed checkpoints found")
    print(f"OK: {len(rows)} events, {checked} signed checkpoints verified")


if __name__ == "__main__":
    main(*sys.argv[1:4])
