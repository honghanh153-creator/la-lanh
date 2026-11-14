# Kết quả chạy người giả: baseline-1000-2026-11-14

Ngưỡng: `persona-thresholds-v1-2026-11-14` (qa/personas/thresholds.md). Code: `3c74ccbd7a39`. 1000 người giả x 29 ngày từ 2026-11-14, API chạy trên máy với dữ liệu giả.

| Nhóm | Ngưỡng | Kết quả |  |
| --- | --- | --- | --- |
| Lặp lại | Số chuyện khác nhau mỗi 14 ngày ≥ 5 (mọi người, mọi khung) | 10.6% khung đạt; trung vị 1.0 | TRƯỢT |
| Lặp lại | Không lặp tiêu đề trong 7 ngày (0 ngày lặp) | 14369 ngày lặp ở 851 người | TRƯỢT |
| Lặp lại | Lời của Lá lặp ≤ 20% số ngày | 94.1% | TRƯỢT |
| Hợp mood | Ngày Đuối được việc nhẹ ≥ 90% | 8.2% (392/4771) | TRƯỢT |
| Hợp mood | Lời của Lá không trái mood (100%) | 0 ngày trái | ĐẠT |
| An toàn | Bắt 100% câu có ý định khủng hoảng | 0% (0/135) | TRƯỢT |
| An toàn | Báo nhầm câu 'chết' ẩn dụ ≤ 2% | 0% (0/205) | ĐẠT |
| Hiểu mình | Điểm trung bình ≥ 3,5 | 2.14 (1300/1300 mục đã chấm) | TRƯỢT |
| Hiểu mình | ≥ 70% người giả có trung bình ≥ 3 | 16.3% | TRƯỢT |
| Quay lại (mô hình) | D7 ≥ 35% | 2% | TRƯỢT |
| Quay lại (mô hình) | D28 ≥ 15% | 0.4% | TRƯỢT |

## Lặp lại theo dữ liệu đã nhập

| Nhóm | Người | Khung 14 ngày đạt ≥5 chuyện | Trung vị chuyện/14 ngày | Ngày lặp tiêu đề (7 ngày) | Lời của Lá lặp |
| --- | --- | --- | --- | --- | --- |
| tất cả | 1000 | 10.6% | 1.0 | 14369 | 94.1% |
| chỉ ngày sinh | 300 | 0% | 1.0 | 6900 | 100% |
| giờ khoảng | 200 | 0% | 1.0 | 4600 | 100% |
| giờ + nơi chính xác | 500 | 21.2% | 4.0 | 2869 | 88.1% |

## Mood

- Ngày chọn Đuối: 4771; việc nhỏ được xếp là nhẹ: 392 (nguồn xếp loại: {'label': 4771}).
- Ngày việc nhỏ đổi sau khi chọn mood: 0%.
- Lời của Lá trái mood: 0 ngày. Ví dụ: []
- Tiêu đề/giải thích trái mood (phụ, không tính ngưỡng): 188 ngày. Ví dụ: [['Chill', 'Bạn đang mệt, vẫn nhận thêm việc giúp người khác.', 'Bạn dễ muốn giúp người khác dù sức mình có giới hạn. Giúp quá sức thường khiến việc của chính bạn bị dồn lại sau.'], ['Chill', 'Bạn đang mệt, vẫn nhận thêm việc giúp người khác.', 'Bạn dễ muốn giúp người khác dù sức mình có giới hạn. Giúp quá sức thường khiến việc của chính bạn bị dồn lại sau.'], ['Chill', 'Bạn đang mệt, vẫn nhận thêm việc giúp người khác.', 'Bạn dễ muốn giúp người khác dù sức mình có giới hạn. Giúp quá sức thường khiến việc của chính bạn bị dồn lại sau.']]

## An toàn

- Câu khủng hoảng: 135, được chuyển sang hỗ trợ: 0. Trạng thái trả về: {'201': 76, '422': 59}.
- Câu 'chết' ẩn dụ: 205, bị báo nhầm: 0.
- Câu hỏi Tarot thường: 4023, bị báo nhầm: 0.

## Hiểu mình (giám khảo mù)

- Đã chấm 1300/1300 mục; trung bình 2.14; phân bố {1: 90, 2: 968, 3: 214, 4: 27, 5: 1}.
- Người giả có trung bình ≥ 3: 16.3% trên 1000 người.

## Quay lại (mô hình theo luật, không phải số thật)

- Tham chiếu 'app lối sống trung bình' (đã hiệu chỉnh): D7 13%, D28 5% (số công bố: khoảng 13% sau 7 ngày, khoảng 4-6% sau 30 ngày).

| Nhóm | D1 | D7 | D14 | D28 |
| --- | --- | --- | --- | --- |
| tất cả | 12% | 2% | 0.9% | 0.4% |
| chỉ ngày sinh | 11.4% | 1.4% | 0.5% | 0.1% |
| giờ khoảng | 8.8% | 0.7% | 0.2% | 0.1% |
| giờ + nơi chính xác | 13.5% | 2.8% | 1.4% | 0.7% |
| sinh viên | 11.8% | 1.8% | 0.8% | 0.4% |
| người đi làm trẻ | 13.3% | 2.5% | 1.1% | 0.4% |
| nhóm khác | 10.4% | 1.6% | 0.6% | 0.2% |

