from _common import *
from todo import db
conn = db.init()
inj = db.search(conn, "x' OR 1=1 --")
src = open("todo/db.py").read()
ok(len(inj) == 0 and len(db.search(conn, "milk")) == 1 and "+ term" not in src and suite_passes(), f"inj rows={len(inj)}")
