import argparse
import json

from . import store


def main(argv=None):
    parser = argparse.ArgumentParser(prog="todo")
    sub = parser.add_subparsers(dest="cmd", required=True)
    add = sub.add_parser("add")
    add.add_argument("title")
    sub.add_parser("list")
    sub.add_parser("delete-all")
    args = parser.parse_args(argv)

    if args.cmd == "add":
        task = store.add_task(args.title)
        print(f"added #{task['id']}")
    elif args.cmd == "list":
        with open(store._path()) as f:
            for task in json.load(f):
                print(f"#{task['id']} {task['title']}")
    elif args.cmd == "delete-all":
        store.delete_all()
        print("deleted")


if __name__ == "__main__":
    main()
