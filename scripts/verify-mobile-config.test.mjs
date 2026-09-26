import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { inspectMobileReleaseConfig, validateMobileApiBaseUrl } from "./verify-mobile-config.mjs";

test("packaged app configuration is privacy-first and fail-closed", () => {
  assert.deepEqual(inspectMobileReleaseConfig(), []);
});

test("packaged app uses an ASCII-safe iOS scheme", () => {
  const config = readFileSync(
    new URL("../apps/mobile/capacitor.config.ts", import.meta.url),
    "utf8",
  );
  assert.match(config, /ios:\s*\{[^}]*scheme:\s*["']la-lanh["']/s);
});

test("native API origin must be explicit HTTPS", () => {
  assert.equal(validateMobileApiBaseUrl("https://api.lalanh.vn/v1"), "https://api.lalanh.vn/v1");
  assert.throws(() => validateMobileApiBaseUrl("/v1"), /absolute HTTPS/);
  assert.throws(() => validateMobileApiBaseUrl("http://api.lalanh.vn/v1"), /absolute HTTPS/);
  assert.throws(() => validateMobileApiBaseUrl("https://user:secret@api.lalanh.vn/v1"), /credentials/);
  assert.throws(() => validateMobileApiBaseUrl("https://api.lalanh.vn/v1?token=x"), /query/);
});

test("iOS app target carries a non-tracking privacy manifest", () => {
  const manifest = readFileSync(
    new URL("../apps/mobile/ios/App/App/PrivacyInfo.xcprivacy", import.meta.url),
    "utf8",
  );
  assert.match(manifest, /<key>NSPrivacyTracking<\/key>\s*<false\/>/);
  assert.match(manifest, /NSPrivacyCollectedDataTypeUserID/);
  assert.match(manifest, /NSPrivacyCollectedDataTypePreciseLocation/);
  assert.match(manifest, /NSPrivacyCollectedDataTypeOtherUserContent/);
  assert.match(manifest, /NSPrivacyCollectedDataTypeProductInteraction/);
  assert.match(manifest, /NSPrivacyCollectedDataTypeOtherDataTypes/);
});
