---
artifact_contract: ce-unified-plan/v1
product_contract_source: ce-plan-bootstrap
execution: code
created_at: 2026-09-28T20:42:00+07:00
topic: question-first-home-and-la-chung-retirement
---

# Question-first Home and Lá Chứng retirement

## Goal Capsule

- **Objective:** Người dùng mở Lá Lành và hiểu ngay app giúp họ soi ba nhóm câu hỏi — về mình, về một người/kết nối, và về chuyện đang xảy ra — đồng thời có thể vào Tarot ngay khi đang có một câu hỏi cụ thể.
- **Means:** Đổi hierarchy Home sang question-first, đưa `Lá Hỏi` thành CTA nổi bật, giữ Daily Note như tín hiệu hằng ngày ở lớp kế tiếp và rút Lá Chứng khỏi product surface.
- **Product authority:** Quyết định UX và copy bám lựa chọn trong phiên này; Tarot vẫn tuân theo `docs/foundation/la-lanh-tarot-engine-spec.md`, các reading astrology vẫn tuân theo content gates hiện có.
- **Stop conditions:** Không thêm free text hoặc personal-data collection trên Home; không làm Tarot trông như bằng chứng chiêm tinh; không xóa dữ liệu Lá Chứng cũ khi chưa có retention/migration riêng; không tạo tab hoặc feature shell chưa có hành vi thật.

## Product Contract

### Problem Frame

Home hiện mở thẳng Daily Note nên giá trị toàn sản phẩm bị hiểu hẹp thành “một câu mỗi ngày”. Tarot đã có flow thật nhưng bị giấu sâu. Các capability hiểu bản thân, hiểu một kết nối và đọc bối cảnh hiện tại tồn tại ở các route khác nhau mà không có một mental model chung. Lá Chứng không còn thuộc hướng sản phẩm mới và tiếp tục xuất hiện làm phân tán USP.

### Session-settled Decisions

- KTD1. Home bắt đầu bằng câu hỏi người dùng đang muốn hiểu, không bắt đầu bằng danh sách feature.
- KTD2. Ba lối đầu là `Mình`, `Một người`, `Chuyện đang xảy ra`; mỗi lối dẫn tới capability đang hoạt động: Natal, Radar và Current Sky.
- KTD3. `Lá Hỏi` là CTA nổi bật trên Home nhưng vẫn được mô tả là một góc tự soi, không phải công cụ đoán tương lai hoặc đọc ý định người khác.
- KTD4. Daily Note vẫn là artifact hằng ngày nhưng đứng sau question router; không xóa mood, context, save/share hoặc full reading.
- KTD5. Không thay đổi bottom navigation trong slice này. Tarot được thử trên Home trước khi dành một tab thường trực.
- KTD6. Lá Chứng ngừng nhận entry mới. Route public/create cũ trả trạng thái “đã khép lại” tĩnh và không fetch token/data; các route quản lý cũ vẫn cho chủ thể thu hồi, ẩn hoặc xóa dữ liệu đã có.

### Requirements

- R1. Sau greeting, Home phải hỏi `Bạn đang muốn hiểu điều gì?` và hiển thị ba lựa chọn có mô tả kết quả, không dùng thuật ngữ chiêm tinh làm nhãn chính.
- R2. `Mình` dẫn tới `/natal`; `Một người` dẫn tới `/radar`; `Chuyện đang xảy ra` dẫn tới `/insights/current-sky?tradition=western`.
- R3. Home phải có card Tarot nổi bật với CTA `Hỏi Lá ngay`, dẫn tới `/tarot`, giải thích ngắn hành vi trước khi điều hướng.
- R4. Home không thu câu hỏi, ngày sinh, thông tin người khác hoặc context mới; collection chỉ xảy ra trong flow đích với notice/consent hiện có.
- R5. Daily Note vẫn render đầy đủ các trạng thái cached/loading/error, full-synthesis gift, context, resonance, mood, save/share và unlock như trước.
- R6. Daily Note có section label rõ để người dùng hiểu đây là tín hiệu hằng ngày, không phải câu trả lời cho mọi câu hỏi.
- R7. Home và router không còn entry tạo/xem Lá Chứng mới.
- R8. URL public/create Lá Chứng cũ hiển thị trang đóng feature, không gọi API hoặc phản chiếu token; backend trả `410 Gone` cho create/resend/replacement/preview/submit. Route quản lý vẫn cho phép revoke/hide/delete/withdraw.
- R9. CTA và card đạt tap target tối thiểu 44px, có focus visible, semantic heading/link và contrast WCAG 2.2 AA trên cả theme tối và sáng.
- R10. Copy không hứa “biết mọi câu trả lời”, không khẳng định certainty và không trộn Tarot với chart evidence.

