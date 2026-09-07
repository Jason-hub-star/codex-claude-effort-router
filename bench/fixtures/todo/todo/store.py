import json
import os
from datetime import date, timedelta

STORE = "tasks.json"


def _path():
    return os.environ.get("TODO_STORE", STORE)


def load_tasks():
    p = _path()
    if not os.path.exists(p):
        return []
    with open(p) as f:
        return json.load(f)


def save_tasks(tasks):
    with open(_path(), "w") as f:
        json.dump(tasks, f)


def list_titles():
    p = _path()
    if not os.path.exists(p):
        return []
    with open(p) as f:
        data = json.load(f)
    return [t["title"] for t in data]


def add_task(title, due=None):
    tasks = load_tasks()
    tasks.append({"id": len(tasks) + 1, "title": title, "due": due, "done": False})
    with open(_path(), "w") as f:
        json.dump(tasks, f)
    return tasks[-1]


def parse_due(text, today=None):
    today = today or date.today()
    if text == "today":
        return today
    if text == "tomorrow":
        return today
    return date.fromisoformat(text)


def export_task(task, name, export_dir="exports"):
    os.makedirs(export_dir, exist_ok=True)
    path = os.path.join(export_dir, name)
    with open(path, "w") as f:
        json.dump(task, f)
    return path


def delete_all():
    save_tasks([])
