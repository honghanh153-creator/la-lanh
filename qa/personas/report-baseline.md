# Baseline 100 người giả, 14.11.2026

**Tạm, chưa qua Codex.** Ngưỡng, rubric giám khảo và mô hình quay lại sẽ được Codex phản biện một lượt ngày 15.11. Có sửa thì chạy lại và thay số ở đây.

- Code đo: `collab/integration` tại `b583d50` cộng bộ chạy (commit `8b9c97e`, không đổi code sản phẩm).
- 100 người giả hư cấu × 29 ngày (14.11 → 12.12.2026). API chạy trên máy, SQLite tạm, dữ liệu giả, không gọi AI bên ngoài, không đụng production. Chạy hết 2 phút.
- Ngưỡng đăng ký trước: [thresholds.md](thresholds.md). Bảng đầy đủ: [runs/baseline-2026-11-14/report.md](runs/baseline-2026-11-14/report.md), số liệu máy đọc: `metrics.json`, toàn bộ 2.900 ngày-người: `transcript.jsonl.gz`.
- Giám khảo mù: 4 Claude subagent riêng chấm 400 mục (ngày 1, 8, 15, 22 của mỗi người). Một subagent khác gắn nhãn "việc nhẹ" cho 14 câu việc nhỏ.

Chạy lại: `pnpm personas:run -- --name <tên>`.

## Kết quả so với ngưỡng

| Mục | Ngưỡng | Baseline | |
|---|---|---|---|
| Số chuyện khác nhau mỗi 14 ngày | ≥ 5, mọi người | trung vị 1; chỉ 9,5% khung 14 ngày đạt | trượt |
| Tiêu đề lặp trong 7 ngày | 0 ngày | 1.479 ngày, ở 86/100 người | trượt |
| Lời của Lá lặp | ≤ 20% số ngày | 94% | trượt |
| Ngày Đuối được việc nhẹ | ≥ 90% | 10% (46/449) | trượt |
| Lời của Lá trái mood | 0 ngày | 0 ngày | đạt |
| Bắt câu có ý định khủng hoảng | 100% | 0/13 | trượt (đã biết; PR lớp khủng hoảng đang làm) |
| Báo nhầm câu "chết" nghĩa bóng | ≤ 2% | 0/21 | đạt |
| Điểm "hiểu mình" trung bình | ≥ 3,5 | 2,23 | trượt |
| Người giả có trung bình ≥ 3 | ≥ 70% | 11% | trượt |
| Quay lại sau 7 ngày (mô hình) | ≥ 35% | 2,3% | trượt |
| Quay lại sau 28 ngày (mô hình) | ≥ 15% | 0,3% | trượt |

Mô hình quay lại đã được chỉnh để một "app lối sống trung bình" ra 13% sau 7 ngày và 5% sau 28 ngày, khớp số công bố (OneSignal 2024: 13% và dưới 6%). Lá hiện ra 2,3% và 0,3%, **thấp hơn mức trung bình**. Đây là mô hình, không phải số người dùng thật.

## Theo dữ liệu người dùng đã nhập

| Đã nhập | Người | Trung vị chuyện / 14 ngày | Lời của Lá lặp | Quay lại sau 7 ngày (mô hình) |
|---|---|---|---|---|
| Chỉ ngày sinh | 30 | 1 | 100% | 2,8% |
| Giờ khoảng | 20 | 1 | 100% | 1,0% |
| Giờ + nơi chính xác | 50 | 4 | 88% | 2,4% |

Người nhập **giờ khoảng** cũng bị kẹt một chuyện suốt 29 ngày như người chỉ nhập ngày sinh. Bản đánh giá trước chưa thấy điều này. Hai nhóm này cũng không có nút "giữ việc nhỏ". Nút chỉ hiện với người có giờ và nơi chính xác (50% số ngày).

## 5 nhóm người giả yếu nhất (theo quay lại sau 7 ngày, mô hình)

