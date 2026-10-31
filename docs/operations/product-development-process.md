# Quy trình phát triển sản phẩm Lá Lành

Owner yêu cầu ngày 31.10.2026: **research trên GitHub trước, rồi mới quyết định xử lý**, và mọi việc
phải đi qua đủ các cổng (tài liệu, UI/UX, BE và kiến trúc, FE, QC, release, bảo mật, data privacy…).

File này nối các tài liệu sẵn có thành một quy trình. Nó không thay thế chúng:

- Luật chung: `AGENTS.md` (ba cổng tài liệu, bảo mật, privacy).
- Quyết định: `docs/operations/decision-checklist.md` (Q1–Q5).
- Vòng tự động: `docs/operations/collab-auto-loop-plan.md`.
- Sản phẩm: `docs/foundation/la-lanh-prd.md`, `la-lanh-srs.md`, `la-lanh-product-plan-v2.md`,
  `docs/user-stories/`, spec từng tính năng trong `docs/foundation/`.
- Release: `hetzner-supabase-release-runbook.md`, `web-beta-release-runbook.md`,
  `chart-synthesis-release-runbook.md`, `luna-rewrite-release-runbook.md`,
  `user-experience-release-gate.md`, `content-matrix-release-gate.md`.
- Privacy và pháp lý: `docs/legal/` (data map, Swiss Ephemeris AGPL, nguồn Tarot).

```
Nhận việc → 1. Research (GitHub + nguồn chính thức) → 2. Quyết định → 3. Thiết kế qua các cổng
         → 4. Làm (PR nhỏ) → 5. QC + review tự động → 6. Merge integration → 7. Release (owner)
```

## 0. Phân loại việc theo mức rủi ro

Mức quyết định cổng nào bắt buộc (bảng mục 4). Khi phân vân, chọn mức cao hơn.

| Mức | Khi nào | Ví dụ |
|---|---|---|
| **S** nhỏ | Sửa lỗi cục bộ, không đổi hành vi người dùng thấy, không đổi dữ liệu/API | lỗi định dạng, test flaky, tooling của vòng tự động |
| **M** vừa | Đổi hành vi hoặc giao diện trong một tính năng có sẵn; không thêm dữ liệu cá nhân, không đổi API công khai | #144 Jyotish 503, #146 footer, #147 thẻ hành tinh |
| **L** lớn | Tính năng mới, đổi API/contract, migration, dữ liệu cá nhân mới, bên thứ ba/AI, chia sẻ công khai, thanh toán | US-23 sửa ngày sinh, US-24 người thật bốc Tarot, xuất dữ liệu |

## 1. Research trên GitHub và nguồn chính thức (bắt buộc mọi mức)

Mục đích: không làm lại điều đã có, không đi ngược quyết định đã chốt, không bỏ sót rủi ro đã
được review trước đó, và học từ cách người khác đã giải.

### 1a. Trong repo của mình (S, M, L)

| Tra gì | Lệnh gợi ý |
|---|---|
| Issue, PR liên quan (kể cả đã đóng) | `gh search issues "<từ khoá>" --repo honghanh153-creator/la-lanh --include-prs --state all` |
| Verdict và phát hiện cũ (P0–P3, fix-forward) | `gh issue list --label fix-forward --state all`; đọc comment `Review verdict` của PR cùng khu vực |
| Quyết định đã chốt | plan §2, `docs/decisions/`, hub #2, `decision-checklist.md` |
| Yêu cầu sản phẩm | US và AC trong `docs/user-stories/`, PRD, SRS, spec trong `docs/foundation/` |
| Code và test hiện có | `git grep`, `git log -S "<chuỗi>"`, test cùng module |
| Lịch sử release, sự cố | `docs/reviews/production-release-*`, issue `ops-alert` |

### 1b. Bên ngoài (M khi cần, L bắt buộc)

| Tra gì | Ở đâu |
|---|---|
| Cách giải đã có (prior art), thư viện | `gh search repos "<chủ đề>" --sort stars`, `gh search code "<API/pattern>"`; ưu tiên dự án duy trì tích cực, license tương thích **AGPL-3.0** của repo |
| Chuẩn và tài liệu chính thức | tài liệu framework/thư viện, OWASP ASVS (web) và MASVS/MASTG (mobile), WCAG 2.2 AA, Apple App Review / Google Play Data Safety, Luật 91/2025/QH15 và Nghị định 356/2025 (dữ liệu cá nhân) |
| Sản phẩm tương tự | chỉ để hiểu trải nghiệm; không chép nội dung hay tài sản có bản quyền |

Không dán dữ liệu người dùng, ngày giờ sinh thật hay câu hỏi Tarot thật vào truy vấn tìm kiếm.

### 1c. Kết quả: "Research note" trên issue task

