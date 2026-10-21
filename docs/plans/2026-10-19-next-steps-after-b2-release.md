# Kế hoạch tiếp theo sau release Tarot B2 (19/10/2026)

> Nguồn: `docs/plans/2026-10-16-personalisation-variety-plan.md` (§6 thứ tự, §8 quyết định owner, §14),
> `docs/plans/2026-10-16-p0-owner-decisions.md` (A1–A12), receipt
> `docs/reviews/production-release-2026-10-18/receipt.md`, owner approval
> `docs/reviews/2026-10-18-b2-tarot-owner-approval.md`, Issue #2, #5, #6, #7, #14.
>
> Kế hoạch này chưa phải approval code hay release. Mỗi bước vẫn là một PR, Codex review theo SHA,
> owner duyệt nội dung mới qua Excel, release theo runbook.

## 0. Trạng thái hiện tại

| Mảng | Trên production (`4111f03cee3c`) |
|---|---|
| Tarot | B2 đầy đủ: hiểu câu hỏi, nghĩa theo vai, hướng nghiêng, tóm tắt nối vai, tiêu đề động, biến thể theo phiên, Cà khịa theo khung |
| Note ngày (Astro) | B3-1a xoay vòng theo người, **bật từ 19/10**. Nội dung tình huống vẫn là bản 15 tình huống cũ |
| Hợp gu (Radar) | Như release 16/10 |
| Hạ tầng | G0 composer (chưa phục vụ), P1 đo baseline, provenance cho payload Luna, fallback approval khoá copy B2 và copy cũ |
| Tắt | Luna (AI rewrite), đăng nhập Google |
| Rủi ro mở | **Chưa có image rollback đọc được bài Tarot B2**: sự cố thì sửa tiến. Backup DB chỉ chạy khi phát hành, chưa có lịch hằng ngày |
| Chờ phát hành | Hotfix hướng nghiêng (PR #34, `tarot-stance-v2`): Codex APPROVE @ `e6debac449cb602b70baf91a8c18c01b693e4a7b` ngày 20/10. Chưa merge, chưa deploy; chờ owner chỉ thị |

## 1. Giai đoạn 0 — người dùng dùng thử (bắt đầu ngay)

**Mục tiêu:** biết người thật có hiểu và thấy bài "đúng là của mình" không, trước khi viết thêm nội dung.

**Owner làm:**
- Mời người dùng thử qua link production. Đề xuất 10–20 người, đủ ba nhóm: có giờ sinh, chỉ có ngày sinh,
  chỉ dùng Tarot.
- Thu phản hồi bên ngoài app (form hoặc phỏng vấn ngắn). App không có kênh phản hồi và không log nội dung;
  không xin người dùng gửi câu hỏi Tarot hay ngày sinh qua kênh không mã hoá.

**Kịch bản và câu hỏi gợi ý** (theo ngưỡng Go/No-Go của runbook):
1. Note ngày, ba ngày liên tiếp: "Bạn nhắc lại được một ý của note hôm nay không?" (mục tiêu ≥ 80%),
   "Có thấy nói về bạn không, hay ai đọc cũng đúng?" (≥ 70% thấy riêng; "chung chung" < 15%),
   "Hôm nay khác hôm qua không?".
2. Tarot: hỏi một câu có/không, một câu chọn A/B, một câu "làm sao". "Bài có trả lời đúng câu bạn hỏi
   không?", "Phần hướng nghiêng có rõ không, có thấy bị phán thay không?", "Bạn làm được việc nhỏ nào?".
3. Giọng Cà khịa: "Vui hay khó chịu?".
4. Hợp gu: "Có hiểu điểm hợp và điểm vướng không?".

**Claude làm (không cần quyền mới):**
- Mẫu phiếu phản hồi và bảng tổng hợp (Excel) theo đúng các ngưỡng trên.
- Đọc phản hồi owner gửi lại và chuyển thành task có AC.

**Theo dõi vận hành trong lúc thử** (cần owner cho phép truy cập server khi kiểm):
- health/ready, log lỗi (không chứa nội dung), số phiên Tarot bị lưu `reading = null` (lỗi gate) qua log
  cảnh báo `tarot_local_content_rejected`;
- B3-1a: note báo `available_update` bất thường.
- **Tiêu chí dừng:** lỗi server lặp lại hoặc bài không mở lại được. Khi đó tắt B3-1a bằng cờ (receipt có hướng
  dẫn), còn Tarot thì sửa tiến.

## 2. Giai đoạn 1 — an toàn vận hành (song song, việc nhỏ)

| # | Việc | Vì sao | Cần owner |
|---|---|---|---|
| O1 | Backup DB hằng ngày (systemd timer cho `backup-database.sh`, giữ 14 ngày) và ghi lại khả năng backup của gói Supabase | Đang có người dùng thật; hiện chỉ backup lúc phát hành | Cho phép cài timer trên server |
| O2 | Image rollback đọc được dữ liệu B2: `small_action` tuỳ chọn trên nền `836222282dfc`, web ẩn khối việc nhỏ rỗng, probe trên DB tạm | Hiện không có mốc rollback cho bài B2 | Duyệt đổi runtime nhánh cũ + build/probe trên server |
| O3 | Đưa `staging.caddy` vào luồng deploy (template trong repo hoặc tự chép từ release trước, có test) | Release 18/10 làm staging mất site | Không (PR thường) |
| O4 | Khoá chữ nằm trong thân hàm (`engine._reflection`, `_meaning`, câu reframe, câu kết, disclaimer; `stance._role_sentence`, `_reason`) vào fallback approval | Hiện sửa các câu này không làm approval báo lệch | Không (giữ nguyên chữ, chứng minh byte-identical) |
| O5 | Dọn Issue: cập nhật #6 (B2 xong, còn backlog C4–C6), #14 (UI đã live 16/10), #5 (B1 → G1) | Issue là nơi bàn giao chung | Không |

Thứ tự đề xuất: O1 → O3 → O5 → O4. O2 làm khi owner duyệt.

## 3. Giai đoạn 2 — nội dung, chặng 1 còn lại (theo §6)

### G1 — Note ngày trên ngữ pháp + phần còn lại của A2 (bước tiếp theo của roadmap)

Mục tiêu (US-21): note riêng cho từng người, đổi mỗi ngày, đúng lý do.

1. **G1-0 task doc:** ánh xạ AC US-21 còn thiếu; khung và ô theo `la-lanh-content-grammar-spec.md`; ngưỡng A1
   (yếu tố riêng), A2 (khoảng lặp ≥ 90 ngày), A3 (< 1% note trùng giữa hai người cùng cung cùng ngày).
2. **G1-1 thí điểm 2 tình huống** trên composer G0 (lần đầu phục vụ nội dung ngữ pháp): khung × ô × 2 giọng,
   gate build, đo bằng `variety:baseline`. Owner đọc 14 ngày mẫu (Excel, khoảng 30 tổ hợp mỗi khung).
3. **G1-2 mở rộng đủ 20 tình huống**, gồm 5 tình huống đã chọn (A8): `waiting-for-reply`, `rest-guilt`,
   `feedback-sting`, `new-environment`, `skipped-small-win`. Mỗi tình huống: meaning brief, anchor/contrary
   cho lời của Lá, luật chart (natal và transit).
4. **G1-3 người chỉ có ngày sinh:** pool 4–6 tình huống từ cung, nguyên tố, tính chất và transit tới Mặt
   Trời natal; giữ nhãn "bản tóm tắt từ ngày sinh".
5. **G1-4 cân lại transit:** transit orb chặt vào top-K; "Vì sao hôm nay?" 3–4 khung theo pha; không lặp một
   transit quá 3 ngày liền.
6. Release G1 theo runbook. Nội dung mới qua Excel; Cà khịa ánh xạ theo mã như B2.

Phản hồi người dùng ở Giai đoạn 0 được đưa vào G1-1 trước khi viết hàng loạt.

### Biên tập catalog Tarot (backlog owner đã chốt)

- C4: rà 3.096 ô cảnh có từ khuyên (phần lớn "thử" kể chuyện), sửa câu thật sự khuyên.
- C5: thêm tình huống "khi…" cho việc nhỏ (hiện 12%).
- Làm theo đợt Excel. Bump knowledge version và làm mới fallback approval khi owner duyệt.

### G2 — Lịch cá nhân từ lá số

Theo `la-lanh-personal-sky-events-spec.md`: sự kiện theo transit tới lá số, mạch nhiều ngày cho note. Làm sau
G1.

### B4 — Hợp gu trên ngữ pháp (US-22, R2)

Cảnh theo chủ đề × ngữ cảnh (2–3 biến thể), câu theo contact (cặp hành tinh × họ góc chiếu), nhịp nguyên
tố/tính chất của hai người, giọng đổi cả câu. Audit 50 cặp × 4 ngữ cảnh × 4 giọng. Làm sau G1.

## 4. Giai đoạn 3 — E: AI lúc soạn (theo đợt)

- Chỉ sau khi khung của mảng ổn định. Nhà cung cấp theo A10 (Claude API hoặc OpenAI, sau khi kiểm điều
  khoản dùng output).
- **Mỗi đợt owner duyệt chi phí trước khi gọi API trả phí.** Output là bản nháp; owner duyệt qua Excel rồi
  mới vào catalog và fallback approval.
- Đợt đầu đề xuất: C6 (2–3 cảnh cho mỗi lá × chủ đề, khoảng 470–940 cảnh) và ô cho 5 tình huống Astro mới.

## 5. Chặng 2 — tín hiệu người dùng tự bật

Chỉ bắt đầu sau khi rà **Luật 91/2025 và NĐ 356/2025 từ nguồn chính thức**, có copy consent mới, data map,
và khai báo Apple/Google.
- B3-3: mood hôm nay → nhịp của việc nhỏ; phản hồi trúng/chưa trúng → xếp hạng lại tình huống (giữ 30 ngày,
  xem và đặt lại được).
- Gợi ý cách hỏi Tarot theo chủ đề; nối Tarot với tình huống note hôm nay.
- Nhật ký Tarot (mặc định tắt, ghi chú tự do là dữ liệu nhạy cảm, có xem, xuất và xoá).
- F "điều bạn đang quan tâm" (A9).

## 6. Chặng 3 — Luna (Issue #7)

Điều kiện trước khi bật:
1. Sửa prompt Tarot: `source`, `stance`, `summary_source` là nhãn provenance (nâng phiên bản prompt, corpus
   rewrite, test). Không gọi provider.
2. Bộ chấm chất lượng: cùng tập mẫu tổng hợp, so bản tất định với bản Luna; lưu kết quả.
3. Owner duyệt: API key (nhập qua kênh bảo vệ), ngân sách tháng, DPA/điều khoản, privacy copy, Data
   Safety/App Privacy; pilot cap và kill switch.
4. Chỉ mở rộng phạm vi khi điểm chấm cho thấy tốt hơn.
5. **Kiểm lại stance v1** (ghi chú review Codex PR #34, 20/10). Gate `stance_consistent`
   (`TarotReadingEngine._stance_consistent`) gọi `stance.recompute`, mà hàm này luôn tính theo thuật toán
   hiện hành (`tarot-stance-v2`) rồi so **toàn bộ** stance, kể cả trường `version`. Một bài có frame lưu
   từ trước hotfix (`tarot-stance-v1`), nếu đem gate lại hoặc đưa vào rewrite, sẽ bị từ chối vì lệch
   version. Khi bài đó hỏi về hành động tự chăm sóc, mức hướng nghiêng cũng có thể lệch.
   - Hiện chưa ảnh hưởng: mở lại phiên cũ chỉ đọc bản đã lưu, không chạy gate này và không đổi version hay
     chữ. Luna đang tắt.
   - Phải chốt trước task bật Luna cho Tarot. Các hướng:
     - (a) Kiểm lại theo đúng version đã lưu: giữ hàm tính v1 dưới tên riêng và cho `recompute` chọn hàm
       theo `stance.version`. Bài cũ vẫn kiểm được và vẫn rewrite được.
     - (b) Chỉ rewrite bài có `tarot-stance-v2`. Bài v1 giữ bản tất định, không tạo request; ghi lý do vào
       ledger hoặc log mà không chứa nội dung.
     - (c) Không chuyển bản lưu v1 sang v2, vì như vậy là đổi lời đã hiển thị cho người dùng.
   - Đề xuất: (b) làm mặc định, vì đơn giản nhất và không gửi gì cho bài cũ. Chỉ thêm (a) nếu cần
     rewrite bài cũ. Cả hai đều cần test: bản v1 tổng hợp đem gate lại không bị đổi chữ, và với (b) thì
     không có request nào cho bài v1.

## 7. Thứ tự đề xuất

1. Giai đoạn 0 (owner mời người dùng) song song với O1, O3, O5.
2. G1-0 → G1-1 (thí điểm, có phản hồi người dùng) → owner đọc 14 ngày mẫu → G1-2 … G1-4 → release G1.
3. O4, đợt biên tập C4/C5 xen giữa các bước G1 khi chờ owner duyệt.
4. G2 → B4.
5. E theo đợt, mỗi đợt duyệt chi phí.
6. Rà luật → chặng 2. Luna khi đủ điều kiện Issue #7.

## 8. Owner cần chốt

| # | Câu hỏi | Đề xuất |
|---|---|---|
| D1 | Số người và nhóm người dùng thử, cách thu phản hồi | 10–20 người, ba nhóm, form ngoài app |
| D2 | Cài backup DB hằng ngày (O1) | Có |
| D3 | Làm image rollback đọc được B2 (O2) | Có, trước khi mời nhiều người hơn |
| D4 | Bắt đầu G1 ngay hay chờ phản hồi người dùng | Bắt đầu G1-0 ngay; G1-1 dùng phản hồi tuần đầu |
| D5 | Thời điểm rà luật cho chặng 2 | Song song với G1, vì không chặn code |
| D6 | Luna | Giữ tắt tới khi xong bước 1–3 và bước 5 (stance v1) ở mục 6 |
