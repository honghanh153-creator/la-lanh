import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { ReadingProjection } from "../api/client";
import { ReadingUpdateGift } from "./ReadingUpdateGift";

const update = {
  revision_id: "00000000-0000-4000-8000-000000000011",
  message: "Có một bản đọc mới đang chờ bạn",
  content: {
    revision_id: "00000000-0000-4000-8000-000000000011",
    source: "deterministic",
    mode: "full_synthesis",
    purpose: "daily_note",
    tradition: "western",
    precision: "exact",
    sections: {
      hook: "Hook",
      thesis: "Thesis",
      manifestation: "Manifestation",
      transit: null,
      micro_action: "Action",
    },
    evidence: { title: "Căn cứ", claims: [], framework_disclosure: "Disclosure" },
    disclaimer: "Disclaimer",
    created_at: "2026-09-12T00:00:00Z",
  },
} satisfies NonNullable<ReadingProjection["available_update"]>;

describe("ReadingUpdateGift", () => {
  it("explains a real depth upgrade", () => {
    render(
      <ReadingUpdateGift
        activeMode="vibe_fallback"
        onActivate={vi.fn()}
        pending={false}
        update={update}
      />,
    );

    expect(screen.getByRole("heading", { name: "Note này có một bản đủ lớp" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Mở bản đủ lớp/ })).toBeInTheDocument();
  });

  it("does not pretend a content refresh came from new birth data", () => {
    render(
      <ReadingUpdateGift
        activeMode="full_synthesis"
        onActivate={vi.fn()}
        pending={false}
        update={update}
      />,
    );

    expect(screen.getByRole("heading", { name: "Có một bản đọc mới hơn" })).toBeInTheDocument();
    expect(screen.queryByText("Giờ sinh đã vào chart")).not.toBeInTheDocument();
  });
});
