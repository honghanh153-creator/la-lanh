import { ArrowRight, ChartBar, Check, Sparkle } from "@phosphor-icons/react";
import { useEffect, useState } from "react";
import type { ReactNode } from "react";

import type {
  DailyExperiment,
  ExperimentOutcome,
  ReadingContent as ReadingContentModel,
} from "../api/client";
import type { DailyExperimentStatus } from "../hooks/useDailyExperiment";
import { NightSky } from "./NightSky";
import { ReadingDisclaimer } from "./ReadingDisclaimer";
import { readingModeLabel, WHY_TODAY_ID } from "./readingLabels";

type ReadingContentProps = {
  content: ReadingContentModel;
  compact?: boolean;
  currentExperiment?: DailyExperiment | null;
  experimentStatus?: DailyExperimentStatus;
  experimentError?: string | null;
  onChoose?: () => void;
  onUndo?: () => void;
  onReflect?: (outcome: ExperimentOutcome) => void;
  /** Present only when the reader can switch between the card's action and the lighter one (#627). */
  lighter?: LighterSwitch | null;
  /** Present only where the reader can fold the small-action box away for the day (#700). */
  readOnly?: ReadOnlySwitch | null;
  toolbar?: ReactNode;
};

/** The mood's alternative action and how to switch to it (#627, #701). */
export type LighterSwitch = {
  shown: boolean;
  onSwitch: () => void;
  /** The alternative to show; defaults to the lighter action. */
  action?: NonNullable<ReadingContentModel["lighter_action"]> | null;
  /** The switch label while the card's action is shown; defaults to the lighter one. */
  label?: string;
};
export type ReadOnlySwitch = { readOnly: boolean; onToggle: () => void };

const ACTION_HEADING = "Thử một việc nhỏ";
export const SHOW_ORIGINAL_ACTION = "Xem việc ban đầu";
export const SHOW_LIGHTER_ACTION = "Xem việc nhẹ hơn";
// Same text as `web.action.read-only.*` in the copy store (copy_registry.json); a test holds them equal.
export const READ_ONLY_TODAY = "Hôm nay chỉ muốn đọc";
export const SHOW_ACTION_AGAIN = "Hiện lại việc nhỏ";
export const FOLDED_ACTION_LABEL = "Việc nhỏ hôm nay đang ẩn";

/**
 * The one button that folds the small-action box to a single line and opens it again. It only
 * changes what this page shows: no request, nothing stored, a kept action stays kept. Render it
 * with the same key in both states so the element, and the keyboard focus on it, survive the press.
 */
export function ReadOnlyToggle({ className, control }: { className: string; control: ReadOnlySwitch }) {
  return (
    <button className={`text-button ${className}`} onClick={control.onToggle} type="button">
      {control.readOnly ? SHOW_ACTION_AGAIN : READ_ONLY_TODAY}
    </button>
  );
}

const outcomeLabels: Record<ExperimentOutcome, string> = {
  not_tried: "Chưa thử",
  helpful: "Có ích một chút",
  no_difference: "Chưa thấy khác",
  not_for_now: "Không hợp lúc này",
};

export function ReadingContent({
  content,
  compact = false,
  currentExperiment = null,
  experimentStatus = "idle",
  experimentError = null,
  onChoose,
  onUndo,
  onReflect,
  lighter = null,
  readOnly = null,
  toolbar,
}: ReadingContentProps) {
  const isVibeFallback = content.mode === "vibe_fallback";
  const experiment = (
    <ExperimentSection
      compact={compact}
      content={content}
      currentExperiment={currentExperiment}
      error={experimentError}
      lighter={lighter}
      onChoose={onChoose}
      onReflect={onReflect}
      onUndo={onUndo}
      readOnly={readOnly}
      status={experimentStatus}
    />
  );

  if (compact) {
    return (
      <article className="reading-content reading-content--compact">
        <header className="reading-content__intro">
          <NightSky moon planet stars={4} />
          {toolbar ? <div className="reading-content__toolbar">{toolbar}</div> : null}
          <p className="reading-mode"><Sparkle aria-hidden="true" weight="fill" /> {readingModeLabel(content)}</p>
          <h2>{content.sections.hook}</h2>
          {!isVibeFallback ? <p>{content.sections.manifestation}</p> : null}
        </header>
        {experiment}
        <Evidence content={content} />
        <ReadingDisclaimer compact>{content.disclaimer}</ReadingDisclaimer>
      </article>
    );
  }

  return (
    <article className="reading-content">
      <header className="reading-content__intro">
          <NightSky moon planet stars={4} />
        {toolbar ? <div className="reading-content__toolbar">{toolbar}</div> : null}
        <p className="reading-mode"><Sparkle aria-hidden="true" weight="fill" /> {readingModeLabel(content)}</p>
        <h1>{content.sections.hook}</h1>
        <p>{content.sections.thesis}</p>
      </header>
      {!isVibeFallback ? (
        <section>
          <h2>{content.tradition === "jyotish" ? "Thông tin đã tính" : "Ngoài đời có thể trông như…"}</h2>
          <p>{content.sections.manifestation}</p>
        </section>
      ) : null}
      {experiment}
      <Evidence content={content} />
      <ReadingDisclaimer>{content.disclaimer}</ReadingDisclaimer>
    </article>
  );
}

