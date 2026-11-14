## 1. Kiến trúc tổng thể

Đây là thiết kế độc lập của Codex, không đọc bản nháp Claude. Phân loại **L**; ma trận dưới bao phủ **167/167 yêu cầu lá**.

Tái dùng sáu thành phần:

| Thành phần | Nền hiện có và phần bổ sung |
|---|---|
| **Điều phối** | Giữ `collab-{tick,turn,lock,heal,watchdog}.mjs`, `prTurn`; chuyển lịch ngày thành quyền chạy liên tục. |
| **Policy** | Mở rộng `collab-{trust,preflight,merge}.mjs`; một manifest quyền owner ký, nằm ngoài checkout agent. |
| **Mục tiêu** | Thêm `collab-goals.mjs`; nối outcome, metric, giả thuyết, issue, bằng chứng và kết quả. Mở rộng metrics của #451. |
| **Xác minh** | CLI dùng Playwright, API thật trên Compose riêng, feature/component map, golden tests và UAT độc lập. |
| **Owner** | Mở rộng `collab-status.mjs`; bảng riêng tư, thẻ quyết định, thông báo, mẫu kiểm tra. |
| **Học hỏi** | Registry prompt/skill, principles, ADR, nhật ký và eval trong repo; scratch từng agent, ngân sách và taste riêng tư. |

Không cần thêm “chief of staff” thường trực. Claude/Codex đổi vai implementer/reviewer; các persona chạy tuần tự bằng hai agent hiện có.

**Baseline cần sửa:** #451 còn `REQUEST_CHANGES`; metrics registry chưa chứng minh Daily được phục vụ. `ui-screens.yml` đã có ảnh 390px với API mock, chưa thay kiểm thử toàn hành trình.

## 2. Luồng mỗi tick

```text
Đọc policy + checkpoint + inbox + trạng thái GitHub.
Nếu policy sai hash/quyền hết hạn → freeze mutation, tiếp tục báo.
Nếu incident → ưu tiên tái hiện, cô lập, phục hồi đã được phép.
Nếu hạ tầng lỗi → retry có backoff, tối đa 3 lần rồi quarantine.
Nếu hết ngân sách → dừng lane tương ứng, giữ incident reserve.
Nếu đang chạy → reconcile kết quả trước khi làm tiếp.
Nếu còn chỗ WIP 1 implement + 1 review → chọn giả thuyết hợp lệ.
Thực hiện một bước prTurn → ghi bằng chứng → đối soát → báo owner.
```

Mỗi hành động có khóa và idempotency key theo task/head/policy. Crash sau merge vẫn nhận diện được merge trực tiếp; không đếm lại. Copy dùng chung bộ đếm, lưu digest đã chấm để câu bị từ chối không chặn mãi hàng sau; fork không được khóa hàng đợi.

Freeze chặn việc mới/merge, vẫn cho chẩn đoán và báo. Mỗi việc bị chặn phải có **execute hoặc skip**, lý do, hạn xét lại. Hai vòng sửa không đạt thì quarantine.

Bỏ mọi cổng giờ mâu thuẫn. Chạy bằng CLI dưới supervisor, không phụ thuộc cửa sổ app. Mac phải thức; muốn chạy khi Mac tắt cần runner owner duyệt. Polling 10 phút còn là đối soát; subscription bổ sung sau.

## 3. Tầng mục tiêu và chống gaming

Owner nhập outcome. Hệ thống lập:

**Goal → metric contract → baseline → giả thuyết → thử nghiệm nhỏ → xác minh → giữ/bỏ.**

Metric contract khóa nguồn, mẫu số, cửa sổ đo, mức cải thiện đáng kể, cỡ mẫu tối thiểu và guardrail trước thử nghiệm. Agent không được sửa rubric để thắng.

Ví dụ “nội dung tốt hơn”: đo bundle được runtime chọn/render, độ cụ thể chấm mù và phản hồi người đọc. Nếu chưa có user, chỉ kết luận readiness; không suy thành retention.

