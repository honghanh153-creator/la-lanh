// Deterministic same-origin Web Locks scheduler for transport-only fixtures.
// Separate client module instances use this one manager, like sibling tabs. As in browsers,
// each lock name is its own resource: holding one name never blocks another.
export function testLocks(): LockManager {
  type Job = { mode: LockMode; run: () => void };
  type Resource = { queue: Job[]; readers: number; writer: boolean };
  const resources = new Map<string, Resource>();
  const resource = (name: string): Resource => {
    let found = resources.get(name);
    if (!found) {
      found = { queue: [], readers: 0, writer: false };
      resources.set(name, found);
    }
    return found;
  };
  const drain = (state: Resource) => {
    if (state.writer) return;
    while (state.queue.length) {
      const job = state.queue[0];
      if (!job || (job.mode === "exclusive" && state.readers > 0)) return;
      state.queue.shift();
      if (job.mode === "exclusive") state.writer = true;
      else state.readers += 1;
      job.run();
      if (state.writer) return;
    }
  };
  function request<T>(name: string, callback: LockGrantedCallback<T>): Promise<T>;
  function request<T>(name: string, options: LockOptions, callback: LockGrantedCallback<T>): Promise<T>;
  function request<T>(name: string, options: LockOptions | LockGrantedCallback<T>, callback?: LockGrantedCallback<T>): Promise<T> {
    const settings = typeof options === "function" ? {} : options;
    const work = typeof options === "function" ? options : callback;
    if (!work) return Promise.reject(new Error("Missing lock callback"));
    const mode = settings.mode ?? "exclusive";
    const state = resource(name);
    return new Promise<T>((resolve, reject) => {
      const job: Job = { mode, run: () => {
        settings.signal?.removeEventListener("abort", abort);
        const lock: Lock = { name, mode };
        Promise.resolve().then(() => work(lock)).then(resolve, reject).finally(() => {
          if (mode === "exclusive") state.writer = false;
          else state.readers -= 1;
          drain(state);
        });
      } };
      const abort = () => {
        const index = state.queue.indexOf(job);
        if (index >= 0) state.queue.splice(index, 1);
        const reason: unknown = settings.signal?.reason;
        reject(reason instanceof Error ? reason : new DOMException("Cancelled", "AbortError"));
        drain(state);
      };
      if (settings.signal?.aborted) { abort(); return; }
      settings.signal?.addEventListener("abort", abort, { once: true });
      state.queue.push(job);
      drain(state);
    });
  }
  return { request, query: () => Promise.resolve({ held: [], pending: [] }) };
}

export function testRequestUrl(input: RequestInfo | URL): string {
  if (typeof input === "string") return input;
  return input instanceof URL ? input.href : input.url;
}
