#!/usr/bin/env python3
"""Offline contract test for the Hermes plugin: no Hermes install needed."""
import importlib.util
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "hermes" / "effort-lanes" / "__init__.py"


def load_plugin():
    spec = importlib.util.spec_from_file_location("effort_lanes_hermes", PLUGIN)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeCtx:
    def __init__(self):
        self.hooks = {}

    def register_hook(self, name, callback):
        self.hooks[name] = callback


class HermesPluginTests(unittest.TestCase):
    def setUp(self):
        self._env = os.environ.get("EFFORT_LANES_ROUTER")
        os.environ["EFFORT_LANES_ROUTER"] = str(ROOT / "router" / "effort_router.py")

    def tearDown(self):
        if self._env is None:
            os.environ.pop("EFFORT_LANES_ROUTER", None)
        else:
            os.environ["EFFORT_LANES_ROUTER"] = self._env

    def test_registers_pre_llm_call_and_injects_context(self):
        plugin = load_plugin()
        ctx = FakeCtx()
        plugin.register(ctx)
        self.assertEqual(list(ctx.hooks), ["pre_llm_call"])
        result = ctx.hooks["pre_llm_call"](
            session_id="s", user_message="implement the parser and test it",
            conversation_history=[], is_first_turn=True, model="gpt-4", platform="cli",
        )
        self.assertIn("[EFFORT LANES] lane=DEEP", result["context"])
        self.assertNotIn("Codex target", result["context"])

    def test_manifest_declares_the_hook(self):
        manifest = (ROOT / "hermes" / "effort-lanes" / "plugin.yaml").read_text(encoding="utf-8")
        self.assertIn("name: effort-lanes", manifest)
        self.assertIn("- pre_llm_call", manifest)

    def test_fails_open(self):
        plugin = load_plugin()
        ctx = FakeCtx()
        plugin.register(ctx)
        self.assertIsNone(ctx.hooks["pre_llm_call"](user_message=""))
        os.environ["EFFORT_LANES_ROUTER"] = "/nonexistent/router.py"
        broken = load_plugin()
        broken.ROUTER_CANDIDATES = ("/nonexistent/router.py",)
        ctx2 = FakeCtx()
        broken.register(ctx2)
        self.assertIsNone(ctx2.hooks["pre_llm_call"](user_message="implement it"))


if __name__ == "__main__":
    unittest.main()
