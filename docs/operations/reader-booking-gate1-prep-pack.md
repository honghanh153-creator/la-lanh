# Bộ hồ sơ chuẩn bị Cổng 1 — pháp nhân, thuế, thanh toán

Ngày soạn: 31.10.2026
Dùng cho: Cổng 1 trong [checklist triển khai mô hình A](../plans/2026-10-31-reader-booking-model-a-launch-checklist.md).

Tài liệu này để chủ sản phẩm làm các thủ tục online theo đúng thứ tự, có sẵn nội dung để chép vào. Các bước đăng nhập VNeID, nhập CCCD, mã số thuế, số tài khoản ngân hàng, tạo tài khoản, ký và bấm nộp **do chủ sản phẩm tự làm**. Agent không thực hiện các bước này.

Repo này công khai: **không** ghi họ tên, số CCCD, địa chỉ, số tài khoản, giá bán, tỉ lệ thù lao hay ngân sách vào đây. Điền các ô `[...]` ở tài liệu nội bộ.

Mức độ chắc chắn: phần lớn căn cứ đọc qua bài tóm tắt của công ty luật, kế toán, kiểm toán; chưa đọc được nguyên văn trên Công báo. Mục ghi **[chưa xác minh]** phải kiểm tra lại trên cổng chính thức khi làm.

## 1. Thứ tự làm

Mỗi bước cần kết quả của bước trước.

| # | Việc | Làm ở đâu | Cần có trước | Thời gian (theo nguồn) |
|---|---|---|---|---|
| 1 | Đăng ký công ty TNHH một thành viên | dangkykinhdoanh.gov.vn hoặc app VNeID | VNeID mức 2, nội dung ở mục 2 | 3 ngày làm việc **[chưa xác minh]** |
| 2 | Mở tài khoản ngân hàng đứng tên công ty | Ngân hàng | Giấy chứng nhận đăng ký doanh nghiệp | Tùy ngân hàng |
| 3 | Đăng ký hóa đơn điện tử và chứng từ khấu trừ điện tử | Qua nhà cung cấp hóa đơn (mục 4) | Mã số thuế công ty | Khoảng 1 ngày làm việc |
| 4 | Xin mã D-U-N-S | Theo hướng dẫn của Apple/Google | Thông tin công ty | Có thể tới 30 ngày |
| 5 | Đưa lên app/web các trang bắt buộc | Kỹ thuật | Thông tin công ty, nội dung ở [bản nháp trang công khai](../legal/reader-booking-public-pages-draft.md) | — |
| 6 | Thông báo nền tảng TMĐT kinh doanh trực tiếp | Cổng dịch vụ công / online.gov.vn → Sở Công Thương | Bước 1 và 5 xong | 3 ngày làm việc |
| 7 | Đăng ký cổng thanh toán | Mục 5 | Bước 1, 2, 6 (ZaloPay đòi chứng từ đã thông báo) | payOS vài phút; ZaloPay 5–7 ngày làm việc |
| 8 | Chuyển app sang tài khoản tổ chức trên Apple/Google (nếu đang là tài khoản cá nhân) | Apple Developer, Google Play Console | Bước 4 | **[chưa xác minh]** quy trình chuyển |
| 9 | Ký hợp đồng cộng tác với Lá Dẫn đầu tiên | Giấy hoặc hợp đồng điện tử | Bước 1, mẫu ở [khung hợp đồng](../legal/reader-contractor-agreement-outline.md) | — |

Bước 3 và 4 làm song song với bước 5.

## 2. Đăng ký công ty

### 2.1 Vì sao chọn công ty TNHH một thành viên, không chọn hộ kinh doanh

- Apple chỉ cho mở tài khoản tổ chức với pháp nhân có D-U-N-S. Hộ kinh doanh không có tư cách pháp nhân nên chỉ dùng được tài khoản cá nhân, khi đó App Store hiện họ tên chủ hộ. Apple Guideline 5.1.1(ix) cũng yêu cầu app thu dữ liệu nhạy cảm (Lá Lành thu ngày, giờ, nơi sinh) do pháp nhân nộp.
- Google Play tài khoản tổ chức cũng cần D-U-N-S.
- Cổng thanh toán (VNPAY, ZaloPay, MoMo) nhận hồ sơ công ty dễ hơn; ZaloPay đòi chứng từ thông báo TMĐT.
- Chủ hộ kinh doanh chịu trách nhiệm vô hạn bằng tài sản cá nhân; công ty TNHH chịu trách nhiệm trong vốn điều lệ.

### 2.2 Nộp online