Hill-climb sửa điểm yếu nhất, mỗi lần một biến. Traffic loại bot/internal; không dùng clickbait. Defect đếm theo nguyên nhân gốc; theo dõi p95 lead time **và tuổi PR mở**, tổng thời gian owner, time-to-user, merge/no-touch rate, turns-to-right, số thử nghiệm. PR count không là mục tiêu. Thiếu mẫu thì chưa kết luận, không tự tạo tín hiệu thắng.

## 4. Lòng tin theo loại thay đổi và full-auto

Mỗi loại có lịch sử riêng: tooling, layout, content, auth, migration, privacy. Đi qua **shadow → đề xuất → integration tự động → mở rộng phạm vi**.

Full-auto chỉ bật khi có verification skill/feature map, UAT độc lập, bằng chứng đúng SHA, rollback drill, thông báo đã thử nhận và đủ lịch sử/mẫu owner đã xem theo policy. Mẫu chưa xem là pending. Risk score học máy chỉ tư vấn, không vượt hard gate.

Mỗi merge, kể cả lệnh trực tiếp, kiểm lại policy/diff, head, base, `PASS`, verdict, AC và quyền. Shared GitHub account hay marker `OWNER` không chứng minh owner ra lệnh. Manifest cần chữ ký ngoài quyền agent. Đổi level không cấp thêm quyền.

Main/deploy/paid/provider/IAM luôn cần lệnh riêng gắn SHA, môi trường, hành động, thời hạn. UI copy, privacy/consent/crisis/safety, trường lưu mới, mục đích/retention, ngày/giờ/nơi sinh vẫn thuộc hard list. Pending copy dùng cơ chế digest/fallback hiện hữu.

## 5. Bề mặt owner

Dashboard ghi riêng **PR mở / integration merge / preview chạy / production chạy**. Mỗi thắng lợi có URL, SHA, ảnh/video và phép kiểm.

Thông báo ngay khi incident hoặc cần quyết định; tiến độ thường gom digest. Thẻ chống trùng theo nguyên nhân/head, có tuổi và hạn; tối đa ba thẻ quyết định mở. Không dựa riêng comment do tài khoản owner tự đăng: thử nhận notification thực tế trước khi nghiệm thu.

Ngân sách review mỗi 2–3 ngày: 10 phút outcome, 20 phút quyết định, 20 phút mẫu ngẫu nhiên theo rủi ro, 10 phút taste/ratings. Tính cả interruptions. Quá tải thì giảm WIP, không giấu việc. Rating một chạm đi vào eval; sửa copy/voice note tạo PR, không sửa live.

## 6. Phản biện mọi plan

Planner và reviewer ngữ cảnh sạch tranh luận tối đa hai vòng. Áp dụng cả goal của owner: chi phí cơ hội, phương án không làm, giả định yếu, bằng chứng bác bỏ, kịch bản “làm tệ nhất”, quyền và ngoại lệ có hạn.

Kết quả là hai lựa chọn kèm khuyến nghị hoặc PRD/EARS trước; có sơ đồ ADR khi đổi kiến trúc. Mọi ID phải là làm ngay, chờ prerequisite hoặc đề xuất bỏ. Không cắt scope ngầm.

Codex/Claude khóa hai thiết kế độc lập rồi mới review chéo. Bất đồng còn lại thành decision card. Spec thắng lời tự báo “đã xong”.

## 7. Giai đoạn theo phụ thuộc

