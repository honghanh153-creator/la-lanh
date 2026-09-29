import { spawn } from "node:child_process";
import { createHash } from "node:crypto";
import { chmodSync, createReadStream, existsSync, mkdirSync, mkdtempSync, rmSync } from "node:fs";
import { stat } from "node:fs/promises";
import { createServer, request as requestUpstream } from "node:http";
import { homedir, tmpdir } from "node:os";
import { extname, join, normalize, resolve, sep } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const MIME_TYPES = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".ico": "image/x-icon",
  ".jpg": "image/jpeg",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml",
  ".webmanifest": "application/manifest+json; charset=utf-8",
  ".woff": "font/woff",
  ".woff2": "font/woff2",
};

export const DEFAULT_QA_API_PORT = 8010;
export const DEFAULT_QA_WEB_PORT = 5180;

export function prepareQaDatabase({
  webPort,
  env = process.env,
  projectRoot = process.cwd(),
  tempRoot = tmpdir(),
} = {}) {
  if (!Number.isInteger(webPort) || webPort < 1 || webPort > 65_535) {
    throw new TypeError("webPort must be a valid port");
  }
  if (env.LA_LANH_QA_DATABASE_URL) {
    return { databaseUrl: env.LA_LANH_QA_DATABASE_URL, cleanup: null, storagePath: null };
  }
  if (env.LA_LANH_QA_EPHEMERAL === "1") {
    const directory = mkdtempSync(join(tempRoot, "la-lanh-qa-live-"));
    return {
      databaseUrl: `sqlite+aiosqlite:///${join(directory, "qa.db")}`,
      cleanup: () => rmSync(directory, { recursive: true, force: true }),
      storagePath: directory,
    };
  }

  const projectKey = createHash("sha256").update(resolve(projectRoot)).digest("hex").slice(0, 12);
  const directory = join(tempRoot, `la-lanh-qa-live-${projectKey}-${webPort}`);
  if (env.LA_LANH_QA_RESET === "1") {
    rmSync(directory, { recursive: true, force: true });
  }
  mkdirSync(directory, { recursive: true, mode: 0o700 });
  chmodSync(directory, 0o700);
  return {
    databaseUrl: `sqlite+aiosqlite:///${join(directory, "qa.db")}`,
    cleanup: null,
    storagePath: directory,
  };
}

const SECURITY_HEADERS = {
  "content-security-policy": "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self'; base-uri 'none'; object-src 'none'; frame-ancestors 'none'; form-action 'self'",
  "cross-origin-opener-policy": "same-origin",
  "permissions-policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
  "referrer-policy": "no-referrer",
  "x-content-type-options": "nosniff",
};

function sendJson(response, status, value) {
  response.writeHead(status, {
    ...SECURITY_HEADERS,
    "cache-control": "no-store",
    "content-type": "application/json; charset=utf-8",
  });
  response.end(JSON.stringify(value));
}

function proxyRequest(request, response, apiOrigin) {
  const target = new URL(request.url ?? "/", apiOrigin);
  const upstream = requestUpstream(target, {
    method: request.method,
    headers: { ...request.headers, host: target.host },
  }, (upstreamResponse) => {
    response.writeHead(upstreamResponse.statusCode ?? 502, {
      ...upstreamResponse.headers,
      ...SECURITY_HEADERS,
    });
    upstreamResponse.pipe(response);
  });
  upstream.setTimeout(15_000, () => upstream.destroy(new Error("API timeout")));
  upstream.on("error", () => sendJson(response, 502, { status: "api_unavailable" }));
  request.pipe(upstream);
}

async function serveStatic(request, response, distDir) {
  const url = new URL(request.url ?? "/", "http://127.0.0.1");
  let pathname;
  try {
    pathname = decodeURIComponent(url.pathname);
  } catch {
    sendJson(response, 400, { status: "invalid_path" });
    return;
  }

  const root = resolve(distDir);
  const relativePath = normalize(pathname).replace(/^[/\\]+/, "");
  let filePath = resolve(join(root, relativePath || "index.html"));
  if (filePath !== root && !filePath.startsWith(`${root}${sep}`)) {
    sendJson(response, 400, { status: "invalid_path" });
    return;
  }

  try {
    if (!(await stat(filePath)).isFile()) throw new Error("not a file");
  } catch {
    filePath = join(root, "index.html");
  }

  try {
    const file = await stat(filePath);
    const basename = filePath.slice(root.length + 1);
    const capabilityPath = pathname.startsWith("/share/")
      || pathname.startsWith("/la-chung/i/")
      || pathname.startsWith("/radar/i/");
    const revalidate = extname(filePath) === ".html"
      || basename === "sw.js"
      || basename === "manifest.webmanifest";
    response.writeHead(200, {
      ...SECURITY_HEADERS,
      "cache-control": capabilityPath
        ? "no-store, max-age=0"
        : revalidate
          ? "no-cache"
          : "public, max-age=31536000, immutable",
      "content-length": file.size,
      "content-type": MIME_TYPES[extname(filePath)] ?? "application/octet-stream",
      ...(capabilityPath ? { "x-robots-tag": "noindex, nofollow, noarchive" } : {}),
    });
    if (request.method === "HEAD") response.end();
    else createReadStream(filePath).pipe(response);
  } catch {
    sendJson(response, 500, { status: "web_build_unavailable" });
  }
}

