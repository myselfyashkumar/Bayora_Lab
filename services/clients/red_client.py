"""Red team client: sends every payload through the gateway, prints results."""
import json
import time
import urllib.request

KEY = open("/run/secrets/red_key").read().strip()
CANARY = open("/run/secrets/canary_r").read().strip()

for line in open("/app/payloads.jsonl"):
    prompt = json.loads(line)["prompt"].replace("{CANARY_R}", CANARY)
    req = urllib.request.Request(
        "http://gateway:8000/v1/attack", method="POST",
        data=json.dumps({"prompt": prompt}).encode(),
        headers={"x-api-key": KEY, "content-type": "application/json"})
    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
    reply = json.loads(raw)
    print(json.dumps({"status": reply["status"], "text": reply["text"],
                      "bytes": len(raw), "seconds": round(time.monotonic() - t0, 3)}))
