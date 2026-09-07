from _common import *
from datetime import date
from todo import store
ok(store.parse_due("tomorrow", today=date(2026, 1, 31)) == date(2026, 2, 1) and store.parse_due("today", today=date(2026,1,31)) == date(2026,1,31) and suite_passes())
