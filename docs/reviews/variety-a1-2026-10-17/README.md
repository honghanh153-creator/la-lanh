# B3-1a (A1): báo cáo sau khi bật xoay vòng

Dữ liệu tổng hợp, không mạng, không provider, không DB. Cùng fixture, cửa sổ (200 ngày từ 2026-10-01) và
cách tính với baseline P1 (`docs/reviews/variety-baseline-2026-10-16/`). Khoá chọn biến thể là khoá tổng
hợp trong script, không phải secret của server. `owner_scope` của mỗi hồ sơ là UUIDv5 của mã fixture.

```bash
pnpm variety:a1   # ghi after.json và after-tables.md trong thư mục này
```

`after.json` và `after-tables.md` sinh từ cùng một lần chạy, mất khoảng 7 phút. Chỉ đo note ngày, vì A1
không đổi Tarot và Hợp gu.

**Lưu ý về pool:** sau A1, pool là top-K (K = 3) issue khác nhau của ngày đó sau khi xếp hạng, không còn là
các issue hoà hạng tốt nhất như ở P1. Vì vậy nhóm theo pool của hai báo cáo không so trực tiếp được: 880
hồ sơ có giờ sinh chuyển từ pool 1 sang pool 2–3.

## So với baseline P1

| Chỉ số | P1 (tắt) | Sau A1 (bật) |
|---|---|---|
| Cùng tình huống, hai ngày liền trùng tiêu đề / cảnh / việc nhỏ | có (cảnh đứng 6 ngày, việc nhỏ 48 ngày) | **0 / 0 / 0** trên 86 167 cặp ngày |
| M2 người chỉ có ngày sinh: cảnh / việc nhỏ trùng hôm trước | 83% / 98% | **0% / 0%** |
| M4 hai người cùng cung, cùng ngày, note giống hệt: chỉ ngày sinh | 100% | **0,25%** |
| M4 cặp cùng ngày sinh (chỉ ngày sinh) | 100% | **0,22%** |
| M4 có giờ sinh | 6,0% | **0,02%** |
| 3 ngày liền cùng tình huống khi pool ≥ 2 | không đo | **0** |
| Bộ đầy đủ (tiêu đề, cảnh, việc nhỏ) đã gặp trong 30 / 60 ngày trước | không đo | **2,5% / 4,9%** |
| M7 ngày sau đổi note | xem P1 | **100%** |

Mô phỏng ngoài engine trong kế hoạch ước 6,7% / 13,6% trùng bộ trong 30 / 60 ngày. Top-K thật cho thấp hơn:
2,5% / 4,9%.

## Chưa đạt, hoặc thuộc bước sau

- **M1 (không lặp câu trong ≥ 90 ngày): 0%.**
  - Mỗi trục chỉ có 6–8 câu, nên câu quay lại sau khoảng 2–8 ngày.
  - Đây là giới hạn của kho, không phải của bộ chọn. Cam kết (b) cần lịch chủ L ≥ 90 của G0/G1.
- **"Vì sao hôm nay?" trùng hôm trước: 12–17%.**
  - Câu này theo transit, khi transit kéo dài nhiều ngày thì câu giữ nguyên.
  - Thuộc AC12 (G1).
- **Lời của Lá:**
  - với người chỉ có ngày sinh, trùng hôm trước 100%;
  - với người có giờ sinh, 14–30%.
  - Lời đi theo issue, mà pool của người chỉ có ngày sinh vẫn là 1. Thuộc A2/G1.

## Đánh đổi cần owner quyết: M5 giảm

Top-K đưa các tình huống hạng 2–3 vào luân phiên. Các tình huống này thường dựa ít yếu tố riêng hơn.

| Có giờ sinh | P1 | Sau A1 |
|---|---|---|
| M5 trung bình (yếu tố riêng mỗi note) | ≈ 0,95 | ≈ 0,69 |
| Ngày có 0 yếu tố riêng | ≈ 10% | ≈ 34% |

Cả hai mức đều dưới ngưỡng owner đã chốt: "có giờ, chưa chọn mối quan tâm ≥ 2". Có hai hướng:

1. **Giữ như spec** (top-K theo điểm) và để G1 cân lại rank, cùng pool transit.
2. **Siết top-K:** chỉ nhận tình huống có ít nhất bằng số yếu tố riêng của tình huống hạng 1. Đổi lại, pool hẹp
   lại và tình huống ít luân phiên hơn. Các trục vẫn xoay mỗi ngày.

PR này làm theo spec đã duyệt (hướng 1) và chỉ báo cáo đánh đổi, không tự đổi spec.
