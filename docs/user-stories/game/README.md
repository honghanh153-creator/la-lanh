# Dòng game — danh sách user story (G-story)

> Trạng thái: **bản nháp, chờ owner duyệt.** Giai đoạn 3 (game) chưa bắt đầu, chưa có code. Mã G-story là **mã nháp**: chưa ghi vào
> bản đồ story chung [`docs/user-stories/README.md`](../README.md). Owner quyết có đưa vào bản đồ đó không, và đưa lúc nào.
>
> Mục lục dòng game, nguyên tắc chung và quyết định chờ owner: [`docs/foundation/game-line/README.md`](../../foundation/game-line/README.md).

## Quy tắc sở hữu

- **Một hành vi thuộc đúng một story.** Story khác chỉ tham chiếu, không chép lại AC. Giống quy tắc của bản đồ story chung.
- **Hành vi phòng trực tiếp dùng chung nằm ở G01–G09** (tạo phòng, vào phòng, đồng ý, 5 câu vô hại, chia vai, phiếu, nút host,
  tiêu huỷ hồ sơ, báo cáo, rời phòng, chỉ xem, vào lại). Story của Phiên Tòa, Sĩ Số +1 và Tam Sao bản trực tiếp chỉ viết phần riêng
  của trò và trỏ về G01–G09.
- Hết Cứu % và Tam Sao bản nhóm chat không chạy trên phòng trực tiếp, nên tự có story cho nhóm, mời, rời và xoá.
- Tri Kỷ nằm trong Lá Lành, dùng lại đường ray Lá Chứng (US-08, US-09) và Radar (US-13). Story Tri Kỷ trỏ về các story đó, không viết
  lại hợp đồng link.
- Thông báo, loading, empty, error, hết hạn là trạng thái trong story sở hữu nghiệp vụ, không tách story riêng.

## Khung mã

| Khung | Trò | Đặc tả |
|---|---|---|
| G00–G09 | Hạ tầng phòng trực tiếp dùng chung (G00 chưa dùng) | [shared-room-platform-srs.md](../../foundation/game-line/shared-room-platform-srs.md) |
| G10–G19 | Hết Cứu % | [PRD](../../foundation/game-line/het-cuu-phan-tram-prd.md) · [SRS](../../foundation/game-line/het-cuu-phan-tram-srs.md) |
| G20–G29 | Tam Sao Thất Bản | [PRD](../../foundation/game-line/tam-sao-that-ban-prd.md) · [SRS](../../foundation/game-line/tam-sao-that-ban-srs.md) |
| G30–G39 | Phiên Tòa Tủ Lạnh (G30 chưa dùng) | [PRD](../../foundation/game-line/phien-toa-tu-lanh-prd.md) · [SRS](../../foundation/game-line/phien-toa-tu-lanh-srs.md) |
| G40–G49 | Sĩ Số +1 (G40 chưa dùng) | [PRD](../../foundation/game-line/si-so-cong-1-prd.md) · [SRS](../../foundation/game-line/si-so-cong-1-srs.md) |
| G50–G59 | Tri Kỷ và Hiểu Nhau Không? | [PRD](../../foundation/game-line/tri-ky-prd.md) · [SRS](../../foundation/game-line/tri-ky-srs.md) |

Mã còn trống trong mỗi khung để dành cho story sau. Không dùng lại mã đã bỏ.

## Danh sách

"MVP" nghĩa là thuộc bản đầu khi giai đoạn 3 mở, không có nghĩa là đã được duyệt để dựng.

### Hạ tầng phòng trực tiếp (Phiên Tòa, Sĩ Số +1, Tam Sao bản trực tiếp)

| ID | Story | Phạm vi | Hành vi sở hữu |
|---|---|---|---|
| [G01](G01-host-tao-phong-va-man-chieu.md) | Host tạo phòng và mở màn chiếu | MVP | Tạo phòng, mã 6 ký tự, QR, token, màn chiếu, sảnh chờ, bắt đầu |
| [G02](G02-vao-phong-bang-qr-biet-danh-dong-y.md) | Vào phòng bằng QR hoặc mã, đặt biệt danh và đồng ý | MVP | Vào phòng, biệt danh, ô 18+, ô hiện câu trả lời trên màn chung, chỉ xem lúc vào |
| [G03](G03-khai-bao-5-cau-vo-hai.md) | Khai báo 5 câu vô hại | MVP | Năm câu chọn sẵn, "Không muốn nói", sửa tới khi khoá |
| [G04](G04-chia-vai-bi-mat-va-chia-nhom.md) | Chia vai bí mật và chia nhóm | MVP | Chia vai, thẻ úp, chia nhóm, gói tin đồng dạng |
| [G05](G05-bo-phieu-dong-thoi.md) | Bỏ phiếu đồng thời | MVP | Phiếu, phiếu trắng, đổi ý, đóng phiếu, công bố số đếm, lượt chọn bí mật theo vai |
| [G06](G06-nut-host-kick-bo-qua-tam-dung-ket-thuc.md) | Nút host: khoá, thu hồi, kick, đổi tên, bỏ qua, tạm dừng, kết thúc | MVP | Mọi nút điều khiển của host |
| [G07](G07-tieu-huy-ho-so-va-het-han-phong.md) | Tiêu huỷ hồ sơ và hết hạn phòng | MVP | Xoá dữ liệu người chơi khi kết thúc, hết hạn cứng 2 giờ, màn tiêu huỷ |
| [G08](G08-bao-cao-roi-phong-chi-xem.md) | Báo cáo, rời phòng và chỉ xem | MVP | Báo cáo, rời phòng, chuyển sang chỉ xem, câu khảo sát cuối buổi |
| [G09](G09-mat-ket-noi-va-vao-lai.md) | Mất kết nối và vào lại | MVP | Thử lại, vào lại, trạng thái vắng |

