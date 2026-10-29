# Hợp gu dễ đọc hơn: bậc có tên, ít chữ, đúng ngữ cảnh (29/10/2026)

**Trạng thái: đã làm theo lệnh của owner ngày 29/10/2026. Copy mới CHƯA được owner đọc. Phải chờ owner đọc
trước khi release.** Không merge, không deploy trong batch này.

- Nhánh: `feat/hop-gu-readable` (từ `origin/collab/integration` @ `e0d62fa`).
- Renderer: `radar-living-dossier-v1` → **`radar-readable-v2`**. Gate: `conditional-reflection-v3` →
  **`conditional-reflection-v4`**. Phân bố tham chiếu mới: **`radar-tier-ref-v1`**. Phiên bản kết quả
  vẫn là `radar-result-v2` (chỉ thêm field, nên kết quả cũ vẫn đọc được).
- Luna (tuỳ chọn): `gpt-6-luna-radar-v1` → `gpt-6-luna-radar-v2` cho bài viết lại từ renderer mới. Bài
  cũ vẫn được viết lại với nhãn cũ. Không đổi schema provider (`radar-rewrite/v1`).
- Nguồn đầu vào: phản hồi của owner và báo cáo `reports/Phương án sửa Tarot và Hợp gu.md`, Phần B (chỉ
  đọc, không sửa).

## 1. Vấn đề (đo trên 50 cặp `radar-pairs-v1` × crush / bạn bè / người yêu = 150 bài, giọng mặc định)

| Vấn đề | Đo trước |
|---|---|
| Quá dài | Trung vị **1.217 chữ** cho mọi lớp (1.002–1.365). Riêng màn mở sẵn đã 466–561 chữ |
| Điểm bị nén | Bắt sóng 47–73 (trung vị 62,5), Dễ phối hợp 40–76 (55), Lực cấn 30–75 (57). Không cặp nào tới 80 |
| Chữ "nhưng" ép buộc | **100%** tiêu đề có dạng "…; nhưng …" |
| Kicker rào đón | **94%** bài. Riêng câu "Có điểm chạm · nên xem bằng tương tác thật" chiếm 78% |
| Cặp nào cũng có điểm cấn | 100% bài có chương "Điểm dễ cấn" (khi thiếu thì vẫn có chương "chưa đủ mạnh để gọi tên") |
| Thuật ngữ | Trung bình 4,6 thuật ngữ/bài ở màn mở sẵn ("chart", "mood", "chemistry", "Radar", tên hành tinh…) |
| Lặp câu | Trung bình 2,4 câu lặp nguyên văn mỗi bài (cảnh "Cảnh dễ gặp" lặp lại câu tóm tắt) |
| Ngữ cảnh gần như không đổi | Cùng một cặp, đổi crush / bạn bè / người yêu chỉ đổi **3,5%** câu ở màn mở sẵn, 5,6% toàn bài |

## 2. Đã đổi gì

**Bậc thay cho ba con số.** Mỗi bài mở đầu bằng **một bậc có tên theo ngữ cảnh** và **một câu lý do**.

| Bậc (thứ hạng so với tham chiếu) | Crush | Bạn bè | Người yêu | Một người |
|---|---|---|---|---|
| 15% cao nhất | Dễ bắt nhịp | Rất hợp cạ | Rất ăn ý | Rất ăn ý |
| 25% kế tiếp | Dễ bắt chuyện | Hợp chuyện | Ăn ý | Ăn ý |
| 30% ở giữa | Có nhiều điều để tò mò | Bổ sung cho nhau | Bổ sung cho nhau | Bổ sung cho nhau |
| 20% kế tiếp | Cần thêm thời gian làm quen | Cần thời gian làm quen | Cần thêm thời gian hiểu nhau | Cần làm quen |
| 10% thấp nhất | Nhịp khá khác nhau | Khác nhịp, cần kiên nhẫn | Khác nhịp, cần nhiều kiên nhẫn | Khác nhịp, cần kiên nhẫn |
| Không đủ dữ kiện | Chưa đủ dữ kiện để xếp bậc | (như bên trái) | | |

- Cách xếp: `ease = coordination − 0,6 × friction` của cặp, đặt vào phân bố của **2.000 cặp tổng hợp**
  (seed cố định, 25% người kia không rõ giờ, không dùng dữ liệu người dùng,
  `uv run python -m scripts.radar_tier_reference`). Vì xếp theo thứ hạng, các bậc trải đều thay vì dồn
  ở giữa. Đây là cách báo cáo gọi là "trung thực", không phải cách "dồn vào dải 60–90 cho dễ nghe".
