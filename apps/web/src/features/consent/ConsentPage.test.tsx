import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

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

  it("names the beta processors and hosting regions", () => {
    renderPrivacyPage();

    expect(screen.getByText(/dữ liệu được truyền từ Việt Nam/i)).toBeInTheDocument();
    expect(screen.getByText(/máy chủ Hetzner tại Đức/i)).toBeInTheDocument();
    expect(screen.getByText(/Supabase tại Frankfurt, Đức/i)).toBeInTheDocument();
  });
});
