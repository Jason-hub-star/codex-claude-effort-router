// model-orchestrator plugin for OpenCode (https://opencode.ai/docs/plugins/)
//
// Thin adapter: the lane decision stays in the Python router (one source of truth).
// - chat.message  → appends one synthetic text part with the routing context (advisory).
// - chat.params   → when enforcement is enabled, sets `reasoningEffort` for the lane.
//
// Enforcement is opt-in. Enable it with `"enforce": {"opencode": true}` in
// ~/.config/model-orchestrator/config.json or `MODEL_ORCHESTRATOR_ENFORCE=1`.
// Set MODEL_ORCHESTRATOR_DEBUG=/path/to/file to append one JSON line per hook call.

import { execFile } from "node:child_process";
import { appendFileSync, existsSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

const CONFIG_DIR = join(homedir(), ".config", "model-orchestrator");
const ROUTER_CANDIDATES = [
  process.env.MODEL_ORCHESTRATOR_ROUTER,
  join(CONFIG_DIR, "model_orchestrator.py"),
  join(homedir(), ".claude", "hooks", "model-orchestrator.py"),
].filter(Boolean);
const TIMEOUT_MS = 2000;

function readConfig() {
  try {
    return JSON.parse(readFileSync(join(CONFIG_DIR, "config.json"), "utf8")) ?? {};
  } catch {
    return {};
  }
}

function enforceEnabled() {
  if (process.env.MODEL_ORCHESTRATOR_ENFORCE === "1") return true;
  const enforce = readConfig().enforce;
  return enforce === true || Boolean(enforce && enforce.opencode === true);
}

function debug(record) {
  const target = process.env.MODEL_ORCHESTRATOR_DEBUG;
  if (!target) return;
  try {
    appendFileSync(target, JSON.stringify({ time: Date.now(), ...record }) + "\n");
  } catch {
    /* debugging must never break the chat */
  }
}

function routerPath() {
  return ROUTER_CANDIDATES.find((p) => existsSync(p));
}

function classify(prompt, cwd) {
  const router = routerPath();
  if (!router) return Promise.resolve(null);
  return new Promise((resolve) => {
    execFile(
      "python3",
      [router, "--classify", "--json", "--runtime", "opencode", "--prompt", prompt, "--cwd", cwd],
      { timeout: TIMEOUT_MS, maxBuffer: 64 * 1024 },
      (error, stdout) => {
        if (error) return resolve(null);
        try {
          resolve(JSON.parse(stdout));
        } catch {
          resolve(null);
        }
      },
    );
  });
}

function partId() {
  return "prt_" + Date.now().toString(36).padStart(9, "0") + Math.random().toString(36).slice(2, 12);
}

export const ModelOrchestratorPlugin = async ({ directory }) => {
  const lanes = new Map(); // sessionID -> route

  return {
    "chat.message": async (input, output) => {
      const texts = (output.parts ?? []).filter((p) => p.type === "text" && !p.synthetic);
      const prompt = texts.map((p) => p.text).join("\n").trim();
      if (!prompt) return;
      const route = await classify(prompt, directory);
      debug({ hook: "chat.message", sessionID: input.sessionID, lane: route?.lane ?? null, reason: route?.reason ?? null });
      if (!route) return;
      lanes.set(input.sessionID, route);
      output.parts.push({
        id: partId(),
        sessionID: input.sessionID,
        messageID: output.message.id,
        type: "text",
        text: route.context,
        synthetic: true,
      });
    },

    "chat.params": async (input, output) => {
      const route = lanes.get(input.sessionID);
      const enforce = enforceEnabled();
      debug({ hook: "chat.params", sessionID: input.sessionID, lane: route?.lane ?? null, effort: route?.effort ?? null, enforce });
      if (!route || !enforce) return;
      output.options = { ...(output.options ?? {}), reasoningEffort: route.effort };
    },
  };
};

export default ModelOrchestratorPlugin;
