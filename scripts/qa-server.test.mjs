import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { access, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { createServer } from "node:http";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import {
  createQaServer,
  DEFAULT_QA_API_PORT,
  DEFAULT_QA_WEB_PORT,
  drainOnStop,
  loopbackApiTarget,
  prepareQaDatabase,
  stopChild,
} from "./qa-server.mjs";

test("QA CLI defaults match the documented review URL", () => {
  assert.equal(DEFAULT_QA_API_PORT, 8010);
  assert.equal(DEFAULT_QA_WEB_PORT, 5180);
});

test("QA database survives restarts by port and can still run ephemerally", async (context) => {
  const tempRoot = await mkdtemp(join(tmpdir(), "la-lanh-qa-database-test-"));
  context.after(async () => {
    await rm(tempRoot, { recursive: true, force: true });
  });

  const projectRoot = join(tempRoot, "project-a");
  const first = prepareQaDatabase({ webPort: 5202, env: {}, projectRoot, tempRoot });
  const second = prepareQaDatabase({ webPort: 5202, env: {}, projectRoot, tempRoot });
  assert.equal(first.databaseUrl, second.databaseUrl);
  assert.equal(first.cleanup, null);
  assert.ok(first.storagePath);
  await access(first.storagePath);

  const otherProject = prepareQaDatabase({
    webPort: 5202,
    env: {},
    projectRoot: join(tempRoot, "project-b"),
    tempRoot,
  });
  assert.notEqual(first.databaseUrl, otherProject.databaseUrl);

  const ephemeral = prepareQaDatabase({
    webPort: 5203,
    env: { LA_LANH_QA_EPHEMERAL: "1" },
    projectRoot,
    tempRoot,
  });
  assert.equal(typeof ephemeral.cleanup, "function");
  ephemeral.cleanup();
});

// Codex #753 r1: the launcher told the API to stop and left at once, and its callers waited only
// for the launcher's exit, so the API's shutdown lines could arrive after the log had been read.
const SLOW_WRITER = "process.stdout.write('ready\\n'); process.on('SIGTERM', () => setTimeout(() => { process.stdout.write('late-line\\n'); process.exit(0); }, 300)); setInterval(() => {}, 1000);";
// A launcher of the old kind: passes its output on to a child, and on SIGTERM signals it and leaves.
const HASTY_PARENT = `const { spawn } = require('node:child_process'); const child = spawn(process.execPath, ['-e', ${JSON.stringify(SLOW_WRITER)}], { stdio: 'inherit' }); process.on('SIGTERM', () => { child.kill('SIGTERM'); process.exit(0); });`;

function startCollecting(script) {
  const child = spawn(process.execPath, ["-e", script], { stdio: ["ignore", "pipe", "pipe"] });
  const seen = { output: "", atExit: null };
  child.stdout.on("data", (chunk) => { seen.output += chunk; });
  child.once("exit", () => { seen.atExit = seen.output; });
  const ready = new Promise((resolveReady) => {
    child.stdout.on("data", () => { if (seen.output.includes("ready")) resolveReady(); });
  });
  return { child, seen, ready };
}

test("drainOnStop waits for lines a grandchild writes after the child itself has exited", async () => {
  const { child, seen, ready } = startCollecting(HASTY_PARENT);
  const stop = drainOnStop(child);
  await ready;
  await stop();
  assert.ok(!seen.atExit.includes("late-line"), "the line is not there yet when the child exits: waiting for exit reads half a log");
  assert.match(seen.output, /late-line/);
  await stop();
});

test("drainOnStop rejects and kills a child that never closes its output", async () => {
  const { child, ready } = startCollecting("process.stdout.write('ready\\n'); process.on('SIGTERM', () => {}); setInterval(() => {}, 1000);");
  const stop = drainOnStop(child);
  const gone = new Promise((resolveGone) => child.once("exit", resolveGone));
  await ready;
  await assert.rejects(stop({ timeoutMs: 300 }), /chưa đóng đầu ra/);
  await gone;
  assert.equal(child.signalCode, "SIGKILL");
});

test("stopChild resolves only after the child has finished its own shutdown", async () => {
  const { child, seen, ready } = startCollecting(SLOW_WRITER);
  const closed = new Promise((resolveClosed) => child.once("close", resolveClosed));
  await ready;
  await stopChild(child);
  assert.equal(child.exitCode, 0);
  await stopChild(child);
  await closed;
  assert.match(seen.output, /late-line/);
});

test("the launcher leaves only after the API has stopped", async () => {
  const source = await readFile(new URL("./qa-server.mjs", import.meta.url), "utf8");
  assert.match(source, /leaving \?\?= stopChild\(api\)\.then\(/);
  assert.ok(!/process\.once\("SIGTERM", \(\) => \{ stop\(\); process\.exit\(0\); \}\)/.test(source));
});

test("QA server serves SPA deep links and proxies API readiness", async (context) => {
  const distDir = await mkdtemp(join(tmpdir(), "la-lanh-qa-"));
  await writeFile(join(distDir, "index.html"), "<main>Lá Lành QA</main>");

  const upstream = createServer((_request, response) => {
    response.writeHead(200, { "content-type": "application/json" });
    response.end(JSON.stringify({ status: "ready", source: "api" }));
  });
  await new Promise((resolve) => upstream.listen(0, "127.0.0.1", resolve));
  context.after(() => upstream.close());
  const upstreamAddress = upstream.address();
  assert(upstreamAddress && typeof upstreamAddress === "object");

  const api = createQaServer({
    distDir,
    apiOrigin: `http://127.0.0.1:${upstreamAddress.port}`,
    readiness: { status: "ready" },
  });
  await new Promise((resolve) => api.listen(0, "127.0.0.1", resolve));
  context.after(() => api.close());

  const address = api.address();
  assert(address && typeof address === "object");
  const origin = `http://127.0.0.1:${address.port}`;

  const deepLink = await fetch(`${origin}/welcome`);
  assert.equal(deepLink.status, 200);
  assert.match(await deepLink.text(), /Lá Lành QA/);

  const capabilityLink = await fetch(`${origin}/share/secret-capability`);
  assert.equal(capabilityLink.status, 200);
  assert.equal(capabilityLink.headers.get("cache-control"), "no-store, max-age=0");
  assert.equal(
    capabilityLink.headers.get("x-robots-tag"),
    "noindex, nofollow, noarchive",
  );

  const radarCapability = await fetch(`${origin}/radar/i/private-token`);
  assert.equal(radarCapability.status, 200);
  assert.equal(radarCapability.headers.get("cache-control"), "no-store, max-age=0");
  assert.equal(
    radarCapability.headers.get("x-robots-tag"),
    "noindex, nofollow, noarchive",
  );

  const readiness = await fetch(`${origin}/__qa/ready`);
  assert.equal(readiness.status, 200);
  assert.deepEqual(await readiness.json(), { status: "ready" });
  assert.equal(readiness.headers.get("cache-control"), "no-store");

  const qaAlias = await fetch(`${origin}/qa`, { redirect: "manual" });
  assert.equal(qaAlias.status, 302);
  assert.equal(qaAlias.headers.get("location"), "/welcome");
  assert.equal(qaAlias.headers.get("cache-control"), "no-store");

  const apiReadiness = await fetch(`${origin}/v1/ready`);
  assert.equal(apiReadiness.status, 200);
  assert.deepEqual(await apiReadiness.json(), { status: "ready", source: "api" });
});

test("a scheme-relative request target never leaves the configured API origin", async (context) => {
  const distDir = await mkdtemp(join(tmpdir(), "la-lanh-qa-"));
  await writeFile(join(distDir, "index.html"), "<main>Lá Lành QA</main>");
  const seen = { api: [], other: [] };
  const api = createServer((request, response) => {
    seen.api.push(request.url);
    response.writeHead(200, { "content-type": "application/json" });
    response.end("{}");
  });
  const other = createServer((request, response) => {
    seen.other.push(request.headers.cookie ?? "");
    response.end("{}");
  });
  await new Promise((resolve) => api.listen(0, "127.0.0.1", resolve));
  await new Promise((resolve) => other.listen(0, "127.0.0.1", resolve));
  const qa = createQaServer({ distDir, apiOrigin: `http://127.0.0.1:${api.address().port}` });
  await new Promise((resolve) => qa.listen(0, "127.0.0.1", resolve));
  context.after(async () => {
    await Promise.all([api, other, qa].map((server) => new Promise((resolve) => server.close(resolve))));
    await rm(distDir, { recursive: true, force: true });
  });

  const { request: httpRequest } = await import("node:http");
  const status = await new Promise((resolve, reject) => {
    const outgoing = httpRequest({
      host: "127.0.0.1",
      port: qa.address().port,
      path: `//127.0.0.1:${other.address().port}/v1/session`,
      headers: { cookie: "la_lanh_guest=synthetic-canary" },
    }, (response) => { response.resume(); response.on("end", () => resolve(response.statusCode)); });
    outgoing.on("error", reject);
    outgoing.end();
  });
  assert.equal(status, 200);
  assert.deepEqual(seen.other, []);
  assert.deepEqual(seen.api, ["/v1/session"]);
});

test("the QA proxy upstream is fixed to an http loopback origin", () => {
  assert.deepEqual(
    { ...loopbackApiTarget("http://127.0.0.1:8010") },
    { hostname: "127.0.0.1", port: 8010, host: "127.0.0.1:8010" },
  );
  assert.equal(loopbackApiTarget("http://localhost:8010").hostname, "localhost");
  assert.equal(loopbackApiTarget("http://[::1]:8010").hostname, "::1");
  assert.equal(loopbackApiTarget("http://127.0.0.1").port, 80);
  for (const origin of [
    "https://127.0.0.1:8010",
    "http://example.com:8010",
    "http://127.0.0.2:8010",
    "http://10.0.0.1:8010",
    "http://user:pass@127.0.0.1:8010",
    "http://127.0.0.1:8010/v1",
    "http://127.0.0.1:8010/?x=1",
    "file:///etc/passwd",
    "not a url",
  ]) {
    assert.throws(() => loopbackApiTarget(origin), TypeError, origin);
    assert.throws(() => createQaServer({ distDir: "/nonexistent", apiOrigin: origin }), TypeError, origin);
  }
});

test("absolute-form request targets keep only their path on the loopback API", async (context) => {
  const distDir = await mkdtemp(join(tmpdir(), "la-lanh-qa-"));
  await writeFile(join(distDir, "index.html"), "<main>Lá Lành QA</main>");
  const seen = { api: [], other: [] };
  const api = createServer((request, response) => {
    seen.api.push({ url: request.url, host: request.headers.host });
    response.writeHead(200, { "content-type": "application/json" });
    response.end("{}");
  });
  const other = createServer((request, response) => {
    seen.other.push(request.url);
    response.end("{}");
  });
  await new Promise((resolve) => api.listen(0, "127.0.0.1", resolve));
  await new Promise((resolve) => other.listen(0, "127.0.0.1", resolve));
  const apiPort = api.address().port;
  const qa = createQaServer({ distDir, apiOrigin: `http://127.0.0.1:${apiPort}` });
  await new Promise((resolve) => qa.listen(0, "127.0.0.1", resolve));
  context.after(async () => {
    await Promise.all([api, other, qa].map((server) => new Promise((resolve) => server.close(resolve))));
    await rm(distDir, { recursive: true, force: true });
  });

  const { request: httpRequest } = await import("node:http");
  const status = await new Promise((resolve, reject) => {
    const outgoing = httpRequest({
      host: "127.0.0.1",
      port: qa.address().port,
      path: `http://127.0.0.1:${other.address().port}/v1/ready?probe=1`,
    }, (response) => { response.resume(); response.on("end", () => resolve(response.statusCode)); });
    outgoing.on("error", reject);
    outgoing.end();
  });
  assert.equal(status, 200);
  assert.deepEqual(seen.other, []);
  assert.deepEqual(seen.api, [{ url: "/v1/ready?probe=1", host: `127.0.0.1:${apiPort}` }]);
});
