# Danh mục nơi sinh Việt Nam

**Phiên bản dữ liệu:** `vn-admin-2025-07-01`  
**Rà soát gần nhất:** 27/09/2026  
**Phạm vi:** ô chọn nơi sinh của Lá Khai Sinh, Aura và Radar; khu vực thô của hồ sơ matching.

## 1. Nguồn chuẩn

- [Nghị quyết `202/2025/QH15`](https://vanban.chinhphu.vn/?classid=1&docid=213930&orggroupid=1&pageid=27160) của Quốc hội có hiệu lực từ 12/06/2025: Việt Nam có 34 đơn vị hành chính cấp tỉnh, gồm 28 tỉnh và 6 thành phố.
- [Quyết định `19/2025/QĐ-TTg` và bảng mã 34 đơn vị](https://xaydungchinhsach.chinhphu.vn/bang-danh-muc-va-ma-so-cua-34-tinh-thanh-moi-cac-don-vi-hanh-chinh-cap-xa-moi-11925070418263625.htm) dùng thống nhất từ 01/07/2025.
- Danh mục dưới đây dùng tên và mã hiện hành; `place_id` nội bộ được giữ ổn định để không làm hỏng chart đã lưu.

## 2. Danh mục 34 tỉnh/thành hiện hành

| Mã | Tỉnh/thành | Mã | Tỉnh/thành |
|---:|---|---:|---|
| 01 | Hà Nội | 04 | Cao Bằng |
| 08 | Tuyên Quang | 11 | Điện Biên |
| 12 | Lai Châu | 14 | Sơn La |
| 15 | Lào Cai | 19 | Thái Nguyên |
| 20 | Lạng Sơn | 22 | Quảng Ninh |
| 24 | Bắc Ninh | 25 | Phú Thọ |
| 31 | Hải Phòng | 33 | Hưng Yên |
| 37 | Ninh Bình | 38 | Thanh Hóa |
| 40 | Nghệ An | 42 | Hà Tĩnh |
| 44 | Quảng Trị | 46 | Huế |
| 48 | Đà Nẵng | 51 | Quảng Ngãi |
| 52 | Gia Lai | 56 | Khánh Hòa |
| 66 | Đắk Lắk | 68 | Lâm Đồng |
| 75 | Đồng Nai | 79 | Thành phố Hồ Chí Minh |
| 80 | Tây Ninh | 82 | Đồng Tháp |
| 86 | Vĩnh Long | 91 | An Giang |
| 92 | Cần Thơ | 96 | Cà Mau |

## 3. Nơi sinh mang tên tỉnh cũ

Nơi một người được sinh ra không thay đổi khi địa giới hành chính thay đổi. Vì vậy:

- Browse mặc định chỉ hiện 34 tên hiện hành.
- Search vẫn nhận đủ 29 tên cấp tỉnh trước sắp xếp năm 2025.
- Kết quả tên cũ luôn ghi rõ `tên trước 2025 · nay thuộc …`; không âm thầm đổi nhãn.
- Tên cũ dùng một `place_id` riêng và tọa độ đại diện của địa phương cũ, không dùng centroid của toàn tỉnh mới đã mở rộng.
- Search tên tỉnh mới không trả hàng loạt tỉnh cũ đã nhập vào tỉnh đó; kết quả hiện hành luôn đứng rõ ràng.

Ví dụ:

- `Bình Dương` → `Bình Dương (tên trước 2025 · nay thuộc TP Hồ Chí Minh)`.
- `Quảng Nam` → `Quảng Nam (tên trước 2025 · nay thuộc Đà Nẵng)`.
- `Sài Gòn`, `TP HCM`, `TPHCM` → `Thành phố Hồ Chí Minh`.

## 4. UX và validation

- User có thể gõ tên có dấu hoặc không dấu, hoặc mở `Xem đủ 34 tỉnh/thành`.
- Danh sách dài nằm trong vùng scroll riêng để không kéo dài toàn bộ màn hình.
- Không cho client tự tạo `place_id`; backend chỉ nhận ID thuộc allow-list hiện hành hoặc alias lịch sử đã version.
- Khu vực matching chỉ nhận một trong 34 mã hiện hành. Tên tỉnh cũ không được dùng làm khu vực matching vì đây là khu vực hiện tại, không phải nơi sinh lịch sử.
- Chọn cấp tỉnh dùng tọa độ đại diện, không phải địa chỉ chính xác. Bản nâng cấp cấp xã/phường cần một dataset và vòng kiểm định riêng trước khi tăng nhãn precision.

## 5. Security và data privacy

- Danh mục và bộ tìm kiếm chạy từ dữ liệu tĩnh trong backend Lá Lành; không gửi từ khóa sang Google Maps hoặc dịch vụ geocoding bên thứ ba.
- Không xin GPS, địa chỉ nhà hoặc vị trí hiện tại trong flow nơi sinh.
- Query tìm kiếm không đi vào analytics, URL, share card hoặc crash breadcrumb.
- `place_id`, display name, timezone và tọa độ đại diện chỉ được lưu theo lifecycle birth profile đã consent; dữ liệu raw vẫn mã hóa at rest và có thể bị xóa từ Profile.
- Radar private chỉ giữ dữ liệu sinh của người kia trong request memory; danh mục mới không thay đổi retention policy này.

## 6. Release gate

Mỗi lần cập nhật danh mục phải chứng minh:

1. Có đúng 34 đơn vị và đúng 34 mã chính thức.
2. Browse rỗng chỉ trả 34 tên hiện hành, không lẫn alias lịch sử.
3. Đủ 29 tên cũ và nhãn hiện rõ mapping mới.
4. Search có/không dấu và alias phổ biến hoạt động.
5. `place_id` lạ bị từ chối ở birth/radar; `region_code` lạ bị từ chối ở matching.
6. Không có network call tới geocoder, GPS prompt hay dữ liệu nơi sinh trong telemetry/public output.
