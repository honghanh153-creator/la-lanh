import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { getInsightOverview, getPrivateReading } from "../../shared/api/client";
import { ReadingDetailPage } from "./ReadingDetailPage";

vi.mock("../../shared/api/client", async (original) => {
  const actual = await original<typeof import("../../shared/api/client")>();
  return { ...actual, getInsightOverview: vi.fn(), getPrivateReading: vi.fn() };
});

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={["/insights/moon-sign?tradition=western"]}>
        <Routes><Route path="/insights/:claimId" element={<ReadingDetailPage />} /></Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("ReadingDetailPage", () => {
  beforeEach(() => {
    vi.mocked(getInsightOverview).mockResolvedValue({
      status: "ready", required_fields: [], houses_available: true, time_precision: "exact", bodies: [],
      reading: {
        tradition: "western", config_hash: "abc123456789", observed_at: "2026-09-06T00:00:00Z",
        disclaimer: "Nội dung tham khảo.",
        provenance: { engine: "swiss_ephemeris", version: "2.10.03", release_commit: "x", ephemeris_set: "se1", profile: "v2", tradition: "western", zodiac: "tropical", ayanamsa: null, config_hash: "abc123456789" },
        claims: [{
          id: "moon-sign", domain: "emotions", title: "Nhịp cảm xúc", summary: "Mặt Trăng ở Bọ Cạp · Nhà 8.", confidence: "high",
          hook: "Bạn không lạnh, bạn chỉ cần đúng tần số.",
          meaning: "Mặt Trăng mô tả cách bạn xử lý cảm xúc. Ở Bọ Cạp, phần này cần chiều sâu và niềm tin.",
          manifestation: "Trong đời thường, bạn có thể im một nhịp trước khi nói thật.",
          watch_for: "Giữ kín quá lâu có thể khiến áp lực nói thay mình.",
          micro_action: "Viết một câu mình cảm thấy và một câu mình cần.",
          evidence: ["Mặt Trăng ở Bọ Cạp", "Mặt Trăng ở Nhà 8"],
          factor_refs: [
            "natal:moon:longitude:213.408725", "natal:moon:sign:scorpio", "natal:moon:house:8",
            "natal:aspect:moon:square:mars:orb:1.240",
          ],
        }],
      },
    });
    vi.mocked(getPrivateReading).mockResolvedValue({
      scope_key: "a".repeat(64),
      available_update: null,
      aura_transition: { profile_readiness: "aura_ready", transition_id: "b".repeat(64), acknowledged: true, unlock_layers: ["multi_factor"] },
      active: {
        revision_id: "00000000-0000-4000-8000-000000000010",
        source: "deterministic",
        mode: "full_synthesis",
        purpose: "reading_detail",
        tradition: "western",
        precision: "exact",
        sections: {
          hook: "Bạn không lạnh, bạn chỉ cần đúng tần số.",
          thesis: "Bạn thường xử lý cảm xúc bằng cách tìm một cấu trúc đủ an toàn.",
          manifestation: "Trong đời thường, điều này có thể trông như việc bạn im một nhịp trước khi nói thật.",
          transit: null,
          micro_action: "Viết một câu bạn muốn nói, rồi đọc lại trước khi gửi.",
        },
        evidence: {
          title: "Căn cứ trong lá số",
          claims: ["Mặt Trăng ở Bọ Cạp", "Mặt Trăng ở Nhà 8"],
          framework_disclosure: "Chiêm tinh là một khung diễn giải, không phải bằng chứng khoa học hay phán quyết thực tế về bạn.",
        },
        disclaimer: "Lá gợi một góc nhìn — quyền quyết định vẫn ở bạn.",
        created_at: "2026-09-07T00:00:00Z",
      },
    });
  });

  it("renders the selected server-owned claim instead of a generic synthesis", async () => {
    const user = userEvent.setup();
    renderPage();

    expect(await screen.findByRole("heading", { name: "Bạn không lạnh, bạn chỉ cần đúng tần số." })).toBeInTheDocument();
    expect(screen.getByText(/bạn có thể im một nhịp/)).toBeInTheDocument();
    const evidence = screen.getByText("Mặt Trăng ở Nhà 8").closest("details");
    expect(evidence).not.toHaveAttribute("open");
    expect(screen.queryByText("Nhịp trời hôm nay")).not.toBeInTheDocument();

    await user.click(screen.getByText("Căn cứ trong lá số"));
    expect(evidence).toHaveAttribute("open");
    expect(screen.getByText("Mặt Trăng ở Nhà 8")).toBeInTheDocument();
    expect(screen.getByText(/khung để tự đối chiếu/)).toBeInTheDocument();
    expect(screen.getByText("Nội dung tham khảo.")).toBeInTheDocument();
    expect(getPrivateReading).not.toHaveBeenCalled();
  });
});
