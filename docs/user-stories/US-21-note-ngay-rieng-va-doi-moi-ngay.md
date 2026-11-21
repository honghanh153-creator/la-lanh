# US-21 — Note ngày riêng cho từng người và đổi mỗi ngày

> Nguồn: kế hoạch `docs/plans/2026-10-16-personalisation-variety-plan.md` (§4, §14; quyết định owner §8:
> A2 với A1 sớm, bản triệt để). Spec liên quan: `la-lanh-content-grammar-spec.md`,
> `la-lanh-personal-sky-events-spec.md`, `la-lanh-variety-measurement-spec.md`.

## User story

Là người mở Lá Lành mỗi ngày, kể cả khi chỉ biết ngày sinh, tôi muốn note hôm nay khác hôm qua, nói về bầu
trời của chính tôi, và nối tiếp được với những ngày trước, nhưng không bịa điều mà dữ liệu của tôi không
cho phép.

## Phạm vi

**Bao gồm:**

- B3-1a (A1): seed, lịch, top-K.
- G1: note trên ngữ pháp nội dung. Gồm pool cho người chỉ có ngày sinh, cân lại transit, 5 tình huống
  mới, hành động theo lens, khung "Vì sao hôm nay?".
- G2: lịch cá nhân từ lá số và mạch nhiều ngày.
- F: "điều bạn đang quan tâm", **chỉ sau khi rà luật** và có copy consent.

**Không bao gồm:** mood và phản hồi dùng để chỉnh note (chặng 2, B3-3); Luna (chặng 3).

## Định nghĩa dùng trong AC

- **Ngày lịch:** ngày dân sự theo `MVP_TIMEZONE = "Asia/Ho_Chi_Minh"`, cùng cách note hiện xác định
  `local_date` (`readings/application.py:65,693-696`). `day_index = local_date − 2026-01-01`, tính theo
  ngày. Nếu sau này đổi sang múi giờ của người dùng thì phải bump `catalog_version` và ghi rõ trong
  release.
- **Hai ngày lịch liên tiếp:** `note_date` D và D+1 của **cùng khung**, cùng `catalog_version` và cùng
  biến thể lịch. Mở lại nhiều lần trong cùng một ngày, hay hai request HTTP, **không** phải hai ngày liên
  tiếp.
- **Replay:** mở lại cùng `(owner_scope, note_date, catalog_version, manifest)` trả **đúng** bản đã tạo,
  kể cả sau cache miss, restart hay đổi giọng. Đổi giọng chỉ tra ánh xạ Cà khịa theo mã tổ hợp.
- **Ngoại lệ:** bản đọc có `variety_exception` (gate an toàn từ chối hoặc manifest hỏng/thiếu) phục vụ kho nền
  ở đúng phiên bản đã duyệt trong `fallback-approval.json`.
  Cặp ngày có ngoại lệ bị **loại khỏi** cam kết (a)/(b) và **báo riêng**, không bao giờ tính là đạt.

## Acceptance Criteria

### Chọn nội dung (A1 + ngữ pháp)

- **AC01:** Seed = `HMAC(K[v], owner_scope ‖ "daily" ‖ catalog_version)`, không chứa ngày. Vị trí
  `p = (day_index + offset) mod L` dùng chung cho mọi khung của một bài.
- **AC02:** Với hai ngày lịch liên tiếp không có ngoại lệ, mọi ô bắt buộc đổi của từng khung đều khác nhau.
  Đúng cả khi đổi bucket và ở biên lịch L−1 → 0. *(Cam kết (a))*
- **AC03:** Cùng một câu ghép, sau chuẩn hoá, không được phục vụ lại cho cùng người trong L ngày (L ≥ 90),
  không tính ngày ngoại lệ. *(Cam kết (b))*
- **AC04:** Replay giữ nguyên (theo định nghĩa trên). Bản đã lưu hoặc chia sẻ giữ nguyên snapshot. Đổi
  khoá `K[v+1]` chỉ áp cho ngày mới.
