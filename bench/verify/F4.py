from _common import *
names = ["_path", "load_tasks", "save_tasks", "list_titles", "add_task", "parse_due", "export_task", "delete_all"]
ok(all(n in ANSWER for n in names), ANSWER.strip()[:80])