### Acceptance Examples

- AE1. **Given** user có Daily Note, **when** mở `/home`, **then** ba lối và Lá Hỏi xuất hiện trước note; note và các hành động cũ vẫn dùng được.
- AE2. **Given** user chọn `Một người`, **when** tap card, **then** app mở `/radar` và không thu dữ liệu người kia trên Home.
- AE3. **Given** user chọn `Hỏi Lá ngay`, **when** tap CTA, **then** app mở Tarot start với guest-first flow hiện có.
- AE4. **Given** user mở `/la-chung/i/<token>`, **when** route render, **then** không request invite data và chỉ hiển thị thông báo feature đã khép lại.
- AE5. **Given** Daily API lỗi nhưng cache còn, **when** Home render, **then** question router vẫn có và cached note vẫn hiển thị đúng trạng thái.
- AE6. **Given** viewport 320–390px hoặc text zoom 200%, **when** scan Home, **then** không overflow ngang, CTA không bị cắt và thứ tự đọc vẫn đúng.

### Scope Boundaries

**In scope**

- Question-first Home hierarchy, copy và styling.
- Primary Tarot bridge and three existing capability links.
- Lá Chứng route retirement page.
- Unit tests, focused browser QA and a durable product/UX spec.

**Out of scope**

- Tab Tarot mới trong bottom nav.
- Hành trình/case memory, recommendations engine hoặc personalization mới.
- Xóa tables/API/data Lá Chứng, migration retention hoặc data export.
- Thay đổi Tarot engine, Daily content engine, Radar report hoặc auth.

## Technical Plan

### Current Patterns to Preserve

- `apps/web/src/features/home/HomePage.tsx` owns Home data and all Daily Note interactions.
- `apps/web/src/shared/styles/signal-note.css` is the latest Home-specific visual layer; `apps/web/src/shared/styles/global.css` supplies shared app tokens and legacy Home helpers.
- `apps/web/src/features/tarot/TarotPage.tsx` already implements direct guest entry, question notice, encryption disclosure, draw and delete.
- `apps/web/src/app/router.tsx` owns both authenticated-style app routes and public capability routes.
- `apps/web/src/features/home/HomePage.test.tsx` has the strongest Home regression coverage and should remain the main test seam.

### Key Technical Decisions

- KTD7. Build the question router as static semantic links, not stateful cards. This avoids storing intent and keeps Back/navigation predictable.
- KTD8. Add a small `RetiredFeaturePage` component with no query hooks for creation/public paths. Keep explicit owner history/result and receipt-withdrawal routes as a minimal data-rights surface.
- KTD9. Disable new Lá Chứng activity server-side by default while preserving revoke/hide/delete/withdraw contracts. Deletion of implementation and storage remains a separate data-lifecycle change.
- KTD10. Use CSS layout and existing icon system only; no image generation or new remote assets. The selected Cosmic Glass Signal visual language remains the source of truth.

## Implementation Units

### U1. Product and privacy contract

- **Files:** `docs/foundation/la-lanh-question-first-home-spec.md`
- **Approach:** Record Home hierarchy, copy contract, route map, Lá Chứng retirement behavior, data inventory and non-goals. Link to Tarot and reading specs rather than duplicating engine rules.
- **Verification:** Doc review confirms runtime behavior, data collection and route retirement agree.
- **Covers:** R1–R10.

### U2. Home question router and Tarot CTA

- **Files:** `apps/web/src/features/home/HomePage.tsx`, `apps/web/src/shared/styles/signal-note.css`, `apps/web/src/features/home/HomePage.test.tsx`
- **Approach:** Insert a semantic `section` after greeting with one question heading, three result-oriented links and one visually dominant Tarot card. Add a Daily section heading before the existing paper card. Remove the Lá Chứng tile and keep Natal discovery as a single secondary card after existing note interactions.
- **Test scenarios:**
  - Three destination links and Tarot CTA render with exact routes.
  - Question-first section precedes `Note hôm nay` in DOM order.
  - Lá Chứng label/link is absent.
  - Cached/error and Vibe/Aura modes still render.
  - 320px and 390px layouts do not overflow; keyboard focus is visible.
- **Covers:** R1–R6, R9–R10; AE1–AE3, AE5–AE6.

### U3. Safe Lá Chứng retirement and legacy data rights

