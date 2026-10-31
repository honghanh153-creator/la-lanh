import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import type { RadarResult } from "../../shared/api/client";
import { RadarResultView } from "./RadarContinuePage";

const closing = "Kết quả để tham khảo, cách hai bạn đối xử với nhau mới là điều quyết định.";

// radar-readable-v2 (29/10/2026): tier, areas, short sections and one "Xem thêm" layer.
const readable: RadarResult = {
  request_id: "request-2",
  recipient_label: "Mèo",
  mode: "private_check",
  version: "radar-result-v2",
  headline: "Hai bạn có thể nói chuyện hàng giờ mà không thấy mệt.",
  summary: "Hai bạn có khá nhiều điểm dễ đi cùng, nổi bật là cách nói chuyện.",
  pair_signature: {
    kicker: "Hợp chuyện",
    headline: "Hai bạn có thể nói chuyện hàng giờ mà không thấy mệt.",
    summary: "Hai bạn có khá nhiều điểm dễ đi cùng, nổi bật là cách nói chuyện.",
    tier: { key: "easy", label: "Hợp chuyện" },
    areas: [
      { key: "talk", label: "Nói chuyện", level: "good", level_label: "hợp", note: "Cách hai bạn nói và nghe dễ khớp nhau." },
      { key: "fun", label: "Chơi chung", level: "balanced", level_label: "cân bằng", note: "Sự hào hứng giữa hai bạn có lúc lên, có lúc xuống." },
      { key: "support", label: "Hỗ trợ nhau", level: "watch", level_label: "cần để ý", note: "Hai bạn có thể cần được quan tâm theo cách khác nhau." },
    ],
    themes: [{ key: "communication", label: "cách nói chuyện" }],
  },
  compatibility_map: [],
  sections: [
    {
      key: "fit", layer: "main", label: "Điều trôi chảy", title: "",
      body: "Hai bạn bắt ý nhau nhanh và hay đùa cùng một kiểu.",
      topics: [], depth: "focused", highlights: [], scene: null, perspectives: [], observation: null, evidence: [],
    },
    {
      key: "friction", layer: "main", label: "Điều cần để ý", title: "",
      body: "Khi một người cần ở một mình, người còn lại dễ hiểu thành bị bỏ rơi.",
      topics: [], depth: "focused", highlights: [], scene: null, perspectives: [], observation: null, evidence: [],
    },
    {
      key: "check", layer: "main", label: "Một gợi ý", title: "",
      body: "Hẹn với nhau một câu báo hiệu khi ai đó cần ở một mình.",
      question: "Khi mệt, cậu muốn được hỏi han hay được để yên?",
      topics: [], depth: "focused", highlights: [], scene: null, perspectives: [], observation: null, evidence: [],
    },
    {
      key: "why", layer: "more", label: "Vì sao ra kết quả này?", title: "Những điểm chạm Lá đã dùng",
      body: "Mỗi dòng là một điểm chạm giữa hai lá số.",
      factors: [{
        key: "communication", label: "Cách nói chuyện", level: "good", level_label: "hợp",
        technical_note: "Sao Thủy của bạn và Mặt Trăng của người kia, góc tam hợp.",
        evidence_ids: ["syn:mercury:trine:moon:1.20"],
      }],
      topics: [], depth: "focused", highlights: [], scene: null, perspectives: [], observation: null,
      evidence: [{
        evidence_id: "syn:mercury:trine:moon:1.20",
        source: "synastry",
        plain: "Sao Thủy của bạn tạo góc tam hợp với Mặt Trăng của người kia.",
        technical: { orb: 1.2 },
      }],
    },
    {
      key: "perspective", layer: "more", label: "Hai phía có thể thấy khác nhau", title: "Cùng một lần gặp",
      body: "Ở cạnh nhau, bạn có thể để ý nhiều tới chuyện trò hằng ngày.",
      topics: [], depth: "focused", highlights: [], scene: null, observation: null, evidence: [],
      perspectives: [{ key: "them", label: "Phía bên kia", title: "Điều nên hỏi thay vì đoán", body: "Thử hỏi nhẹ một câu." }],
    },
  ],
  dimensions: [],
  strongest_contacts: [],
  metadata: {
    knowledge_version: "relationship-corpus-v2-2026-09-17",
    renderer_version: "radar-readable-v2",
    gate_version: "conditional-reflection-v4",
    tier_calibration_version: "radar-tier-ref-v1",
    chart_config_version: "config",
    evidence_ids: ["syn:mercury:trine:moon:1.20"],
    concept_ids: [],
    voice: "straight_warm",
    voice_label: "Thẳng mà ấm",
  },
  disclaimer: closing,
};

describe("RadarResultView · radar-readable-v2", () => {
  it("leads with the named tier and reason, without any 0-100 number", () => {
    const { container } = render(<MemoryRouter><RadarResultView ownerView result={readable} /></MemoryRouter>);

    expect(screen.getByText("Hợp chuyện")).toBeInTheDocument();
    expect(screen.getByText(readable.summary)).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 1, name: readable.headline })).toBeInTheDocument();
    expect(container.textContent).not.toMatch(/\/100|Lực cấn|Bắt sóng/);
    const areas = screen.getByRole("list", { name: "Từng mảng" });
    expect(within(areas).getAllByRole("listitem")).toHaveLength(3);
    expect(within(areas).getByText("cần để ý")).toBeInTheDocument();
  });

  it("shows short main sections and keeps chart terms behind one closed Xem thêm", () => {
    const { container } = render(<MemoryRouter><RadarResultView ownerView result={readable} /></MemoryRouter>);

    expect(screen.getByRole("heading", { level: 2, name: "Điều trôi chảy" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 2, name: "Điều cần để ý" })).toBeInTheDocument();
    expect(screen.getByText(/Thử hỏi: “Khi mệt, cậu muốn được hỏi han hay được để yên\?”/)).toBeInTheDocument();
    const more = container.querySelectorAll("details.radar-more");
    expect(more).toHaveLength(1);
    expect(more[0]).not.toHaveAttribute("open");
    expect(within(more[0] as HTMLElement).getByText(/Sao Thủy của bạn và Mặt Trăng/)).toBeInTheDocument();
    const outside = Array.from(container.querySelectorAll(".radar-signature, .radar-areas, .radar-readable"))
      .map((node) => node.textContent ?? "")
      .join(" ");
    expect(outside).not.toMatch(/Sao Thủy|Mặt Trăng|tam hợp|chart|contact/);
    expect(screen.getAllByText(closing)).toHaveLength(1);
  });

  it("renders no friction card for a calm pair, and the number only when the owner turns it on", () => {
    const calm: RadarResult = {
      ...readable,
      pair_signature: { ...readable.pair_signature!, tier: { key: "easy", label: "Hợp chuyện", score: 72 } },
      sections: readable.sections!.filter((section) => section.key !== "friction"),
    };
    render(<MemoryRouter><RadarResultView result={calm} /></MemoryRouter>);

    expect(screen.queryByRole("heading", { level: 2, name: "Điều cần để ý" })).not.toBeInTheDocument();
    expect(screen.getByText("· 72")).toBeInTheDocument();
  });
});
