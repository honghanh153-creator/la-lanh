# Lịch sử phát hành Lá Lành

Mỗi lần phát hành production (bản tuần hoặc bản vá) có một mục ở đây, mới nhất ở trên. Lệnh của owner ngày
28.11.2026: mọi lần phát hành và bản vá chạy trong một luồng phát hành duy nhất. Luồng đó giữ file này đúng sau
mỗi lần phát hành.

- Chi tiết và bằng chứng của từng lần nằm trong biên nhận `docs/reviews/production-release-<ngày>/`. File này chỉ
  tóm tắt. Khi hai bên khác nhau, biên nhận đúng.
- Repo công khai: không ghi dữ liệu cá nhân, số tiền ngân sách hay địa chỉ IP của máy chủ.
- Chỗ nào biên nhận và lịch sử git không xác nhận được thì ghi "chưa rõ", không đoán.
- Quay lại bản cũ: chỉ đổi image. Không bao giờ chạy `alembic downgrade` hay khôi phục backup vào bản chạy thật
  (P07/B trong runbook).

## Cách cập nhật

1. Sau khi phát hành xong (đã có biên nhận), thêm một mục mới lên đầu phần "Đã phát hành", theo mẫu bên dưới.
2. Chuyển các PR vừa phát hành ra khỏi phần "Chưa phát hành".
3. Sáng thứ Sáu, làm mới phần "Chưa phát hành" từ ứng viên cuối cùng. Danh sách đó là danh sách thay đổi của lần
   phát hành tiếp theo:

   ```sh
   git fetch origin
   git log --first-parent --merges --format='%h %s' <ứng viên lần trước>..origin/collab/integration
   ```

Mẫu một mục:

```text
## <ngày> — <bản tuần | bản vá> <12 ký tự đầu của main>
| main / image | schema | cờ đổi | PR | quay lại | biên nhận |
Người dùng sẽ thấy: 3–6 dòng tiếng Việt đời thường.
Kiểm: smoke.sh, qa-public-smoke, journey, ảnh 360/390.
```

## Chưa phát hành

Đã merge vào `collab/integration` sau ứng viên `a3a12222` của lần 28.11 (đầu nhánh lúc ghi: `db913b80`, 28.11.2026).

| PR | Nội dung | Người dùng thấy gì |
|---|---|---|
| #851 | Daily: thêm chủ đề "va chạm" cho 4 tiếp xúc căng | Chưa thấy: câu còn chờ duyệt |
| #849 | Daily: thêm chủ đề "quá tải" cho 3 tiếp xúc căng của Hỏa tinh | Chưa thấy: câu còn chờ duyệt |
| #860 | Quy trình: mỗi bài học phải đỏ trước, xanh sau | Không (chỉ máy kiểm) |
| #944 | Tài liệu: nhìn lại vòng tự động 27.11 | Không |
| #943 | Tài liệu: nhìn lại vòng tự động 26.11 | Không |

Đang chờ merge, cũng không đổi app: #961 (biên nhận 28.11 và runbook), #962 (đưa `main` về lại `collab/integration`,
diff rỗng).

## Đã phát hành

### 28.11.2026 — bản tuần `5518cca34786`

