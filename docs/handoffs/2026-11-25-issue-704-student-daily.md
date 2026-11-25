# Bàn giao #704: nội dung sinh viên tuần 2

Codex triển khai cục bộ theo kế hoạch cuối và sáu phản biện người dùng cung cấp. Cỡ M.
Nhánh `agent/codex/issue-704`, base và HEAD vẫn là `d3818f59b47cccccd8d59560fcb5e3d9625a294c`.
Thay đổi chưa commit. Người dùng yêu cầu không mạng, không commit/push; chưa đăng issue/PR,
đọc inbox hay đồng bộ integration. Không suy ra tình trạng claim/WIP từ checkout sạch.
Review độc lập trên thay đổi cuối và author check từ CI vẫn còn thiếu.

## Phạm vi và nguồn đã đọc

- `AGENTS.md`; luật đang hiệu lực R1–R17; quy trình cộng tác, phát triển sản phẩm và checklist quyết định.
- Nội dung #704 và kế hoạch cuối, phản biện trong yêu cầu của người dùng. Các tham chiếu
  #502/#686/#699/#708/#923 là nguồn được cung cấp, chưa đọc lại trên GitHub trong lượt ngoại tuyến.
- PRD phần F1.2; SRS phần Daily; US-03 AC18, delta Home và §22; US-04 AC10/AC14.
- `docs/foundation/la-lanh-plain-vietnamese-content-standard.md`, `qa/personas/judge-rubric.md`.
- `copy_approval.py`, `daily_psychology.py`, `companion.py`, `companion_pool.py`,
  `lighter_action.py`, `action_tags.py`, renderer và đường trình bày giọng.
- Bảy file test được kế hoạch chỉ định. Rà tham chiếu cả bốn vấn đề trong tests, web, packages,
  docs: chỉ số đếm riêng của `changed-plan` cần tăng lên 13 bộ. Số 12 của
  `capacity-before-agreement` giữ nguyên. Không thấy snapshot hay danh sách FE cần đồng bộ.

Chọn thêm bundle vào vấn đề hiện có. Không thêm vấn đề, runtime, API, schema hoặc luật chọn.
Câu mới thuộc nhóm reading và chờ duyệt; không phát sinh chi phí, dịch vụ, quyền truy cập,
chữ nhạy cảm hay dữ liệu cá nhân mới. Không có bước cần owner trong phạm vi sửa cục bộ này.

## Danh sách 12 câu mới

Tất cả đều `category: reading`, `status: pending`, không có `approver`, `date`, `digest` duyệt.
Nhóm biên tập chỉ xuất hiện trong test và bảng này, không gắn vào người dùng.

| Nhóm | Bundle | Headline | Scene | Action và nhãn |
|---|---|---|---|---|
| Đang tìm việc | `daily.bundle.perfect-before-start.13` | Khi hồ sơ sắp hết hạn nộp. | Khi sát hạn nộp hồ sơ, bạn vẫn sửa bản nháp đủ ý trên máy trước khi gửi xin góp ý. | Gửi bản nháp hồ sơ cho người góp ý, hỏi một chỗ cụ thể cần sửa. `normal / connection` |
| Đang tìm việc | `daily.bundle.defend-old-choice.13` | Khi nơi định nộp đã đóng hồ sơ. | Khi nơi tuyển dụng ngừng nhận hồ sơ, bạn vẫn giữ cách viết cũ vì tiếc công sửa. | Kiểm tra kết quả cách cũ, chọn một phần hồ sơ cần thay đổi cho nơi còn nhận. `normal / study_work` |
| Vừa học vừa làm | `daily.bundle.changed-plan.13` | Khi đề nghị đổi ca trùng giờ học. | Khi ở nhà, bạn nhận đề nghị đổi lịch ca trùng giờ học, giờ mới chưa chốt. | Nói rõ giờ học cần giữ và đề xuất giờ khác để hai bên chốt ca mới. `normal / boundary` |
| Vừa học vừa làm | `daily.bundle.decision-fatigue.13` | Khi mệt sau ca, bài còn nhiều phần. | Khi mệt sau ca làm, bạn chọn mãi giữa các phần bài, chưa cần chốt ngay. | Chọn hạn nộp làm tiêu chí, gạch bớt các phần bài chưa cần chọn lúc này. `normal / study_work` |

