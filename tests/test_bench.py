#!/usr/bin/env python3
"""Offline checks for the benchmark runner: event parsing and verify scripts fail on the untouched fixture."""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("bench_run", ROOT / "bench" / "run.py")
RUN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUN)


class BenchTests(unittest.TestCase):
    def test_parse_events_sums_tokens_and_keeps_last_text_per_part(self):
        lines = [
            "timestamp=... level=INFO noise",
            json.dumps({"type": "text", "part": {"id": "p1", "type": "text", "text": "OK"}}),
            json.dumps({"type": "text", "part": {"id": "p1", "type": "text", "text": "OKAY"}}),
            json.dumps({"type": "text", "part": {"id": "p2", "type": "text", "text": "ctx", "synthetic": True}}),
            json.dumps({"type": "step_finish", "part": {"tokens": {"input": 10, "output": 5, "reasoning": 7, "cache": {"read": 100, "write": 0}}, "cost": 0.01}}),
            json.dumps({"type": "step_finish", "part": {"tokens": {"input": 1, "output": 1, "reasoning": 0, "cache": {"read": 50}}, "cost": 0.005}}),
            json.dumps({"type": "error", "error": {"message": "boom"}}),
        ]
        tokens, cost, steps, answer, errors = RUN.parse_events("\n".join(lines))
        self.assertEqual(tokens, {"input": 11, "output": 6, "reasoning": 7, "cache_read": 150, "cache_write": 0})
        self.assertAlmostEqual(cost, 0.015)
        self.assertEqual((steps, answer, errors), (2, "OKAY", 1))

    def test_tasks_have_verify_scripts_that_fail_on_the_untouched_fixture(self):
        tasks = json.loads((ROOT / "bench" / "tasks.json").read_text())
        self.assertEqual(len(tasks), 15)
        work = Path(tempfile.mkdtemp())
        shutil.copytree(ROOT / "bench" / "fixtures" / "todo", work, dirs_exist_ok=True)
        answer = work / ".bench_answer.txt"
        answer.write_text("")
        for task in tasks:
            script = ROOT / "bench" / "verify" / f"{task['id']}.py"
            self.assertTrue(script.exists(), task["id"])
            result = subprocess.run([sys.executable, str(script)], cwd=ROOT / "bench" / "verify",
                                    env={**os.environ, "WORKDIR": str(work), "ANSWER_FILE": str(answer)},
                                    capture_output=True, text=True, timeout=120)
            self.assertNotEqual(result.returncode, 0, f"{task['id']} must fail before the agent works")

    def test_config_content_targets_the_model(self):
        data = json.loads(RUN.config_content("opencode-go/gpt-5.6-luna", "high"))
        self.assertEqual(data["provider"]["opencode-go"]["models"]["gpt-5.6-luna"]["options"]["reasoningEffort"], "high")


if __name__ == "__main__":
    unittest.main()