| Mục | Giá trị |
|---|---|
| main / image | `5518cca3478649ed2b8cedf1e7c6f37ec8cd24ce` / `la-lanh:5518cca34786` (`sha256:7517a74c5638…`) |
| Schema | `20261111_0042`, không có migration |
| Cờ đổi | AE1: `LA_LANH_KEEP_ACTION_ALL_PROFILES=true` (chỉ production; staging để tắt). Lịch chủ đề chống lặp và Lá pixel vẫn tắt |
| PR | #953: ứng viên `a3a12222` merge với `main`; 71 PR kể từ ứng viên 20.11 (`059d3c35`) |
| Quay lại | `la-lanh:42b678c13a93` (cùng schema). Chỉ tắt AE1: đặt cờ thành `false` |
| Biên nhận | [production-release-2026-11-28](../reviews/production-release-2026-11-28/receipt.md) (trong #961, chưa merge lúc ghi) |

Người dùng sẽ thấy:
- Người chỉ có ngày sinh hoặc giờ sinh ước chừng cũng giữ được việc nhỏ của Note hôm nay (#740). Home hiện việc đang
  giữ và cho đổi việc khác (#756).
- Nút "Hôm nay chỉ muốn đọc" thu ô việc nhỏ lại còn một dòng (#833).
- Chữ tiếng Việt dễ hiểu hơn ở các màn tuần đầu và ở Hợp gu (#776, #787); Khám phá và Aura không lặp câu giữa các thẻ
  (#774).
- Nút "Tạo thẻ chia sẻ" ở Mình dễ đọc hơn (#836). Câu đồng ý ngày sinh và dòng riêng tư của Tarot theo bản owner đã
  duyệt (#792).
- Chưa thấy: các câu việc nhẹ hơn, việc làm một mình, câu theo cảm giác Căng và Lạc trôi. Code đã có, câu còn chờ
  duyệt.

Kiểm: `smoke.sh` đạt; `qa-public-smoke` 9/9; kiểm nút giữ trên production với người chỉ có ngày sinh đạt; ảnh 360 và
390 px đạt (ảnh nằm trên máy owner); journey 22/22. Claude review: được phát hành, có việc sửa tiếp, không có P0/P1.
Codex review: chờ lượt.

### 21.11.2026 — bản vá `42b678c13a93`

| Mục | Giá trị |
|---|---|
| main / image | `42b678c13a9333c68840e5ac65b2ae06dff4be81` / `la-lanh:42b678c13a93` (`sha256:807bdcbcff52…`) |
| Schema | `20261111_0042`, không có migration |
| Cờ đổi | Không |
| PR | #824: cherry-pick bản sửa #808 (issue #809). Phát hành theo quyền bản vá R12 |
| Quay lại | `la-lanh:577a5d0b7a98` (cùng schema; quay lại thì các câu từ biệt bị bỏ sót sẽ quay lại) |
| Biên nhận | [production-release-2026-11-21](../reviews/production-release-2026-11-21/receipt.md) (#826) |

Người dùng sẽ thấy:
- Khi gõ những câu từ biệt như "đi xa mãi mãi" hay "khỏi cuộc đời này", người dùng nhận thông báo hỗ trợ khủng hoảng
  thay vì một bài đọc.
- Những câu bản 20.11 đã nhận ra thì vẫn được nhận ra.

Kiểm: `smoke.sh` đạt; `qa-public-smoke` 9/9; kiểm khủng hoảng trên production với 6 câu Tarot đạt; journey: các bước
bắt buộc đạt, bước tùy chọn chọn cảm giác hỏng do máy kiểm còn tìm nhãn nút cũ. Ảnh 360 px: chưa rõ (biên nhận chỉ ghi
390 px). Codex review: được phát hành, có việc sửa tiếp.

### 20.11.2026 — bản tuần `577a5d0b7a98`

| Mục | Giá trị |
|---|---|
| main / image | `577a5d0b7a9875d0e66c9a780e6f4db5cb77b68c` / `la-lanh:577a5d0b7a98` (`sha256:a9eb4b1fcb73…`) |
| Schema | `20261111_0042`, không có migration |
| Cờ đổi | Không. `LA_LANH_KEEP_ACTION_ALL_PROFILES` để trống (bật ở bản 28.11) |
| PR | #769: ứng viên `059d3c35` merge với `main`; 141 PR kể từ bản 13.11. Owner duyệt "Ah1" |
| Quay lại | `la-lanh:56523ccb7de5` (cùng schema) |
| Biên nhận | [production-release-2026-11-20](../reviews/production-release-2026-11-20/receipt.md) (#770) |

Người dùng sẽ thấy:
- Chặn nội dung tự hại trong ô gõ chữ (#505).
- Bỏ "Vibe"; không mời đăng nhập khi đăng nhập đang tắt (#503).
- Chọn cảm giác hôm nay nằm dưới Note (#449).
- Daily ít lặp hơn cho người có giờ ước chừng và người chỉ có ngày sinh (#660, #666, #684).
- Jyotish dùng được với giờ ước chừng (#388). Chữ của Daily dễ hiểu hơn (#491, #635, #685). Ba câu riêng tư theo bản
  owner đã duyệt.

Kiểm: `pnpm check` đạt; 200 người giả đạt; kiểm lặp Daily cho kết quả "giữ", owner chấp nhận (AH1); `smoke.sh` đạt;
`qa-public-smoke` 9/9; journey 22/22 ở lần chạy thứ hai (lần đầu bước chọn cảm giác hỏng vì máy kiểm tìm nhãn nút cũ).
Ảnh 360/390 px: chưa rõ (biên nhận chỉ ghi journey 390 px). Claude review và Codex review: được phát hành, có việc sửa
tiếp.

### 15.11.2026 — bản vá `56523ccb7de5`

| Mục | Giá trị |
|---|---|
| main / image | `56523ccb7de5a18df7e5aa9510e27a48e77d2794` / `la-lanh:56523ccb7de5` (`sha256:f42a945ee43e…`) |
| Schema | `20261111_0042`, không có migration |
| Cờ đổi | Không |
| PR | #549: cherry-pick bản sửa #546 (issue #545) |
| Quay lại | `la-lanh:f6246ed2fb7a` (cùng schema; quay lại thì lỗi quay lại) |
| Biên nhận | [production-release-2026-11-15](../reviews/production-release-2026-11-15/receipt.md) (#550) |

Người dùng sẽ thấy:
- Trên Hôm nay, nút "Đọc bản mới" mở được bài đọc mới cho mọi loại hồ sơ.
- Trước bản vá, người có giờ ước chừng, và người chỉ có ngày sinh sau khi nội dung được đọc lại trong ngày, luôn gặp
  "Món quà chưa mở được".

Kiểm: test API đạt; `smoke.sh` đạt; `qa-public-smoke` 9/9; kiểm AC1 trên production đạt; journey: các bước bắt buộc
đạt. Ảnh 360 px: chưa rõ. Codex review: được phát hành.

### 13.11.2026 — bản lớn, hai bước: R1 `f22a755f7128`, R2 `f6246ed2fb7a`

| Mục | Giá trị |
|---|---|
| main / image | R1 `f22a755f7128c564193331d4b34c2bd29ac4f370` / `la-lanh:f22a755f7128` (`sha256:a0e57af3ad11…`); R2 `f6246ed2fb7a5033247ad6b41af33f35022cab12` / `la-lanh:f6246ed2fb7a` (`sha256:b9e860240f01…`) |
| Schema | R1: `20261029_0038a`. R2: `0039` (bỏ cascade của bản lưu và link chia sẻ), `0040`–`0042` chỉ thêm. Từ đây mọi lần phát hành bắt đầu từ `0042` |
| Cờ đổi | Không bật cờ nào. Cờ mới `LA_LANH_HUMAN_TAROT_*` và `LA_LANH_MOOD_ENCRYPTED_WRITES` để tắt |
| PR | R1: #464 (cùng các bản vá #427, #430). R2: #472, `collab/integration` `cac542e` (186 PR) merge với `main`. Owner: "đẩy hết lên production" |
| Quay lại | `la-lanh:f22a755f7128` chỉ dùng được trên `0038a`. Sau `0039` thì sửa tiến, không quay lại |
| Biên nhận | [production-release-2026-11-13](../reviews/production-release-2026-11-13/receipt.md) (#473) |

Người dùng sẽ thấy:
- Trang tổng quan lá số trong Khám phá (#463).
- Phần lớn 186 PR: chưa rõ. Biên nhận không tóm tắt thay đổi cho người dùng.

Kiểm: `pnpm check` đạt; `smoke.sh` đạt; `qa-public-smoke` 9/9; ảnh 360/390 px của trang tổng quan lá số trên staging
đạt; journey 22/22. Đây là lần đầu journey thành bước bắt buộc. Codex review: hai lượt, không có P0/P1 trong luồng
chính, một P1 về lời mời đăng nhập khi đăng nhập tắt (đã sửa ở bản 20.11).

### 26.10.2026 — `89ebdb0cf6b9`

| Mục | Giá trị |
|---|---|
| main / image | `89ebdb0cf6b974994b7f67807873ac320b5ed228` / `la-lanh:89ebdb0cf6b9` (`sha256:8fcab2f44e27…`) |
| Schema | `20261018_0037` → `20261023_0038` (sổ ghi việc xóa dữ liệu) |
| Cờ đổi | Không. Luna vẫn chỉ bật cho Daily |
| PR | #75: `collab/integration` `7e6d69e`. Không gồm #83, #87, #88, #89 |
| Quay lại | Không có bản quay lại đã kiểm chứng (`c3fab3311d65` chưa được kiểm trên `0038`). Sửa tiến |
| Biên nhận | [production-release-2026-10-26](../reviews/production-release-2026-10-26/receipt.md) |

Người dùng sẽ thấy:
- Không có thay đổi màn hình nào được ghi. Bản này thêm sổ ghi việc xóa dữ liệu, backup hằng ngày và lịch kiểm backup.

Kiểm: `pnpm check` (Codex chạy) đạt; `smoke.sh` đạt; `qa-public-smoke` đạt trên staging và production. Journey và ảnh
360/390 px: chưa có (journey bắt đầu từ 13.11).

### 21.10.2026 — `c3fab3311d65`

| Mục | Giá trị |
|---|---|
| main / image | `c3fab3311d659c240da944a84fec305eca416cc6` / `la-lanh:c3fab3311d65` (`sha256:ff8247ab158b…`) |
| Schema | `20261018_0037`, không có migration |
| Cờ đổi | Bật Luna viết lại Daily (`LA_LANH_GENERATION_ENABLED=true`, chỉ cho Daily trên Home, thử 14 ngày, tối đa 20 người đã đồng ý). Trần chi tiêu là số riêng, không ghi ở đây |
| PR | #33–#39 |
| Quay lại | `la-lanh:4111f03cee3c` (cùng schema). Note Daily đã xóa theo #38 không lấy lại được nếu không dùng backup |
| Biên nhận | [production-release-2026-10-21](../reviews/production-release-2026-10-21/receipt.md) |

Người dùng sẽ thấy:
- Lịch sử Daily chỉ hiện trong 24 giờ (#38). Radar giữ bản kiểm riêng trong 24 giờ (#35).
- Người đã đồng ý có thể nhận Note Daily do Luna viết lại (#37).
- Trang riêng tư có chữ mới về giữ lịch sử Daily và về Luna.

Kiểm: `pnpm check` đạt; `smoke.sh` đạt; trang riêng tư không tràn ngang ở 390 px. `qa-public-smoke`: chưa rõ. Journey
và ảnh 360 px: chưa có.

### 19.10.2026 — bật cờ, cùng image `4111f03cee3c`

| Mục | Giá trị |
|---|---|
| main / image | `4f595a35dd6851b154f5a61e1bd2f6e28615ebc3` / không build lại, vẫn chạy `la-lanh:4111f03cee3c` (thay đổi duy nhất trong `apps/` là một dòng test) |
| Schema | `20261018_0037`, không có migration |
| Cờ đổi | Bật xoay vòng Daily: `LA_LANH_DAILY_VARIETY_FROM=2026-10-19` trên production và staging |
| PR | #32 |
| Quay lại | Xóa dòng cờ (hoặc dùng lại file env cũ `app.env.pre-daily-variety`) rồi chạy lại `deploy.sh`. Note đã lưu giữ nguyên |
| Biên nhận | [production-release-2026-10-18, phần bổ sung 19.10](../reviews/production-release-2026-10-18/receipt.md#addendum--19102026-b3-1a-daily-rotation-enabled) |

Người dùng sẽ thấy:
- Từ ngày 19.10, Note Daily xoay vòng theo từng người. Note đã mở trước lúc bật cờ giữ nguyên.

Kiểm: `smoke.sh` đạt trên production và staging; `qa-public-smoke` đạt (Note Daily người chỉ có ngày sinh, Tarot 1/3/5,
Radar, xóa khách thử). Journey và ảnh 360 px: chưa có.

### 18.10.2026 — `4111f03cee3c`

| Mục | Giá trị |
|---|---|
| main / image | `4111f03cee3c7a3b3e886530f536236e30fc3526` / `la-lanh:4111f03cee3c` (`sha256:3194d73b9762…`) |
| Schema | `20261011_0036` → `20261018_0037` (thêm `tarot_variant_cursors`) |
| Cờ đổi | Không bật. Xoay vòng Daily có trong code nhưng để tắt (`LA_LANH_DAILY_VARIETY_FROM` để trống); bật ngày 19.10, xem mục 19.10 |
| PR | #20–#31 |
| Quay lại | Không có bản quay lại đã kiểm chứng: `la-lanh:836222282dfc` khởi động được nhưng không mở được bài Tarot B2 lưu sau khi phát hành |
| Biên nhận | [production-release-2026-10-18](../reviews/production-release-2026-10-18/receipt.md) |

Người dùng sẽ thấy:
- Tarot đọc theo câu hỏi (B2): tiêu đề theo câu hỏi, phần "Hướng nghiêng" kèm lý do, phần tóm tắt nối các lá.
- Câu hỏi về người thứ ba được nói lại theo hướng của chính người hỏi.
- Xóa được một lần bốc. Link cũ báo không mở lại được.

Kiểm: `pnpm check` đạt; `smoke.sh` đạt; `qa-public-smoke` đạt; diễn tập migration trên bản sao backup đạt; kiểm trên
trình duyệt production đạt. Journey và ảnh 360 px: chưa có.

### 16.10.2026 — bản vá `836222282dfc`

| Mục | Giá trị |
|---|---|
| main / image | `836222282dfc99022a1de5da69483bc9c83670a8` / `la-lanh:836222282dfc` (`sha256:aabf64a081d0…`) |
| Schema | `20261011_0036`, không có migration |
| Cờ đổi | Không |
| PR | #15, #16. Owner: "merge và deploy #15, #16" |
| Quay lại | `la-lanh:b474cafbc434` (cùng schema) |
| Biên nhận | [production-release-2026-10-16 (bản vá)](../reviews/production-release-2026-10-16/receipt-836222282dfc.md) |

Người dùng sẽ thấy:
- Xóa một kết quả Radar thì có bảng hỏi lại trước ("Xoá kết quả với {tên}?"), bấm "Giữ lại" thì không xóa.
- Nút "Xóa vĩnh viễn" dễ đọc ở cả nền sáng và nền tối.

Kiểm: `pnpm check` đạt; `smoke.sh` và `qa-public-smoke` đạt trên staging và production; kiểm trên trình duyệt ở 375 px
đạt. Journey: chưa có.

### 16.10.2026 — `b474cafbc434`

| Mục | Giá trị |
|---|---|
| main / image | `b474cafbc434cc78ec649e2949a75ac1ba1132da` / `la-lanh:b474cafbc434` (`sha256:10ba22405c47…`) |
| Schema | `20261011_0036`, không có migration |
| Cờ đổi | Không |
| PR | #4, #8, #10, #11, #12, #13 |
| Quay lại | `la-lanh:a6e11bfd149b` (cùng schema) |
| Biên nhận | [production-release-2026-10-16](../reviews/production-release-2026-10-16/receipt.md) |

Người dùng sẽ thấy:
- Lá có câu nói đi kèm (#12).
- Giao diện "Tím đêm dịu" (#13).
- Home có thẻ ban đêm, "Thử một việc nhỏ", "Đọc đầy đủ" và nút chọn cảm giác.

Kiểm: `pnpm check` đạt; `smoke.sh` và `qa-public-smoke` đạt trên staging và production; kiểm trên trình duyệt ở 375 px
đạt. Journey: chưa có.

### 11.10.2026 — `a6e11bfd149b`

| Mục | Giá trị |
|---|---|
| main / image | `a6e11bfd149baf5639d1d3e94ac547ef3d1c7628` / `la-lanh:a6e11bfd149b` (digest: chưa rõ) |
| Schema | `20261008_0028` → `20261011_0036` |
| Cờ đổi | Đăng nhập Google tắt (`auth_enabled=false`); viết bằng AI tắt |
| PR | #1 (fast-forward vào `main`) |
| Quay lại | `la-lanh:a7fadf7e4511`, cần trả lại file `database_url` cũ trước |
| Biên nhận | [production-release-2026-10-11](../reviews/production-release-2026-10-11/receipt.md) |

Người dùng sẽ thấy:
- Chưa rõ. Biên nhận chỉ ghi phần kỹ thuật: kết nối cơ sở dữ liệu an toàn hơn và có thêm môi trường staging riêng.
- Sự cố trong lúc phát hành: khoảng 11:05–11:33 UTC, một phần lượt dùng production bị chia sang staging, nên có thể
  gặp lỗi 401 hoặc CSRF. Không lộ dữ liệu giữa người dùng.

Kiểm: `pnpm check` đạt; diễn tập migration đạt; `smoke.sh` đạt trên staging và production; kiểm trên trình duyệt ở
390 px đạt. Journey: chưa có.

### 08.10.2026 — `a7fadf7e4511`

| Mục | Giá trị |
|---|---|
| main / image | `a7fadf7e45113e9a2be5cc9e2e7f7785bde56049` / `la-lanh:a7fadf7e4511` (`sha256:b2842068c398…`) |
| Schema | `20261008_0028` (khóa quyền đọc bảng từ trình duyệt bằng RLS) |
| Cờ đổi | Viết bằng AI và worker tắt |
| PR | Chưa rõ |
| Quay lại | `la-lanh:328c48e8906f` (ngay trước); `la-lanh:3798652ed4a3` (trước khi phát hành) |
| Biên nhận | [production-release-2026-10-08](../reviews/production-release-2026-10-08/receipt.md) |

Người dùng sẽ thấy:
- Home và Note dùng chữ nói thẳng.
- Hình trang trí chuyển động dừng được.
- Bước thêm giờ sinh có lựa chọn "không biết giờ" và ô đồng ý riêng, mặc định không tích.

Kiểm: `pnpm check` đạt; kiểm công khai từ đầu tới cuối với người giả đạt; trình duyệt 390 px không tràn ngang. Journey:
chưa có.

### Trước 08.10.2026

Chưa rõ. Không có biên nhận trong repo. Biên nhận 08.10 chỉ nhắc tới hai image cũ hơn: `la-lanh:3798652ed4a3` và
`la-lanh:328c48e8906f`.
