import { useMemo, useState } from "react";

import { BrandMark } from "../../shared/ui/BrandMark";
import {
  createContentDraft,
  getContentWorkspace,
  publishContentRevision,
  rollbackContentRevision,
  StudioApiError,
  type ContentRevision,
  type ContentValidation,
  type ContentWorkspace,
} from "../../shared/api/studioClient";
import "./studio.css";

type MatrixPayload = ContentWorkspace["payload"];

const GROUP_LABELS: Record<string, string> = {
  planets: "Hành tinh",
  signs: "Cung",
  houses: "Nhà",
  aspects: "Góc",
};

const FIELD_LABELS: Record<string, string> = {
  drive: "Nhu cầu cốt lõi",
  stress: "Điểm dễ kẹt",
  action: "Việc có thể thử",
  style: "Cách vận hành",
  manifestation: "Ngoài đời trông như…",
  practices: "Ngân hàng hành động",
  hooks: "Ngân hàng mở bài",
  arena: "Vùng đời sống",
  bridge: "Cách hai phần tương tác",
  watch: "Điểm cần canh",
};

export function ContentStudioPage() {
  const [token, setToken] = useState("");
  const [workspace, setWorkspace] = useState<ContentWorkspace | null>(null);
  const [draft, setDraft] = useState<MatrixPayload | null>(null);
  const [group, setGroup] = useState("signs");
  const [entryId, setEntryId] = useState("pisces");
  const [query, setQuery] = useState("");
  const [reason, setReason] = useState("Làm rõ nội dung cho người mới đọc");
  const [savedRevision, setSavedRevision] = useState<ContentRevision | null>(null);
  const [validation, setValidation] = useState<ContentValidation | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const entryIds = useMemo(
    () => Object.keys(draft?.[group] ?? {}).filter((id) => id.includes(query.trim().toLowerCase())),
    [draft, group, query],
  );
  const entries = draft?.[group] ?? {};
  const selected = entries[entryId];

  const connect = async () => {
    setBusy(true);
    setError(null);
    try {
      const normalizedToken = token.trim();
      const next = await getContentWorkspace(normalizedToken);
      setToken(normalizedToken);
      setWorkspace(next);
      setDraft(structuredClone(next.payload));
      const first = Object.keys(next.payload.signs ?? {})[0];
      if (first) setEntryId(first);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Không thể mở Studio.");
    } finally {
      setBusy(false);
    }
  };

  const updateField = (field: string, value: string | string[]) => {
    if (!draft || !selected) return;
    setDraft({
      ...draft,
      [group]: {
        ...draft[group],
        [entryId]: { ...selected, [field]: value },
      },
    });
    setSavedRevision(null);
    setValidation(null);
  };

  const saveDraft = async () => {
    if (!workspace || !draft) return;
    setBusy(true);
    setError(null);
    try {
      const result = await createContentDraft(
        token,
        draft,
        workspace.channel.active_revision_id,
        reason,
      );
      setSavedRevision(result.revision);
      setValidation(result.validation);
    } catch (requestError) {
      if (requestError instanceof StudioApiError && requestError.validation) {
        setValidation(requestError.validation);
      }
      setError(requestError instanceof Error ? requestError.message : "Không thể lưu draft.");
    } finally {
      setBusy(false);
    }
  };

  const publish = async () => {
    if (!workspace || !savedRevision || !validation?.passed) return;
    if (!window.confirm("Publish release này cho các note được sinh từ bây giờ?")) return;
    setBusy(true);
    setError(null);
    try {
      await publishContentRevision(
        token,
        savedRevision.id,
        workspace.channel.generation,
        reason,
      );
      const next = await getContentWorkspace(token);
      setWorkspace(next);
      setDraft(structuredClone(next.payload));
      setSavedRevision(null);
      setValidation(null);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Không thể publish.");
    } finally {
      setBusy(false);
    }
  };

  const rollback = async (revisionId: string) => {
    if (!workspace) return;
    if (!window.confirm("Quay lại release này cho các note được sinh từ bây giờ?")) return;
    setBusy(true);
    setError(null);
    try {
      await rollbackContentRevision(
        token,
        revisionId,
        workspace.channel.generation,
        `Rollback: ${reason}`,
      );
      const next = await getContentWorkspace(token);
      setWorkspace(next);
      setDraft(structuredClone(next.payload));
      setSavedRevision(null);
      setValidation(null);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Không thể rollback.");
    } finally {
      setBusy(false);
    }
  };

  if (!workspace || !draft) {
    return (
      <main className="studio-login">
        <div className="studio-login__card">
          <BrandMark />
          <p className="studio-kicker">CONTENT STUDIO · BETA NỘI BỘ</p>
          <h1>Review nội dung trước khi người dùng thấy.</h1>
          <p>
            Token chỉ nằm trong bộ nhớ của tab này. Studio không đọc hồ sơ sinh hoặc câu hỏi thật.
          </p>
          <label>
            Token truy cập
            <input
              type="password"
              autoComplete="off"
              value={token}
              onChange={(event) => setToken(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") void connect();
              }}
            />
          </label>
          <button type="button" className="studio-primary" disabled={busy || token.length < 32} onClick={() => void connect()}>
            {busy ? "Đang mở…" : "Mở Content Studio"}
          </button>
          {error ? <p className="studio-error" role="alert">{error}</p> : null}
        </div>
      </main>
    );
  }

  return (
    <main className="studio-shell">
      <header className="studio-header">
        <BrandMark />
        <div>
          <p className="studio-kicker">CONTENT STUDIO</p>
          <h1>Daily content matrix</h1>
          <p>
            Nguồn đang dùng: <strong>{workspace.source === "published" ? "release đã publish" : "baseline trong code"}</strong>
            {" · "}generation {workspace.channel.generation}
          </p>
        </div>
        <button type="button" className="studio-quiet" disabled={busy} onClick={() => {
          setWorkspace(null);
          setDraft(null);
          setToken("");
          setSavedRevision(null);
          setValidation(null);
          setError(null);
          setReason("Làm rõ nội dung cho người mới đọc");
        }}>
          Khóa Studio
        </button>
      </header>

      <RewriteReviewBoard workspace={workspace} />

      <section className="studio-workspace">
        <aside className="studio-nav" aria-label="Nhóm content matrix">
          <input
            aria-label="Tìm ID nội dung"
            placeholder="Tìm ID…"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          <div className="studio-tabs">
            {Object.keys(draft).map((key) => (
              <button
                type="button"
                className={key === group ? "is-active" : ""}
                key={key}
                onClick={() => {
                  setGroup(key);
                  const first = Object.keys(draft[key])[0];
                  if (first) setEntryId(first);
                }}
              >
                <span>{GROUP_LABELS[key] ?? key}</span>
                <small>{workspace.summary[key]}</small>
              </button>
            ))}
          </div>
          <div className="studio-entry-list">
            {entryIds.map((id) => (
              <button
                type="button"
                className={id === entryId ? "is-active" : ""}
                key={id}
                onClick={() => setEntryId(id)}
              >
                {id}
              </button>
            ))}
          </div>
        </aside>

        <section className="studio-editor">
          <div className="studio-section-heading">
            <div>
              <p className="studio-kicker">{GROUP_LABELS[group] ?? group}</p>
              <h2>{entryId}</h2>
            </div>
            <span className="studio-version">{savedRevision ? `draft ${savedRevision.id.slice(0, 8)}` : "chưa lưu"}</span>
          </div>
          {selected ? Object.entries(selected).map(([field, value]) => (
            <label className="studio-field" key={field}>
              <span>{FIELD_LABELS[field] ?? field}</span>
              {Array.isArray(value) ? (
                <textarea
                  rows={Math.max(4, value.length * 2)}
                  value={value.join("\n")}
                  onChange={(event) => updateField(field, event.target.value.split("\n").filter(Boolean))}
                />
              ) : (
                <textarea
                  rows={3}
                  value={value}
                  onChange={(event) => updateField(field, event.target.value)}
                />
              )}
              <small>{Array.isArray(value) ? "Mỗi dòng là một biến thể." : `${value.length}/360 ký tự`}</small>
            </label>
          )) : <p>Chọn một mục để review.</p>}
        </section>

        <aside className="studio-preview">
          <p className="studio-kicker">PREVIEW MỘT ENTRY</p>
          <h2>Đọc riêng mảnh này</h2>
          {selected ? <PreviewCard group={group} selected={selected} /> : null}
          <p className="studio-preview-note">
            Đây chưa phải note hoàn chỉnh. Gate server sẽ kiểm tra matrix trước khi cho publish.
          </p>
          <label className="studio-field">
            <span>Lý do thay đổi</span>
            <textarea rows={3} value={reason} onChange={(event) => setReason(event.target.value)} />
          </label>
          <div className={`studio-gate ${validation?.passed ? "is-pass" : ""}`}>
            <strong>{validation ? (validation.passed ? "Gate đã qua" : "Gate đang chặn") : "Chưa chạy gate"}</strong>
            {validation?.findings.map((finding) => (
              <p key={`${finding.rule_id}-${finding.path}`}>
                <b>{finding.path}</b><br />{finding.message}
              </p>
            ))}
          </div>
          {error ? <p className="studio-error" role="alert">{error}</p> : null}
          <button type="button" className="studio-secondary" disabled={busy || reason.trim().length < 3} onClick={() => void saveDraft()}>
            {busy ? "Đang xử lý…" : "Lưu draft & chạy gate"}
          </button>
          <button type="button" className="studio-primary" disabled={busy || !savedRevision || !validation?.passed} onClick={() => void publish()}>
            Publish release
          </button>
          <p className="studio-footnote">Publish chỉ đổi nội dung cho lần sinh note mới. Nội dung người dùng đã lưu không bị viết lại.</p>
          <section className="studio-history" aria-labelledby="studio-history-title">
            <div className="studio-history__heading">
              <h3 id="studio-history-title">Lịch sử release</h3>
              <span>{workspace.revisions.length}</span>
            </div>
            {workspace.revisions.length === 0 ? (
              <p>Chưa có release. Baseline trong code đang được dùng.</p>
            ) : workspace.revisions.slice(0, 6).map((revision) => {
              const isActive = workspace.channel.active_revision_id === revision.id;
              return (
                <article className="studio-history__item" key={revision.id}>
                  <div>
                    <strong>{revision.id.slice(0, 8)}</strong>
                    <small>{new Date(revision.created_at).toLocaleString("vi-VN")}</small>
                  </div>
                  {isActive ? (
                    <span className="studio-history__active">Đang dùng</span>
                  ) : revision.status === "published" ? (
                    <button
                      type="button"
                      className="studio-history__rollback"
                      disabled={busy}
                      onClick={() => void rollback(revision.id)}
                    >
                      Quay lại bản này
                    </button>
                  ) : (
                    <span>Draft</span>
                  )}
                </article>
              );
            })}
          </section>
        </aside>
      </section>
    </main>
  );
}

