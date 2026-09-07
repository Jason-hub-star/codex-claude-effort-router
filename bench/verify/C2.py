from _common import *
import tempfile
from todo import store
d = tempfile.mkdtemp()
def escapes(name):
    try: store.export_task({"id": 1}, name, export_dir=os.path.join(d, "exports")); return False
    except ValueError: return True
p = store.export_task({"id": 1}, "one.json", export_dir=os.path.join(d, "exports"))
ok(escapes("../evil.json") and escapes("/tmp/evil.json") and os.path.exists(p) and not os.path.exists(os.path.join(d, "evil.json")) and suite_passes())