## Đối chiếu nghĩa và tám cách ghép việc nhẹ

Đã đọc đủ 12 câu theo R15: tiếng Việt đời thường, ngắn, cụ thể, không thơ,
không giải thích nguyên nhân kỹ thuật. Cả bốn headline/scene có điều kiện, không khẳng định
người đọc thất nghiệp, thiếu tiền hay làm nghề cụ thể. Không hứa tuyển dụng, đoán ý nhà tuyển dụng
hoặc dự đoán sự kiện. Đây là rà nghĩa của tác giả, chưa thay thế review độc lập.

| Vấn đề | Meaning, takeaway, câu hỏi và hai giọng Lá | Ghép slot .01 | Ghép slot .02 |
|---|---|---|---|
| `perfect-before-start` | Bản nháp đủ ý nhưng sửa mãi; gửi để xin góp ý. Action nêu rõ người góp ý, không gửi hồ sơ chưa xong để ứng tuyển. | Duỗi vai/cổ một phút, để bản nháp trên máy. Hợp cảnh, một mình, không liên lạc/học/làm/chọn/đánh giá. `light / body` | Gấp máy, thở năm hơi. Cảnh có máy và bản nháp. Cùng tiêu chí việc nhẹ. `light / rest` |
| `defend-old-choice` | Tiếc công giữ cách cũ, xem kết quả trước khi bỏ thêm công. Action đổi một phần cho nơi còn nhận; không tiếp tục đầu tư vào nơi đã đóng. | Uống nước, thở chậm; ngừng cố giữ cách cũ để công đã bỏ ra không uổng. Không dựng người tranh luận. Một mình, không liên lạc/học/làm/chọn/đánh giá. `light / body` | Ngồi yên hai phút rồi mới nghĩ cách cũ/mới. Cảnh có cách viết cũ; nghỉ trước khi đánh giá. `light / rest` |
| `changed-plan` | Giờ mới chưa chốt; giữ giờ học và đề xuất giờ khác để hai bên thống nhất, hợp câu hỏi về giờ mới. | Nghỉ ba phút trước khi xếp lại. Đề nghị thay lịch đã đến nhưng ca chưa chốt, không cần xử lý ngay. Một mình, không liên lạc/học/làm/chọn/đánh giá. `light / rest` | Đi một vòng quanh nhà. Scene nói rõ đang ở nhà; chưa cần chốt lịch. `light / body` |
| `decision-fatigue` | Mệt và đang cân nhắc nhiều phần bài; dùng hạn nộp làm tiêu chí để bớt lựa chọn. Không mở thêm việc hay ép học ngay. | Hoãn chọn năm phút, rửa mặt. Scene nói chưa cần chốt ngay. Một mình, không liên lạc/học/làm/chọn/đánh giá. `light / body` | Nhắm mắt một phút, chưa chọn. Hợp cảnh mệt sau ca, không quyết định gấp. `light / rest` |

Tám slot `lighter.issue.<vấn đề>.01/.02` giữ nguyên chữ, thứ tự, digest và nhóm hình.
Cả tám vẫn pending, chưa có bằng chứng phục vụ thật sau duyệt.

Fixture phê duyệt chỉ tồn tại trong bộ nhớ test. Renderer/selector thật chọn trọn từng bundle;
test đi qua GENERAL và mọi arena của từng vấn đề, cả Direct/Cà khịa, cả hai slot việc nhẹ.
Headline/scene/action mới chưa có cặp Cà khịa riêng nên giữ chữ direct theo fallback hiện hành;
lời Lá đổi đúng cặp giọng đã viết sẵn. Meaning, takeaway và câu hỏi quan sát vẫn của cùng vấn đề.

`EXTRA_LINE_SELECTION_ENABLED` giữ `False`. Những câu bổ sung pending chưa hợp cảnh mới gồm:

