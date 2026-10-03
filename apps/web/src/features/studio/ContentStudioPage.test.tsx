import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";

import { ContentStudioPage } from "./ContentStudioPage";

afterEach(() => vi.restoreAllMocks());

const WORKSPACE = {
  source: "bundled-baseline",
  channel: { active_revision_id: null, generation: 0, updated_at: "2026-09-30T00:00:00Z" },
  active_revision: null,
  payload: {
    planets: {
      moon: {
        drive: "được an toàn trước khi mở lòng",
        stress: "nuốt nhu cầu xuống rồi mong người khác tự hiểu",
        action: "viết riêng điều mình cảm và điều mình cần",
      },
    },
    signs: {
      pisces: {
        style: "mềm và bắt bầu không khí rất nhanh",
        stress: "tự nối thêm ý nghĩa khi chưa đủ dữ kiện",
        manifestation: "khi một người trả lời ngắn hơn thường lệ",
        practices: ["hỏi một câu rõ", "tách điều biết khỏi điều đoán", "gọi tên cảm xúc"],
        hooks: ["Một tin nhắn ngắn đang kéo theo nhiều suy nghĩ.", "Hỏi trước khi đoán.", "Chưa cần kết luận."],
      },
    },
    houses: { "1": { arena: "cách bạn xuất hiện", manifestation: "khi vào một nhóm mới" } },
    aspects: { conjunction: { bridge: "được kích hoạt cùng lúc", watch: "phản ứng quá nhanh" } },
  },
  summary: { planets: 1, signs: 1, houses: 1, aspects: 1 },
  revisions: [],
  events: [],
  rewrite_candidates: [
    {
      id: "64fb6851-4759-4d9b-bbcd-070aec02ca43",
      surface: "daily_home",
      status: "pending",
      last_result: null,
      candidate_variant: "luna-v1",
      provider: "openai",
      model: "gpt-6-luna",
      prompt_version: "daily-v1",
      schema_version: "daily-v1",
      gate_version: "daily-gate-v1",
      gate_receipt_id: null,
      input_tokens: null,
      output_tokens: null,
      attempt_count: 0,
      created_at: "2026-10-03T00:00:00Z",
      updated_at: "2026-10-03T00:00:00Z",
    },
  ],
  rewrite_surfaces: [
    {
      surface: "daily_home",
      fields: ["headline", "scene", "advice"],
      schema_version: "daily-v1",
      gate_version: "daily-gate-v1",
      forbidden_claims: ["fate"],
      privacy_manifest: "field names only; request and output values stay encrypted",
    },
  ],
};

it("keeps the token in the tab flow and opens the review workspace", async () => {
  const user = userEvent.setup();
  const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify(WORKSPACE), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    }),
  );
  render(<ContentStudioPage />);

  await user.type(
    screen.getByLabelText("Token truy cập"),
    "la-lanh-local-studio-review-2026-09-30",
  );
  await user.click(screen.getByRole("button", { name: "Mở Content Studio" }));

  expect(await screen.findByRole("heading", { name: "Daily content matrix" })).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Đọc riêng mảnh này" })).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Hàng chờ nội dung cá nhân hóa" })).toBeInTheDocument();
  expect(screen.getByText("daily_home")).toBeInTheDocument();
  expect(screen.getByText("gpt-6-luna · daily-v1")).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: /gọi model/i })).not.toBeInTheDocument();
  expect(screen.queryByText(/private-owner/i)).not.toBeInTheDocument();
  expect(fetchSpy).toHaveBeenCalledWith(
    "/v1/studio/workspace",
    expect.objectContaining({
      credentials: "omit",
      headers: expect.objectContaining({
        Authorization: "Bearer la-lanh-local-studio-review-2026-09-30",
      }),
    }),
  );

  await user.click(screen.getByRole("button", { name: "Khóa Studio" }));
  expect(screen.getByRole("heading", { name: "Review nội dung trước khi người dùng thấy." })).toBeInTheDocument();
});
