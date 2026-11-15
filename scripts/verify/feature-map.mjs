// Shared helpers for the feature map (docs/operations/feature-map.json).
// Used by feature-map-check.mjs (coverage check) and verify.mjs (verification run).
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

export const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
export const MAP_PATH = join(REPO_ROOT, "docs/operations/feature-map.json");
export const ROUTER_PATH = join(REPO_ROOT, "apps/web/src/app/router.tsx");
export const WEB_SRC = join(REPO_ROOT, "apps/web/src");
export const FIXTURES_PATH = join(REPO_ROOT, "apps/web/tests/verify/fixtures.ts");

const ROLES = new Set([
  "button", "link", "heading", "textbox", "combobox", "checkbox", "radio", "switch", "region", "navigation",
  "main", "status", "alert", "note", "complementary", "group", "list", "listitem", "img", "dialog", "tab", "tablist",
]);
const STEP_KINDS = ["goto", "click", "fill", "check", "press", "expect"];

export function loadMap(path = MAP_PATH) {
  return JSON.parse(readFileSync(path, "utf8"));
}

/**
 * Route patterns from router.tsx. Children of the "/" shell are relative ("welcome"), top-level
 * routes are absolute ("/studio"); `index: true` is "/".
 */
export function parseRouterRoutes(source) {
  const routes = new Set();
  if (/\bindex:\s*true\b/.test(source)) routes.add("/");
  for (const match of source.matchAll(/\bpath:\s*"([^"]+)"/g)) {
    const raw = match[1];
    routes.add(raw.startsWith("/") ? raw : `/${raw}`);
  }
  return [...routes].sort();
}

function walkFiles(dir, out = []) {
  for (const name of readdirSync(dir)) {
    const full = join(dir, name);
    if (statSync(full).isDirectory()) walkFiles(full, out);
    else out.push(full);
  }
  return out;
}

/** Concatenated non-test source of apps/web/src (tsx/ts), used to prove a selector name exists. */
export function loadAppSource(srcDir = WEB_SRC) {
  return walkFiles(srcDir)
    .filter((file) => /\.(tsx?|css)$/.test(file) && !/\.test\.tsx?$/.test(file) && !file.includes(`${sep}test${sep}`))
    .map((file) => readFileSync(file, "utf8"))
    .join("\n");
}

/** All selectors in a feature with a label saying where each sits (for error messages). */
export function featureSelectors(feature) {
  const out = [];
  const add = (selector, where) => {
    if (!selector) return;
    out.push({ selector, where });
    if (selector.within) add(selector.within, `${where}.within`);
  };
  (feature.key_selectors ?? []).forEach((selector, index) => add(selector, `key_selectors[${index}]`));
  for (const [state, spec] of Object.entries(feature.states ?? {})) {
    if (!spec || spec.manual) continue;
    add(spec.ready, `states.${state}.ready`);
    (spec.ac_checks ?? []).forEach((check, index) => {
      add(check.expect, `states.${state}.ac_checks[${index}].expect`);
      add(check.count?.selector, `states.${state}.ac_checks[${index}].count.selector`);
    });
    (spec.walk ?? []).forEach((step, index) => {
      for (const kind of ["click", "fill", "check", "press", "expect"]) {
        if (step[kind] && typeof step[kind] === "object") add(step[kind], `states.${state}.walk[${index}].${kind}`);
      }
    });
  }
  return out;
}

export function automatedStates(feature) {
  return Object.entries(feature.states ?? {}).filter(([, spec]) => spec && !spec.manual);
}

/**
 * Problems with the map. `routes` are the router's patterns, `appSource` the app source text,
 * `fixtureSource` the fixtures module text. Returns a list of human-readable problems.
 */
