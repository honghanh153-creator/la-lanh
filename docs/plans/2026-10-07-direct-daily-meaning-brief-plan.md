# Daily Note direct, có ý nghĩa rõ

Ngày: 2026-10-07. Người dùng đã chọn bản direct và yêu cầu plan rồi triển khai.

## Quyết định đã chốt

Mẫu chuẩn: "Bạn gật đầu, nhưng vẫn chưa hiểu hết." Cảnh: "Cả nhóm chốt rất nhanh. Bạn có thể đồng ý theo, dù vẫn còn một chỗ muốn hỏi lại." Hành động riêng: "Hỏi ngay chỗ đó: Mình chưa rõ phần này, giải thích thêm được không?"

Không đổi UI, không deploy, không gọi API trả phí, không bật billing. CMS không phải điều kiện để note chạy tốt. Phạm vi là Daily Note Home, bài "Đọc thêm" của note và brief/gate của nhánh Daily rewrite; không gọi đây là việc viết lại toàn bộ Natal, Radar hoặc Tarot.

## Lỗi cần sửa

Matrix hiện ghép độc lập headline, scene, observation, advice và câu đệm. Một issue có nhiều tình huống khác nhau nên cùng issue vẫn có thể sai ngữ cảnh. Gate keyword đã cho qua chính câu "Ý kiến đông người dễ nghe giống ý kiến đúng". Brief hiện chuyển lại câu nguồn mà chưa giải thích người đọc cần hiểu điều gì.

## Các bước thực hiện

1. Biên tập 10 issue thành 10 tình huống rõ. Mỗi tình huống có cách viết khác nhau nhưng cùng một ý; không ghép quan sát của tình huống khác hoặc reflection chung chung.
2. Thêm meaning brief có core meaning, điều người đọc cần hiểu, dấu hiệu nhìn thấy được, giới hạn suy luận. Đây là ngữ cảnh biên tập, không phải sự kiện đã xảy ra với người dùng.
3. Truyền brief qua allowlist bảo mật hiện có. Luna chỉ đổi cách viết, không chọn vấn đề, thêm dữ kiện, sửa chart hoặc suy đoán ý định người khác.
4. Cập nhật prompt direct và gate. Test đúng câu đã bị phàn nàn, scene/action lệch nhau, lời khuyên chen vào scene, khẳng định chắc chắn, độ dài và contract cũ.
5. Nâng version và sửa note hiện tại bằng revision có kiểm soát. Không xóa profile, không viết lại bản share hoặc bản lưu đã đóng băng.
6. Giữ bài "Đọc thêm" giải thích cùng tình huống với Home. Biên tập câu hỏi nhìn lại cho từng tình huống; dùng cùng projection cho màn đọc, nút giữ thử nghiệm và khi tải lại thử nghiệm đã giữ.
7. Chạy kiểm thử offline, audit các mẫu tổng hợp, khởi động lại QA với generation tắt, kiểm tra Home và "Đọc thêm" thật.

## AC và DoD

- [x] Tiêu đề 3–11 từ; scene 8–40 từ; advice 4–24 từ; tổng tối đa 70 từ cho bản Home.
- [x] Mỗi issue có một cảnh và ý chính dễ nhắc lại; mọi biến thể cùng issue/action đều hợp cảnh.
- [x] Không có các câu đã bị phàn nàn hoặc câu đệm "Làm xong, xem tình hình có dễ hơn không".
- [x] Brief được giữ ở backend, hash vào rewrite key và đi qua PrivacyMinimiser; không thêm DOB, địa điểm, mood, chat hoặc định danh vào payload.
- [x] Cùng ngày replay ổn định; 365 ngày general không trùng bộ ba câu. Đây là khác cách viết, không phải 365 phát hiện tâm lý độc lập; lens hẹp có chu kỳ ngắn hơn.
- [x] Fallback hoạt động không cần Luna/CMS. Model timeout, từ chối hoặc không qua gate không thay thế fallback.
- [x] Test/lint/typecheck qua; QA hiện note mới mà không reset dữ liệu.

## Lỗi phát hiện khi đi hết flow

Home đã đổi cảnh nhưng thesis của "Đọc thêm" còn lấy từ cách ghép natal cũ. Nay thesis dùng meaning/takeaway của cùng issue. Câu hỏi sau thử nghiệm cũng đi theo issue, không còn hỏi chung chung về "một khác biệt nhỏ" ở Daily v4.

Đoạn transit của Daily chỉ mô tả dữ kiện góc và pha đang tính, không dùng nó để khẳng định một sự kiện sẽ xảy ra. Evidence gate trước đây so pha đã bỏ dấu với danh sách còn dấu nên loại cả claim đúng. Đã sửa bằng danh sách pha canonical được chuẩn hóa cùng cách và giữ test từ chối pha sai. Không tắt gate để cho qua nội dung.

Fingerprint lấy từ toàn bộ catalog Daily vào renderer version. Sửa câu chữ, meaning hoặc câu hỏi nhìn lại sẽ tạo revision mới mà không phải nhớ nâng version bằng tay.

## Kiểm tra trải nghiệm

Đọc mẫu của đủ 10 issue như người mới: chuyện gì đang xảy ra, câu nào nói rõ điều đó, advice có làm được ngay không? Mẫu tổng hợp không thay cho test với 10 người thật. Gate tự động bắt lỗi cụ thể, không bảo đảm hiểu hết tiếng Việt.

## Nguồn và giới hạn

US-03, daily psychology foundation, plain Vietnamese standard, Luna release runbook và AGENTS là contract nền. OpenAI hướng dẫn dùng context và ví dụ đầu vào/đầu ra trong [prompt engineering](https://developers.openai.com/api/docs/guides/prompt-engineering); [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs) giữ schema nhưng không bảo đảm nội dung đúng. Không tuyên bố đã đọc toàn văn sách hoặc chứng minh hành vi từ chiêm tinh.

Không đổi thu thập dữ liệu, consent, owner scope, chia sẻ hay ngân sách. Brief mới chỉ chứa copy do Lá Lành biên tập và cảnh minh họa; không truyền sự kiện riêng tư mới.

## Bổ sung từ kiểm tra browser

2026-10-08: Home chọn "Công việc" nhưng đường dẫn "Đọc thêm" và "Chia sẻ" chưa mang context, nên hai màn sau tự tải bản auto. Đây là lỗi nối flow, không phải lỗi sinh câu. Sửa link, parse context theo allowlist, tách query cache, giữ đúng lens khi chọn thử nghiệm và gửi revision đang hiển thị khi lưu/chia sẻ. Không đổi layout, không thêm dữ liệu cá nhân, không tự tạo public link trong QA.

Đã hoàn thành phạm vi Daily trên QA local. [Biên bản kiểm tra](../reviews/direct-daily-content-2026-10-07/qa-receipt.md) lưu kết quả test, ảnh thật, giới hạn và bước release còn lại. Chưa deploy/push hoặc chạy paid provider evaluation.
