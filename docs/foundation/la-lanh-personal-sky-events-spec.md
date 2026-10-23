# Spec sự kiện bầu trời cá nhân (G2, P0)

Phiên bản: `event-spec/v1` (16/10/2026). Nguồn: plan §14.4 (Codex APPROVE @ 8574d72). Áp cho note ngày
(US-21), Hợp gu khi người kia không rõ giờ (US-22), và chương lịch cá nhân. Tham chiếu tính toán: Swiss
Ephemeris (`swe_calc_ut`, vị trí và tốc độ), https://www.astro.com/swisseph/swephprg.htm.

## 1. Miền ngày sinh

- **Có giờ và nơi sinh:** dùng thời điểm sinh như hiện nay (`calculate_chart`).
- **Chỉ có ngày sinh:** khoảng `I = [ngày 00:00 UTC − 14h, ngày 23:59:59 UTC + 12h]`, khoảng 50 giờ, cùng
  cách `calculate_date_only_sun` (`astro/engine.py:583-606`) đang dùng cho Mặt Trời. Không tự đặt giờ.

## 2. Miền longitude của từng hành tinh

- Áp cho Mặt Trời, Sao Thuỷ, Sao Kim, Sao Hoả, Sao Mộc, Sao Thổ, Thiên Vương, Hải Vương, Diêm Vương.
  **Không** áp cho Mặt Trăng, cung mọc, đỉnh nhà hay nhà.
- `[λmin, λmax]` = cực trị của longitude trên I. Tìm bằng cách:
  1. tính ở hai đầu I;
  2. tìm mọi điểm đứng bên trong I (tốc độ đổi dấu) bằng chia đôi trên tốc độ, dung sai 1 phút;
  3. lấy cực trị trong các điểm trên.
- Vòng 0°/360° được xử lý bằng cách mở khoảng qua 0 (biểu diễn `[λmin, λmax + 360]` khi cần).
- **Cung:** nếu cả miền nằm trong một cung thì cung đó là chắc. Nếu không thì ghi `candidates` và không
  dùng cung để kết luận.
- Dung sai: miền phải chứa vị trí thật với sai số ≤ 0,01°. Có test so với lấy mẫu dày mỗi 10 phút.

## 2b. Mốc thời gian quan sát (`observed_at`)

- **Note ngày:** dùng đúng `observed_at` của projection hiện hành. `_scope_time` lấy `local_date` theo
  `MVP_TIMEZONE`, rồi đặt `observed_at = local_date 12:00 UTC` (`DAILY_OBSERVED_HOUR_UTC = 12`,
  `readings/application.py:65-66,686-700`). Mốc này **không** phải thời điểm request. Hai request lúc
  01:00 UTC và 13:00 UTC cùng `local_date` cho cùng `observed_at`.
- Mọi phép tính của G2 cho note ngày (orb, pha, ưu tiên chương, kiểm cửa sổ, đếm ngày) dùng `observed_at`
  này.
- Đổi chính sách mốc là thay đổi riêng: bump `event_spec_version` và `catalog_version`, có AC riêng. Không
  đổi ngầm.
- **Hợp gu:** natal–natal (§9), không có `observed_at` transit.

## 3. Orb dạng khoảng

- Với transit T (vị trí tại `observed_at`), điểm natal có miền `[λmin, λmax]` và góc chiếu A có ngưỡng orb
  θ (ngưỡng hiện hành của engine):
  - `orb_min` và `orb_max` = cực tiểu và cực đại của |khoảng cách góc tới A| khi λ chạy trên miền.
  - **Chắc trong orb:** `orb_max ≤ θ`. **Có thể:** `orb_min ≤ θ < orb_max`. **Ngoài:** `orb_min > θ`.
- Có giờ sinh thì miền là một điểm, nên `orb_min = orb_max`.

## 4. Pha

- Pha tại một thời điểm (`approaching`, `exact`, `separating`) tính như `_transit_phase` hiện có
  (`engine.py:609-619`: exact khi orb ≤ 0,2°, so với vị trí sau một giờ).
- **Pha chắc:** tính pha ở hai đầu miền và ở mọi cực trị bên trong; nếu tất cả giống nhau thì pha đó chắc.
  Nếu không thì `phase = None`, và bài **không** nói pha.
- **Ví dụ bắt buộc thành test** (probe của Codex, dữ liệu tổng hợp 1990-03-15): Sao Thuỷ natal
  349,157941°…353,138133°, cùng cung Song Ngư. Transit lúc 2026-02-21 12:00 UTC cho orb 1,558642° và
  2,421549°, pha separating và approaching. Kỳ vọng:
  - `phase = None`, nên bài **không** có câu nói về pha;
  - orb ở mức "chắc trong orb" (cả hai ≤ 2,5°);
  - `observed_at` nằm trong cửa sổ chắc, nên **được** hiện "Ngày N" (đếm từ `t_s`, §5).

  Chắc về orb không đồng nghĩa với chắc về pha. Hai điều kiện độc lập.

## 5. Chương (lượt đi qua)

- **ID lượt:** `pass_id = H(T, điểm natal, A, thứ tự lượt k, event_spec_version)`. k là thứ tự theo thời
  gian các lần vào orb trong một chu kỳ chuyển động. Có nhiều lượt khi nghịch hành.
- **Cửa sổ chắc** `[t_s, t_e]`: khoảng thời gian `orb_max ≤ θ`. **Cửa sổ có thể** `[t'_s, t'_e]`: khoảng
  thời gian `orb_min ≤ θ`. Cửa sổ chắc luôn nằm trong cửa sổ có thể.
