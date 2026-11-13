import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { getBirthSupplement, getInsightOverview, getPrivateReading } from "../../shared/api/client";
import { ReadingDetailPage } from "./ReadingDetailPage";

vi.mock("../../shared/api/client", async (original) => {
  const actual = await original<typeof import("../../shared/api/client")>();
  return { ...actual, getBirthSupplement: vi.fn(), getInsightOverview: vi.fn(), getPrivateReading: vi.fn() };
});

function renderPage(entry = "/insights/moon-sign?tradition=western") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[entry]}>
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

  it("does not promise houses and aspects when the birth time is approximate (#143 E4)", async () => {
    vi.mocked(getInsightOverview).mockResolvedValue({
      status: "ready", required_fields: [], houses_available: false, time_precision: "approximate", bodies: [],
      reading: {
        tradition: "western", config_hash: "abc123456789", observed_at: "2026-11-04T00:00:00Z",
        disclaimer: "Nội dung tham khảo.",
        provenance: { engine: "swiss_ephemeris", version: "2.10.03", release_commit: "x", ephemeris_set: "se1", profile: "v2", tradition: "western", zodiac: "tropical", ayanamsa: null, config_hash: "abc123456789" },
        claims: [{
          id: "sun-sign", domain: "core", title: "Lõi sáng", summary: "Mặt Trời ở Ma Kết.", confidence: "high",
          hook: "Một tín hiệu riêng.", meaning: "Một lớp nghĩa.", manifestation: "Một biểu hiện đời thường.",
          watch_for: "Một điểm cần quan sát.", micro_action: "Một việc nhỏ để thử.",
          evidence: ["Mặt Trời ở Ma Kết"], factor_refs: ["natal:sun:sign:capricorn"],
        }],
      },
    });
    renderPage("/insights/sun-sign?tradition=western");

    expect(await screen.findByText("Mặt Trời ở Ma Kết")).toBeInTheDocument();
    expect(screen.queryByText(/nhà và góc chiếu/)).not.toBeInTheDocument();
  });

  it("opens the full overview with every natal claim section", async () => {
    const user = userEvent.setup();
    const western = await vi.mocked(getInsightOverview).getMockImplementation()?.({ tradition: "western" } as never);
    const moon = western!.reading!.claims[0];
    vi.mocked(getInsightOverview).mockResolvedValue({
      ...western!,
      reading: {
        ...western!.reading!,
        tradition: "jyotish",
        claims: [
          moon,
          {
            id: "sun-sign", domain: "core", title: "Lõi sáng", summary: "Mặt Trời ở Ma Kết.", confidence: "high",
            hook: "Bạn hay nhận việc khó về mình trước.",
            meaning: "Mặt Trời mô tả điều bạn muốn làm cho tốt.",
            manifestation: "Bạn thường lập danh sách trước khi bắt đầu một việc mới.",
            watch_for: "Nhận quá nhiều việc cùng lúc dễ làm bạn mệt.",
            micro_action: "Chọn một việc trong danh sách để nhờ người khác.",
            evidence: ["Mặt Trời ở Ma Kết"], factor_refs: ["natal:sun:sign:capricorn"],
          },
        ],
      },
    } as never);
    renderPage("/insights/overview?tradition=jyotish");

    expect(await screen.findByText(/Mặt Trăng mô tả cách bạn xử lý cảm xúc/)).toBeInTheDocument();
    expect(screen.getByText("Bản đọc tổng quan · Jyotish")).toBeInTheDocument();
    // Every claim renders its own sections, not only the first one.
    expect(screen.getByRole("heading", { level: 2, name: "Bạn không lạnh, bạn chỉ cần đúng tần số." })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 2, name: "Bạn hay nhận việc khó về mình trước." })).toBeInTheDocument();
    expect(screen.getByText("Giữ kín quá lâu có thể khiến áp lực nói thay mình.")).toBeInTheDocument();
    expect(screen.getByText("Nhận quá nhiều việc cùng lúc dễ làm bạn mệt.")).toBeInTheDocument();
    expect(screen.getByText("Viết một câu mình cảm thấy và một câu mình cần.")).toBeInTheDocument();
    expect(screen.getByText("Chọn một việc trong danh sách để nhờ người khác.")).toBeInTheDocument();
    expect(screen.getAllByText("Căn cứ trong lá số")).toHaveLength(2);
    for (const summary of screen.getAllByText("Căn cứ trong lá số")) await user.click(summary);
    expect(screen.getByText("Mặt Trăng ở Nhà 8")).toBeVisible();
    expect(screen.getByText("Mặt Trời ở Ma Kết")).toBeVisible();
    expect(vi.mocked(getInsightOverview).mock.lastCall?.[0]).toMatchObject({ tradition: "jyotish" });
  });

  it("keeps Lá đọc sâu and links to the overview", async () => {
    renderPage("/insights/synthesis?tradition=western");
    expect(await screen.findByRole("link", { name: "Xem bản đọc tổng quan" })).toHaveAttribute("href", "/insights/overview?tradition=western");
    expect(screen.getByText("Lá đọc sâu · Tây phương")).toBeInTheDocument();
  });

  it("gives the overview a page heading and a retry when the chart fails", async () => {
    vi.mocked(getBirthSupplement).mockRejectedValue(new Error("offline"));
    vi.mocked(getInsightOverview).mockRejectedValue(new Error("offline"));
    renderPage("/insights/overview?tradition=western");

    expect(await screen.findByRole("button", { name: "Thử lại" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 1, name: "Bản đọc tổng quan · Tây phương" })).toBeInTheDocument();
  });

  it("shows the birth-time line and no house note for an approximate time", async () => {
    vi.mocked(getBirthSupplement).mockRejectedValue(new Error("offline"));
    const ready = await vi.mocked(getInsightOverview).getMockImplementation()?.({ tradition: "western" } as never);
    vi.mocked(getInsightOverview).mockResolvedValue({ ...ready, time_precision: "unknown", houses_available: false } as never);
    renderPage("/insights/overview?tradition=western");

    expect(await screen.findByText(/Bạn biết giờ sinh chính xác/)).toBeInTheDocument();
    expect(screen.queryByText(/nhà và góc chiếu/)).not.toBeInTheDocument();
  });

  it("keeps the retry on a single claim page when the chart fails", async () => {
    vi.mocked(getBirthSupplement).mockRejectedValue(new Error("offline"));
    vi.mocked(getInsightOverview).mockRejectedValue(new Error("offline"));
    renderPage("/insights/moon-sign?tradition=western");

    expect(await screen.findByRole("button", { name: "Thử lại" })).toBeInTheDocument();
    expect(screen.queryByText("Lớp này chưa có trong chart.")).not.toBeInTheDocument();
  });

  it("shows the locked recovery on a single claim page", async () => {
    vi.mocked(getBirthSupplement).mockRejectedValue(new Error("offline"));
    vi.mocked(getInsightOverview).mockResolvedValue({ status: "locked", required_fields: ["birth_time"], houses_available: false, time_precision: "unknown", bodies: [], reading: null } as never);
    renderPage("/insights/moon-sign?tradition=western");

    expect(await screen.findByRole("button", { name: "Thử tải lại bản đọc" })).toBeInTheDocument();
    expect(screen.queryByText("Lớp này chưa có trong chart.")).not.toBeInTheDocument();
  });
});
