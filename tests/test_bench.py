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

    def test_conditions_change_exactly_one_axis_each(self):
        c = RUN.CONDITIONS
        # plugin off vs on
        self.assertTrue(c["none"]["pure"] and c["always-low"]["pure"] and c["always-high"]["pure"])
        self.assertFalse(c["advisory"]["pure"] or c["enforce"]["pure"] or c["enforce-low"]["pure"])
        # forced effort only where intended
        self.assertEqual(c["always-low"]["effort"], "low")
        self.assertEqual(c["always-high"]["effort"], "high")
        self.assertNotIn("effort", c["none"])
        self.assertNotIn("effort", c["advisory"])
        # enforce-low differs from enforce by the fast lane's effort and nothing else
        self.assertEqual(c["enforce"]["env"], c["enforce-low"]["env"])
        self.assertNotIn("lane_config", c["enforce"])
        self.assertEqual(c["enforce-low"]["lane_config"], {"lanes": {"fast": {"effort": "low"}}})

    def test_lane_config_reaches_the_router(self):
        """The experiment's axis: a config file must be able to change one lane's effort."""
        spec = importlib.util.spec_from_file_location("router_for_bench", ROOT / "router" / "effort_router.py")
        router = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = router
        spec.loader.exec_module(router)
        work = Path(tempfile.mkdtemp())
        config = work / "cfg.json"
        config.write_text(json.dumps(RUN.CONDITIONS["enforce-low"]["lane_config"]))
        router.GLOBAL_CONFIG = config
        self.assertEqual(router.classify("count the files", cwd=str(work)).effort, "low")
        self.assertEqual(router.classify("implement and test it", cwd=str(work)).effort, "high", "other lanes untouched")

    def test_routed_effort_reads_back_what_the_plugin_set(self):
        work = Path(tempfile.mkdtemp())
        debug = work / "d.jsonl"
        debug.write_text("\n".join([
            json.dumps({"hook": "chat.message", "lane": "fast"}),
            json.dumps({"hook": "chat.params", "lane": "fast", "effort": "low", "enforce": True}),
        ]))
        self.assertEqual(RUN.routed_effort(debug), "low")
        self.assertIsNone(RUN.routed_effort(work / "missing.jsonl"))
        advisory = work / "advisory.jsonl"
        advisory.write_text(json.dumps({"hook": "chat.params", "lane": "fast", "effort": "medium", "enforce": False}))
        self.assertIsNone(RUN.routed_effort(advisory), "an advisory turn applies no effort")

    def test_decision_rule_order_is_deterministic(self):
        """C (pass-rate loss) beats B (noise band) beats A (clear reduction)."""
        work = Path(tempfile.mkdtemp())

        def rows(enforce_reason, low_reason, enforce_pass=5, low_pass=5):
            out = []
            for cond, reason, passes in (("enforce", enforce_reason, enforce_pass), ("enforce-low", low_reason, low_pass)):
                for i in range(5):
                    out.append({"lane_expected": "fast", "condition": cond, "pass": i < passes,
                                "tokens": {"reasoning": reason}})
            return "\n".join(json.dumps(r) for r in out)

        def decide(text):
            path = work / "r.jsonl"
            path.write_text(text)
            proc = subprocess.run([sys.executable, str(ROOT / "bench" / "run.py"), "decide", str(path)],
                                  capture_output=True, text=True, check=True)
            return proc.stdout

        self.assertIn("case A", decide(rows(100, 50)))            # clear reduction
        self.assertIn("case B", decide(rows(100, 90)))            # inside the 15% band
        self.assertIn("case C", decide(rows(100, 50, low_pass=3)))  # cheaper but loses passes
        self.assertIn("case C*", decide(rows(100, 200)))          # worse, outside the sealed table

    def test_config_content_targets_the_model(self):
        data = json.loads(RUN.config_content("opencode-go/gpt-5.6-luna", "high"))
        self.assertEqual(data["provider"]["opencode-go"]["models"]["gpt-5.6-luna"]["options"]["reasoningEffort"], "high")


if __name__ == "__main__":
    unittest.main()
