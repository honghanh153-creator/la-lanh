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

// L04: acceptance checks name an AC of the feature, say what they prove, and their selectors are checked.
test("acceptance checks are tied to the feature's AC and say what they prove", () => {
  const withChecks = (ac_checks, ac = ["US-02 AC01"]) => feature({ ac, states: { default: { ...feature().states.default, ac_checks } } });
  const ok = checkMap({ features: [withChecks([{ ac: "US-02 AC01", part: "nút khớp hiện", expect: { role: "button", name: "Khớp tín hiệu" } }, { ac: "US-02 AC01", part: "phần còn lại", manual: "kiểm tay" }])] }, { routes: ["/birth"], appSource, fixtureSource });
  assert.deepEqual(ok, []);
  const bad = checkMap({ features: [withChecks([
    { ac: "US-09 AC01", part: "x", expect: { role: "button", name: "Khớp tín hiệu" } },
    { ac: "US-02 AC01", part: "", expect: { role: "button", name: "Không có trong mã" } },
    { ac: "US-02 AC01", part: "y" },
    { ac: "US-02 AC01", part: "z", text: "chữ", count: { selector: { role: "link" }, max: 6 } },
  ])] }, { routes: ["/birth"], appSource, fixtureSource });
  assert.ok(bad.some((p) => p.includes('"US-09 AC01" is not in the feature\'s "ac" list')));
  assert.ok(bad.some((p) => p.includes('says no "part"')));
  assert.ok(bad.some((p) => p.includes("Không có trong mã")), "an AC selector name is checked against the source");
  assert.ok(bad.some((p) => p.includes('needs "expect", "count" or a "manual" note')));
  assert.ok(bad.some((p) => p.includes('"text" needs an "expect" selector')));
});
