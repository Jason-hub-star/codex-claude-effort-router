// Offline contract test for the OpenClaw plugin: plain Node, no gateway needed.
import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";

const here = dirname(fileURLToPath(import.meta.url));
const router = join(here, "..", "router", "effort_router.py");
const { default: plugin, splitTarget } = await import("../openclaw/index.js");

function fakeApi(pluginConfig) {
  const handlers = {};
  return { api: { pluginConfig, logger: console, on: (name, fn) => { handlers[name] = fn; } }, handlers };
}

// manifest shape
assert.equal(plugin.id, "effort-lanes");
assert.equal(typeof plugin.register, "function");
assert.equal(plugin.configSchema.type, "object");

// advisory by default: context prepended, no model override
{
  const { api, handlers } = fakeApi({ router });
  plugin.register(api);
  const ctx = { sessionKey: "agent:main:main", workspaceDir: join(here, "..") };
  const resolve = await handlers.before_model_resolve({ prompt: "audit security of the login flow" }, ctx);
  assert.equal(resolve, undefined);
  const build = await handlers.before_prompt_build({ prompt: "audit security of the login flow", messages: [] }, ctx);
  assert.match(build.prependContext, /\[EFFORT LANES\] lane=CRITICAL/);
  assert.doesNotMatch(build.prependContext, /Codex target/);
}

// enforce with a lane model map: provider/model is split for the override
{
  const { api, handlers } = fakeApi({ router, enforce: true, models: { critical: "anthropic/claude-opus-5" } });
  plugin.register(api);
  const ctx = { sessionKey: "s", workspaceDir: join(here, "..") };
  const resolve = await handlers.before_model_resolve({ prompt: "audit security" }, ctx);
  assert.deepEqual(resolve, { providerOverride: "anthropic", modelOverride: "claude-opus-5" });
  const none = await handlers.before_model_resolve({ prompt: "count files" }, ctx);
  assert.equal(none, undefined, "no model configured for the fast lane → no override");
}

// enforce with a bare model id
assert.deepEqual(splitTarget("llama3.3:8b"), { modelOverride: "llama3.3:8b" });
assert.equal(splitTarget(""), null);

// missing router: fail open on both hooks
{
  const { api, handlers } = fakeApi({ router: "/nonexistent/router.py", enforce: true, models: { deep: "x/y" } });
  const saved = { router: process.env.EFFORT_LANES_ROUTER, home: process.env.HOME };
  process.env.EFFORT_LANES_ROUTER = "/nonexistent/too.py";
  process.env.HOME = mkdtempSync(join(tmpdir(), "effort-lanes-"));  // no installed fallback either
  plugin.register(api);
  process.env.EFFORT_LANES_ROUTER = saved.router;
  process.env.HOME = saved.home;
  const ctx = { sessionKey: "s" };
  assert.equal(await handlers.before_model_resolve({ prompt: "implement it" }, ctx), undefined);
  assert.equal(await handlers.before_prompt_build({ prompt: "implement it", messages: [] }, ctx), undefined);
}

console.log("OpenClaw plugin contract OK");
