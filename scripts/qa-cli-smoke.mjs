import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("..", import.meta.url));
const scratch = await mkdtemp(join(tmpdir(), "la-lanh-qa-cli-"));
const apiPort = 18_000 + Math.floor(Math.random() * 400);
const webPort = apiPort + 500;
const origin = `http://127.0.0.1:${webPort}`;
const databaseUrl = `sqlite+aiosqlite:///${join(scratch, "qa.db")}`;
const child = spawn(process.execPath, ["scripts/qa-server.mjs"], {
  cwd: root,
  env: {
    ...process.env,
    LA_LANH_DATABASE_URL: databaseUrl,
    LA_LANH_QA_API_PORT: String(apiPort),
    LA_LANH_QA_WEB_PORT: String(webPort),
  },
  stdio: ["ignore", "pipe", "pipe"],
});

let output = "";
child.stdout.on("data", (chunk) => { output += chunk; });
child.stderr.on("data", (chunk) => { output += chunk; });

try {
  const deadline = Date.now() + 40_000;
  let ready = false;
  while (Date.now() < deadline && child.exitCode === null) {
    try {
      const response = await fetch(`${origin}/__qa/ready`, {
        signal: AbortSignal.timeout(1_000),
      });
      ready = response.ok;
      if (ready) break;
    } catch {
      // Startup includes a fresh QA schema and the real API readiness check.
    }
    await new Promise((resolveDelay) => setTimeout(resolveDelay, 250));
  }

  assert.equal(ready, true, `QA launcher did not become ready:\n${output}`);
  const deepLink = await fetch(`${origin}/welcome`);
  assert.equal(deepLink.status, 200);
  assert.match(await deepLink.text(), /<div id="root"><\/div>/);
  const api = await fetch(`${origin}/v1/health`);
  assert.equal(api.status, 200);
  assert.equal((await api.json()).status, "ok");
} finally {
  if (child.exitCode === null) {
    child.kill("SIGTERM");
    await new Promise((resolveExit) => child.once("exit", resolveExit));
  }
  await rm(scratch, { recursive: true, force: true });
}

console.log("QA CLI smoke passed: fresh schema, API, proxy and SPA deep-link are ready.");
