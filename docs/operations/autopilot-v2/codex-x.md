1. Lỗi và lỗ hổng

- **P1:** T0.1/T0.2 thiếu gốc tin cậy ngoài quyền agent. Hash không chống sửa cả policy lẫn hash; [repo dùng chung tài khoản OWNER](scripts/collab-trust.mjs:33). Cần manifest owner ký, khóa ký và credential merge ngoài agent.
- **P1:** Mục 5 cho câu chữ tự phát hành, L4 tự deploy mâu thuẫn [danh sách cấm](docs/operations/decision-checklist.md). Policy không thay lệnh phát hành riêng.
- **P1:** P4 mở merge đêm trước UAT P5. Đưa UAT độc lập, kiểm quyền và bằng chứng đúng SHA thành điều kiện trước P4.
- **P1:** Freeze thiếu điều kiện thoát; kiểm ngân sách sau review; “chỉ sửa khi tái hiện được” bỏ lọt sự cố gián đoạn. Thêm chuyển trạng thái phục hồi có phép, kiểm quota trước từng hành động, cho cô lập dù chưa tái hiện.
- Sai baseline: #448–451 còn mở; #452 merged. [#451](https://github.com/honghanh153-creator/la-lanh/pull/451) đã sửa ba finding chặn nhưng chưa có verdict tại head `ed100bd`. Sửa chữ “xong” trong ma trận.

2. Nhận từ Claude

Giữ bốn tầng, ma trận từng ID, ngừng nhận tính năng khi phát hành quá hạn, findings gom nguyên nhân, kiểm định nghi thức hằng tháng, ca DST/giờ lịch sử, Daily đo qua runtime. Nhận dreaming ban đêm nhưng giới hạn ngân sách, chỉ đề xuất khi đủ bằng chứng. Bản tôi chưa cụ thể bằng.

3. Claude phải nhận

Tái dùng scripts hiện hữu; checkpoint, idempotency theo task/head/policy; đối soát merge trực tiếp và crash; digest câu bị bác, chống fork khóa hàng đợi; subscription kèm polling.

UAT/held-out phải tách credential và quyền đọc/ghi thật; “Codex giữ” hoặc khác repo chưa đủ. Khóa metric contract gồm mẫu số, cửa sổ, baseline, mức cải thiện, mẫu tối thiểu. Thiếu mẫu thì chưa kết luận.

Bảng owner tách PR/integration/preview/production; thử nhận thông báo thật; tối đa ba thẻ, tính cả interruptions. Thêm 360px, không chỉ 390px.

Rollback giữ deletes/revocations, có schema floor và fix-forward. Trước tester phải qua security/privacy; session, taste, feedback cần kho riêng tư, retention/xóa, cổng dữ liệu trước model theo [data map](docs/legal/store-privacy-data-map.md). Đã kiểm nguồn [Luật 91](https://vanban.chinhphu.vn/?docid=214590&pageid=27160).

Mỗi ID phải có AC, bằng chứng, trạng thái; ghi “ý sản phẩm” chưa tính hoàn thành.

4. Thẻ quyết định còn lại

- Shadow: A khớp vòng cũ ≥90% / B đạt 100% bất biến an toàn, giải thích sai khác / chọn B.
- Canary: A ngưỡng policy / B cố định 30 phiên, 24h / chọn A theo power, SLO.
- Tester: A chỉ tuyển năm người / B thêm ≥4/5 hoàn thành / chọn B cho usability, không suy retention.
- WIP: A owner nâng là chạy song song / B thêm bằng chứng khóa, quota, cô lập / chọn B.
- Critic: A hỏi thật nhiều / B chỉ hỏi dữ kiện quyết định / chọn B.
- Copy: A luôn 0 verifier AC / B theo rủi ro, giữ owner-only / chọn B.
- Café: A theo mục tiêu / B bắt buộc sau Lá Dám / chọn A, giữ gate trước tích hợp.
- Research: A luôn hai nguồn / B nguồn chính thức đủ chứng minh / chọn B.

5. **CHỐT NẾU SỬA**

Giữ cấu trúc Claude, áp sửa mục 1, nhận mục 2–3 và tám khuyến nghị. Chưa cấp quyền phát hành. Đã kiểm read-only; chưa chứng minh 167/167 hay chạy acceptance test.