```
Research note (<agent>, <ngày>)
- Mức: S | M | L — lý do
- Đã có trong repo: <issue/PR/doc/test liên quan, quyết định đã chốt>
- Bên ngoài: <prior art, chuẩn, link chính thức> (L)
- Lựa chọn: A … / B … — ưu, nhược, rủi ro
- Đề xuất: … — vì sao
- Cổng bị ảnh hưởng: G1 … G10
- Câu hỏi cho owner (chỉ khi Q1–Q5 có "có")
```

## 2. Quyết định

Chạy Q1–Q5 của `decision-checklist.md`. Tất cả "không" → agent tự quyết, làm và báo lại. Có "có" → hỏi
owner một lần, kèm lựa chọn đánh số và khuyến nghị; trong lúc chờ thì làm việc khác.

Mức L hoặc mọi thay đổi kiến trúc: ghi một quyết định ngắn vào `docs/decisions/YYYY-MM-DD-<chủ-đề>.md`
(bối cảnh, lựa chọn đã cân nhắc, quyết định, hệ quả, cách hoàn tác).

## 3. Các cổng

Mỗi cổng có: việc phải làm, bằng chứng để trong PR, phần nào máy kiểm tự động.

### G1. Tài liệu và hợp đồng sản phẩm

- Nối thay đổi với US/AC cụ thể; nếu thiếu thì ghi rõ khoảng trống.
- Cập nhật PRD/SRS/spec/US khi hành vi đổi; API contract, migration, copy, privacy copy và runbook
  phải khớp code.
- Bằng chứng: link US/AC, đoạn tài liệu đã sửa. Máy: `contracts:check` (OpenAPI và TS sinh ra).

### G2. UI/UX (trước khi code giao diện)

- Phác luồng và mọi trạng thái: mặc định, đang tải, rỗng, lỗi, không có quyền, offline, dữ liệu kém chính xác.
- Kiểm 360 px và 390 px; bàn phím; không chỉ dựa vào màu; WCAG 2.2 AA.
- Câu hỏi của `user-experience-release-gate.md` (5 giây hiểu màn hình làm gì, tiêu đề không lặp,
  hành động cụ thể, `Lưu ý` tách riêng).
- Chuẩn câu chữ: `la-lanh-plain-vietnamese-content-standard.md`; north star "êm, vui, được hiểu".
- Bằng chứng: ảnh chụp hoặc mô tả trạng thái, kết quả kiểm 360/390. Máy: `experience:audit`, e2e.

### G3. Nội dung và câu chữ

- Câu mới mà người dùng thấy cần owner duyệt (Q2); không ngôn ngữ định mệnh hay dự đoán chắc chắn.
- Sau duyệt: cập nhật `fallback-approval.json` khi đụng bảng nội dung.
- Bằng chứng: bảng trước/sau, câu owner duyệt. Máy: `content:audit`, `content:review`,
  `grammar:check`, `fallback_approval --check`, `tarot:audit`.

### G4. BE và kiến trúc

- Giữ ranh giới module (modular monolith, SRS §1.2); không gọi LLM đồng bộ trong request path (SRS §6.2).
- API: đổi schema thì sinh lại OpenAPI/TS và giữ tương thích hoặc ghi rõ phá vỡ.
- Migration: có đường lùi, chạy được với quyền backend tối thiểu, không mất dữ liệu; thứ tự migrate/deploy ghi trong PR.
- Model lưu trữ: chú ý "rollback floor" (bản ghi mới phải đọc được khi quay về code cũ), ví dụ `ReadingCandidate`.
- Hiệu năng và chi phí: đo khi đụng vòng lặp lớn, batch, hay lời gọi trả phí.
- Bằng chứng: quyết định kiến trúc (L), kế hoạch migration và rollback. Máy: `api:lint`, `api:typecheck`, `api:test`.

### G5. FE

- Dùng contract sinh ra, không tự gõ kiểu API; xử lý đủ trạng thái của G2.
- Không lưu dữ liệu cá nhân trong Web Storage hay URL; không lộ thông tin kỹ thuật cho người dùng.
- Bằng chứng: test component cho trạng thái chính. Máy: `web:lint`, `web:typecheck`, `web:test`.

### G6. QC

- Lỗi: tái hiện trước (dữ liệu tổng hợp), test hồi quy **đỏ trên code cũ, xanh trên code mới**.
- Tính năng: test theo từng AC, biên (giờ khoảng, không có giờ, múi giờ, dữ liệu trống, đồng thời, rút đồng ý).
- Author check: `pnpm check` đầy đủ trên đúng head (vòng tự động). Mức L: kịch bản QC thủ công ngắn
  (luồng chính trên 360/390 px) ghi trong PR.
- Bằng chứng: tên test hồi quy, `Author check: PASS @ <SHA>`.

### G7. Bảo mật