function ExperimentSection({
  compact,
  content,
  currentExperiment,
  error,
  lighter,
  onChoose,
  onReflect,
  onUndo,
  readOnly,
  status,
}: {
  compact: boolean;
  content: ReadingContentModel;
  currentExperiment: DailyExperiment | null;
  error: string | null;
  lighter: LighterSwitch | null;
  onChoose?: () => void;
  onReflect?: (outcome: ExperimentOutcome) => void;
  onUndo?: () => void;
  readOnly: ReadOnlySwitch | null;
  status: DailyExperimentStatus;
}) {
  // The lighter action replaces what is shown, never the note itself (US-04 AC14).
  const alternative = lighter ? (lighter.action ?? content.lighter_action) : null;
  const lighterAction = lighter?.shown ? alternative : null;
  const experiment = lighterAction ? lighterAction.experiment : content.experiment;
  const plainAction = lighterAction ? lighterAction.action : content.sections.micro_action;
  const switchButton = lighter && alternative ? (
    <button className="text-button reading-content__lighter-switch" onClick={lighter.onSwitch} type="button">
      {lighter.shown ? SHOW_ORIGINAL_ACTION : (lighter.label ?? SHOW_LIGHTER_ACTION)}
    </button>
  ) : null;
  const readOnlyToggle = readOnly ? (
    <ReadOnlyToggle className="reading-content__read-only" control={readOnly} key="read-only-toggle" />
  ) : null;
  const isDaily = content.purpose === "daily_note" || content.purpose === "personalized_sky";
  // Home already shows this action; the detail page must not drop it just
  // because a non-exact reading has no holdable experiment.
  if (!experiment && (compact || !isDaily || !plainAction)) return null;
  if (readOnly?.readOnly) {
    // Folded to one line (#700). Every branch returns a <section>, so the toggle keeps its focus.
    return (
      <section aria-label={FOLDED_ACTION_LABEL} className="reading-content__action reading-content__action--read-only">
        {readOnlyToggle}
      </section>
    );
  }
  if (!experiment) {
    return (
      <section className="reading-content__action" aria-labelledby="reading-action-title">
        <h2 id="reading-action-title">{ACTION_HEADING}</h2>
        <p className="reading-content__experiment-action">{plainAction}</p>
        {switchButton}
        {readOnlyToggle}
      </section>
    );
  }

  return (
    <section className="reading-content__action" aria-labelledby={`experiment-${experiment.action_key}`}>
      <h2 id={`experiment-${experiment.action_key}`}>{ACTION_HEADING}</h2>
      <p className="reading-content__experiment-action">{experiment.action}</p>
      <div className="reading-content__experiment-cues">
        <p><strong>Để ý:</strong> {experiment.observation}</p>
        <p className="reading-content__permission">{experiment.permission}</p>
      </div>
      {switchButton}

      <ExperimentControls
        currentExperiment={currentExperiment}
        error={error}
        experiment={experiment}
        onChoose={onChoose}
        onReflect={onReflect}
        onUndo={onUndo}
        status={status}
      />
      {readOnlyToggle}
    </section>
  );
}

/**
 * Keep, stop keeping, replace and look back on the day's action. Home and the note page render
 * this one component over the same server state, so the two cannot drift apart (US-03 AC33).
 */