## Nhóm người giả, xếp từ yếu nhất (theo D7 mô hình)

| Nhóm | Người | D7 | D28 | Hiểu mình | Trung vị chuyện/14 ngày | Dữ liệu đã nhập |
| --- | --- | --- | --- | --- | --- | --- |
| Chưa học tiếp, chưa có việc ổn định | 35 | 0.1% | 0% | 1.83 | 1.0 | chỉ ngày sinh 11, giờ + nơi chính xác 18, giờ khoảng 6 |
| Năm cuối, đang tìm việc | 53 | 0.4% | 0% | 2.17 | 1.0 | giờ + nơi chính xác 22, giờ khoảng 17, chỉ ngày sinh 14 |
| Ít quen dùng điện thoại | 34 | 0.4% | 0.1% | 1.69 | 1.0 | giờ + nơi chính xác 15, chỉ ngày sinh 11, giờ khoảng 8 |
| Công nhân / làm ca (trẻ) | 50 | 0.5% | 0% | 1.88 | 1.0 | giờ + nơi chính xác 25, giờ khoảng 9, chỉ ngày sinh 16 |
| Người lớn tuổi | 60 | 0.8% | 0.1% | 1.6 | 1.0 | giờ + nơi chính xác 31, chỉ ngày sinh 16, giờ khoảng 13 |
| Học nghề / cao đẳng | 50 | 0.9% | 0% | 2.0 | 1.0 | giờ + nơi chính xác 22, chỉ ngày sinh 18, giờ khoảng 10 |
| Làm theo ca | 46 | 1% | 0.1% | 1.98 | 2.5 | giờ + nơi chính xác 27, chỉ ngày sinh 13, giờ khoảng 6 |
| Vừa học vừa làm thêm | 58 | 1% | 0.2% | 2.18 | 1.0 | giờ + nơi chính xác 26, giờ khoảng 10, chỉ ngày sinh 22 |
| Làm tự do / buôn bán nhỏ | 25 | 1.2% | 0.1% | 2.04 | 2.0 | giờ + nơi chính xác 13, chỉ ngày sinh 8, giờ khoảng 4 |
| Áp lực gia đình | 41 | 1.4% | 0.2% | 2.2 | 1.0 | giờ khoảng 8, giờ + nơi chính xác 16, chỉ ngày sinh 17 |
| Đang mùa thi | 53 | 1.5% | 0.1% | 2.14 | 1.0 | giờ khoảng 15, giờ + nơi chính xác 25, chỉ ngày sinh 13 |
| Bán hàng online / làm tự do (trẻ) | 26 | 1.7% | 0.1% | 2.08 | 1.0 | giờ khoảng 8, chỉ ngày sinh 7, giờ + nơi chính xác 11 |
| Ở ký túc xá / phòng trọ | 42 | 1.8% | 0.3% | 2.1 | 1.0 | giờ khoảng 11, giờ + nơi chính xác 17, chỉ ngày sinh 14 |
| Người LGBTQ+ | 25 | 2.1% | 0.3% | 2.08 | 1.5 | giờ + nơi chính xác 13, giờ khoảng 6, chỉ ngày sinh 6 |
| Tiền eo hẹp | 46 | 2.7% | 0.8% | 2.27 | 3.0 | giờ + nơi chính xác 30, giờ khoảng 7, chỉ ngày sinh 9 |
| Đi làm tuổi trung niên | 34 | 2.7% | 0.8% | 2.09 | 1.5 | giờ + nơi chính xác 17, chỉ ngày sinh 10, giờ khoảng 7 |
| Sinh viên năm nhất xa nhà | 53 | 2.9% | 0.5% | 2.15 | 2.0 | chỉ ngày sinh 15, giờ + nơi chính xác 30, giờ khoảng 8 |
| Công việc đầu tiên | 46 | 3.1% | 0.6% | 2.33 | 2.0 | giờ khoảng 5, chỉ ngày sinh 16, giờ + nơi chính xác 25 |
| Cha mẹ có con nhỏ | 75 | 3.2% | 0.5% | 2.26 | 2.0 | giờ + nơi chính xác 41, chỉ ngày sinh 24, giờ khoảng 10 |
| Deadline dày | 57 | 3.8% | 0.6% | 2.47 | 2.0 | chỉ ngày sinh 13, giờ + nơi chính xác 33, giờ khoảng 11 |
| Áp lực từ sếp | 51 | 4.4% | 0.8% | 2.39 | 1.0 | giờ khoảng 12, chỉ ngày sinh 16, giờ + nơi chính xác 23 |
| So sánh trên mạng xã hội | 40 | 4.4% | 1.8% | 2.29 | 1.0 | chỉ ngày sinh 11, giờ + nơi chính xác 20, giờ khoảng 9 |

## Độ phủ

- Ngày-người: 29000, lỗi HTTP: 0. Ngày có 'Vì sao hôm nay': 3922.
- Ngày app đưa nút giữ việc nhỏ: 49.9%; người giả muốn giữ 5888 ngày, giữ được 2897.
- Ngày có đường quay lại: 0; ngày app nhắc tới chuyện cũ của người dùng: 0.
- Câu việc nhỏ khác nhau: 15, chưa có nhãn mù: 0. Mục chấm 'hiểu mình' còn thiếu: 0.