- Đăng nhập dangkykinhdoanh.gov.vn bằng VNeID mức 2 (hoặc nộp trong app VNeID).
- Người nộp tự đứng tên và tự ký thì không cần chữ ký số (Công văn 234/BTC-DNTN ngày 08.01.2026, theo bài của LuatVietnam).
- Nộp online được miễn lệ phí đăng ký; phí công bố thông tin khoảng 100.000 đồng **[chưa xác minh mức hiện hành]**.

### 2.3 Hồ sơ

- Giấy đề nghị đăng ký doanh nghiệp (Mẫu I-2, Thông tư 68/2025/TT-BTC).
- Điều lệ công ty.
- Kê khai chủ sở hữu hưởng lợi (theo NĐ 296/2026/NĐ-CP).
- Không cần bản sao CCCD nếu đã khai số định danh.

### 2.4 Nội dung chuẩn bị sẵn

| Ô | Gợi ý |
|---|---|
| Tên công ty | `[Tên tiếng Việt]`, kiểm tra trùng trên cổng trước khi nộp |
| Tên viết tắt / tiếng Anh | `[...]` |
| Trụ sở | `[Địa chỉ]`; sẽ hiện công khai trên app (trang thông tin bên bán) |
| Vốn điều lệ | `[...]`; ghi ở tài liệu nội bộ |
| Người đại diện theo pháp luật | Chủ sở hữu |
| Ngành nghề | Xem 2.5 |

### 2.5 Ngành nghề (Hệ thống ngành kinh tế theo QĐ 36/2025/QĐ-TTg, hiệu lực 15.11.2025)

| Mã | Tên | Dùng cho |
|---|---|---|
| 58292 | Xuất bản phần mềm ứng dụng | App Lá Lành |
| 62190 | Lập trình máy tính khác | Phát triển phần mềm |
| 9690 (mã cấp 5 phù hợp) | Hoạt động dịch vụ phục vụ cá nhân khác | Buổi đọc 1–1 |

- Mã cấp 5 cụ thể trong nhóm 9690 **[chưa xác minh]**: mở danh mục trên dangkykinhdoanh.gov.vn khi nộp và chọn mã "chưa được phân vào đâu".
- Ghi chi tiết ngành theo hướng: *"Dịch vụ trò chuyện, chiêm nghiệm cá nhân qua tarot và chiêm tinh, mang tính tham khảo, giải trí."*
- **Không** dùng các chữ "bói toán", "giải hạn", "cúng", "xem vận mệnh".
- **Không** chọn mã nhóm 63 (cổng thông tin, xử lý dữ liệu) vì dễ kéo theo giấy phép trang thông tin tổng hợp.
- Nếu Phòng Đăng ký kinh doanh yêu cầu sửa cách ghi ngành, sửa theo hướng dẫn của họ.

## 3. Thông báo nền tảng thương mại điện tử

- **Căn cứ:** Luật Thương mại điện tử 2025 (Luật 122/2025/QH15) và NĐ 248/2026/NĐ-CP, cùng hiệu lực 01.07.2026, thay NĐ 52/2013 và NĐ 85/2021.
- **Loại:** "nền tảng thương mại điện tử kinh doanh trực tiếp" (Lá Lành tự bán dịch vụ của mình), làm thủ tục **thông báo**, không phải đăng ký sàn.
- **Phạm vi:** khai cả tên miền website và tên ứng dụng trên App Store/Google Play.
- **Nơi nộp:** Sở Công Thương cấp tỉnh nơi đặt trụ sở, qua Cổng dịch vụ công quốc gia / online.gov.vn (NĐ 248 Điều 23, 24, 45).
- **Hồ sơ:** Tờ khai Mẫu 01, Phụ lục II NĐ 248.
- **Thời hạn:** trả lời trong 3 ngày làm việc. Nếu bị yêu cầu bổ sung mà 60 ngày không phản hồi thì hồ sơ tự chấm dứt. Có thay đổi thông tin thì sửa thông báo trong 20 ngày làm việc.
- **Kết quả:** biểu tượng xác nhận, gắn ở chân trang web và trang thông tin bên bán trong app.

Trước khi nộp, app/web phải có sẵn các thông tin bắt buộc (Luật Điều 11; NĐ 248 Điều 4–10, 14, 15, 17), đặt ở vị trí dễ thấy. Nội dung nháp ở [reader-booking-public-pages-draft.md](../legal/reader-booking-public-pages-draft.md).

## 4. Hóa đơn và thuế

### 4.1 Hóa đơn điện tử

