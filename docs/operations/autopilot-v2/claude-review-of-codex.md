# Claude phản biện bản độc lập của Codex

## Nhận vào thiết kế chung (Codex có, Claude thiếu)

1. **Manifest quyền có chữ ký, nằm ngoài checkout của agent.** Mạnh hơn khoá theo diff của Claude. Hai agent dùng chung tài khoản, nên chỉ chữ ký ngoài tầm với của agent mới chứng minh owner thật sự ra lệnh.
2. **Idempotency key cho từng hành động** (task + head + policy). Nếu crash sau merge, lượt sau vẫn nhận ra merge đó và không đếm lại. Lô duyệt câu lưu digest đã chấm, nên câu bị từ chối không chặn mãi hàng sau (đúng lỗi verdict #451).
3. **Phải thử nhận thông báo thật trước khi nghiệm thu bề mặt owner.** Comment do tài khoản owner đăng không chứng minh owner đã nhận được.
4. **UAT tách credential thật**, không chỉ tách repo.
5. **Tiêu chí tester cụ thể.**
   - 5 người lớn tự nguyện, dùng miễn phí, được rút lui và xoá dữ liệu.
   - Tiếp tục khi ≥ 4/5 hoàn thành hành trình và nói được giá trị nhận được. Có lỗi an toàn hoặc riêng tư thì dừng.
6. **Canary định lượng.** ≥ 30 phiên đủ điều kiện, ≥ 24 giờ, có nhóm đối chứng, tính power trước. Không dùng traffic giả thay người thật.
7. **Rollback thật.** Có schema floor; giữ lại lệnh xoá và thu hồi qua bước restore. Khi không tương thích thì tắt tính năng, giới hạn phục vụ và sửa tiến.
8. **Ngân sách phiên owner chia rõ:** 10 phút kết quả, 20 phút quyết định, 20 phút mẫu theo rủi ro, 10 phút gu/đánh giá. Quá tải thì giảm WIP, không giấu việc.
9. **Bảng trạng thái 4 mức:** PR mở / đã merge integration / bản xem thử đang chạy / production đang chạy. Mỗi kết quả kèm URL, SHA, ảnh và phép kiểm.
10. **Giai đoạn bám theo lộ trình owner** (go-live → bảo mật/riêng tư → Lá Dám → café). Bảo mật cơ bản phải xong trước go-live. Analytics phải khớp Luật Bảo vệ dữ liệu cá nhân 91/2025, Nghị định 356, Apple App Privacy; dữ liệu đã đặt bí danh vẫn là dữ liệu cá nhân.
11. **Hợp đồng chỉ số (metric contract) khoá trước thí nghiệm:** nguồn, mẫu số, cửa sổ đo, mức cải thiện đáng kể, cỡ mẫu tối thiểu. Mỗi lần chỉ thay một biến. Traffic loại bot và nội bộ, không dùng clickbait.

## Không đồng ý (để thành thẻ hoặc giữ cách của Claude)

1. **Codex đề xuất bỏ "1–10 verifier", "xem lại main mỗi sáng" và quét bằng model rẻ.** Claude không bỏ mà chuyển cách làm:
   - Verifier chạy **tuần tự** trong ngân sách, số lượng co giãn theo rủi ro (0–3).
   - Buổi sáng chỉ là **tóm tắt để lướt**, không bắt owner đọc; owner xem trong phiên định kỳ.
   - Quét bằng model rẻ chỉ bật khi owner duyệt chi phí.

   Như vậy không vượt quyền và không quá tải hai agent. Ghi thành thẻ cho owner.
2. **Tick flow của Codex thiếu thứ tự rõ** giữa việc của mục tiêu, chỉ số đỏ, backlog và phát hành. Giữ thang 10 nhánh của Claude.
3. **Codex không có bảng chỉ số → hành động** gồm mục tiêu, đối trọng và việc cụ thể. Giữ bảng của Claude, cộng hợp đồng chỉ số của Codex.
4. **Codex nói "không cần điều phối thường trực".** Claude giữ điều phối nhưng ở dạng **file trạng thái cho mỗi mục tiêu + một lượt Claude**, không phải agent thường trực. Hai cách thực chất gần nhau, chỉ cần ghi rõ.
5. **Ma trận của Codex gộp theo khoảng mã** (ví dụ D19a–D19c), khó kiểm từng mục. Giữ ma trận từng mã của Claude.
6. **Cờ tính năng:** đồng ý với Codex là không dùng cờ cho refactor, chỉ cho hành vi có thể tắt. Cờ không thay cho rollback dữ liệu.
