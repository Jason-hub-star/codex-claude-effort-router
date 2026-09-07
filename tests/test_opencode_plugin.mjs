// Offline contract test for the OpenCode plugin: runs under plain Node, no OpenCode needed.
import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";

const here = dirname(fileURLToPath(import.meta.url));
process.env.EFFORT_LANES_ROUTER = join(here, "..", "router", "effort_router.py");
delete process.env.EFFORT_LANES_ENFORCE;

const { EffortLanesPlugin } = await import("../opencode/effort-lanes.js");
const hooks = await EffortLanesPlugin({ directory: join(here, "..") });

async function turn(text, sessionID = "ses_test") {
  const message = { id: "msg_1", sessionID, role: "user" };
  const output = { message, parts: [{ id: "prt_0", sessionID, messageID: "msg_1", type: "text", text }] };
  await hooks["chat.message"]({ sessionID }, output);
  return output;
}

// advisory context is appended as one synthetic text part
let out = await turn("fix the bug and test it");
assert.equal(out.parts.length, 2);
assert.equal(out.parts[1].synthetic, true);
assert.match(out.parts[1].text, /\[EFFORT LANES\] lane=DEEP/);
assert.doesNotMatch(out.parts[1].text, /Codex target/);

// synthetic parts are not re-classified (no runaway growth)
const again = { message: out.message, parts: out.parts.filter((p) => p.synthetic) };
await hooks["chat.message"]({ sessionID: "ses_test" }, again);
assert.equal(again.parts.length, 1);

// enforcement is off by default
let params = { options: { existing: 1 } };
await hooks["chat.params"]({ sessionID: "ses_test" }, params);
assert.deepEqual(params.options, { existing: 1 });

// enforcement sets reasoningEffort for the lane and keeps other options
process.env.EFFORT_LANES_ENFORCE = "1";
params = { options: { existing: 1 } };
await hooks["chat.params"]({ sessionID: "ses_test" }, params);
assert.deepEqual(params.options, { existing: 1, reasoningEffort: "high" });

// unknown session: never throws, never sets options
params = { options: {} };
await hooks["chat.params"]({ sessionID: "ses_other" }, params);
assert.deepEqual(params.options, {});

// missing router: fail open, prompt untouched (HOME is moved so no installed fallback is found)
process.env.EFFORT_LANES_ROUTER = "/nonexistent/router.py";
process.env.HOME = mkdtempSync(join(tmpdir(), "effort-lanes-"));
const { EffortLanesPlugin: Broken } = await import("../opencode/effort-lanes.js?broken");
const broken = await Broken({ directory: join(here, "..") });
const untouched = { message: { id: "m" }, parts: [{ type: "text", text: "hello" }] };
await broken["chat.message"]({ sessionID: "s" }, untouched);
assert.equal(untouched.parts.length, 1);

console.log("OpenCode plugin contract OK");
