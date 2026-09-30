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
