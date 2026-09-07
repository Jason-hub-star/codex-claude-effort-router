import os
import tempfile
import unittest

from todo import store


class SmokeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.environ["TODO_STORE"] = os.path.join(self.tmp, "tasks.json")

    def test_add_and_load(self):
        store.add_task("a")
        self.assertEqual([t["title"] for t in store.load_tasks()], ["a"])


if __name__ == "__main__":
    unittest.main()