export function checkMap(map, { routes, appSource, fixtureSource, repoRoot = REPO_ROOT }) {
  const problems = [];
  const features = Array.isArray(map.features) ? map.features : [];
  if (!features.length) problems.push("feature map has no features");
  const fixtureNames = new Set([...fixtureSource.matchAll(/^\s*"?([a-z][a-z0-9-]*)"?:\s*\{\s*onboarding:/gm)].map((m) => m[1]));
  const ids = new Set();
  const mapped = new Set();
  for (const feature of features) {
    const label = `feature "${feature.id ?? "?"}"`;
    if (!feature.id || !/^[a-z][a-z0-9-]*$/.test(feature.id)) problems.push(`${label}: id must be kebab-case`);
    if (ids.has(feature.id)) problems.push(`${label}: duplicate id`);
    ids.add(feature.id);
    for (const field of ["title", "routes", "user_path", "states", "source_files"]) {
      if (feature[field] === undefined) problems.push(`${label}: missing "${field}"`);
    }
    if (typeof feature.owner_only !== "boolean") problems.push(`${label}: "owner_only" must be true or false`);
    if (!Array.isArray(feature.us)) problems.push(`${label}: "us" must be a list (empty list + "gap" when no story)`);
    else if (!feature.us.length && !feature.gap) problems.push(`${label}: no user story; record it in "gap"`);
    for (const route of feature.routes ?? []) {
      if (!routes.includes(route)) problems.push(`${label}: route "${route}" is not in the router`);
      mapped.add(route);
    }
    for (const file of feature.source_files ?? []) {
      if (!existsSync(join(repoRoot, file))) problems.push(`${label}: source file "${file}" does not exist`);
    }
    const automated = automatedStates(feature);
    if (!automated.length) problems.push(`${label}: needs at least one automated state (fixture + walk + ready)`);
    for (const [state, spec] of automated) {
      if (!fixtureNames.has(spec.fixture)) problems.push(`${label}: states.${state} uses unknown fixture "${spec.fixture}"`);
      if (!spec.ready) problems.push(`${label}: states.${state} has no "ready" selector`);
      for (const [index, check] of (spec.ac_checks ?? []).entries()) {
        const at = `${label}: states.${state}.ac_checks[${index}]`;
        if (!(feature.ac ?? []).includes(check.ac)) problems.push(`${at}: "${check.ac}" is not in the feature's "ac" list`);
        if (!String(check.part ?? "").trim()) problems.push(`${at}: says no "part" (what this check proves)`);
        const kinds = ["expect", "count"].filter((kind) => check[kind]);
        if (kinds.length > 1) problems.push(`${at}: use "expect" or "count", not both`);
        if (!kinds.length && !String(check.manual ?? "").trim()) problems.push(`${at}: needs "expect", "count" or a "manual" note`);
        if (check.text !== undefined && !check.expect) problems.push(`${at}: "text" needs an "expect" selector`);
      }
      if (!Array.isArray(spec.walk) || !spec.walk.length || !spec.walk[0].goto) problems.push(`${label}: states.${state}.walk must start with a goto step`);
      for (const step of spec.walk ?? []) {
        const kinds = STEP_KINDS.filter((kind) => kind in step);
        if (kinds.length !== 1) problems.push(`${label}: states.${state} has a step with ${kinds.length ? kinds.join("+") : "no"} action`);
      }
    }
    for (const { selector, where } of featureSelectors(feature)) {
      if (!ROLES.has(selector.role)) problems.push(`${label}: ${where} has unknown role "${selector.role}"`);
      if (selector.name === undefined) continue;
      const haystack = selector.source === "fixture" ? fixtureSource : appSource;
      if (!haystack.includes(selector.name)) {
        const from = selector.source === "fixture" ? "apps/web/tests/verify/fixtures.ts" : "apps/web/src";
        problems.push(`${label}: ${where} name "${selector.name}" is not in ${from}`);
      }
    }
  }
  for (const route of routes) {
    if (!mapped.has(route)) problems.push(`route "${route}" has no feature-map entry`);
  }
  return problems;
}

function globToRegExp(pattern) {
  const escaped = pattern.replace(/[.+^${}()|[\]\\]/g, "\\$&").replace(/\*\*/g, "\u0000").replace(/\*/g, "[^/]*").replace(/\u0000/g, ".*");
  return new RegExp(`^${escaped}$`);
}

/**
 * Features touched by a list of changed repo-relative paths. Web source that no feature lists
 * (shared UI, styles, router, API client) can affect any screen, so it selects every feature.
 */
export function featuresForChangedFiles(map, changedFiles) {
  const selected = new Set();
  let shared = [];
  for (const file of changedFiles) {
    const owners = map.features.filter((feature) => (feature.source_files ?? []).some((pattern) => globToRegExp(pattern).test(file)));
    owners.forEach((feature) => selected.add(feature.id));
    const isWeb = file.startsWith("apps/web/src/") || file.startsWith("apps/web/public/") || file === "apps/web/index.html";
    if (!owners.length && isWeb && !/\.test\.tsx?$/.test(file)) shared.push(file);
    if (file.startsWith("apps/web/tests/verify/") || file === "docs/operations/feature-map.json") shared.push(file);
  }
  shared = [...new Set(shared)];
  if (shared.length) return { ids: map.features.map((feature) => feature.id), all: true, shared };
  return { ids: [...selected], all: false, shared };
}

export function toRepoPath(file) {
  return relative(REPO_ROOT, resolve(file)).split(sep).join("/");
}
