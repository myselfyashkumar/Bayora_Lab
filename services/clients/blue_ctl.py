"""Blue team client.  python blue_ctl.py upload | release"""
import json
import sys
import urllib.error
import urllib.request

KEY = open("/run/secrets/blue_key").read().strip()


def call(method, path, body=None):
    req = urllib.request.Request("http://gateway:8000" + path, method=method,
                                 data=json.dumps(body).encode() if body else None,
                                 headers={"x-api-key": KEY, "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


if sys.argv[1] == "upload":
    policy = json.load(open("/app/policy.json"))
    # Blue's canary lives inside its own policy; it must never reach Red.
    policy["block_patterns"].append(open("/run/secrets/canary_b").read().strip())
    print(call("POST", "/v1/blue/policy", policy))
else:
    print(json.dumps(call("GET", "/v1/release")[1], indent=1))
