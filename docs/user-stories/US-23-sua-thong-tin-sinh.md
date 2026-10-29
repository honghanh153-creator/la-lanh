# US-23 — Sửa thông tin sinh sau khi đã lưu

> Nguồn: kế hoạch `docs/plans/2026-10-29-birth-data-edit-plan.md` (bản sửa sau Codex r52, quyết định D1–D6 do
> Claude chốt theo uỷ quyền của owner ngày 29/10/2026; owner có thể đổi bất kỳ quyết định nào). Story liên quan:
> US-02 (ngày sinh, cổng 18+), US-05 (lưu và chia sẻ), US-06 (giờ và nơi sinh), US-12/US-13 (Hợp gu).
> Ghi chú bàn giao và rà soát quyền riêng tư: `docs/plans/2026-10-29-us23-delivery-notes.md`.

## 1. User story

Là người đã có Lá Khai Sinh, tôi muốn sửa ngày sinh nhập nhầm, hoặc thêm, đổi, xoá giờ và nơi sinh, ngay trong
**Mình** mà không phải bắt đầu lại, để Lá và note nói đúng về mình. Trước khi xác nhận tôi thấy rõ cái gì sẽ đổi,
và sau đó không có dữ liệu cũ nào lẫn vào dữ liệu mới.

## 2. Phạm vi

**Bao gồm:**