- **Tìm biên:** bước ≤ 6 giờ (không quá khoảng thời gian thay đổi orb 0,5° theo tốc độ hiện tại), chia đôi
  tới dung sai 1 phút. Phát hiện điểm đứng của T trong cửa sổ.
- **Predicate duy nhất cho "Ngày N"** (dùng chung cho spec, US-21 AC08/AC09 và test):
  `day_allowed = (t_s ≤ observed_at ≤ t_e)`, so **timestamp với timestamp**.
  - Khi đúng: `N = local_date(observed_at) − local_date(t_s) + 1`, cả hai ngày lấy theo `MVP_TIMEZONE`.
  - Không phụ thuộc pha.
- **Predicate cho câu nói về pha:** `phase_allowed = (phase ≠ None)` (pha chắc, §4). Độc lập với
  `day_allowed`.
- **Nhịp:** chia `[t_s, t_e]` thành ba đoạn thời gian bằng nhau: nhận ra → thử → nhìn lại. Nhịp lấy theo
  đoạn chứa `observed_at`; chỉ có khi `day_allowed`. Ngoài cửa sổ chắc nhưng trong cửa sổ có thể thì không
  có nhịp và không có số ngày; chữ hiển thị là "đợt này" hoặc bỏ chi tiết.
- **Ưu tiên khi nhiều chương:** orb chắc nhỏ hơn trước, rồi điểm natal cá nhân (Mặt Trời, Sao Thuỷ, Sao
  Kim, Sao Hoả), rồi hành tinh transit chậm hơn. Tối đa một chương nổi trên Home.
- Tất cả tính lại được từ ephemeris, **không lưu lịch sử**. Bản đọc đã tạo đóng băng trước `plan_hash`.

## 6. Lịch cá nhân

| Sự kiện | Có giờ sinh | Chỉ có ngày sinh |
|---|---|---|
| Sinh nhật (Mặt Trời trở về) | Thời điểm chính xác | Ngày theo miền; nếu miền Mặt Trời trải qua ranh giới ngày thì nói "quanh ngày …" |
| Sao Mộc, Sao Thổ trở về | Lượt theo §5 | Lượt theo §5 trên miền |
| Transit chậm (Mộc → Diêm Vương) tới hành tinh cá nhân | §5 | §5, chỉ cửa sổ chắc mới có số ngày |
| Sao Thuỷ nghịch hành chạm Sao Thuỷ natal | §5 | §5 trên miền Sao Thuỷ |

## 7. Chữ hiển thị

- Chỉ dùng: tên hành tinh, góc chiếu bằng lời đời thường, pha khi chắc, "Ngày N của đợt …" khi chắc.
- Nhịp "nhìn lại" chỉ mời tự soi; không khẳng định người đọc đã làm gì.
- Người chỉ có ngày sinh luôn thấy dòng "bản đọc từ ngày sinh".
- Hình học thiên văn là căn cứ chọn nội dung, không phải bằng chứng nhân quả.

## 8. Test bắt buộc

1. Cùng cung, khác orb và pha (ví dụ ở §4).
2. Hành tinh đổi cung trong I.
3. Vòng 0°/360°.
4. Điểm đứng nằm trong I.
5. Nhiều lượt do nghịch hành: `pass_id` khác nhau, số ngày đếm lại từ đầu mỗi lượt.
6. Ranh giới ngày ở `MVP_TIMEZONE`; `observed_at` không đổi theo giờ request (01:00 và 13:00 UTC cùng
   `local_date`).
9. `day_allowed` đúng nhưng `phase = None` (ví dụ ở §4): có "Ngày N", không có câu nói về pha.
7. So miền với lấy mẫu dày mỗi 10 phút (≤ 0,01°).
8. Tất định: cùng đầu vào và `event_spec_version` cho cùng `pass_id`, cửa sổ và số ngày.

## 9. Hợp gu: natal–natal

- Khi một hoặc cả hai người chỉ có ngày sinh, mỗi điểm natal có miền theo §2. Orb của contact là khoảng
  trên **tích hai miền**: `orb_min`/`orb_max` khi cả hai longitude chạy trên miền của mình.
- Ngưỡng orb và phiên bản lấy từ bảng **synastry** của engine (`calculate_synastry`), **không** dùng ngưỡng
  transit.
- Contact chỉ dùng khi chắc trong orb (`orb_max ≤ θ_synastry`). Synastry không có pha, chương hay
  `observed_at`.
- Không dùng Mặt Trăng, cung mọc hay nhà của người không rõ giờ.
- **Cài đặt (R02, 22/10/2026):** `NatalChartEngine.longitude_domains` + `orb_bounds` (`astro/engine.py`,
  `astro/aspects.py`). Radar luôn có nơi sinh, và chart không rõ giờ được tính lúc 12:00 giờ địa phương, nên
  miền là trưa ± 14 giờ (±12 giờ của ngày dân sự cộng tối đa 2 giờ đổi múi trong ngày), hẹp hơn khoảng 50 giờ
  của §1 cho trường hợp không có nơi sinh nhưng luôn chứa thời điểm thật. Orb và strength báo ra là giá trị
  xấu nhất trên miền. Composite midpoint dùng cùng miền: bỏ điểm khi trung điểm cung ngắn có thể lật 180°, và
  bỏ góc chiếu nào không chắc trong orb (cận độc lập, nên chỉ bỏ bớt, không thêm). Chart có giờ không đổi.