| Pha | Điều kiện và acceptance test |
|---|---|
| **P0: hợp đồng** | Khóa catalog, policy, quyền và hai thiết kế. Thử agent giả owner/sửa policy: bị từ chối; truy vết không thiếu ID. |
| **P1: vận hành** | Sửa #451, chạy shadow, supervisor và WIP. Thử qua đêm, mất mạng, kill giữa bước: không trùng việc, không mất thông báo, không vượt cap. |
| **P2: content + UX** | UAT tách quyền, verification CLI; mở rộng `test_engine_golden.py`, không xây lại swetest. Runtime chứng minh bundle được render; giữ hồi quy #448–450; sửa U2/U5/U7/U9. Suite ≤15 phút, overnight không flaky. |
| **P3: go-live** | Drain backlog, release packet, owner ra lệnh. Owner tuyển năm người trưởng thành tự nguyện thử lần đầu và quay lại hôm sau; họ nhận bản thử miễn phí, có thể rút/xóa. Tiếp tục khi ≥4/5 hoàn thành hành trình và nói được giá trị; lỗi safety/privacy thì dừng. |
| **P4: security/privacy sâu + điều khiển metrics** | Baseline an toàn bắt buộc trước P3; audit toàn repo và analytics hợp lệ ở đây. Chỉ điều khiển khi đủ mẫu. Canary ≥30 phiên đủ điều kiện, ≥24h, có control, và tăng mẫu nếu tính power yêu cầu. |
| **P5: Lá Dám** | Sau P4; prototype người thật trước, guardrail mood/draw cap. Preference memory phải consent/xóa; push/widget/companion cần quyền nền tảng và owner duyệt phạm vi. |
| **P6: café** | Sau Lá Dám; vouch, chống lạm dụng, consent hai phía. Thử thu hồi/xóa/chặn trước growth loop bạn bè. |

Rollback không chỉ đổi image: kiểm schema floor, giữ deletes/revocations qua restore. Drill cả rollback thất bại; khi không tương thích thì tắt feature, giới hạn phục vụ và fix-forward. Không đủ canary thì giữ, không dùng traffic giả thay người thật.

## 8. Ma trận truy vết

Khoảng ID dưới đây bao gồm mọi nhánh ghi trong khoảng.

| ID | Thành phần/cách thích nghi | Pha |
|---|---|---|
| R1,R2,G1,C2,C3,D3e,L16 | Điều phối, recovery, worktree mới | P0–1 |
| R3,R4,G2,G3,C5,C7,D3f,D4a,D5e,D10b,D16b,L13,L15,L18,E3–E5,D28a | Outcome/metric/experiment, appetite; đo tốc độ thật | P1–4 |
| R5,C6,D3a,D6b,D10a,D11c,D19a–D19c,D28b,E1,E2 | Critic, hỏi thiếu dữ kiện, spec/ADR, alternative flows | P0–2 |
| R6,G7,C10,D4c,D9e,D15b,D25c,D28c,D30a,L7 | Owner cards/widgets, voice→ticket, taste, sampling | P1–3 |
| R7,G4,C1,C8,D4d,D9b,D11a,D11b,D22c,D27a | Release packet, flags/SLO/error budget, tester, freeze | P2–4 |
| R8,R9 | Nguồn→thích nghi; thiết kế độc lập→review chéo | P0 |
| R10,C4,D4b,D4e,D6c,D7c,D13a,D25a,D25b,L3,L8,L17 | Policy, risk/size, schema approval, draft-only, bỏ credentials | P0–4 |
| G5,D3d,D6a,D9c,D15c,D16c,D30b | Wiki/principles/blueprints; lesson xác thực hai lần | P0–2 |
| D1a,D2d,D7b,L10,L11 | Findings→lint/test/codemod, import/type boundaries | P2 |
| G6,G8,D1b,D1c,D2b,D15a,D22a,L1,L2 | No-any, snapshots, component map, UI thật, a11y/Lighthouse | P2 |
| D1d,D7a,D18a–D18c,L6 | CI persona matrix; verifier từng AC, spec/base trước diff | P2 |
| D1e,D12a,D13c,D26a,D26b,D29a,L4,L5,L9 | Dreaming có đếm evidence; recall/diary; gom root cause | P2 |
| D2a,D2c,D12b,D15d,D23 | Role đọc-only, menu việc, memory hash/scratch, phiên ngắn | P1 |
| D3b,D17a–D17c,D21a | Use-case→DSL/Playwright; held-out UAT, regeneration check | P2 |
| D3c,D8b,D9a,L14 | Repro bot, mã lỗi; điều tra trước PR | P2–4 |
| D5a,D7d,D8a,D8c,D10c,D20b,D20c | Turns-to-right, churn×coverage, reliability tuần; bác lazy fix | P2 |
| D5b | Production signals đã lọc→giả thuyết | P4 |
| D5c,D13b,D13d,D14a,D14b,D14d,D27c,L12 | Registry/eval/version; kiểm overlap, drift, non-activation, rot, overload | P2 |
| D5d | Research ngoài bằng hai agent hiện có | P1–2 |
| D9d | Event subscription kèm đối soát polling | P4 |
| D11d,D29b,D29c | Keep/trash/try; eval có/không pack; retire pack | P2 |
| D12c | Preference memory consent/xóa | P5 |
| D14c | `minimumReleaseAge`, audit global hooks | P2 |
| D16a,D16d,D27b | Judge hiệu chuẩn người; JSONL giống nhau local/CI/staging; whole-system | P2–3 |
| D20a,C9 | Mở rộng swetest golden hiện hữu | P2 |
| D20d,D20e | Kiểu consent/token không log; security toàn repo | P2–4 |
| D22b | Issue đã ủy quyền, WIP 1+1 | P1 |
| D22d | Vouch café | P6 |
| D24a–D24c | Mood điều hòa, điểm dừng, draw cap; không streak/alarm | P2–5 |
| D26c | Sweep bằng agent hiện có; Haiku chờ owner | P2/§9 |
| E6,U4 | Giá trị sớm, hành động giây, push; bạn bè/widget/companion; retention thấp, giọng êm | P2/P4–6 |
| U1,U3,U8 | Giữ hồi quy #450/#449/#448; chưa gọi là live | P2 |
| U2,U5,U7,U9 | Tên thống nhất, Lưu rõ, preview Khám phá, sửa X | P2 |
| U6 | Giữ bỏ demo theo quyết định 10.10 | P0/§9 |

