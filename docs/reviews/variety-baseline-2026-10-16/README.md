# Baseline đa dạng và cá nhân hoá (P1), 16/10/2026

Đo trên **engine hiện tại** (release `836222282dfc`, renderer Daily `deterministic-vi-v12+daily-c0d51e63`,
Tarot `tarot-knowledge-v4`, Radar `radar-living-dossier-v1`). Chỉ dùng dữ liệu tổng hợp: không mạng, không
provider, không database. Định nghĩa chỉ số theo `docs/foundation/la-lanh-variety-measurement-spec.md`.
Ngưỡng theo `docs/plans/2026-10-16-p0-owner-decisions.md` (owner chốt theo đề xuất ngày 16/10).

**Tái hiện:**

```sh
cd apps/api
uv run python -m scripts.variety_fixtures --check   # fixture không đổi
uv run python -m scripts.variety_baseline           # khoảng 13 phút, ghi baseline.json + baseline-tables.md
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

Bản này thay bản đầu (88cd432) sau review của Codex, sửa 4 phép đo: pool, M5, R2/R3, ma trận Tarot.
Tạo lại từ head của PR; `baseline.json` và `baseline-tables.md` sinh từ cùng lần chạy (khoảng 13 phút).

### Cách phân nhóm theo pool

**Pool** của một ngày là số issue khác nhau mà planner **có thể** chọn hôm đó: đầu vào của
`daily_psychology._pick`, ghi lại mà không đổi lựa chọn. Đây không phải các issue đã thắng trong cả cửa
sổ. Nhóm của hồ sơ là **bucket xuất hiện nhiều nhất** trong các ngày; hoà thì lấy bucket nhỏ hơn. Người chỉ
có ngày sinh không đi qua `_pick` (issue cố định theo cung), nên pool = 1.

Phân bố ngày-hồ sơ có giờ sinh: pool 1 ở **204 119** ngày, 2–3 ở **35 880** ngày, ≥ 4 ở **1** ngày.

### Note ngày

| Nhóm | Hồ sơ | Tiêu đề | Cảnh trùng hôm trước | Việc nhỏ trùng hôm trước | "Vì sao hôm nay?" trùng hôm trước | Lời của Lá trùng hôm trước |
|---|---|---|---|---|---|---|
| Chỉ ngày sinh, pool 1 | 300 | lặp sau 6 ngày | **83%** | **98%** | không áp dụng | **100%** |
| Có giờ sinh, pool 1 | 865 | lặp sau 6 ngày | 21% | 31% | 57% | 31% |
| Có giờ sinh, pool 2–3 | 35 (**thiếu mẫu**) | lặp sau 6 ngày | 12% | 19% | 50% | 20% |
| Có giờ sinh, pool ≥ 4; chỉ ngày sinh, pool 2–3 hoặc ≥ 4 | 0 | thiếu mẫu | | | | |

- **M1** (khoảng lặp ≥ 90 ngày): **0%** ở mọi phần và mọi nhóm đo được. Mục tiêu ≥ 95%.
- **M4** (note giống hệt, cùng cung, cùng ngày): có giờ sinh **6,0%**; chỉ ngày sinh **100%**; cặp cùng ngày
  sinh **100%**. Mục tiêu < 1%.
- **M5** (yếu tố riêng, đếm theo spec §5: transit cá nhân và cấu hình natal là hai cờ độc lập; cặp + nhà tính
  một lần; không tính placement đơn hay salt):

  | Nhóm | Trung bình | Phân vị 10 | Phân bố |
  |---|---|---|---|
  | Chỉ ngày sinh | 0 | 0 | 0 nguồn: 60 000 note |
  | Có giờ sinh, pool 1 | 0,96 | 1 | 2 nguồn: 9 045; 1 nguồn: 147 456; 0 nguồn: 16 499 |
  | Có giờ sinh, pool 2–3 | 0,75 | 0 | |

  Mục tiêu: ≥ 1 (chỉ ngày sinh, chưa chọn mối quan tâm) và ≥ 2 (có giờ, chưa chọn).
- **M7:** bỏ giờ sinh thì 88% note đổi; sang ngày mới thì 100% note đổi ít nhất một phần.
- M3, M6, M8: chưa áp dụng (cần G0/G2).

### Tarot (247 câu hỏi được chấp nhận hiện tại, không gồm "khi nào"; đủ 6 map × 4 giọng = 5 928 bài)

- **T2** (tiêu đề trùng, gộp theo giọng):

  | Giọng | Bài | Số tiêu đề khác nhau | Tỷ lệ trùng |
  |---|---|---|---|
  | straight_warm | 1 482 | 5 | **99,66%** |
  | gentle_specific | 1 482 | 5 | **99,66%** |
  | playful_grounded | 1 482 | 5 | **99,66%** |
  | roast | 1 482 | 9 | **99,39%** |

  Mục tiêu < 10%.
- **T3** (trên 23 712 vị trí):
  - "Ví dụ:" ở **23 712/23 712** cảnh (100%);
  - "Ý chính của lá:" ở 1 976 vị trí (8,3%, rơi vào các vai không có nhánh riêng);
  - "Thử nhé:" ở 5 232 vị trí (giọng mặc định).

  Mục tiêu 0.
- **T4** (cùng lá × vai × chủ đề, mọi cặp câu hỏi khác nhau; 24 vai × 78 lá × 6 chủ đề; giọng mặc định):
  **0%** khác câu trên **9 292 608** cặp. Mục tiêu ≥ 80%.
- **T1:** chưa áp dụng, vì engine chưa có dạng câu.

### Hợp gu (50 cặp × 4 ngữ cảnh × 4 giọng = 800 bài)

Câu được trích từ đúng phần web hiển thị (`RadarContinuePage`): tiêu đề, tóm tắt, chữ ký cặp, ý nghĩa bản
đồ; trong mỗi mục có tiêu đề, thân, highlight, scene, perspectives, observation.

- **R2** (chỉ câu ở mục "hợp" và "ma sát", mỗi chỉ số 1 200 phép so):
  - đổi ngữ cảnh: **0%** câu đổi;
  - đổi giọng: **0%** câu đổi.

  Mục tiêu ≥ 50%.
- **Chẩn đoán** (không phải R2): đổi giọng trên toàn bài thì đổi 5,1% câu, chủ yếu ở mục kiểm chứng.
- **R3:** **91,3%** câu của một cặp cũng có ở cặp khác. Mục tiêu < 30%.
- **R1** (đại diện tạm: câu không trùng cặp nào khác): trung bình 5,16 câu mỗi bài, phân vị 10 là 2.
- 0 cặp ít tín hiệu.

## Phát hiện cần ghi

1. **Pool đủ điều kiện gần như luôn hẹp.** 85% ngày-hồ sơ có giờ sinh chỉ có **1** tình huống để chọn, và
   chỉ 1 ngày có ≥ 4. Bản đầu kết luận ngược lại vì đếm các issue đã thắng. Hệ quả cho G1:
   - đa dạng không thể chỉ đến từ luân phiên tình huống (top-K hiếm khi > 1); lịch chủ theo khung trong một
     tình huống là đòn bẩy chính;
   - fixture cho pool ≥ 4 phải **dựng có chủ đích**, không lấy mẫu được.
2. **Người chỉ có ngày sinh:** mọi người cùng cung nhận cùng một note; lời của Lá không đổi suốt 200 ngày.
3. **Hợp gu:** ngữ cảnh và giọng không đổi câu nào ở mục "hợp" và "ma sát". Người kia không rõ giờ được tính
   tại 12:00 giờ địa phương rồi bỏ Mặt Trăng, nhà và các góc; xử lý ở B4/G2 (spec G2 §9).
4. **Tarot:** 4 giọng chung 5 tiêu đề (Cà khịa có 9). Nghĩa của lá không phụ thuộc câu hỏi.

## Mức sàn

Theo quyết định owner (A1–A3), mức sàn là **mục tiêu**, không phải hiện trạng. Baseline này là điểm xuất
phát. Mức sàn **chưa** được đưa vào `content-matrix-baseline.json`, vì engine hiện tại sẽ không đạt và CI
sẽ đỏ. Mỗi mảng sẽ đưa mức sàn vào khi đạt (B2 cho Tarot, G1 cho Daily, B4 cho Hợp gu).
