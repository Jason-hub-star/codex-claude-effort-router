from _common import *
import tempfile
os.environ["TODO_STORE"] = os.path.join(tempfile.mkdtemp(), "t.json")
from todo import store
def raises(title):
    try: store.add_task(title); return False
    except ValueError: return True
ok(raises("") and raises("   ") and store.add_task("ok")["title"] == "ok" and suite_passes())
