import "@testing-library/jest-dom/vitest";
import { configure } from "@testing-library/react";

// findBy*/waitFor return as soon as the element appears; this only bounds how long they keep
// looking. Owner-bound pages (Radar history, private checks) render after a session → claim →
// history chain. Measured on 26/10/2026 (time to the Radar delete button): about 30 ms alone,
// 450–735 ms in a clean full web run, 1.9–3.5 s under machine load. That put the default
// 1,000 ms inside normal variance and made those waits fail intermittently.
export const ASYNC_UTIL_TIMEOUT_MS = 5_000;
configure({ asyncUtilTimeout: ASYNC_UTIL_TIMEOUT_MS });
