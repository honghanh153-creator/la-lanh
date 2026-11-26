import { readFileSync } from "node:fs";
import { join } from "node:path";

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it, vi } from "vitest";

import type { ReadingContent as ReadingContentModel } from "../api/client";
import ultravioletStyles from "../styles/ultraviolet.css?raw";
import {
  FOLDED_ACTION_LABEL,
  READ_ONLY_TODAY,
  ReadingContent,
  SHOW_ACTION_AGAIN,
  SHOW_ALONE_ACTION,
  SHOW_PREVIOUS_ACTION,
} from "./ReadingContent";

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
  it("labels natal evidence as natal rather than a claim about today", () => {
    render(<ReadingContent content={{ ...content, purpose: "reading_detail" }} />);
    expect(screen.getByText("Bản đọc này dựa vào đâu?")).toBeVisible();
    expect(screen.queryByText("Vì sao hôm nay?")).not.toBeInTheDocument();
  });
  it("hides current activation for a natal-only reading", () => {
    render(<ReadingContent content={content} />);
    expect(screen.queryByText("Nhịp hiện tại đang tăng dần; quan sát điều gì lặp lại.")).not.toBeInTheDocument();
    expect(screen.getByRole("note", { name: "Lưu ý về bản đọc" })).toHaveTextContent(
      content.disclaimer,
    );
  });

  it("still shows the Daily action without a hold button when there is no experiment", () => {
    render(<ReadingContent content={{ ...content, mode: "limited", precision: "unknown" }} />);

    expect(screen.getByRole("heading", { name: "Thử một việc nhỏ" })).toBeInTheDocument();
    expect(screen.getByText(content.sections.micro_action)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Giữ để thử hôm nay" })).not.toBeInTheDocument();
  });

  it("shows the alone action in place of the one on screen, with a way back (#703)", async () => {
    const onSwitch = vi.fn();
    const action = { action: "Ghi ra giấy một câu bạn muốn nói, giữ cho riêng mình.", replaces: ["card" as const], experiment: null };
    const limited = { ...content, mode: "limited" as const, precision: "unknown" as const };
    const { rerender } = render(<ReadingContent alone={{ shown: false, onSwitch, action }} content={limited} />);

    expect(screen.getByText(content.sections.micro_action)).toBeInTheDocument();
    expect(screen.queryByText(action.action)).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: SHOW_ALONE_ACTION }));
    expect(onSwitch).toHaveBeenCalledTimes(1);

    rerender(
      <ReadingContent
        alone={{ shown: true, onSwitch, action }}
        content={{ ...limited, lighter_action: { action: "Uống một ly nước.", weight: "light" as const, experiment: null } }}
        lighter={{ shown: false, onSwitch: vi.fn() }}
      />,
    );
    expect(screen.getByText(action.action)).toBeInTheDocument();
    expect(screen.queryByText(content.sections.micro_action)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: SHOW_PREVIOUS_ACTION })).toBeInTheDocument();
    // Only the way back is offered while the alone action is on screen.
    expect(screen.queryByRole("button", { name: "Xem việc nhẹ hơn" })).not.toBeInTheDocument();
  });

  it("offers no alone button when the page passes none", () => {
    render(<ReadingContent content={content} />);
    expect(screen.queryByRole("button", { name: SHOW_ALONE_ACTION })).not.toBeInTheDocument();
  });

  it("shows the common line only when the server sends one (#703)", () => {
    const line = "Nhiều bạn cũng chần chừ trước khi nhắn lại.";
    const { rerender } = render(<ReadingContent content={{ ...content, common_line: line }} />);
    expect(screen.getByText(line)).toBeInTheDocument();
    rerender(<ReadingContent content={{ ...content, common_line: null }} />);
    expect(screen.queryByText(line)).not.toBeInTheDocument();
  });

  it("shows the lighter action in place of the card's own, with a way back (#627)", async () => {
    const onSwitch = vi.fn();
    const withLighter = {
      ...content,
      mode: "limited" as const,
      precision: "unknown" as const,
      lighter_action: { action: "Uống một ly nước rồi ngồi yên hai phút.", weight: "light" as const, experiment: null },
    };
    const { rerender } = render(<ReadingContent content={withLighter} lighter={{ shown: true, onSwitch }} />);

    expect(screen.getByText(withLighter.lighter_action.action)).toBeInTheDocument();
    expect(screen.queryByText(content.sections.micro_action)).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Xem việc ban đầu" }));
    expect(onSwitch).toHaveBeenCalledTimes(1);

    rerender(<ReadingContent content={withLighter} lighter={{ shown: false, onSwitch }} />);
    expect(screen.getByText(content.sections.micro_action)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Xem việc nhẹ hơn" })).toBeInTheDocument();

    // Without the switch (another mood) the lighter action never shows.
    rerender(<ReadingContent content={withLighter} />);
    expect(screen.getByText(content.sections.micro_action)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Xem việc/ })).not.toBeInTheDocument();
  });

  // #700: "Hôm nay chỉ muốn đọc" folds the small-action box to one line. Synthetic data only.
  describe("read-only today (#700)", () => {
    const cues = { observation: "Bạn thấy nhẹ hơn chưa?", permission: "Không hợp thì bỏ qua." };
    const experiment = { action_key: "d".repeat(64), action: "Viết câu chính trước.", ...cues };

    function Harness({ model }: { model: ReadingContentModel }) {
      const [readOnly, setReadOnly] = useState(false);
      return <ReadingContent content={model} readOnly={{ readOnly, onToggle: () => setReadOnly((value) => !value) }} />;
    }

    it.each([
      ["an action that can be kept", { ...content, experiment }],
      ["an action that cannot be kept", { ...content, mode: "limited" as const, precision: "unknown" as const }],
    ])("folds %s to one line and opens it again, keeping the focus on the button", async (_name, model) => {
      const user = userEvent.setup();
      render(<Harness model={model} />);
      expect(screen.getByRole("heading", { name: "Thử một việc nhỏ" })).toBeInTheDocument();

      const fold = screen.getByRole("button", { name: READ_ONLY_TODAY });
      fold.focus();
      await user.keyboard("{Enter}");

      const folded = screen.getByRole("region", { name: FOLDED_ACTION_LABEL });
      expect(folded.children).toHaveLength(1);
      expect(within(folded).getByRole("button", { name: SHOW_ACTION_AGAIN })).toHaveFocus();
      expect(screen.queryByRole("heading", { name: "Thử một việc nhỏ" })).not.toBeInTheDocument();
      expect(screen.queryByText(content.sections.micro_action)).not.toBeInTheDocument();
      expect(screen.queryByRole("button", { name: "Giữ để thử hôm nay" })).not.toBeInTheDocument();
      // The rest of the note stays.
      expect(screen.getByRole("heading", { name: content.sections.hook })).toBeInTheDocument();

      await user.keyboard(" ");
      expect(screen.getByRole("button", { name: READ_ONLY_TODAY })).toHaveFocus();
      expect(screen.getByText(content.sections.micro_action)).toBeInTheDocument();
    });

    it("never keeps, stops or records anything when the box is folded over a kept action", async () => {
      const handlers = { onChoose: vi.fn(), onUndo: vi.fn(), onReflect: vi.fn() };
      const held = {
        id: "10000000-0000-4000-8000-000000000001", version: 1, daily_note_id: "00000000-0000-4000-8000-000000000001",
        revision_id: content.revision_id, state: "chosen" as const, background_lens: "auto" as const, ...experiment, outcome: null,
        created_at: "2026-09-07T12:00:00Z", updated_at: "2026-09-07T12:00:00Z", expires_at: "2026-10-07T12:00:00Z", reflected_at: null,
      };
      function Kept() {
        const [readOnly, setReadOnly] = useState(false);
        return <ReadingContent content={{ ...content, experiment }} currentExperiment={held} readOnly={{ readOnly, onToggle: () => setReadOnly((value) => !value) }} {...handlers} />;
      }
      render(<Kept />);
      expect(screen.getByRole("button", { name: "Bỏ giữ việc này" })).toBeInTheDocument();
      await userEvent.click(screen.getByRole("button", { name: READ_ONLY_TODAY }));
      await userEvent.click(screen.getByRole("button", { name: SHOW_ACTION_AGAIN }));

      // Still kept, and no handler ran.
      expect(screen.getByRole("button", { name: "Bỏ giữ việc này" })).toBeInTheDocument();
      for (const handler of Object.values(handlers)) expect(handler).not.toHaveBeenCalled();
    });

    it("offers no fold button where the page did not ask for one, or where there is no action box", () => {
      const { rerender } = render(<ReadingContent content={{ ...content, experiment }} />);
      expect(screen.queryByRole("button", { name: READ_ONLY_TODAY })).not.toBeInTheDocument();
      rerender(<ReadingContent content={{ ...content, purpose: "reading_detail" }} readOnly={{ readOnly: false, onToggle: vi.fn() }} />);
      expect(screen.queryByRole("button", { name: READ_ONLY_TODAY })).not.toBeInTheDocument();
      rerender(<ReadingContent content={{ ...content, purpose: "reading_detail" }} readOnly={{ readOnly: true, onToggle: vi.fn() }} />);
      expect(screen.queryByRole("button", { name: SHOW_ACTION_AGAIN })).not.toBeInTheDocument();
    });

    it("uses the labels recorded in the copy store", () => {
      const registry = JSON.parse(readFileSync(join(process.cwd(), "../api/app/domains/content/copy_registry.json"), "utf8")) as {
        entries: { id: string; text: string }[];
      };
      const text = (id: string) => registry.entries.find((entry) => entry.id === id)?.text;
      expect(text("web.action.read-only.hide")).toBe(READ_ONLY_TODAY);
      expect(text("web.action.read-only.show")).toBe(SHOW_ACTION_AGAIN);
      expect(text("web.action.read-only.folded")).toBe(FOLDED_ACTION_LABEL);
      expect(text("web.action.alone.show")).toBe(SHOW_ALONE_ACTION);
      expect(text("web.action.alone.back")).toBe(SHOW_PREVIOUS_ACTION);
    });

    it("gives the fold button a 44 px touch target on both pages", () => {
      // .text-button is 2.75rem high app-wide; the two rules for this button must not undo that.
      expect(ultravioletStyles).toMatch(/:is\(\.text-button,[^{]*\{ min-height: 2\.75rem;/);
      for (const rule of ultravioletStyles.split("\n").filter((line) => line.includes("__read-only"))) {
        expect(rule).not.toMatch(/(min-)?height:/);
      }
    });
  });

  it("does not add a Daily action to a natal reading", () => {
    render(<ReadingContent content={{ ...content, purpose: "reading_detail" }} />);

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

    // One label: the summary. No second heading repeating the same question.
    expect(screen.getAllByText(/Vì sao hôm nay/)).toHaveLength(1);
    expect(screen.queryByRole("heading", { name: /Vì sao hôm nay/ })).not.toBeInTheDocument();
    expect(screen.getByText(withTransit.sections.transit)).toBeInTheDocument();
  });

  it("does not promise a reason for today when the note is natal-only", () => {
    render(<ReadingContent content={content} />);
    expect(screen.queryByText("Vì sao hôm nay?")).not.toBeInTheDocument();
    expect(screen.getByText("Note này dựa vào đâu?")).toBeVisible();
    expect(screen.getByText("Note này dựa trên lá số gốc của bạn.")).toBeInTheDocument();
  });

  it("folds technical evidence under its own label", () => {
    const { container } = render(<ReadingContent content={content} />);
    const technical = container.querySelector("details.reading-evidence__technical");
    expect(technical).not.toBeNull();
    expect(technical).not.toHaveAttribute("open");
    expect(technical).toHaveTextContent("Chi tiết lá số");
    expect(technical).toHaveTextContent(content.evidence.claims[0]);
  });

  it("opens the why-today panel when Home links to it", () => {
    window.history.replaceState(null, "", "/note/today#vi-sao-hom-nay");
    const { container } = render(<ReadingContent content={content} />);
    expect(container.querySelector("details#vi-sao-hom-nay")).toHaveAttribute("open");
    window.history.replaceState(null, "", "/");
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