- **AC05:** Tình huống chọn từ top-K đã sắp xếp ổn định, theo `day_index mod K`. Không quá 2 ngày liền
  cùng tình huống khi pool có ít nhất 2 phần tử. Pool 1 phần tử thì tình huống đứng yên và các ô vẫn đổi.
  *Đối chiếu với note ngày 24 giờ, owner quyết 2026-10-21 (sửa theo review PR #39):* note D−1/D−2
  thường đã bị ẩn hoặc xoá, và owner không chấp nhận best effort hay lưu thêm lịch sử. Guard không đọc
  lịch sử nữa; nó chỉ dựa vào lá số và ngày, với lookback cố định:
  - **Ngày lẻ** (`day_index` lẻ): đổi sang lựa chọn kế tiếp khi tình huống danh nghĩa trùng tình huống
    thực tế của ngày chẵn hôm trước.
  - **Ngày chẵn:** đổi khi ngày lẻ hôm trước có pool 1 phần tử (không đổi được) và hai tình huống danh
    nghĩa trùng nhau.
  - Mọi đầu vào được tính lại bằng đúng phép chọn khi phục vụ (transit ngày đó, hạt giống rotation, nhánh
    dự phòng natal); pool 1 phần tử được nhận ra bằng cách yêu cầu phép chọn thật đổi khỏi nó. Ngày chẵn
    tính thêm 1 ngày, ngày lẻ 2 ngày. Không lưu gì, không gửi gì. Plan đã đóng băng replay nguyên (AC04);
    ngày bị đổi không dịch vị trí danh nghĩa của ngày sau (AC06).
  - **Bảo đảm:** 3 ngày liền cùng tình huống chỉ còn xảy ra khi chính ngày thứ ba có pool 1 phần tử (ngoại
    lệ của AC05). Cặp (chẵn, lẻ) luôn khác nhau trừ khi ngày lẻ có pool 1; ngày chẵn sau ngày lẻ như vậy
    sẽ đổi, trừ khi nó cũng có pool 1.
  - **Bằng chứng tổng hợp:** 100 lá số × 120 ngày không có lịch sử (12.000 ngày): 965 lần guard đổi tình
    huống, 769 lần pool đổi ngay sau đó, 46 lần 3 ngày liền và cả 46 đều có pool 1 ở ngày thứ ba. Phản ví dụ
    của Codex (lá số 1993-02-08, 22–24/4/2027) không còn lặp. Quy tắc "trùng trên 60% thì đổi góc viết":
    hai ngày liền kề trùng tối đa 40% trên 5 trục (tình huống, tiêu đề, cảnh, việc nhỏ, transit).
  - **Giới hạn:** phép tính dùng góc nhìn (lens) hiện tại và catalog hiện hành; đổi lens, đổi lá số hoặc
    đổi catalog là một chuỗi mới.
- **AC05 (mới, từ ngày bật `daily_topic_schedule_from`; plan `docs/plans/2026-11-21-daily-topic-anti-repeat.md`, #841, #855):**
  Tình huống của ngày D lấy trong pool xếp hạng của ngày D, tối đa 6 tình huống đủ điều kiện. Chọn tình huống đầu tiên
  theo thứ tự xoay cố định riêng của người đó (bắt đầu từ vị trí của ngày) mà người đó **chưa gặp trong 6 ngày trước**.
  Nếu không có, chọn tình huống gặp lâu nhất. "Đã gặp" là kết quả của chính phép chọn này ở các ngày trước trong khối
  12 ngày của người đó, **tính lại** từ lá số, transit từng ngày và seed. Không đọc lịch sử, không lưu, không gửi gì
  (giữ quyết định owner 21.10). Mỗi khối bắt đầu rỗng, nên lịch sử khớp tuyệt đối với cái đã phục vụ. Pool không đổi
  (giờ gần đúng, chỉ có ngày sinh) xoay đều theo ngày như AC05 cũ. Người chỉ có ngày sinh đếm lượt xuất hiện bằng
  `day_index // cỡ pool` (toàn cục), nên AC03 giữ nguyên.
  - **Bằng chứng (200 người giả × 29 ngày):** chủ đề lặp trong 3 ngày 30,3% → 21,2% (giờ chính xác 24,0% → 7,0%);
    trong 7 ngày 79,5% → 73,2%; tiêu đề lặp trong 7 ngày 11,9% → 8,4%; trung vị số chủ đề trong 14 ngày 3 → 4.
  - **Giới hạn:** lặp trong 7 ngày bị chặn bởi số tình huống đủ điều kiện (trung bình 2,3 mỗi ngày). Mở rộng pool ở
    #847, #848, #849, #851 (câu chờ duyệt).
- **AC06:** Ngày bị ép ngoại lệ D thì D+1 ở đúng vị trí danh nghĩa (không dịch). Báo cáo có số lượt và
  tỷ lệ ngoại lệ. *(Phản ví dụ của Codex)*

### Người chỉ có ngày sinh

- **AC07:** Không còn "một tình huống cố định theo cung cả năm". Pool có 4–6 tình huống, lấy từ cung,
  nguyên tố, tính chất và **transit chắc chắn** tới các hành tinh có miền xác định
  (`la-lanh-personal-sky-events-spec.md`).
  - *Trạng thái 18.11.2026 (#626): mới đạt một phần.* Pool lấy từ cung và nguyên tố của Mặt Trời:
    8 cung có 2 tình huống đổi nhau mỗi ngày; Bạch Dương, Kim Ngưu, Cự Giải, Bảo Bình vẫn 1 tình
    huống vì cung và nguyên tố cho cùng một tình huống. Mặt Trời ở ranh giới hai cung chưa được gì
    thêm. Chưa có: tính chất, các hành tinh khác chắc cung từ ngày sinh, transit chắc chắn; nên
    chưa tới 4–6.
  - *Trạng thái 20.11.2026 (chạy thử người dùng cũ):* thêm **tính chất** của cung Mặt Trời
    (`SUN_MODALITY_ISSUES`: thống lĩnh → đổi kế hoạch, kiên định → nói rõ nhu cầu, linh hoạt →
    mở nhiều việc cùng lúc), xếp dưới nguyên tố, cùng một yếu tố Mặt Trời theo ngày sinh. 6 cung
    có 3 tình huống, 6 cung (Bạch Dương, Kim Ngưu, Song Tử, Cự Giải, Bọ Cạp, Bảo Bình) có 2; không
    cung nào còn 1.
    Không thêm câu chữ mới. Vẫn chưa có: các hành tinh khác chắc cung, transit chắc chắn.
- **AC08:** Không dùng Mặt Trăng, cung mọc, nhà. Bài ghi rõ là bản đọc từ ngày sinh.
  - Câu nói về **pha** chỉ hiện khi pha chắc trên miền ngày sinh (`phase_allowed`).
  - "Ngày N" theo AC09.
  - Mọi phép tính dùng `observed_at` của projection (`local_date` 12:00 UTC), không dùng giờ request.

### Lịch cá nhân và mạch

- **AC09:** Một chương = một lượt có ID ổn định.
  - "Ngày N" chỉ hiện khi `day_allowed = (t_s ≤ observed_at ≤ t_e)` trên cửa sổ chắc (so timestamp).
    `N = local_date(observed_at) − local_date(t_s) + 1` theo `MVP_TIMEZONE`.
  - Không phụ thuộc pha. Pha chắc chỉ quyết định câu nói về pha (AC08).
  - Nhịp "nhìn lại" chỉ mời tự soi, không khẳng định người đọc đã làm gì.
- **AC10:** Tối đa một chương nổi trên Home. Ưu tiên theo độ chặt orb và mức cá nhân.

### Kho nội dung

- **AC11:** 20 tình huống (gồm 5 mới do owner chọn). Mỗi khung có lịch chủ ≥ 90 tổ hợp chủ; tiêu đề ≥ 90
  tổ hợp mỗi tình huống. Có hành động theo lens công việc, giao tiếp, năng lượng.
- **AC12:** "Vì sao hôm nay?" có 3–4 khung theo loại transit. Không quá 3 ngày liền cùng một transit.
  Giữ evidence binding.

### "Điều bạn đang quan tâm" (F)

- **AC13:**
  - Mặc định chưa chọn.
  - Đổi hoặc xoá trong Mình, qua CSRF và quyền sở hữu phiên.
  - Chỉ dùng để chọn tag cảnh và đối tượng; không suy luận thêm; không log.
  - Xoá cùng hồ sơ.
  - Không gửi Luna, kể cả dưới dạng nội dung suy ra trong scene hoặc brief khi Luna được bật sau này.
  - **Không bật trước khi rà luật xong**, và trước khi data map, privacy copy, khai báo store được cập nhật.

### Đo

- **AC14:** Các chỉ số trong `la-lanh-variety-measurement-spec.md` tính trên **output cuối cùng được phục
  vụ**, theo nhóm. Ngưỡng do owner chốt (`docs/plans/2026-10-16-p0-owner-decisions.md`).

## Definition of Done

- AC01–AC14 có test và audit. Manifest, allowlist và lịch qua CI.
- Owner đọc 14 ngày mẫu cho 2 tình huống thí điểm trước khi mở rộng.
- Owner duyệt giá trị ô và mẫu ghép (gồm Cà khịa).
- Cập nhật content standard, baseline, data map (với F), runbook.
- Codex APPROVE @ SHA; release theo runbook.
