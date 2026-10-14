"""Sealed defense runner. Holds Blue's policy; only the gateway can reach it."""
import re

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()
rules: list[re.Pattern] = []


class Policy(BaseModel):
    block_patterns: list[str]


class Item(BaseModel):
    stage: str  # "input" or "output"
    text: str


@app.post("/policy")
def load(p: Policy):
    global rules
    rules = [re.compile(x, re.IGNORECASE) for x in p.block_patterns]
    return {"loaded": len(rules)}


@app.post("/inspect")
def inspect(item: Item):
    hit = any(r.search(item.text) for r in rules)
    return {"decision": "block" if hit else "allow", "score": 1.0 if hit else 0.0}
