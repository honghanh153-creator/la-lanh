import { readFileSync } from "node:fs";
import { join, relative } from "node:path";
import { cwd } from "node:process";
import { globSync } from "node:fs";

const root = cwd();
const runtimeRoots = ["apps/api/app", "apps/web/src", "packages/contracts/src"];
const allowed = new Set([
  "apps/web/src/features/consent/DemoPage.tsx",
]);

const patterns = [
  /\bmock(?:ed|s)?\b/i,
  /\bfake\b/i,
  /\bfixture\b/i,
  /\bhardcoded\b/i,
];

const findings = [];
for (const runtimeRoot of runtimeRoots) {
  for (const file of globSync(`${runtimeRoot}/**/*.{py,ts,tsx}`, { cwd: root })) {
    if (allowed.has(file)) {
      continue;
    }
    const body = readFileSync(join(root, file), "utf8");
    const lines = body.split("\n");
    lines.forEach((line, index) => {
      if (patterns.some((pattern) => pattern.test(line))) {
        findings.push(`${relative(root, join(root, file))}:${index + 1}: ${line.trim()}`);
      }
    });
  }
}

if (findings.length > 0) {
  console.error("Runtime mock guard failed:");
  console.error(findings.join("\n"));
  process.exit(1);
}

console.log("Runtime mock guard passed.");
