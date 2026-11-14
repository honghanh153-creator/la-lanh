# Codex kiểm soát, Claude thực thi — thiết kế của Codex (13.11.2026)

Owner 13.11.2026: "tôi cần codex là người kiểm soát còn claude sẽ thực thi". Văn bản dưới đây do Codex viết (chạy chỉ đọc, `codex exec`), Claude chỉ thêm tiêu đề này. Trạng thái từng lát nằm trong `scripts/collab-lessons.json` (L13, L17–L20). Lát 3, 4, 6 chờ owner duyệt vì đổi quyền và luật merge.

**Codex phải giữ quyền cho phép bắt đầu, công nhận hoàn tất và dừng việc. Claude thực hiện trong phạm vi được giao.** Giữ Codex chỉ đọc; chương trình riêng thực thi quyết định của Codex.

Tôi đối chiếu snapshot `b045f1c`, audit, memory, thỏa thuận A–L, thiết kế v2, scripts và GitHub. Ba PR vẫn mở. Phép thử dữ liệu giả xác nhận `mergeGate()` hiện chấp nhận PASS/APPROVE tự dựng bằng comment OWNER. Chưa chạy toàn bộ test; không sửa file.

### 1. Codex kiểm soát những quyết định nào

Dùng broker trong [thiết kế v2](https://github.com/honghanh153-creator/la-lanh/blob/b045f1c/docs/operations/autopilot-v2/README.md): chương trình giữ khóa, credential và trạng thái ngoài quyền ghi của hai agent. Broker tự gọi Codex bằng prompt đã khóa, nhận JSON trực tiếp, lưu biên nhận gắn task, head, base, bằng chứng và phiên bản policy. Claude không được nộp JSON thay Codex.

Các cơ chế dưới đây là **đề xuất, chưa vận hành**.

| Quyết định | Hôm nay ai quyết | Sau thay đổi | Cơ chế cưỡng chế | Claude vượt được không; phát hiện |
|---|---|---|---|---|
| Plan và thứ tự | Tick xếp PR; Claude bổ sung | Codex chốt 3–5 task trong ưu tiên owner | `collab-plan` đọc plan có biên nhận; khóa trước báo cáo 08h | Tự thêm task không được cấp lượt; báo task ngoài plan |
| Việc mới hay nợ workflow | Claude chọn | Codex ưu tiên nợ chặn và quá hạn | `collab-buffer` chỉ cấp task mới khi đủ điều kiện; giữ WIP 1+1 | Sửa nhãn không bỏ được nợ trong trạng thái chuẩn |
| Đóng bài học | Claude ghi nhận | Codex xác nhận; broker đổi trạng thái | Test lỗi cũ trượt, bản sửa đạt, caller chạy thật, bằng chứng đúng commit | Sửa JSON không đóng được; xóa mục hoặc dời hạn hiện trong diff |
| Review vòng ≥3 | Claude theo memory owner giao | Codex quyết tiếp tục sửa trong phạm vi; bất đồng phạm vi gửi owner | Broker đếm vòng; quyền tiếp tục có hạn; không tự xóa `needs-owner` | Xóa nhãn không tạo quyền; broker ghi lần thử |
| “Checklist-safe” Q1–Q5 | Claude tự đánh giá | Codex duyệt phạm vi; Claude tự chọn cách làm bên trong | Bộ kiểm diff cộng kết luận Codex; thiếu thông tin thì giữ | Khai sai trong body không thắng diff; mở rộng phạm vi phải xét lại |
| Báo cáo 08/14/22, retro | Claude viết; tick có bản tin 12/22 | Máy thu sự kiện; Codex chịu trách nhiệm kết luận | Một snapshot nguồn cho mọi kênh; lưu lịch sử báo cáo | Claude không sửa phần dữ kiện chuẩn; đối chiếu bản gửi với snapshot |
| Phân loại sự cố | Watchdog báo; Claude xử lý | Luật máy dừng ngay khi chạm ngưỡng; Codex phân loại và cho phục hồi | Trạng thái đóng băng giữ qua restart; chỉ cấp việc sửa sự cố | Tick khỏe không tự xóa sự cố; cần bằng chứng phục hồi |
| Sửa scripts/policy của loop | Claude làm, Codex review thường | Codex kiểm; owner duyệt thay đổi quyền | Broker chạy phiên bản đã khóa; diff chạm policy, prompt, CI, khóa phải qua owner | Merge code chưa tự cập nhật broker; lệch phiên bản bị báo |

Q1–Q5 vẫn giữ nguyên ranh giới owner. Bộ kiểm tự động không thể hiểu hết ý nghĩa thay đổi; trường hợp không rõ phải giữ lại cho Codex xét.

### 2. Báo cáo trung thực

Nguồn chuẩn gồm GitHub PR/CI, commit thực tế, biên nhận broker, kết quả kiểm runtime và nhật ký gửi thông báo. Mỗi dữ kiện có thời điểm và nguồn.

Báo cáo bắt buộc ghi:

- Plan gốc, phần thêm/bỏ, việc chưa đạt AC.
- Đã merge, đã chạy, đã phát hành thành các trạng thái riêng.
- Nợ quá hạn, sự cố chưa đóng, chờ owner và lượt Codex.
- “Chưa kiểm được” khi thiếu nguồn.

Claude được viết giải thích nguyên nhân và đề xuất, ghi rõ đó là nhận định của Claude. Codex kiểm các kết luận trước khi gửi. Máy bắt số liệu hoặc trạng thái không khớp; không thể bảo đảm bắt mọi câu tô hồng.

Retro lấy cùng dữ kiện, thêm **lỗi Codex duyệt sót**. Báo cáo phải tới chat/push theo lịch, có kết quả gửi và thử lại khi lỗi.

### 3. Ba PR tối nay

- **[#480](https://github.com/honghanh153-creator/la-lanh/pull/480): đúng hướng, còn thiếu.** Giữ quyết định trước khi xuất PR giúp tiết kiệm lượt. Nhưng sau ba lần lỗi, tick sau vẫn có thể trở lại xanh. Cần giữ sự cố đến lúc phục hồi; thử lại thông báo thất bại; cho xuất quyết định đã lưu khi hết cap vì bước này không gọi Codex.
- **[#481](https://github.com/honghanh153-creator/la-lanh/pull/481): dùng làm danh sách đề xuất, chưa đủ công nhận hoàn tất.** Claude được thêm bài học và bằng chứng; trạng thái chuẩn, hạn và việc đóng do Codex kiểm soát qua broker. `confirmClosed()` hiện nhận bất kỳ APPROVE tự động nào, không đối chiếu head hay verdict cuối. Cache chỉ theo bài học/PR không phát hiện bằng chứng đổi. Tìm tên test và chuỗi caller chưa chứng minh đã chạy; chế độ offline cũng không được in “đã chạy thật”.
- **[#482](https://github.com/honghanh153-creator/la-lanh/pull/482): sửa đúng thiếu sót, cần kiểm độc lập việc cài.** Hook có thể bị bỏ qua bằng `--no-verify`. [Git xác nhận hành vi này](https://git-scm.com/docs/git-push). Muốn kiểm soát trước khi dữ liệu lên repo công khai, broker phải giữ quyền push và quét trước upload; CI chỉ kiểm sau upload. Ruff/mypy chạy cấu hình PR cần môi trường cách ly.

### 4. Ranh giới và trách nhiệm của Codex

Owner giữ quyền main, deploy, server/DB thật, IAM/secret, dịch vụ trả phí, cap Codex, đổi hướng sản phẩm, copy UI và privacy/consent/crisis/safety.

**Giữ Codex chỉ đọc.** Codex không sửa code, giữ credential, đổi policy hoặc tự miễn bằng chứng cho kết luận của mình. Broker chỉ thực hiện các hành động đã được cấp quyền. Credential owner dùng chung phải rút khỏi Claude; cấu hình GitHub phải ngăn đường merge trực tiếp. GitHub hỗ trợ bắt buộc check từ [App xác định](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets).

Codex đã duyệt sót ở #451/#462. Vì vậy cần bộ lỗi cài sẵn và kiểm mẫu độc lập. Lỗi lọt phải mở lại bài học, sửa phép kiểm và ghi trách nhiệm reviewer.

### 5. Thứ tự triển khai

Mỗi lát do **Claude xây**, Codex kiểm.

| Lát | Nội dung | Codex kiểm; phép thử chứng minh | Owner |
|---|---|---|---|
| **1. Tối nay** | Hoàn thiện #480/#482, giữ PR riêng | Hai tick lỗi–phục hồi; hết retry vẫn báo lỗi; push thử có dữ liệu giả bị chặn; Git sạch không có danh tính vẫn commit được | Không đổi luật |
| 2 | Sửa #481 ở chế độ báo cáo | APPROVE cũ, bằng chứng thiếu, caller bị gỡ đều không thành “xong” | Không |
| 3 | Broker tối thiểu, tiếp nối #456 | Comment giả, chép receipt, đổi base, đọc khóa từ Claude, merge ngoài broker đều bị chặn | **Có: quyền và luật merge** |
| 4 | Phiếu giao việc cho plan, Q1–Q5, nợ và vòng ≥3 | Task ngoài plan, mở rộng phạm vi, tự đóng bài học bị từ chối | Có khi bật cổng mới |
| 5 | Báo cáo/retro chung nguồn, đóng băng sự cố | Giả mất nguồn, lỗi gửi, restart; vẫn báo thiếu và giữ sự cố | Theo policy đã duyệt |
| 6 | Kiểm Codex và sửa loop | Cài lại lỗi #451/#462; sửa policy không tự có hiệu lực | Có khi kích hoạt policy |

Chưa lát nào được tính hoàn tất chỉ bằng test xanh; phải có bằng chứng cơ chế đang chạy.

### 6. Ngân sách Codex

Ước tính thêm **5 lượt cố định/ngày**: plan kiêm báo cáo 08h, kiểm 14h, kiểm 22h, retro, kiểm mẫu. Thêm **0–2 lượt** cho đổi plan hoặc sự cố.

Với khoảng 20 lượt hiện tại: **25–27/32**. Thu dữ kiện, gửi báo cáo và thử lại xuất PR không cần AI. Dành bốn lượt cuối cho sự cố; hết ngân sách thì dừng cấp việc mới. Broker phải đếm mọi caller tự động, kể cả gọi trực tiếp. **Không đề xuất tăng cap.**
