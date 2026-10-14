"""Notary: signs audit-chain head hashes with a key the gateway never holds."""
import json

from fastapi import FastAPI
from nacl.signing import SigningKey
from pydantic import BaseModel

with open("/run/secrets/notary_key") as f:
    KEY = SigningKey(bytes.fromhex(f.read().strip()))

app = FastAPI()


class Checkpoint(BaseModel):
    exp: str
    seq: int
    head: str


@app.post("/sign")
def sign(c: Checkpoint):
    msg = f"{c.exp}|{c.seq}|{c.head}".encode()
    sig = KEY.sign(msg).signature.hex()
    with open("/data/checkpoints.jsonl", "a") as f:  # the notary keeps its own copy
        f.write(json.dumps({"exp": c.exp, "seq": c.seq, "head": c.head, "sig": sig}) + "\n")
    return {"sig": sig}
