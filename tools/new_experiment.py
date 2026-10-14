"""Create fresh keys, salt and canaries for one experiment.

Run on the host:  python tools/new_experiment.py
Writes experiments/current/ (mounted into containers as Compose secrets).
"""
import os
import secrets
import shutil
from nacl.signing import SigningKey

out = os.path.join(os.path.dirname(__file__), "..", "experiments", "current")
shutil.rmtree(out, ignore_errors=True)
os.makedirs(out)


def write(name, value):
    path = os.path.join(out, name)
    with open(path, "w") as f:
        f.write(value)
    os.chmod(path, 0o644)  # containers run as uid 10001 and must read it


exp_id = "exp_" + secrets.token_hex(3)
write("exp_id", exp_id)
write("red_key", secrets.token_hex(16))
write("blue_key", secrets.token_hex(16))
write("admin_key", secrets.token_hex(16))
write("exp_salt", secrets.token_hex(16))
write("canary_b", f"CNRY-B-{exp_id}-{secrets.token_hex(8)}")
write("canary_m", f"CNRY-M-{exp_id}-{secrets.token_hex(8)}")
write("canary_r", f"CNRY-R-{exp_id}-{secrets.token_hex(8)}")

key = SigningKey.generate()
write("notary_key", bytes(key).hex())
# The public key is pinned here, on the host, before anything runs.
write("notary_pub", key.verify_key.encode().hex())
print("experiment", exp_id, "->", os.path.abspath(out))
