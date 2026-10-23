import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  ApiProblem,
  getSession,
  getTarotSession,
  startTarotSession,
  type GuestSession,
  type TarotSession,
} from "../../shared/api/client";
import { clearPersonalDataOnDevice } from "../../shared/storage/clearPersonalData";
import { TarotPage } from "./TarotPage";

// P01 (audit 2026-10-22): a free-text Tarot question must never sit in Web Storage. The retry key
// for an unchanged draft lives in memory only, bound to the draft and the guest session.

vi.mock("../../shared/api/client", async (original) => {
  const actual = await original<typeof import("../../shared/api/client")>();
  return {
    ...actual,
    createTarotGuest: vi.fn(),
    getSession: vi.fn(),
    getTarotSession: vi.fn(),
    startTarotSession: vi.fn(),
  };
});

const CANARY = "zqcanary7tim";
const QUESTION = `Mình nên nói rõ điều gì ${CANARY}?`;

function session(epoch = "synthetic-epoch-a"): GuestSession {
  return {
    state: "active",
    onboarding_status: "completed",
    expires_at: "2026-11-20T00:00:00Z",
    resumed: true,
    session_epoch: epoch,
  };
}

const created: TarotSession = {
  id: "8e3b79e4-74fc-4cbc-8975-77fa0c77c6a8",
  version: 1,
  state: "choosing",
  context: "relationships",
  spread: "three_card",
  spread_map: "three_unblock",
  voice: "playful_grounded",
  origin: "direct",
  question: QUESTION,
  fan_size: 78,
  required_cards: 3,
  selected_cards: [],
  created_at: "2026-10-22T12:00:00Z",
  updated_at: "2026-10-22T12:00:00Z",
  expires_at: "2026-11-20T12:00:00Z",
};

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={["/tarot"]}>
        <Routes>
          <Route path="/tarot" element={<TarotPage />} />
          <Route path="/tarot/:sessionId" element={<TarotPage />} />
          <Route path="/welcome" element={<p>Start safely</p>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

function webStorageText(): string {
  const values: string[] = [];
  for (const store of [sessionStorage, localStorage]) {
    for (let index = 0; index < store.length; index += 1) {
      const key = store.key(index);
      if (key) values.push(`${key}=${store.getItem(key) ?? ""}`);
    }
  }
  return values.join("\n");
}

async function ask(question = QUESTION) {
  const user = userEvent.setup();
  const box = screen.getByRole("textbox", { name: /Câu hỏi của bạn/ });
  await user.clear(box);
  await user.type(box, question);
  await user.click(screen.getByRole("button", { name: /^Xòe \d lá$/ }));
  return user;
}

function sentKeys(): string[] {
  return vi.mocked(startTarotSession).mock.calls.map(([body]) => body.idempotency_key);
}

describe("Tarot question storage (P01)", () => {
  const consoleSpies: ReturnType<typeof vi.spyOn>[] = [];

  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
    localStorage.clear();
    vi.mocked(getSession).mockResolvedValue(session());
    vi.mocked(getTarotSession).mockResolvedValue(created);
    for (const method of ["log", "info", "warn", "error", "debug"] as const) {
      consoleSpies.push(vi.spyOn(console, method).mockImplementation(() => undefined));
    }
  });

  afterEach(() => {
    for (const spy of consoleSpies.splice(0)) {
      for (const call of spy.mock.calls) expect(JSON.stringify(call)).not.toContain(CANARY);
      spy.mockRestore();
    }
  });

  it("keeps no question in Web Storage after a failed start, and retries with the same key", async () => {
    vi.mocked(startTarotSession).mockRejectedValue(new Error("synthetic offline failure"));
    renderPage();
    const user = await ask();
    await waitFor(() => expect(startTarotSession).toHaveBeenCalledTimes(1));
    expect(webStorageText()).not.toContain(CANARY);

    await user.click(screen.getByRole("button", { name: /^Xòe \d lá$/ }));
    await waitFor(() => expect(startTarotSession).toHaveBeenCalledTimes(2));
    const [first, second] = sentKeys();
    expect(second).toBe(first); // unchanged draft, same session: idempotent retry
    expect(webStorageText()).not.toContain(CANARY);
  });

  it("uses a new key once the draft changes", async () => {
    vi.mocked(startTarotSession).mockRejectedValue(new Error("synthetic offline failure"));
    renderPage();
    await ask();
    await waitFor(() => expect(startTarotSession).toHaveBeenCalledTimes(1));
    await ask(`Mình nên hỏi lại điều gì ${CANARY}?`);
    await waitFor(() => expect(startTarotSession).toHaveBeenCalledTimes(2));
    const [first, second] = sentKeys();
    expect(second).not.toBe(first);
  });

  it("keeps no question in Web Storage after a reframe rejection", async () => {
    vi.mocked(startTarotSession).mockRejectedValue(
      new ApiProblem(422, "TAROT_QUESTION_REFRAME_REQUIRED", "reframe", {
        suggested_reframe: "Mình muốn hiểu điều gì rõ hơn?",
        explanation: "Câu hỏi cần mở hơn.",
      }),
    );
    renderPage();
    await ask();
    await waitFor(() => expect(startTarotSession).toHaveBeenCalledTimes(1));
    expect(webStorageText()).not.toContain(CANARY);
  });

  it("removes the legacy stored question on load and keeps nothing after a remount", async () => {
    sessionStorage.setItem(
      "la-lanh-tarot-start",
      JSON.stringify({ signature: JSON.stringify({ question: QUESTION }), key: "legacy-key" }),
    );
    renderPage();
    await waitFor(() => expect(sessionStorage.getItem("la-lanh-tarot-start")).toBeNull());

    vi.mocked(startTarotSession).mockRejectedValue(new Error("synthetic offline failure"));
    await ask();
    await waitFor(() => expect(startTarotSession).toHaveBeenCalledTimes(1));
    cleanup();
    renderPage();
    expect(screen.getByRole("textbox", { name: /Câu hỏi của bạn/ })).toHaveValue("");
    expect(webStorageText()).not.toContain(CANARY);
  });

  it("binds the retry key to the guest session: a new session never reuses it", async () => {
    vi.mocked(startTarotSession).mockRejectedValue(new Error("synthetic offline failure"));
    renderPage();
    const user = await ask();
    await waitFor(() => expect(startTarotSession).toHaveBeenCalledTimes(1));

    sessionStorage.setItem("la-lanh-session-epoch", "synthetic-epoch-b");
    vi.mocked(getSession).mockResolvedValue(session("synthetic-epoch-b"));
    await user.click(screen.getByRole("button", { name: /^Xòe \d lá$/ }));
    await waitFor(() => expect(startTarotSession).toHaveBeenCalledTimes(2));
    const [first, second] = sentKeys();
    expect(second).not.toBe(first);
    expect(webStorageText()).not.toContain(CANARY);
  });

  it("keeps no question after a successful start and after clearing personal data", async () => {
    vi.mocked(startTarotSession).mockResolvedValue(created);
    renderPage();
    await ask();
    await waitFor(() => expect(startTarotSession).toHaveBeenCalledTimes(1));
    expect(webStorageText()).not.toContain(CANARY);

    sessionStorage.setItem("la-lanh-tarot-start", `{"signature":"${CANARY}"}`);
    await clearPersonalDataOnDevice();
    expect(webStorageText()).not.toContain(CANARY);
  });
});
