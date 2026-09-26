import { readFileSync } from "node:fs";
import { join } from "node:path";
import { runInNewContext } from "node:vm";

import { beforeEach, describe, expect, it, vi } from "vitest";

type WorkerHandler = (event: unknown) => void;

describe("service worker runtime caching", () => {
  const handlers = new Map<string, WorkerHandler>();
  const cachePut = vi.fn<(request: Request, response: Response) => Promise<void>>();
  const cacheMatch = vi.fn<(request: Request | string) => Promise<Response | undefined>>();
  const cacheAddAll = vi.fn<(requests: string[]) => Promise<void>>();
  const fetchMock = vi.fn<(request: Request) => Promise<Response>>();

  beforeEach(() => {
    handlers.clear();
    cachePut.mockReset().mockResolvedValue(undefined);
    cacheMatch.mockReset().mockResolvedValue(undefined);
    cacheAddAll.mockReset().mockResolvedValue(undefined);
    fetchMock.mockReset();

    const source = readFileSync(join(process.cwd(), "public/sw.js"), "utf8");
    runInNewContext(source, {
      URL,
      fetch: fetchMock,
      caches: {
        match: cacheMatch,
        open: vi.fn().mockResolvedValue({ addAll: cacheAddAll, put: cachePut }),
        keys: vi.fn().mockResolvedValue([]),
        delete: vi.fn().mockResolvedValue(true),
      },
      self: {
        location: { origin: "https://app.lalanh.vn" },
        clients: { claim: vi.fn() },
        skipWaiting: vi.fn(),
        addEventListener: (type: string, handler: WorkerHandler) => handlers.set(type, handler),
      },
    });
  });

  it("precaches the current fingerprinted bundles during a fresh install", async () => {
    fetchMock.mockResolvedValueOnce(new Response(`<!doctype html>
      <link rel="stylesheet" href="/assets/index-STYLE.css">
      <script type="module" src="/assets/index-APP.js"></script>`));
    const waitUntil = vi.fn<(promise: Promise<void>) => void>();

    handlers.get("install")?.({ waitUntil });

    expect(waitUntil).toHaveBeenCalledTimes(1);
    await waitUntil.mock.calls[0]?.[0];
    expect(cacheAddAll).toHaveBeenCalledTimes(2);
    expect(cacheAddAll.mock.calls[1]?.[0]).toEqual([
      "/assets/index-STYLE.css",
      "/assets/index-APP.js",
    ]);
  });

  it("caches a same-origin generated asset and serves it when the network is offline", async () => {
    const asset = new Request("https://app.lalanh.vn/assets/index-C0FFEE.js");
    const onlineResponse = new Response("export const ready = true", { status: 200 });
    const cachedResponse = new Response("export const ready = true", { status: 200 });
    fetchMock.mockResolvedValueOnce(onlineResponse).mockRejectedValueOnce(new TypeError("offline"));
    cacheMatch.mockResolvedValueOnce(cachedResponse);
    const fetchHandler = handlers.get("fetch");
    expect(fetchHandler).toBeDefined();

    let firstResponse: Promise<Response> | undefined;
    fetchHandler?.({
      request: asset,
      respondWith: (response: Promise<Response>) => { firstResponse = response; },
    });
    expect(await firstResponse).toBe(onlineResponse);
    await vi.waitFor(() => expect(cachePut).toHaveBeenCalledTimes(1));
    expect(cachePut.mock.calls[0]?.[0].url).toBe(asset.url);

    let offlineResponse: Promise<Response> | undefined;
    fetchHandler?.({
      request: asset,
      respondWith: (response: Promise<Response>) => { offlineResponse = response; },
    });
    expect(await offlineResponse).toBe(cachedResponse);
  });

  it.each([
    "https://app.lalanh.vn/v1",
    "https://app.lalanh.vn/v1/daily-note",
    "https://app.lalanh.vn/metrics",
    "https://app.lalanh.vn/metrics/runtime",
  ])("never intercepts or caches API and metrics traffic at %s", (url) => {
    const respondWith = vi.fn();

    handlers.get("fetch")?.({ request: new Request(url), respondWith });

    expect(respondWith).not.toHaveBeenCalled();
    expect(fetchMock).not.toHaveBeenCalled();
    expect(cachePut).not.toHaveBeenCalled();
  });
});