UAT riêng phải **tách credentials thực**, không chỉ khác repo. Skill eval dùng thư mục trung tính, judge khác model, chấm tay trước, chạy lại mỗi thay đổi. Dreaming chỉ đề xuất; owner/reviewer nhận hoặc bác.

## 9. Đề xuất bỏ — owner quyết

- Bỏ cách áp dụng máy móc “review main mỗi sáng”, 1–10 verifier đồng thời, thêm Haiku: vượt quyền hoặc tải hai agent. Giữ xác minh bằng phiên độc lập và sampling.
- Bỏ flag cho mọi refactor; giữ flag cho hành vi có thể tắt. Flag không thay rollback dữ liệu.
- Không khôi phục demo U6, streak pressure hay mood alarm nếu owner chưa đổi quyết định.

Đã đối chiếu PRD/SRS, US-03/04/05, quy trình G1–G10, release gates, scripts, web/API và [#451 cùng verdict](https://github.com/honghanh153-creator/la-lanh/pull/451). Tham chiếu chính thức: [Anthropic](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents), [GitHub security](https://docs.github.com/en/copilot/concepts/security-governance-and-network-settings/risks-and-mitigations), [WCAG](https://www.w3.org/TR/WCAG22/), [Luật 91](https://vanban.chinhphu.vn/?docid=214590&pageid=27160), [Nghị định 356](https://vanban.chinhphu.vn/?docid=216387&pageid=27160), [Apple Privacy](https://developer.apple.com/app-store/app-privacy-details/). Analytics cần data map, purpose/retention, consent/deletion và khai báo store khớp runtime; pseudonym vẫn là dữ liệu cá nhân.

Không sửa file hay lỗi runtime trong lượt này. Inbox CLI bị chặn mạng; đã đọc GitHub qua connector. Cross-review, triển khai và toàn bộ acceptance test còn chưa thực hiện.