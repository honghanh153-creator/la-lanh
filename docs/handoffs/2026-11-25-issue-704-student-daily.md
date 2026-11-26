# Bàn giao PR #933: nội dung sinh viên tuần 2

Cập nhật 25.11.2026, Codex xử lý phản biện Antigravity vòng 2, vòng cuối. Cỡ M.
[PR #933](https://github.com/honghanh153-creator/la-lanh/pull/933) thực hiện
[task #704](https://github.com/honghanh153-creator/la-lanh/issues/704), phần nội dung của
[#502 việc 4](https://github.com/honghanh153-creator/la-lanh/issues/502) trong
[hub tuần 2 #686](https://github.com/honghanh153-creator/la-lanh/issues/686).
Phụ thuộc [#699](https://github.com/honghanh153-creator/la-lanh/issues/699), kho việc theo sức.

Nhánh `agent/codex/issue-704`. Lúc bắt đầu vòng 2, HEAD checkout và head PR cùng là
`0c6cebaff9c520ad5141f765b08af5359a290bda`, base PR `d3818f59b47cccccd8d59560fcb5e3d9625a294c`.
Bản gốc `800294685d41664d626457a5238414eac8931616` và bản sửa vòng 1 đã được phiên điều phối
đưa lên PR. Vì vậy ghi chú vòng 1 còn ở checkout trong bàn giao cũ đã hết đúng.
Bản sửa vòng 2 ghi dưới đây chưa commit/push theo yêu cầu người dùng. Chưa có CI, verdict hoặc
`Author check: PASS` cho diff vòng 2. Không lấy kiểm tra của hai commit trước làm biên nhận cho diff này.

## Nguồn, phối hợp và quyết định

- Đã đọc `AGENTS.md`, luật R1–R17, quy trình cộng tác, phát triển sản phẩm và checklist quyết định.
- Đã đọc PR #933 và hai comment [phản biện vòng 1](https://github.com/honghanh153-creator/la-lanh/pull/933#issuecomment-7164632749),
  [trả lời vòng 1 được điều phối đăng lại](https://github.com/honghanh153-creator/la-lanh/pull/933#issuecomment-7165022895)
  qua connector GitHub; phản biện vòng 2 do người dùng cung cấp là phạm vi lượt sửa này.
- Đã đọc issue #704, #699, #502, #686 và comment kế hoạch phần 2 của #699. #699 vẫn mở tại lần kiểm
  ngày 25.11.2026; không suy ra phụ thuộc đã xong vì có mã trong checkout.
- `node scripts/collaboration-inbox.mjs` được gọi lại, exit 1 vì CLI không kết nối GitHub. Connector
  đọc được các mục liên quan, chưa thay thế toàn bộ inbox/WIP. Lượt trước không ghi được khóa PR do
  EPERM, claim thuộc `coordinator`; không lấy hay nhả khóa của phiên khác. Người dùng giao rõ Codex
  sửa checkout này, Claude vẫn điều phối xuất bản. Không sửa script hoặc chuyển thư mục khóa.
- Nguồn sản phẩm: PRD F1.2; SRS phần Content Generation; product plan tầng Daily;
  US-03 AC18, §22 và DoD; US-04 AC10/AC14; chuẩn tiếng Việt đời thường;
  `qa/personas/judge-rubric.md`; `docs/legal/store-privacy-data-map.md`.
- Đối chiếu kho câu với `copy_approval.py`, `daily_psychology.py`, `companion.py`, `voice.py`,
  gate rewrite, `lighter_action.py`, `action_tags.py` và các test liên quan.
- Q1/Q3/Q4/Q5 không phát sinh quyết định owner trong diff sửa cục bộ. Q2 có: giữ toàn bộ câu pending.
  Chọn giữ mạch nhờ người bạn xem hồ sơ vì khớp meaning, takeaway và lời Lá hiện có. Phương án tự nộp
  bỏ góp ý sẽ đổi mạch toàn thẻ. Không đổi meaning hoặc lời Lá chỉ để qua kiểm tra.

Phạm vi sửa vòng 2: `apps/api/app/domains/content/copy_registry.json`,
`apps/api/app/domains/readings/normal_action_tags.json`,
`apps/api/tests/content/test_student_daily_situations.py` và bàn giao này.
Không đổi `.github`, script `collab-*` hay file luật owner. Chưa đăng comment hoặc đổi nhãn/thread;
phiên điều phối cần đăng bàn giao vào Issue/PR khi xuất bản diff.

## Trả lời từng điểm phản biện vòng 2

| Điểm | Kết luận | Đã sửa và bằng chứng | Còn thiếu |
|---|---|---|---|
| 1, P2: mạch hồ sơ và hai việc chồng nhau | Đồng ý | `copy_registry.json`: scene nói hồ sơ trên máy đã đủ ý nhưng vẫn sửa trước khi gửi bạn xem giúp; action chỉ gửi bản hiện có cho người định nhờ. Bỏ đặt giờ tự rà lại, không lấy hồi âm làm điều kiện nộp. Giữ nhãn connection và đồng bộ digest ở `normal_action_tags.json`. Test render kiểm cùng meaning/takeaway/lời Lá ở mọi arena và hai giọng. | Biên nhận Codex duyệt chính chữ cuối cùng. |
| 2, P2: AC và kiểm chứng còn trống | Đồng ý | Bảng AC và mục việc còn thiếu tách rõ test cục bộ với CI, vòng tự động và xác minh sau merge. Không đánh dấu AC1/AC3 đã xong. | pnpm check, CI/author check đúng head mới, ảnh 360/390 và 100 người giả thuộc vòng tự động sau khi điều phối đẩy; #699 và duyệt 20 mục còn chờ. Không commit/push trong lượt này. |
| 3, P3: slot nhẹ duyệt lệch bị bỏ qua | Đồng ý | `test_unservable_student_parts_never_enter_runtime` kiểm `approved_copy` cho cả 8 slot. `_assert_student_unlock` kiểm slot có đủ key và không servable trước nhánh continue khi cả bộ còn pending. Thêm 16 ca cho 4 bộ × 2 slot × duyệt riêng/thiếu slot. | Không còn khoảng trống kiểm này trong phạm vi test. Đây là cổng CI, không phải thay đổi quy tắc phục vụ runtime. |
| 4, P3: gọt câu hồ sơ và đổi ca | Đồng ý | Action dùng "Kiểm tra cách viết hồ sơ, chọn một chỗ sửa lại cho lần nộp tiếp theo."; đồng bộ digest. Scene dùng "đổi ca làm trùng lịch học", bỏ "đổi lịch ca". `cách`/`lịch` giữ neo nghĩa đúng hợp đồng hiện có; không nới gate. | Duyệt câu chữ cùng các phần còn lại. |
| 5, P3: trạng thái bàn giao khi xuất bản | Đồng ý | Cập nhật vòng 1 đã xuất bản tại `0c6cebaf…`, phân biệt rõ diff vòng 2 chưa xuất bản. Giao phiên điều phối cập nhật SHA/CI/author check thực tế khi đẩy. Ghi riêng slot changed-plan.02 sửa từ vòng 1 còn pending, cần đối chiếu #699 trước mở. | Chỉ có thể điền SHA và biên nhận mới sau khi điều phối commit/push; không ghi giả giá trị tương lai. |

Vòng 1 đã xử lý các điểm nhân quả hồ sơ chưa hồi âm, chủ thể "được đề nghị đổi ca", bỏ neo ở nhà,
chọn phần bài sau ca, khóa pending, kiểm hai giọng và xoay đủ 13 bộ. Vòng 2 giữ các sửa đó.

## Bốn bộ câu sau sửa cuối

Mỗi phần đều `category: reading`, `status: pending`, không có approver/date/digest duyệt.
Nhóm chỉ là mô tả biên tập, không gắn nhãn người dùng hay suy ra nghề nghiệp.

| Nhóm | Bundle | Headline | Scene | Action và nhãn |
|---|---|---|---|---|
| Đang tìm việc | `daily.bundle.perfect-before-start.13` | Khi gần hạn nộp mà bạn vẫn sửa hồ sơ. | Khi hồ sơ trên máy đã đủ ý, bạn vẫn sửa mãi dù định gửi bạn xem giúp trước hạn nộp. | Gửi bản hồ sơ hiện có cho người bạn định nhờ xem giúp. `normal / connection` |
| Đang tìm việc | `daily.bundle.defend-old-choice.13` | Khi hồ sơ gửi đi chưa có hồi âm. | Khi hồ sơ gửi vài nơi chưa có hồi âm, bạn vẫn giữ cách viết cũ vì tiếc công sửa. | Kiểm tra cách viết hồ sơ, chọn một chỗ sửa lại cho lần nộp tiếp theo. `normal / study_work` |
| Vừa học vừa làm | `daily.bundle.changed-plan.13` | Khi được đề nghị đổi ca trùng giờ học. | Khi được đề nghị đổi ca làm trùng lịch học, bạn chưa biết hai bên sẽ chốt giờ nào. | Nói rõ giờ học cần giữ và đề xuất giờ khác để hai bên chốt ca mới. `normal / boundary` |
| Vừa học vừa làm | `daily.bundle.decision-fatigue.13` | Khi mệt sau ca, bài còn nhiều phần. | Khi mệt sau ca làm, bạn phân vân chưa chọn được phần bài nào dù chưa cần quyết ngay. | Chọn phần bài gần hạn nộp nhất để làm trước, gác lại các phần chưa gấp. `normal / study_work` |

| Bundle issue | Slot nhẹ .01 | Slot nhẹ .02 | Đối chiếu nghĩa |
|---|---|---|---|
| `perfect-before-start` | Duỗi vai/cổ một phút, body | Gấp máy, thở năm hơi, rest | Scene có hồ sơ trên máy; nghỉ ngắn không đòi chờ hồi âm. |
| `defend-old-choice` | Uống nước/thở chậm, body | Ngồi yên hai phút, rest | Nghỉ trước khi rà cách viết; không dựng người tranh luận. |
| `changed-plan` | Nghỉ ba phút, rest | Đi vài bước rồi nghỉ, body | Hai việc đều hoãn xếp lại khi giờ mới chưa chốt, không cần đang ở nhà. |
| `decision-fatigue` | Hoãn chọn năm phút/rửa mặt, body | Nhắm mắt một phút, rest | Cảnh chưa cần quyết ngay; không bắt đầu thêm bài hay ép chọn khi nghỉ. |

Cả tám slot vẫn pending. `lighter.issue.changed-plan.02` đã đổi chữ/digest trong vòng 1 tại
`0c6cebaf…`, gồm catalog `lighter_action.py`; vòng 2 không sửa slot hay catalog đó. Vì #699 chưa chốt,
reviewer cần đối chiếu câu và pin với #699 trước khi duyệt mở, giữ thứ tự/nhóm hình.
`EXTRA_LINE_SELECTION_ENABLED` vẫn False; không bật các lời Lá bổ sung pending.

Gate `evaluate_daily_rewrite` dùng neo nudge của giọng Thẳng. `voice.py` phục vụ thẻ Cà khịa viết sẵn,
không ghép từng phần từ Luna. Test gọi gate cả hai giọng: Thẳng đạt ở bốn bộ; Cà khịa của changed-plan
và defend-old-choice trả đúng `daily_companion_off_brief` vì chữ lời Lá khác neo Thẳng; hai bộ còn lại
đạt. Không nới gate, không sửa lời Lá cũ và không gọi hai kết quả bị từ chối là đã đạt rewrite.

## Kiểm chứng cục bộ ngày 25.11.2026

Dùng Python/dependency đã cài, chạy ngoại tuyến, không tải gói, sửa lockfile hay gọi API trả phí.
Lệnh dưới chạy trực tiếp theo yêu cầu người dùng, không phải receipt test guard hoặc author check.

Từ `apps/api`:

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

Kết quả cuối: **4.292 passed**, exit 0. File sinh viên có **123 ca**, thêm 16 so với vòng 1.
Trước sửa cổng, chạy riêng `-k light_slot_changes_while_bundle_is_pending` cho **16 failed** với
`DID NOT RAISE`; sau sửa cả 16 ca xanh trong bộ trên. Dữ liệu duyệt chỉ được dựng trong bộ nhớ.
Một lượt gọt câu thiếu neo và một lượt bị luật khẳng định quá khứ từ chối; đã sửa câu rồi chạy lại
đến xanh, không đổi chuẩn/gate hoặc bỏ test.

Các lệnh kiểm còn lại, chạy từ `apps/api`:

```sh
.venv/bin/python -m scripts.grammar_build --check
.venv/bin/python -m scripts.fallback_approval --check
.venv/bin/python -m scripts.audit_content_matrix
.venv/bin/python -m scripts.review_content_release
.venv/bin/python -m scripts.persona_validate
.venv/bin/ruff check tests/content/test_student_daily_situations.py
.venv/bin/ruff format --check tests/content/test_student_daily_situations.py
.venv/bin/python -m mypy tests/content/test_student_daily_situations.py
```

Tất cả đạt, exit 0. Audit giữ 630 Daily variants, 23 relationship concepts, 8 Radar themes.
Mypy có note override `prometheus_client` không dùng, không có lỗi. Content review là kiểm nội dung
đang phục vụ và clarity ratchet, không thay biên nhận duyệt chữ pending hoặc bộ 100 người giả.

Từ root repo:

```sh
node scripts/verify-no-mock-runtime.mjs
node scripts/verify-privacy.mjs
node scripts/verify-mobile-config.mjs
git diff --check
```

Cả bốn đạt, exit 0. Đối chiếu registry với HEAD đầu vòng 2: đúng 4 entry pending đổi chữ, tập ID và
mọi entry approved giữ nguyên; 12 phần sinh viên và 8 slot vẫn pending. Hai digest normal thay đổi
khớp chữ mới, nhóm hình giữ nguyên. Không đổi nhãn dựa trên nội dung người đọc.

## AC và ba cổng chất lượng

| AC | Bằng chứng cục bộ | Phần chưa hoàn tất |
|---|---|---|
| AC1 | Bốn bộ cho hai nhóm; normal + hai light mỗi bộ; render mọi arena/hai giọng; selector xoay cùng 12 bộ cũ. | #699, duyệt đồng bộ 12 phần + 8 light; xác minh phục vụ sau duyệt/merge trên môi trường được phép. |
| AC2 | Câu có điều kiện, không gán thiếu tiền/thất nghiệp hay dự đoán trúng tuyển; không thêm input hoặc phân nhóm người dùng. | Reviewer xác nhận nghĩa toàn thẻ trên diff cuối. |
| AC3 | Tất cả 20 mục pending, metadata duyệt trống; clarity/gate xanh; mạch hồ sơ một việc, đổi ca rõ chủ thể. | Biên nhận Codex duyệt chính chữ cuối; cập nhật pin và thay test pre-approval trong PR có biên nhận. Không tự đổi sang approved trong lượt sửa. |
| AC4 | Trường/ID/digest/cỡ/nhóm hình, ca âm/dương, 16 ca duyệt lệch đỏ rồi xanh; 4.292 test liên quan đạt. | CI và author check đúng commit chứa diff vòng 2. |

G1/G3 có bảng câu và AC; G2 thiếu ảnh; G4/G5 không đổi kiến trúc, API hoặc FE; G6 có test cục bộ,
thiếu full check/CI; G7/G8 rà dưới đây; G9 chưa phát hành; G10 không thêm dịch vụ/chi phí/dependency.
DoD và các cổng còn thiếu không được coi là đã hoàn tất vì test cục bộ xanh.

- Tài liệu/hợp đồng: không đổi schema, luật chọn hoặc API; hai nhãn digest khớp runtime đọc kho câu.
- Bảo mật: không đổi auth/session ownership, authorization/CSRF, endpoint/input/rate limit,
  crypto/key/log, dependency/network/storage, lỗi trả ra, share/invite/token hoặc đường xóa.
  Entry pending không phục vụ; hỏng digest không mở slot hoặc gọi dịch vụ dự phòng.
  Không phát hiện P0/P1 mới trong diff. Không thay quyền nền tảng hoặc lưu trữ native.
- Privacy: không thêm trường thu/suy ra/gửi/lưu/cache/log/chia sẻ/xuất/SDK. Ngày/giờ/nơi sinh,
  tọa độ, mood, quan hệ, định danh/token và profile suy ra giữ nguyên luồng hiện có.
  Các nhóm sinh viên chỉ là nhãn test/biên tập, không lưu hoặc gán cho người đọc.
  Mục đích, consent, retention, encryption, access/rút/xóa và bên nhận không đổi trong diff.
  Suy luận từ phạm vi mã: chưa có delta khai báo store/data map; chưa kiểm console hoặc binary release.

## Nguồn chính thức đối chiếu lại ngày 25.11.2026

| Nguồn và đường dẫn | Phần thực sự kiểm trong vòng 2 | Đối chiếu |
|---|---|---|
| [Luật 91/2025/QH15](https://vanban.chinhphu.vn/?docid=214590&pageid=27160) | Trang thuộc tính Chính phủ: ban hành 26.06.2025, hiệu lực 01.01.2026. PDF ký số không trích được chữ; không dùng nó để tuyên bố đã rà toàn văn luật. | Nhận diện văn bản nền; không coi thay câu là kiểm chứng tuân thủ toàn sản phẩm. |
| [Nghị định 356/2025/NĐ-CP](https://vanban.chinhphu.vn/?docid=216387&pageid=27160), [bản Công báo](https://congbaocdn.chinhphu.vn/180507251028987904/2026/1/17/356signed-1768638052103952849513.pdf) | Trang thuộc tính hiệu lực 01.01.2026; đọc Điều 3–4 trang PDF 2–3 về dữ liệu cơ bản/nhạy cảm và Điều 6 trang 5–6 về đồng ý kiểm chứng được, không mặc định đồng ý. | Bản sửa không thêm các trường đó, không biến đọc câu thành đồng ý thu dữ liệu. |
| [Apple App Review 5.1.1(i)–(v)](https://developer.apple.com/app-store/review/guidelines/#privacy) | Privacy policy, consent/rút, tối thiểu hóa dữ liệu, quyền truy cập và đăng nhập/thông tin bắt buộc. | Không thêm quyền/SDK/input hoặc yêu cầu khai nghề/hoàn cảnh. Không viết mới chữ privacy/consent trong app. |
| [Google Play User Data](https://support.google.com/googleplay/android-developer/answer/10144311?hl=en) | Full Policy, Prominent Disclosure & Consent Requirement: disclosure trước consent/permission, hành động đồng ý rõ ràng. | Không thêm thu/chia sẻ hay SDK; hành động đọc không thành consent. |
| [Google Play Data safety](https://support.google.com/googleplay/android-developer/answer/10787469?hl=en) | Overview: nhà phát triển chịu trách nhiệm khai đầy đủ/chính xác, gồm SDK. | Không có delta thu/chia sẻ trong diff; cần đối chiếu binary/console trước phát hành. |

Truy vấn chỉ dùng luật/chính sách và repo công khai. Đây là kiểm các mục ghi trên, chưa rà toàn bộ luật,
lịch sử sửa đổi hoặc tuân thủ của sản phẩm. Không dùng bảng làm quyết định bật luồng dữ liệu/phát hành.

## Việc còn thiếu và trách nhiệm tiếp tục

- Phiên điều phối xuất bản diff vòng 2 khi được giao; cập nhật SHA mới, liên kết CI và biên nhận đúng
  head vào bàn giao/Issue/PR. Chưa có SHA mới hoặc kết quả CI để điền trong lượt này.
- Theo ghi chú điều phối, `pnpm check`, CI/author check, ảnh preview 360/390 và mô phỏng 100 người giả
  trước/sau là việc của vòng tự động sau khi đẩy. Chưa chạy/quan sát chúng trên diff vòng 2, chưa có
  receipt, ảnh, điểm trước/sau hay mức tăng 0,2. Lỗi pnpm/browser/khóa ghi ở vòng 1 là lịch sử,
  không khẳng định đã thử lại các bước đó trong vòng 2. `persona_validate` không thay bộ 100 người.
- #699 vẫn mở; đối chiếu slot `lighter.issue.changed-plan.02` và digest catalog đã sửa vòng 1 trước duyệt mở.
  Codex cần đọc trọn bốn thẻ, meaning/takeaway/câu hỏi, hai giọng và tám slot rồi cấp biên nhận chữ cuối.
  Khi duyệt, cập nhật pin/test pre-approval trong PR có biên nhận; mô phỏng duyệt trong test không thay việc này.
- Sau duyệt/merge, xác minh normal/light trên môi trường được phép và thẻ cũ giữ nguyên. Đây là bước
  sau merge/duyệt, chưa thực hiện ở checkout pending. AC1/AC3 và DoD chưa được xác nhận hoàn tất.
- Khoảng trống cần owner theo R2/R12: phát hành ra người dùng thật, merge main hoặc deploy chưa được
  cấp trong task này. Giữ chưa phát hành. Không phát sinh chi phí/dịch vụ/quyền mới, chữ
  privacy/consent/crisis/safety hoặc bật thu dữ liệu mới; nếu bước sau cần chúng, ghi owner action,
  giữ cờ tắt và không tự quyết. Không viết lời đồng ý hoặc chữ nhạy cảm trong lượt sửa này.
- #923, #705–#708, chip/lưu chip và các mốc toàn hub không hoàn tất bằng PR nội dung này.
  Không đóng #704 với tuyên bố AC1/AC3 đã xong khi điều kiện trên còn thiếu.

## Còn khác ý

không có.
