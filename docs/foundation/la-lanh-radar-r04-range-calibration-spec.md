# Hợp gu R04 — khoảng điểm và calibration (spec chờ owner duyệt)

Trạng thái: **thay thế 29/10/2026** bởi bậc có tên xếp theo thứ hạng (`radar-readable-v2`,
`radar-tier-ref-v1`, xem `docs/reviews/2026-10-29-hop-gu-readable.md`): bài mới không còn hiện ba chỉ
báo 0–100 nên khoảng điểm không cần nữa. Phần phân bố tham chiếu và phân vị (§4) được dùng lại cho bậc.
Bản gốc: **đề xuất, chưa triển khai**. Viết 22/10/2026 cho audit R04. Không đổi API, UI, version hay kết quả đã
lưu cho tới khi owner duyệt spec này; sau đó mới làm PR riêng có test và adapter cho bài cũ.

## 1. Hiện trạng (đo trên `c3fab33`, 50 cặp tổng hợp `radar-pairs-v1`, ngữ cảnh crush)

| Chỉ báo | min | p10 | trung vị | p90 | max | ≥ 90 |
|---|---|---|---|---|---|---|
| Bắt sóng (resonance) | 51 | 57 | 63 | 71 | 74 | 0 |
| Dễ phối hợp (coordination) | 42 | 50 | 58 | 65 | 76 | 0 |
| Lực cấn (friction) | 30 | 47 | 58,5 | 71 | 75 | 0 |

- Công thức (`radar/reading.py` `_index`): trung bình có trọng số của tối đa 6 contact mạnh nhất theo kênh, rồi
  `18 + 78 × trung bình`, kẹp vào `[8, 96]`, làm tròn thành **một số nguyên**.
- Hệ quả: số bị nén quanh 45–75 vì trung bình của strength (0–1) × trọng số aspect hiếm khi gần 1. Một số nguyên
  trông chính xác hơn mức bằng chứng cho phép, và không có cách nói "chưa chắc". Cặp mạnh nhất không bao giờ tới
  90 dù owner muốn khả năng đó (quyết định 19/10).

## 2. Mục tiêu và không mục tiêu

Mục tiêu:
1. Giữ **ba chỉ báo độc lập**; mỗi chỉ báo hiện một **khoảng** `[thấp, cao]` thay vì một số.
2. Độ rộng khoảng phản ánh độ chắc của bằng chứng: ít contact, contact yếu hoặc không rõ giờ sinh → khoảng rộng hơn.
3. Calibration theo phân bố tham chiếu, để vị trí tương đối có nghĩa: cặp thuộc nhóm mạnh nhất của tham chiếu có
   thể tới 90–100 **vì dữ liệu của họ**, không phải vì cộng thêm.
4. Ít tín hiệu thì nói thật: không hiện số.

Không mục tiêu (giữ nguyên từ US-22 AC04 và audit):
- Không điểm tổng, không cộng/trung bình ba chỉ báo, không "% hợp", không xác suất thành công.
- Không ép số lên 100 cho vui mắt: không làm tròn theo bội số (5, 10) và không kéo biên về 0/100. Chính sách biên duy
  nhất là **làm tròn ra ngoài tới số nguyên gần nhất** (mục 5): khoảng hiển thị luôn chứa khoảng chưa làm tròn, nên
  `100` chỉ hiện khi `high_raw > 99` và `0` chỉ khi `low_raw < 1`.
- Không đổi kết quả đã lưu (frozen); không đọc lại bằng công thức mới.

## 3. Định nghĩa

Với mỗi kênh `c ∈ {resonance, coordination, friction}`:

- `S_c` = tập contact được chọn (như hiện tại: tối đa 6 contact mạnh nhất theo kênh, đã qua lọc cá nhân hoá và, nếu
  không rõ giờ, chỉ contact chắc trên miền ngày sinh — R02).
- `raw_c` = trung bình có trọng số hiện có (trước bước `18 + 78×`), trong `[0, 1]`.
- `n_c` = số contact trong `S_c`; `spread_c` = độ lệch chuẩn của đóng góp từng contact.
- `u` = cờ không chắc giờ sinh (`time_precision = unknown` ở một trong hai người).

## 4. Calibration

1. **Phân bố tham chiếu** cố định, có version (`radar-calibration-ref-v1`): 2.000 cặp tổng hợp, ngày sinh rải đều
   1960–2007, giờ đều trong ngày, nơi sinh trong danh sách địa điểm có sẵn, 25% không rõ giờ. Sinh từ seed cố định,
   lưu dưới dạng các phân vị của `raw_c` (không lưu cặp). Không dùng dữ liệu người dùng.
2. **Ánh xạ đơn điệu** `cal_c(raw)` = tuyến tính từng đoạn qua các điểm neo phân vị của tham chiếu:

   | Phân vị tham chiếu | p5 | p25 | p50 | p75 | p90 | p97 | p99,5 |
   |---|---|---|---|---|---|---|---|
   | Giá trị hiển thị | 20 | 40 | 55 | 70 | 82 | 90 | 97 |

   Dưới p5: nối tuyến tính từ `(min tham chiếu, 10)` tới neo p5; trên p99,5: nối tuyến tính từ neo p99,5 tới
   `(max tham chiếu, 100)`; ngoài `[min, max]` của tham chiếu thì kẹp ở 10 và 100. Đơn điệu không giảm, nên thứ tự
   giữa các cặp không đổi. Bảng neo là đề xuất; owner chốt lại khi xem phân bố thật của tham chiếu.
   - **Phân vị:** nội suy tuyến tính giữa các thống kê thứ tự (phương pháp "linear", Hyndman–Fan loại 7) trên
     2.000 giá trị, tính một lần lúc sinh tham chiếu và lưu kèm version.
   - **Ties:** cùng `raw` ⇒ cùng giá trị; nếu hai neo liền nhau có cùng `raw` (phân bố có bậc), đoạn đó lấy giá trị
     của neo cao hơn để hàm vẫn là hàm, đơn điệu và tái lập.