- **Không hiện con số (đã chọn).** Lý do: (1) spec và US-22 AC04 đang có invariant "không điểm số tổng";
  (2) báo cáo cảnh báo rằng thổi phồng điểm làm đẹp khảo sát nhưng kém trung thực (hiệu ứng Barnum);
  (3) con số chính là thứ owner thấy "khó đọc". **Đổi dễ:** cờ `SHOW_TIER_SCORE` trong
  `apps/api/app/domains/radar/reading.py` thêm `tier.score` (thứ hạng 0–100), và web đã sẵn sàng hiện
  "Hợp chuyện · 72". Bật cờ là gỡ invariant, nên cần owner quyết, bump `GATE_VERSION`, sửa một dòng test
  `test_owner_switch_adds_a_rank_number_only_when_turned_on` và chạy lại fallback approval.

**Tiêu đề** là một câu về cách hai người tương tác, chọn theo mảng hợp nhất × ngữ cảnh. Không còn "nhưng".

**Ba mảng theo ngữ cảnh**, mỗi mảng có mức *hợp / cân bằng / cần để ý / chưa rõ* và một câu lý do (kiểu
checklist "xem tuổi"):

| Ngữ cảnh | Mảng |
|---|---|
| Crush | Điểm thu hút · Cách mở lời · Nhịp tiến gần |
| Bạn bè | Nói chuyện · Chơi chung · Hỗ trợ nhau |
| Người yêu | Gắn bó · Xử lý bất đồng · Nhịp sống chung |
| Một người | Nói chuyện · Cảm xúc · Nhịp phối hợp |

**Màn mặc định ngắn:**

- *Điều trôi chảy*: mảng hợp nhất, thêm mảng "hợp" thứ hai nếu có.
- *Điều cần để ý*: **chỉ khi** một nhóm tín hiệu có friction ≥ 0,6 và lớn hơn coordination. Khoảng 40%
  cặp tham chiếu (42% cặp fixture) có đoạn này; 58–60% không có. Đoạn này gồm một tình huống tạm thời và
  một bước làm.
- *Một gợi ý*: một việc nhỏ và một câu bạn có thể hỏi người kia, thay cho việc đoán.
- **Một dòng kết cố định**, xuất hiện một lần: "Kết quả để tham khảo, cách hai bạn đối xử với nhau mới là
  điều quyết định." Thay cho kicker rào đón và disclaimer dài.

**Một lớp "Xem thêm: vì sao ra kết quả này"** (đóng sẵn):

