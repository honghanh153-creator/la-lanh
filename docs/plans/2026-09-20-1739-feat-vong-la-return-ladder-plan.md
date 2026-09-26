---
title: "Vòng Lá return ladder cho ba lần ghé chưa chuyển đổi"
type: feat
date: 2026-09-20
artifact_contract: ce-unified-plan/v1
product_contract_source: conversation
execution: code
---

# Vòng Lá return ladder cho ba lần ghé chưa chuyển đổi

## Goal Capsule

### Objective

Làm trang giới thiệu Vòng Lá hấp dẫn dần qua ba phiên ghé chưa tạo hồ sơ, nhưng vẫn nói đúng sản phẩm đang chạy: ưu tiên và ranh giới cứng đi trước, birth chart giải thích kiểu kết nối, request một phía luôn kín và chỉ mutual mới mở chat.

### Means

Dùng một ladder nội dung ba bậc trên `/vong-la`, đếm tối đa một lần trong mỗi phiên app bằng trạng thái cục bộ tối giản; cùng một CTA dẫn tới flow thật `/vong-la/setup?start=profile`. Khi hồ sơ ghép lưu thành công, ladder dừng tăng.

### Stop conditions

- Không gắn CTA `Check hai đứa` vào Lá Chứng hoặc một route giả; Lá Ghép US-12/13 chưa có runtime end-to-end.
- Không gửi visit state, timestamp, ngày sinh, account id hoặc matching data lên server/analytics.
- Không thay eligibility, consent, verification, synastry hay matching ranking trong work này.

### Success signal

Người dùng mới hiểu Vòng Lá là gì và vì sao khác swipe; người quay lại lần hai/ba nhận copy cụ thể và trực diện hơn; mọi CTA mở flow tạo hồ sơ hiện có; reload hoặc quay lại trong cùng phiên không làm copy nhảy bậc.

## Product Contract

### Key Decisions

- **Ba lần ghé dùng ba mức thuyết phục: tò mò → lợi ích cụ thể → trực diện.** (session-settled: user-approved) Governs R1–R3.
- **Đếm theo phiên app, chỉ trên thiết bị và dừng ở bậc 3.** (session-settled: user-approved) Governs R4–R7.
- **Chỉ CTA vào flow Vòng Lá đang hoạt động.** (session-settled: user-approved) Governs R8–R9.
- **Lá Ghép hai người là nhánh riêng, không giả lập trong landing này.** (session-settled: user-approved) Governs R10.

### Requirements

- **R1.** Phiên ghé đầu dùng hook tò mò, giải thích đây là năm gợi ý có lý do chứ không phải feed vô tận.
- **R2.** Phiên ghé thứ hai gọi rõ ba lợi ích đời thường: dễ bắt chuyện, điểm dễ lệch nhịp và ranh giới.
- **R3.** Từ phiên thứ ba, copy trực diện hơn nhưng không gây áp lực, FOMO hoặc tuyên bố app biết người dùng đã quay lại.
- **R4.** Một phiên trình duyệt/app chỉ ghi nhận một exposure dù reload, React Strict Mode hoặc đi rồi quay lại route.
- **R5.** Exposure tăng 1 → 2 → 3 và giữ ở 3; dữ liệu hỏng/không hợp lệ phải fail safe về bậc 1.
- **R6.** Bản ghi chỉ gồm số bậc và cờ conversion; session marker chỉ tồn tại trong `sessionStorage`.
- **R7.** Xóa dữ liệu trên thiết bị phải xóa cả local exposure và session marker.
- **R8.** Primary CTA ở cả ba bậc dẫn tới `/vong-la/setup?start=profile`; microcopy nói đúng về thời gian, consent và privacy hiện tại.
- **R9.** Lưu hồ sơ ghép thành công đánh dấu conversion; các lần ghé sau không tăng bậc nữa.
- **R10.** Không hiển thị CTA kiểm tra cặp đôi cho đến khi US-12/13 có endpoint, state và QA end-to-end riêng.

### Copy ladder

| Bậc | Vai trò | Eyebrow | Headline | CTA |
|---|---|---|---|---|
| 1 | Gợi tò mò | `GU CỦA BẠN ĐÂU CHỈ CÓ MỘT KIỂU` | `Có kiểu người nào cứ làm bạn nghĩ mãi?` | `Xem gu mình hợp ai` |
| 2 | Nêu giá trị | `KHÔNG CHỈ LÀ HỢP CUNG` | `Bắt sóng ở đâu? Dễ cấn ở chỗ nào?` | `Tìm người hợp gu` |
| 3 | Kêu gọi trực diện | `ĐỪNG SWIPE THÊM VỘI` | `Thử một vòng có lý do.` | `Mở Vòng Lá` |