- `AGENTS.md` §2: phiên và quyền sở hữu, phân quyền, CSRF, kiểm tra đầu vào, giới hạn lạm dụng, mã hoá
  và khoá, log, endpoint công khai, link chia sẻ, phụ thuộc, lưu trữ, mạng, lộ lỗi, đường xoá.
- Mức L: threat model ngắn cho luồng dữ liệu mới và đường hỏng/rollback; web theo OWASP ASVS, mobile
  theo MASVS/MASTG (quyền nền tảng, lưu trữ native).
- Không ship P0/P1. Bằng chứng: mục Security trong PR. Máy: `verify:runtime`, guard trong `pnpm check`, Codex review.

### G8. Data privacy

- `AGENTS.md` §3: liệt kê mọi trường dữ liệu cá nhân được thu, suy ra, gửi, lưu, cache, log, chia sẻ,
  xuất hay gửi bên thứ ba; mục đích, tối thiểu hoá, đồng ý đúng lúc, thời hạn lưu, mã hoá, quyền truy
  cập, rút đồng ý và xoá, quyền chủ thể dữ liệu.
- Ngày/giờ/nơi sinh, toạ độ, quan hệ, mood, định danh, token, hồ sơ chiêm tinh suy ra: luôn xem kỹ.
- Đồng bộ data map (`docs/legal/store-privacy-data-map.md`), privacy copy trong app, Apple App Privacy,
  Google Play Data Safety, chính sách privacy.
- Kiểm lại Luật 91/2025/QH15 và Nghị định 356/2025 từ nguồn chính thức khi đụng dữ liệu cá nhân.
- Bằng chứng: bảng dữ liệu trước/sau trong PR. Máy: `verify:runtime` (gồm `scripts/verify-privacy.mjs`), canary trong test.

### G9. Release và vận hành (chỉ owner ra lệnh)

- Merge `collab/integration` → `main` và deploy chỉ khi owner ra lệnh, theo runbook tương ứng.
- Trước release: `pnpm check` trên commit release, cổng UX và cổng content, kế hoạch rollback, thứ tự migration,
  theo dõi sau deploy, receipt release trong `docs/reviews/production-release-*`.
- Bằng chứng: receipt release. Máy: CI Compose proof (O01) khi có.

### G10. Chi phí, license và bên thứ ba

- Lời gọi trả phí (Luna, Codex) có trần; con số ngân sách Luna không đưa lên repo public.
- License: tương thích AGPL-3.0 (Swiss Ephemeris); nguồn Tarot theo `tarot-source-rights-notes.md`.
- Bên thứ ba mới (SDK, API): G8 và data map trước khi dùng.

## 4. Cổng nào bắt buộc theo mức

| Cổng | S | M | L |
|---|---|---|---|
| Research 1a (trong repo) | ✓ | ✓ | ✓ |
| Research 1b (bên ngoài) | — | khi có chuẩn/thư viện mới | ✓ |
| G1 Tài liệu | khi đổi hành vi | ✓ | ✓ + cập nhật spec/US |
| G2 UI/UX | — | nếu đụng giao diện | ✓ trước khi code |
| G3 Câu chữ | — | nếu có câu mới | ✓ |
| G4 BE/kiến trúc | nếu đụng BE | nếu đụng BE | ✓ + quyết định kiến trúc |
| G5 FE | nếu đụng FE | nếu đụng FE | ✓ |
| G6 QC | test hồi quy | ✓ | ✓ + kịch bản QC thủ công |
| G7 Bảo mật | checklist nhanh | ✓ | ✓ + threat model |
| G8 Privacy | checklist nhanh | ✓ | ✓ + data map, nhãn store |
| G9 Release | — | — | owner ra lệnh |
| G10 Chi phí/license | — | nếu có | ✓ |

"Checklist nhanh" là trả lời một dòng trong PR: thay đổi này có đụng tới phiên, quyền, dữ liệu cá nhân
hay log không; nếu có thì nâng lên M.

## 5. Bằng chứng ở đâu

- Research note: comment trên issue task.
- Mức và cổng: PR body (mục "Cổng") ghi mức và bằng chứng từng cổng bắt buộc.
- Codex review tự động đọc file này: kiểm PR có đủ bằng chứng cho mức đã khai; thiếu cổng bắt buộc là
  REQUEST_CHANGES (P1 nếu là G7/G8, P2 nếu khác).

Chuyển tiếp: PR mở trước 01.11.2026 không bắt buộc khai mức và mục "Cổng"; Codex vẫn review theo ba cổng
của `AGENTS.md` như trước. PR mở từ 01.11.2026 theo đủ file này.

## 6. Khi nào cần owner

Chỉ ở: câu chữ mới (G3), dữ liệu cá nhân mới hoặc đổi mục đích (G8), hướng sản phẩm, chi phí, và release (G9).
Mọi thứ khác agent tự làm theo file này và checklist quyết định.