- *Vì sao ra kết quả này?*: tối đa 5 mảng, mỗi mảng có mức và thuật ngữ chiêm tinh (ví dụ "Sao Thủy của
  bạn và Mặt Trăng của người kia, góc tam hợp"), kèm dữ kiện kỹ thuật.
- *Hai phía có thể thấy khác nhau*: không nói hộ phía kia, chỉ gợi ý hỏi.
- *Thêm vài cách thử*: các prompt biên tập theo giọng đã chọn.

**Ngôn ngữ:** không còn "chart", "contact", "mood", "flirt", "chemistry", "Radar", tên hành tinh hay tên
góc ở màn mặc định. Không câu nào nói người kia nghĩ, cảm thấy, muốn hay sẽ làm gì. Không "định mệnh",
"tri kỷ", phần trăm. Với crush, không câu nào đoán người kia có thích mình không.

**Ghi chú không rõ giờ sinh** (service): "Không rõ giờ sinh của người kia, nên Lá bỏ qua những dữ kiện cần
giờ sinh. Bài đọc ngắn hơn một chút nhưng không đoán bừa." Câu này thay câu cũ có "Moon / Rising / House",
và không còn bị nối vào dòng kết.

**Trang giới thiệu Radar** (bước 3): đổi "Ba chỉ báo giúp nhìn điểm hợp…" thành "Một bậc có tên kèm lý do,
vài mảng hợp hoặc cần để ý, và một gợi ý nhỏ để thử…", cho khớp runtime.

## 3. Số đo trước / sau (cùng 150 bài)

| Chỉ số | Trước (`radar-living-dossier-v1`) | Sau (`radar-readable-v2`) | Mục tiêu báo cáo |
|---|---|---|---|
| Chữ ở màn mặc định | 466–561 (trung vị 518) | **138–221 (trung vị 174,5)** | 250–400 (đề xuất) |
| Chữ màn mặc định + mở "Vì sao?" | n/a | **251–341 (trung vị 294)** | |
| Chữ toàn bộ các lớp | 1.002–1.365 (trung vị 1.217) | 464–638 (trung vị 555) | |
| Tiêu đề có "nhưng" | 100% | **0%** | 0 |
| Kicker rào đón | 94% | **0%** (chỉ còn dòng kết cố định) | 0 |
| Bài có đoạn cấn | 100% | **42%** (tham chiếu 40,4%) | thấp hơn rõ |
| Thuật ngữ ở màn mặc định | 4,6 / bài | **0** | 0 |
| Câu lặp trong một bài | 2,4 / bài | **0** | 0 |
| Câu đổi khi đổi ngữ cảnh (màn mặc định) | 3,5% | **60,4%** | ≥ 50% |
| Câu đổi khi đổi ngữ cảnh (mọi lớp) | 5,6% | 17,8% (lớp "Xem thêm" giống nhau giữa ngữ cảnh) | |
| Phân bố điểm / bậc | 3 điểm, mỗi điểm trong 30–76 | 50 cặp: 6 / 10 / 15 / 15 / 4 (12% / 20% / 30% / 30% / 8%); tham chiếu đúng 15 / 25 / 30 / 20 / 10% | không bậc nào quá lớn |
| US-22 AC02 ngữ cảnh (fit/friction) | 0,0 | **1,0** | ≥ 0,5 |
| US-22 AC02 giọng | 0,0 | 0,0 (chưa đổi) | ≥ 0,5 |
| US-22 AC03 trùng giữa các cặp | 0,9132 | 0,9439 | < 0,3 |

Màn mặc định nay **ngắn hơn** dải 250–400 của báo cáo. Báo cáo ghi dải này "là đề xuất, không phải chuẩn
ngành", và tự tính cả ô "Vì sao?" vào đó. Nếu tính cả "Vì sao?" (một lần bấm), bài nằm trong 251–341.
Nếu owner muốn màn đầu dài hơn, xem quyết định 3 ở mục 6.

## 4. Mẫu trước / sau

Mẫu đầy đủ (4 cặp × 3 ngữ cảnh, kèm số đo) đã được dựng bằng script tạm ngoài repo. Dưới đây là phần đại
diện.

**Trước, `radar-18` · người yêu** (rút gọn; toàn bài 1.263 chữ):

> [Dễ vào nhịp · vẫn cần nói thật]
> **Nói chuyện có thể vào rất nhanh; nhưng chemistry không tự nói hộ ý định.**
> Chỗ dễ đi cùng nằm ở cách nói và hiểu nhau: … Chỗ cần thương lượng nằm ở sức hút và cách thể hiện sự
> thích: …
> Bắt sóng 71/100 · Dễ phối hợp 73/100 · Lực cấn 62/100
> **Điểm hợp: Nói đúng nhịp là bắt được ý khá nhanh.** Điểm dễ đi cùng nhất nằm ở cách nói và hiểu nhau.
> Phần dưới chỉ ra lúc nó giúp hai người vào nhịp… Cách bạn thể hiện thích và quan tâm chạm vào cách người
> kia nghe, hiểu và trả lời… (thêm 3 chương: Điểm dễ cấn, Hai phía có thể thấy khác nhau, Đem ra đời thật,
> mỗi chương 3–5 khối)
> *Ba chỉ báo là bản đồ tương tác từ hai chart, không phải xác suất thành công…*

**Sau, cùng cặp `radar-18`, ba ngữ cảnh** (màn mặc định đầy đủ cho người yêu, rút gọn cho hai ngữ cảnh kia; 174–182 chữ):

> **Người yêu · [Rất ăn ý]** Nhiều điểm của hai bạn đi cùng chiều, rõ nhất là cách nói chuyện.
> **Hai bạn dễ nói cho nhau hiểu.**
> Gắn bó: *cần để ý*. Nhịp chủ động của hai bạn dễ lệch nhau · Xử lý bất đồng: *hợp*. Cách hai bạn nói và
> nghe dễ khớp nhau · Nhịp sống chung: *cân bằng*. Nhịp giữ hẹn, giữ lời của hai bạn cần thống nhất thêm.
> **Điều trôi chảy.** Chuyện lớn hay chuyện nhỏ, hai bạn đều dễ tìm ra cách nói cho nhau hiểu. Lúc cần bàn
> việc chung, hai bạn ít phải vòng vo.
> **Điều cần để ý.** Khi một người muốn gần gũi mà người còn lại đang mệt, dễ có cảm giác bị từ chối. Nói
> rõ "không phải lúc này, không phải không muốn" giúp cả hai nhẹ lòng.
> **Một gợi ý.** Thử làm lại một điều hai bạn từng rất thích làm cùng nhau. Thử hỏi: "Có việc gì bạn muốn
> hai đứa làm cùng nhau thêm không?"
> ▸ Xem thêm: vì sao ra kết quả này
> *Kết quả để tham khảo, cách hai bạn đối xử với nhau mới là điều quyết định.*

> **Bạn bè · [Rất hợp cạ]** … **Hai bạn có thể nói chuyện hàng giờ mà không thấy mệt.**
> Nói chuyện: *hợp* · Chơi chung: *cần để ý* · Hỗ trợ nhau: *cân bằng*
> **Điều trôi chảy.** Hai bạn bắt ý nhau nhanh và hay đùa cùng một kiểu…
> **Điều cần để ý.** Hai bạn đều có ý riêng, nên chuyện chọn chỗ đi hay việc làm chung dễ thành giành phần.
> Thay phiên nhau quyết là cách đơn giản.
> **Một gợi ý.** Lên một kế hoạch đi chơi mà mỗi người chọn một phần. Thử hỏi: "Có chỗ nào cậu muốn đi mà
> chưa đi được không?"

> **Crush · [Dễ bắt nhịp]** … **Hai bạn dễ bắt chuyện với nhau.**
> Điểm thu hút: *cần để ý* · Cách mở lời: *hợp* · Nhịp tiến gần: *cân bằng*
> **Điều trôi chảy.** Câu chuyện giữa hai bạn dễ đi từ chuyện vặt sang chuyện thật…
> **Điều cần để ý.** Sự hào hứng lúc đầu dễ làm nhịp của hai bạn lệch nhau: một người muốn tiến nhanh, một
> người muốn từ từ. Để cả hai cùng chủ động sẽ dễ chịu hơn.
> **Một gợi ý.** Rủ nhau làm một việc nhỏ cùng nhau, như đi uống nước hay cùng xem một bộ phim.

**Sau, một cặp không có đoạn cấn (`radar-00` · crush, 169 chữ):**

> **[Dễ bắt chuyện]** Hai bạn có khá nhiều điểm dễ đi cùng, nổi bật là cách nhận ra cảm xúc của nhau.
> **Hai bạn dễ cảm được tâm trạng của nhau.**
> Điểm thu hút: *cân bằng* · Cách mở lời: *cân bằng* · Nhịp tiến gần: *hợp*
> **Điều trôi chảy.** Không cần nói nhiều, hai bạn vẫn dễ bắt được không khí khi gặp nhau. Điều đó làm
> những lần gặp đầu bớt gượng. Gặp nhau, hai bạn dễ nảy ra những ý tưởng bất ngờ. Không ai phải đóng một
> vai cố định.
> **Một gợi ý.** Khi thấy không khí trầm xuống, hỏi nhẹ một câu rồi để bạn ấy tự chọn kể hay không. Thử
> hỏi: "Hôm nay của cậu thế nào?"

## 5. Đổi hợp đồng (ghi rõ từng chỗ)

1. **US-22 AC04:** bỏ "không điểm tổng" để cho phép **bậc có tên theo ngữ cảnh**, xếp theo thứ hạng. Vẫn
   giữ: không con số, không phần trăm, không "Soulmate / Challenging / định mệnh / tri kỷ", không đoán
   ý người kia.
2. **US-22 AC11 (mới):** hợp đồng dễ đọc với ngưỡng: ≤ 400 chữ ở màn mặc định; 0 "nhưng" ở tiêu đề; kicker
   = tên bậc; đoạn cấn chỉ trên ngưỡng 0,6, tỷ lệ trong (0; 0,6]; 0 thuật ngữ ở màn mặc định; 0 câu lặp;
   0 cụm cấm ở mọi lớp; không bậc nào > 40% cặp; đổi ngữ cảnh ≥ 50% câu. Gate nằm trong
   `pnpm experience:audit`, và audit này kiểm thêm việc phân bố tham chiếu khớp hằng số.
3. **Spec Radar** (`la-lanh-radar-hop-gu-spec.md` §1, §7, §8): mô tả `radar-readable-v2`. Bỏ quy tắc "Pair
   Signature mở đầu bằng một mâu thuẫn" và "bốn chương bắt buộc" cho bài mới. Ngữ cảnh nay đổi cả bậc, mảng
   và các đoạn. Invariant "không con số" giữ nguyên, kèm cờ owner.
4. **R04** (khoảng điểm): đánh dấu *thay thế*, vì bài mới không còn ba chỉ báo. Ý tưởng phân bố tham chiếu
   được dùng lại.
5. **Experience audit:** viết lại cho cấu trúc mới (prompt "Thử ngoài đời" nay ở section `practice`, gợi ý
   theo ngữ cảnh ở `check`) và thêm lớp đo trên 50 cặp.
6. **Content matrix audit:** kiểm độ phủ của bảng mới (`HEADLINES`, `FIT_COPY`, `TENSION_COPY`,
   `SUGGESTIONS`, `FACTOR_COPY`, `AREAS`, `TIER_LABELS`) thay cho `SCENE_COPY` / `CONTEXT_CHECKS`. Baseline
   vẫn 8 theme, 4 ngữ cảnh.
7. **Luna rewrite:** section `friction` nay tuỳ chọn. Provider vẫn đòi ít nhất 1 friction, nên bài không có
   đoạn cấn gửi một nghĩa cố định "không có điểm cần để ý". Bản viết lại vẫn qua gate cấm, rồi bị **bỏ,
   không bao giờ hiện**. Payload vẫn không có dữ kiện chiêm tinh: band thô lấy từ
   `metadata.signal_bands`, và lớp "Vì sao?" không được gửi đi. Projector nhận cả renderer cũ lẫn mới.
8. **Test được sửa vì hợp đồng đổi:** `tests/radar/test_reading.py` (viết lại),
   `tests/radar/test_flow.py::_assert_dossier_payload`, `test_rewrite_payload_chart_free` (phiên bản), và
   `tests/content_rewrite/test_radar_rewrite.py`. Các ca hồi quy polarity S3 (Codex #72) chạy trên đúng câu
   chữ cũ, được đặt vào fit body; thêm 3 ca cho friction tuỳ chọn. Thêm test web
   `RadarReadableView.test.tsx`. Test bài cũ `RadarContinuePage.test.tsx` giữ nguyên và vẫn qua, chứng tỏ
   bài đã lưu vẫn render.
9. **Fallback approval:** đã refresh bảng radar (renderer, gate, bảng mới) và thêm evidence
   `radar_readable_v2` trỏ về tài liệu này. `approved_release` giữ nguyên (chưa release).

## 6. Owner cần quyết

1. **Đọc toàn bộ copy mới** trong `apps/api/app/domains/radar/reading.py`: `TIER_LABELS`, `TIER_REASONS`,
   `HEADLINES`, `FIT_COPY`, `TENSION_COPY`, `SUGGESTIONS`, `FACTOR_COPY`, `AREAS`, `CLOSING_LINE`,
   `LOW_SIGNAL_*`. Có 32 tiêu đề, 32 đoạn hợp, 32 đoạn cấn, 32 cặp gợi ý và câu hỏi, 24 câu mảng. **Chặn
   release.**
2. **Hiện số hay không** (quyết định 6 của báo cáo): hiện tại không hiện; bật bằng `SHOW_TIER_SCORE`.
3. **Độ dài màn mặc định:** đang ~140–220 chữ, dưới dải 250–400 của báo cáo. Có thể giữ, hoặc đưa "Hai
   phía" lên màn đầu, hoặc viết mỗi đoạn 3 câu.
4. **Ngưỡng đoạn cấn** (quyết định 9): `TENSION_THRESHOLD = 0,6`, cho khoảng 40% cặp có đoạn cấn. Hạ xuống
   0,55 cho khoảng 50%; tăng lên 0,7 cho khoảng 19%.
5. **Tỷ lệ bậc:** 15 / 25 / 30 / 20 / 10% (`TIER_BANDS`), và tên từng bậc theo ngữ cảnh (quyết định 8). Có
   dùng "Tri kỷ" cho bạn bè không? Hiện không dùng vì gần nghĩa "soulmate" mà AC04 cấm.
6. **Dòng kết cố định** (quyết định 10): "Kết quả để tham khảo, cách hai bạn đối xử với nhau mới là điều
   quyết định."
7. **Giọng đọc** (US-22 AC02 giọng = 0): giọng hiện chỉ đổi lớp "Thêm vài cách thử". Có muốn giọng đổi cả
   màn mặc định không? Nếu có, phải viết thêm 4× copy.
8. Owner có thể chỉnh thêm `GOOD_MIN_COORDINATION = 0,45` (ngưỡng "hợp" của mảng) và
   `EASE_FRICTION_WEIGHT = 0,6`.

## 7. Bảo mật và quyền riêng tư (AGENTS.md)

- **Nguồn đã kiểm:** `AGENTS.md`; US-22; spec Radar; R04; báo cáo Phần B; `docs/legal/store-privacy-data-map.md`;
  `docs/legal/privacy-security-flow-notes.md`; code `radar/{reading,rewrite,service}.py`,
  `content_rewrite/registry.py`, `infrastructure/generation/{schemas,privacy}.py`; `scripts/fallback_approval.py`.
- **Không đổi:** endpoint, auth/session, CSRF, link mời / receipt (no-store, no-referrer, noindex), TTL
  (24 giờ / 30 ngày), mã hoá kết quả (AES-GCM theo ngữ cảnh), xoá / rút / thu hồi, migration DB.
- **Dữ liệu:** không thu thêm field nào; không gửi thêm gì cho bên thứ ba. Kết quả lưu có thêm bậc (key và
  tên), mức của 3 mảng và `signal_bands` (low/medium/high). Đây đều là dữ liệu cá nhân suy ra từ cùng hai
  lá số, ít chi tiết hơn ba con số cũ, nằm trong cùng ciphertext và hết hạn cùng kết quả. Store data map và
  privacy notes đã cập nhật mô tả; khai báo Apple / Google không đổi (cùng loại dữ liệu, mục đích, người
  nhận).
- **Payload Luna:** test `test_rewrite_payload_chart_free` (12 cặp × 4 ngữ cảnh) vẫn qua: không tên hành
  tinh / góc / nhà, không ID, không ngày sinh. Bản friction "không có" bị bỏ sau gate.
- **Không rõ giờ (AC07):** `test_unknown_time_contacts` vẫn qua: không trích Mặt Trăng của B, không trích
  contact chỉ đúng ở 12 giờ trưa giả định.
- **Đoán ý / thao túng:** test quét mọi bảng copy tìm cụm cấm. Audit quét mọi lớp hiển thị trên 200 bài:
  0 lần trúng.
- **Chưa làm lại:** luật Việt Nam (Luật 91/2025, Nghị định 356/2025) và chính sách Apple / Google chưa
  đọc lại từ nguồn chính thức trong batch này, vì thay đổi không thêm dữ liệu thu thập, chia sẻ hay mục
  đích. Rủi ro mở cũ về "check kín" (nhập dữ liệu người thứ ba) không đổi.

## 8. Rủi ro còn mở, AC / DoD chưa xong

- **Owner chưa đọc copy:** chặn release (AC10: owner duyệt; workbook Excel cho copy mới chưa làm).
- **US-22 AC01** (câu riêng theo contact, catalog R03), **AC02 giọng**, **AC03** (trùng 0,94) vẫn đỏ. Gate
  `audit_radar_us22` vẫn là strict xfail.
- **Thẩm định giao diện:** chỉ có unit test (vitest) và typecheck / lint. Chưa xem trên trình duyệt hay
  điện thoại thật; cần QA thị giác ở 375px trước release.
- **Ô mảng có thể nhắc lại ý tiêu đề** cho mảng hợp nhất (ví dụ tiêu đề "dễ cảm được tâm trạng của nhau"
  và mảng "Hai bạn dễ nhận ra cảm xúc của nhau"). Không trùng nguyên văn, nhưng owner nên đọc.
- **Lớp "Xem thêm" giống nhau giữa các ngữ cảnh**, chỉ màn mặc định đổi.
- `pnpm check` đầy đủ chưa chạy (theo quy tắc workspace). Các lệnh đã chạy được liệt kê trong handoff.
- DoD "Codex APPROVE @ SHA; release theo runbook" chưa làm.