- Dòng "Ngày sinh: dd/mm/yyyy · Sửa" trong Mình → Chiếc Lá của bạn, và dòng "Giờ và nơi sinh: … · Sửa" (hoặc
  "Chưa thêm · Thêm") tóm tắt lớp dữ liệu US-06 đang có. Tóm tắt chỉ nêu độ chính xác và thành phố ("đã có giờ
  sinh, Hà Nội"), không hiện giờ thô: trạng thái chung không bao giờ chứa giờ sinh; giờ chỉ có ở form sửa riêng.
- Sheet xác nhận, trang sửa (BirthDatePage ở chế độ sửa), API `PUT /v1/birth-profile/date`, giới hạn đổi, cổng
  18+, loại nhật ký xoá `birth_date_replaced`.
- Điều kiện tiên quyết: bản lưu và link chia sẻ sống lâu hơn nguồn của chúng (bỏ FK cascade, migration
  `20261029_0039`), và quản lý link chia sẻ: `GET /v1/share-artifacts` + mục "Link đã chia sẻ" trong Đã lưu.
- `POST /v1/birth-profile` từ chối đổi ngày khi đã có hồ sơ sinh đang dùng.

**Không bao gồm:**

- Hồ sơ thứ hai (US-01 cấm).
- Sửa dữ liệu của người khác trong Hợp gu/Radar.
- Sửa nội dung bản lưu hay link đã chia sẻ.
- Đổi hành vi của "Xóa giờ sinh"/"Xóa nơi sinh" (vẫn xoá note, bản lưu và link như đang báo — US-06).

## 3. Quyết định (D1–D6)

| # | Quyết định |
|---|---|
| D1 | Đổi ngày sinh là **thay thế**, không phải lịch sử. Xoá: mọi chart snapshot cũ, plan, revision, projection, note ngày (kèm mood và phản hồi gắn với note theo cascade), việc nhỏ, kết quả và lời mời Hợp gu có người này tham gia (cả hai phía), job viết lại đang chờ. Note hôm nay được tạo lại từ ngày mới. |
| D2 | **Bản lưu và link chia sẻ đã có được giữ** như bản đóng băng. Vẫn bỏ lưu được (Đã lưu) và thu hồi được (Đã lưu → Link đã chia sẻ). Sheet xác nhận nói rõ. |
| D3 | Giờ, nơi sinh và đồng ý dữ liệu sâu bị **xoá** khi đổi ngày; muốn thêm lại phải đồng ý lại. |
| D4 | `POST /v1/birth-profile` với ngày khác khi đã có hồ sơ sinh đang dùng → `409 BIRTH_DATE_CHANGE_REQUIRES_EDIT`. Chỉ `PUT /v1/birth-profile/date` được đổi. |
| D5 | Tối đa **3 lần đổi trong 24 giờ** mỗi người. |
| D6 | Cổng **18+** áp dụng y như lúc khai lần đầu: ngày dưới 18 tuổi (hoặc quá 120 năm) bị từ chối ở client trước khi gửi và ở service trước khi tính, không thay đổi gì, không lưu hay log giá trị bị từ chối, và gợi ý lối "Xóa Lá và dữ liệu". |

## 4. User flow

1. **Mình → Chiếc Lá của bạn**: "Ngày sinh: 12/03/2001 · Sửa"; dưới đó "Giờ và nơi sinh: đã có giờ sinh, Huế · Sửa"
   hoặc "Chưa thêm · Thêm" (mở `/birth-time`, US-06).
2. **Sửa ngày sinh** mở sheet:
   - Tiêu đề: "Đổi ngày sinh sẽ tạo lại Lá của bạn."
   - Sẽ thay đổi: Lá Khai Sinh, note hôm nay và gợi ý được tính lại; giờ và nơi sinh bị xoá, bạn có thể thêm lại;
     kết quả Hợp gu tạo từ ngày cũ bị xoá; **lời mời Hợp gu bạn đã gửi mà chưa được chấp nhận sẽ ngừng hoạt động,
     kể cả khi người nhận đã mở link** (Codex r54 P3).
   - Được giữ: note đã lưu và link đã chia sẻ. Bạn có thể bỏ lưu hoặc thu hồi link trong Đã lưu.
   - Nút: "Đổi ngày sinh" / "Giữ như cũ".
3. **Trang sửa** (`/birth?edit=1`): ngày hiện tại điền sẵn; trước khi gửi hỏi lại ngày một lần nữa để tránh gõ nhầm;
   kiểm tra 18+ trước khi gửi.
4. **Thành công:** sang trang reveal của Lá mới, kèm lời mời "Thêm giờ và nơi sinh để Lá rõ hơn". Web rút dữ liệu
   chart cũ khỏi bộ nhớ đệm (mục 8).
5. **Lỗi:** xem mục 6.
6. **Điều hướng:** `/birth` (không có `edit=1`) chuyển người đã có hồ sơ sinh đang dùng về Mình.
7. **Đã lưu → Link đã chia sẻ:** mỗi link hiện ngày tạo, ngày hết hạn và trạng thái; link còn hiệu lực có "Thu hồi
   link". Nút "Bỏ lưu" không bao giờ được ghi là thu hồi link.

## 5. Field và validation

| Field | Nơi | Ràng buộc |
|---|---|---|
| `birth_date` | body `PUT /v1/birth-profile/date` | Ngày ISO; tuổi 18–120 tính theo ngày hiện tại của server (UTC), cùng hàm với US-02; khác ngày đang lưu. |
| `confirm_birth_date` | body | Phải bằng `birth_date`, nếu không → `422 BIRTH_DATE_CONFIRMATION_MISMATCH`. Chỉ là kiểm tra gõ nhầm; server không lưu. |
| `expected_revision` | body | `profile_revision` (thời điểm cập nhật hồ sơ) đọc từ `GET /v1/birth-profile`. Khác giá trị hiện tại → `409 BIRTH_PROFILE_CHANGED`. |
| Phiên | cookie + `X-CSRF-Token` | Trusted Origin + CSRF bắt buộc; chủ sở hữu suy ra từ cookie, không từ body. Cần đồng ý `birth_profile_basic` còn hiệu lực. |
| Thân request | — | `extra="forbid"`; không nhận field khác. Không có ngày trong URL hay query. |
| `limit` | query `GET /v1/share-artifacts` | 1–50, mặc định 20. |
| `cursor` | query | Chuỗi mờ do server cấp (`next_cursor`); sai định dạng → `422 SHARE_CURSOR_INVALID`. |

### Thứ tự kiểm tra của `PUT /v1/birth-profile/date`

1. Trusted Origin, CSRF, phiên, đồng ý cơ bản.
2. `confirm_birth_date` khớp.
3. Tuổi 18–120 (D6) — **trước** mọi đọc/ghi/tính.
4. Có hồ sơ sinh đang dùng (nếu không → `404 BIRTH_PROFILE_NOT_FOUND`; khai lần đầu dùng `POST`).
5. Khác ngày đang lưu (nếu không → `409 BIRTH_DATE_UNCHANGED`).
6. `expected_revision` khớp; còn lượt D5.
7. Tính chart ngày mới và mã hoá (pha 1, không giữ khoá ghi).
8. Một transaction dưới khoá dòng guest (pha 2): kiểm tra lại revision, D5 và ngày; ghi nhận các lượt gửi provider
   đã được nhận; xoá D1; xoá giờ/nơi/đồng ý sâu; kích hoạt snapshot mới; ghi lượt đổi; ghi nhật ký
   `birth_date_replaced`; commit.
9. Sau commit (pha 3): chờ mọi lượt gửi provider đã ghi nhận kết thúc, rồi mới trả thành công.

## 6. Mã lỗi và thông điệp

| Tình huống | HTTP / code | Thông điệp web |
|---|---|---|
| Ngày giống ngày đang lưu | `409 BIRTH_DATE_UNCHANGED` | "Ngày này đã được lưu." |
| Dưới 18 hoặc quá 120 năm | `422 BIRTH_DATE_OUT_OF_RANGE` | "Lá Lành hiện dành cho người từ 18 tuổi." + lối "Xóa Lá và dữ liệu" |
| Hai ô ngày không khớp | `422 BIRTH_DATE_CONFIRMATION_MISMATCH` (client chặn trước) | "Hai lần nhập chưa giống nhau. Kiểm tra lại nhé." |
| Revision cũ (tab khác vừa sửa) | `409 BIRTH_PROFILE_CHANGED` | "Hồ sơ vừa được cập nhật ở nơi khác. Mình đã tải lại ngày hiện tại." |
| Quá 3 lần/24 giờ | `429 BIRTH_DATE_CHANGE_LIMITED` | "Bạn đã đổi ngày sinh vài lần hôm nay. Thử lại sau nhé." |
| Engine bận / không có | `429 BIRTH_CHART_BUSY`, `503 CHART_ENGINE_UNAVAILABLE` | "Chưa tính được Lá mới. Lá cũ vẫn giữ nguyên." |
| `POST` đổi ngày khi đã có hồ sơ | `409 BIRTH_DATE_CHANGE_REQUIRES_EDIT` | (web không gọi `POST` khi đã có hồ sơ) |

Không body lỗi nào chứa ngày, giờ, nơi sinh hay giá trị chart.

## 7. Edge cases

| Tình huống | Rủi ro | Cách xử lý |
|---|---|---|
| Hai tab cùng sửa | Tab sau ghi đè tab trước | Revision fence trong transaction; tab thua nhận `409` và tải lại ngày hiện tại. |
| Bấm gửi hai lần / retry mạng | Đổi hai lần, tốn lượt | Lần hai có revision cũ → `409`; không xoá thêm, không tính lượt. |
| Engine lỗi giữa chừng | Mất chart cũ | Pha 1 không ghi gì; Lá cũ và mọi dữ liệu giữ nguyên (US-02 `:246`). |
| Lỗi trong pha 2 | Xoá nửa chừng | Một transaction; rollback toàn bộ, kể cả nhật ký và lượt đếm. |
| Job Luna đang gửi provider lúc đổi | Bản viết lại của ngày cũ hiện sau khi đổi | Lượt gửi được ghi nhận trong khoá và chờ xong trước khi trả thành công; kết quả muộn của job đã xoá bị loại bởi lease/epoch của worker. |
| Bỏ lưu lúc offline rồi đổi ngày | Mất yêu cầu bỏ lưu, bản lưu còn trên server | Web chỉ bỏ các lệnh *lưu* đang chờ; lệnh *bỏ lưu* được giữ và gửi lại theo `daily_note_id` của bản lưu còn giữ. |
| Link chia sẻ tạo trước khi đổi | Không tìm lại được để thu hồi | Liệt kê trong Đã lưu → Link đã chia sẻ; thu hồi bằng id như mọi link. |
| Lời mời Hợp gu chưa được chấp nhận (kể cả đã mở) | Người nhận mở link hỏng | Sheet báo trước; lời mời bị xoá, link trả lời như link không tồn tại. |
| Người kia trong kết quả Hợp gu | Thấy kết quả biến mất | Kết quả bị xoá ở cả hai phía, không nêu lý do (như khi xoá giờ/nơi sinh). |
| Đổi lần thứ 4 trong 24 giờ | "Chart shopping", lách tuổi | `429`, không đổi gì. |
| Người thực sự dưới 18 | Bị giữ trong sản phẩm 18+ | Từ chối như onboarding, không xoá dữ liệu vì một lần gõ nhầm; gợi ý "Xóa Lá và dữ liệu". |
| Khôi phục bản sao lưu trước khi đổi | Ngày cũ quay lại | Replay `birth_date_replaced` xoá chủ thể cũ và phụ thuộc, để **không có hồ sơ sinh đang dùng**; lần mở sau app hỏi lại ngày sinh (`POST` chấp nhận vì không còn chủ thể). |
| Khôi phục bản sao lưu sau khi đổi | Replay xoá nhầm ngày mới | Dòng nhật ký đã nằm trong bản sao (checkpoint) → báo `reflected`, không chạm ngày mới. |
| Xoá giờ/nơi sinh sau khi đổi ngày | Bản lưu tách nguồn còn sót | Xoá giờ/nơi sinh xoá **mọi** bản lưu và link của người này, kể cả bản tách nguồn, đúng như câu xác nhận. |
| Xoá hồ sơ khách | Bản lưu tách nguồn mồ côi | FK `guest_id` vẫn cascade; xoá guest xoá mọi bản sao. |

## 8. Bộ nhớ đệm web sau khi đổi

Không dùng `clearChartDerivedData` vì nó xoá cả lệnh bỏ lưu đang chờ. Hàm rút riêng cho việc đổi ngày:

- tăng chart revision fence để callback cũ không tạo lại dữ liệu chart;
- huỷ và reset các query suy ra từ chart;
- xoá bản đọc hằng ngày đang hoạt động và note hôm nay đã cache;
- bỏ các lệnh **lưu** đang chờ (`dropQueuedSaves`) vì chúng trỏ tới note cũ;
- **giữ lệnh bỏ lưu** và gửi lại;
- tải lại danh sách bản lưu và link chia sẻ thay vì xoá chúng khỏi máy.

## 9. API contract

```
PUT  /v1/birth-profile/date      { birth_date, confirm_birth_date, expected_revision }
     → 200 BirthRevealResponse (+ profile_revision), Cache-Control: no-store
     admission: birth-compute bucket; D5: 3 lần / 24 giờ / người
POST /v1/birth-profile           → 409 BIRTH_DATE_CHANGE_REQUIRES_EDIT khi đã có chủ thể và ngày khác
GET  /v1/birth-profile           → thêm profile_revision (dùng làm expected_revision)
GET  /v1/share-artifacts?limit=&cursor=
     → { items: [{ id, format, status: active|revoked|expired, created_at, expires_at, revoked_at }], next_cursor }
     chỉ link của phiên hiện tại; không token, không nội dung, không daily_note_id; no-store; admission share-list
DELETE /v1/share-artifacts/{id}  (đã có) thu hồi, kể cả link đã tách nguồn
```

## 10. Acceptance Criteria

- **AC1:** Có hồ sơ đã lưu → Mình hiện ngày đã lưu với "Sửa". Chưa có giờ/nơi → hiện "Chưa thêm".
- **AC2:** Xác nhận ngày mới → chart mới đang dùng; snapshot, plan, revision, projection, note ngày, kết quả và lời
  mời Hợp gu tạo từ ngày cũ, job viết lại đều không còn; giờ, nơi, đồng ý sâu bị xoá; bản lưu và link chia sẻ còn,
  vẫn bỏ lưu/thu hồi được.
- **AC3:** Ngày giống ngày đang lưu → không đổi gì, người dùng được báo.
- **AC4:** Revision cũ từ tab khác → `409`, không đổi gì, trang tải lại ngày hiện tại.
- **AC5:** Lần đổi thứ tư trong 24 giờ → server từ chối, chart cũ giữ nguyên.
- **AC6:** Tính chart lỗi → chart cũ và dữ liệu của nó giữ nguyên.
- **AC7:** Đã có chủ thể sinh đang dùng → `POST /v1/birth-profile` với ngày khác trả
  `409 BIRTH_DATE_CHANGE_REQUIRES_EDIT`.
- **AC8:** Khôi phục và replay:
  - Bản sao lưu trước khi đổi, khôi phục sau khi đổi → replay xoá chủ thể cũ và phụ thuộc, không còn chủ thể sinh
    đang dùng; app hỏi lại ngày sinh. Nhật ký không chứa giá trị sinh nào.
  - Bản sao lưu sau khi đổi → replay để nguyên chủ thể mới.
- **AC9:** Ngày mới dưới 18 (hoặc quá 120 năm) → trang từ chối trước khi gửi và service từ chối trước khi tính, với
  thông điệp onboarding; không đổi gì (ngày, chart, Matching, dữ liệu); trang gợi ý "Xóa Lá và dữ liệu"; ngày bị
  từ chối không được lưu hay log.
- **AC10:** Không có ngày, giờ, nơi sinh trong log, URL hay body lỗi.
- **AC11:** Có lượt gửi provider được nhận trước khi đổi → thành công chỉ trả sau khi lượt đó kết thúc; sau đó
  không có văn bản nào của chủ thể cũ được công bố.
- **AC12:** Link chia sẻ tạo trước khi đổi → sau khi đổi và tải lại vẫn được liệt kê trong Đã lưu và thu hồi được;
  link công khai sau đó trả lời như link đã thu hồi.
- **AC13:** Lệnh bỏ lưu xếp hàng lúc offline trước khi đổi → sau khi đổi và tải lại, lệnh tới được server.
- **AC14:** Có lời mời Hợp gu chưa được chấp nhận (kể cả đã được mở) → sheet xác nhận nói nó sẽ ngừng hoạt động
  trước khi người dùng xác nhận.

## 11. Definition of Done

- Mọi AC có test; AC2, AC4, AC8, AC11 và migration vòng đời có test PostgreSQL (dạng gated, chạy trên probe dùng
  một lần theo `docs/operations/disposable-postgres-journal-probe.md`).
- Codex APPROVE ở từng SHA chính xác.
- Tài liệu, privacy copy và data map khớp hành vi runtime; khai báo store không đổi loại dữ liệu (kiểm lại khi
  release).
- Experience audit và content audit qua; copy pass cho các chuỗi mới (kể cả dòng lời mời Hợp gu).
- Kiểm thử trên bản native (thiết bị) cho sheet, trang sửa và việc rút cache.
- Migration `20261029_0039` và `20261029_0040` được deploy trước khi bật màn sửa ngày; release vẫn cần lệnh owner.
