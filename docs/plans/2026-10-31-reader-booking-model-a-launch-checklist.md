# Checklist triển khai đọc tarot với người thật — mô hình A

Ngày: 31.10.2026
Trạng thái: kế hoạch, chưa triển khai. Tính năng mới, xếp sau nội dung và quyền riêng tư theo thứ tự ưu tiên hiện hành.
Áp dụng cho: PRD F5.2 Reader Booking ([la-lanh-prd.md](../foundation/la-lanh-prd.md), mục 5) và cột Paid "Reader đọc sâu" trong [product plan v2](../foundation/la-lanh-product-plan-v2.md), Phần 8.

## Mô hình đã chọn

**Lá Lành bán dịch vụ, người đọc bài (Lá Dẫn) là cộng tác viên.**

- Người dùng mua buổi đọc của Lá Lành. Lá Lành là bên bán, xuất hóa đơn, chịu trách nhiệm với người tiêu dùng.
- Lá Dẫn ký hợp đồng cộng tác (dịch vụ) với Lá Lành, nhận thù lao từ Lá Lành, không tự bán hay tự thu tiền trên app.
- Không mở cho Lá Dẫn tự đăng ký bán. Danh sách Lá Dẫn do Lá Lành tuyển và duyệt.

Vì sao chọn A cho bản đầu: ít Lá Dẫn, dễ kiểm soát giọng và chất lượng; không phải vận hành nghĩa vụ của nền tảng trung gian theo Luật Thương mại điện tử 2025 (định danh người bán, khấu trừ thuế thay người bán theo NĐ 117/2025). Điều kiện giữ mô hình A: Lá Dẫn không được tự đặt giá, tự đăng gian hàng hay nhận tiền trực tiếp từ người dùng. Nếu sau này muốn mở như vậy thì phải làm lại checklist cho mô hình sàn.

Ký hiệu người làm: **[Chủ]** chủ sản phẩm, **[KT]** kỹ thuật, **[VH]** vận hành/hỗ trợ, **[ND]** nội dung.

## Cổng 0 — Phạm vi bản đầu (chốt trước khi viết code)

- [ ] [Chủ] Chỉ bán **buổi đọc 1–1 trực tiếp** (thời gian thực: gọi thoại/video hoặc chat trực tiếp trong khung giờ đã đặt). Đọc bất đồng bộ (gửi câu hỏi, trả lời sau) và phòng nhóm để sau, vì cả hai bắt buộc dùng IAP trên iOS (xem Cổng 3).
- [ ] [Chủ] Chỉ loại đọc "Hiểu bản thân sâu hơn" (Natal Chart). Loại "Hiểu một mối quan hệ" (Composite Chart) **tạm khóa** cho tới khi có cách lấy đồng ý của người thứ hai (xem Cổng 4).
- [ ] [Chủ] Chỉ người dùng đã đăng nhập, từ 18 tuổi trở lên, được đặt buổi trả phí.
- [ ] [Chủ] Chốt số Lá Dẫn chạy thử, số buổi tối đa mỗi tuần, thời lượng buổi và thời điểm dừng thử. Giá, tỉ lệ thù lao và ngân sách ghi ở tài liệu nội bộ, **không ghi vào repo công khai**.
- [ ] [Chủ] Ghi rõ những gì **không** bán: giải hạn, vật phẩm tâm linh, cam kết kết quả, tư vấn sức khỏe/tài chính/pháp lý, buổi bán thêm do Lá Dẫn tự mời.

## Cổng 1 — Pháp nhân, thuế, thanh toán

