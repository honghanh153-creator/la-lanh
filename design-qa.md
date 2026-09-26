# Design QA — Cosmic Glass Signal

Ngày review: 2026-09-02  
Viewport chính: mobile 390 × 844; contract reflow: 320/390/430px và text scale 200%.

## Kết luận

**Final result: passed cho web/PWA reference của US01–US06 sau vòng sửa 2026-09-03.** Direction 02 — Cosmic Glass Signal đã thay thế quyết định Warm Electric/Editorial cũ trên toàn shell và các màn Welcome, Consent, Birth, Reveal, Home, Note detail, Saved, Share card, Public share, Birth supplement và Profile/Settings. Light/dark dùng cùng cấu trúc, vocabulary và hierarchy.

## Visual source of truth

- Selected reference: `docs/design-directions/home-2026-09-02-v2/02-cosmic-glass-signal.png`
- Design system: `docs/design-directions/home-2026-09-02-v2/COSMIC-GLASS-SYSTEM.md`
- Generated atmospheric asset: `apps/web/public/assets/note/cosmic-glass-sky.png`

## Evidence đã kiểm

- Browser QA toàn happy path ở 390 × 844: guest → consent → DOB → `Vibe · Mềm` → Home → mood → save → detail → supplement exact time/place → `Aura · Mềm`.
- Route transition được kiểm `scrollY=0`; không còn trường hợp màn mới mở ở giữa và tạo cảm giác thiếu flow.
- Home được so trực tiếp với selected reference: paper asset, pin, coral underline, glass frame, mood/action hierarchy và planetary focal point đã khớp lại.
- Share safe link và revoke đều hoạt động; link cũ không còn mở được sau thu hồi.
- Dark/light toggle ở Mình → Cài đặt hoạt động và giữ preference; không đổi nghiệp vụ.
- Không có horizontal overflow hoặc console error ở lượt kiểm cuối.
- Typography: toàn bộ app và card export chỉ dùng Be Vietnam Pro; hierarchy đến từ weight, size và spacing.
- `Vibe` dành cho persona Sun-only; `Aura` chỉ cho snapshot sâu được server xác nhận; mood dùng “Hôm nay bạn thấy sao?”.

## Hệ thống thị giác đã chốt

- Celestial atmosphere là background/focal point, không mang nội dung thiết yếu.
- Opaque reading surface dành cho note, form và privacy copy; glass dành cho control, disclosure và navigation.
- Electric lime là signal chính; coral là event accent; lavender là support. Không rải đồng thời cả ba màu trong mọi card.
- Tối đa năm type token, một hero title/màn và một primary CTA/màn.
- Target sản phẩm ≥44px; focus-visible và Reduce Motion được giữ ở cả hai theme.

## Sai khác có chủ đích so với ảnh direction

- Background được tái tạo thành asset không chứa chữ/UI để nội dung thật vẫn là semantic HTML, đọc được bằng screen reader và co giãn theo text size.
- Form/privacy surfaces đục hơn ảnh concept để bảo đảm khả năng scan và contrast.
- Home giữ Daily Note là primary object; mood và actions thấp hierarchy hơn để tránh quay lại tình trạng rối của mockup đầu.

## Release gate còn mở

- Cần evidence native iOS/Android cho Dynamic Type/font scale, Reduce Transparency, safe-area, VoiceOver/TalkBack và device screenshot.
- Web/PWA QA không thay thế kiểm thử app binary, secure storage hoặc store privacy declarations.

## Audit evidence 2026-09-03

- Full step report: `docs/reviews/cosmic-flow-audit-2026-09-03/README.md`
- Accepted screenshots: `docs/reviews/cosmic-flow-audit-2026-09-03/10-welcome-1.png` đến `23-final-welcome.png`.

---

# Design QA — Moon Field Notes detail

Ngày review: 2026-09-06

State: private Western Moon detail; hồ sơ có giờ/nơi sinh chính xác; Moon Song Ngư; chương 01 mở; dữ liệu chart đóng.

Source visual truth: `docs/design-directions/us07-us09-cosmic-glass-signal-2026-09-04/us07-moon-field-notes-selected.png`.

Implementation: `http://127.0.0.1:5173/insights/moon-sign?tradition=western`.

Implementation screenshot: `docs/reviews/moon-field-notes-2026-09-06/implementation-ce-work-final-390x844.png`.
Combined comparison: `docs/reviews/moon-field-notes-2026-09-06/source-vs-ce-work-final.jpg`.

## Viewport and normalization

