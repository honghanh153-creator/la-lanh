/* global caches, fetch, self, URL */

const CACHE_NAME = "la-lanh-app-shell-v4";
const APP_SHELL = [
  "/",
  "/index.html",
  "/offline.html",
  "/manifest.webmanifest",
  "/app-icon.svg",
  "/assets/note/warm-bento-note.jpg",
  "/assets/note/dark-editorial-note.jpg",
  "/assets/note/dark-editorial-eclipse.jpg",
  "/assets/note/cosmic-glass-sky.png",
  "/assets/note/moon-field-notes-crescent-v2.png",
  "/assets/note/moon-field-notes-paper-v2.png",
];

async function precacheAppShell() {
  const cache = await caches.open(CACHE_NAME);
  await cache.addAll(APP_SHELL);

  // Vite fingerprints the app bundles. Discover those current URLs from the
  // built HTML during installation so a fresh install can reopen offline.
  const indexResponse = await fetch("/index.html", { cache: "no-store" });
  if (!indexResponse.ok) return;
  await cache.put("/index.html", indexResponse.clone());
  const html = await indexResponse.text();
  const generatedAssets = [...html.matchAll(/(?:src|href)=["'](\/assets\/[^"']+)["']/g)]
    .map((match) => match[1]);
  if (generatedAssets.length > 0) {
    await cache.addAll([...new Set(generatedAssets)]);
  }
}

self.addEventListener("install", (event) => {
  event.waitUntil(precacheAppShell());
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key)),
    )),
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (
    url.pathname === "/v1"
    || url.pathname.startsWith("/v1/")
    || url.pathname === "/metrics"
    || url.pathname.startsWith("/metrics/")
  ) return;

  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request)
        .catch(() => caches.match("/index.html").then((cached) => cached ?? caches.match("/offline.html"))),
    );
    return;
  }

  const isGeneratedAsset = url.pathname.startsWith("/assets/");
  if (
    url.origin !== self.location.origin
    || (!isGeneratedAsset && !APP_SHELL.includes(url.pathname))
  ) return;

  event.respondWith(
    fetch(request)
      .then(async (response) => {
        if (!response.ok) return response;
        const copy = response.clone();
        const cache = await caches.open(CACHE_NAME);
        await cache.put(request, copy);
        return response;
      })
      .catch(async (error) => {
        const cached = await caches.match(request);
        if (cached) return cached;
        throw error;
      }),
  );
});
