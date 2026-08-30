import { execFileSync } from "node:child_process";
import { readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const packageRoot = fileURLToPath(new URL("..", import.meta.url));
const contractPath = join(packageRoot, "openapi", "v1.json");
const outputPath = join(packageRoot, "src", "v1.ts");
const checkMode = process.argv.includes("--check");
const command = process.platform === "win32" ? "openapi-typescript.cmd" : "openapi-typescript";

if (!checkMode) {
  execFileSync(command, [contractPath, "--output", outputPath], { stdio: "inherit" });
  process.stdout.write("Generated packages/contracts/src/v1.ts\n");
  process.exit(0);
}

const temporaryPath = join(tmpdir(), `la-lanh-contract-${process.pid}.ts`);

try {
  execFileSync(command, [contractPath, "--output", temporaryPath], { stdio: "inherit" });
  const expected = readFileSync(outputPath, "utf8");
  const generated = readFileSync(temporaryPath, "utf8");

  if (expected !== generated) {
    process.stderr.write("Generated TypeScript contract drift detected; run `pnpm contracts:generate`.\n");
    process.exitCode = 1;
  } else {
    process.stdout.write("Generated TypeScript contract is current.\n");
  }
} finally {
  rmSync(temporaryPath, { force: true });
}
