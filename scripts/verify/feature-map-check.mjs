#!/usr/bin/env node
// Coverage check for docs/operations/feature-map.json:
// - every route in apps/web/src/app/router.tsx has a feature-map entry (and no entry names a dead route);
// - every selector name in the map exists in app source (or in the verify fixtures for fake data);
// - fixtures, source files and walk steps are valid.
// Usage: node scripts/verify/feature-map-check.mjs   (exit 1 when there are problems)
import { readFileSync } from "node:fs";
import { isMain } from "../is-main.mjs";

import { checkMap, FIXTURES_PATH, loadAppSource, loadMap, parseRouterRoutes, ROUTER_PATH } from "./feature-map.mjs";

export function runCheck() {
  const map = loadMap();
  const routes = parseRouterRoutes(readFileSync(ROUTER_PATH, "utf8"));
  const problems = checkMap(map, {
    routes,
    appSource: loadAppSource(),
    fixtureSource: readFileSync(FIXTURES_PATH, "utf8"),
  });
  return { problems, routes: routes.length, features: map.features.length };
}

if (isMain(import.meta.url)) {
  const { problems, routes, features } = runCheck();
  if (problems.length) {
    console.error(`feature-map: ${problems.length} problem(s)`);
    for (const problem of problems) console.error(`- ${problem}`);
    console.error("Fix docs/operations/feature-map.json in the same PR that changes routes or screen text.");
    process.exit(1);
  }
  console.log(`feature-map: ok (${features} features cover ${routes} routes)`);
}
