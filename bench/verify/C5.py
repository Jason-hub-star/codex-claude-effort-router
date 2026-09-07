from _common import *
import tempfile, stat
os.environ["TODO_STORE"] = os.path.join(tempfile.mkdtemp(), "t.json")
from todo import store
store.add_task("a")
mode = stat.S_IMODE(os.stat(os.environ["TODO_STORE"]).st_mode)
ok(mode == 0o600 and suite_passes(), f"mode={oct(mode)}")
