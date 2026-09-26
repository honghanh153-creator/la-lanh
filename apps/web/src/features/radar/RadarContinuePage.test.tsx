import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import type { RadarResult } from "../../shared/api/client";
import { RadarResultView } from "./RadarContinuePage";

const result: RadarResult = {
  request_id: "request-1",
  recipient_label: "Mèo",
  version: "radar-result-v2",
  headline: "Cách nói chuyện kéo hai bạn lại gần - và cũng dễ làm mọi thứ nóng lên.",
  summary: "Chỗ dễ vào là cách nói và hiểu nhau; chỗ cần làm rõ là nhịp cảm xúc.",
  pair_signature: {
    kicker: "Hút rõ · cấn cũng rõ",
    headline: "Cách nói chuyện kéo hai bạn lại gần - và cũng dễ làm mọi thứ nóng lên.",
    summary: "Chỗ dễ vào là cách nói và hiểu nhau; chỗ cần làm rõ là nhịp cảm xúc.",
  },
  compatibility_map: [
    {
      key: "resonance",
      label: "Bắt sóng",
      value: 82,
      meaning: "Dễ làm nhau chú ý.",
      evidence: [{
        evidence_id: "syn:venus:trine:mars:0.70",
        source: "synastry",
        plain: "Venus của bạn tạo góc tam hợp với Mars của người kia.",
        technical: { orb: 0.7 },
      }],
    },
    { key: "coordination", label: "Dễ phối hợp", value: 64, meaning: "Có đường để làm cùng." },
    { key: "friction", label: "Lực cấn", value: 76, meaning: "Khác biệt khó bị lờ đi." },
  ],
  sections: [
    {
      key: "fit",
      label: "Điểm hợp",
      title: "Nói đúng nhịp là bắt được ý khá nhanh",
      body: "Cách một người diễn đạt có thể chạm khá nhanh vào cách người kia tiếp nhận.",
      topics: ["cách nói và hiểu nhau", "nhịp cảm xúc"],
      depth: "layered",
      highlights: [{
        key: "fit:communication:primary",
        label: "Tín hiệu chính",
        title: "Một câu nói có thể đi xa hơn phần chữ",
        body: "Hai người dễ nghe cả điều nằm sau câu chữ khi cùng chậm lại một nhịp.",
        evidence_ids: ["syn:mercury:trine:moon:1.20"],
      }],
      scene: {
        label: "Cảnh dễ gặp",
        title: "Một đoạn chat đang trôi, rồi một câu ngắn làm nhịp đổi",
        body: "Hai người có thể bắt được ý khá nhanh nhưng cũng dễ phản ứng với giọng điệu.",
      },
      perspectives: [],
      observation: null,
      evidence: [{
        evidence_id: "syn:mercury:trine:moon:1.20",
        source: "synastry",
        plain: "Mercury của bạn tạo góc tam hợp với Mặt Trăng của người kia.",
        technical: { orb: 1.2 },
      }, {
        evidence_id: "syn:moon:sextile:mercury:0.90",
        source: "synastry",
        plain: "Mặt Trăng của bạn tạo góc lục hợp với Mercury của người kia.",
        technical: { orb: 0.9 },
      }],
    },
    {
      key: "friction",
      label: "Điểm dễ cấn",
      title: "Một câu thiếu ngữ cảnh cũng đủ làm lệch sóng",
      body: "Khác biệt khó bị lờ đi khi hai người đang phản ứng nhanh.",
      topics: ["cách nói và hiểu nhau"],
      depth: "focused",
      highlights: [],
      scene: null,
      perspectives: [],
      observation: null,
      evidence: [{
        evidence_id: "syn:mercury:square:saturn:0.80",
        source: "synastry",
        plain: "Mercury của bạn tạo góc vuông với Saturn của người kia.",
        technical: { orb: 0.8 },
      }],
    },
    {
      key: "perspective",
      label: "Hai phía có thể thấy khác nhau",
      title: "Cùng một kết nối, chưa chắc cùng một trải nghiệm",
      body: "Mỗi phía có thể đặt trọng lượng vào một vùng khác nhau.",
      topics: ["vùng riêng tư"],
      depth: "layered",
      highlights: [],
      scene: null,
      perspectives: [
        { key: "you", label: "Bạn có thể tạo tín hiệu này", title: "Bạn chạm vùng riêng tư", body: "Người kia có thể cần thêm thời gian để gọi tên." },
        { key: "them", label: "Người kia có thể tạo tín hiệu này", title: "Họ chạm vùng vui và flirt", body: "Bạn có thể thấy tương tác này nổi bật hơn." },
        { key: "shared", label: "Nhịp chung khi ở cạnh nhau", title: "Hai người dễ tạo một thế giới riêng", body: "Đây là pattern chung, không phải tính cách riêng." },
      ],
      observation: { label: "Điều đáng đối chiếu", title: "Đừng đo hộ phía còn lại", body: "Hỏi trải nghiệm thật sẽ chính xác hơn suy từ chart." },
      evidence: [{
        evidence_id: "overlay:a:mercury:b:h12",
        source: "house_overlay",
        plain: "Mercury của A nằm trong nhà 12 của B.",
        technical: { house: 12 },
      }],
    },
    {
      key: "check",
      label: "Đem ra đời thật",
      title: "Thử một lần nói rõ, đừng thử lòng",
      body: "Hỏi một câu có thể trả lời thẳng rồi nhìn vào phản hồi thật.",
      topics: ["giao tiếp"],
      depth: "focused",
      highlights: [],
      scene: null,
      perspectives: [],
      observation: { label: "Một lần thử là đủ", title: "Nhìn cách hai người quay lại", body: "Đừng chỉ đo bằng lúc chemistry đang cao." },
      evidence: [{
        evidence_id: "syn:mercury:trine:moon:1.20",
        source: "synastry",
        plain: "Mercury của bạn tạo góc tam hợp với Mặt Trăng của người kia.",
        technical: { orb: 1.2 },
      }],
    },
  ],
  dimensions: [],
  strongest_contacts: [],
  disclaimer: "Ba chỉ báo là bản đồ tương tác từ hai chart, không phải xác suất thành công.",
};

