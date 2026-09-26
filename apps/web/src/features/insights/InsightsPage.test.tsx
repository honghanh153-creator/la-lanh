import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { getInsightOverview } from "../../shared/api/client";
import { InsightsPage } from "./InsightsPage";

const claimDetail = {
  hook: "Một tín hiệu riêng.",
  meaning: "Một lớp nghĩa có căn cứ.",
  manifestation: "Một biểu hiện đời thường.",
  watch_for: "Một điểm cần quan sát.",
  micro_action: "Một việc nhỏ để thử.",
  evidence: ["Một vị trí trong chart"],
};

vi.mock("../../shared/api/client", async (original) => {
  const actual = await original<typeof import("../../shared/api/client")>();
  return { ...actual, getInsightOverview: vi.fn() };
});

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}><MemoryRouter><InsightsPage /></MemoryRouter></QueryClientProvider>);
}

describe("InsightsPage", () => {
  beforeEach(() => vi.mocked(getInsightOverview).mockReset());

  it("shows a privacy-safe precision gate", async () => {
    vi.mocked(getInsightOverview).mockResolvedValue({
      status: "locked", required_fields: ["birth_time", "birth_place"], reading: null,
      bodies: [], houses_available: false, time_precision: "unknown",
    });
    renderPage();
    expect(await screen.findByText("Cần giờ và nơi sinh để đọc đủ chart.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Mở lớp sâu" })).toHaveAttribute("href", "/birth-time");
  });

  it("renders the returned synthesis instead of hard-coded Sun/Moon", async () => {
    vi.mocked(getInsightOverview).mockResolvedValue({
      status: "ready", required_fields: [], houses_available: true, time_precision: "exact", bodies: [],
      reading: {
        tradition: "western", config_hash: "abc123456789", observed_at: "2026-09-04T00:00:00Z",
        disclaimer: "Nội dung tham khảo.",
        provenance: { engine: "swiss_ephemeris", version: "2.10.03", release_commit: "x", ephemeris_set: "se1", profile: "v2", tradition: "western", zodiac: "tropical", ayanamsa: null, config_hash: "abc123456789" },
        claims: [
          { ...claimDetail, id: "mercury-sign", domain: "mind", title: "Mạch suy nghĩ", summary: "Một lớp đọc thật.", factor_refs: ["natal:mercury"], confidence: "high" },
          { ...claimDetail, id: "venus-sign", domain: "relating", title: "Cách kết nối", summary: "Một lớp đọc thật.", factor_refs: ["natal:venus"], confidence: "high" },
          { ...claimDetail, id: "mars-sign", domain: "drive", title: "Động lực", summary: "Một lớp đọc thật.", factor_refs: ["natal:mars"], confidence: "high" },
          { ...claimDetail, id: "jupiter-sign", domain: "core", title: "Vùng nở rộng", summary: "Một lớp đọc thật.", factor_refs: ["natal:jupiter"], confidence: "high" },
        ],
      },
      reading_projection: {
        scope_key: "a".repeat(64), available_update: null,
        aura_transition: { profile_readiness: "aura_ready", transition_id: "b".repeat(64), acknowledged: true, unlock_layers: ["multi_factor"] },
        active: {
          revision_id: "00000000-0000-4000-8000-000000000010", source: "deterministic",
          mode: "full_synthesis", purpose: "aura", tradition: "western", precision: "exact",
          sections: {
            hook: "Nhiều lớp trong bạn đang nói cùng lúc.",
            thesis: "Bạn vừa cần tự do, vừa cần một nơi đủ chắc để quay về.",
            manifestation: "Ngoài đời có thể trông như việc bạn đổi nhịp rất nhanh.",
            transit: null, micro_action: "Chọn một việc cần rõ trước tối nay.",
          },
          evidence: { title: "Căn cứ trong lá số", claims: ["Sao Thủy ở Song Tử"], framework_disclosure: "Khung diễn giải." },
          disclaimer: "Lá gợi một góc nhìn — quyền quyết định vẫn ở bạn.", created_at: "2026-09-07T00:00:00Z",
        },
      },
    });
    renderPage();
    expect(await screen.findByRole("heading", { name: "Nhiều lớp trong bạn đang nói cùng lúc." })).toBeInTheDocument();
    expect(screen.getByText("Aura · Tổng hòa lá số")).toBeInTheDocument();
    expect(await screen.findByText("Mạch suy nghĩ")).toBeInTheDocument();
    expect(screen.getByText("Vùng nở rộng")).toBeInTheDocument();
  });
});
