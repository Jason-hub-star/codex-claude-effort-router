from _common import *
import re, glob
n = len([p for p in glob.glob("**/*.py", recursive=True) if "/.bench" not in p])
nums = re.findall(r"\d+", ANSWER)
ok(bool(nums) and int(nums[-1]) == n, f"expected {n}, answer={ANSWER.strip()[:40]!r}")
