from _common import *
leak = subprocess.run(["grep", "-rn", "sk-live-9f8e7d6c5b4a3210", "--include=*.py", "--include=*.md", "--include=*.toml", "."], capture_output=True, text=True).stdout
os.environ.pop("TODO_API_KEY", None)
import importlib, todo.sync as sync
def missing_raises():
    try:
        importlib.reload(sync); sync.headers(); return False
    except Exception: return True
m = missing_raises()
os.environ["TODO_API_KEY"] = "k123"
importlib.reload(sync)
ok(not leak and m and sync.headers()["Authorization"] == "Bearer k123" and suite_passes(), f"leak={bool(leak)}")
