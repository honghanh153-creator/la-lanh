import { spawnSync } from "node:child_process";

import { validateMobileApiBaseUrl } from "./verify-mobile-config.mjs";

const apiBaseUrl = validateMobileApiBaseUrl(process.env.VITE_API_BASE_URL ?? "");
const pnpm = process.platform === "win32" ? "pnpm.cmd" : "pnpm";

function run(args, env = process.env) {
  const result = spawnSync(pnpm, args, { env, stdio: "inherit" });
  if (result.error) throw result.error;
  if (result.status !== 0) process.exit(result.status ?? 1);
}

run(["--filter", "@la-lanh/web", "build"], { ...process.env, VITE_API_BASE_URL: apiBaseUrl });
run(["--filter", "@la-lanh/mobile", "sync"]);
