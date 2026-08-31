import { readFileSync } from "node:fs";
import { join, relative } from "node:path";
import { cwd } from "node:process";
import { globSync } from "node:fs";

const root = cwd();
const scannedRoots = ["apps/api/app", "apps/web/src"];
const patterns = [
  /console\.log/i,
  /logger\.(debug|info|warning|error|exception)\([^)]*(birth_date|birthDate|dateOfBirth|dob)/i,
  /[?&](birth_date|birthDate|dateOfBirth|dob)=/i,
];

const findings = [];
for (const scannedRoot of scannedRoots) {
  for (const file of globSync(`${scannedRoot}/**/*.{py,ts,tsx}`, { cwd: root })) {
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
  console.error("Privacy guard failed:");
  console.error(findings.join("\n"));
  process.exit(1);
}

console.log("Privacy guard passed.");
