# Kế hoạch hoàn thiện Vòng Lá và sản phẩm Lá Lành

Ngày: 2026-09-17  
Trạng thái: implementation-ready  
Phạm vi: US-14 đến US-18, cổng xác thực US-19, app Capacitor là sản phẩm chính

## 1. Goal capsule

Biến nền tảng relationship engine hiện có thành một hành trình matching dùng dữ liệu thật, an toàn và có cá tính: người dùng chỉ đăng nhập khi vào Vòng Lá; khai intent và consent riêng; nhận tối đa năm kiểu kết nối khác nhau; request kín; chỉ mở chat khi mutual; luôn có block/report; nhận recap không gây cảm giác bị chấm điểm hay bị từ chối.

Thành công khi:

- Luồng từ `/vong-la` đến readiness, vòng tuần, request, mutual, Lá Nối/chat và recap chạy trên API + database thật.
- Không có candidate giả, `% hợp nhau`, GPS/khoảng cách số, hay suy đoán intent từ hành vi.
- Synastry là lớp lựa chọn trước mutual; Composite chỉ là bonus sau mutual; Davison chỉ dùng khi đủ giờ/nơi sinh và có consent phù hợp.
- Trải nghiệm chạy trong app Capacitor, web dùng chung codebase và đóng vai trò companion/review surface.
- Ảnh/xác minh và moderation không được mô phỏng là “đã duyệt”; production fail-closed cho đến khi có quy trình/provider thật.

## 2. Product contract

### 2.1 Người dùng và giá trị

- Người đã dùng Daily Note có thể vào Vòng Lá mà không bị ép đăng nhập từ onboarding.
- Vòng Lá không hứa “định mệnh” hay xếp hạng con người. Mỗi lá trả lời: *kiểu kết nối nào đáng thử, bằng tín hiệu nào, và nên tự kiểm chứng ra sao*.
- Weekly intent chỉ điều chỉnh cách phối năm lá, không nới điều kiện tuổi, mục đích, khu vực, block hay an toàn.

### 2.2 Quy tắc bất biến

1. 18+ và age gate đủ mạnh trước mọi chức năng matching/chat.
2. Matching consent tách riêng, có version, purpose, granted/withdrawn time.
3. Chỉ lưu vùng thô (thành phố/quận); không thu GPS cho matching.
4. Request ẩn danh cho đến mutual; không có trạng thái “bị từ chối”.
5. Chat chỉ sau mutual; block/report luôn nhìn thấy, có hiệu lực tức thời.
6. Không đưa dữ liệu sinh, chart thô, mood, nội dung chat hoặc popularity vào ranker.
7. API riêng tư trả `Cache-Control: no-store`; mọi mutation có CSRF và owner authorization.
8. Account deletion phải xóa/ẩn danh dữ liệu matching, ảnh và UGC theo retention policy.

### 2.3 Launch blockers không được giả lập

- Provider hoặc hàng đợi moderation thật cho ảnh hồ sơ/xác minh, gồm retry/appeal và SLA.
- Kênh xử lý report trong 24 giờ, community rules và contact hỗ trợ công khai.
- Push notification credentials cho iOS/Android.
- Store configuration chặn người dưới 18 tuổi; app không target trẻ em.

Dev/QA được dùng fixture riêng để tạo trạng thái `verified`; runtime production không có endpoint tự duyệt.

## 3. Kiến trúc đích

### 3.1 Backend

Domain `matching` giữ ranh giới riêng:

- `MatchingProfile`: principal, intent, preference, coarse region, weekly intent, active state.
- `MatchingConsent`: version, purpose, granted/withdrawn.
- `ProfileVerification`: pending/pass/fail, reason code, reviewer/provider reference; ảnh nằm trong private object storage, không trong database.
- `VongLaPool` + `VongLaSlate` + `VongLaCard`: snapshot tuần, version của algorithm/chart/evidence, tối đa 5 lá và 3 lượt mở.
- `VongLaRequest` + `MutualMatch`: request idempotent; mutual atomic và unique theo cặp/pool.
- `LaNoiSnapshot`: nội dung relationship bất biến sau mutual; không tính lại khi mở màn.
- `ChatThread`, `ChatMessage`, `Block`, `Report`, `Unmatch`: authorization theo participant, audit và retention.
- `VongLaRecap`: snapshot Chủ nhật, share projection ẩn danh.

