# Baseline đa dạng và cá nhân hoá (P1), 16/10/2026

Đo trên **engine hiện tại** (release `836222282dfc`, renderer Daily `deterministic-vi-v12+daily-c0d51e63`,
Tarot `tarot-knowledge-v4`, Radar `radar-living-dossier-v1`). Chỉ dùng dữ liệu tổng hợp: không mạng, không
provider, không database. Định nghĩa chỉ số theo `docs/foundation/la-lanh-variety-measurement-spec.md`.
Ngưỡng theo `docs/plans/2026-10-16-p0-owner-decisions.md` (owner chốt theo đề xuất ngày 16/10).

**Tái hiện:**

```sh
cd apps/api
uv run python -m scripts.variety_fixtures --check   # fixture không đổi
uv run python -m scripts.variety_baseline           # khoảng 6 phút, ghi baseline.json + baseline-tables.md
PYTHONPATH=. uv run python ../../docs/fixtures/validate_tarot_question_bank.py
```

**Fixture:**

- `tests/fixtures/variety/profiles-v1.json` (sha256 `be5f447263b49f0d…`): 900 hồ sơ có giờ sinh, 300 hồ sơ
  chỉ có ngày sinh, 20 cặp cùng ngày sinh và cùng không rõ giờ.
- `radar-pairs-v1.json` (`0c11130f90925454…`): 50 cặp; một nửa người kia không rõ giờ.
- Ngân hàng câu hỏi Tarot v1.

Note ngày: 200 ngày từ 2026-10-01, `observed_at = local_date 12:00 UTC` như projection, giọng direct. Giọng
Cà khịa hiện ánh xạ một-một lên cùng bài nên cho cùng kết quả lặp.

## Kết quả chính

### Note ngày

| Nhóm | Hồ sơ | Tiêu đề | Cảnh | Việc nhỏ | Vì sao hôm nay? | Lời của Lá |
|---|---|---|---|---|---|---|
| Chỉ ngày sinh, pool 1 | 300 | lặp sau 6 ngày; 0% đạt ≥ 90 ngày | **83%** ngày trùng hôm trước | **98%** trùng hôm trước | không áp dụng | **100%** trùng hôm trước |
| Có giờ sinh, pool ≥ 4 | 900 | lặp sau 6 ngày; 0% đạt | 20% trùng hôm trước | 30% | 56% | 31% |
| Có giờ sinh, pool 1 hoặc 2–3; chỉ ngày sinh, pool 2–3 hoặc ≥ 4 | 0 | thiếu mẫu | | | | |

- **M1** (khoảng lặp ≥ 90 ngày): **0%** ở mọi phần và mọi nhóm đo được. Mục tiêu đã chốt là ≥ 95%.
- **M4** (note giống hệt giữa hai người cùng cung, cùng ngày): có giờ sinh **6,0%**; chỉ ngày sinh **100%**;
  cặp cùng ngày sinh **100%** số ngày. Mục tiêu đã chốt là < 1% (cặp cùng ngày sinh báo riêng).
- **M5** (yếu tố riêng mỗi note): chỉ ngày sinh **0**; có giờ sinh trung bình **0,43**, phân vị 10 là 0.
  Mục tiêu đã chốt là ≥ 1 cho nhóm chỉ ngày sinh chưa chọn mối quan tâm, và ≥ 2 cho nhóm có giờ chưa chọn.
- **M7:** bỏ giờ sinh thì 88% note đổi; sang ngày mới thì 100% note đổi ở ít nhất một phần.
- M3, M6, M8 chưa áp dụng (cần G0/G2).

### Tarot (247 câu hỏi hiện được chấp nhận, không gồm "khi nào"; 988 bài)

- **T2** (tiêu đề trùng): giọng mặc định chỉ có **5** tiêu đề khác nhau trên 247 câu, trùng **98%**. Cà khịa
  có 9 tiêu đề, trùng 96%. Mục tiêu US-20 là < 10%.
- **T3** (dấu hiệu câu chung chung trên 1976 vị trí):
  - "Ý chính của lá:" ở 988 vị trí (50%);
  - "Thử nhé:" ở 872/988 vị trí của giọng mặc định;
  - "Ví dụ:" ở **1976/1976** cảnh.

  Mục tiêu là 0.
- **T4** (cùng lá × vị trí, câu hỏi khác nhau): **0%** khác câu trên 21 060 cặp. Mục tiêu US-20 là ≥ 80%.
- **T1:** chưa áp dụng, vì engine chưa có dạng câu. Fixture: 253 chấp nhận / 75 từ chối (xem
  `docs/fixtures`).

### Hợp gu (50 cặp × 4 ngữ cảnh × 4 giọng = 800 bài)

- **R2:** đổi ngữ cảnh thì mục "hợp" và "ma sát" đổi **0%** câu. Đổi giọng thì đổi **8,8%** câu. Mục tiêu
  ≥ 50%.
- **R3:** **91%** câu của một cặp cũng có ở cặp khác. Mục tiêu < 30%.
- **R1** (đại diện tạm: câu không trùng cặp nào khác): trung bình 3,16 câu mỗi bài, phân vị 10 là 1.
- 0 cặp ít tín hiệu.

## Phát hiện cần ghi

1. **Người chỉ có ngày sinh:** mọi người cùng cung nhận cùng một note mỗi ngày. Lời của Lá không đổi suốt
   200 ngày. Đây là ưu tiên cao nhất của G1.
2. **Không hồ sơ có giờ nào rơi vào pool 1 hay 2–3** trong 200 ngày. Các fixture pool hẹp mà spec yêu cầu
   phải **dựng có chủ đích** ở G1 (ép pool), không lấy mẫu được.
3. **Hợp gu với người kia không rõ giờ:** chart được tính tại 12:00 giờ địa phương rồi bỏ Mặt Trăng, nhà
   và các góc (`BirthService.calculate_transient_chart`). Contact của hành tinh nhanh gần ngưỡng orb vì vậy
   có thể sai. Spec G2 §9 thay bằng orb trên tích hai miền ngày sinh. Đây là phát hiện để xử lý ở B4/G2,
   không sửa trong P1.
4. Tiêu đề Daily đổi mỗi ngày nhưng lặp sau đúng 6 ngày ở mọi nhóm, do chọn theo `ordinal % 6`.

## Mức sàn

Theo quyết định owner (A1–A3), mức sàn là **mục tiêu**, không phải hiện trạng. Baseline này ghi điểm xuất
phát. Mức sàn **chưa** được đưa vào `content-matrix-baseline.json`, vì engine hiện tại sẽ không đạt và CI
sẽ đỏ. Mức sàn được đưa vào theo từng bước khi mảng tương ứng đạt (B2 cho Tarot, G1 cho Daily, B4 cho Hợp
gu).