describe("RadarResultView", () => {
  it("renders pair signature, independent indicators and evidence disclosure", () => {
    render(<MemoryRouter><RadarResultView ownerView result={result} /></MemoryRouter>);

    expect(screen.getByText("Bạn × Mèo")).toBeInTheDocument();
    expect(screen.getByText("Hút rõ · cấn cũng rõ")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Ba tín hiệu, đọc riêng từng cái." })).toBeInTheDocument();
    expect(screen.getByText("Bắt sóng")).toBeInTheDocument();
    expect(screen.getByText("Dễ phối hợp")).toBeInTheDocument();
    expect(screen.getByText("Lực cấn")).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: "Mục lục bản đọc" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /01 điểm hợp/i })).toBeInTheDocument();
    expect(screen.getByText("Một câu nói có thể đi xa hơn phần chữ")).toBeInTheDocument();
    expect(screen.getByText("Bạn có thể tạo tín hiệu này")).toBeInTheDocument();
    expect(screen.getByText("Vì sao có con số này?")).toBeInTheDocument();
    expect(screen.getAllByText("Vì sao Lá đọc vậy?")).toHaveLength(4);
    expect(screen.getAllByText("Giữa hai chart").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Mercury của bạn tạo góc tam hợp với Mặt Trăng của người kia.").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Mặt Trăng của bạn tạo góc lục hợp với Mercury của người kia.")).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: "Tiến độ Radar" })).toBeInTheDocument();
    expect(screen.getByText("Bản đọc").closest('[aria-current="step"]')).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Check thêm một người" })).toHaveAttribute("href", "/radar/start");
    expect(screen.getByRole("link", { name: "Xem các lần check" })).toHaveAttribute("href", "/radar/start#radar-history");
    expect(screen.getByRole("navigation", { name: "Điều hướng chính" })).toBeInTheDocument();
    expect(document.querySelector("#radar-chapter-fit")).toHaveAttribute("open");
    expect(document.querySelector("#radar-chapter-friction")).not.toHaveAttribute("open");
    fireEvent.click(document.querySelector("#radar-chapter-friction > summary")!);
    expect(document.querySelector("#radar-chapter-friction")).toHaveAttribute("open");
    expect(screen.queryByText(/xác suất thành công/i)).toBeInTheDocument();
  });

  it("keeps rendering stored v2 results that do not have dossier fields", () => {
    const legacyResult: RadarResult = {
      ...result,
      sections: result.sections?.slice(0, 1).map((section) => ({
        key: section.key,
        label: section.label,
        title: section.title,
        body: section.body,
        evidence: section.evidence,
      })),
    };

    render(<MemoryRouter><RadarResultView result={legacyResult} /></MemoryRouter>);

    expect(screen.getByText("Nói đúng nhịp là bắt được ý khá nhanh")).toBeInTheDocument();
    expect(screen.getByText("Chart nào tạo ra điều này?")).toBeInTheDocument();
  });
});