- Browser-rendered viewport: 390 × 844 CSS px, DPR 1; implementation screenshot is exactly 390 × 844px.
- Source: 853 × 1844px, normalized to 390 × 844px with Lanczos downsampling. No device frame or browser chrome is included in either side.
- Main page measured 390 × 844px after the final correction. The reading surface, all four chapter controls, provenance disclosure and fixed actions remain visible in the first viewport.
- The combined full-view comparison keeps hero, headline, body, chapter rail, chart disclosure and actions readable. A separate focused crop was not needed because both normalized sides remain legible at original comparison size.

## Findings

- No actionable P0/P1/P2 remains after the user-rejected comparison was treated as blocked and corrected again.
- Fonts/typography: all rendered text uses Be Vietnam Pro. The source hierarchy is preserved with a compact 900-weight headline, 800/900 chapter labels and regular reading copy. The factual Song Ngư headline has different wrapping from the source’s Bọ Cạp example; this is expected dynamic content rather than type drift.
- Spacing/layout rhythm: crescent-to-paper overlap, 20px paper side margins, diagonal torn top edge, continuous chapter rail, single-open chapter and detached bottom actions now follow the selected composition. All sections and persistent controls are visible at 390 × 844.
- Colors/tokens: midnight indigo, warm ivory, smoky lilac, coral line detail and one acid-lime signal are aligned with option 3. Signal color is limited to active chapter and key insight marker.
- Image quality/asset fidelity: the implementation now uses dedicated high-resolution raster assets for the single-moon hero and blank torn paper. There is no second planet, pin, folded corner, dark rectangular mat, emoji, placeholder, CSS drawing or handcrafted SVG replacement.
- Copy/content: source mock uses Moon Bọ Cạp; QA profile correctly renders Moon Song Ngư and sign-specific copy. Page structure and reading hierarchy are unchanged.
- Accessibility: accordion headings contain buttons with `aria-expanded` and `aria-controls`; open panel uses `role=region` with `aria-labelledby`. Bookmark exposes pressed state and live feedback. The action controls remain at least 48px high.

## Comparison history

- Iteration 1 — blocked. [P1] The paper used `dark-editorial-note.jpg`, creating a thick aubergine rectangle, red pin and folded corner absent from the selected source. [P1] The hero contained an extra planet and circular crop. [P2] Main content measured about 1416px high, pushing persistent actions outside the first viewport. Evidence: `docs/reviews/moon-field-notes-2026-09-06/source-vs-implementation.jpg`.
- Fix 1: generated and installed a blank deckled ivory paper asset; removed the old mat/pin/fold treatment; removed the old page background; tightened heading, chapter, marker and evidence rhythm.
- Iteration 2 — blocked. Paper fidelity improved, but the existing moon raster still included a second planet and the page measured 1142px high; CTA was not visible on entry.
- Fix 2: replaced the hero with a dedicated single-crescent raster, changed the hero to a wide uncropped region, moved the paper upward and made the bottom actions persist in the safe visible area.
- Iteration 3 — blocked. The correct asset family and CTA were visible, but only chapters 01–02 appeared above the action; chapter 04 and chart provenance still fell outside the selected source’s above-the-fold composition.
- Fix 3: normalized intro, open-chapter and collapsed-row density; moved paper to y=141.6; reduced action height without reducing its touch target. Post-fix visual evidence: `docs/reviews/moon-field-notes-2026-09-06/source-vs-implementation-final.jpg`.
- Iteration 4 — blocked after user rejection. [P1] The crescent remained over-cropped and the paper top was horizontal; [P2] chapter circles were visually disconnected; [P1] the app could retain the old shell because the service worker used cache-first assets under cache version v3.
- Fix 4: created versioned v2 moon/paper assets; moved the crescent composition upward inside its raster; created the reference-matching diagonal deckled paper; restored the continuous 01–04 timeline; upgraded the app shell to cache v4 and changed shell assets to network-first with offline fallback.
- Iteration 5 — blocked. Scaling the moon inside a transparent container exposed a dark rectangular panel because the global `.flow-page` rule overrode the screen background.
- Fix 5: removed the inner scale-gap treatment, matched the screen background to the raster edge, and used a higher-specificity `.flow-page.moon-reading-page` rule. Post-fix evidence: `docs/reviews/moon-field-notes-2026-09-06/source-vs-ce-work-final.jpg`.

## Interaction and runtime checks

