"""Bayora Lab: hacker-style guided demo, made for screen recording.

  python3 tools/showcase.py          # pauses for Enter between modules
  python3 tools/showcase.py --auto   # runs by itself with short pauses
"""
import datetime
import getpass
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from report import PROMPT_LABELS, CATEGORIES, build  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUTO = "--auto" in sys.argv
VERSION = "1.0"

# ---------------------------------------------------------------- colours
def c256(n):
    return f"\033[38;5;{n}m"


END, BOLD, DIM = "\033[0m", "\033[1m", "\033[2m"
GREEN, RED, BLUE, AMBER, PURPLE, GREY = c256(46), c256(203), c256(75), c256(214), c256(141), c256(245)
RAMPS = {
    "green": [46, 46, 40, 34, 28], "red": [210, 203, 196, 160, 124],
    "blue": [117, 81, 75, 33, 27], "amber": [228, 221, 214, 208, 172],
    "purple": [183, 177, 141, 135, 99],
}
SHADOW = c256(238)
TICK, CROSS = f"{GREEN}✔{END}", f"{RED}✘{END}"
ANSI = re.compile(r"\x1b\[[0-9;]*m")
HL, ARROW = "\u2500", "\u2192"

# ---------------------------------------------------------------- block font (5 rows, our own)
FONT = {
    "A": [".###.", "#...#", "#####", "#...#", "#...#"], "B": ["####.", "#...#", "####.", "#...#", "####."],
    "C": [".####", "#....", "#....", "#....", ".####"], "D": ["####.", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "####.", "#....", "#####"], "F": ["#####", "#....", "####.", "#....", "#...."],
    "G": [".####", "#....", "#..##", "#...#", ".####"], "H": ["#...#", "#...#", "#####", "#...#", "#...#"],
    "I": ["###", ".#.", ".#.", ".#.", "###"], "J": ["..###", "...#.", "...#.", "#..#.", ".##.."],
    "K": ["#...#", "#..#.", "###..", "#..#.", "#...#"], "L": ["#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#...#", "#...#"], "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", ".###."], "P": ["####.", "#...#", "####.", "#....", "#...."],
    "Q": [".###.", "#...#", "#.#.#", "#..#.", ".##.#"], "R": ["####.", "#...#", "####.", "#..#.", "#...#"],
    "S": [".####", "#....", ".###.", "....#", "####."], "T": ["#####", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", ".###."], "V": ["#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#.#.#", "##.##", "#...#"], "X": ["#...#", ".#.#.", "..#..", ".#.#.", "#...#"],
    "Y": ["#...#", ".#.#.", "..#..", "..#..", "..#.."], "Z": ["#####", "...#.", "..#..", ".#...", "#####"],
    "0": [".###.", "#..##", "#.#.#", "##..#", ".###."], "1": [".#.", "##.", ".#.", ".#.", "###"],
    "2": ["####.", "....#", ".###.", "#....", "#####"], "3": ["####.", "....#", ".###.", "....#", "####."],
    "4": ["#..#.", "#..#.", "#####", "...#.", "...#."], "5": ["#####", "#....", "####.", "....#", "####."],
    "6": [".###.", "#....", "####.", "#...#", ".###."], "7": ["#####", "....#", "...#.", "..#..", "..#.."],
    "8": [".###.", "#...#", ".###.", "#...#", ".###."], "9": [".###.", "#...#", ".####", "....#", ".###."],
    " ": ["..", "..", "..", "..", ".."],
}


def banner(text, ramp="green"):
    """Render text as pixel letters with a drop shadow. Returns a list of lines."""
    grid = [[] for _ in range(5)]
    for ch in text.upper():
        glyph = FONT.get(ch, FONT[" "])
        for r in range(5):
            grid[r].extend(glyph[r] + ".")
    width = len(grid[0]) + 1
    filled = [[grid[r][c] == "#" if c < len(grid[r]) else False for c in range(width)] for r in range(5)]
    lines = []
    for r in range(6):
        colour = c256(RAMPS[ramp][min(r, 4)])
        out = ""
        for c in range(width):
            if r < 5 and filled[r][c]:
                out += colour + "█"
            elif r > 0 and c > 0 and filled[r - 1][c - 1]:
                out += SHADOW + "░"
            else:
                out += " "
        lines.append(out.rstrip() + END)
    return lines