export function ExperimentControls({
  experiment,
  currentExperiment,
  error,
  onChoose,
  onReflect,
  onUndo,
  status,
}: {
  /** The action on screen that can be kept. */
  experiment: NonNullable<ReadingContentModel["experiment"]>;
  currentExperiment: DailyExperiment | null;
  error: string | null;
  onChoose?: () => void;
  onReflect?: (outcome: ExperimentOutcome) => void;
  onUndo?: () => void;
  status: DailyExperimentStatus;
}) {
  const [replaceConfirming, setReplaceConfirming] = useState(false);
  const [reflectionOpen, setReflectionOpen] = useState(false);
  const currentMatches = currentExperiment?.action_key === experiment.action_key;
  const busy = status === "choosing" || status === "undoing" || status === "reflecting";

  useEffect(() => {
    setReplaceConfirming(false);
    setReflectionOpen(false);
  }, [currentExperiment?.id, currentExperiment?.version, experiment.action_key]);

  const isReflected = currentMatches && currentExperiment?.state === "reflected";
  const actionLabel = status === "choosing"
    ? "Đang giữ…"
    : currentMatches
      ? "Đang giữ việc này"
      : currentExperiment
        ? replaceConfirming ? "Xác nhận thay việc đang giữ" : "Thay việc đang giữ"
        : "Giữ để thử hôm nay";

  return (
    <>
      {isReflected ? (
        <div className="reading-content__reflected" role="status">
          <Check aria-hidden="true" />
          <span>Đã nhìn lại: <strong>{outcomeLabels[currentExperiment.outcome ?? "not_tried"]}</strong></span>
        </div>
      ) : null}

      {currentExperiment && !currentMatches ? (
        <div className="reading-content__held-experiment">
          <p className="eyebrow">Việc đang giữ</p>
          <p className="reading-content__experiment-action">{currentExperiment.action}</p>
          <div className="reading-content__experiment-cues">
            <p><strong>Để ý:</strong> {currentExperiment.observation}</p>
            <p className="reading-content__permission">{currentExperiment.permission}</p>
          </div>
          {currentExperiment.state === "chosen" ? (
            <button className="text-button" disabled={busy} onClick={onUndo} type="button">
              {status === "undoing" ? "Đang bỏ giữ…" : "Bỏ giữ việc này"}
            </button>
          ) : null}
        </div>
      ) : null}

      {!currentMatches ? (
        <button
          aria-describedby={currentExperiment ? `experiment-replace-${experiment.action_key}` : undefined}
          className="reading-content__experiment-button"
          disabled={busy || status === "loading"}
          onClick={() => {
            if (currentExperiment && !replaceConfirming) {
              setReplaceConfirming(true);
              return;
            }
            onChoose?.();
          }}
          type="button"
        >
          {actionLabel}<ArrowRight aria-hidden="true" />
        </button>
      ) : null}

      {currentExperiment && !currentMatches && replaceConfirming ? (
        <p className="reading-content__replace-note" id={`experiment-replace-${experiment.action_key}`}>
          Việc đang giữ sẽ được thay thế. Chỉ việc mới được giữ lại; không tạo streak hay đánh dấu hoàn thành.
        </p>
      ) : null}

      {currentMatches && !isReflected ? (
        <div className="reading-content__experiment-actions">
          <button className="text-button" disabled={busy} onClick={onUndo} type="button">{status === "undoing" ? "Đang bỏ giữ…" : "Bỏ giữ việc này"}</button>
          <button className="text-button" disabled={busy} onClick={() => setReflectionOpen((open) => !open)} type="button">
            {reflectionOpen ? "Đóng nhìn lại" : "Mở phần nhìn lại"}
          </button>
        </div>
      ) : null}

      {reflectionOpen && currentMatches && !isReflected ? (
        <fieldset className="reading-content__outcomes">
          <legend>Điều gì đúng với bạn?</legend>
          <div>
            {(Object.keys(outcomeLabels) as ExperimentOutcome[]).map((outcome) => (
              <button disabled={busy} key={outcome} onClick={() => onReflect?.(outcome)} type="button">
                {outcomeLabels[outcome]}
              </button>
            ))}
          </div>
        </fieldset>
      ) : null}

      {error ? <p className="reading-content__experiment-error" role="alert">{error}</p> : null}
    </>
  );
}

function Evidence({ content }: { content: ReadingContentModel }) {
  const isDaily = content.purpose === "daily_note" || content.purpose === "personalized_sky";
  const transit = content.sections.transit;
  const openFromLink = isDaily && typeof window !== "undefined" && window.location.hash === `#${WHY_TODAY_ID}`;
  // "Vì sao hôm nay?" is only promised when today's sky truly explains the note.
  const summary = !isDaily ? "Bản đọc này dựa vào đâu?" : transit ? "Vì sao hôm nay?" : "Note này dựa vào đâu?";
  return (
    <details className="reading-evidence" id={isDaily ? WHY_TODAY_ID : undefined} open={openFromLink || undefined}>
      <summary><ChartBar aria-hidden="true" /><span>{summary}</span></summary>
      {transit ? <p className="reading-content__transit">{transit}</p> : null}
      {isDaily && !transit ? <p className="reading-content__basis">Note này dựa trên lá số gốc của bạn.</p> : null}
      <details className="reading-evidence__technical">
        <summary>Chi tiết lá số</summary>
        <strong>{content.evidence.title}</strong>
        <ul>
          {content.evidence.claims.map((claim) => <li key={claim}>{claim}</li>)}
        </ul>
        <p>{content.evidence.framework_disclosure}</p>
      </details>
    </details>
  );
}