- Browser-tested at 390 × 844: open chapter 02, open chart evidence and toggle bookmark. `aria-expanded`/`aria-pressed` changed correctly.
- Browser warning/error log after interactions: empty.
- Production build passed. Web test suite: 13/13 passed. Service worker syntax check passed.
- Web lint, runtime mock guard and privacy guard passed. At 320px there is no horizontal overflow; the fixed action remains inside the viewport.
- Documentation check: accordion implementation remains aligned with WAI-ARIA APG semantics.
- Security/privacy regression check: this change adds only bundled static visual assets and CSS; it adds no external asset request, new storage, identifier, permission, analytics event or birth-data exposure.
- Code review: skipped (ce-code-review unavailable) — the isolated reviewer timed out while the repository contained a large unrelated WIP set; a manual scoped diff scan found no remaining correctness, cache, privacy or security blocker in the files changed by this correction.

## Follow-up polish

- [P3] The source shows a sign glyph inside the moon. It is intentionally omitted until 12 sign-specific raster variants exist; substituting a text glyph or CSS drawing would violate asset fidelity.
- [P3] Native iOS/Android capture must separately validate safe areas and Dynamic Type; this pass covers the web companion implementation.

final result: passed

---

# Design QA — “Một thử nghiệm nhỏ” trên Home

Ngày review: 2026-09-16
Phạm vi: bản sửa tương phản và hierarchy của khối thử nghiệm trong Note hôm nay.

## Comparison target

- Source visual truth: `docs/design-directions/home-2026-09-02-v2/02-cosmic-glass-signal.png`.
- Implementation route: `http://127.0.0.1:5180/home`.
- Final implementation screenshot: `docs/reviews/design-qa-2026-09-16/implementation-final-copy-390x844.png`; bản contrast trước vòng copy polish vẫn được giữ tại `implementation-after-viewport-390x844@2x.png`.
- State: dark theme; Aura full-synthesis đang active; Context Dial ở `Tự động`; có một thử nghiệm mới; chưa giữ thử nghiệm; không có loading/error/consent sheet.
- Visual contrast pass: 390 × 844 CSS px, `deviceScaleFactor: 2`. Final copy verification chạy lại trong in-app browser ở effective content viewport 376 × 753 px.
- Source: 852 × 1846 px, được hiển thị chuẩn hóa về 390 × 844 trong full-view comparison.
- Final runtime capture: 376 × 753 px; focused crop: 344 × 410 px.
- Focused source crop: 720 × 560 px; chỉ dùng để đối chiếu cách source dùng dark ink/accent trên giấy sáng, vì source gốc có trước tính năng thử nghiệm.

## Full-view comparison evidence

- Review page cập nhật cuối: `docs/reviews/design-qa-2026-09-16/comparison.html`; static combined comparison trước copy polish vẫn ở `comparison-full-source-vs-after.png`.
- Cosmic Glass atmosphere, cream paper, single-font hierarchy và electric lime CTA vẫn cùng direction.
- Context Dial làm Note bắt đầu thấp hơn source. Đây là sai khác có chủ đích từ requirement “việc gì đang chiếm sóng”, không phát sinh từ lần sửa này và không làm nội dung hay persistent navigation tràn ngang.

## Focused region comparison evidence

- Focus cuối sau contrast + copy polish: `docs/reviews/design-qa-2026-09-16/implementation-final-experiment-focus.png`.
- Before vs after contrast: `docs/reviews/design-qa-2026-09-16/comparison-iteration-before-vs-after.png`.
- Source dùng ink tím/đen đậm trên giấy sáng và giữ màu electric cho accent. Implementation sau sửa áp dụng cùng nguyên tắc: nhãn dùng deep-leaf ink; lime vẫn dành cho CTA có chữ tối.

## Findings

- [Resolved P1] Nhãn “Một thử nghiệm nhỏ” gần như mất trên nền sáng.
  - Location: Home → Note hôm nay → `.reading-content__action > .eyebrow`; `apps/web/src/shared/styles/signal-note.css`.
  - Evidence: trước sửa, chữ `#D8FA19` trên nền `#F1F7CF` chỉ đạt khoảng 1.08:1; đường nhấn dùng cùng lime cũng gần như biến mất. Source dùng chữ ink đậm trên giấy sáng.
  - Impact: người dùng khó scan tên khối, đặc biệt khi giảm sáng màn hình hoặc có thị lực tương phản thấp.
  - Fix: chuyển nhãn sang deep leaf `#405C00`, đường nhấn sang `#5A7510`, thu label về 0.72rem để trả hierarchy cho hành động chính; contrast chữ đạt khoảng 6.89:1.