### Hết Cứu %

| ID | Story | Phạm vi | Hành vi sở hữu |
|---|---|---|---|
| [G10](G10-tao-nhom-va-moi.md) | Tạo nhóm và mời bạn vào | MVP | Nhóm 4–12 người, link mời, thu hồi, gỡ thành viên, chuyển host |
| [G11](G11-tu-khai-phan-tram-va-dat-la.md) | Nhận sự kiện tuần, tự khai % và đặt lá | MVP (cơ chế lá chờ D3) | Thả đề thứ Hai, tự khai, thẻ lời khai, phiếu đoán, lá |
| [G12](G12-tin-nong-giua-tuan.md) | Tin nóng giữa tuần | **Sau MVP** | Dòng tin nóng thứ Tư, một lượt sửa số |
| [G13](G13-man-lat-thu-sau.md) | Màn lật tối thứ Sáu | MVP | Màn lật, danh hiệu, thẻ danh hiệu chia sẻ |
| [G14](G14-tong-ket-mua.md) | Mùa 8 tuần, tuần nghỉ và tổng kết mùa | MVP | Mùa, tuần nghỉ, tạm dừng nhóm, tổng kết mùa, vòng đời nhóm (HC-D4) |
| [G15](G15-quyen-rieng-tu-cua-toi.md) | Lựa chọn riêng tư của tôi | MVP | Ẩn %, đừng đoán tôi, thông báo, rời nhóm, xoá dữ liệu, xem dữ liệu, báo cáo |
| [G16](G16-nhan-vat-chinh-tu-nguyen.md) | Nhân Vật Chính tự nguyện và màn ba nhịp | MVP (chờ D8) | Nhận ghế, rút lui, màn ba nhịp, giữ khoảnh khắc |

### Tam Sao Thất Bản

| ID | Story | Phạm vi | Hành vi sở hữu |
|---|---|---|---|
| [G20](G20-phong-truc-tiep-chuoi-song-song.md) | Chơi một ván phòng trực tiếp với chuỗi song song | MVP | Chia bàn, xoay vòng năm bước, Bot Sao Thủy khi thiếu người |
| [G21](G21-nhom-chat-nhan-luot.md) | Ván nhóm chat không đồng bộ với "nhận lượt" | **Chỉ khi D4 đạt** (chờ owner) | Tạo ván chat, nhận lượt, hạn chót, câu nhắc host tự gửi |
| [G22](G22-man-lat-va-phat-lai.md) | Màn lật, phát lại, bỏ phiếu và thẻ lật | MVP | Độ thất bản, phát lại, hai ô hiện biệt danh, phiếu, thẻ lật |
| [G23](G23-ngan-hang-de-va-phuong-an-gan-dung.md) | Ngân hàng đề và phương án gần đúng | MVP | Ngân hàng, ghép phương án, kiểm tra trước phát hành |
| [G24](G24-quyen-host-va-nguoi-choi.md) | Quyền của host và người chơi | MVP | Nút riêng của Tam Sao; toàn bộ nút của bản chat |
| [G25](G25-xoa-du-lieu-va-tieu-huy-ho-so.md) | Xoá dữ liệu và tiêu huỷ hồ sơ | MVP | Xoá bản chat sau 48 giờ, host xoá ngay, rời ván |

### Phiên Tòa Tủ Lạnh

| ID | Story | Phạm vi | Hành vi sở hữu |
|---|---|---|---|
| [G31](G31-mo-phien-toa-chon-che-do-va-goi-vu.md) | Mở Phiên Tòa: chọn chế độ, gói vụ và đổi vụ an toàn | MVP | Chế độ, chọn vụ, "Tránh chủ đề lấy đồ", đổi sang vụ con vịt |
| [G32](G32-nhan-doi-va-vai-phien-toa.md) | Nhận đội hành tinh và vai Phiên Tòa | MVP | Đội, vai cả buổi, vai theo vụ, điều kiện nhận vai |
| [G33](G33-dieu-tra-mot-vu.md) | Điều tra một vụ | MVP | Cáo trạng, câu hỏi phụ, manh mối, buộc tội |
| [G34](G34-ra-toa-phan-doi-va-bo-phieu.md) | Ra tòa: ghế bị cáo, Luật Sư, "Phản đối!" và bỏ phiếu | MVP | Ghế bị cáo, Luật Sư, Phản đối, phiếu kết án |
| [G35](G35-tuyen-an-mien-an-su-that-la.md) | Tuyên án, Miễn án và "Sự thật là…" | MVP | Bản án tượng trưng, Miễn án, lật manh mối, điểm đội |
| [G36](G36-dai-an-ke-chu-muu-va-tieu-huy.md) | Đại Án: tìm Kẻ Chủ Mưu, trao danh hiệu, tiêu huỷ hồ sơ | MVP | Đại Án, danh hiệu, chuyển sang tiêu huỷ |
| [G37](G37-tham-phan-la-mau-cau.md) | Thẩm Phán Lá chạy bằng mẫu câu | MVP (chờ D7) | Kho mẫu câu, điền slot, không AI |