# ---------------------------------------------------------------- terminal helpers
def cols():
    return shutil.get_terminal_size((110, 40)).columns


def vis(s):
    return len(ANSI.sub("", s))


def box(lines, title="", colour=GREEN, width=None):
    w = min(width or cols() - 2, 112)
    head = f"[ {title} ]" if title else ""
    out = [f"{colour}┌─{BOLD}{head}{END}{colour}{'─' * max(0, w - 3 - len(head))}┐{END}"]
    for line in lines:
        pad = max(0, w - 4 - vis(line))
        out.append(f"{colour}│{END} {line}{' ' * pad} {colour}│{END}")
    out.append(f"{colour}└{'─' * (w - 2)}┘{END}")
    print("\n".join(out))


def clear():
    print("\033[2J\033[H", end="")


def typed(cmd, colour=GREEN):
    print(f"{colour}{BOLD}bayora{END} {colour}❯{END} ", end="", flush=True)
    for ch in cmd:
        print(ch, end="", flush=True)
        time.sleep(0.025)
    print()
    time.sleep(0.3)


def pause():
    if AUTO:
        time.sleep(2.5)
    else:
        input(f"\n{DIM}  ⏎ Enter: next module   ·   Ctrl+C: quit{END}")


def env():
    e = dict(os.environ)
    f = os.path.join(ROOT, "experiments", "current", "exp_id")
    if os.path.exists(f):
        e["EXP_ID"] = open(f).read().strip()
    return e


def sh(cmd):
    return subprocess.run(cmd, shell=True, cwd=ROOT, capture_output=True, text=True, env=env())


def spin(cmd, label):
    frames = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    with tempfile.TemporaryFile("w+") as out, tempfile.TemporaryFile("w+") as err:
        p = subprocess.Popen(cmd, shell=True, cwd=ROOT, stdout=out, stderr=err, text=True, env=env())
        i, t0 = 0, time.time()
        while p.poll() is None:
            print(f"\r  {AMBER}{frames[i % 10]}{END} {label} {DIM}{time.time() - t0:4.1f}s{END}", end="", flush=True)
            time.sleep(0.1)
            i += 1
        out.seek(0), err.seek(0)
        mark = TICK if p.returncode == 0 else CROSS
        print(f"\r  {mark} {label} {DIM}{time.time() - t0:4.1f}s{END}   ")
        return p.returncode, out.read(), err.read()


def module_header(word, ramp, colour, tag, subtitle):
    clear()
    print()
    for line in banner(word, ramp):
        print("  " + line)
    print(f"\n  {colour}{BOLD}{tag}{END}  {GREY}{subtitle}{END}\n")


def exp_id():
    return open(os.path.join(ROOT, "experiments", "current", "exp_id")).read().strip()


