from _common import *
import tempfile, ast
src = open("todo/store.py").read()
tree = ast.parse(src)
opens = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "open"]
loads = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(getattr(n.func, "value", None), "id", "") == "json" and n.func.attr == "load"]
dumps = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(getattr(n.func, "value", None), "id", "") == "json" and n.func.attr == "dump"]
os.environ["TODO_STORE"] = os.path.join(tempfile.mkdtemp(), "t.json")
from todo import store
store.add_task("a"); store.add_task("b")
behaves = store.list_titles() == ["a", "b"] and len(store.load_tasks()) == 2
ok(len(loads) == 1 and len(dumps) == 1 and len(opens) <= 3 and behaves and suite_passes(), f"json.load={len(loads)} json.dump={len(dumps)} open={len(opens)}")
