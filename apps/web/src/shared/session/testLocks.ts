// Deterministic same-origin Web Locks scheduler for transport-only fixtures.
// Separate client module instances use this one manager, like sibling tabs.
export function testLocks(): LockManager {
  type Job = { mode: LockMode; run: () => void };
  const queue: Job[] = [];
  let readers = 0;
  let writer = false;
  const drain = () => {
    if (writer) return;
    while (queue.length) {
      const job = queue[0];
      if (!job || (job.mode === "exclusive" && readers > 0)) return;
      queue.shift();
      if (job.mode === "exclusive") writer = true;
      else readers += 1;
      job.run();
      if (writer) return;
    }
  };
  function request<T>(name: string, callback: LockGrantedCallback<T>): Promise<T>;
  function request<T>(name: string, options: LockOptions, callback: LockGrantedCallback<T>): Promise<T>;
  function request<T>(name: string, options: LockOptions | LockGrantedCallback<T>, callback?: LockGrantedCallback<T>): Promise<T> {
    const settings = typeof options === "function" ? {} : options;
    const work = typeof options === "function" ? options : callback;
    if (!work) return Promise.reject(new Error("Missing lock callback"));
    const mode = settings.mode ?? "exclusive";
    return new Promise<T>((resolve, reject) => {
      const job: Job = { mode, run: () => {
        settings.signal?.removeEventListener("abort", abort);
        const lock: Lock = { name, mode };
        Promise.resolve().then(() => work(lock)).then(resolve, reject).finally(() => {
          if (mode === "exclusive") writer = false;
          else readers -= 1;
          drain();
        });
      } };
      const abort = () => {
        const index = queue.indexOf(job);
        if (index >= 0) queue.splice(index, 1);
        const reason: unknown = settings.signal?.reason;
        reject(reason instanceof Error ? reason : new DOMException("Cancelled", "AbortError"));
        drain();
      };
      if (settings.signal?.aborted) { abort(); return; }
      settings.signal?.addEventListener("abort", abort, { once: true });
      queue.push(job);
      drain();
    });
  }
  return { request, query: () => Promise.resolve({ held: [], pending: [] }) };
}

export function testRequestUrl(input: RequestInfo | URL): string {
  if (typeof input === "string") return input;
  return input instanceof URL ? input.href : input.url;
}