Các job tuần phải idempotent và có thể chạy lại: publish slate, expire request, generate recap, cleanup retention.

### 3.2 App/web

Một feature `apps/web/src/features/matching/` dùng chung cho PWA và Capacitor:

- Entry + readiness checklist.
- Intent/preference/region/consent/verification.
- Countdown, closed/low-pool/error/reconnect.
- Five-card deck, detail “Vì sao có lá này?”, open limit.
- Request/pending/mutual/Lá Nối.
- Chat + 3 icebreakers + block/report/unmatch.
- Recap story + native share.

Navigation có mục `Vòng Lá`; cổng login chỉ xuất hiện khi người dùng chọn tham gia social matching.

## 4. Implementation units

### U1 — Nền dữ liệu, quyền và privacy (P0)

Files chính:

- `apps/api/app/domains/matching/tables.py`
- `apps/api/app/domains/matching/repository.py`
- `apps/api/app/domains/matching/postgres.py`
- `apps/api/app/domains/matching/service.py`
- `apps/api/migrations/versions/20260917_0019_vong_la_core.py`
- `apps/api/app/db/base.py`
- `apps/api/app/main.py`

Kết quả:

- Persistence thật cho profile/consent/verification/pool/slate/card.
- Owner identity bắt buộc; không nhận `principal_id` từ client.
- Withdrawal/leave-pool xóa khỏi active discovery ngay.
- Không lưu raw chart trong matching tables; chỉ lưu version + evidence ids cần thiết.

Verification:

- Repository/service tests cho consent version, age gate, leave pool, authorization và retention-safe serialization.
- Migration preflight + unique/check constraints.

### U2 — Readiness API và app flow (P0)

Files chính:

- `apps/api/app/api/v1/routes/matching.py`
- `apps/web/src/shared/api/client.ts`
- `apps/web/src/features/matching/MatchingEntryPage.tsx`
- `apps/web/src/features/matching/MatchingSetupPage.tsx`
- `apps/web/src/features/matching/matching.css`
- `apps/web/src/app/router.tsx`
- `apps/web/src/shared/ui/AppNav.tsx`

Kết quả:

- `GET /matching/readiness`, `PUT /matching/profile`, `POST/DELETE /matching/consent`, `POST/DELETE /matching/pool-membership`.
- Checklist nói rõ dữ liệu nào được dùng; login/claim chỉ khi vào Vòng Lá.
- Verification hiển thị đúng trạng thái; production không có “tự pass”.

Verification:

- API 401/403/422, CSRF, under-18, consent withdrawal.
- Component test và mobile viewport 390×844; light/dark; keyboard/screen reader.

### U3 — Weekly slate thật và five-card experience (P0)

Files chính:

- mở rộng `apps/api/app/domains/matching/slate.py`
- `apps/api/app/domains/matching/jobs.py`
- routes/cards trong `apps/api/app/api/v1/routes/matching.py`
- `apps/web/src/features/matching/VongLaPage.tsx`
- `apps/web/src/features/matching/VongLaCardPage.tsx`

Kết quả:

- Hard filters chạy trước Synastry projection.
- Slate ổn định theo tuần, tối đa năm slot khác nhau; pool thiếu trả low-pool trung thực.
- Mở tối đa 3 lá; detail không có điểm số và chỉ có tối đa ba evidence.
- Window 20:00–23:00 thứ Bảy theo Asia/Ho_Chi_Minh; clock injectable để test.

Verification:

- Golden deterministic fixtures, no-self/block/intent/region, refresh stability, duplicate prevention.
- Không có `compatibility_score`, GPS hoặc birth payload trong contract.

