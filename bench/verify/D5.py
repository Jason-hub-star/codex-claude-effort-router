from _common import *
import tempfile
env = dict(os.environ, TODO_STORE=os.path.join(tempfile.mkdtemp(), "missing.json"))
r = subprocess.run([sys.executable, "-m", "todo.cli", "list"], capture_output=True, text=True, env=env)
ok(r.returncode == 0 and "no tasks" in r.stdout.lower() and suite_passes(), r.stdout[:40] + r.stderr[-80:])
