import { ArrowRight, ChartBar, Check, Sparkle } from "@phosphor-icons/react";
import { useEffect, useState } from "react";
import type { ReactNode } from "react";

import type {
  DailyExperiment,
  ExperimentOutcome,
  ReadingContent as ReadingContentModel,
} from "../api/client";
import type { DailyExperimentStatus } from "../hooks/useDailyExperiment";
import { ReadingDisclaimer } from "./ReadingDisclaimer";
import { readingModeLabel } from "./readingLabels";

type ReadingContentProps = {
  content: ReadingContentModel;
  compact?: boolean;
  currentExperiment?: DailyExperiment | null;
  experimentStatus?: DailyExperimentStatus;
  experimentError?: string | null;
  onChoose?: () => void;
  onUndo?: () => void;
  onReflect?: (outcome: ExperimentOutcome) => void;
  toolbar?: ReactNode;
};

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
  toolbar,
}: ReadingContentProps) {
  const experiment = (
    <ExperimentSection
      content={content}
      currentExperiment={currentExperiment}
      error={experimentError}
      onChoose={onChoose}
      onReflect={onReflect}
      onUndo={onUndo}
      status={experimentStatus}
    />
  );

  if (compact) {
    return (
      <article className="reading-content reading-content--compact">
        <header className="reading-content__intro">
          {toolbar ? <div className="reading-content__toolbar">{toolbar}</div> : null}
          <p className="reading-mode"><Sparkle aria-hidden="true" weight="fill" /> {readingModeLabel(content)}</p>
          <h2>{content.sections.hook}</h2>
          <p>{content.sections.manifestation}</p>
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
        {toolbar ? <div className="reading-content__toolbar">{toolbar}</div> : null}
        <p className="reading-mode"><Sparkle aria-hidden="true" weight="fill" /> {readingModeLabel(content)}</p>
        <h1>{content.sections.hook}</h1>
        <p>{content.sections.thesis}</p>
      </header>
      <section>
        <h2>Ngoài đời có thể trông như…</h2>
        <p>{content.sections.manifestation}</p>
      </section>
      {experiment}
      <Evidence content={content} />
      <ReadingDisclaimer>{content.disclaimer}</ReadingDisclaimer>
    </article>
  );
}

function ExperimentSection({
  content,
  currentExperiment,
  error,
  onChoose,
  onReflect,
  onUndo,
  status,
}: {
  content: ReadingContentModel;
  currentExperiment: DailyExperiment | null;
  error: string | null;
  onChoose?: () => void;
  onReflect?: (outcome: ExperimentOutcome) => void;
  onUndo?: () => void;
  status: DailyExperimentStatus;
}) {
  const experiment = content.experiment;
  const [replaceConfirming, setReplaceConfirming] = useState(false);
  const [reflectionOpen, setReflectionOpen] = useState(false);
  const currentMatches = Boolean(experiment && currentExperiment?.action_key === experiment.action_key);
  const busy = status === "choosing" || status === "undoing" || status === "reflecting";

  useEffect(() => {
    setReplaceConfirming(false);
    setReflectionOpen(false);
  }, [currentExperiment?.id, currentExperiment?.version, experiment?.action_key]);

  if (!experiment) {
    return (
      <section className="reading-content__action">
        <p className="eyebrow">Một góc để kiểm chứng</p>
        <h2>Đối chiếu với hôm nay</h2>
        <p className="reading-content__experiment-action">{content.sections.micro_action}</p>
      </section>
    );
  }

  const isReflected = currentMatches && currentExperiment?.state === "reflected";
  const actionLabel = status === "choosing"
    ? "Đang giữ…"
    : currentMatches
      ? "Đang giữ việc này"
      : currentExperiment
        ? replaceConfirming ? "Xác nhận thay việc đang giữ" : "Thay việc đang giữ"
        : "Giữ để thử hôm nay";

  return (
    <section className="reading-content__action" aria-labelledby={`experiment-${experiment.action_key}`}>
      <p className="eyebrow">Một thử nghiệm nhỏ</p>
      <h2 id={`experiment-${experiment.action_key}`}>Thử rồi tự kiểm chứng</h2>
      <p className="reading-content__experiment-action">{experiment.action}</p>
      <div className="reading-content__experiment-cues">
        <p><strong>Để ý:</strong> {experiment.observation}</p>
        <p><strong>Quyền của bạn:</strong> {experiment.permission}</p>
      </div>

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
            <p><strong>Quyền của bạn:</strong> {currentExperiment.permission}</p>
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
    </section>
  );
}

function Evidence({ content }: { content: ReadingContentModel }) {
  return (
    <details className="reading-evidence">
      <summary><ChartBar aria-hidden="true" /><span>Vì sao hôm nay?</span></summary>
      {content.sections.transit ? (
        <div className="reading-content__transit">
          <h2>Vì sao hôm nay thấy rõ hơn?</h2>
          <p>{content.sections.transit}</p>
        </div>
      ) : null}
      <strong>{content.evidence.title}</strong>
      <ul>
        {content.evidence.claims.map((claim) => <li key={claim}>{claim}</li>)}
      </ul>
      <p>{content.evidence.framework_disclosure}</p>
    </details>
  );
}