### U4 — Request kín, mutual và Lá Nối (P0)

Kết quả:

- Request chỉ từ card đã mở; idempotent; hết hạn theo pool.
- Reciprocal request tạo đúng một mutual trong transaction.
- Snapshot Lá Nối có chỗ dễ bắt sóng, chỗ dễ lệch nhịp và đúng 3 cửa mở.
- Composite bonus chỉ sau mutual; Davison bị hạ cấp nếu thiếu dữ liệu/consent.

Verification:

- Concurrency test hai request đồng thời.
- Block race trước mutual và authorization test.

### U5 — Chat an toàn và moderation seam (P0 trước public launch)

Kết quả:

- Chat text sau mutual; đúng ba icebreaker editable; không auto-send.
- Block tức thì, report từ tin đầu, unmatch, rate limit và audit event.
- Filter input/output, contact/support, community rules; moderation queue interface.

Verification:

- Unauthorized thread, blocked race, duplicate/offline send, report privacy, abuse rate limit.

### U6 — Recap, share và return loop (P1)

Kết quả:

- Recap snapshot Chủ nhật, tone tích cực kể cả không mutual.
- Share card ẩn danh, native share sheet trong app, safe web preview.
- CTA quay lại Daily Note hoặc countdown tuần sau.

Verification:

- 0/1/3 opened, 0/n request, 0/n mutual, blocked candidate, unauthenticated deep link.

### U7 — App hardening và release readiness (P0 launch gate)

Kết quả:

- Capacitor sync iOS/Android; universal/app links; push permission đúng thời điểm.
- Secure storage cho token; không log PII/evidence/chat; private response no-store.
- Account deletion/consent withdrawal/retention cleanup end-to-end.
- App Store/Play Console metadata 18+, privacy labels/data safety, moderation/contact docs.

Verification:

- Full API test + mypy + Ruff + web test/build + Playwright smoke.
- iOS/Android simulator smoke; OWASP MASVS storage/auth/network/privacy checklist.
- Manual safety QA: report/block/unmatch/deletion/low-pool/no-network/reduced motion.

## 5. Thứ tự thực hiện

1. U1 → U2 để có readiness thật và cổng login đúng lúc.
2. U3 để có giá trị cốt lõi “năm kiểu kết nối”, kể cả khi local chỉ hiện low-pool trung thực.
3. U4 → U5 vì mutual không được phát hành nếu chưa có safety/chat boundary.
4. U6 để tạo retention loop.
5. U7 xuyên suốt, release gate cuối cùng.

Không mở public beta nếu U5/U7 hoặc verification/moderation launch blocker chưa đạt.

## 6. Definition of Done toàn sản phẩm

- US-14…US-18 đạt toàn bộ AC/DoD và truy được bằng automated test hoặc QA receipt.
- Người dùng có thể rời pool, block/report/unmatch và xóa tài khoản ngay trong app.
- Không có mock candidate, auto-pass verification, scalar compatibility hoặc deterministic “phán” tương lai.
- Tất cả private endpoint được owner-authorized, CSRF-protected, no-store và log-redacted.
- Migration tiến/lùi được kiểm tra; job idempotent; reconnect không làm đổi slate hay gửi trùng.
- App iOS/Android chạy cùng version contract; web companion vẫn hoạt động.
- Store, privacy, moderation và incident runbook được duyệt trước launch.

## 7. Quy chuẩn và nguồn bắt buộc kiểm tra khi release

- Apple App Review Guidelines 1.2 (UGC: filter/report/block/contact) và 5.1.1 (privacy, login tối thiểu, account deletion).
- Google Play UGC policy và Age-Restricted Content/Matchmaking safeguards.
- OWASP MASVS: STORAGE, AUTH, NETWORK, PRIVACY.
- Nghị định 13/2023/NĐ-CP và quy định Việt Nam còn hiệu lực tại thời điểm release; cần legal review, không coi tài liệu kỹ thuật là tư vấn pháp lý.

