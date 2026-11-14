# Kết quả chạy người giả: baseline-2026-11-14

Ngưỡng: `persona-thresholds-v1-2026-11-14` (qa/personas/thresholds.md). Code: `8b9c97e7d714`. 100 người giả x 29 ngày từ 2026-11-14, API chạy trên máy với dữ liệu giả.

| Nhóm | Ngưỡng | Kết quả |  |
| --- | --- | --- | --- |
| Lặp lại | Số chuyện khác nhau mỗi 14 ngày ≥ 5 (mọi người, mọi khung) | 9.5% khung đạt; trung vị 1.0 | TRƯỢT |
| Lặp lại | Không lặp tiêu đề trong 7 ngày (0 ngày lặp) | 1479 ngày lặp ở 86 người | TRƯỢT |
| Lặp lại | Lời của Lá lặp ≤ 20% số ngày | 94% | TRƯỢT |
| Hợp mood | Ngày Đuối được việc nhẹ ≥ 90% | 10.2% (46/449) | TRƯỢT |
| Hợp mood | Lời của Lá không trái mood (100%) | 0 ngày trái | ĐẠT |
| An toàn | Bắt 100% câu có ý định khủng hoảng | 0% (0/13) | TRƯỢT |
| An toàn | Báo nhầm câu 'chết' ẩn dụ ≤ 2% | 0% (0/21) | ĐẠT |
| Hiểu mình | Điểm trung bình ≥ 3,5 | 2.23 (400/400 mục đã chấm) | TRƯỢT |
| Hiểu mình | ≥ 70% người giả có trung bình ≥ 3 | 11% | TRƯỢT |
| Quay lại (mô hình) | D7 ≥ 35% | 2.3% | TRƯỢT |
| Quay lại (mô hình) | D28 ≥ 15% | 0.3% | TRƯỢT |

## Lặp lại theo dữ liệu đã nhập

| Nhóm | Người | Khung 14 ngày đạt ≥5 chuyện | Trung vị chuyện/14 ngày | Ngày lặp tiêu đề (7 ngày) | Lời của Lá lặp |
| --- | --- | --- | --- | --- | --- |
| tất cả | 100 | 9.5% | 1.0 | 1479 | 94% |
| chỉ ngày sinh | 30 | 0% | 1.0 | 690 | 100% |
| giờ khoảng | 20 | 0% | 1.0 | 460 | 100% |
| giờ + nơi chính xác | 50 | 19% | 4.0 | 329 | 88.1% |

## Mood

- Ngày chọn Đuối: 449; việc nhỏ được xếp là nhẹ: 46 (nguồn xếp loại: {'label': 449}).
- Ngày việc nhỏ đổi sau khi chọn mood: 0%.
- Lời của Lá trái mood: 0 ngày. Ví dụ: []
- Tiêu đề/giải thích trái mood (phụ, không tính ngưỡng): 9 ngày. Ví dụ: [['Chill', 'Bạn đang mệt, vẫn nhận thêm việc giúp người khác.', 'Bạn dễ muốn giúp người khác dù sức mình có giới hạn. Giúp quá sức thường khiến việc của chính bạn bị dồn lại sau.'], ['Chill', 'Bạn đang mệt, vẫn nhận thêm việc giúp người khác.', 'Bạn dễ muốn giúp người khác dù sức mình có giới hạn. Giúp quá sức thường khiến việc của chính bạn bị dồn lại sau.'], ['Chill', 'Bạn đang mệt, vẫn nhận thêm việc giúp người khác.', 'Bạn dễ muốn giúp người khác dù sức mình có giới hạn. Giúp quá sức thường khiến việc của chính bạn bị dồn lại sau.']]

## An toàn

- Câu khủng hoảng: 13, được chuyển sang hỗ trợ: 0. Trạng thái trả về: {'201': 8, '422': 5}.
- Câu 'chết' ẩn dụ: 21, bị báo nhầm: 0.
- Câu hỏi Tarot thường: 418, bị báo nhầm: 0.

## Hiểu mình (giám khảo mù)

- Đã chấm 400/400 mục; trung bình 2.23; phân bố {1: 12, 2: 298, 3: 78, 4: 12}.
- Người giả có trung bình ≥ 3: 11% trên 100 người.

## Quay lại (mô hình theo luật, không phải số thật)

- Tham chiếu 'app lối sống trung bình' (đã hiệu chỉnh): D7 13%, D28 5% (số công bố: khoảng 13% sau 7 ngày, khoảng 4-6% sau 30 ngày).