- [ ] [Chủ] Có pháp nhân (doanh nghiệp hoặc hộ kinh doanh) đứng tên bán dịch vụ, ngành nghề đăng ký bao phủ dịch vụ này. Tên pháp nhân, địa chỉ, mã số thuế hiển thị ở trang điều khoản và hóa đơn.
- [ ] [Chủ] Thông báo website/app thương mại điện tử bán hàng với Bộ Công Thương trước khi nhận tiền thật. Đối chiếu nghĩa vụ hiện hành theo Luật Thương mại điện tử 2025 (hiệu lực 01.07.2026) và nghị định hướng dẫn.
- [ ] [Chủ] Hóa đơn điện tử cho từng buổi đã thu tiền; kê khai GTGT/TNDN theo pháp nhân đã chọn.
- [ ] [Chủ] Thuế TNCN khi trả thù lao Lá Dẫn: khấu trừ tại nguồn với thu nhập vãng lai. **Kiểm tra lại ngưỡng hiện hành** trước khi trả lần đầu: hướng dẫn cũ dùng 2 triệu đồng/lần, một số nguồn nói ngưỡng mới là 5 triệu đồng/lần theo văn bản hướng dẫn Luật Thuế TNCN mới (NĐ 253/2026/NĐ-CP). Đọc văn bản gốc, không dùng bài tư vấn.
- [ ] [KT] Thanh toán qua cổng có giấy phép (VNPay, MoMo, PayOS hoặc tương đương). Lá Lành **không** lưu số thẻ/tài khoản người dùng; chỉ lưu mã giao dịch, số tiền, trạng thái.
- [ ] [KT] Tiền vào tài khoản của pháp nhân Lá Lành, không chia tách trả thẳng cho Lá Dẫn tại thời điểm thanh toán (giữ đúng mô hình A).
- [ ] [VH] Quy trình đối soát hằng tuần: giao dịch cổng ↔ booking ↔ hóa đơn ↔ hoàn tiền.
- [ ] [Chủ] Lịch trả thù lao: chỉ trả cho buổi đã `completed` và hết thời hạn khiếu nại (giữ 7–14 ngày như PRD F5.3). Không trả theo số buổi Lá Dẫn tự khai.

## Cổng 2 — Nội dung và giới hạn pháp lý của buổi đọc

Rủi ro: NĐ 38/2021/NĐ-CP (Điều 14) xử phạt hành chính hoạt động mê tín dị đoan; nặng hơn là Điều 320 Bộ luật Hình sự. Lá Lành định vị buổi đọc là **soi chiếu, giúp người dùng tự hiểu mình**, đúng giọng sản phẩm hiện tại.

- [ ] [ND] Bộ quy tắc Lá Dẫn (đính kèm hợp đồng), tối thiểu:
  - không phán chắc chắn chuyện tương lai, không nói "chắc chắn sẽ", "số bạn là";
  - không giải hạn, không bán hay giới thiệu vật phẩm, lễ, dịch vụ ngoài;
  - không khuyên về chẩn đoán/điều trị, đầu tư, pháp lý; chỉ gợi ý tìm người chuyên môn;
  - không hù dọa, không tạo cảm giác phải mua thêm buổi;
  - không xin số điện thoại, mạng xã hội, chuyển khoản riêng; không hẹn gặp ngoài;
  - không ghi âm/chụp màn hình phía Lá Dẫn.
- [ ] [ND] Lời giới thiệu trước khi đặt: buổi đọc là trải nghiệm soi chiếu, không thay thế tư vấn chuyên môn. Câu chữ ngắn, ấm, theo [chuẩn tiếng Việt dễ hiểu](../foundation/la-lanh-plain-vietnamese-content-standard.md); không viết như cảnh báo pháp lý.
- [ ] [ND] Hồ sơ Lá Dẫn: tên hiển thị, ảnh, phong cách đọc, kinh nghiệm thật. Không dùng danh xưng gây hiểu là chuyên gia tâm lý/bác sĩ nếu không phải.
- [ ] [ND] Nội dung email/thông báo: xác nhận đặt, nhắc trước 30 phút, đổi/hủy, hoàn tiền, cảm ơn và mời đánh giá. Thông báo không lộ nội dung câu hỏi trên màn hình khóa.

## Cổng 3 — App Store và Google Play

- [ ] [KT] **iOS:** Apple Guideline 3.1.3(d) cho phép thu tiền ngoài IAP với dịch vụ 1–1 thời gian thực giữa hai người. Chỉ dùng ngoại lệ này cho buổi đọc trực tiếp đúng nghĩa; mọi thứ mở khóa nội dung số (bản ghi, báo cáo đọc lại, gói đọc bất đồng bộ) phải dùng IAP (3.1.1).
- [ ] [KT] **Google Play:** chính sách thanh toán không có ngoại lệ rõ cho dịch vụ 1–1 từ xa. Mặc định dùng Play Billing cho bản Android, trừ khi xác minh được Việt Nam thuộc chương trình thanh toán thay thế và đăng ký chương trình đó.
- [ ] [Chủ] Tính phí store và phí cổng thanh toán vào giá trước khi chốt giá (tài liệu nội bộ).
- [ ] [KT] Chat/gọi giữa người dùng và Lá Dẫn là nội dung do người dùng tạo (Apple 1.2): có nút báo cáo, chặn, liên hệ hỗ trợ ngay trong buổi; có cách gỡ Lá Dẫn khỏi hệ thống.
- [ ] [Chủ] Ghi chú cho Apple review: điểm khác biệt so với app bói toán khác (Apple 4.3(b) coi nhóm này đã bão hòa), mô tả luồng thanh toán và tài khoản thử.