3. Lực cấn dùng cùng cơ chế với tham chiếu của chính nó. Số cao nghĩa là "dễ cấn hơn", không phải "tệ hơn"; copy
   giữ nguyên tinh thần hiện tại.

## 5. Khoảng

- Tâm: `m = cal_c(raw_c)`.
- Nửa độ rộng: `w = 4 + 10/√n_c + 25·spread_c + (6 nếu u)`, kẹp `[5, 20]`.
- Giá trị chưa làm tròn: `low_raw = max(0, m − w)`, `high_raw = min(100, m + w)`. Implementation **giữ hai giá trị này**
  (metadata kiểm thử) để test kiểm được biên thật, không bị phép kẹp che đi.
- Khoảng hiển thị: số nguyên làm tròn **ra ngoài**, không có quy tắc biên nào khác: `low = floor(low_raw)`,
  `high = ceil(high_raw)`. Hệ quả: `[low, high]` luôn chứa `[low_raw, high_raw]` và rộng hơn tối đa 1 đơn vị mỗi đầu;
  `high = 100` khi và chỉ khi `high_raw > 99` (ví dụ `99,000001 → 100`, `99 → 99`); `low = 0` khi và chỉ khi
  `low_raw < 1`. Đây là làm tròn ra ngoài một bước, không phải kéo lên biên. (Bản trước làm tròn bội số 5 có thể đẩy
  95,08 lên 100, trái AC3; đã bỏ.)
- `n_c < 2` hoặc cặp low-signal (`_motifs` rỗng): **không có khoảng**, giữ câu "Chưa đủ tín hiệu riêng…" hiện có.
- Ví dụ minh hoạ (không phải dữ liệu thật): `raw` ở p92, `n = 5`, `spread = 0,1`, có giờ → `m ≈ 84`, `w ≈ 10,97`
  → `low_raw ≈ 73,03`, `high_raw ≈ 94,97` → hiện `73–95`.
- Phản ví dụ của review (Codex #64): `m = 82`, `n = 6`, `spread = 0,2`, có giờ → `w = 13,0825` → `high_raw = 95,0825`
  → hiện `high = 96`, không phải 100.

## 6. Hợp đồng dữ liệu và lifecycle (làm sau khi duyệt)

- API: mỗi phần tử `compatibility_map` thêm `range: {low, high} | null` và `calibration_version`; giữ `value` cho bài
  cũ. UI hiện khoảng khi `range` có mặt, ngược lại hiện như cũ.
- Version: bump `RENDERER_VERSION`/`GATE_VERSION` của Radar và ghi `calibration_version` vào metadata kết quả.
- Bài đã lưu: không tính lại; adapter hiển thị `value` cũ như hiện tại cho tới khi hết hạn (24 giờ / 30 ngày).
- Không đổi dữ liệu thu thập; không lưu thêm gì của người kia.

## 7. Tiêu chí nghiệm thu (cho PR triển khai)

1. Đơn điệu: với `n_c`, `spread_c`, `u` giữ cố định, `raw` tăng ⇒ tâm, `low_raw` và `high_raw` không giảm (test thuộc
   tính trên lưới `raw`). Không khẳng định đơn điệu của cả khoảng khi `spread` hoặc `n` cũng đổi.
2. Tái lập: cùng bundle ⇒ cùng khoảng; phân vị tham chiếu sinh lại từ seed khớp bản đã lưu.
3. Trên tham chiếu: cặp ở top 2,5% có `high ≥ 90`; trung vị nằm quanh 50–60. `high = 100` khi và chỉ khi
   `high_raw > 99`, `low = 0` khi và chỉ khi `low_raw < 1`, đúng theo `floor`/`ceil` ở mục 5 (test giữ giá trị chưa
   làm tròn, gồm phản ví dụ `m=82, n=6, spread=0,2, u=false` ⇒ `high = 96`, và biên `high_raw = 99,000001 ⇒ 100`,
   `high_raw = 99 ⇒ 99`).
4. Độ rộng: không rõ giờ ⇒ khoảng không hẹp hơn cùng cặp có giờ; `n_c` giảm ⇒ khoảng không hẹp hơn.
5. Low-signal và `n_c < 2` ⇒ `range = null` và câu trung thực hiện có.
6. Không có trường nào cộng ba chỉ báo; copy không có "%", "điểm hợp", "xác suất".
7. Bài cũ hiển thị không đổi (golden test trên kết quả đã lưu).

## 8. Owner cần quyết

- Duyệt cơ chế khoảng (thay số nguyên) và cách hiển thị: "70–95" hay thanh khoảng.
- Chốt bảng neo §4.2 (đặc biệt p97 → 90 và p99,5 → 97) sau khi xem phân bố tham chiếu.
- Chốt công thức độ rộng §5 hoặc yêu cầu đơn giản hơn (ví dụ cố định ±10, ±15 khi không rõ giờ).
- Copy cho dòng giải thích khoảng (một câu, sẽ đưa vào workbook để duyệt).
