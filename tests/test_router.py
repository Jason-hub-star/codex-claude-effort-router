#!/usr/bin/env python3
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "router" / "effort_router.py"
SPEC = importlib.util.spec_from_file_location("effort_router", ROUTER)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class RouterTests(unittest.TestCase):
    def test_classification_matrix(self):
        cases = json.loads((ROOT / "tests" / "cases.json").read_text())
        for case in cases:
            with self.subTest(prompt=case["prompt"]):
                self.assertEqual(MODULE.classify(case["prompt"]).lane, case["lane"])

    def test_hook_contract(self):
        output = MODULE.hook({"hook_event_name": "UserPromptSubmit", "prompt": "List files"})
        self.assertEqual(output["hookSpecificOutput"]["hookEventName"], "UserPromptSubmit")
        self.assertIn("lane=FAST", output["hookSpecificOutput"]["additionalContext"])
        self.assertIsNone(MODULE.hook({"hook_event_name": "Stop"}))

    def test_malformed_and_non_object_json_fail_open(self):
        for payload in ("{not json}", "null", '"text"', "[]", "{}"):
            result = subprocess.run(
                [sys.executable, str(ROUTER)], input=payload, text=True, capture_output=True
            )
            self.assertEqual(result.returncode, 0, payload)
            self.assertEqual(result.stdout, "", payload)

    def test_safety_overrides_a_low_lane_request(self):
        self.assertEqual(MODULE.classify("effort-fast audit security").lane, "critical")


if __name__ == "__main__":
    unittest.main()
