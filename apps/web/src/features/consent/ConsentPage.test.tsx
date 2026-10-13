import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { OPENAI_ABUSE_RETENTION_NOTICE } from "../../shared/config/externalRewriteDisclosure";
import { ConsentPage } from "./ConsentPage";

describe("ConsentPage privacy details", () => {
  function renderPrivacyPage() {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={["/privacy"]}>
          <ConsentPage />
        </MemoryRouter>
      </QueryClientProvider>,
    );
  }

  it("gives network users a visible link to the corresponding source", () => {
    renderPrivacyPage();

    expect(screen.getByRole("link", { name: "Xem mã nguồn tương ứng" })).toHaveAttribute(
      "href",
      "https://github.com/honghanh153-creator/la-lanh",
    );
    expect(screen.getByRole("link", { name: "Đọc giấy phép" })).toHaveAttribute(
      "href",
      "https://github.com/honghanh153-creator/la-lanh/blob/main/LICENSE",
    );
    expect(screen.getByText(/được cung cấp không kèm bảo hành/i)).toBeInTheDocument();
  });

  it("states the full OpenAI abuse-monitoring retention exceptions", () => {
    renderPrivacyPage();

    const notice = screen.getByText((_, element) => element?.tagName === "P" && (element.textContent ?? "").includes(OPENAI_ABUSE_RETENTION_NOTICE));
    expect(notice).toHaveTextContent("tối đa 30 ngày");
    expect(notice).toHaveTextContent("khi pháp luật yêu cầu");
    expect(notice).toHaveTextContent("bảo vệ dịch vụ hay bên thứ ba khỏi tổn hại");
  });

  it("names the beta processors and hosting regions", () => {
    renderPrivacyPage();

    expect(screen.getByText(/dữ liệu được truyền từ Việt Nam/i)).toBeInTheDocument();
    expect(screen.getByText(/máy chủ Hetzner tại Đức/i)).toBeInTheDocument();
    expect(screen.getByText(/Supabase tại Frankfurt, Đức/i)).toBeInTheDocument();
  });

  it("discloses provider profile processing, actual Radar storage and unverified backup erasure", () => {
    renderPrivacyPage();
    expect(screen.getByText(/Google và Supabase xử lý mã định danh, email/i)).toBeInTheDocument();
    expect(screen.getByText(/Nhóm quan hệ và giọng đọc là các trường vận hành không mã hoá riêng/i)).toBeInTheDocument();
    expect(screen.getByText(/chưa xác minh đầy đủ thời hạn xoá trong backup/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "honghanh153@gmail.com" })).toHaveAttribute("href", "mailto:honghanh153@gmail.com");
  });
});