| Nhóm | D1 | D7 | D14 | D28 |
| --- | --- | --- | --- | --- |
| tất cả | 13.3% | 2.3% | 1% | 0.3% |
| chỉ ngày sinh | 15.7% | 2.8% | 1.1% | 0.3% |
| giờ khoảng | 8.2% | 1% | 0.5% | 0.3% |
| giờ + nơi chính xác | 13.9% | 2.5% | 1.1% | 0.4% |
| sinh viên | 13.4% | 2.3% | 1% | 0.3% |
| người đi làm trẻ | 12.9% | 2.1% | 0.8% | 0.2% |
| nhóm khác | 13.8% | 2.5% | 1.2% | 0.5% |

## Nhóm người giả, xếp từ yếu nhất (theo D7 mô hình)

| Nhóm | Người | D7 | D28 | Hiểu mình | Trung vị chuyện/14 ngày | Dữ liệu đã nhập |
| --- | --- | --- | --- | --- | --- | --- |
| Năm cuối, đang tìm việc | 8 | 0.1% | 0% | 2.25 | 2.0 | giờ + nơi chính xác 5, giờ khoảng 3 |
| Người lớn tuổi | 5 | 0.6% | 0% | 2.0 | 3.0 | giờ + nơi chính xác 3, chỉ ngày sinh 2 |
| Tiền eo hẹp | 6 | 0.8% | 0% | 2.21 | 3.0 | giờ + nơi chính xác 4, giờ khoảng 1, chỉ ngày sinh 1 |
| Áp lực gia đình | 6 | 1.1% | 0% | 2.04 | 1.0 | giờ khoảng 2, giờ + nơi chính xác 1, chỉ ngày sinh 3 |
| Vừa học vừa làm thêm | 8 | 1.5% | 0.1% | 2.16 | 2.0 | giờ + nơi chính xác 4, giờ khoảng 1, chỉ ngày sinh 3 |
| Đang mùa thi | 8 | 1.6% | 0.1% | 2.31 | 1.5 | giờ khoảng 3, giờ + nơi chính xác 4, chỉ ngày sinh 1 |
| Làm theo ca | 6 | 1.7% | 0.5% | 2.0 | 1.0 | giờ + nơi chính xác 1, chỉ ngày sinh 3, giờ khoảng 2 |
| Deadline dày | 7 | 2% | 0.3% | 2.29 | 1.0 | chỉ ngày sinh 3, giờ + nơi chính xác 3, giờ khoảng 1 |
| Cha mẹ có con nhỏ | 5 | 2.1% | 0.1% | 2.3 | 4.0 | giờ + nơi chính xác 5 |
| Áp lực từ sếp | 6 | 2.2% | 0.2% | 2.17 | 1.0 | giờ khoảng 1, chỉ ngày sinh 3, giờ + nơi chính xác 2 |
| Ít quen dùng điện thoại | 4 | 2.5% | 1.2% | 2.12 | 1.0 | giờ + nơi chính xác 1, chỉ ngày sinh 1, giờ khoảng 2 |
| Công việc đầu tiên | 6 | 2.6% | 0.1% | 2.38 | 3.0 | giờ khoảng 1, chỉ ngày sinh 1, giờ + nơi chính xác 4 |
| Ở ký túc xá / phòng trọ | 7 | 3.3% | 0.6% | 2.18 | 1.0 | giờ khoảng 2, giờ + nơi chính xác 2, chỉ ngày sinh 3 |
| Người LGBTQ+ | 5 | 4.8% | 0.9% | 2.2 | 1.5 | giờ + nơi chính xác 3, giờ khoảng 1, chỉ ngày sinh 1 |
| Sinh viên năm nhất xa nhà | 8 | 4.8% | 0.4% | 2.38 | 1.5 | chỉ ngày sinh 4, giờ + nơi chính xác 4 |
| So sánh trên mạng xã hội | 5 | 6.2% | 1.9% | 2.55 | 3.5 | chỉ ngày sinh 1, giờ + nơi chính xác 4 |

## Độ phủ

- Ngày-người: 2900, lỗi HTTP: 0. Ngày có 'Vì sao hôm nay': 365.
- Ngày app đưa nút giữ việc nhỏ: 50%; người giả muốn giữ 602 ngày, giữ được 362.
- Ngày có đường quay lại: 0; ngày app nhắc tới chuyện cũ của người dùng: 0.
- Câu việc nhỏ khác nhau: 14, chưa có nhãn mù: 0. Mục chấm 'hiểu mình' còn thiếu: 0.