export function createQaServer({
  distDir,
  apiOrigin = "http://127.0.0.1:8000",
  readiness = { status: "ready" },
} = {}) {
  if (!distDir) throw new TypeError("distDir is required");
  return createServer((request, response) => {
    const pathname = new URL(request.url ?? "/", "http://127.0.0.1").pathname;
    if (pathname === "/__qa/ready") {
      sendJson(response, readiness.status === "ready" ? 200 : 503, readiness);
      return;
    }
    if (pathname === "/qa") {
      response.writeHead(302, {
        ...SECURITY_HEADERS,
        "cache-control": "no-store",
        location: "/welcome",
      });
      response.end();
      return;
    }
    if (apiOrigin && (pathname.startsWith("/v1/") || pathname === "/metrics")) {
      proxyRequest(request, response, apiOrigin);
      return;
    }
    if (request.method !== "GET" && request.method !== "HEAD") {
      sendJson(response, 405, { status: "method_not_allowed" });
      return;
    }
    void serveStatic(request, response, distDir);
  });
}

async function waitForApi(origin, child, timeoutMs = 30_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (child.exitCode !== null) throw new Error(`API stopped with code ${child.exitCode}`);
    try {
      const response = await fetch(`${origin}/v1/ready`, { signal: AbortSignal.timeout(1_500) });
      if (response.ok) return;
    } catch {
      // The API needs a moment to initialize its database and ephemeris runtime.
    }
    await new Promise((resolveDelay) => setTimeout(resolveDelay, 250));
  }
  throw new Error("API did not become ready within 30 seconds");
}

function qaPort(name, fallback) {
  const value = Number.parseInt(process.env[name] ?? String(fallback), 10);
  if (!Number.isInteger(value) || value < 1 || value > 65_535) {
    throw new Error(`${name} phải là port hợp lệ.`);
  }
  return value;
}

async function startCli() {
  const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
  const distDir = join(root, "apps/web/dist");
  const indexFile = join(distDir, "index.html");
  if (!existsSync(indexFile)) {
    throw new Error("Chưa có web build. Hãy chạy `pnpm qa:build` trước.");
  }

  const apiPort = qaPort("LA_LANH_QA_API_PORT", DEFAULT_QA_API_PORT);
  const webPort = qaPort("LA_LANH_QA_WEB_PORT", DEFAULT_QA_WEB_PORT);
  const apiOrigin = `http://127.0.0.1:${apiPort}`;
  const webOrigin = `http://127.0.0.1:${webPort}`;
  const apiDir = join(root, "apps/api");
  const uv = process.env.UV_BIN ?? join(homedir(), ".local/bin/uv");
  if (!existsSync(uv)) {
    throw new Error("Không tìm thấy uv tại ~/.local/bin/uv. Hãy cài dependencies của API trước.");
  }
  const qaDatabase = prepareQaDatabase({ projectRoot: root, webPort });
  const apiEnv = {
    ...process.env,
    LA_LANH_DATABASE_URL: qaDatabase.databaseUrl,
    LA_LANH_ENVIRONMENT: "development",
    LA_LANH_CORS_ORIGINS: process.env.LA_LANH_CORS_ORIGINS
      ?? JSON.stringify([webOrigin]),
  };

  const api = spawn(uv, [
    "run", "--directory", apiDir, "uvicorn", "app.main:app",
    "--host", "127.0.0.1", "--port", String(apiPort),
    "--no-access-log",
  ], {
    cwd: root,
    env: apiEnv,
    stdio: ["ignore", "inherit", "inherit"],
  });

  const stop = () => {
    if (api.exitCode === null) api.kill("SIGTERM");
    qaDatabase.cleanup?.();
  };
  process.once("SIGINT", () => { stop(); process.exit(0); });
  process.once("SIGTERM", () => { stop(); process.exit(0); });

  try {
    await waitForApi(apiOrigin, api);
    const server = createQaServer({ distDir, apiOrigin });
    server.on("close", stop);
    server.listen(webPort, "127.0.0.1", () => {
      if (qaDatabase.storagePath && process.env.LA_LANH_QA_EPHEMERAL !== "1") {
        console.log(`QA data cục bộ: ${qaDatabase.storagePath} (LA_LANH_QA_RESET=1 để xoá)`);
      }
      console.log(`\nLá Lành QA đã sẵn sàng: http://127.0.0.1:${webPort}/welcome\n`);
    });
  } catch (error) {
    stop();
    throw error;
  }
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? "").href) {
  startCli().catch((error) => {
    console.error(error instanceof Error ? error.message : String(error));
    process.exitCode = 1;
  });
}
