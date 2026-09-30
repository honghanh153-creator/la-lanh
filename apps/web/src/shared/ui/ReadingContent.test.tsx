import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { ReadingContent as ReadingContentModel } from "../api/client";
import { ReadingContent } from "./ReadingContent";

const content = {
  revision_id: "00000000-0000-4000-8000-000000000010",
  source: "deterministic",
  mode: "full_synthesis",
  purpose: "daily_note",
  tradition: "western",
  precision: "exact",
  sections: {
    hook: "Một phần muốn tiến, phần kia muốn chắc.",
    thesis: "Hai nhịp đang cần được thương lượng.",
    manifestation: "Bạn có thể sửa đi sửa lại một tin nhắn.",
    transit: null,
    micro_action: "Viết câu chính trước.",
  },
  evidence: {
    title: "Căn cứ trong lá số",
    claims: ["Mặt Trời ở Song Tử"],
    framework_disclosure: "Khung diễn giải, không phải phán quyết.",
  },
  disclaimer: "Lá gợi một góc nhìn — quyền quyết định vẫn ở bạn.",
  created_at: "2026-09-12T00:00:00Z",
} satisfies ReadingContentModel;

describe("ReadingContent", () => {
  it("hides current activation for a natal-only reading", () => {
    render(<ReadingContent content={content} />);
    expect(screen.queryByRole("heading", { name: "Vì sao hôm nay thấy rõ hơn?" })).not.toBeInTheDocument();
    expect(screen.getByRole("note", { name: "Lưu ý về bản đọc" })).toHaveTextContent(
      content.disclaimer,
    );
  });

  it("does not invent an action block when the reading has no experiment", () => {
    render(<ReadingContent content={content} />);

    expect(screen.queryByRole("heading", { name: "Đối chiếu với hôm nay" })).not.toBeInTheDocument();
    expect(screen.queryByText(content.sections.micro_action)).not.toBeInTheDocument();
  });

  it("keeps a date-only Vibe concise instead of showing speculative scenes", () => {
    const vibe = { ...content, mode: "vibe_fallback" as const, precision: "unknown" as const };
    render(<ReadingContent compact content={vibe} />);

    expect(screen.getByRole("heading", { name: vibe.sections.hook })).toBeInTheDocument();
    expect(screen.queryByText(vibe.sections.manifestation)).not.toBeInTheDocument();
    expect(screen.queryByText(vibe.sections.micro_action)).not.toBeInTheDocument();
  });

  it("explains the current activation once when transit is present", () => {
    const withTransit = {
      ...content,
      sections: {
        ...content.sections,
        transit: "Nhịp hiện tại đang tăng dần; quan sát điều gì lặp lại.",
      },
    } satisfies ReadingContentModel;
    render(<ReadingContent content={withTransit} />);

    expect(screen.getByRole("heading", { name: "Vì sao hôm nay thấy rõ hơn?" })).toBeInTheDocument();
    expect(screen.getByText(withTransit.sections.transit)).toBeInTheDocument();
  });

  it("renders server-owned action cues and requires explicit replace confirmation", async () => {
    const user = userEvent.setup();
    const onChoose = vi.fn();
    const onReflect = vi.fn();
    const withExperiment = {
      ...content,
      experiment: {
        action_key: "a".repeat(64),
        action: "Đặt điện thoại xuống trong một phút.",
        observation: "Để ý xem đầu óc có bớt bị kéo đi không.",
        permission: "Bạn có thể dừng bất cứ lúc nào.",
      },
    } satisfies ReadingContentModel;
    const held = {
      id: "00000000-0000-4000-8000-000000000022",
      version: 2,
      daily_note_id: "00000000-0000-4000-8000-000000000001",
      revision_id: content.revision_id,
      state: "chosen" as const,
      background_lens: "auto" as const,
      action_key: "b".repeat(64),
      action: "Việc cũ.",
      observation: "Quan sát cũ.",
      permission: "Dừng nếu không hợp.",
      outcome: null,
      created_at: "2026-09-16T00:00:00Z",
      updated_at: "2026-09-16T00:00:00Z",
      expires_at: "2026-09-17T00:00:00Z",
      reflected_at: null,
    } satisfies import("../api/client").DailyExperiment;

    render(<ReadingContent content={withExperiment} currentExperiment={held} onChoose={onChoose} onReflect={onReflect} />);
    expect(screen.getByText("Để ý xem đầu óc có bớt bị kéo đi không.")).toBeInTheDocument();
    expect(screen.getByText("Bạn có thể dừng bất cứ lúc nào.")).toBeInTheDocument();
    expect(screen.getByText("Việc đang giữ")).toBeInTheDocument();
    expect(screen.getByText("Việc cũ.")).toBeInTheDocument();
    expect(screen.getByText("Quan sát cũ.")).toBeInTheDocument();
    expect(screen.getByText("Dừng nếu không hợp.")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Thay việc đang giữ" }));
    expect(screen.getByText(/Việc đang giữ sẽ được thay thế/)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Xác nhận thay việc đang giữ" }));
    expect(onChoose).toHaveBeenCalledOnce();

    const sameAction = { ...held, action_key: withExperiment.experiment.action_key };
    render(<ReadingContent content={withExperiment} currentExperiment={sameAction} onReflect={onReflect} />);
    await user.click(screen.getByRole("button", { name: "Mở phần nhìn lại" }));
    expect(screen.getByRole("button", { name: "Không hợp lúc này" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Không hợp lúc này" }));
    expect(onReflect).toHaveBeenCalledWith("not_for_now");
  });

  it("requires a new replace confirmation when the held experiment changes", async () => {
    const user = userEvent.setup();
    const onChoose = vi.fn();
    const withExperiment = {
      ...content,
      experiment: {
        action_key: "a".repeat(64),
        action: "Đặt điện thoại xuống trong một phút.",
        observation: "Để ý xem đầu óc có bớt bị kéo đi không.",
        permission: "Bạn có thể dừng bất cứ lúc nào.",
      },
    } satisfies ReadingContentModel;
    const held = {
      id: "00000000-0000-4000-8000-000000000022",
      version: 2,
      daily_note_id: "00000000-0000-4000-8000-000000000001",
      revision_id: content.revision_id,
      state: "chosen" as const,
      background_lens: "auto" as const,
      action_key: "b".repeat(64),
      action: "Việc cũ.",
      observation: "Quan sát cũ.",
      permission: "Dừng nếu không hợp.",
      outcome: null,
      created_at: "2026-09-16T00:00:00Z",
      updated_at: "2026-09-16T00:00:00Z",
      expires_at: "2026-09-17T00:00:00Z",
      reflected_at: null,
    } satisfies import("../api/client").DailyExperiment;
    const view = render(
      <ReadingContent content={withExperiment} currentExperiment={held} onChoose={onChoose} />,
    );

    await user.click(screen.getByRole("button", { name: "Thay việc đang giữ" }));
    expect(screen.getByRole("button", { name: "Xác nhận thay việc đang giữ" })).toBeInTheDocument();

    view.rerender(
      <ReadingContent
        content={withExperiment}
        currentExperiment={{
          ...held,
          id: "00000000-0000-4000-8000-000000000023",
          version: 3,
        }}
        onChoose={onChoose}
      />,
    );

    expect(screen.getByRole("button", { name: "Thay việc đang giữ" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Thay việc đang giữ" }));
    expect(onChoose).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Xác nhận thay việc đang giữ" })).toBeInTheDocument();
  });

  it("does not offer undo after an experiment has been reflected", () => {
    const withExperiment = {
      ...content,
      experiment: {
        action_key: "a".repeat(64),
        action: "Đặt điện thoại xuống trong một phút.",
        observation: "Để ý xem đầu óc có bớt bị kéo đi không.",
        permission: "Bạn có thể dừng bất cứ lúc nào.",
      },
    } satisfies ReadingContentModel;
    const reflected = {
      id: "00000000-0000-4000-8000-000000000024",
      version: 2,
      daily_note_id: "00000000-0000-4000-8000-000000000001",
      revision_id: content.revision_id,
      state: "reflected" as const,
      background_lens: "auto" as const,
      action_key: withExperiment.experiment.action_key,
      action: withExperiment.experiment.action,
      observation: withExperiment.experiment.observation,
      permission: withExperiment.experiment.permission,
      outcome: "helpful" as const,
      created_at: "2026-09-16T00:00:00Z",
      updated_at: "2026-09-16T01:00:00Z",
      expires_at: "2026-09-17T00:00:00Z",
      reflected_at: "2026-09-16T01:00:00Z",
    } satisfies import("../api/client").DailyExperiment;

    render(<ReadingContent content={withExperiment} currentExperiment={reflected} />);

    expect(screen.getByRole("status")).toHaveTextContent("Đã nhìn lại");
    expect(screen.queryByRole("button", { name: "Bỏ giữ việc này" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Mở phần nhìn lại" })).not.toBeInTheDocument();
  });
});
