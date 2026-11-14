**Chưa nên mở auto.** 166/166 chứng minh đủ mục được nhắc, chưa chứng minh chất lượng.

Đã đối chiếu A/B, repo tại `05cc773`, quy trình, checklist, gate và spec 1b. Inbox lỗi mạng nên chưa xác nhận PR mới nhất. Không sửa file.

1. So với Lauren

Lệch thiếu lý do: P4 nghiệm thu bằng một đêm thay lịch sử kiểm mẫu; eval skill tận P7 dù mở quyền P4; “không test chập chờn” thiếu cửa sổ chứng minh. Mọi thay đổi UAT chờ chủ sẽ gây tắc.

Lệch đúng: verifier tuần tự, WIP nhỏ, integration riêng, giữ cửa dữ liệu/phát hành cho người. Phù hợp hai agent, một Mac. Nhận outcome vượt thực hành Lauren, cần kiểm chứng riêng.

2. Mong muốn → mức đáp ứng trên thiết kế, chưa phải triển khai

| Mong muốn | Mức | Khoảng thiếu |
|---|---|---|
| Chạy khi ngủ | Một phần | Chưa thử mất Mac/mạng |
| Full-auto giữ chất lượng | Một phần | Chưa có lịch sử lỗi lọt |
| Chỉ giao outcome | Một phần | Chưa kiểm được nhân quả |
| Chỉ số thật, không lách | Một phần | ≥2 thí nghiệm/tuần vẫn ép sản lượng |
| Phản biện cả chủ | Đạt | Eval ngoài ba mẫu còn thiếu |
| Luôn báo tiến độ | Một phần | Watchdog cùng Mac cũng chết |
| Ý tưởng thành app có proof | Một phần | Go-live chờ P5 không cần thiết |
| Học ngoài, không cắt ngầm/thiên lệch | Một phần | Ma trận mã không kiểm nghĩa |
| Giá trị chưa đo được | Một phần | Nhãn A–E chưa chứng minh lợi ích |
| Spec/doc/US trong luồng | Đạt | Chưa chứng minh thực thi |
| Hai bên thiết kế/phản biện | Đạt | Chung tài khoản chưa độc lập quyền |
| Quyền chủ, roadmap, ngân sách thời gian | Một phần | UX trước content; tải chưa đo |

3. Bảy cải tiến theo tác động

1) Cô lập quyền: broker ngoài agent giữ credential; thu hồi PAT/phiên web cũ. Nghiệm thu: agent giả OWNER, gọi API, sửa gate đều không vượt quyền.

2) Khoá bằng chứng theo head, base, artifact, policy; base đổi phải kiểm lại bản ghép. Nghiệm thu: hai PR xanh riêng nhưng xung đột hành vi bị chặn. [GitHub](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue) dùng base mới khi kiểm.

3) Đưa verify và eval skill trước mở quyền. Kiểm runtime, fallback, thu hồi/xoá; cài lỗi chủ động. Nghiệm thu: bắt toàn bộ lỗi nghiêm trọng đã cài, trên đúng artifact.

4) Tách go-live khỏi tầng mục tiêu. Làm content → runtime → tester, giữ cổng security/privacy. Nghiệm thu: P5 chưa xong vẫn dựng được gói phát hành content.

5) Thay “một đêm/20 PR” bằng hồ sơ từng loại: lỗi lọt, mẫu tồn, khoảng tin cậy, hạ quyền. Nghiệm thu: vượt ngưỡng khoá đúng loại. 0/20 vẫn có cận trên khoảng 14% ở mức tin cậy 95%.

6) Watchdog ngoài Mac; tự cô lập sự cố khi chủ ngủ. Nghiệm thu: tắt Mac vẫn báo điện thoại; thử 14 ngày, tổng tải ≤60 phút/phiên.

7) Bỏ quota thí nghiệm; đăng ký giả thuyết, đối trọng, luật dừng trước đo. Nghiệm thu: bot traffic, thiếu mẫu hoặc đối trọng xấu không được tính thắng.

4. Có đảm bảo chất lượng?

Chỉ bảo đảm bất biến đã cưỡng chế trong mô hình đe doạ đã kiểm. Lỗi lọt và phạm vi ảnh hưởng chỉ giới hạn được. Không bảo đảm hết lỗi, nội dung hay hay tăng traffic.

Trước merge đêm cần bằng chứng mục 1–3, 5–6, kiểm mẫu thực, AC đạt. Full-auto release cần thêm lệnh ký, artifact bất biến, rollback/restore giữ xoá–thu hồi, canary đủ lực thống kê, SLO và kill switch đã thử. 30 phiên/24h không tự đủ; thiếu tín hiệu phải giữ. [Google SRE](https://sre.google/workbook/canarying-releases/)

5. P0/P1

Chưa xác lập P0. Hai P1 tại [gate hiện tại](scripts/collab-merge.mjs:7): comment OWNER giả lập vẫn qua; base đổi giữ bằng chứng cũ vẫn qua. Tôi xác nhận bằng gọi hàm với dữ liệu giả. Cô lập quyền, kiểm runtime và phục hồi vẫn chưa có bằng chứng nghiệm thu.