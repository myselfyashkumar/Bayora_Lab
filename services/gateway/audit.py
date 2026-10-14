"""Append-only, hash-chained audit log stored in SQLite."""
import hashlib
import json
import sqlite3
import threading
import time

GENESIS = "00" * 32


def event_hash(prev_hex: str, body: str) -> str:
    return hashlib.sha256(bytes.fromhex(prev_hex) + body.encode()).hexdigest()


class Audit:
    def __init__(self, path: str, exp_id: str):
        self.exp_id = exp_id
        self.lock = threading.Lock()
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS events ("
            " seq INTEGER PRIMARY KEY, body TEXT NOT NULL,"
            " prev TEXT NOT NULL, hash TEXT NOT NULL)")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS checkpoints ("
            " seq INTEGER PRIMARY KEY, head TEXT NOT NULL, sig TEXT NOT NULL)")
        self.db.commit()

    def append(self, actor, action, decision, commit=""):
        with self.lock:
            row = self.db.execute(
                "SELECT seq, hash FROM events ORDER BY seq DESC LIMIT 1").fetchone()
            seq, prev = (row[0] + 1, row[1]) if row else (0, GENESIS)
            event = {"seq": seq, "exp": self.exp_id, "ts": int(time.time()),
                     "actor": actor, "action": action,
                     "decision": decision, "commit": commit}
            body = json.dumps(event, sort_keys=True, separators=(",", ":"))
            h = event_hash(prev, body)
            self.db.execute("INSERT INTO events VALUES (?,?,?,?)", (seq, body, prev, h))
            self.db.commit()
            return seq, h

    def head(self):
        row = self.db.execute(
            "SELECT seq, hash FROM events ORDER BY seq DESC LIMIT 1").fetchone()
        return row if row else (-1, GENESIS)

    def save_checkpoint(self, seq, head, sig):
        with self.lock:
            self.db.execute("INSERT OR REPLACE INTO checkpoints VALUES (?,?,?)",
                            (seq, head, sig))
            self.db.commit()