function RewriteReviewBoard({ workspace }: { workspace: ContentWorkspace }) {
  const candidates = workspace.rewrite_candidates ?? [];
  const surfaces = workspace.rewrite_surfaces ?? [];
  const pending = candidates.filter((item) => item.status === "pending" || item.status === "leased");
  const rejected = candidates.filter((item) => item.last_result === "gate_rejected");
  return (
    <section className="studio-rewrite-board" aria-labelledby="studio-rewrite-title">
      <div>
        <p className="studio-kicker">LUNA REWRITE · READ ONLY</p>
        <h2 id="studio-rewrite-title">Hàng chờ nội dung cá nhân hóa</h2>
        <p>
          Studio chỉ hiện trạng thái, phiên bản và tên field. Dữ liệu người dùng, brief và output
          vẫn được mã hóa; không có nút gọi model từ màn này.
        </p>
      </div>
      <div className="studio-rewrite-stats">
        <span><strong>{surfaces.length}</strong> surface</span>
        <span><strong>{pending.length}</strong> đang chờ</span>
        <span><strong>{rejected.length}</strong> gate chặn</span>
      </div>
      <div className="studio-rewrite-list">
        {candidates.length === 0 ? (
          <p>Chưa có candidate runtime. App vẫn dùng nội dung deterministic đã duyệt.</p>
        ) : candidates.slice(0, 8).map((item) => (
          <article key={item.id}>
            <div><strong>{item.surface}</strong><small>{item.model} · {item.prompt_version}</small></div>
            <span className={`is-${item.status}`}>{item.last_result ?? item.status}</span>
          </article>
        ))}
      </div>
    </section>
  );
}

function PreviewCard({ group, selected }: { group: string; selected: Record<string, string | string[]> }) {
  const hooks = Array.isArray(selected.hooks) ? selected.hooks : [];
  const practices = Array.isArray(selected.practices) ? selected.practices : [];
  const answer = hooks[0]
    ?? selected.drive
    ?? selected.bridge
    ?? selected.arena
    ?? "Nội dung này chưa có câu mở đầu.";
  const scene = selected.manifestation
    ?? selected.stress
    ?? selected.watch
    ?? "Chưa có tình huống đời thường.";
  const action = practices[0] ?? selected.action ?? "Chưa có việc nhỏ để thử.";
  return (
    <article className="studio-reading-card">
      <small>{GROUP_LABELS[group] ?? group}</small>
      <h3>{answer}</h3>
      <p>{scene}</p>
      <div>
        <span>Một việc có thể thử</span>
        <strong>{action}</strong>
      </div>
      <footer>Phần giải thích kỹ thuật và disclaimer sẽ được tách riêng trên app.</footer>
    </article>
  );
}