- **Căn cứ:** NĐ 254/2026/NĐ-CP và Thông tư 91/2026/TT-BTC (hiệu lực 01.07.2026), thay NĐ 123/2020, NĐ 70/2025, TT 32/2025.
- **Đăng ký:** Mẫu 01/ĐKTĐ-HĐĐT, nộp qua nhà cung cấp; cơ quan thuế phản hồi khoảng 1 ngày làm việc. Không còn thủ tục thông báo phát hành.
- **Thời điểm lập:** ngay khi thu tiền, tức lúc cổng thanh toán báo thành công, không chờ buổi đọc (NĐ 254 Điều 9 khoản 2).
- **Hủy, hoàn tiền:** lập hóa đơn điều chỉnh hoặc thay thế **[chưa xác minh thủ tục theo NĐ 254]**.
- **Dữ liệu khách trên hóa đơn:** khách là cá nhân thì chỉ ghi tên, mã số thuế hoặc CCCD khi khách yêu cầu. Mặc định ghi tối thiểu; không bao giờ ghi nội dung buổi đọc.
- **Tự động hóa:** app gửi dữ liệu từng giao dịch qua API của nhà cung cấp, nhà cung cấp ký số và truyền cho cơ quan thuế.

| Nhà cung cấp | API công khai | Giá công bố |
|---|---|---|
| MISA meInvoice | Có (REST/JSON) | Có bảng giá theo gói số hóa đơn, có phí khởi tạo (bảng giá ghi từ 2020, cần hỏi lại) |
| VNPT Invoice | Chưa thấy tài liệu công khai | Chỉ có giá qua bên thứ ba |
| Viettel S-Invoice | Chưa thấy tài liệu công khai | Không công bố |
| BKAV eHoaDon | Chưa thấy tài liệu công khai | Không công bố |

Đề xuất: MISA meInvoice cho bản thử, vì là bên duy nhất có tài liệu API công khai. Hỏi họ hai điều: có đăng ký chứng từ khấu trừ TNCN điện tử (Mẫu 01/ĐKTĐ-CTĐT) cùng lúc được không, và giá hiện hành.

### 4.2 Thuế GTGT

- Dịch vụ đọc bài không thuộc nhóm không chịu thuế hay thuế suất 5%, nên áp dụng 10%.
- Từ 01.07.2025 đến 31.12.2026 được giảm còn 8% (NĐ 174/2025/NĐ-CP), trừ các nhóm trong phụ lục loại trừ. **[chưa xác minh]** dịch vụ đọc bài trực tuyến có bị xếp vào nhóm công nghệ thông tin bị loại trừ không.
- Công ty có doanh thu dưới 1 tỷ đồng/năm dùng phương pháp trực tiếp (tỷ lệ 5% trên doanh thu dịch vụ), trừ khi tự chọn phương pháp khấu trừ (Luật Thuế GTGT 2024 Điều 12).
- Giá hiển thị cho người dùng phải ghi rõ đã gồm thuế.

### 4.3 Thuế TNDN

- **[chưa xác minh]** NĐ 141/2026/NĐ-CP được nói là miễn TNDN cho doanh nghiệp có doanh thu đến 1 tỷ đồng/năm. Kiểm tra trước kỳ quyết toán đầu tiên.

### 4.4 Thuế TNCN khi trả thù lao Lá Dẫn

- **Căn cứ:** Luật Thuế TNCN 109/2025/QH15, NĐ 253/2026/NĐ-CP, Thông tư 87/2026/TT-BTC (hiệu lực 01.07.2026).
- **Mức khấu trừ:** 10% nếu mỗi lần chi từ **5.000.000 đồng** trở lên (NĐ 253 Điều 50 khoản 2). Dưới mức này chỉ khấu trừ khi Lá Dẫn yêu cầu. Không chia nhỏ khoản chi để né ngưỡng.
- **Cam kết không khấu trừ:** Lá Dẫn chỉ có một nguồn thu nhập thuộc diện khấu trừ và thu nhập ước tính chưa tới mức chịu thuế thì nộp Mẫu 08/CK-TNCN (nay thuộc Thông tư 89/2026/TT-BTC). Lá Lành vẫn khai danh sách khi quyết toán năm.
- **Chứng từ khấu trừ điện tử** (NĐ 254 Điều 17, 24, 29):
  - đăng ký trước bằng Mẫu 01/ĐKTĐ-CTĐT;
  - lập mỗi lần khấu trừ, hoặc gộp cả năm nếu Lá Dẫn yêu cầu;
  - gửi cơ quan thuế ngay trong ngày lập.
