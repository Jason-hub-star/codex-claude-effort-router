#!/usr/bin/env python3
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "router" / "model_orchestrator.py"
SPEC = importlib.util.spec_from_file_location("model_orchestrator", ROUTER)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class RouterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name) / "project"
        self.project.mkdir()
        self._global = MODULE.GLOBAL_CONFIG
        MODULE.GLOBAL_CONFIG = Path(self.tmp.name) / "missing-global.json"

    def tearDown(self):
        MODULE.GLOBAL_CONFIG = self._global
        self.tmp.cleanup()

    def write_config(self, data, where=None):
        (where or self.project).joinpath(MODULE.CONFIG_NAME).write_text(json.dumps(data), encoding="utf-8")

    def classify(self, prompt):
        return MODULE.classify(prompt, cwd=str(self.project))

    def test_classification_matrix(self):
        cases = json.loads((ROOT / "tests" / "cases.json").read_text())
        for case in cases:
            with self.subTest(prompt=case["prompt"]):
                self.assertEqual(self.classify(case["prompt"]).lane, case["lane"])

    def test_hook_contract(self):
        payload = {"hook_event_name": "UserPromptSubmit", "prompt": "List files", "cwd": str(self.project)}
        output = MODULE.hook(payload)
        self.assertEqual(output["hookSpecificOutput"]["hookEventName"], "UserPromptSubmit")
        self.assertIn("lane=FAST", output["hookSpecificOutput"]["additionalContext"])
        self.assertIn("effort=low", output["hookSpecificOutput"]["additionalContext"])
        self.assertIsNone(MODULE.hook({"hook_event_name": "Stop"}))

    def test_hermes_shell_hook_contract(self):
        payload = {
            "hook_event_name": "pre_llm_call", "tool_name": None, "tool_input": None,
            "session_id": "s", "cwd": str(self.project),
            "extra": {"user_message": "audit security of the login flow", "is_first_turn": True},
        }
        output = MODULE.hook(payload)
        self.assertEqual(set(output), {"context"})
        self.assertIn("[MODEL ORCHESTRATOR] lane=CRITICAL", output["context"])
        self.assertNotIn("Codex target", output["context"])
        self.assertIsNone(MODULE.hook({"hook_event_name": "pre_llm_call", "extra": {"user_message": ""}}))
        self.assertIsNone(MODULE.hook({"hook_event_name": "pre_llm_call", "extra": "garbage"}))

    def test_malformed_and_non_object_json_fail_open(self):
        for payload in ("{not json}", "null", '"text"', "[]", "{}"):
            result = subprocess.run(
                [sys.executable, str(ROUTER)], input=payload, text=True, capture_output=True
            )
            self.assertEqual(result.returncode, 0, payload)
            self.assertEqual(result.stdout, "", payload)

    def test_safety_overrides_a_low_lane_request(self):
        self.assertEqual(self.classify("effort-fast audit security").lane, "critical")

    def test_project_floor_raises_but_never_lowers(self):
        self.write_config({"floor": "deep"})
        route = self.classify("explain this function")
        self.assertEqual((route.lane, route.reason), ("deep", "project floor"))
        self.assertEqual(self.classify("audit security").lane, "critical")
        self.assertEqual(self.classify("lane=fast list files").lane, "fast", "explicit request beats the floor")

    def test_project_config_is_found_from_a_subdirectory(self):
        self.write_config({"default_lane": "deep"})
        nested = self.project / "src" / "deep" / "inside"
        nested.mkdir(parents=True)
        self.assertEqual(MODULE.classify("ㄱ", cwd=str(nested)).lane, "deep")
        self.assertEqual(self.classify("ㄱ").lane, "deep")

    def test_config_keywords_extend_and_lanes_override_targets(self):
        self.write_config({
            "keywords": {"critical": ["movej"]},
            "lanes": {"critical": {"opencode": "anthropic/claude-opus-5", "codex": "Astra/xhigh"}},
        })
        route = self.classify("run movej on the arm")
        self.assertEqual(route.lane, "critical")
        self.assertEqual(route.targets["codex"], "Astra/xhigh")
        self.assertEqual(route.targets["opencode"], "anthropic/claude-opus-5")
        context = MODULE.render_context(route.lane, route.reason, route.effort, route.targets, "opencode")
        self.assertIn("Suggested opencode model=anthropic/claude-opus-5", context)

    def test_malformed_or_hostile_config_fails_open(self):
        self.project.joinpath(MODULE.CONFIG_NAME).write_text("{oops", encoding="utf-8")
        self.assertEqual(self.classify("explain this").lane, "daily")
        self.write_config({"floor": "godmode", "default_lane": 7, "keywords": "no", "fast_max_chars": -1})
        self.assertEqual(self.classify("explain this").lane, "daily")
        self.assertEqual(self.classify("count files").lane, "fast")

    def test_global_config_is_overridden_by_project_config(self):
        MODULE.GLOBAL_CONFIG = Path(self.tmp.name) / "global.json"
        MODULE.GLOBAL_CONFIG.write_text(json.dumps({"default_lane": "fast", "keywords": {"deep": ["zzimplement"]}}))
        self.assertEqual(self.classify("ㄱ").lane, "fast")
        self.assertEqual(self.classify("zzimplement it").lane, "deep")
        self.write_config({"default_lane": "deep"})
        self.assertEqual(self.classify("ㄱ").lane, "deep")
        self.assertEqual(self.classify("zzimplement it").lane, "deep", "global keywords survive the merge")

    def test_env_can_relocate_the_global_config(self):
        alt = Path(self.tmp.name) / "alt.json"
        alt.write_text(json.dumps({"default_lane": "critical"}))
        env = {**os.environ, "MODEL_ORCHESTRATOR_CONFIG": str(alt)}
        result = subprocess.run([sys.executable, str(ROUTER), "--classify", "--prompt", "ㄱ", "--cwd", str(self.project)],
                                text=True, capture_output=True, check=True, env=env)
        self.assertEqual(json.loads(result.stdout)["lane"], "critical")

    def test_cli_json_for_plugins(self):
        result = subprocess.run(
            [sys.executable, str(ROUTER), "--classify", "--json", "--runtime", "openclaw",
             "--prompt", "fix the bug and test it", "--cwd", str(self.project)],
            text=True, capture_output=True, check=True,
        )
        data = json.loads(result.stdout)
        self.assertEqual(data["lane"], "deep")
        self.assertEqual(data["effort"], "high")
        self.assertIn("[MODEL ORCHESTRATOR] lane=DEEP", data["context"])
        self.assertNotIn("Codex target", data["context"])
        legacy = subprocess.run(
            [sys.executable, str(ROUTER), "--classify", "--prompt", "count files"],
            text=True, capture_output=True, check=True,
        )
        self.assertEqual(set(json.loads(legacy.stdout)), {"lane", "reason"})


if __name__ == "__main__":
    unittest.main()
