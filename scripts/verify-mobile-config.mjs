import { readFileSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";

const root = fileURLToPath(new URL("..", import.meta.url));

function source(path) {
  return readFileSync(new URL(`../${path}`, import.meta.url), "utf8");
}

export function validateMobileApiBaseUrl(value) {
  let parsed;
  try {
    parsed = new URL(value);
  } catch {
    throw new Error("Mobile API base URL must be an absolute HTTPS URL.");
  }
  if (parsed.protocol !== "https:" || !parsed.hostname) {
    throw new Error("Mobile API base URL must be an absolute HTTPS URL.");
  }
  if (parsed.username || parsed.password) {
    throw new Error("Mobile API base URL must not contain credentials.");
  }
  if (parsed.search) throw new Error("Mobile API base URL must not contain a query string.");
  if (parsed.hash) throw new Error("Mobile API base URL must not contain a fragment.");
  if (parsed.pathname === "/") {
    throw new Error("Mobile API base URL must include the versioned API path.");
  }
  return value.replace(/\/$/, "");
}

export function inspectMobileReleaseConfig() {
  const config = source("apps/mobile/capacitor.config.ts");
  const manifest = source("apps/mobile/android/app/src/main/AndroidManifest.xml");
  const privacyManifest = source("apps/mobile/ios/App/App/PrivacyInfo.xcprivacy");
  const xcodeProject = source("apps/mobile/ios/App/App.xcodeproj/project.pbxproj");
  const findings = [];

  const checks = [
    [config, /ios:\s*\{[^}]*scheme:\s*["']la-lanh["']/s, "The iOS scheme must be the ASCII-safe value la-lanh."],
    [config, /loggingBehavior:\s*["']none["']/, "Capacitor release logging must be disabled."],
    [config, /allowNavigation:\s*\[\s*\]/, "Native WebView navigation must stay deny-by-default."],
    [config, /cleartext:\s*false/, "Capacitor cleartext traffic must be disabled."],
    [config, /allowMixedContent:\s*false/, "Android mixed content must be disabled."],
    [config, /CapacitorCookies:\s*\{\s*enabled:\s*true/s, "Native cookie support must be enabled."],
    [config, /CapacitorHttp:\s*\{\s*enabled:\s*true/s, "Native HTTP transport must be enabled."],
    [config, /webContentsDebuggingEnabled:\s*false/g, "Release WebView debugging must be disabled."],
    [manifest, /android:allowBackup=["']false["']/, "Android backup must be disabled."],
    [manifest, /android:usesCleartextTraffic=["']false["']/, "Android cleartext traffic must be disabled."],
    [privacyManifest, /<key>NSPrivacyTracking<\/key>\s*<false\/>/, "iOS tracking declaration must stay false."],
    [privacyManifest, /NSPrivacyCollectedDataTypeUserID/, "iOS privacy manifest must declare the guest user ID."],
    [privacyManifest, /NSPrivacyCollectedDataTypePreciseLocation/, "iOS privacy manifest must declare birth-place coordinates."],
    [privacyManifest, /NSPrivacyCollectedDataTypeOtherUserContent/, "iOS privacy manifest must declare user-provided profile content."],
    [privacyManifest, /NSPrivacyCollectedDataTypeOtherDataTypes/, "iOS privacy manifest must declare derived chart data."],
    [xcodeProject, /PrivacyInfo\.xcprivacy in Resources/, "The app target must bundle its privacy manifest."],
  ];

  for (const [body, pattern, message] of checks) {
    if (!pattern.test(body)) findings.push(message);
  }
  const debugMatches = config.match(/webContentsDebuggingEnabled:\s*false/g) ?? [];
  if (debugMatches.length < 2) {
    findings.push("Both iOS and Android release WebView debugging must be disabled.");
  }
  if (/server:\s*\{[^}]*\burl\s*:/s.test(config)) {
    findings.push("Packaged releases must not load a remote server URL in the WebView.");
  }
  return findings;
}

function run() {
  const findings = inspectMobileReleaseConfig();
  if (findings.length > 0) {
    console.error("Mobile release guard failed:\n" + findings.join("\n"));
    process.exitCode = 1;
    return;
  }
  console.log(`Mobile release guard passed for ${root}.`);
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? "").href) run();