- Không còn P0/P1/P2 có thể hành động trong phạm vi component này.

## Required fidelity surfaces

- Fonts/typography: Be Vietnam Pro là font duy nhất; label 800 weight, 0.72rem, tracking 0.075em; action chính vẫn có weight và line-height đủ đọc. Không có fallback bất ngờ, tràn hoặc cắt chữ.
- Spacing/layout rhythm: component giảm từ khoảng 314.59 xuống 312.66 CSS px; padding, cue inset và tap target không đổi; không có horizontal overflow (`scrollWidth = clientWidth = 390`).
- Colors/tokens: deep leaf được dùng làm ink/border trên giấy sáng; lime vẫn dùng cho CTA với text `#17152C` (contrast khoảng 14.40:1). Không thêm màu mới ngoài nhánh xanh lá đã có trong Aura preview.
- Image quality/assets: cosmic sky và paper texture vẫn là bundled raster assets, sắc nét ở DPR 2; lần sửa không thay, rasterize hoặc thay thế asset.
- Copy/content: hierarchy cuối là label “Một thử nghiệm nhỏ” → heading “Thử rồi tự kiểm chứng” → việc cần thử → điều cần quan sát → quyền dừng. Hai nhãn không còn lặp nghĩa.
- Accessibility/interaction: CTA browser-tested từ “Giữ để thử hôm nay” sang trạng thái đã giữ và hiện “Bỏ giữ việc này”; không có console error hoặc page error.

## Comparison history

- Iteration 1 — blocked. [P1] Acid lime trên giấy xanh-kem đạt khoảng 1.08:1; label và left rule không đọc rõ. Evidence: `implementation-before-experiment@2x.png` và phần trái của `comparison-iteration-before-vs-after.png`.
- Fix 1: thêm paper-surface override có specificity cao hơn dark-theme eyebrow rule; dùng `#405C00` cho label, `#5A7510` cho border/cue; giảm cỡ label để rõ hierarchy.
- Iteration 2 — passed. Computed color là `rgb(64, 92, 0)` trên `rgb(241, 247, 207)`, contrast khoảng 6.89:1; full view và focus view không còn mismatch P0/P1/P2. Evidence: `implementation-after-experiment@2x.png`, `comparison-focus-source-vs-after.png` và phần phải của `comparison-iteration-before-vs-after.png`.

## Verification

- Accessibility reference: W3C WCAG 2.2 SC 1.4.3 requires at least 4.5:1 for normal-sized text; the post-fix label is about 6.89:1 (`https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html`).
- Browser-rendered capture ở 390 × 844 CSS px/DPR 2; primary CTA state transition pass; console errors: 0; page errors: 0.
- Production build pass.
- Web lint pass.
- Web typecheck pass.
- Web tests: 22 files, 67 tests pass.

## Follow-up polish

- [Resolved P3] Đổi heading “Thử một việc nhỏ” thành “Thử rồi tự kiểm chứng”, làm rõ CTA giữ lại một thử nghiệm để người dùng tự quan sát thay vì coi đây là lời khuyên phải làm. Evidence cuối: `implementation-final-copy-390x844.png`, `implementation-final-experiment.png` và crop `implementation-final-experiment-focus.png`.

final result: passed

---

# Design QA — final app flow US01–US09

Ngày review: 2026-09-07; xác nhận lại sau final build: 2026-09-08
Viewport kiểm trực tiếp: 390 × 844.

## Kết quả

- Cosmic Glass Signal giữ đúng midnight/lavender/acid-lime/coral hierarchy; light mode chuyển sang lavender mist nhưng vẫn cùng design language.
- Toàn app dùng Be Vietnam Pro; Home đo được đúng một font stack và không horizontal overflow.
- Vibe và Aura khác nhau ngay ở source chip, headline, body copy và gift activation; full chart không tự thay note đang đọc.
- Bản đồ Lá ưu tiên tổng hòa trước dữ liệu kỹ thuật; Western/Jyotish và cách tính là control rõ ràng, không trộn hai hệ.
- Lá Chứng đặt privacy/checkpoint đúng thời điểm tạo link; public responder không cần tài khoản và không có free-text input.
- Dark/light toggle nằm trong Mình → Giao diện, có role switch và label trạng thái.
- Profile sau khi mở Aura ghi đúng nguồn “tổng hòa nhiều hành tinh, nhà và góc chiếu”, không quay lại nhãn Mặt Trời của Vibe.
- Fresh QA path được chạy lại trên schema mới: Welcome → Consent → ngày sinh → Vibe → Home → giờ/nơi sinh → consent sâu → quà Aura → activate → Profile → Western/Jyotish.
- Console warning/error: không có trong lượt browser QA cuối.