## Cổng 4 — Quyền riêng tư

Căn cứ: Luật BVDLCN 91/2025/QH15 và NĐ 356/2025/NĐ-CP (hiệu lực 01.01.2026). Đây là luồng dữ liệu mới: lần đầu dữ liệu sinh và câu hỏi riêng tư của người dùng được **một người bên ngoài** đọc trực tiếp.

### 4.1 Kiểm kê dữ liệu

| Dữ liệu | Ai thấy | Mục đích | Lưu bao lâu |
|---|---|---|---|
| Tên hiển thị, ảnh đại diện | Lá Dẫn của buổi đó | Nhận biết khách | Theo tài khoản |
| Ngày, giờ, nơi sinh; chart đã tính | Lá Dẫn của buổi đó, chỉ từ lúc mở buổi đến khi kết thúc | Đọc bài | Không lưu phía Lá Dẫn |
| Câu hỏi/chủ đề người dùng nhập trước buổi | Lá Dẫn của buổi đó | Chuẩn bị đọc | Chốt thời hạn ngắn, rồi xóa |
| Nội dung chat trong buổi | Người dùng, Lá Dẫn, [VH] khi có báo cáo | Thực hiện buổi, xử lý khiếu nại | Chốt thời hạn ngắn, rồi xóa |
| Ghi âm/ghi hình | Mặc định **không ghi** | — | — |
| Booking, số tiền, mã giao dịch, trạng thái | Người dùng, [VH], kế toán | Thanh toán, hóa đơn, đối soát | Theo nghĩa vụ kế toán/thuế |
| Đánh giá 1–5 sao, nhận xét | Người dùng, Lá Dẫn (ẩn danh hóa), [VH] | Chất lượng | Chốt thời hạn |
| Định danh và tài khoản nhận tiền của Lá Dẫn | [VH], kế toán | Hợp đồng, trả thù lao, thuế | Theo nghĩa vụ kế toán/thuế |
| Mood, Lá Khai Sinh, lịch sử tarot tự bốc | **Không** chia sẻ với Lá Dẫn trừ khi người dùng chọn chia sẻ từng mục | — | — |

- [ ] [KT] Thêm các dòng trên vào [store-privacy-data-map.md](../legal/store-privacy-data-map.md) trước khi bật.

### 4.2 Việc phải làm

- [ ] [KT] Xin đồng ý riêng, ngay tại bước đặt buổi: "chia sẻ ngày/giờ/nơi sinh và câu hỏi của bạn với [tên Lá Dẫn] cho buổi này". Không gộp vào điều khoản chung; không tích sẵn.
- [ ] [KT] Lá Dẫn chỉ xem dữ liệu qua giao diện của Lá Lành, trong khung giờ của buổi; không có chức năng tải xuống/xuất; mọi lần mở hồ sơ được ghi nhật ký truy cập (không ghi nội dung).
- [ ] [Chủ] Hợp đồng cộng tác có điều khoản xử lý dữ liệu: chỉ dùng cho buổi đọc, không sao chép, không lưu, không liên hệ ngoài, bảo mật sau khi chấm dứt, báo ngay khi lộ dữ liệu.
- [ ] [KT] **Composite Chart (thiếu sót trong PRD F5.2):** PRD cho người dùng nhập ngày/giờ/nơi sinh của người khác. Không làm như vậy. Khi mở lại loại đọc này, chỉ cho chọn từ một Lá Ghép mà người kia đã chấp nhận và đã đồng ý cho dùng trong buổi đọc với Lá Dẫn.
- [ ] [KT] Người dùng xóa tài khoản → xóa câu hỏi, chat, đánh giá; giữ lại tối thiểu dữ liệu giao dịch theo nghĩa vụ kế toán, tách khỏi danh tính khi được phép. Cập nhật [backup-restore-and-deletion-reconciliation.md](../operations/backup-restore-and-deletion-reconciliation.md).
- [ ] [KT] Không ghi ngày sinh, câu hỏi, nội dung chat, mã giao dịch đầy đủ vào log hay công cụ theo dõi lỗi.
- [ ] [Chủ] Cập nhật hồ sơ đánh giá tác động xử lý dữ liệu (DPIA) cho luồng mới. Nếu máy chủ, cổng thanh toán, dịch vụ gọi video hoặc Lá Dẫn ở ngoài Việt Nam thì cập nhật cả hồ sơ chuyển dữ liệu ra nước ngoài (đang mở ở P10). Không ghi là "đã tuân thủ" khi các hồ sơ này chưa xong.
- [ ] [KT] Nếu dùng dịch vụ gọi video/chat bên thứ ba: ghi tên nhà cung cấp, nơi đặt máy chủ, việc họ có ghi lại hay không; ưu tiên loại không lưu nội dung.
- [ ] [ND] Cập nhật chính sách quyền riêng tư, chữ quyền riêng tư trong app, Apple App Privacy (thêm Purchases, User Content, dữ liệu chia sẻ với bên thứ ba) và Google Play Data Safety — bốn chỗ phải khớp nhau và khớp hành vi chạy thật.