### Acceptance Examples

- **AE1:** Given chưa có state, when mở `/vong-la`, then thấy bậc 1 và CTA đúng route setup.
- **AE2:** Given reload/cùng phiên, when mở lại landing, then vẫn thấy cùng bậc.
- **AE3:** Given bắt đầu phiên mới lần hai/lần ba, when mở landing, then thấy lần lượt bậc 2/bậc 3; lần bốn vẫn là bậc 3.
- **AE4:** Given local state hỏng hoặc storage bị chặn, when mở landing, then trang vẫn hoạt động bằng bậc 1.
- **AE5:** Given lưu hồ sơ thành công, when mở landing ở phiên sau, then bậc không tiếp tục tăng.
- **AE6:** Given xóa dữ liệu trên thiết bị, when mở landing lại, then ladder bắt đầu từ bậc 1.

### Definition of Done

- Ba bậc copy render đúng và CTA vào flow thật.
- Exposure helper có test happy path, same-session, clamp, malformed storage, converted và storage failure.
- Profile save đánh dấu conversion; local-data cleanup xóa ladder.
- Unit tests, lint, typecheck và production build qua; UI kiểm tra ở viewport app 390×844.
- Docs US-14, security review và privacy inventory khớp runtime.

## Planning Contract

### Key Technical Decisions

- **KTD1 — Helper storage thuần, phòng thủ với storage failure.** Module matching riêng sở hữu parse/clamp/read/write; UI không chạm trực tiếp JSON.
- **KTD2 — Session marker là constant, không dùng UUID/timestamp.** Chỉ cần biết exposure của phiên hiện tại đã được ghi; sessionStorage tự phân tách phiên và giảm dữ liệu không cần thiết.
- **KTD3 — Conversion là một cờ trong local record.** Save profile thành công ghi cờ trước khi refetch; lỗi ghi local không được làm hỏng mutation thành công.
- **KTD4 — Shared React source là source of truth cho app và web.** Sau QA web, build được đồng bộ vào Capacitor để app nhận cùng behavior.

### Implementation Units

#### U1 — Exposure state và tests

- **Files:** `apps/web/src/features/matching/matchingIntroExposure.ts`, test cùng tên.
- **Work:** parse/clamp, one-per-session register, converted freeze, clear/reset; graceful storage failure.
- **Verification:** focused Vitest với first/same/new session, cap 3, malformed, converted, thrown storage.

#### U2 — Dynamic landing copy

- **Files:** `MatchingLandingPage.tsx`, `MatchingLandingPage.test.tsx`, chỉnh CSS tối thiểu nếu cần.
- **Work:** map ba variant vào hero/CTA/microcopy; giữ value, flow và privacy sections hiện có.
- **Verification:** component tests cho cả ba bậc và CTA route; visual mobile 390×844.

#### U3 — Conversion và deletion lifecycle

- **Files:** `MatchingPage.tsx`, `MatchingPage.test.tsx`, `clearPersonalData.ts`, `clearPersonalData.test.ts`.
- **Work:** mark converted sau save thành công; xóa local/session ladder khi user xóa dữ liệu.
- **Verification:** save test kiểm tra cờ; cleanup test kiểm tra cả hai key.

#### U4 — Contract, QA và app parity

- **Files:** `docs/user-stories/US-14-chuan-bi-profile-matching-ready.md`, build artifacts qua quy trình mobile sync.
- **Work:** bổ sung AC return ladder, privacy inventory và boundary US-12/13; chạy lint/typecheck/test/build và browser QA.
- **Verification:** focused + full web checks; mobile config guard/sync khi API base hợp lệ.

### Security and Privacy Review

- State là input không tin cậy: JSON parse trong `try/catch`, kiểm type, clamp 1–3, không render HTML động.
- Không có network call, cookie, account linkage, timestamp, fingerprint hoặc cross-device sync.
- Không dùng exposure để thay eligibility, ranking, consent hoặc verification.
- Local delete phải xóa state; privacy policy/store declarations chỉ cần mô tả nếu runtime sau này gửi dữ liệu off-device.
- Current official references: Apple App Privacy on on-device-only processing; Google Play Data Safety on data processed only on-device; Việt Nam Personal Data Protection Law 91/2025/QH15 effective 2026-01-01.

### Deferred work

- US-12/13 Lá Ghép cần API pair chart/synastry, subject consent, invite ownership, revocation và UI riêng trước khi landing có thể dùng CTA `Check hai đứa`.
- Analytics/A-B testing của ladder không nằm trong scope; nếu bổ sung phải có contract consent và data declaration riêng.
