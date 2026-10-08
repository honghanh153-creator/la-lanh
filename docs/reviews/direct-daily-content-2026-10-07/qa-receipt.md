# Daily content direct: biên bản QA

Plan bắt đầu 2026-10-07, hoàn thành QA local 2026-10-08. Phạm vi là Daily Home, Note Detail, brief/prompt/gate Daily và giữ đúng bản đọc khi chuyển sang share preview. Không phải bản release lại toàn bộ Natal, Radar hoặc Tarot.

## Thay đổi đã kiểm chứng

- Biên tập 10 issue thành tình huống cụ thể, với headline/scene/advice cùng ý. Bỏ observation ghép độc lập và câu reflection chung chung.
- Brief backend lưu nghĩa chính, điều muốn người đọc hiểu, trạng thái minh họa, anchors và câu hỏi nhìn lại. Không thêm hoàn cảnh riêng hoặc dữ liệu sinh vào provider payload.
- Prompt `surface-rewrite-v3` hướng Luna viết direct, không sửa chart, đổi vấn đề, invent motive hoặc coi cảnh minh họa là sự kiện đã biết.
- Gate Daily v2 chạy cả trước fallback publication; có regression cho chính câu "Ý kiến đông người dễ nghe giống ý kiến đúng", lệch scene/action, advice chen vào scene, khẳng định chắc chắn và hành động sai thời điểm.
- Thesis "Đọc thêm" giải thích đúng issue của Home. Câu hỏi sau thử nghiệm cũng theo issue, dùng cùng factory ở projection và kho thử nghiệm, kể cả khi giữ rồi tải lại.
- Evidence gate v2 sửa lỗi so pha đã bỏ dấu với giá trị còn dấu. Claim pha đúng được chấp nhận, pha sai vẫn bị từ chối. Daily transit giữ dữ kiện canonical thay vì gán một sự kiện cho người dùng.
- Fingerprint catalog vào renderer version để biên tập copy tạo revision mới. Sửa active deterministic cùng plan qua CAS; không reset profile hoặc viết lại history/saved/share snapshots.
- Home mang context vào "Đọc thêm" và share preview. Query key riêng; không lấy cache auto làm fallback cho context lỗi. Giữ thử nghiệm gửi đúng lens. Lưu/chia sẻ dùng revision trên màn hình, không dựa vào một request khác vừa chạy.

## Test cuối

| Kiểm tra | Kết quả |
|---|---|
| Backend `pytest -o addopts='-ra' -q` | 517 passed |
| Web `vitest run` | 189 passed, 47 files |
| Backend mypy | 274 source files, không có lỗi |
| Backend Ruff | check và format check qua, 301 files |
| Web TypeScript / ESLint / Vite build | qua; còn cảnh báo bundle JS lớn hơn 500 kB |
| OpenAPI + generated TS contracts | current |
| Runtime mock / privacy / mobile guards | qua |
| QA server unit tests | 3 passed; lần chạy sandbox bị chặn bind localhost đã được chạy lại với quyền bind |
| Toàn bộ tuple Daily được biên tập | 480 tuple qua direct gate |
| 365 ngày × 6 lens | qua gate; general có 365 bộ câu khác nhau |
| Content matrix audit hiện có | qua: 630 legacy daily variants, 23 relationship concepts, 8 Radar themes |
| Content Review Agent | 10 hồ sơ tổng hợp, 30 readings, không có critical/high; 36 medium follow-up ở Tarot |
| Rewrite corpus manifest | 670 case tổng hợp, 13 surfaces; chỉ manifest, không phải paid model scoring |
| `git diff --check` | qua |

480 tuple là cách viết của 10 tình huống, không phải 480 insight độc lập. General không lặp bộ ba câu trong test 365 ngày; lens hẹp vẫn có thể lặp sớm hơn. Gate từ khóa/độ dài không bảo đảm mọi câu đều dễ hiểu đối với mọi người.

## Browser thật

QA: `http://127.0.0.1:5207`, API `8027`. Dùng lại database QA theo port, không reset dữ liệu. Generation và worker đều tắt.

1. Home tải được bản direct, note nằm trước các route khám phá.
2. Chọn "Việc cần chốt". Home hiện "Bạn bận cả buổi, việc vẫn chưa xong." cùng cảnh chuyển việc và action chọn việc làm trước.
3. Bấm "Đọc thêm" tới `/note/today?context=work`. Giữ nguyên headline, scene và action; thesis nói đúng chuyện nhiều việc dang dở.
4. Bấm giữ thử nghiệm, tải lại: vẫn đúng bản work và câu hỏi "Bạn đã chọn được việc làm trước và biết việc nào để sau chưa?". Bỏ giữ sau QA để không để lại một việc đang giữ.
5. Mở preview `/card?context=work`: đúng headline/scene từ bản work. Không bấm tạo public link hoặc gửi dữ liệu ra ngoài.

Ảnh thật:

- [Home](01-home.png)
- [Note detail](02-note-detail.png)
- [Share preview](03-share-preview.png)

## Security, privacy và nguồn

Brief do server biên tập được kiểm tra bằng model `extra=forbid`, PrivacyMinimiser và tests chặn PII lồng trong brief/câu hỏi. URL chỉ chứa context nằm trong allowlist, không chứa ngày/giờ/nơi sinh hoặc câu hỏi riêng. Owner scope, CSRF, consent và chính sách chia sẻ không bị nới lỏng. Các test giữ thử nghiệm tiếp tục kiểm tra active revision, action key, CAS và từ chối client-authored text.

Hướng brief và ví dụ được đối chiếu với [OpenAI prompt engineering](https://developers.openai.com/api/docs/guides/prompt-engineering). [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs) không bảo đảm nội dung có nghĩa; gate và bản biên tập vẫn cần thiết. Đây là kiểm tra local/fixture, không có provider call hoặc chi phí API trong lần làm này.

## Giới hạn và bước tiếp theo

- Chưa deploy production, push GitHub hay bật generation. Bản live chưa nhận thay đổi này.
- Chưa test với 10 người thật. Hồ sơ tổng hợp kiểm tra coverage/gates, không đo mức dễ hiểu thực tế.
- Natal/Radar/Tarot và copy điều hướng không được viết lại toàn bộ trong scope này. 36 cảnh báo medium lặp câu Tarot vẫn cần xử lý riêng.
- Chart signature hiện xoay editorial slots; nó không chứng minh một hành vi tâm lý từ natal/transit. Không gọi Daily psychology copy là sự kiện app đã quan sát hoặc dự báo chắc chắn.
- Active generated revision cũ vẫn đi qua available-update/activation hiện có, không bị âm thầm thay bằng một bản generated khác. Bản deterministic cùng plan được sửa qua CAS.
- Trước khi bật Luna cho bản prompt mới cần evaluation so với fallback. Paid evaluation hoặc deploy live là bước riêng, không tự phát sinh phí từ tài liệu này.