## Cổng 5 — Bảo mật

- [ ] [KT] Vai trò Lá Dẫn tách khỏi người dùng thường: chỉ xem booking của chính mình; không duyệt danh sách người dùng; không thấy email/số điện thoại của khách.
- [ ] [KT] Kiểm tra quyền ở máy chủ cho mọi API booking, lịch trống, hồ sơ khách, chat (không tin ID từ phía app).
- [ ] [KT] Webhook cổng thanh toán: xác thực chữ ký, chống gửi lặp (idempotency), đối chiếu số tiền với booking; trạng thái chỉ đổi theo webhook đã xác thực.
- [ ] [KT] Giới hạn tần suất đặt/hủy và tạo giao dịch; chặn giữ chỗ ảo.
- [ ] [KT] Lá Dẫn đăng nhập với xác thực hai bước; thu hồi quyền ngay khi chấm dứt hợp đồng.
- [ ] [KT] Link vào buổi gọi là link có quyền truy cập: chỉ hai người trong buổi mở được, hết hạn sau buổi, không lưu cache, không để lộ qua referrer hay log.
- [ ] [KT] Trên app di động: rà theo OWASP MASVS (quyền micro/camera chỉ xin khi vào buổi, không lưu nội dung chat vào bộ nhớ máy không mã hóa).

## Cổng 6 — Bảo vệ người tiêu dùng

Căn cứ: Luật Bảo vệ quyền lợi người tiêu dùng 2023.

- [ ] [Chủ] Điều khoản dịch vụ cho buổi đọc: mô tả dịch vụ, giá đã gồm thuế, thời lượng, quyền và trách nhiệm hai bên, cách khiếu nại.
- [ ] [Chủ] Quy tắc hủy/đổi/hoàn tiền (PRD có trạng thái `cancelled`, `no_show` nhưng chưa có quy tắc):
  - người dùng hủy trước một mốc giờ → hoàn toàn bộ; sau mốc → chốt mức;
  - Lá Dẫn vắng mặt hoặc trễ quá ngưỡng → hoàn toàn bộ và ưu tiên đặt lại;
  - người dùng vắng mặt → chốt mức;
  - lỗi kỹ thuật phía Lá Lành → hoàn toàn bộ;
  - người dùng báo vi phạm bộ quy tắc → hoàn tiền trong lúc xem xét.
- [ ] [VH] Kênh khiếu nại trong app, thời hạn phản hồi đã cam kết, ghi lại kết quả xử lý.
- [ ] [KT] Kiểm tra tuổi trước khi thanh toán; không hiển thị lời mời mua với người dưới 18 tuổi.
- [ ] [ND] Không dùng đếm ngược, "chỉ còn 1 chỗ", hay thông báo thúc mua. Đúng nguyên tắc "Paid mua chiều sâu, không mua quyền tiếp cận".

## Cổng 7 — Tuyển và vận hành Lá Dẫn

- [ ] [VH] Tiêu chí tuyển: kinh nghiệm, buổi đọc thử với người của Lá Lành, đánh giá theo bộ quy tắc ở Cổng 2.
- [ ] [VH] Xác minh danh tính và mã số thuế cá nhân trước khi ký hợp đồng.
- [ ] [VH] Đào tạo: giọng Lá Lành, bộ quy tắc, cách dùng dashboard, quy trình khủng hoảng, quy tắc dữ liệu.
- [ ] [VH] **Quy trình khi người dùng đang khủng hoảng tinh thần** (nói về tự hại, bạo lực, bị lạm dụng): Lá Dẫn dừng phần đọc bài, nói chuyện nhẹ nhàng, đưa thông tin đường dây hỗ trợ đã được Lá Lành xác minh, báo [VH] ngay sau buổi; buổi đó được hoàn tiền. [ND] viết sẵn lời gợi ý cho Lá Dẫn.
- [ ] [VH] Bảo vệ Lá Dẫn: Lá Dẫn được kết thúc buổi khi bị quấy rối, báo cáo và chặn người dùng; không bị trừ thù lao trong trường hợp đó.
- [ ] [VH] Kiểm tra chất lượng: theo dõi đánh giá, khiếu nại, tỉ lệ vắng mặt; ngưỡng cảnh báo và ngưỡng ngừng hợp tác.
- [ ] [VH] Lịch trực hỗ trợ trong các khung giờ có buổi đọc.

