# Bàn giao PR #933: nội dung sinh viên tuần 2

Cập nhật 25.11.2026, Codex xử lý phản biện Antigravity vòng 1. Cỡ M.
[PR #933](https://github.com/honghanh153-creator/la-lanh/pull/933) thực hiện
[task #704](https://github.com/honghanh153-creator/la-lanh/issues/704), là phần nội dung của
[#502 việc 4](https://github.com/honghanh153-creator/la-lanh/issues/502) trong
[hub tuần 2 #686](https://github.com/honghanh153-creator/la-lanh/issues/686).
Phụ thuộc [#699](https://github.com/honghanh153-creator/la-lanh/issues/699), kho việc theo sức.

Nhánh `agent/codex/issue-704`. Bản gốc đã nằm trong PR tại
`800294685d41664d626457a5238414eac8931616`, base `d3818f59b47cccccd8d59560fcb5e3d9625a294c`.
Lượt sửa vòng 1 này chỉ nằm trong checkout, chưa commit/push theo yêu cầu người dùng.
Không có verdict duyệt hoặc author check cho lượt sửa này. Không merge hay phát hành.

## Nguồn và phối hợp

- Đã đọc `AGENTS.md`, luật owner R1–R17, quy trình cộng tác, phát triển sản phẩm và checklist quyết định.
- Đã đọc lại PR #933, comment phản biện `7164632749`, issue #704, #699, #502, #686 qua connector GitHub.
  #699 còn mở tại lần kiểm. Không suy ra phụ thuộc đã hoàn tất từ việc mã đã có trong checkout.
- `collaboration-inbox.mjs` không kết nối được GitHub qua CLI. Nguồn GitHub trên là lần đọc trực tiếp
  các việc liên quan, không thay thế được toàn bộ inbox/WIP.
- `collab-pr-claim.mjs --claim 933` thiếu session ở lần đầu; thử lại với session của lượt sửa bị EPERM
  khi ghi khóa chung. Lệnh đọc trạng thái thấy claim của `coordinator`. Comment PR ghi Claude điều phối
  và Codex sửa vòng tiếp theo, khớp yêu cầu người dùng. Không đổi hay cưỡng chế nhả claim.
- Đọc PRD F1.2, SRS phần Daily, US-03 AC18 và chuẩn tiếng Việt đời thường; US-04 AC10/AC14;
  `qa/personas/judge-rubric.md`, `docs/legal/store-privacy-data-map.md` và cổng content/UX release.
- Đối chiếu `copy_approval.py`, `daily_psychology.py`, `lighter_action.py`, `action_tags.py`,
  `companion.py`, `companion_pool.py`, `voice.py`, gate rewrite và các test liên quan.
- Q1/Q3/Q4/Q5 không phát sinh thay đổi cần owner trong bản sửa này. Q2 có, nên câu vẫn pending.
  G1/G3/G6/G7/G8 có bằng chứng dưới đây; G2 thiếu ảnh; G4/G5 không đổi kiến trúc, API hay FE;
  G9 chưa phát hành; G10 không thêm dịch vụ, chi phí hay dependency.

Không sửa `.github`, các script `collab-*` hay file luật owner. Bàn giao này là bản ghi cục bộ cho
phiên điều phối đăng lại sau khi kiểm tra; chưa đăng comment, trả lời thread hay đổi nhãn PR.

## Trả lời từng điểm phản biện

| Điểm | Kết luận | Sửa và bằng chứng | Còn thiếu |
|---|---|---|---|
| 1, P1: hồ sơ đóng nhưng lại kiểm kết quả cách cũ | Đồng ý | `copy_registry.json`: đổi cả bộ `defend-old-choice.13` thành đã gửi vài nơi chưa có hồi âm, giữ cách viết vì tiếc công; action kiểm các lần gửi và sửa một chỗ cho lần tiếp. Đồng bộ digest normal trong `normal_action_tags.json`. | Duyệt câu chữ độc lập. |
| 2, P1: chủ thể đổi ca và neo ở nhà | Đồng ý | Headline dùng "được đề nghị"; scene nêu lịch ca trùng giờ học và giờ hai bên chưa chốt. Slot pending `lighter.issue.changed-plan.02` đổi thành đi vài bước, bỏ điều kiện quanh nhà; cập nhật đúng digest của slot trong `lighter_action.py`, giữ thứ tự/nhóm body. | Duyệt lại slot nhẹ đã sửa cùng bundle. |
| 3, P2: sát hạn mà chờ góp ý | Đồng ý, sửa theo mạch còn thời gian xin góp ý | Cảnh nói còn vài ngày, bản nháp đã đủ ý; action đặt giờ tự rà lại trước hạn, không cần lấy hồi âm làm điều kiện. Giữ chuyện hạn nộp trong phạm vi #704 và giữ mạch gửi bản nháp của meaning/takeaway/lời Lá hiện có. Đồng bộ digest normal. | Review nghĩa toàn thẻ, gồm việc nhẹ gấp máy. |
| 4, P2: chọn bài sau ca làm | Đồng ý | Scene nói phân vân chưa chọn được phần bài; action chọn phần gần hạn nhất và gác phần chưa gấp. Bỏ cách nói gạch phần bài; đồng bộ digest normal. | Duyệt câu chữ độc lập. |
| 5, P2: thiếu kiểm chứng/duyệt | Đồng ý | Chạy lại test ngoại tuyến và các cổng chạy được; bảng AC và danh sách thiếu ở dưới không đánh dấu phục vụ thật hay đủ AC3. | pnpm check, CI đúng head sửa, ảnh 360/390, 100 người giả trước/sau, duyệt 20 câu liên quan và phục vụ sau duyệt. |
| 6, P2: trạng thái và selector bị mock che | Đồng ý với khoảng trống test | Thêm test pre-approval bắt buộc 12 phần và 8 slot pending, metadata duyệt trống. Test runtime bỏ các nhánh if có thể bỏ qua. Kiểm độ rõ và luật hành động nhẹ cho 8 slot. Thêm test selector với nguyên registry, mở 13 bundle trong bộ nhớ, không mock eligibility: mỗi bundle xuất hiện đúng một lần trong chu kỳ 13 lượt. Cả hai giọng đều được gọi gate rewrite; giới hạn đúng hợp đồng giọng giải thích bên dưới. | Test mở khóa là mô phỏng trong bộ nhớ, không phải duyệt thật hay bằng chứng phục vụ trên môi trường phát hành. |
| 7, P3: bàn giao cũ và đường dẫn máy | Đồng ý | Viết lại file bàn giao này theo PR #933; phân biệt commit gốc và lượt sửa chưa commit, nối rõ #704/#502/#686, bỏ toàn bộ đường dẫn máy. | Phiên điều phối cần đăng bản ghi lên PR sau khi có bản sửa được xuất bản. |

Điểm 2 có một suy luận chưa đúng về mã: `daily_psychology.lead_scene()` không thay phần "Khi ở nhà".
Nó thêm lead và viết thường chữ đầu của cảnh. Điều này không làm mất neo, nhưng vẫn khiến cảnh gượng;
vì vậy vẫn sửa P1, không giữ neo cũ để dựa vào suy luận này.

Ở điểm 6, `_check_action` của Daily đòi ID daily và neo của việc thường, nên không dùng nó để ép
việc nhẹ phải làm học/việc. Tám slot chạy `_check_clarity`, `has_observable_action`, `light_by_rule`,
giới hạn ký tự và `within_five_minutes`. `test_issue_light_store.py` còn kiểm cả kho theo cùng rubric.

Gate `evaluate_daily_rewrite` dùng ý nhắc Thẳng từ `companion.nudge_failures`; `voice.py` và chuẩn
nội dung quy định Cà khịa dùng thẻ viết sẵn, không ghép từng phần từ Luna. Test nay gọi gate ở cả
hai giọng, không bỏ qua ROAST: cả bốn thẻ Thẳng đạt; Cà khịa của `changed-plan` và `defend-old-choice`
trả đúng `daily_companion_off_brief` do câu Lá viết sẵn dùng chữ khác neo Thẳng. Hai Cà khịa còn lại
đạt gate này. Không tuyên bố hai câu bị từ chối đã qua rewrite, không nới gate và không sửa lời Lá
có sẵn để làm test xanh. Lượt `review_content_release` kiểm cả Direct/Roast cũng đạt; lượt đó kiểm
nội dung đang phục vụ, không thay thế duyệt các câu pending mới.

## Bốn bộ câu sau sửa

Mỗi phần đều `category: reading`, `status: pending`, không có approver/date/digest duyệt.
Hai nhóm dưới đây chỉ mô tả nội dung biên tập, không gắn nhãn hay suy ra nhóm của người dùng.

| Nhóm | Bundle | Headline | Scene | Action và nhãn |
|---|---|---|---|---|
| Đang tìm việc | `daily.bundle.perfect-before-start.13` | Khi gần hạn nộp mà bạn vẫn sửa hồ sơ. | Khi còn vài ngày trước hạn nộp, bạn vẫn sửa hồ sơ trên máy dù bản nháp đã đủ ý. | Gửi bản nháp hồ sơ xin góp ý, đặt giờ tự rà lại trước hạn nộp. `normal / connection` |
| Đang tìm việc | `daily.bundle.defend-old-choice.13` | Khi hồ sơ gửi đi chưa có hồi âm. | Khi hồ sơ gửi vài nơi chưa có hồi âm, bạn vẫn giữ cách viết cũ vì tiếc công sửa. | Kiểm tra kết quả các lần gửi hồ sơ, chọn một chỗ thay đổi cho lần nộp tiếp theo. `normal / study_work` |
| Vừa học vừa làm | `daily.bundle.changed-plan.13` | Khi được đề nghị đổi ca trùng giờ học. | Khi được đề nghị đổi lịch ca trùng giờ học, bạn chưa biết hai bên sẽ chốt giờ nào. | Nói rõ giờ học cần giữ và đề xuất giờ khác để hai bên chốt ca mới. `normal / boundary` |
| Vừa học vừa làm | `daily.bundle.decision-fatigue.13` | Khi mệt sau ca, bài còn nhiều phần. | Khi mệt sau ca làm, bạn phân vân chưa chọn được phần bài nào dù chưa cần quyết ngay. | Chọn phần bài gần hạn nộp nhất để làm trước, gác lại các phần chưa gấp. `normal / study_work` |

| Bundle issue | Slot nhẹ .01 | Slot nhẹ .02 | Đối chiếu nghĩa |
|---|---|---|---|
| `perfect-before-start` | Duỗi vai/cổ một phút, body | Gấp máy, thở năm hơi, rest | Máy và bản nháp có trong scene; còn vài ngày, việc nghỉ không yêu cầu chờ người khác. |
| `defend-old-choice` | Uống nước/thở chậm, body | Ngồi yên hai phút, rest | Nghỉ trước khi xem cách cũ/cách mới; không dựng người tranh luận. |
| `changed-plan` | Nghỉ ba phút, rest | Đi vài bước rồi nghỉ, body | Cả hai đều hoãn xếp lại khi giờ mới chưa chốt, không đòi đang ở nhà. |
| `decision-fatigue` | Hoãn chọn năm phút/rửa mặt, body | Nhắm mắt một phút, rest | Cảnh nói chưa cần quyết ngay; không bắt đầu thêm bài hay ép chọn khi nghỉ. |

Cả tám slot vẫn pending. Chỉ `.changed-plan.02` đổi chữ/digest trong lượt này. Slot đó chưa được duyệt
ở head gốc; việc sửa không thay câu đã phục vụ. Không thêm, đảo thứ tự hay đổi nhóm hình catalog.

`EXTRA_LINE_SELECTION_ENABLED` vẫn False. Các câu Lá bổ sung pending nói gọi món, so giá, so hai tuần,
làm ba tuần hoặc để nháp một tuần không được bật cho bốn bộ mới. Việc bật cần review ghép nghĩa riêng.

## Kiểm chứng cục bộ ngày 25.11.2026

Dependency dùng môi trường Python đã cài sẵn. Các lệnh Python dưới đây chạy trực tiếp ngoại tuyến theo
yêu cầu của người dùng, không gọi API trả phí, không tải gói hay sửa lockfile. Đây không phải receipt
của test guard/author check. Không đổi vị trí khóa chung. Lệnh nặng cần khóa và lượt CI còn thiếu ở dưới.

Chạy từ `apps/api`:

```sh
.venv/bin/python -m pytest \
  tests/content/test_student_daily_situations.py \
  tests/content/test_daily_variants.py \
  tests/content/test_daily_scene_bundles.py \
  tests/content/test_copy_approval.py \
  tests/readings/test_daily_bundles.py \
  tests/readings/test_issue_light_store.py \
  tests/readings/test_action_tags.py -o addopts='' -q --tb=short
```

Kết quả cuối: **4.276 passed**, exit 0. File sinh viên có 107 ca, tăng 5 ca so với bản gốc.
Lượt đầu phát hiện scene thiếu neo chọn và action mở đầu không thuộc động từ của gate; đã sửa câu,
không nới gate. Fixture chu kỳ ban đầu bắt đầu giữa hai chu kỳ nên lặp; đã căn đầu chu kỳ 13 lượt
đúng `axis_slot`, không thay thuật toán chọn trong sản phẩm.

Các lệnh sau đều đạt, exit 0, chạy từ `apps/api`:

```sh
.venv/bin/python -m scripts.grammar_build --check
.venv/bin/python -m scripts.fallback_approval --check
.venv/bin/python -m scripts.audit_content_matrix
.venv/bin/python -m scripts.review_content_release
.venv/bin/python -m scripts.persona_validate
.venv/bin/ruff check app/domains/readings/lighter_action.py tests/content/test_student_daily_situations.py
.venv/bin/ruff format --check app/domains/readings/lighter_action.py tests/content/test_student_daily_situations.py
.venv/bin/python -m mypy tests/content/test_student_daily_situations.py
```

Audit giữ 630 Daily variants, 23 relationship concepts, 8 Radar themes; clarity ratchet đạt.
Review Direct và Roast: mỗi lượt 10 người giả/30 bài, không critical/high hoặc medium follow-up.
Đây là kiểm cục bộ đang phục vụ, không phải bộ 100 người giả của #502 hay điểm tăng của #708.
Mypy không có lỗi; có note cấu hình override `prometheus_client` không dùng.

Từ root repo, ba lệnh sau đạt: `node scripts/verify-no-mock-runtime.mjs`,
`node scripts/verify-privacy.mjs`, `node scripts/verify-mobile-config.mjs`.
`git diff --check` đạt. Đối chiếu registry với HEAD gốc bằng Python: đúng 11 entry pending đổi chữ,
không đổi tập ID, mọi entry approved giữ nguyên. Daily fingerprint trước/sau cùng `ac130cb3`.

## AC và ba cổng chất lượng

| AC | Bằng chứng đã có | Phần chưa hoàn tất |
|---|---|---|
| AC1 | Bốn bộ cho hai nhóm; normal + hai light mỗi bộ; test inventory, mọi arena/hai giọng; test xoay cạnh 12 bộ cũ. | Phụ thuộc #699, duyệt đồng bộ 12 phần + 8 light; kiểm phục vụ thật sau duyệt. |
| AC2 | Câu điều kiện, không gán thiếu tiền/thất nghiệp, không dự đoán trúng tuyển; không thêm input hoặc phân nhóm. | Review nghĩa độc lập trên bản sửa cuối. |
| AC3 | Tất cả 20 câu liên quan còn pending; test trạng thái tường minh, clarity và gate; sửa bốn điểm câu chữ. | Biên nhận Codex duyệt chính chữ cuối cùng, cập nhật pin sau duyệt theo quy trình. Không tự duyệt trong lượt sửa. |
| AC4 | Kiểm kê trường/ID/digest/cỡ/nhóm hình, ca âm và runtime, 4.276 test liên quan đạt. | CI và author check đúng commit chứa bản sửa này. |

- Tài liệu/hợp đồng: không đổi schema hay luật chọn; bảng trên nối đủ AC và nêu phần thiếu.
- Bảo mật: diff chỉ kho câu, digest/tag, test và bàn giao. Không đổi authentication/session ownership,
  authorization/CSRF, endpoint/input/rate limit, key/crypto/log, dependency/network/storage,
  lỗi trả ra, share/invite/token hay đường xóa. Pending không phục vụ, approved pin và fingerprint giữ nguyên.
  Hỏng digest thì không lấy slot, không mở dữ liệu hoặc gọi dịch vụ thay thế. Chưa thấy P0/P1 bảo mật mới.
- Privacy: các trường ngày/giờ/nơi sinh, tọa độ, mood, quan hệ, định danh/token và profile suy ra không đổi.
  Không thu, suy ra, lưu, cache, log, xuất, chia sẻ hay gửi SDK thêm trường nào. Nội dung note là dữ liệu
  suy ra theo luồng có sẵn, chưa nhận các câu pending này; không suy ra nghề, thu nhập hoặc nhóm sinh viên.
  Mục đích, consent, retention, encryption, quyền truy cập/rút/xóa và bên nhận không đổi trong diff.
  Suy luận kỹ thuật từ phạm vi diff: chưa có delta cho data map hay khai báo store; chưa kiểm console/binary release.

## Nguồn chính thức đã đối chiếu ngày 25.11.2026

| Nguồn | Phần thực sự kiểm | Đối chiếu với thay đổi |
|---|---|---|
| [Luật 91/2025/QH15](https://vanban.chinhphu.vn/?docid=214590&pageid=27160), [CSDL Bộ Công an](https://bocongan.gov.vn/chinh-sach-phap-luat/co-so-du-lieu-van-ban/luat-bao-ve-du-lieu-ca-nhan-1753688803) | Thuộc tính: ban hành 26.06.2025, hiệu lực 01.01.2026; Bộ Công an ghi còn hiệu lực. Đọc thêm định nghĩa khoản 1 Điều 2 được trích trong [bài hướng dẫn của Bộ Công an](https://bocongan.gov.vn/chinh-sach-phap-luat/bai-viet/canh-giac-nguy-co-vi-pham-phap-luat-trong-bao-ve-du-lieu-ca-nhan-khach-hang-1787901431): dữ liệu giúp xác định cá nhân thuộc phạm vi bảo vệ. | Không coi note suy ra hoặc định danh tổng hợp là dữ liệu vô danh mặc nhiên. Không thêm luồng xử lý; chưa kết luận tuân thủ toàn bộ sản phẩm. |
| [Nghị định 356/2025/NĐ-CP](https://vanban.chinhphu.vn/?docid=216387&pageid=27160), [bản Công báo](https://congbaocdn.chinhphu.vn/180507251028987904/2026/1/17/356signed-1768638052103952849513.pdf) | Hiệu lực 01.01.2026. Đọc Điều 3–4, trang PDF 2–3, về danh mục cơ bản/nhạy cảm; Điều 6, trang 5–6, về đồng ý phải kiểm chứng được và không đặt mặc định đồng ý. Bản PDF ký số đầu tiên không trích được chữ, đã chuyển sang bản Công báo có chữ. | Ngày/nơi sinh, định danh, quan hệ và dữ liệu nhạy cảm vẫn thuộc kiểm kê G8; bản sửa không thêm chúng. Không tạo consent mặc định hay biến thao tác đọc thành đồng ý thu dữ liệu. |
| [Apple App Review 5.1.1(i)–(iii), (v)](https://developer.apple.com/app-store/review/guidelines/#privacy) | Chính sách privacy, consent, tối thiểu hóa dữ liệu, không buộc nhập thông tin không cần thiết. | Bộ câu không đòi khai nghề hay hoàn cảnh; không thêm quyền/SDK/input. Không viết lại privacy/consent trong app. |
| [Google Play User Data](https://support.google.com/googleplay/android-developer/answer/10144311?hl=en) | Full Policy; Personal and Sensitive User Data; Prominent Disclosure and Consent. | Không thêm thu/chia sẻ dữ liệu hoặc dùng AI/SDK mới; không coi câu tình huống là lời đồng ý của người đọc. |
| [Google Play Data safety](https://support.google.com/googleplay/android-developer/answer/10787469?hl=en) | Overview: khai báo phải đầy đủ và đúng hành vi app, gồm SDK. | Không có delta thu/chia sẻ trong diff. Chưa kiểm hoặc sửa khai báo trên console; cần đối chiếu binary trước phát hành. |

Các nguồn web chỉ nhận truy vấn công khai về luật/chính sách và repo công khai, không dữ liệu người dùng.
Phần luật chỉ kiểm các mục đã ghi, chưa rà toàn bộ điều khoản hoặc lịch sử sửa đổi. Nếu bản phát hành
bật luồng thu dữ liệu mới, cần rà pháp lý chi tiết lại và owner quyết theo R2, không dùng bảng này làm duyệt bật.

## Việc còn thiếu và điều kiện tiếp tục

- `pnpm check`: đã gọi, exit 127 do không có `pnpm`. Chưa chạy bộ web/e2e/full check; không tải gói để lấp thiếu.
- `collab-test-guard.mjs --wait-min 0 -- true`: EPERM khi tạo khóa chung. Vì vậy chưa chạy mô phỏng 100
  người giả trước/sau qua guard; không đổi thư mục khóa. Chưa có báo cáo, điểm hay mức tăng 0,2.
  #502 yêu cầu đo sau mỗi PR; #708 còn là việc riêng cho bốn nhóm. `persona_validate` không thay hai việc đó.
- Ảnh/preview 360 và 390 px: CUA trả danh sách browser rỗng, báo browser access host unavailable.
  Chưa có ảnh của câu sửa cuối hoặc kết luận về tràn dòng/font ứng dụng. Fixture cũ không phải bằng chứng mới.
- CI đúng head và `Author check: PASS @ <SHA>` chỉ có thể ghi sau khi phiên điều phối commit/push bản sửa
  và chạy kiểm. CI trên `80029468` không chứng minh bản sửa chưa commit này.
- Reviewer phải đọc trọn bốn thẻ, meaning/takeaway/câu hỏi và hai giọng/lựa chọn nhẹ, rồi có biên nhận Codex
  duyệt 12 phần cùng 8 slot. Khi đó cập nhật pin và thay test pre-approval trong chính PR có biên nhận;
  không chỉ đổi pending để test qua. Test mô phỏng mở khóa không phải biên nhận này.
- Sau duyệt và merge cần xác minh phục vụ normal/light trên môi trường được phép, giữ thẻ đã mở ổn định.
  Phát hành ra người dùng thật, merge main/deploy vẫn là khoảng trống cần owner theo R2/R12.
- Chi phí/dịch vụ/quyền mới, chữ privacy/consent/crisis/safety và bật thu dữ liệu cá nhân mới không phát sinh
  trong bản sửa. Nếu bước tiếp theo cần chúng thì ghi việc cần owner, không tự quyết hoặc bật. Không tạo
  lời đồng ý, chữ nhạy cảm hay quyết định phát hành trong lượt này.
- #923, #705–#708 và các phần chip/lưu chip không được giải quyết bởi PR nội dung này. Không đóng #704
  với tuyên bố AC1/AC3 đã hoàn tất khi các điều kiện trên còn thiếu.

## Còn khác ý

Không có P1 còn khác ý. Giới hạn của gate rewrite đối với Cà khịa và mức đọc nguồn luật đã nêu rõ,
không dùng chúng để tuyên bố đã qua các bước chưa kiểm.
