**CHỐT NẾU SỬA.** Chốt hướng; chưa mở auto.

**1. Bảy đề xuất Claude**

1. Đồng ý-sửa: cài lỗi trong sandbox; bắt 100% lỗi nghiêm trọng đã cài, không dùng 95% chung.
2. Đồng ý: verify P1, trước cấp quyền.
3. Đồng ý-sửa: chặn độ phức tạp tăng; refactor theo rủi ro, bỏ quota tách file.
4. Đồng ý-sửa: phân tầng sau khi chứng minh cổng; vẫn giới hạn tổng WIP.
5. Đồng ý-sửa: eval trước mở quyền, chạy lại khi đổi skill/model/policy; transcript chỉ gợi ý.
6. Đồng ý-sửa: replay tìm sai lệch; quyết định người không mặc nhiên đúng.
7. Đồng ý-sửa: lệnh dừng xác thực ngoài agent; hạn áp dụng cả tác vụ đang chạy.

**2. Phản hồi**

Nhận cả bảy điểm Claude chấp thuận, gồm [ngữ nghĩa merge-queue](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue). Nhận UAT do agent khác review, nối spec; thay đổi làm yếu tiêu chí kiểm phải bị chặn. Owner kiểm mẫu, giữ quyền chính sách. Nhận content trước, UX hỗ trợ; “hay hơn” cần so cặp mù, tiêu chí an toàn, mẫu độc lập.

**3. Top-10 cuối**

P0 = ngay; P1 = trước auto-merge; P2 = mở rộng; P3 = release.

| # | Cơ chế | Nghiệm thu | Pha |
|---|---|---|---|
| 1 | Broker, thu hồi credential cũ | Giả owner không vượt quyền | P0–1 |
| 2 | Khoá head/base/artifact/policy | Base đổi, huỷ evidence | P0–1 |
| 3 | Verify runtime, bản đồ tính năng | AC chạy trên artifact thật | P1 |
| 4 | Cài lỗi, eval skill kín | Bắt mọi lỗi nghiêm trọng đã cài | P1 |
| 5 | Trust theo loại, khoảng tin cậy | Vượt ngưỡng tự hạ quyền | P1–2 |
| 6 | Watchdog ngoài Mac, dừng | Tắt Mac vẫn báo; chặn merge | P1 |
| 7 | Review tầng, hàng rào kiến trúc | Lỗi lọt không tăng; WIP hữu hạn | P2 |
| 8 | Traceability kiểm nghĩa, replay | Phát hiện AC bị bỏ/sửa yếu | P1 |
| 9 | Content trước; bỏ quota thí nghiệm | So cặp thắng, đối trọng đạt | P2 |
| 10 | Go-live độc lập goal; canary, restore | Phục hồi giữ xoá/thu hồi | P3 |

**4. Trả lời owner**

Không bảo đảm tuyệt đối khi chạy auto.  
Chỉ cưỡng chế được bất biến đã kiểm trong phạm vi quyền bị khoá.  
Lỗi chưa biết vẫn có thể lọt; đo riêng từng loại thay đổi.  
“Hay” cần người đọc đánh giá, không suy từ test xanh.  
Rollback không xoá được hậu quả dữ liệu đã lộ.  
Hiện hai P1 còn đó, chưa đủ điều kiện mở auto.  
Release vẫn cần lệnh owner và bằng chứng riêng.

**5. Hai P1 sửa ngay**

- **Giả OWNER:** `isTrusted()` chỉ xét association. Thêm `author.login===ownerLogin` chặn fixture giả login, nhưng cùng tài khoản vẫn giả được. Vá an toàn ngay: `mergeGate` từ chối evidence comment tài khoản chung; không fallback. Mở lại bằng receipt xác thực từ signer độc lập. Test: OWNER sai/thiếu login, agent cùng login, marker giả đều bị từ chối; không gọi merge.
- **Base đổi:** lấy base SHA thật; PASS và APPROVE phải cùng head/base, thiếu tuple thì từ chối. Bỏ phụ thuộc marker retarget; huỷ cả PASS cũ. Test: B1→B2 không marker, retarget rồi chỉ review lại đều bị chặn; cấp lại cả hai mới qua. Thử base đổi giữa check/merge; chưa cưỡng chế nguyên tử thì giữ auto đóng.

Đối chiếu `05cc773`, trust/merge/tests và quy trình. Inbox/GitHub chưa đọc được; thiếu Node nên chưa chạy lại test. Không sửa file.