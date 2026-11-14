# 1000 người giả

`personas-1000.json` = 100 người giả cũ (`personas-100.json`, **giữ nguyên** để so được với mọi lần chấm trước) + 900 người mới P101–P1000.
Mọi người là **hư cấu**. Không dùng hồ sơ, bài đăng hay dữ liệu của người thật nào. Ngày, giờ, nơi sinh sinh ngẫu nhiên có hạt giống cố định.

## Dựng lại

```bash
python3 qa/personas/build_skeleton_1000.py > skeleton-900.json   # khung, hạt giống 2026111410
# 30 người viết mù, mỗi người ~30 khung, theo personas-1000-writing-guide.md, tự kiểm bằng check_batch.py
python3 qa/personas/merge_1000.py <thư mục out-NN.json> > qa/personas/personas-1000.json
uv run --directory apps/api python -m scripts.persona_validate --personas ../../qa/personas/personas-1000.json
```

Phần khung (tỉ lệ, tuổi, thuộc tính, câu thử an toàn) tái tạo y hệt từ hạt giống. Phần chữ do người viết là mô hình AI, nên không tái tạo y hệt được; tệp JSON đã commit là bản chuẩn.

## Tỉ lệ và nguồn

Nguồn số liệu: [youth-stats-2026-11-14.md](youth-stats-2026-11-14.md) (số tổng hợp đã qua 3 lượt kiểm chứng). Mục nào không có số kiểm chứng được ghi là **giả định nội bộ**.

| Thuộc tính | Toàn bộ 1000 | Nguồn |
|---|---|---|
| Tuổi 18–24 | 600 (60%) | Owner chọn. Không có người 17 tuổi vì app chỉ nhận từ 18 tuổi (US-02) |
| Sinh viên đại học | 386 | Owner ưu tiên sinh viên |
| Học nghề / cao đẳng | 50 | Owner chọn (thêm bối cảnh) |
| Chưa học tiếp, chưa có việc ổn định | 35 | Owner chọn |
| Đi làm, 18–24 tuổi (việc đầu, công nhân/làm ca, bán online) | 127 | Owner chọn |
| Đi làm, 25–34 tuổi (deadline, sếp, làm ca, tự do) | 174 | Giả định |
| Đi làm 35–49 | 34 | Giả định |
| Cha mẹ có con nhỏ | 75 | Giả định |
| Người lớn tuổi (50+) | 60 | Giả định |
| Ít quen điện thoại (nhóm riêng) | 34 | Giả định; cộng người lớn tuổi ít quen điện thoại thì khoảng 6% |
| LGBTQ+ (25 trong nhóm riêng, 45 rải ở các nhóm khác) | 70 (7%) | Giả định; không có số Việt Nam qua kiểm chứng |
| Vùng Bắc / Trung / Nam (900 mới) | 342 / 198 / 360 | Giả định, gần phân bố dân số |
| Đang sống ở thành phố / thị xã / nông thôn (900 mới) | 460 / 256 / 184 | Giả định; sinh viên phần lớn ở thành phố nơi học |
| Mức chi sinh viên (không kể học phí) | dưới 5 triệu khoảng 80%; từ 5 triệu: TP.HCM 32%, Hà Nội 19%, Đà Nẵng 9%, nơi khác 19% | Cốc Cốc 12/2025, n=842 (phát hiện 4) |
| Thu nhập người đi làm | dưới 5 triệu 20%, 5–10 triệu 40%, 10–20 triệu 30%, trên 20 triệu 10% | Giả định; số lương đầu VNU-IS (trung bình 12,3 triệu) chỉ của một trường |
| Dùng Facebook | khoảng 95% | DataReportal 2025 (phát hiện 2) |
| TikTok là app dùng nhiều nhất | 70% người ≤ 26 tuổi; 35% người 27–44; 15% người 45+ | Q&Me 2025: TikTok là app số 1 ở người ≤ 26 (định tính); tỉ lệ là giả định |
| YouTube / Messenger | khoảng 78% / 70% | DataReportal 2025 |
| Zalo | mọi người có; app chính của người 50+ | Decision Lab: Zalo dẫn đầu ở người lớn tuổi (định tính) |
| Xem video "chọn tụ" Tarot trên TikTok | 30% người ≤ 26 có TikTok; 10% người lớn hơn | Giả định; không có số Tarot qua kiểm chứng |
| Tin chiêm tinh (nhiều / nửa tin / không) | 30 / 45 / 25% (900 mới) | YouGov 2017: 75% người Việt coi trọng tử vi |
| Thức sau 0 giờ | 43% người ≤ 26 | Sinh viên Y TP.HCM 2021 (phát hiện 6) |
| Mức căng thẳng thấp / vừa / cao | 22 / 63 / 15% | CSSQ 2021 (phát hiện 7) |
| Dùng chung điện thoại | khoảng 9% (900 mới); cao hơn ở người lớn tuổi, ít quen điện thoại, nông thôn | Giả định |
| Không có ai an toàn để tâm sự | khoảng 22% (900 mới); cao hơn ở áp lực gia đình, LGBTQ+, chưa có việc | Giả định |
| Loại hồ sơ: chỉ ngày sinh / giờ khoảng / chính xác | 300 / 200 / 500 | Giữ tỉ lệ 30/20/50 của bộ 100 |
| Câu thử khủng hoảng | 100 người (10%), 135 câu | Giữ tỉ lệ bộ 100 |
| Câu "chết" nghĩa bóng | 180 người (18%), 205 câu | Giữ tỉ lệ bộ 100 |

Hai chỗ lệch đã thấy ở bộ 100 được sửa trong 900 người mới: TikTok là app chính của phần lớn người trẻ, và có sinh viên tiêu từ 5 triệu/tháng theo đúng tỉ lệ đo được. Bộ 100 cũ không sửa.

## Thuộc tính mới

Người mới có thêm `attributes`: `gen_z`, `lives_in`, `living_area`, `income`, `platforms`, `main_app`, `pick_a_pile_watcher`, `lgbtq`, `shared_phone`, `no_safe_person`, `digital_literacy`, `sleeps_after_midnight`, `stress`. P001–P100 không có trường này; báo cáo theo thuộc tính chỉ dùng P101–P1000, trừ khi ghi khác.

Lưu ý: ở các lần chấm mock trước, "dùng chung máy" và "không có ai an toàn" là **tình huống hôm nay** gán cho từng người. Ở bộ 1000, đây là **thuộc tính lâu dài** của người mới; tình huống hôm nay vẫn có thể gán thêm khi chấm mock.

## Giới hạn

- Số liệu nguồn là mẫu nhỏ, mẫu thuận tiện hoặc của một trường; nhiều tỉ lệ là giả định. Tỉ lệ ở đây để người giả gần thực tế hơn, không phải để suy ra tỉ lệ người dùng thật.
- Người viết là mô hình AI, nên hồ sơ có thể giống nhau về giọng văn.
