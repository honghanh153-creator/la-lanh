import assert from "node:assert/strict";
import { mkdtemp, writeFile } from "node:fs/promises";
import { createServer } from "node:http";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import {
  createQaServer,
  DEFAULT_QA_API_PORT,
  DEFAULT_QA_WEB_PORT,
} from "./qa-server.mjs";

test("QA CLI defaults match the documented review URL", () => {
  assert.equal(DEFAULT_QA_API_PORT, 8010);
  assert.equal(DEFAULT_QA_WEB_PORT, 5180);
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
