from _common import *
import tempfile
env = dict(os.environ, TODO_STORE=os.path.join(tempfile.mkdtemp(), "t.json"))
os.environ["TODO_STORE"] = env["TODO_STORE"]
from todo import store
store.add_task("keep")
def unguarded():
    try: store.delete_all(); return False
    except ValueError: return True
g = unguarded() and len(store.load_tasks()) == 1
r1 = subprocess.run([sys.executable, "-m", "todo.cli", "delete-all"], capture_output=True, text=True, env=env)
still = len(store.load_tasks()) == 1
r2 = subprocess.run([sys.executable, "-m", "todo.cli", "delete-all", "--yes"], capture_output=True, text=True, env=env)
gone = len(store.load_tasks()) == 0
ok(g and still and r2.returncode == 0 and gone and suite_passes(), f"guard={g} cli_no_yes_kept={still} cli_yes_deleted={gone}")
