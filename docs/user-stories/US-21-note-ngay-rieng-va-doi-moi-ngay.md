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
- **Ngoại lệ:** bản đọc có `variety_exception` (gate an toàn từ chối hoặc manifest hỏng) phục vụ kho nền.
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
- **AC06:** Ngày bị ép ngoại lệ D thì D+1 ở đúng vị trí danh nghĩa (không dịch). Báo cáo có số lượt và
  tỷ lệ ngoại lệ. *(Phản ví dụ của Codex)*

### Người chỉ có ngày sinh

- **AC07:** Không còn "một tình huống cố định theo cung cả năm". Pool có 4–6 tình huống, lấy từ cung,
  nguyên tố, tính chất và **transit chắc chắn** tới các hành tinh có miền xác định
  (`la-lanh-personal-sky-events-spec.md`).
- **AC08:** Không dùng Mặt Trăng, cung mọc, nhà. Pha transit và "Ngày N của đợt" chỉ hiện khi bất biến
  trên miền ngày sinh. Bài ghi rõ là bản đọc từ ngày sinh.

### Lịch cá nhân và mạch

- **AC09:** Một chương = một lượt có ID ổn định. "Ngày N" chỉ dùng trong cửa sổ chắc. Nhịp "nhìn lại" chỉ
  mời tự soi, không khẳng định người đọc đã làm gì.
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
