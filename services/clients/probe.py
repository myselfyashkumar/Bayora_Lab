"""Toolbox used by the test script from inside red_probe and blue_probe.

  python probe.py tcp HOST PORT            -> OPEN or BLOCKED
  python probe.py http METHOD PATH KEY [JSON]  -> HTTP status code
  python probe.py write PATH               -> WRITE_OK or WRITE_DENIED
  python probe.py forkbomb                 -> how many processes we managed to start
"""
import json
import os
import signal
import socket
import sys
import time
import urllib.error
import urllib.request

GATEWAY = "http://gateway:8000"


def tcp(host, port):
    try:
        with socket.create_connection((host, int(port)), timeout=2):
            print("OPEN")
            return 0
    except OSError as e:
        print(f"BLOCKED ({type(e).__name__})")
        return 1


def http(method, path, keyname, body=None):
    key = open(f"/run/secrets/{keyname}").read().strip() if keyname != "none" else ""
    req = urllib.request.Request(GATEWAY + path, method=method,
                                 data=body.encode() if body else None,
                                 headers={"x-api-key": key, "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            print(r.status)
    except urllib.error.HTTPError as e:
        print(e.code)
    return 0


def write(path):
    try:
        with open(path, "w") as f:
            f.write("x")
        print("WRITE_OK")
    except OSError:
        print("WRITE_DENIED")
    return 0


def forkbomb():
    kids = []
    try:
        for _ in range(1000):
            pid = os.fork()
            if pid == 0:
                time.sleep(30)
                os._exit(0)
            kids.append(pid)
    except OSError:
        pass
    print(len(kids))
    for pid in kids:
        os.kill(pid, signal.SIGKILL)
        os.waitpid(pid, 0)
    return 0

def attack(prompt):
    key = open("/run/secrets/red_key").read().strip()
    req = urllib.request.Request(GATEWAY + "/v1/attack", method="POST",
                                 data=json.dumps({"prompt": prompt}).encode(),
                                 headers={"x-api-key": key, "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
    print(len(raw), json.loads(raw)["status"])  # size and decision, never the text
    return 0

if __name__ == "__main__":
    cmd, args = sys.argv[1], sys.argv[2:]
    sys.exit({"tcp": tcp, "http": http, "write": write, "forkbomb": forkbomb, "attack": attack}[cmd](*args))