- **Lá Dẫn là hộ kinh doanh đã đăng ký:** họ tự xuất hóa đơn cho Lá Lành, Lá Lành không khấu trừ.
- **Bảo hiểm xã hội:** hợp đồng dịch vụ đúng bản chất không phải đóng BHXH bắt buộc (Luật BHXH 2024 Điều 2). Nếu bị coi là hợp đồng lao động thì phải truy đóng; cách tránh ở [khung hợp đồng](../legal/reader-contractor-agreement-outline.md).

## 5. Cổng thanh toán

| | payOS | VNPAY | ZaloPay |
|---|---|---|---|
| Đăng ký | Online, tự động, vài phút; xác thực bằng một lần chuyển khoản từ tài khoản cùng tên | Liên hệ kinh doanh, ký hợp đồng | Online tại mc.zalopay.vn; 5–7 ngày làm việc |
| Hồ sơ | Mã số thuế công ty, tài khoản ngân hàng cùng tên | Giấy đăng ký, CCCD người đại diện, tài khoản thụ hưởng | Giấy đăng ký, CCCD, chứng từ sở hữu web/app, **chứng từ đã thông báo TMĐT** |
| Phí công bố | Miễn phí giao dịch, cài đặt, duy trì | Tham khảo: nội địa 1,1% + 1.650đ; VNPAY-QR 0,88%; thực tế theo hợp đồng | Theo thỏa thuận |
| Phương thức | Chuyển khoản / VietQR / Napas 247; **không nhận thẻ** | QR, thẻ nội địa, thẻ quốc tế | Ví, QR, thẻ |
| Chữ ký webhook | HMAC-SHA256 | HMAC-SHA512 (IPN gửi lại tối đa 10 lần) | HMAC-SHA256, chỉ HTTPS |
| API hoàn tiền | **Không có**, phải hoàn thủ công hoặc qua API chi hộ | Có, toàn phần và một phần | Có |
| Sandbox | **Không có**, test trên production với số tiền nhỏ | Có | Có |

MoMo không công bố biểu phí; quy chế TMĐT của MoMo (cho người bán trên app MoMo) cấm "mê tín dị đoan", nên không chọn MoMo làm cổng chính.

**Đề xuất cho bản thử:** dùng payOS cho web, đồng thời nộp hồ sơ VNPAY làm cổng thứ hai (có thẻ, có hoàn tiền qua API, có sandbox).

Vì payOS thiếu hai thứ, phải bù như sau:
- **Không có API hoàn tiền:** quy trình hoàn tiền thủ công có sổ ghi (người duyệt, thời điểm, mã đơn), thời hạn hoàn ghi rõ trong chính sách hoàn tiền.
- **Không có sandbox:** test trên production bằng đơn có số tiền nhỏ, đánh dấu đơn test, có quy trình hoàn lại.

**Rủi ro ngành nghề:** không cổng nào công khai danh sách cấm tarot, nhưng bộ phận thẩm định có thể từ chối hoặc khóa merchant. Trước khi tích hợp sâu, chủ sản phẩm gửi email hỏi từng cổng, mô tả dịch vụ là "buổi trò chuyện chiêm nghiệm 1–1 trực tuyến qua tarot và chiêm tinh, mang tính tham khảo, giải trí", và lưu câu trả lời. Đầu mối hỗ trợ lấy trên trang chính thức của từng cổng.

**Yêu cầu kỹ thuật chung** (chi tiết ở Cổng 5 của checklist):
- Kiểm tra chữ ký webhook bằng so sánh constant-time.
- Xử lý webhook idempotent theo mã đơn.
- Đối chiếu số tiền với booking.
- Không ghi log secret, payload thô hay dữ liệu định danh.
- Mô tả đơn và nội dung chuyển khoản chỉ chứa mã đơn: nội dung này hiện trên sao kê ngân hàng.

## 6. Việc chủ sản phẩm tự làm và việc agent làm

| Chủ sản phẩm tự làm | Agent làm |
|---|---|
| Đăng nhập VNeID, nộp hồ sơ công ty, ký | Soạn nội dung các ô, điều lệ nháp, chọn ngành nghề |
| Mở tài khoản ngân hàng | — |
| Xin D-U-N-S, chuyển tài khoản Apple/Google | Hướng dẫn từng bước khi làm |
| Ký hợp đồng nhà cung cấp hóa đơn, nộp Mẫu 01/ĐKTĐ | So sánh nhà cung cấp, tích hợp API hóa đơn |
| Nộp thông báo TMĐT | Soạn và đưa lên các trang bắt buộc |
| Đăng ký cổng thanh toán, nhập tài khoản ngân hàng, gửi email hỏi ngành nghề | Soạn email hỏi, tích hợp thanh toán, webhook, hoàn tiền |
| Ký hợp đồng với Lá Dẫn, khai thuế | Khung hợp đồng, bảng tính thù lao và thuế, script đối soát |