- `la.issue.decision-fatigue.01.roast`: nói gọi món;
- `la.issue.decision-fatigue.04.roast`: nói mở tab so giá;
- `la.issue.defend-old-choice.02.direct`: yêu cầu so kết quả giữa hai tuần;
- `la.issue.defend-old-choice.01.roast`: giả định đã làm ba tuần;
- `la.issue.perfect-before-start.02.roast`: giả định bản nháp đã nằm một tuần.

Không duyệt các câu này. Việc bật chọn lời bổ sung cần review ghép nghĩa riêng.

## Gate CI và kiểm chứng

Gate trong `tests/content/test_student_daily_situations.py`, được pytest của `api:test` thu thập.
Chỉ xét bốn bundle liệt kê tường minh. Bất kỳ một phần servable kích hoạt yêu cầu đủ ba phần
và cả hai slot nhẹ; dùng `CopyEntry.servable`, `registry_problems`, digest NFC, `light_slots`
và `lighter_action_for`. Nhãn việc thường được kiểm cả khi bundle chưa phục vụ.
Test lâu dài không khóa câu ở pending mãi; kiểm chứng trạng thái pending của lần thêm này là
đối chiếu riêng với base.

Ca âm gồm sáu cách duyệt thiếu 1–2 phần cho mỗi bộ, thiếu phần, slot nhẹ pending/thiếu/sửa chữ
và duyệt lại, metadata sai/thiếu, nhãn thiếu/sai hình/sai digest/sai cỡ, catalog thiếu slot/sai hình,
giới hạn độ dài/năm phút của runtime. Ca dương giữ bundle cũ phục vụ khi cả bốn bộ mới pending,
và mở từng bộ mới đầy đủ trong khi ba bộ còn lại vẫn pending.

Môi trường: dependency lấy từ cache máy sang `<thư mục cache tạm>`, dùng
`UV_OFFLINE=1 UV_CACHE_DIR=<thư mục cache tạm>`; không tải mạng hoặc sửa lockfile.
`make -C vendor/swisseph` build thư viện đã có mã nguồn trong repo, không sửa file được theo dõi.

```sh
uv run --offline --directory apps/api pytest \
  tests/content/test_student_daily_situations.py \
  tests/content/test_daily_variants.py \
  tests/content/test_daily_scene_bundles.py \
  tests/content/test_copy_approval.py \
  tests/readings/test_daily_bundles.py \
  tests/readings/test_issue_light_store.py \
  tests/readings/test_action_tags.py
```

Kết quả: **4.271 passed**, gồm 102 test mới. Test kiểm kê đỏ trước khi thêm nội dung vì thiếu
`perfect-before-start.13.headline`. Lần chạy đầu bộ bảy file thiếu thư viện Swiss Ephemeris;
sau build cục bộ đã xanh. Không nới assertion nội dung để bỏ lỗi.

Các lệnh sau đều exit 0, tương đương phần Python của grammar:check/content:audit/content:review:

```sh
uv run --offline --directory apps/api python -m scripts.grammar_build --check
uv run --offline --directory apps/api python -m scripts.fallback_approval --check
uv run --offline --directory apps/api python -m scripts.audit_content_matrix
uv run --offline --directory apps/api python -m scripts.review_content_release
uv run --offline --directory apps/api python -m scripts.persona_validate
uv run --offline --directory apps/api ruff check tests/content/test_student_daily_situations.py tests/content/test_daily_variants.py
uv run --offline --directory apps/api ruff format --check tests/content/test_student_daily_situations.py tests/content/test_daily_variants.py
uv run --offline --directory apps/api mypy tests/content/test_student_daily_situations.py
git diff --check
```

Audit: 630 Daily variants, 23 relationship concepts, 8 Radar themes; clarity ratchet đạt,
không tăng số lỗi/giảm độ phủ. Mypy không có lỗi; chỉ nhắc cấu hình override prometheus chưa dùng.
Log tại `/private/tmp/issue-704-{tests,grammar,approval,audit,review}.log`.