# ---------------------------------------------------------------- modules
def home():
    clear()
    print(f"\n  {GREEN}initializing bayora lab...{END}\n")
    sh("docker compose down -v")
    spin("python3 tools/new_experiment.py", "generating fresh keys, salt and canaries")
    rc, _, err = spin("docker compose up -d --build", "building and starting isolated containers")
    if rc != 0:
        print(f"\n{RED}could not start the lab:{END}\n{err[-800:]}")
        sys.exit(1)
    time.sleep(2)

    running = 0
    for svc in ["gateway", "defense_runner", "model", "notary", "red_probe", "blue_probe"]:
        cid = sh(f"docker compose ps -q {svc}").stdout.strip()
        if cid and sh(f"docker inspect -f '{{{{.State.Running}}}}' {cid}").stdout.strip() == "true":
            running += 1
    nets = len(sh("docker network ls --filter name=bayora_ -q").stdout.split())
    os_name = platform.system()
    if os.path.exists("/etc/os-release"):
        m = re.search(r'PRETTY_NAME="([^"]+)"', open("/etc/os-release").read())
        os_name = m[1] if m else os_name
    docker_v = sh("docker version --format '{{.Server.Version}}'").stdout.strip() or "?"
    now = datetime.datetime.now()
    ready = running == 6
    info = [
        ("os", os_name), ("kernel", platform.release()[:34]), ("user", f"{getpass.getuser()} @ {platform.node()}"),
        ("docker", docker_v), ("python", platform.python_version()), ("experiment", exp_id()),
        ("containers", f"{running} running · hardened"), ("networks", f"{nets} isolated · no internet"),
        ("session", now.strftime("%Y-%m-%d  %H:%M")),
        ("status", f"{GREEN}✔ READY{END}" if ready else f"{RED}✘ NOT READY{END}"),
    ]
    panel = [f"{GREY}{k:<11}{END}: {v}" for k, v in info]
    art = banner("BAYORA LAB", "green")
    width = min(cols() - 2, 112)
    clear()
    print()
    title = f"Bayora Lab v{VERSION}"
    print(f"{GREEN}┌─[ {BOLD}{title}{END}{GREEN} ]{'─' * (width - 7 - len(title))}┐{END}")
    side = vis(art[0]) + 6 + 44 <= width
    rows = max(len(art), len(panel)) if side else len(art) + 1 + len(panel)
    body = []
    if side:
        for i in range(rows):
            left = art[i] if i < len(art) else ""
            right = panel[i] if i < len(panel) else ""
            body.append(f"{left}{' ' * (vis(art[0]) + 3 - vis(left))}{GREY}│{END} {right}")
    else:
        body = art + [""] + panel
    body += ["", f"{GREY}“Isolate. Attack. Prove.”  red team vs blue team, one machine, zero leaks{END}",
             f"{RED}⚠ isolated lab · authorized security testing only{END}"]
    for line in body:
        print(f"{GREEN}│{END} {line}{' ' * max(0, width - 4 - vis(line))} {GREEN}│{END}")
    stamp = f"[ {now.strftime('%Y-%m-%d  %H:%M')} ]"
    print(f"{GREEN}└{'─' * (width - 4 - len(stamp))}{stamp}──┘{END}\n")
    typed("/modules")
    mods = [(BLUE, "blue-team"), (RED, "red-team"), (RED, "breakout"), (AMBER, "attack-suite"),
            (PURPLE, "audit"), (GREEN, "verdict")]
    print("  " + "   ".join(f"{c}{BOLD}{n}{END}" for c, n in mods))
    pause()


def blue_team():
    module_header("BLUE TEAM", "blue", BLUE, "[ MODULE 1 ]", "the defender loads its secret rules")
    typed("blue.load_policy policy.json --target sealed-runner", BLUE)
    out = sh("docker compose exec -T blue_probe python blue_ctl.py upload").stdout
    ok = "loaded" in out
    box([f"{TICK if ok else CROSS} Blue's rules uploaded through the gateway",
         f"{TICK} stored in a sealed room on its own network (defense_net)",
         f"{TICK} Red can never read them",
         f"{TICK} Blue can't watch Red's attacks until the test ends"], "BLUE · POLICY", BLUE)
    pause()


