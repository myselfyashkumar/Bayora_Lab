"""Bayora console: a live dashboard for the lab.

Runs on the host, OUTSIDE the sealed lab. It talks to the gateway's admin
endpoints and drives Red and Blue through `docker compose exec`. It never
reads Blue's policy and never joins a lab network. Standard library only.

  python3 tools/console/app.py     ->  http://localhost:8090
"""
import json
import os
import shutil
import subprocess
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SECRETS = os.path.join(ROOT, "experiments", "current")
LIVE = os.path.join(ROOT, "evidence", "console_live")
PORT = int(os.getenv("CONSOLE_PORT", "8090"))
GATEWAY = "http://127.0.0.1:8000"
ALLOWED_HOSTS = {f"127.0.0.1:{PORT}", f"localhost:{PORT}"}
TAMPER_MODES = ["edit", "delete", "swap", "truncate", "rechain", "forge"]
attack_lock = threading.Lock()  # one attack at a time keeps timing steady
audit_lock = threading.Lock()


def secret(name):
    with open(os.path.join(SECRETS, name)) as f:
        return f.read().strip()


def run(cmd, timeout=120):
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout + p.stderr).strip()


def gateway(method, path):
    req = urllib.request.Request(GATEWAY + path, method=method,
                                 headers={"x-api-key": secret("admin_key")})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def api_events(after):
    try:
        data = gateway("GET", f"/admin/events?after={int(after)}")
        return {"exp": secret("exp_id"), "status": data["status"], "events": data["events"]}
    except Exception as e:
        return {"error": f"Lab not reachable ({type(e).__name__}). Start it with: make demo-real"}


def api_attack(body):
    prompt = body.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 8000 or "\x00" in prompt:
        return 400, {"error": "The prompt must be 1 to 8000 characters."}
    if not attack_lock.acquire(blocking=False):
        return 429, {"error": "Another attack is still running."}
    try:
        _, out = run(["docker", "compose", "exec", "-T", "red_probe",
                      "python", "probe.py", "attackjson", prompt])
    finally:
        attack_lock.release()
    try:
        reply = json.loads(out.splitlines()[-1])
    except (ValueError, IndexError):
        return 502, {"error": "The attack failed.", "detail": out[-300:]}
    if not body.get("show_text"):
        reply["text"] = ""  # model output never reaches the browser unless asked for
    return 200, reply


def api_blue_upload():
    _, out = run(["docker", "compose", "exec", "-T", "blue_probe", "python", "blue_ctl.py", "upload"])
    return {"ok": "'loaded'" in out, "raw": out[-200:]}


def snapshot(dest):
    gateway("POST", "/admin/checkpoint")
    shutil.rmtree(dest, ignore_errors=True)
    os.makedirs(dest)
    for src, name in (("gateway:/data/audit.db", "audit.db"),
                      ("notary:/data/checkpoints.jsonl", "checkpoints.jsonl")):
        code, out = run(["docker", "compose", "cp", src, os.path.join(dest, name)])
        if code != 0:
            raise RuntimeError(out[-200:])
    shutil.copy(os.path.join(SECRETS, "notary_pub"), os.path.join(dest, "notary_pub"))


def verify(folder):
    _, out = run(["python3", os.path.join(ROOT, "tools", "verify.py"),
                  os.path.join(folder, "audit.db"),
                  os.path.join(folder, "checkpoints.jsonl"),
                  os.path.join(folder, "notary_pub")])
    return out.splitlines()[-1] if out else "FAIL: the verifier printed nothing"


def api_verify():
    with audit_lock:
        try:
            snapshot(LIVE)
            message = verify(LIVE)
        except Exception as e:
            return 500, {"error": str(e)[:200]}
    return 200, {"ok": message.startswith("OK"), "message": message}


def api_tamper(mode):
    if mode not in TAMPER_MODES:
        return 400, {"error": "Unknown tamper mode."}
    with audit_lock:
        try:
            snapshot(LIVE)
            before = verify(LIVE)
            bad = LIVE + "_tampered"
            run(["python3", os.path.join(ROOT, "tools", "tamper.py"), mode, LIVE, bad])
            after = verify(bad)
            shutil.rmtree(bad, ignore_errors=True)
        except Exception as e:
            return 500, {"error": str(e)[:200]}
    return 200, {"mode": mode, "before": before, "after": after, "detected": after.startswith("FAIL")}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, code, body, ctype="application/json"):
        raw = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy",
                         "default-src 'none'; connect-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'")
        self.end_headers()
        self.wfile.write(raw)

    def host_ok(self):
        return self.headers.get("Host", "") in ALLOWED_HOSTS

    def do_GET(self):
        if not self.host_ok():
            return self.reply(403, {"error": "bad host"})
        url = urlparse(self.path)
        if url.path == "/":
            with open(os.path.join(HERE, "index.html"), "rb") as f:
                return self.reply(200, f.read(), "text/html; charset=utf-8")
        if url.path == "/api/events":
            return self.reply(200, api_events(parse_qs(url.query).get("after", ["-1"])[0]))
        self.reply(404, {"error": "not found"})

    def do_POST(self):
        if not self.host_ok() or self.headers.get("X-Console") != "1":
            return self.reply(403, {"error": "forbidden"})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(min(size, 20000)) or b"{}")
        except ValueError:
            return self.reply(400, {"error": "bad json"})
        path = urlparse(self.path).path
        if path == "/api/attack":
            return self.reply(*api_attack(body))
        if path == "/api/blue/upload":
            return self.reply(200, api_blue_upload())
        if path == "/api/verify":
            return self.reply(*api_verify())
        if path == "/api/tamper":
            return self.reply(*api_tamper(body.get("mode")))
        self.reply(404, {"error": "not found"})


if __name__ == "__main__":
    print(f"Bayora console: http://localhost:{PORT}   (Ctrl+C to stop)")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()