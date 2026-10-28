"""Model service.

Without OLLAMA_URL it is a stub for development and tests. The stub is
deliberately leaky: if asked for its system prompt it repeats it, including
the CNRY-M canary, so the gateway's canary filter can be tested end to end.

With OLLAMA_URL set (docker-compose.ollama.yml) it forwards to a real small
model with fixed settings, so runs are repeatable.
"""
import os

import httpx
from fastapi import FastAPI
from pydantic import BaseModel

with open("/run/secrets/canary_m") as f:
    SYSTEM_PROMPT = f"You are a test model. Internal tag: {f.read().strip()}"

OLLAMA = os.getenv("OLLAMA_URL")
MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b")
NUM_PREDICT = int(os.getenv("OLLAMA_NUM_PREDICT", "64"))  # shorter answers = faster, steadier replies
app = FastAPI()


class Req(BaseModel):
    prompt: str


@app.post("/generate")
def generate(r: Req):
    if OLLAMA:
        resp = httpx.post(f"{OLLAMA}/api/generate", timeout=60, json={
            "model": MODEL, "system": SYSTEM_PROMPT, "prompt": r.prompt, "stream": False,
            "options": {"temperature": 0, "seed": 42, "num_predict": NUM_PREDICT}})
        resp.raise_for_status()
        return {"text": resp.json()["response"]}
    lowered = r.prompt.lower()
    if "system prompt" in lowered:
        return {"text": f"My system prompt is: {SYSTEM_PROMPT}"}
    if "long reply" in lowered:  # lets the tests check that long answers get trimmed
        return {"text": "word " * 700}
    return {"text": f"[stub] I received a prompt of {len(r.prompt)} characters."}