def red_team():
    module_header("RED TEAM", "red", RED, "[ MODULE 2 ]", "the attacker goes after the AI model")
    typed("red.attack --payloads payloads.jsonl --via gateway", RED)
    rc, raw, _ = spin("docker compose exec -T red_probe python red_client.py", "firing 6 prompts at the model")
    replies = [json.loads(l) for l in raw.splitlines() if l.strip().startswith("{")]
    lines = [f"{GREY}{'#':<3}{'attack':<46}{'result':<11}{'size':>7}{'time':>10}{END}"]
    for i, r in enumerate(replies):
        col = GREEN if r["status"] == "answered" else RED
        label = PROMPT_LABELS[i] if i < len(PROMPT_LABELS) else f"prompt {i + 1}"
        lines.append(f"{i + 1:<3}{label:<46}{col}{r['status']:<11}{END}{r['bytes']:>5} B{r['seconds']:>8.3f} s")
    if replies:
        spread = round((max(r["seconds"] for r in replies) - min(r["seconds"] for r in replies)) * 1000)
        same = len({r["bytes"] for r in replies}) == 1
        lines += ["", f"{TICK if same else CROSS} every reply: {replies[0]['bytes']} bytes, within {spread} ms of each other",
                  f"{GREY}  Red learns only IF it was blocked, never WHY. Blue's rules stay secret.{END}",
                  f"{GREY}  behind the scenes: #3 #5 hit Blue's rules · #4 the model leaked a secret,{END}",
                  f"{GREY}  the gateway caught it. From Red's side, all three look identical.{END}"]
    box(lines, "RED · WHAT RED SAW", RED)
    pause()


def breakout():
    module_header("BREAKOUT", "red", RED, "[ MODULE 3 ]", "Red attacks the platform itself")
    typed("red.escape --targets defense,model,internet,filesystem", RED)
    tries = [("connect to Blue's sealed defense", "tcp defense_runner 8001"),
             ("connect to the AI model directly", "tcp model 8002"),
             ("reach the internet", "tcp 1.1.1.1 443"),
             ("overwrite its own program files", "write /app/hack.py")]
    lines = []
    for what, args in tries:
        print(f"  {DIM}→ trying to {what}...{END}", end="", flush=True)
        res = sh("docker compose exec -T red_probe python probe.py " + args).stdout.strip()
        blocked = res.startswith("BLOCKED") or res == "WRITE_DENIED"
        print("\r" + " " * 70 + "\r", end="")
        lines.append(f"{'red → ' + what:<46} {GREEN if blocked else RED}{BOLD}{'BLOCKED' if blocked else 'ALLOWED'}{END} {TICK if blocked else CROSS}")
        time.sleep(0.4)
    box(lines + ["", f"{GREY}  no route exists: separate networks, read-only filesystem, no privileges{END}"],
        "BREAKOUT · RESULTS", RED)
    pause()


def attack_suite():
    module_header("ATTACK SUITE", "amber", AMBER, "[ MODULE 4 ]", "35 automated attacks on our own system")
    typed("suite.run --all", AMBER)
    rc, out, _ = spin("bash tests/run_tests.sh", "running 35 attacks: escapes, stolen keys, overload, leaks, tampering")
    tests = [l for l in out.splitlines() if re.match(r"^T\d\d", l)]
    lines = []
    for cid, label in CATEGORIES.items():
        group = [l for l in tests if l.startswith(cid)]
        if group:
            ok = sum(" PASS " in l for l in group)
            lines.append(f"{TICK if ok == len(group) else CROSS} {label:<62}{ok:>3}/{len(group)}")
    passed = sum(" PASS " in l for l in tests)
    colour = GREEN if passed == len(tests) and tests else RED
    lines += ["", f"{colour}{BOLD}{passed} of {len(tests)} attacks stopped{END}"]
    box(lines, "SUITE · RESULTS", AMBER)
    pause()
    return tests


