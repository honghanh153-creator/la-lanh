# Việc nhẹ hơn đi kèm việc nhỏ của Daily (#627, PR #634)

Ngày: 17.11.2026. Người viết: Claude. Người review: Codex (vòng tự động). Mức: L (thêm trường vào hợp đồng API, thêm một trường tùy chọn vào dữ liệu mã hóa của việc đang giữ).

## Bối cảnh

Mốc "Ngày Đuối được việc nhẹ" đang ở 10,5%, đích là từ 90% trở lên (#627 AC2). App chưa có chỗ nào đưa ra việc nhẹ, và kho việc nhỏ gần như không có việc nhẹ. Thẻ Daily và Note đã chụp không được đổi sau khi tạo (US-04 AC14).

## Lựa chọn đã cân nhắc

1. Ai chọn việc nhẹ.
   - A. Máy chủ đọc mood đã lưu rồi đổi việc nhỏ của thẻ. Nhược: máy chủ dùng mood cho một mục đích mới, thẻ đổi sau khi tạo, mất mạng thì không đổi được.
   - B. Máy chủ trả sẵn cả hai việc, thiết bị chọn theo mood vừa chạm. Ưu: máy chủ không đọc mood, thẻ không đổi, chạy được khi mất mạng.
2. Thẻ nào nhận câu nào.
   - A. Chia theo số câu đang được duyệt. Nhược (Codex, vòng 1): duyệt thêm một câu làm thẻ cũ đổi câu, và khóa "giữ việc" của thẻ đang mở bị từ chối.
   - B. Lưu câu đã chọn vào revision. Nhược: đổi dữ liệu revision đã mã hóa, bản cũ không đọc được khi lùi bản; hoặc cần migration.
   - C. Danh sách cố định trong code (id câu + mã băm nội dung). Mỗi revision luôn rơi vào đúng một ô. Ô chưa được duyệt thì thẻ không có việc nhẹ.
3. Note đã lưu có giữ việc nhẹ không.
   - A. Có. Nhược (Codex, vòng 1): bản phát hành trước từ chối trường lạ, nên lùi bản làm hỏng danh sách Note đã lưu và file tải dữ liệu.
   - B. Không. Note đã lưu là bản chụp của Note; việc nhẹ là gợi ý lúc đang xem thẻ.

## Quyết định

- 1B, 2C, 3B.
- Câu chỉ được trả ra khi: đã duyệt, đúng mã băm trong danh sách, không quá 120 ký tự, và không nêu khoảng thời gian dài hơn 5 phút (định nghĩa "việc nhẹ" trong `qa/personas/judge-rubric.md`). Hai điều sau được kiểm lúc chạy, không chỉ lúc duyệt.
- Khi giữ việc nhẹ, câu được lưu trong phần đã mã hóa của bản ghi việc đang giữ, nên việc đang giữ vẫn đọc lại được sau khi câu rời sổ câu chữ.

## Hệ quả

- Khi mới duyệt một phần 12 câu, một số thẻ chưa có việc nhẹ. Mốc 90% cần ít nhất 11 trên 12 câu được duyệt.
- Sửa chữ một câu đã duyệt thì câu đó ngừng được trả ra cho tới khi danh sách trong code ghi mã băm mới. Câu chưa từng phát hành thì sửa mã băm tại chỗ. Câu đã phát hành thì thêm id mới.
- Thêm câu về sau: tạo danh sách mới, chỉ áp dụng cho revision mang dấu phiên bản mới. Không nối thêm hay đổi thứ tự danh sách hiện có, vì việc đó làm thẻ đã mở đổi câu.
- Hai ngày liền có thể trùng câu.

## Rủi ro và đường hỏng

- Khóa giả: khóa "giữ việc" chỉ được nhận khi đúng chủ, đúng revision đang hiện và đúng câu của ô đó đang được duyệt. Khóa tạo từ câu chưa duyệt bị từ chối (có test).
- Dữ liệu cá nhân: không thu thêm. Bản ghi việc đang giữ cho biết người đó đã chọn giữ việc nhẹ; vòng đời, hoàn tác và xóa như việc đang giữ hiện có. Câu là câu của kho, không phải lời người dùng.
- Lùi bản:
  - Note đã lưu: an toàn, vì không ghi trường mới (có test đọc lại bằng hợp đồng của bản trước).
  - Việc nhẹ đang giữ: bản cũ không đọc được bản ghi có câu việc nhẹ. Bản ghi như vậy chỉ xuất hiện sau khi có câu được duyệt và web có nút (PR B). Trước khi phát hành PR B phải ghi rõ điều này trong runbook phát hành: lùi bản qua mốc này cần xóa hoặc chuyển các bản ghi đó trước.

## Cách hoàn tác

Đặt 12 câu về `pending` (hoặc gỡ PR): API trả `lighter_action: null`, web bỏ qua trường này, không có dữ liệu nào cần dọn khi chưa ai giữ việc nhẹ.

## Chưa làm

- Research bên ngoài (mục 1b của quy trình) chưa làm cho quyết định này.
- Kịch bản QC thủ công của mức L làm cùng PR B, khi người dùng thấy được việc nhẹ.
