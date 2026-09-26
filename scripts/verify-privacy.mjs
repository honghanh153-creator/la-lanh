import { readFileSync } from "node:fs";
import { join, relative } from "node:path";
import { cwd } from "node:process";
import { globSync } from "node:fs";

const root = cwd();
const scannedRoots = ["apps/api/app", "apps/web/src"];
const sensitiveFields = [
  "birth_date",
  "birthDate",
  "dateOfBirth",
  "dob",
  "birth_time",
  "birthTime",
  "birth_time_local",
  "birthTimeLocal",
  "birth_place",
  "birthPlace",
  "place_id",
  "placeId",
  "latitude",
  "longitude",
];
const sensitiveFieldPattern = sensitiveFields.join("|");
const experimentFields = ["action_key", "background_lens", "outcome"];
const experimentFieldPattern = experimentFields.join("|");
const patterns = [
  /console\.log/i,
  new RegExp(`logger\\.(debug|info|warning|error|exception)\\([^)]*(${sensitiveFieldPattern})`, "i"),
  new RegExp(`[?&](${sensitiveFieldPattern})=`, "i"),
  new RegExp(`[?&](${experimentFieldPattern})=`, "i"),
  new RegExp(`logger\\.(debug|info|warning|error|exception)\\([^)]*(${experimentFieldPattern})`, "i"),
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

const providerSource = readFileSync(
  join(root, "apps/api/app/infrastructure/generation/openai.py"),
  "utf8",
);
const safePayloadSource = providerSource.split("def _safe_payload", 2)[1]?.split(
  "def _parse_response",
  1,
)[0] ?? "";
const forbiddenProviderKeys = [
  "birth_date",
  "birth_time",
  "birth_time_local",
  "place_id",
  "latitude",
  "longitude",
  "guest_id",
  "profile_id",
  "session_id",
  "chart_id",
];
for (const key of forbiddenProviderKeys) {
  if (new RegExp(`["']${key}["']\\s*:`).test(safePayloadSource)) {
    findings.push(`Provider allowlist contains forbidden key: ${key}`);
  }
}
if (!/["']store["']:\s*False/.test(providerSource)) {
  findings.push("Responses requests must explicitly set store=false.");
}
for (const statefulFeature of ["previous_response_id", "conversation", "tools", "background"]) {
  if (new RegExp(`["']${statefulFeature}["']\\s*:`).test(providerSource)) {
    findings.push(`Provider request must remain one-shot and stateless: ${statefulFeature}`);
  }
}

const clientSource = readFileSync(join(root, "apps/web/src/shared/api/client.ts"), "utf8");
if (/localStorage\.setItem\([^\n]*(guest|owner|session)[_-]?(token|credential)/i.test(clientSource)) {
  findings.push("Native client must not persist guest/owner session credentials in localStorage.");
}
if (!/X-La-Lanh-Client["']:\s*["']capacitor-v1/.test(clientSource)) {
  findings.push("Native API calls must carry the explicit Capacitor client marker.");
}

for (const publicSource of [
  "apps/api/app/domains/share/models.py",
  "apps/api/app/api/v1/routes/share_artifacts.py",
]) {
  const source = readFileSync(join(root, publicSource), "utf8");
  for (const field of ["action_key", "background_lens", "outcome", "experiment_id"]) {
    if (new RegExp(`^\\s*${field}\\s*:`, "m").test(source)) {
      findings.push(`Public share contract contains experiment field ${field}: ${publicSource}`);
    }
  }
}

if (findings.length > 0) {
  console.error("Privacy guard failed:");
  console.error(findings.join("\n"));
  process.exit(1);
}

console.log("Privacy guard passed.");
