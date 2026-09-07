#!/usr/bin/env python3
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "harness-audit" / "scripts" / "audit.py"
SPEC = importlib.util.spec_from_file_location("audit", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.project = root / "proj"
        for name in ("alive", "linked", "dead"):
            d = self.project / ".claude" / "skills" / name
            d.mkdir(parents=True)
            (d / "SKILL.md").write_text(f"---\nname: {name}\n---\nbody\n")
        (self.project / ".claude" / "skills" / "_archive" / "old").mkdir(parents=True)
        (self.project / ".claude" / "skills" / "_archive" / "old" / "SKILL.md").write_text("---\nname: old\n---\n")
        cmds = self.project / ".claude" / "commands"
        cmds.mkdir()
        (cmds / "go.md").write_text("Run the `linked` skill first.\n")
        # fake session logs: one in the project dir, one in a subdirectory session
        self._log_root = MODULE.LOG_ROOT
        MODULE.LOG_ROOT = root / "logs"
        enc = MODULE.encode(self.project)
        (MODULE.LOG_ROOT / enc).mkdir(parents=True)
        (MODULE.LOG_ROOT / enc / "a.jsonl").write_text('{"name":"Skill","input":{"skill":"alive"}}\n')
        (MODULE.LOG_ROOT / (enc + "-sub")).mkdir()
        (MODULE.LOG_ROOT / (enc + "-sub") / "b.jsonl").write_text("<command-name>/alive</command-name>\n")

    def tearDown(self):
        MODULE.LOG_ROOT = self._log_root
        self.tmp.cleanup()

    def test_verdicts_and_counts(self):
        report = MODULE.audit(self.project)
        by = {r["skill"]: r for r in report["skills"]}
        self.assertEqual(report["sessions"], 2)
        self.assertEqual(report["installed"], 3, "archived skills are not counted")
        self.assertEqual((by["alive"]["verdict"], by["alive"]["invocations"]), ("ALIVE", 2))
        self.assertEqual((by["linked"]["verdict"], by["linked"]["entry_points"]), ("LINKED", ["command:go"]))
        self.assertEqual(by["dead"]["verdict"], "DEAD")
        self.assertEqual(report["recovery_rate"], 0.33)
        self.assertFalse(report["over_cap"])
        self.assertIn("DEAD", MODULE.render(report))

    def test_idle_project_is_flagged_not_judged(self):
        MODULE.LOG_ROOT = Path(self.tmp.name) / "nowhere"
        report = MODULE.audit(self.project)
        self.assertEqual(report["sessions"], 0)
        self.assertIn("no sessions found", MODULE.render(report))


if __name__ == "__main__":
    unittest.main()
