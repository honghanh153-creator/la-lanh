import assert from "node:assert/strict";
import { test } from "node:test";

import { checkMap, featuresForChangedFiles, loadMap, parseRouterRoutes } from "./feature-map.mjs";
import { runCheck } from "./feature-map-check.mjs";

const fixtureSource = `const FIXTURES = {\n  guest: { onboarding: "none" },\n  "signed-in": { onboarding: "completed" },\n};\nconst x = "Tên từ dữ liệu giả";`;
const appSource = `<button>Khớp tín hiệu</button><h1>Bạn xuất hiện ngày nào?</h1>`;

function feature(overrides = {}) {
  return {
    id: "birth-date", title: "Nhập ngày sinh", us: ["US-02"], routes: ["/birth"], owner_only: false,
    source_files: ["scripts/verify/feature-map.mjs"], user_path: ["Welcome"],
    states: { default: { fixture: "guest", walk: [{ goto: "/birth" }], ready: { role: "button", name: "Khớp tín hiệu" } } },
    ...overrides,
  };
}

test("the real feature map covers every router route and every selector exists", () => {
  const { problems, routes, features } = runCheck();
  assert.deepEqual(problems, []);
  assert.ok(routes >= 40, `expected the router to have many routes, got ${routes}`);
  assert.ok(features >= 30, `expected many features, got ${features}`);
});

test("router parsing: relative children get a leading slash, index is /, absolute routes stay", () => {
  const routes = parseRouterRoutes(`children: [{ index: true }, { path: "welcome" }, { path: "radar/result/:requestId" }], { path: "/studio" }`);
  assert.deepEqual(routes, ["/", "/radar/result/:requestId", "/studio", "/welcome"]);
});

test("a router route with no map entry is reported", () => {
  const problems = checkMap({ features: [feature()] }, { routes: ["/birth", "/new-screen"], appSource, fixtureSource });
  assert.deepEqual(problems, ['route "/new-screen" has no feature-map entry']);
});

test("a map route that is no longer in the router is reported", () => {
  const problems = checkMap({ features: [feature({ routes: ["/birth", "/old"] })] }, { routes: ["/birth"], appSource, fixtureSource });
  assert.ok(problems.some((p) => p.includes('route "/old" is not in the router')), problems.join("\n"));
});

test("a selector whose name is not in the source is reported, fixture text is checked against fixtures", () => {
  const f = feature({
    key_selectors: [
      { role: "button", name: "Nút không tồn tại" },
      { role: "heading", name: "Tên từ dữ liệu giả", source: "fixture" },
      { role: "heading", name: "Bạn xuất hiện ngày nào?", source: "fixture" },
    ],
  });
  const problems = checkMap({ features: [f] }, { routes: ["/birth"], appSource, fixtureSource });
  assert.deepEqual(problems, [
    'feature "birth-date": key_selectors[0] name "Nút không tồn tại" is not in apps/web/src',
    'feature "birth-date": key_selectors[2] name "Bạn xuất hiện ngày nào?" is not in apps/web/tests/verify/fixtures.ts',
  ]);
});

test("unknown fixture, unknown role, bad walk and missing story gap are reported", () => {
  const f = feature({
    us: [],
    states: { default: { fixture: "nobody", walk: [{ click: { role: "buton", name: "Khớp tín hiệu" } }], ready: { role: "button", name: "Khớp tín hiệu" } } },
  });
  const problems = checkMap({ features: [f] }, { routes: ["/birth"], appSource, fixtureSource });
  assert.ok(problems.some((p) => p.includes('unknown fixture "nobody"')));
  assert.ok(problems.some((p) => p.includes('unknown role "buton"')));
  assert.ok(problems.some((p) => p.includes("must start with a goto step")));
  assert.ok(problems.some((p) => p.includes('record it in "gap"')));
});

test("changed files map to features; shared web files select every feature", () => {
  const map = loadMap();
  const home = featuresForChangedFiles(map, ["apps/web/src/features/home/HomePage.tsx"]);
  assert.equal(home.all, false);
  assert.ok(home.ids.includes("home") && home.ids.includes("mood"));
  assert.ok(!home.ids.includes("tarot"));

  const shared = featuresForChangedFiles(map, ["apps/web/src/shared/styles/global.css"]);
  assert.equal(shared.all, true);
  assert.equal(shared.ids.length, map.features.length);

  const docsOnly = featuresForChangedFiles(map, ["docs/user-stories/US-03-doc-note-hom-nay.md", "apps/web/src/features/home/HomePage.test.tsx"]);
  assert.deepEqual(docsOnly, { ids: [], all: false, shared: [] });
});
