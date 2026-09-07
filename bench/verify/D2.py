from _common import *
import tempfile
os.environ["TODO_STORE"] = os.path.join(tempfile.mkdtemp(), "t.json")
from todo import store
t = store.add_task("x")
store.complete(t["id"])
done = [x for x in store.load_tasks() if x["id"] == t["id"]][0]["done"]
try:
    store.complete(999); missing_raises = False
except KeyError:
    missing_raises = True
ok(done is True and missing_raises and suite_passes())