## Sai khác có chủ đích với concept ảnh

- UI production tiết chế texture và electric accent để scan nhanh trên màn app nhỏ.
- Reading copy là semantic HTML trên surface đủ tương phản; asset chỉ tạo atmosphere.
- Bottom navigation và primary action giữ touch target app; visual density thấp hơn ảnh poster tham chiếu.

## Gate còn mở

Native screenshot và accessibility QA trên signed iOS/Android chưa thể chạy trên máy hiện tại. Web/PWA evidence không thay thế safe-area, Dynamic Type, VoiceOver/TalkBack và store binary review.

final result: passed for local web/PWA reference; native release evidence pending

---

# Design QA — Trạm Bắt Sóng + Personal Signal Daily Note

Ngày review: 2026-09-14
Viewport đối chiếu: 390 × 844 CSS px, DPR 2.
Visual authority: `docs/design-directions/signal-note-2026-09-14/`.

## Kết quả cuối

- `00/02 → 01/02 → 02/02` bám đúng nhịp Trạm Bắt Sóng: một trust/consent decision, một composite DOB form, một Vibe reveal; không login wall, carousel hoặc fake loading.
- Home mặc định mở ở bản dark Cosmic Glass đã chọn; light vẫn là lựa chọn chủ động trong `Mình → Cài đặt`, không còn tự làm nhạt direction ở lần mở đầu.
- Toàn bộ bốn capture chỉ dùng Be Vietnam Pro. Không phát hiện font thứ hai, console error hoặc horizontal overflow.
- Context Dial giữ bốn góc scan nhanh giống reference; `Năng lượng` và `Chăm mình` nằm trong disclosure `Thêm 2 góc` để đủ feature contract mà không làm rối first scan.
- Cream Note là điểm nhìn chính. Compact Home chỉ giữ hook, biểu hiện đời thường, một micro-action, disclosure chứng cứ và boundary `Chart giữ nguyên · chỉ đổi góc đời thường`; nội dung đầy đủ vẫn ở `Đọc note đầy đủ`.
- Cùng một chart, đổi `Tình cảm` làm manifestation/action đổi rõ; URL vẫn `/home`, chart/evidence không đổi và không có context preference trong local storage.
- Mood, chia sẻ/lưu, mở Aura, Bản đồ Lá và Lá Chứng đều còn trên giao diện nhưng thấp hierarchy hơn Note.
- Bottom nav cố định là sai khác có chủ đích cho app runtime. Page có safe bottom padding để nội dung có thể cuộn ra khỏi nav; full-page QA capture có thể ghi lại nav giữa ảnh vì nó là fixed UI.

## Evidence

- Source onboarding: `docs/design-directions/signal-note-2026-09-14/onboarding-tram-bat-song-reference.png`.
- Source Home: `docs/design-directions/signal-note-2026-09-14/daily-note-personal-signal-reference.png`.
- Final captures: `qa-welcome-390x844.png`, `qa-birth-390x844.png`, `qa-reveal-390x844.png`, `qa-home-390x844.png` trong cùng thư mục.
- Browser flow: 8/8 pass trên mobile Chromium và desktop Chromium.
- Web unit/component: 51/51 pass; lint, typecheck và production build pass.

## Findings đã sửa

- [P1] Home mới từng khởi tạo light mặc định, làm mất chiều sâu của source dark. Đã đổi default thành dark; light chỉ được lưu khi user chủ động toggle.
- [P1] Home từng render toàn bộ long-form reading ngay trong card, làm page khó scan. Đã tách compact projection và giữ long form ở detail.
- [P2] Context Dial 2×2 cao hơn source. Ở 390–699px bốn góc chính chuyển thành một hàng; hai góc bổ sung dùng progressive disclosure.
- [P2] Browser-flow test dùng text locator không có scope và vướng hai nhãn giống nhau. Đã scope vào region `Note hôm nay`; luồng thật và test đều pass.

## Release boundary

Visual QA cho shared app UI đã pass. Native store release vẫn là No-Go tới khi có API HTTPS versioned thật, sync lại bundle vào iOS/Android và chạy simulator/device checks cho safe area, Dynamic Type, VoiceOver/TalkBack, cookies/CSRF và lifecycle. Không dùng host giả để tạo bằng chứng release.

final result: passed
