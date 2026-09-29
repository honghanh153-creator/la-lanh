import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { randomUUID } from "node:crypto";
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

  const guestResponse = await fetch(`${origin}/v1/guest-sessions`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      origin,
    },
    body: JSON.stringify({
      consent_version: "birth-profile-v1",
      purpose: "birth_profile_basic",
      idempotency_key: `qa-smoke-${randomUUID()}`,
    }),
  });
  assert.equal(guestResponse.status, 200);
  const guest = await guestResponse.json();
  assert.equal(typeof guest.csrf_token, "string");
  const cookies = guestResponse.headers.getSetCookie()
    .map((header) => header.split(";", 1)[0])
    .join("; ");
  assert.match(cookies, /la_lanh_guest=/);

  const birthResponse = await fetch(`${origin}/v1/birth-profile`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      cookie: cookies,
      origin,
      "x-csrf-token": guest.csrf_token,
    },
    body: JSON.stringify({ birth_date: "1990-03-15" }),
  });
  assert.equal(birthResponse.status, 200);
  assert.equal((await birthResponse.json()).calculation_kind, "date_only_sun");

  const noteResponse = await fetch(`${origin}/v1/daily-note`, {
    headers: { cookie: cookies, origin },
  });
  assert.equal(noteResponse.status, 200);
  const note = await noteResponse.json();
  assert.equal(typeof note.title, "string");
  assert.ok(note.title.length > 0);
  assert.equal(typeof note.reading_projection?.active?.sections?.hook, "string");
} finally {
  if (child.exitCode === null) {
    child.kill("SIGTERM");
    await new Promise((resolveExit) => child.once("exit", resolveExit));
  }
  await rm(scratch, { recursive: true, force: true });
}

console.log("QA CLI smoke passed: schema, proxy, SPA deep-link and real guest → birth → daily-note flow are ready.");
