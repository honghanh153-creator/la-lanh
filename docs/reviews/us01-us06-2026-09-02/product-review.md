# Product review US01–US06 — 2026-09-02

## Verdict

**US01–US06 đã thành một web/PWA reference chạy end-to-end với backend thật và Cosmic Glass Signal thống nhất.** Đây chưa phải production native app: secure storage, privacy manifest/data-safety declaration, binary security test, rate limit và retention operations vẫn là release gate.

## Coverage theo user story

| US | Flow/màn đã có | Khả năng hiện tại | Trạng thái |
|---|---|---|---|
| US01 | `/welcome` → `/consent` → `/privacy` → `/demo` | Value-first; guest sau consent; decline vẫn xem demo; không login wall; privacy/retention copy | Web/PWA complete |
| US02 | `/birth` → `/reveal` → `/birth-card` | DD/MM/YYYY strict; age gate 18+; Swiss Ephemeris; Sun-only `Vibe`; factual provenance; safe card export | Web/PWA complete |
| US03 | `/home` → `/note/today` | Daily Note immutable theo ngày/snapshot; full body 80–140 từ; cache/offline/error; persona + provenance/fallback | Web/PWA complete |
| US04 | Mood module Home | 5 enum mood; selected state; server upsert; bounded local pending khi offline; không free text/diagnosis | Web/PWA complete |
| US05 | Home/Detail → `/card`; `/saved`; `/share/:token` | Save idempotent; local fallback/TTL; preview 9:16/1:1; PNG; safe opaque link; owner revoke | Web/PWA complete |
| US06 | Home/Profile → `/birth-time` → success | Exact/approx/unknown; city search; deep-data consent; timezone-aware natal chart; edit/remove; valid deep chart đổi sang `Aura` | Web/PWA complete |

## Screen inventory

| Màn | US | Làm được gì |
|---|---:|---|
| Welcome 1–2 | 01 | Hiểu value, cách dùng dữ liệu và vào dùng thử |
| Consent | 01 | Đồng ý purpose cụ thể hoặc từ chối và vào demo |
| Privacy detail | 01 | Xem dữ liệu, mục đích, retention và quyền xóa |
| Demo | 01 | Xem value không gửi birth data |
| Birth date | 02 | Nhập/validate ngày sinh và age gate trước submit |
| Compute ritual/error | 02 | Trạng thái tính thật, lỗi và retry |
| Reveal | 02 | `Vibe · label`, factual Sun provenance, vào Home/card |
| Birth card | 02 | Preview/export card an toàn |
| Home | 03–06 | Đọc note, mood, save/share và mở lớp dữ liệu sâu |
| Note detail | 03/05 | Đọc 80–140 từ, provenance, save/share |
| Saved | 05 | Xem snapshot đã lưu và bỏ lưu có undo |
| Share card | 05 | Chọn ratio, PNG/share, safe link và revoke |
| Public share | 05 | Snapshot read-only đã sanitize bằng opaque token |
| Birth supplement | 06 | Precision, time/place, consent và recompute |
| Profile / Settings | 01–06 | Xem/sửa/xóa dữ liệu, privacy và toggle dark/light |

## Vocabulary và theme đã chốt

- Sun-only: `Vibe · <label 3–5 chữ>`; full natal hợp lệ: `Aura · <label 3–5 chữ>`.
- 12 Vibe labels: Nóng, Bền, Lanh, Mềm, Rực, Gọn, Duyên, Sâu, Phiêu, Chắc, Khác, Mộng.
- Aura theo dominant element: Rực, Chắc, Lanh, Mềm; server version hóa mapping và xử lý tie-break.
- Factual placement như “Mặt Trời Cự Giải” vẫn ở reveal/profile/provenance, không dùng làm compact persona.
- Toàn bộ light/dark dùng **direction 02 — Cosmic Glass Signal**; entry toggle ở Mình → Cài đặt.

## Security và privacy review

Đã có trong implementation:

- Guest token HttpOnly cookie; mutations dùng CSRF và trusted-origin check.
- Ownership được kiểm ở API; public token ngẫu nhiên 256-bit, chỉ lưu hash, response không phân biệt token sai/hết hạn/revoked.
- Public snapshot theo allowlist, không có DOB/time/place/coordinates/session/profile/mood; owner có thể thu hồi link.
- Request schema từ chối field thừa; no-mock runtime guard và privacy guard chạy trong quality gate.
- Server-side guest delete đi trước, sau đó client xóa session, note/save/mood caches và CacheStorage.
- Daily cache TTL 36 giờ; local saved snapshot TTL 30 ngày; theme preference không gửi server.

Release blockers:

- Thêm rate limiting/abuse protection cho compute, place search và public share.
- Chạy retention cleanup job có monitoring/audit evidence; hoàn thiện data-subject request và incident playbook.
- Native app phải dùng Keychain/Keystore-backed storage, backup exclusion, transport policy và MASVS verification.
- Khai App Privacy/Privacy Manifest và Google Play Data Safety đúng với binary/SDK thật trước khi phát hành.

## Verification evidence

- Browser QA 390 × 844: full US01–US06 happy path, Vibe→Aura, light/dark, safe share + revoke; không console error/overflow.
- API suite: 54/54 tests pass; lint, format và strict typecheck pass.
- Contract generation current; migration chain có share revoke và daily persona metadata.
- Full `pnpm check` pass; production web/API build pass. Bundle JS hiện khoảng 533 kB và còn warning code-split P2.

## Release priority

1. P0 native — app shell, secure storage, privacy manifests/data-safety và device accessibility tests.
2. P1 platform — rate limit, abuse monitoring, retention/deletion operational evidence.
3. P1 verification — staging E2E 320/390/430px, text scale 200%, offline/app-kill/network recovery.
4. P2 quality — bundle split, observability và richer content QA without deterministic claims.