| Nhóm | Người | Hiểu mình | Quay lại sau 7 ngày |
|---|---|---|---|
| Sinh viên năm cuối đang tìm việc | 8 | 2,25 | 0,1% |
| Người lớn tuổi | 5 | 2,00 | 0,6% |
| Sinh viên tiền eo hẹp | 6 | 2,21 | 0,7% |
| Sinh viên chịu áp lực gia đình | 6 | 2,04 | 1,1% |
| Sinh viên vừa học vừa làm thêm | 8 | 2,16 | 1,5% |

Nhóm khá nhất là sinh viên hay so sánh trên mạng xã hội (2,55 điểm, 6,2%). Không nhóm nào chạm mức app trung bình.

## Điều thấy được

1. **Cả 2.900 ngày chỉ có 14 câu việc nhỏ khác nhau.** Câu "Nói rõ bạn cần bao nhiêu thời gian để làm phần được nhờ" xuất hiện 843 lần. Giám khảo xếp 13/14 câu là không nhẹ (phải nói, hỏi, gửi cho người khác, hoặc so, chọn), nên ngày Đuối hầu như luôn nhận việc nặng.
2. **Mood không đổi gì.** 0% ngày việc nhỏ đổi sau khi chọn mood. Lời của Lá chưa lần nào trái mood, nhưng tiêu đề thì có. Ví dụ có 9 ngày chọn Chill mà tiêu đề vẫn là "Bạn đang mệt, vẫn nhận thêm việc giúp người khác." Đây là đúng lỗi trong #479.
3. **Nội dung xoay quanh vài chuyện văn phòng** (góp ý bản nháp, nhận lời giúp, tin nhắn chưa rõ). Giám khảo nhiều lần ghi "không hợp" với công nhân đi ca, người làm cơ khí, cư dân, người lớn tuổi. 298/400 mục được 2 điểm ("chung chung, ai đọc cũng được").
4. **Không có đường quay lại nào**: 0 ngày app nhắc chuyện hôm qua, 0 ngày có lời hẹn cho ngày mai. "Vì sao hôm nay" chỉ có ở 365/2.900 ngày, tất cả của người có giờ chính xác.
5. **An toàn:** 13 câu có ý định khủng hoảng gõ vào ô câu hỏi Tarot. 8 câu nhận một bài đọc Tarot bình thường. 5 câu bị yêu cầu "hỏi lại cho rõ", không có đường dây hỗ trợ nào. 21 câu "chết" nghĩa bóng và 418 câu hỏi thường đều không bị báo nhầm. Đây là mức nền để đo PR lớp khủng hoảng.

## Giới hạn

- Người giả và giám khảo đều là mô hình AI. Giám khảo đọc chữ, không thấy giao diện, tốc độ hay thông báo. Điểm cho biết hướng, không phải cảm nhận thật.
- Bốn lô giám khảo (mục được xáo ngẫu nhiên) cho trung bình 2,18–2,29, mục 2 điểm 67–80/99 mỗi lô. Chưa đo độ khớp giữa hai giám khảo trên **cùng** mục.
- Mô hình quay lại là luật tự đặt. Hiệu chỉnh khớp D7 và D28 công bố, nhưng D1 tham chiếu (33%) cao hơn số công bố (25%).
- Phần web chỉ lấy câu Lá đáp lại mood. Không chạy trình duyệt cho 2.900 ngày-người.
- Hồ sơ người giả hiện do Claude viết trên bộ khung có tỉ lệ cố định. Owner muốn neo thêm vào số liệu tổng hợp đã công bố về giới trẻ Việt Nam (dùng điện thoại, mạng xã hội, game, chi tiêu). Việc đó đang làm, sẽ chạy lại khi xong.
- Không dùng dữ liệu của người thật nào, kể cả mạng xã hội.

## Trong lúc làm đã sửa

- Một người giả 17 tuổi bị app từ chối vì app chỉ nhận từ 18 tuổi (US-02). Đã đổi thành 18 tuổi, thêm luật vào bộ sinh và bộ kiểm.
- Bộ chạy giữ việc nhỏ ngày thứ hai bị từ chối (409) vì app cần thay việc cũ. Đã làm như web: lấy việc đang giữ rồi thay rõ ràng.
- Dạng đầu của mô hình quay lại không cho phép đạt ngưỡng 35% ngay cả khi trải nghiệm gần hoàn hảo. Đã đổi trước baseline, ghi trong thresholds.md.
