import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  checkInMood,
  getBirthSupplement,
  getCurrentMood,
  getDailyNote,
  getResonanceStatus,
  listSavedNotes,
  type DailyNote,
  type ReadingProjection,
} from "../../shared/api/client";
import { clearCachedDailyNote } from "../../shared/storage/noteCache";
import { HomePage } from "./HomePage";

// P04 lifecycle boundary on the real Home component (adapted from Codex's #48 probes): only API
// I/O is mocked; every assertion is on what the device stores or sends.
vi.mock("../../shared/api/client", async (original) => {
  const actual = await original<typeof import("../../shared/api/client")>();
  return {
    ...actual,
    checkInMood: vi.fn(),
    getBirthSupplement: vi.fn(),
    getContextualReading: vi.fn(),
    getCurrentMood: vi.fn(),
    getDailyNote: vi.fn(),
    getResonanceStatus: vi.fn(),
    listSavedNotes: vi.fn(),
    recordResonance: vi.fn(),
  };
});

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}><MemoryRouter><HomePage /></MemoryRouter></QueryClientProvider>);
}

const baseNoteId = "00000000-0000-4000-8000-000000000001";

function content(revisionId: string, mode: "vibe_fallback" | "full_synthesis", hook: string) {
  return {
    revision_id: revisionId, source: "deterministic" as const, mode,
    purpose: "daily_note" as const, tradition: "western" as const,
    precision: mode === "vibe_fallback" ? "unknown" as const : "exact" as const,
    sections: {
      hook,
      thesis: mode === "vibe_fallback" ? "Đây là một lớp đọc nhẹ từ ngày sinh." : "Nhiều yếu tố trong lá số đang được đọc cùng nhau.",
      manifestation: "Ngoài đời có thể trông như một khoảng dừng trước khi trả lời.",
      transit: null,
      micro_action: "Chọn một câu cần nói rõ hôm nay.",
    },
    evidence: { title: "Căn cứ trong lá số", claims: ["Một dữ kiện đã duyệt"], framework_disclosure: "Chiêm tinh là một khung diễn giải." },
    disclaimer: "Lá gợi một góc nhìn — quyền quyết định vẫn ở bạn.",
    created_at: "2026-09-07T00:00:00Z",
  };
}

function projection(active: ReturnType<typeof content>, update?: ReturnType<typeof content>): ReadingProjection {
  return {
    scope_key: "a".repeat(64), active,
    available_update: update ? { revision_id: update.revision_id, message: "Có một bản đọc mới đang chờ bạn", content: update } : null,
    aura_transition: { profile_readiness: "vibe", transition_id: null, acknowledged: false, unlock_layers: [] },
  };
}

function noteWith(readingProjection: ReadingProjection): DailyNote {
  return {
    id: baseNoteId, note_date: "2026-09-07",
    title: "Legacy title", body: "Legacy body", full_body: "Legacy full body",
    context_label: "Legacy context", content_version: "legacy-v1", persona_mode: "vibe",
    persona_label: "Mềm", persona_version: "v1", source_level: "date_only_sun",
    astrology_source_version: "2.10.03", fallback_used: false, fallback_reason: null,
    created_at: "2026-09-07T00:00:00Z", awakening: null, sky_chapter: null,
    reading_projection: readingProjection,
  };
}



const vibe = content("00000000-0000-4000-8000-000000000010", "vibe_fallback", "Chậm lại một nhịp.");

describe("Home pending mood lifecycle (P04)", () => {
 beforeEach(() => {
  vi.clearAllMocks(); localStorage.clear(); sessionStorage.clear(); clearCachedDailyNote();
  sessionStorage.setItem("la-lanh-session-epoch", "epoch-a");
  Object.defineProperty(navigator,"onLine",{value:true,configurable:true});
  vi.mocked(getDailyNote).mockResolvedValue(noteWith(projection(vibe)));
  vi.mocked(getCurrentMood).mockResolvedValue(null); vi.mocked(listSavedNotes).mockResolvedValue([]);
  vi.mocked(getBirthSupplement).mockRejectedValue(new Error("none"));
  vi.mocked(getResonanceStatus).mockResolvedValue({consented:false,feedback_count:0,last_choice:null});
 });
 it("discards expired private mood even when Home opens offline", async () => {
  const raw=JSON.stringify({session_epoch:"epoch-a",note_id:baseNoteId,mood:"Chill",saved_at:Date.now()-25*60*60*1000});
  localStorage.setItem("la-lanh-pending-mood-v1",raw);
  Object.defineProperty(navigator,"onLine",{value:false,configurable:true});
  renderPage(); await screen.findByRole("heading",{name:vibe.sections.hook});
  expect(localStorage.getItem("la-lanh-pending-mood-v1")).toBeNull();
  expect(checkInMood).not.toHaveBeenCalled();
 });
 it("does not renew the first-capture clock after a retry fails", async () => {
  const savedAt=Date.now()-23*60*60*1000;
  localStorage.setItem("la-lanh-pending-mood-v1",JSON.stringify({session_epoch:"epoch-a",note_id:baseNoteId,mood:"Chill",saved_at:savedAt}));
  vi.mocked(checkInMood).mockRejectedValue(new Error("offline"));
  renderPage(); await waitFor(()=>expect(checkInMood).toHaveBeenCalledTimes(1));
  await waitFor(()=>expect(localStorage.getItem("la-lanh-pending-mood-v1")).not.toBeNull());
  expect(JSON.parse(localStorage.getItem("la-lanh-pending-mood-v1")!).saved_at).toBe(savedAt);
 });
 it("removes the prior pending mood once a later deliberate choice is acknowledged", async () => {
  vi.mocked(checkInMood).mockRejectedValueOnce(new Error("offline")).mockResolvedValueOnce({id:"00000000-0000-4000-8000-000000000099",daily_note_id:baseNoteId,mood:"Rực",checked_in_at:"2026-10-22T00:00:00Z"});
  const user=userEvent.setup(); renderPage();
  await user.click(await screen.findByRole("button",{name:"Chọn mood hôm nay"}));
  await user.click(screen.getByRole("button",{name:/Chill/}));
  await waitFor(()=>expect(localStorage.getItem("la-lanh-pending-mood-v1")).not.toBeNull());
  await user.click(screen.getByRole("button",{name:"Mood hôm nay: Chill"}));
  await user.click(screen.getByRole("button",{name:/Rực/}));
  await waitFor(()=>expect(checkInMood).toHaveBeenCalledTimes(2));
  await screen.findByRole("button",{name:"Mood hôm nay: Rực"});
  expect(localStorage.getItem("la-lanh-pending-mood-v1")).toBeNull();
 });

 it("does not relabel an old owner's failed mutation under a new session", async () => {
  let reject!:(reason:Error)=>void;
  vi.mocked(checkInMood).mockImplementationOnce(()=>new Promise((_resolve,r)=>{reject=r;}));
  const user=userEvent.setup();renderPage();
  await user.click(await screen.findByRole("button",{name:"Chọn mood hôm nay"}));
  await user.click(screen.getByRole("button",{name:/Chill/}));
  await waitFor(()=>expect(checkInMood).toHaveBeenCalledTimes(1));
  localStorage.clear();sessionStorage.setItem("la-lanh-session-epoch","epoch-b");
  await act(()=>{reject(new Error("session changed"));return Promise.resolve();});
  expect(localStorage.getItem("la-lanh-pending-mood-v1")).toBeNull();
 });

});