## Cổng 8 — Chạy thử và điều kiện dừng

- [ ] [Chủ] Chạy thử kín với nhóm nhỏ người dùng được mời, số Lá Dẫn ít, trong thời gian giới hạn.
- [ ] [Chủ] Chỉ số theo dõi: tỉ lệ hoàn tất buổi, đánh giá trung bình, khiếu nại/hoàn tiền, báo cáo vi phạm, người dùng quay lại dùng phần miễn phí sau buổi (thước đo "được hiểu" theo north star).
- [ ] [Chủ] Điều kiện dừng ngay: có lộ dữ liệu; Lá Dẫn vi phạm nghiêm trọng bộ quy tắc; khiếu nại hoặc hoàn tiền vượt ngưỡng đã chốt; phản hồi cho thấy người dùng thấy bị ép mua.
- [ ] [Chủ] Sau chạy thử: viết báo cáo ngắn, quyết định mở rộng, chỉnh hoặc dừng.

## Đối chiếu PRD F5.2

| Tiêu chí trong PRD | Trạng thái trong checklist |
|---|---|
| Lá Dẫn tự đặt lịch trống | Giữ; quyền giới hạn ở Cổng 5 |
| Thanh toán trước khi xác nhận | Giữ; cách thanh toán theo nền tảng ở Cổng 1 và 3 |
| Nhắc lịch trước 30 phút cho cả hai bên | Giữ; nội dung thông báo ở Cổng 2 |
| Đánh giá 1–5 sao + nhận xét | Giữ; thời hạn lưu ở Cổng 4 |
| Composite Chart với dữ liệu người kia | **Đổi**: tạm khóa, chỉ mở lại qua Lá Ghép đã đồng ý |
| `cancelled` / `no_show` | **Thiếu quy tắc** trong PRD → bổ sung ở Cổng 6 |
| Đồng ý chia sẻ dữ liệu với Lá Dẫn | **Thiếu** trong PRD → bổ sung ở Cổng 4 |
| Tuyển, xác minh, đào tạo Lá Dẫn | **Thiếu** trong PRD → bổ sung ở Cổng 7 |
| Độ tuổi người mua | **Thiếu** trong PRD → bổ sung ở Cổng 0 và 6 |

Khi bắt đầu làm tính năng, cập nhật PRD F5.2 và SRS theo bảng này trước khi viết code.

## Nguồn đã xem (31.10.2026)

- Apple App Review Guidelines, mục 1.2, 3.1.1, 3.1.3(d), 4.3(b): https://developer.apple.com/app-store/review/guidelines/
- Google Play Payments policy: https://support.google.com/googleplay/android-developer/answer/9858738
- Luật Thương mại điện tử 2025 (Luật 122/2025/QH15, hiệu lực 01.07.2026) — tóm tắt báo chí, cần đọc văn bản gốc: https://vneconomy.vn/luat-thuong-mai-dien-tu-2025-cam-cuong-va-minh-bach-hoa-thi-truong.htm
- NĐ 117/2025/NĐ-CP, sàn khấu trừ thuế thay (lý do không chọn mô hình sàn): https://lsvn.vn/san-thuong-mai-dien-tu-phai-khau-tru-va-nop-thue-thay-cho-ho-ca-nhan-kinh-doanh-a170137.html
- NĐ 38/2021/NĐ-CP Điều 14 và BLHS Điều 320 — qua trang tư vấn, mức phạt giữa các nguồn chưa khớp: https://luatvietnam.vn/linh-vuc-khac/to-chuc-xem-boi-co-vi-pham-phap-luat-khong-883-90440-article.html
- Luật BVDLCN 91/2025/QH15 và NĐ 356/2025/NĐ-CP: https://www.ey.com/vi_vn/technical/tax/tax-and-law-updates/nghi-dinh-so-356-2025-nd-cp-quy-dinh-chi-tiet-mot-so-dieu-va-bien-phap-thi-hanh-luat-bao-ve-du-lieu-ca-nhan
- Ngưỡng khấu trừ TNCN thu nhập vãng lai (chưa xác nhận được ngưỡng hiện hành): https://thuvienphapluat.vn/lao-dong-tien-luong/chu-de/khau-tru-thue-thu-nhap-ca-nhan

Các mục pháp lý trên đã đọc qua bài tóm tắt, chưa đọc toàn văn. Đối chiếu văn bản gốc trên Công báo trước khi chốt từng cổng.