## Nguồn

Pháp nhân, đăng ký, thông báo TMĐT:
- Apple Developer Program enrollment: https://developer.apple.com/programs/enroll/
- Apple App Review Guidelines (3.1.3(d), 5.1.1(ix)): https://developer.apple.com/app-store/review/guidelines/
- Google Play xác minh nhà phát triển, D-U-N-S: https://goo.gle/developer-verification
- NĐ 248/2026/NĐ-CP: https://hethongphapluat.com/nghi-dinh-248-2026-nd-cp-huong-dan-luat-thuong-mai-dien-tu.html ; https://tapchicongthuong.vn/bo-cong-thuong-pho-bien-luat-thuong-mai-dien-tu-va-nghi-dinh-so-248-2026-nd-cp-531199.htm
- Luật Thương mại điện tử 2025 Điều 11: https://hethongphapluat.com/luat-thuong-mai-dien-tu-2025/khoan-1-dieu-11
- NĐ 296/2026/NĐ-CP về đăng ký doanh nghiệp: https://kpmg.com/vn/vi/insights/2026/08/decree-296-on-enterprise-registration.html
- Không phải ký số khi đăng ký qua VNeID: https://luatvietnam.vn/tin-van-ban-moi/khong-phai-ky-so-bieu-mau-dien-tu-khi-dang-ky-doanh-nghiep-ho-kinh-doanh-qua-vneid-186-106439-article.html
- Mã ngành 5829, 6219: https://vnlawfirm.vn/ma-nganh-5829-xuat-ban-phan-mem-khac/ ; https://vnlawfirm.vn/ma-nganh-6219-lap-trinh-may-tinh-khac/
- NĐ 147/2024/NĐ-CP (mạng xã hội): https://assets.kpmg.com/content/dam/kpmg/vn/pdf/Legal-Update/2025/02/decree-147-on-internet-services-vi.pdf

Thuế, hóa đơn, hợp đồng:
- NĐ 254/2026 và TT 91/2026: https://www.ey.com/vi_vn/technical/tax/tax-and-law-updates/nghi-dinh-254-2026-nd-cp-ve-hoa-don-dien-tu-va-chung-tu-dien-tu
- Thời điểm lập hóa đơn theo NĐ 254: https://amis.misa.vn/39192/thoi-diem-xuat-hoa-don/
- NĐ 253/2026 và TT 87/2026: https://www.forvismazars.com/vn/vi/n-ph-m-s-ki-n/c-p-nh-t-v-vi-t-nam/b-n-tin-thong-bao-chuyen-mon/b-n-tin-v-thu-va-phap-ly/ngh-d-nh-253-va-thong-t-87-v-thu-tncn ; https://www.sapo.vn/blog/nghi-dinh-253-2026-nd-cp
- Trang văn bản NĐ 253 trên Cổng Chính phủ: https://vanban.chinhphu.vn/?pageid=27160&docid=218684
- Mẫu biểu TT 89/2026: https://amis.misa.vn/282421/tai-to-khai-thue-tncn-thue-gtgt-theo-thong-tu-89/
- Giảm GTGT NĐ 174/2025: https://hoatieu.vn/phap-luat/nghi-dinh-174-2025-nd-cp-234321
- Luật Thuế GTGT 2024 Điều 12: https://hethongphapluat.com/luat-thue-gia-tri-gia-tang-2024/dieu-12
- Bảng giá MISA meInvoice: https://www.meinvoice.vn/bao-gia/
- Luật BHXH 2024 Điều 2: https://hethongphapluat.com/luat-bao-hiem-xa-hoi-2024/dieu-2

Cổng thanh toán:
- payOS: https://payos.vn/ ; webhook https://payos.vn/docs/tich-hop-webhook/kiem-tra-du-lieu-voi-signature/ ; API https://payos.vn/docs/api/ ; môi trường test https://payos.vn/docs/moi-truong-test
- VNPAY: https://vnpay.vn/dang-ky-vnpay-qr-cho-cua-hang-00izi3uzy80zq ; https://sandbox.vnpayment.vn/apis/docs/thanh-toan-pay/pay.html ; hoàn tiền https://sandbox.vnpayment.vn/apis/docs/truy-van-hoan-tien/querydr&refund.html
- ZaloPay: https://mc.zalopay.vn/ ; https://docs.zalopay.vn/vi/docs/specs/order-refund
- Quy chế TMĐT MoMo: https://www.momo.vn/quy-che-hoat-dong-ung-dung-tmdt
