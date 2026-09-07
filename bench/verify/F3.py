from _common import *
t = open("README.md").read()
ok("recieve" not in t and "receive" in t and "tasks.json" in t)
