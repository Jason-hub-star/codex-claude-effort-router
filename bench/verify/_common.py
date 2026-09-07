import os, subprocess, sys
WORKDIR = os.environ["WORKDIR"]
ANSWER = open(os.environ["ANSWER_FILE"], encoding="utf-8", errors="ignore").read() if os.path.exists(os.environ["ANSWER_FILE"]) else ""
os.chdir(WORKDIR)
sys.path.insert(0, WORKDIR)
def suite_passes():
    r = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."], capture_output=True, text=True)
    return r.returncode == 0 and "NO TESTS RAN" not in r.stderr
def ok(cond, msg=""):
    print(("PASS " if cond else "FAIL ") + msg); sys.exit(0 if cond else 1)