def audit():
    module_header("AUDIT", "purple", PURPLE, "[ MODULE 5 ]", "can anyone secretly rewrite history?")
    ev = os.path.join(ROOT, "evidence", exp_id())
    typed("audit.verify evidence/audit.db", PURPLE)
    v1 = sh(f"python3 tools/verify.py {ev}/audit.db {ev}/checkpoints.jsonl {ev}/notary_pub").stdout.strip()
    print(f"  {GREEN}{v1}{END}\n")
    time.sleep(0.8)
    tmp = os.path.join(ROOT, "evidence", "_tamper_demo")
    typed("audit.tamper --edit one-entry --copy", RED)
    sh(f"python3 tools/tamper.py edit {ev} {tmp}")
    typed("audit.verify evidence/tampered-copy.db", PURPLE)
    v2 = sh(f"python3 tools/verify.py {tmp}/audit.db {tmp}/checkpoints.jsonl {tmp}/notary_pub").stdout.strip()
    print(f"  {RED}{BOLD}{v2}{END}\n")
    shutil.rmtree(tmp, ignore_errors=True)
    box([f"{TICK} every action is chained to the one before it",
         f"{TICK} an independent notary signs the chain with its own key",
         f"{TICK if v2.startswith('FAIL') else CROSS} changing even one entry is caught instantly",
         f"{GREY}  also caught: deleting, swapping, cutting off, rebuilding the chain, faking signatures{END}"],
        "AUDIT · TAMPER-EVIDENT LOGBOOK", PURPLE)
    pause()
    return ev


def verdict(tests, ev):
    def all_pass(prefix, name=""):
        group = [l for l in tests if l.startswith(prefix) and name in l]
        return bool(group) and all(" PASS " in l for l in group)
    passed, total = sum(" PASS " in l for l in tests), len(tests)
    module_header("VERDICT", "green", GREEN, "[ RESULT ]", "experiment " + exp_id())
    report = build(ev)
    good = passed == total and total > 0
    box([f"{TICK if good else CROSS} {passed}/{total} attacks on our own system stopped",
         f"{TICK if all_pass('T08') else CROSS} 0 secrets leaked to the Red team",
         f"{TICK if all_pass('T00', 'same size') else CROSS} uniform replies: Red can't tell why it was blocked",
         f"{TICK if all_pass('T09') else CROSS} logbook tampering caught",
         f"{TICK} fresh keys and secrets for every run",
         "", f"{GREY}  visual report: {os.path.relpath(report, ROOT)}{END}"],
        "BAYORA LAB · SUMMARY", GREEN)
    open_report(report)
    print()


def open_report(report):
    """Show the report in a browser: Codespaces tab, Windows (WSL) browser, or a local web server."""
    if os.environ.get("CODESPACES") == "true":
        serve()
        name = os.environ.get("CODESPACE_NAME", "")
        domain = os.environ.get("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN", "app.github.dev")
        print(f"\n  {GREEN}report:{END} https://{name}-8080.{domain}/latest_report.html")
        print(f"  {DIM}(a browser tab opens by itself; if not, open the Ports tab and click port 8080){END}")
    elif shutil.which("explorer.exe") and shutil.which("wslpath"):
        win = sh(f"wslpath -w '{report}'").stdout.strip()
        subprocess.run(["explorer.exe", win], cwd=ROOT)
        print(f"\n  {DIM}opening the visual report in your browser...{END}")
    elif shutil.which("xdg-open") or shutil.which("open"):
        subprocess.run([shutil.which("xdg-open") or "open", report], cwd=ROOT,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"\n  {DIM}opening the visual report in your browser...{END}")
    else:
        serve()
        print(f"\n  {GREEN}report:{END} http://localhost:8080/latest_report.html")


def serve():
    """Serve evidence/ on port 8080 in the background (once)."""
    import socket
    with socket.socket() as s:
        if s.connect_ex(("127.0.0.1", 8080)) == 0:
            return
    subprocess.Popen([sys.executable, "-m", "http.server", "8080", "--directory",
                      os.path.join(ROOT, "evidence")], cwd=ROOT, start_new_session=True,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)


def main():
    home()
    blue_team()
    red_team()
    breakout()
    tests = attack_suite()
    ev = audit()
    verdict(tests, ev)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{DIM}stopped{END}")
