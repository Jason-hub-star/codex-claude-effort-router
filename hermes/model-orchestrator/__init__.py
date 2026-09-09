"""model-orchestrator plugin for Hermes Agent.

``pre_llm_call`` returns a routing-context string that Hermes injects into the user turn.
The lane decision is made by the shared Python router (one source of truth); this module
only locates it and calls ``classify``. Every failure path returns ``None`` so a broken or
missing router never blocks a turn.

Hermes hooks cannot change the model or reasoning effort per turn (see
NousResearch/hermes-agent issues #23739 and #7273), so this plugin is advisory only.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType

ROUTER_CANDIDATES = (
    os.environ.get("MODEL_ORCHESTRATOR_ROUTER", ""),
    str(Path.home() / ".config" / "model-orchestrator" / "model_orchestrator.py"),
    str(Path.home() / ".claude" / "hooks" / "model-orchestrator.py"),
)

_router: ModuleType | None = None


def _load_router() -> ModuleType | None:
    global _router
    if _router is not None:
        return _router
    for candidate in ROUTER_CANDIDATES:
        if not candidate or not Path(candidate).is_file():
            continue
        spec = importlib.util.spec_from_file_location("model_orchestrator_router", candidate)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module  # dataclasses on Python 3.14 resolve the module via sys.modules
        try:
            spec.loader.exec_module(module)
        except Exception:  # noqa: BLE001 - fail open
            sys.modules.pop(spec.name, None)
            continue
        _router = module
        return module
    return None


def route_context(user_message: object) -> str | None:
    router = _load_router()
    text = user_message if isinstance(user_message, str) else str(user_message or "")
    if router is None or not text.strip():
        return None
    try:
        route = router.classify(text, cwd=os.getcwd())
        return router.render_context(route.lane, route.reason, route.effort, route.targets, "hermes")
    except Exception:  # noqa: BLE001 - fail open
        return None


def _on_pre_llm_call(**kwargs: object) -> dict[str, str] | None:
    context = route_context(kwargs.get("user_message"))
    return {"context": context} if context else None


def register(ctx: object) -> None:
    ctx.register_hook("pre_llm_call", _on_pre_llm_call)  # type: ignore[attr-defined]