Đối chiếu registry với HEAD bằng Python: đúng 12 ID mới, đều pending và không có metadata duyệt;
mọi entry cũ và nhãn cũ giữ nguyên, chỉ thêm bốn nhãn normal.
Approved pin giữ nguyên, Daily fingerprint trước/sau đều `ac130cb3`.

## AC và ba cổng chất lượng

| AC | File | Kiểm chứng và phần chưa hoàn tất |
|---|---|---|
| AC1 | `copy_registry.json`, `normal_action_tags.json` | Bốn bộ/12 câu, hai nhóm biên tập; normal + hai slot light; test inventory và render hai giọng/mọi arena. Phục vụ thật chờ duyệt cả bộ và tám việc nhẹ. |
| AC2 | Kho câu và fixture trong `test_student_daily_situations.py` | Rà nghĩa trên toàn thẻ như bảng trên; test chỉ dùng đầu vào hiện có. Không thêm/suy ra trường nghề nghiệp, thu nhập, tình trạng việc làm hay nhóm sinh viên. |
| AC3 | Kho câu, `test_daily_variants.py`, test mới | 12 câu pending, qua kiểm độ rõ và cổng nội dung/R15. Chưa có review độc lập hoặc phê duyệt mở khóa. |
| AC4 | `test_student_daily_situations.py` | Kiểm kê rõ bốn bộ, trường bắt buộc, ID duy nhất, digest, cỡ, nhóm hình, hai slot, ca âm/dương và runtime. Local xanh; CI đúng head chưa chạy. |

- Tài liệu/hợp đồng: không thay runtime, API hay schema; AC và các phần chờ được ghi ở trên.
- Bảo mật: diff chỉ kho câu, nhãn, test và bàn giao; không thay phiên/quyền/CSRF/endpoint/input/log,
  dependency, storage, mạng, share/token hoặc xóa. Pending vẫn không phục vụ; gate ngăn duyệt dở.
- Privacy: không có trường dữ liệu cá nhân mới được thu/suy ra/lưu/cache/log/chia sẻ/xuất/gửi SDK;
  không phân nhóm người dùng, đổi mục đích mood hay thêm analytics. Không sửa privacy/consent/crisis/safety.
  Không phát sinh thay đổi pháp lý/chính sách nền tảng cần xác minh online trong phạm vi này.

## Việc còn thiếu trước merge hoặc kết luận đạt toàn bộ

- 100 người giả trước/sau: đã chạy `persona_validate` đạt và chuẩn bị bản nguồn base bằng
  `git archive HEAD` trong `/private/tmp/issue-704-before`. Lệnh chạy before qua
  `scripts/collab-test-guard.mjs --wait-min 0 -- uv ... python -m scripts.persona_run
  --name issue-704-before-d3818f59 --workers 1` bị EPERM khi tạo khóa chung ngoài checkout.
  Không chạy vòng mô phỏng nào, không thay vị trí khóa để né R10. Chưa có báo cáo, so sánh hay điểm;
  mọi chỉ số trước/sau ghi **chưa đo**. After cũng còn thiếu. HEAD chưa đổi vì không commit.
- Preview 360/390: đã tạo fixture HTML cục bộ với CSS Home, hai giọng và ba lựa chọn action tại
  `/private/tmp/issue-704-preview-360.html` và `issue-704-preview-390.html`. Dùng font hệ thống,
  chưa phải kiểm chứng font ứng dụng. Chromium bị sandbox chặn MachPortRendezvous;
  browser host của CUA cũng unavailable. Chưa có ảnh hoặc kết luận đạt khả năng đọc/tràn dòng.
- Chưa có `pnpm check`, CI đúng head, author check, reviewer độc lập, PR, merge hay phát hành.
  Không đóng #704 với kết luận đạt đầy đủ AC1 trước khi xác minh phục vụ sau duyệt.
- #923 vẫn ngoài phạm vi: chưa giải quyết độ phủ nhãn việc thường trong Python hoặc Plan link
  của PR trước. #705–#708 và phát hành vẫn riêng; không tuyên bố đạt mức tăng 0,2 hay mốc tuần 2.
