import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it } from "vitest";

import { MatchingLandingPage } from "./MatchingLandingPage";
import { MATCHING_INTRO_STORAGE_KEY } from "../../shared/storage/matchingIntroExposure";

describe("MatchingLandingPage", () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
  });

  it("opens with a curiosity-led first visit and the real setup route", () => {
    render(<MemoryRouter><MatchingLandingPage /></MemoryRouter>);

    expect(screen.getByRole("heading", { name: "Có kiểu người nào cứ làm bạn nghĩ mãi?" })).toBeInTheDocument();
    expect(screen.getByText("Vòng Lá bắt đầu bằng điều bạn thật sự muốn. Khi vòng ghép mở, chart sẽ giúp gợi tối đa năm người có một lý do đáng thử nói chuyện.")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Một lời giới thiệu có chiều sâu trước câu “hi”." })).toBeInTheDocument();
    expect(screen.getByText("Chờ vòng ghép mở")).toBeInTheDocument();
    expect(screen.getByText("Chỉ lưu thành phố và lựa chọn bạn chủ động nhập; bản hiện tại chưa phát hồ sơ hay request cho người khác.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Bật radar hợp gu" })).toHaveAttribute("href", "/vong-la/setup?start=profile");
    expect(screen.getByText("Bước đầu là đặt ranh giới · chưa vào pool cho tới khi bạn đồng ý.")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Check hai đứa/i })).not.toBeInTheDocument();
  });

  it.each([
    [
      1,
      "Không chỉ là hợp cung",
      "Bắt sóng ở đâu? Dễ cấn ở chỗ nào?",
      "Bạn sẽ thấy nhịp giao tiếp dễ vào, chỗ hai người có thể lệch sóng và ranh giới nên giữ — trước khi quyết định mở lời.",
      "Tạo hồ sơ hợp gu",
      "Bạn đặt intent và ranh giới trước · Lá chưa ghép ai ở bước này.",
    ],
    [
      2,
      "Đừng swipe thêm vội",
      "Thử một vòng có lý do.",
      "Không feed vô tận, không điểm hợp công khai. Bắt đầu bằng một hồ sơ có chủ đích; năm gợi ý chỉ mở khi các chốt an toàn đã sẵn sàng.",
      "Vào trạm ghép",
      "Không GPS · chưa gửi request hay tự nhắn ai ở bước này.",
    ],
  ])("shows the next message after %i completed visit(s)", (visit, eyebrow, heading, detail, cta, note) => {
    localStorage.setItem(MATCHING_INTRO_STORAGE_KEY, JSON.stringify({ converted: false, visit }));

    render(<MemoryRouter><MatchingLandingPage /></MemoryRouter>);

    expect(screen.getByText(eyebrow)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: heading })).toBeInTheDocument();
    expect(screen.getByText(detail)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: cta })).toHaveAttribute("href", "/vong-la/setup?start=profile");
    expect(screen.getByText(note)).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Check hai đứa/i })).not.toBeInTheDocument();
  });
});