- **Files:** `apps/web/src/features/la-chung/RetiredFeaturePage.tsx`, `apps/web/src/features/la-chung/ResponseManagementPage.tsx`, `apps/web/src/features/la-chung/InviteHistoryPage.tsx`, `apps/web/src/app/router.tsx`, `apps/api/app/api/v1/routes/la_chung.py`
- **Approach:** Route creation/public paths to one static retirement page without parsing token params. Return `410` from every new-activity endpoint. Keep only owner history/result and receipt withdrawal as explicit data-management routes.
- **Test scenarios:**
  - Creation and public token routes resolve to retirement copy without calling invite API.
  - Cached clients cannot create, resend, replace, preview or submit.
  - Owners can revoke pending invitations and hide/delete results; respondents can withdraw by receipt.
  - Radar public route and all unrelated routes remain unchanged.
- **Covers:** R7–R9; AE4.

### U4. Verification and experience gate

- **Files:** `apps/web/tests/e2e/product-flow.spec.ts` only if existing route smoke needs adjustment; no production code expected.
- **Approach:** Run focused unit tests, web lint/typecheck/build and browser QA at mobile/desktop with both themes. Check copy clarity, first-scan hierarchy, contrast, focus, back navigation and no network call on retired public routes.
- **Verification scenarios:**
  - Home gives a new user an answer to “app này giúp gì?” within the first viewport.
  - Tarot, Natal, Radar and Current Sky routes open without dead ends.
  - Existing Daily note actions still work.
  - Lá Chứng old URLs expose no invite content.

## Security and Privacy Review

- **Data inventory:** U2 adds no collection, storage, analytics or third-party transmission. It only navigates. Tarot continues to collect question/context after a just-in-time notice and stores the encrypted session under its existing retention contract.
- **Capability links:** U3 intentionally avoids calling public Lá Chứng endpoints, so old tokens are neither validated nor reflected. Tokens must not be logged by new code.
- **Retention caveat:** Existing Lá Chứng server records remain until a separate inventory, user-rights and retention migration is approved; surface retirement is not data deletion.
- **Legal baseline:** Vietnam’s Personal Data Protection Law 91/2025/QH15 is effective from 2026-01-01. The implementation follows purpose limitation and minimization by not collecting intent on Home.
- **Accessibility:** Apply WCAG 2.2 AA contrast, 44px targets, semantic links/headings and visible focus.

## Verification Contract

- Focused: `pnpm --filter @la-lanh/web test -- HomePage.test.tsx router.test.tsx`
- Static: `pnpm web:lint && pnpm web:typecheck`
- Build: `pnpm web:build`
- Browser: mobile 390×844 and narrow 320px; dark/light theme; Home, Tarot, Natal, Radar, Current Sky and one old Lá Chứng public URL.
- Experience gate: first viewport has one primary question, one dominant action and no competing feature jargon; copy says what each tap does.

## Definition of Done

- R1–R10 and AE1–AE6 pass.
- Home is question-first and Tarot is visible before Daily Note.
- All three capability links and Tarot route work end to end.
- Daily Note behaviors regressions are covered and existing tests pass.
- Lá Chứng has no active acquisition/response path; only explicit legacy data-management routes remain.
- Docs, runtime copy, security/privacy notes and tests agree.
- No unresolved P0/P1 security or privacy issue; retention cleanup is recorded as deferred, not silently claimed complete.

## Sources

- Internal: `docs/foundation/la-lanh-tarot-engine-spec.md`, `docs/foundation/la-lanh-reading-knowledge-spec.md`, `plans/2026-09-27-2016-feat-contextual-tarot-and-content-studio-plan.md`, `apps/web/src/features/home/HomePage.tsx`, `apps/web/src/features/tarot/TarotPage.tsx`, `apps/web/src/app/router.tsx`.
- External: [Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15](https://vanban.chinhphu.vn/?classid=1&docid=214590&pageid=27160&typegroup=), [OWASP Privacy by Design](https://owasp.org/www-chapter-los-angeles/assets/prez/OWASPLA_prez_2024_01.pdf), [WCAG 2.2](https://www.w3.org/TR/WCAG/).

## Assumptions

- User’s “bỏ Lá Chứng” means stop exposing and acquiring through this feature now; destructive data removal requires a separate, reviewed migration.
- Existing Tarot, Radar, Natal and Current Sky routes are the correct destinations for the three-door model.
- This slice is validated on the web beta but uses app-first responsive components and does not create a web-only information architecture.
