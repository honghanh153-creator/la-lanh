import { readFileSync } from "node:fs";
import { join } from "node:path";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { CRISIS_CHECK_DISCLOSURE } from "../../shared/config/crisisCheckDisclosure";
import { MOOD_LIGHTER_TASK_NOTE } from "../../shared/config/moodLighterTaskNote";
import { OPENAI_ABUSE_RETENTION_NOTICE, OPENAI_REWRITE_SCOPE_NOTICE } from "../../shared/config/externalRewriteDisclosure";
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

  it("shows the owner-approved crisis check sentence, word for word (15.11, \"D duyệt\")", () => {
    renderPrivacyPage();

    const note = screen.getByText(CRISIS_CHECK_DISCLOSURE);
    expect(note.tagName).toBe("P");
    expect(note.closest("details")).toBeNull();
    expect(note).toHaveTextContent("không được lưu lại và không gửi cho ai khác");
    expect(note).toHaveTextContent("có thể nhận nhầm hoặc bỏ sót");
    expect(note).not.toHaveTextContent(/mọi câu/i);

    const registry = JSON.parse(readFileSync(join(process.cwd(), "../api/app/domains/content/copy_registry.json"), "utf8")) as {
      entries: { id: string; category: string; text: string; status: string; approver?: string; date?: string }[];
    };
    const entry = registry.entries.find((item) => item.id === "privacy.crisis-check-disclosure");
    expect(entry).toMatchObject({ category: "privacy", status: "approved", approver: "owner", date: "2026-11-15", text: CRISIS_CHECK_DISCLOSURE });
  });

  it("shows the owner-approved mood sentence next to the note and mood retention text, word for word (17.11, item S)", () => {
    renderPrivacyPage();

    const note = screen.getByText(MOOD_LIGHTER_TASK_NOTE);
    expect(note.tagName).toBe("P");
    expect(note.closest("article")).toHaveTextContent("Lịch sử có thời hạn riêng");
    expect(note).toHaveTextContent("dành cho bạn");
    expect(note).not.toHaveTextContent("trên máy bạn");

    const registry = JSON.parse(readFileSync(join(process.cwd(), "../api/app/domains/content/copy_registry.json"), "utf8")) as {
      entries: { id: string; category: string; text: string; status: string; approver?: string; date?: string }[];
    };
    const entry = registry.entries.find((item) => item.id === "privacy.mood-lighter-task");
    expect(entry).toMatchObject({ category: "privacy", status: "approved", approver: "owner", date: "2026-11-17", text: MOOD_LIGHTER_TASK_NOTE });
    expect(MOOD_LIGHTER_TASK_NOTE).toBe("Mood bạn chọn cũng dùng để gợi ý việc nhỏ nhẹ hơn trong ngày, dành cho bạn.");
  });

  it("shows the owner-approved Hợp gu privacy text word for word (AM1, 20.11.2026)", () => {
    renderPrivacyPage();
    const registry = JSON.parse(readFileSync(join(process.cwd(), "../api/app/domains/content/copy_registry.json"), "utf8")) as {
      entries: { id: string; category: string; text: string; status: string; approver?: string; date?: string }[];
    };
    for (const id of ["privacy.radar.consent-invite", "privacy.radar.consent-recipient"]) {
      const entry = registry.entries.find((item) => item.id === id);
      expect(entry).toMatchObject({ category: "privacy", status: "approved", approver: "owner", date: "2026-11-20" });
      expect(screen.getByText(entry!.text)).toBeInTheDocument();
    }
    expect(document.body.textContent).not.toMatch(/[Cc]heck kín/);
  });

  // Owner AP2/AQ1 (21.11.2026): the self-attested check is retired, so its "enter someone else's
  // data" block is gone; the still-true storage sentences stay word for word; the weekly note is
  // the owner-approved sentence.
  it("drops the retired Hợp gu tick block and shows the owner-approved weekly note (AP2/AQ1)", () => {
    renderPrivacyPage();
    const registry = JSON.parse(readFileSync(join(process.cwd(), "../api/app/domains/content/copy_registry.json"), "utf8")) as {
      entries: { id: string; category: string; text: string; status: string; approver?: string; date?: string }[];
    };
    expect(screen.queryByText("Radar xem riêng")).not.toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/Việc bạn đánh dấu xác nhận|Chỉ nhập thông tin sinh của người khác/);
    expect(screen.getByText(/Hệ thống mã hoá tên gọi và kết quả trước khi lưu\./)).toBeInTheDocument();
    const weekly = registry.entries.find((item) => item.id === "privacy.radar.weekly.optin-help");
    expect(weekly).toMatchObject({ category: "privacy", status: "approved", approver: "owner", date: "2026-11-21" });
    expect(screen.getByText(weekly!.text)).toBeInTheDocument();
  });

  // Owner AT1 (21.11.2026): the card-link line, word for word, in its own block after "Hai bạn tuần này"
  // and before "Tải bản sao dữ liệu".
  it("shows the owner-approved card-link line in the Thẻ Hợp gu block (AT1)", () => {
    renderPrivacyPage();
    const registry = JSON.parse(readFileSync(join(process.cwd(), "../api/app/domains/content/copy_registry.json"), "utf8")) as {
      entries: { id: string; category: string; text: string; status: string; approver?: string; date?: string }[];
    };
    const card = registry.entries.find((item) => item.id === "privacy.radar.cards.privacy-page");
    expect(card).toMatchObject({ category: "privacy", status: "approved", approver: "owner", date: "2026-11-21" });
    const line = screen.getByText(card!.text);
    expect(line.closest("details")?.querySelector("summary")?.textContent).toBe("Thẻ Hợp gu");
    const summaries = [...document.querySelectorAll("details.consent-detail > summary")].map((node) => node.textContent);
    const at = summaries.indexOf("Thẻ Hợp gu");
    expect(summaries[at - 1]).toBe("Hai bạn tuần này");
    expect(summaries[at + 1]).toBe("Tải bản sao dữ liệu");
  });

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

  it("says automatic Daily notes show at most 24 hours, may be cleaned earlier, and other history 30 days", () => {
    renderPrivacyPage();

    const history = screen.getByText((_, element) => element?.tagName === "P" && (element.textContent ?? "").startsWith("Khi đồng ý, note ngày"));
    expect(history).toHaveTextContent("chỉ hiện tối đa 24 giờ từ lúc tạo, kèm mood của ngày đó");
    expect(history).toHaveTextContent("có thể được xoá sớm hơn");
    expect(history).not.toHaveTextContent("rồi được xoá");
    expect(history).toHaveTextContent("được giữ ẩn tới khi các mục đó hết hạn");
    expect(history).toHaveTextContent("Lịch sử khác giữ tối đa 30 ngày");
    expect(history).toHaveTextContent("Bấm Lưu để giữ một note lâu hơn");
  });

  it("says the AI rewrite gets only Lá's shared Daily wording, never direct chart facts", () => {
    renderPrivacyPage();

    const notice = screen.getByText((_, element) => element?.tagName === "P" && (element.textContent ?? "").includes(OPENAI_REWRITE_SCOPE_NOTICE));
    expect(notice).toHaveTextContent("Không gửi lá số");
    expect(notice).not.toHaveTextContent("nhãn chiêm tinh liên quan");
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