### Sĩ Số +1

| ID | Story | Phạm vi | Hành vi sở hữu |
|---|---|---|---|
| [G41](G41-mo-man-diem-danh-n-cong-1.md) | Mở màn: chọn chế độ, cảnh báo nội dung và điểm danh ra N+1 | MVP (chờ D6) | Bối cảnh, chế độ, cảnh báo, số vòng, mở màn |
| [G42](G42-nhan-vai-va-pha-dem.md) | Nhận vai, chọn dãy bàn và pha đêm | MVP | Vai, dãy bàn, lượt bắt, ứng viên, lời thì thầm, Thầy Pháp, việc giả |
| [G43](G43-buoi-sang-nguoi-thu-n-cong-1-noi.md) | Buổi sáng: Người thứ N+1 nói một chi tiết thật | MVP | Lời buổi sáng, thành Hồn, kết quả Thầy Pháp, bảng thư |
| [G44](G44-ban-ngay-day-ban-va-truc-xuat.md) | Ban ngày: thảo luận theo dãy bàn, bỏ phiếu trục xuất, thắng thua | MVP | Thảo luận, trục xuất, Ngoài Hành Lang, thắng thua (SS-FR-70–73) |
| [G45](G45-hon-gui-chu-cai.md) | Hồn gửi chữ cái | MVP | Mục tiêu của Hồn, chọn chữ, bảng thư |
| [G46](G46-vong-akinator.md) | Khoảnh khắc Akinator | MVP | Cây hỏi, "Bỏ qua tôi", kết quả |
| [G47](G47-lat-mat-ban-sao-ghep-va-xoa-so.md) | Lật mặt, giải thích cơ chế, bản sao ghép, xoá sổ | MVP | Công tắc "Hiện tên tôi", giải thích bắt buộc, bản sao ghép, chuyển sang tiêu huỷ |

### Tri Kỷ (trong Lá Lành)

| ID | Story | Phạm vi | Hành vi sở hữu |
|---|---|---|---|
| [G50](G50-gui-loi-moi-tri-ky.md) | Gửi lời mời Tri Kỷ | MVP (sau giai đoạn riêng tư) | Lối vào, đồng ý của A, tạo link, gửi lại, thu hồi |
| [G51](G51-nhan-va-dong-y-tri-ky.md) | Nhận và đồng ý lời mời Tri Kỷ | MVP (sau giai đoạn riêng tư) | Xem trước, đồng ý của B, không nhận, chặn, báo cáo |
| [G52](G52-xem-la-doi-tri-ky.md) | Xem lá đôi Tri Kỷ | MVP (sau giai đoạn riêng tư) | Ba khối nội dung, nhãn kiểu, dựng lại khi hồ sơ đổi |
| [G53](G53-chia-se-khi-ca-hai-dong-y.md) | Chia sẻ ảnh lá đôi khi cả hai đồng ý | MVP (sau giai đoạn riêng tư) | Xin chia sẻ, duyệt, hết hạn im lặng, dựng ảnh trên máy |
| [G54](G54-giai-tan-im-lang-va-xoa.md) | Giải tán lá đôi im lặng và xoá dữ liệu cặp | MVP (sau giai đoạn riêng tư) | Giải tán, rút đồng ý, xoá theo chuỗi |
| [G55](G55-hieu-nhau-khong.md) | Hiểu Nhau Không? | **Sau MVP** (TK-11) | Đồng ý trò đố, lượt 7 câu, điểm chung x/7 của cặp, kỷ lục của cặp |

## Bàn giao theo AGENTS.md

**Nguồn đã kiểm tra:** đầu file của từng story G01–G55; PRD và SRS của năm trò và hạ tầng phòng (bảng phạm vi MVP, truy vết);
`docs/user-stories/README.md` (quy tắc phân ranh giới).

**Phát hiện đã sửa:** README dòng game ghi story hạ tầng là G00–G09 trong khi file thật là G01–G09; đã sửa và ghi khung mã còn trống.

**Rủi ro chưa giải quyết:** mã G-story chưa đăng ký trong bản đồ story chung; G21 phụ thuộc D4; G11, G16, G37, G41 phụ thuộc D3, D8,
D7, D6.

**AC/DoD còn thiếu:** toàn bộ story chưa được owner duyệt và chưa có code.
