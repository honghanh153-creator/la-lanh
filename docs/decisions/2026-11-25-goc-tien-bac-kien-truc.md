# Góc Tiền bạc: kiến trúc và bản đồ dữ liệu (#709)

Ngày: 25.11.2026. Người thực hiện tài liệu: Codex theo kế hoạch đã thống nhất với người phản biện. Review độc lập đúng bản thay đổi: chưa có.

## 1. Phạm vi và trạng thái

Quyết định này chốt thiết kế cho tuần 2 của [kế hoạch 7 tuần](../plans/2026-11-15-ke-hoach-7-tuan-moc-do.md), điều kiện bắt đầu số 5, hub [#686](https://github.com/honghanh153-creator/la-lanh/issues/686), task [#709](https://github.com/honghanh153-creator/la-lanh/issues/709). Chỉ sửa quyết định và [bản đồ dữ liệu](../legal/store-privacy-data-map.md#money-context-design-delta--2026-11-25-not-implemented). Chưa thêm enum vào code, API, UI, schema, consent hay cờ; chưa thu dữ liệu thật, chưa cho phép bật hoặc phát hành.

Issue ghi cỡ S; áp dụng mức thẩm định M cho phần tài liệu theo kế hoạch đã chốt, có G1/G4/G6/G7/G8 và threat model ở mục 5. Phần runtime sau này đổi API và dữ liệu cá nhân phải phân loại L theo [quy trình](../operations/product-development-process.md), không kế thừa nhánh docs-only để giảm cổng. G2/G3/G5 được bàn giao, G9 chưa thực hiện, G10 không có dịch vụ/chi phí/quyền mới. Theo [checklist](../operations/decision-checklist.md), Q2/Q3 có điều kiện trước bật; Q1/Q4/Q5 không phát sinh hành động bị cấm trong thay đổi tài liệu này. Áp dụng R1–R17 từ [luật đang hiệu lực](../operations/luat-dang-hieu-luc.md).

Mốc mã đã đối chiếu tại máy: `d3818f59b47cccccd8d59560fcb5e3d9625a294c`, nhánh `agent/codex/issue-709`. Checkout sạch trước sửa. Theo lệnh không mạng, không chạy inbox vì script gọi `gh`, không tra GitHub/nguồn ngoài, không ghi Issue/PR, commit/push hoặc sync. Kế hoạch và phản biện trong yêu cầu là hồ sơ bàn giao, không phải bằng chứng đã kiểm lại nguồn gốc. Không kết luận không có việc trùng. Khi được nối mạng phải kiểm inbox, [#710](https://github.com/honghanh153-creator/la-lanh/issues/710), [#711](https://github.com/honghanh153-creator/la-lanh/issues/711), [#712](https://github.com/honghanh153-creator/la-lanh/issues/712), [#690](https://github.com/honghanh153-creator/la-lanh/issues/690) và [verdict PR #395](https://github.com/honghanh153-creator/la-lanh/pull/395#issuecomment-6765202453) trước bàn giao trên GitHub. Không coi AC4/G1 nghiên cứu ngoài đã PASS trong lượt offline này.

## 2. Hợp đồng lựa chọn và nội dung (AC1, AC3)

Thiết kế thêm `money` vào `BackgroundLens` cùng trường `money_situation` có đúng bốn giá trị:

| Chuyện trong yêu cầu | Mã kỹ thuật |
|---|---|
| Thiếu học phí hoặc tiền nhà | `tuition_or_rent_shortfall` |
| Cuối tháng cạn | `month_end_shortfall` |
| Phải gửi tiền về nhà | `family_remittance` |
| Bị rủ đi chơi tốn tiền | `costly_social_invitation` |

Bảng chép yêu cầu và đặt mã kỹ thuật, chưa phải nhãn giao diện được duyệt. Mọi câu mới để `status: pending`; câu chưa duyệt không được phục vụ. #709 không soạn câu privacy/consent/crisis/safety mới.

Lựa chọn chỉ gửi cho lần đọc đang yêu cầu qua POST context riêng, kế thừa US-03 AC23:

```json
{
  "background_lens": "money",
  "money_situation": "family_remittance"
}
```

- `money` bắt buộc đúng một chuyện con, không chọn sẵn. Lens khác không nhận `money_situation`.
- Payload cũ, gồm `voice`, giữ hợp lệ và hành vi cũ. `ContextProjectionRequest` hiện đã có `extra="forbid"`; giữ quy tắc tại DTO đó, không siết thêm DTO khác.
- Từ chối mã lạ, mảng, số tiền, free text và trường ngoài contract. Lỗi không trả lại giá trị, request body hay validation context riêng tư.
- Không hỏi số tiền, không suy luận lựa chọn từ ngày sinh, mood, lịch sử, feedback hay bản đọc trước. Không tạo preference hoặc tự chọn lại ở lần đọc sau.
- Sau khi chọn, `family_remittance` và `costly_social_invitation` vẫn không có nghĩa là thiếu tiền, mắc nợ hay khủng hoảng. Không suy ra thu nhập, tài sản, nợ, hoàn cảnh gia đình hoặc kết quả tài chính. Không trách người giữ tiền, dự đoán sự kiện đời người hay khuyên quyết định tài chính lớn.
- Chuyện con chỉ đổi cách thể hiện và việc nhỏ; chart facts, factors, evidence, precision, confidence và nguồn kiến thức giữ nguyên theo US-03 AC22.
- Chỉ tạo `money` cho `ReadingPurpose.DAILY_NOTE`. Tầng application dùng chung phải từ chối `money` ở `AURA`, `READING_DETAIL`, `PERSONALIZED_SKY`; mở enum không tự mở mọi consumer.
- Bộ dựng nội dung xác định sẵn trên máy chủ `apps/api`, không gọi LLM/AI, dùng câu đã duyệt của #710. Chặn AI ở application enqueue, worker và adapter/provider, kể cả khi consent AI chung đang bật.

#710 kiểm từng note, việc nhẹ và việc thường theo AC3 sau lựa chọn, phối hợp #705. #711 sinh lại OpenAPI/client types; #712 dùng kiểu sinh từ contract. Đây là việc bàn giao, chưa có bằng chứng chạy `money`.

## 3. Lưu dữ liệu và lựa chọn thay thế (AC2)

| Phương án | Lợi ích | Đánh đổi |
|---|---|---|
| Chỉ RAM, không lưu mã hoặc nội dung theo chuyện tiền | Ít dữ liệu lưu nhất | Không đọc lại/lưu đúng bài đã thấy; cần đường đọc tạm thay cho luồng revision hiện tại |
| Bỏ mã chuyện con, giữ prose trong revision | Giảm một trường đầu vào | Prose vẫn tiết lộ chuyện tiền, vẫn tạo lịch sử; vẫn cần consent, privacy, xóa và khai báo store |
| Giữ mã và prose trong plan/revision mã hóa hiện có | Đọc lại đúng revision, replay, lưu riêng và xuất cho chính chủ | Có lịch sử hoàn cảnh tiền; phải bảo vệ cả metadata, vòng đời và reader khi rollback |

Chọn phương án thứ ba trong phạm vi encrypted plan/revision được [US-03 §21, AC23](../user-stories/US-03-doc-note-hom-nay.md#21-canonical-delta--personal-signal-daily-note-2026-09-14) cho phép. Đọc lại đúng bản đã thấy là lý do giữ luồng revision hiện có; không tạo thêm loại bài đọc tạm với hành vi lưu/xuất khác.

Có lịch sử lựa chọn và nội dung liên quan tiền trong revision còn giữ. Không tuyên bố chuyện tiền không bị lưu. Không tạo bảng lịch sử lựa chọn, hồ sơ sở thích, thống kê hoàn cảnh tiền hoặc tự học. Mục tiêu là giới hạn nơi lưu, quyền truy cập và nơi gửi tiếp. Mã hóa không phải quyền bật thu dữ liệu: R2 vẫn chặn trước khi có owner cho phép.

Mã chuyện và prose chỉ nằm trong envelope plan/revision và bản lưu mã hóa hiện có; lựa chọn chưa gửi chỉ trong memory. Nếu phải thêm nơi lưu chuyện con hoặc dấu suy ra ngoài cơ chế góc hiện có, dừng phần đó theo AC2/điều kiện số 5, ghi khoảng trống cần owner. Đổi tên hoặc băm trường không tránh điều kiện dừng. Receipt consent tối thiểu ở mục 6 được kê riêng; không chứa chuyện con.

## 4. Replay và metadata có khóa (AC2)

Hiện `canonical_lens_variant` băm lens bằng SHA-256; `canonical_reading_plan_key` băm toàn bộ plan; scope/revision cũng có canonical hash. Chỉ sửa lens hoặc scope vẫn để chuyện con đi vào hash toàn plan. Tập bốn giá trị có thể bị thử; hash không phải ẩn danh.

Chọn HMAC-SHA-256 có khóa máy chủ cho toàn bộ định danh mới phụ thuộc `money`, tái sử dụng `guest_hash_key` và mẫu tách miền `SecretHasher` hiện có. Khóa bí mật tách khỏi DB là điều kiện bảo vệ khi chỉ DB bị lộ. Không thêm dịch vụ, secret hoặc IAM. Đây là quyết định thiết kế dựa trên mẫu code hiện có; nguồn RFC cần kiểm lại ở mục 8.

1. Dùng miền riêng cho `lens_variant`, `scope_key`, `plan_key`, `revision_key`. Đầu vào canonical có phân cách rõ, ràng buộc chủ, profile, nguồn chart, ngày/scope thời gian, purpose, chuyện con và phiên bản nội dung liên quan. Không dùng cùng thông điệp cho nhiều mục đích.
2. Cả `plan_key`, `revision_key` và mọi fingerprint dẫn xuất phụ thuộc `money` phải có khóa; không đưa mã chuyện hoặc toàn plan trở lại hash không khóa.
3. Dùng các cột sẵn có `lens_variant`, `scope_key`, `plan_key`, `revision_key` với định dạng 64 ký tự hex hiện có. Không thêm cột chuyện con, bảng dedupe hay index hoàn cảnh tiền.
4. Scheme/phiên bản khóa để kiểm đọc lại nằm trong payload mã hóa. Version renderer/content/schema ở cột công khai không được phân biệt từng chuyện con. Khóa để đọc các bản còn hạn phải còn khả dụng; không rekey lúc người dùng mở bài.
5. Giữ nguyên canonical key và cách đọc lens cũ; trường mới vắng mặt không làm đổi danh tính bản ghi cũ. Không để null/default mới lọt vào serialization canonical của bản cũ.
6. Sửa đồng bộ tạo khóa, record validation, repository và đối chiếu projection/revision. Không bỏ kiểm danh tính để reader chấp nhận khóa mới. Thiếu khóa hợp lệ thì từ chối; không fallback sang hash không khóa.

Replay bắt buộc: cùng chủ/nguồn chart/ngày/chuyện/phiên bản nội dung trả đúng revision; đổi chuyện không lấy bài trước; khác chủ không dùng chung dấu; đồng thời cùng scope không tạo hai active hoặc trả nhầm nội dung. Sau rút rồi đồng ý lại không tái sử dụng dữ liệu đã xóa.

Các HMAC vẫn là metadata cá nhân có thể liên kết, cho thấy sự lặp lại. Khi DB và khóa cùng lộ, kẻ tấn công có thể thử tập giá trị. Không log, xuất hoặc gửi HMAC sang AI. Nếu #711 không làm được trong vị trí metadata hiện có, hoặc cần secret/IAM mới, giữ tắt ghi mới và bàn giao owner; không tự tạo nơi lưu mới.

## 5. Ranh giới downstream và threat model (AC2, G7/G8)

| Đường dữ liệu | Quyết định thiết kế |
|---|---|
| POST context | Kiểm chủ, CSRF/trusted Origin, giới hạn lạm dụng, input đóng, cờ và consent trước lập plan hoặc ghi |
| Plan/revision | Envelope mã hóa; kiểm AAD, chủ và nguồn dữ liệu; dữ liệu sinh/chart không có thêm bản sao do `money` |
| Client | Chỉ memory gắn phiên/request; hủy hoặc chặn response cũ khi đổi phiên, rút consent hay rời luồng |
| Cache | Không Web Storage, IndexedDB, service worker, Capacitor Preferences hay HTTP cache cho `money`, kể cả ID của ý định lưu offline |
| Lịch sử | Chính chủ đọc revision còn được giữ; không dùng để gợi ý lại chuyện con |
| Lưu riêng | Giữ đúng revision trong bản lưu mã hóa hiện có; không có nhãn hoàn cảnh tiền plaintext |
| Xuất dữ liệu của tôi | Chỉ lựa chọn và nội dung còn thuộc phạm vi xuất của chính chủ; không internal plan, ID, HMAC, token hay dữ liệu người khác |
| Log/trace/báo lỗi/analytics | Không mã chuyện, prose, body, HMAC hay exception chứa chúng |
| AI/bên thứ ba | Không job/enqueue/worker/adapter/provider nhận dữ liệu `money`. Hosting hiện có vẫn là bên xử lý dữ liệu, không được coi là đã loại mọi chuyển xuyên biên giới |

### Chia sẻ, link và ảnh

Không chia sẻ revision `money`. Dựng lại bản nền không có góc tiền từ dữ kiện nền được phép dùng, rồi preview trước khi người dùng xác nhận. Không lấy snapshot bài tiền rồi chỉ xóa `money_situation`: hook, manifestation, action và nội dung suy ra đều không tái sử dụng. Share record không tham chiếu revision `money`. API kiểm nguồn revision, từ chối cả ID bài tiền đi kèm lens giả. Giữ bảo vệ capability token, thu hồi link, no-cache/no-index/no-referrer hiện hành.

Đây là khác biệt với yêu cầu snapshot đúng bài đã thấy của [US-05](../user-stories/US-05-luu-va-chia-se-note.md). Không tự gọi bài nền là bài tiền đã chia sẻ. G1 phải chốt delta hợp đồng/preview trước bật; chưa sửa US trong #709.

### Việc đang giữ và phản hồi

Việc nhẹ/thường của #710 được hiển thị trong bài tiền, nhưng không ghi việc đó, action key hoặc revision `money` vào bảng việc đang giữ. Muốn giữ việc nền phải mở bản nền và xác nhận việc đang thấy. Không âm thầm đổi việc khi bấm giữ. API kiểm provenance revision thay vì tin lens client.

Không ghi feedback cho revision `money` trong đợt này, kể cả chỉ `revision_id` hoặc digest. Không gán feedback bài tiền sang bài nền. UI không hiện nút gửi feedback trực tiếp trên bài tiền. Feedback nền giữ consent/TTL/reset/revoke hiện có.

[US-03 AC25/AC29 và §22, AC33–35](../user-stories/US-03-doc-note-hom-nay.md) yêu cầu feedback và giữ việc trên Note. Các giới hạn trên là khoảng trống hợp đồng chặn bật, không phải xác nhận đã đáp ứng US hoặc tự cắt yêu cầu. G1 phải giải quyết/ghi delta được review; #711 không tự chọn lại ranh giới lưu.

### Cache, export và native

`Cache-Control: no-store` cho mọi phản hồi riêng có dữ liệu `money`: POST context, GET chi tiết, lịch sử, bản lưu, export và lỗi tương ứng. Client dùng chế độ không cache. Không ETag/304 giữ lại nội dung. Cờ tắt không làm các đường đọc cũ mất bảo vệ này.

File chính chủ tải là ngoại lệ lưu thiết bị có chủ đích. Không giữ bản sao server; filename cố định không chứa chuyện tiền. Native dùng file tạm app-private cache và dọn sau share sheet, kể cả hủy/lỗi, theo contract export hiện có. Lỗi dọn không được coi đã xóa; kiểm riêng trên iOS/Android, kể cả backup thiết bị, WebView cache, quyền và chuyển phiên. Không xin quyền nền tảng mới trong thiết kế này. MASVS/MASTG và logging sources ở mục 8 là căn cứ kiểm bàn giao.

| Đe dọa/đường hỏng | Biện pháp phải chứng minh trước bật |
|---|---|
| Người khác dùng ID/phiên cũ đọc bài | Owner/source check, chống enumeration, hủy response cũ, a11y không đọc nội dung cũ |
| Đoán bốn mã từ DB metadata | HMAC mọi định danh phụ thuộc, phân miền/chủ/scope; kiểm DB không có plaintext/hash tập đóng |
| Bài tiền lọt qua share/giữ việc/feedback hoặc cache | Kiểm provenance ở server, dựng nền mới/preview, từ chối ghi downstream; no-store và canary prose |
| AI chung bật hoặc lỗi validation ghi dữ liệu | Chặn tại application/worker/provider; lỗi redact; canary log/network/báo lỗi |
| Withdraw đua với read/write; restore hồi sinh dữ liệu | Khóa/phiên bản quyền chung, chặn truy cập trước dọn, journal và retry, kiểm restore |
| Rollback reader không hiểu enum/khóa mới | Giữ reader tương thích và sàn SHA, diễn tập có bản mới; không bỏ identity validation |

Không thêm auth/session, crypto implementation, dependency, storage service hoặc endpoint public trong #709. Test tĩnh hiện có không chứng minh threat model `money` đã đạt.

## 6. Consent, withdrawal và retention (AC4)

Consent riêng cho `money` là đầu việc còn thiếu trong chuỗi #709–#712. Consent birth-profile hoặc AI không đủ. Bàn giao dự kiến: Claude triển khai consent API/UI và tests; Codex review. Đây là phân công đề xuất cho task chưa tạo, phải xác nhận khi lập Issue, chưa có số Issue hoặc cam kết đã nhận việc. R2 chặn bật trước approval dữ liệu mới.

AC của đầu việc consent:

- Owner cung cấp/duyệt chữ `/privacy`, disclosure và consent. #709 chỉ ghi yêu cầu kỹ thuật, không soạn câu mới.
- UI thông báo trước lần gửi lựa chọn đầu tiên, không đồng ý sẵn; từ chối vẫn đọc bản nền. Chữ/version chưa duyệt không được nhận consent.
- API accept/status/withdraw có owner, CSRF/Origin và phiên bản được duyệt; server kiểm consent hiện hành mỗi lần tạo, không tin cờ client.
- Tái sử dụng bảng `consents`, purpose dự kiến `money_context`, với chủ, purpose, version, `accepted_at`, `revoked_at`. Không chuyện con, số tiền hay revision. Version trỏ tới nội dung duyệt bất biến để chứng minh đã đồng ý điều gì. Bảng có trường cần thiết, chưa chốt thêm schema; cần thêm trường/nơi lưu phải thiết kế/review trước, không dùng log thay bằng chứng.
- Receipt là dữ liệu mới, mặc định tắt, có dòng riêng ở data map. Giữ trạng thái tối thiểu theo vòng đời consent/hồ sơ hiện hành; xóa guest cascade receipt. Chưa chốt đủ bằng chứng thời hạn thực tế trước bật, không tự đặt TTL mới hoặc giữ prose làm bằng chứng.
- Test cancel ghi zero rows, missing/stale/revoked version, gọi trực tiếp, khác chủ, rút trong request đang chạy, đồng ý lại và xóa tài khoản. Cờ tắt không nhận receipt mới.

### Rút đồng ý

1. Ngừng xử lý mới ngay, chặn request đang chờ ghi hoặc trả dữ liệu sau mốc rút.
2. Gỡ quyền hiển thị và xóa plan/revision `money`, projection, bản lưu riêng và bản sao phụ thuộc do app giữ. Không xóa bản nền/chart/tài khoản chỉ vì rút consent tiền.
3. Dọn memory/file tạm app kiểm soát. Không hứa xóa file chính chủ đã lưu ngoài app.
4. Tái sử dụng erasure journal để xóa lại sau restore, không ghi chuyện con. Giữ tối thiểu trạng thái đã rút theo vòng đời consent hiện có.
5. Nếu dọn lỗi, trạng thái đã rút vẫn chặn nội dung, có retry; không báo đã xóa xong sớm. Read/write/withdraw dùng cùng khóa hoặc phiên bản quyền để request cũ không ghi lại dữ liệu. Đồng ý lại không hồi sinh dữ liệu đã xóa.

Đây là lựa chọn sản phẩm cần phản ánh trong chữ owner duyệt, không phải khẳng định pháp luật buộc mọi withdrawal xóa tức thời.

### Thời hạn và backup

Kế thừa vòng đời đang mô tả ở [data map](../legal/store-privacy-data-map.md#accounthistory-delta--2026-10-10-not-a-store-submission): Daily history tự động hiển thị tối đa 24 giờ, đủ điều kiện dọn từ 18 giờ khi không còn Note hôm nay, job mỗi sáu giờ. Chưa chứng minh hạn xóa vật lý tuyệt đối 24 giờ. Note hiện tại/bản lưu có ngoại lệ theo vòng đời hồ sơ; không kéo dài hạn vì xem lại, đổi góc hoặc thêm `money`.

Root có thể bị giữ ẩn khi con còn hạn. `money` không tạo con share/experiment/feedback để kéo dài root. Hồ sơ legacy chưa có retention policy không được ghi `money` tới khi policy có hiệu lực rõ; không tự nhận consent lịch sử. Backup có vòng đời riêng; thời hạn và restore của mọi bên xử lý chưa xác minh đủ là điều kiện chặn bật. Journal hiện mô tả mặc định 15 ngày và ít nhất phủ backup còn phục hồi; phải đối chiếu cấu hình thực tế, không suy từ code ra vận hành.

## 7. Pháp luật, tuổi, store và /privacy (AC4)

Lựa chọn gắn hồ sơ, prose suy ra và HMAC đều là dữ liệu cá nhân theo thiết kế, kể cả khi mã hóa. Không mặc nhiên coi bốn mã là dữ liệu khách hàng tổ chức tín dụng. Dự án áp dụng mức bảo vệ nhạy cảm vì có thể tiết lộ đời sống riêng tư; phân loại pháp lý cuối cùng cần đối chiếu nguồn chính thức.

Hồ sơ pháp luật trong repo có [bảng nguồn ngày 26.10](../legal/2026-10-26-game-line-dpia.md#1-nguồn-pháp-luật-đã-kiểm-tra-26102026), đã đọc lại offline. Luật 91/2025/QH15 Điều 9/11 là điểm đối chiếu consent trước thu; Điều 20–22 là chuyển xuyên biên giới và hồ sơ tác động; Điều 24 là trẻ em. Nghị định 356/2025/NĐ-CP Điều 4/6 là phân loại và consent kiểm chứng được. Đây là dẫn chiếu từ hồ sơ cũ/kế hoạch, chưa phải lần kiểm luật hiện hành 25.11; nguồn gốc ở mục 8 cần mở và đối chiếu trước bật, không tự nhận tuân thủ pháp luật.

Hosting ngoài Việt Nam vẫn cần hồ sơ chuyển dù không gọi AI. Trước bật phải xác định hồ sơ đánh giá tác động xử lý/chuyển cần lập mới hay cập nhật, đơn vị chịu trách nhiệm và bằng chứng thực hiện. Không tự nhận miễn trừ doanh nghiệp nhỏ khi xử lý có thể nhạy cảm; thiếu bằng chứng thì giữ tắt.

Giữ 18+ theo US-02, `/privacy` trong `ConsentPage.tsx` và `_require_adult_date` trong `birth/service.py`, cùng kiểm sửa ngày sinh US-23. Học phí không chứng minh là trẻ em hay đã thành niên. Kiểm gọi trực tiếp, legacy và sửa ngày sinh; không thu thêm giấy tờ/tuổi/người đại diện. Muốn mở cho người chưa thành niên phải có việc riêng/owner duyệt. Luật Trẻ em Điều 1 phân biệt trẻ dưới 16, không gộp mọi người dưới 18 thành cùng một nhóm pháp lý; bản hợp nhất chính thức cần kiểm lại.

Phân loại store cụ thể được ghi ở data map: chuyện tiền là Apple Financial Info → Other Financial Info, Google Financial info → Other financial info; prose là Other User Content/Other Data Types và Other user-generated content, kèm tài chính khi tiết lộ hoàn cảnh; metadata/receipt là User ID/Product Interaction và User IDs/App interactions theo dữ liệu thực tế. Đây là phân loại thận trọng của dự án, không phải store nêu đích danh bốn mã.

Khi bật: collected có, linked có cả guest, optional, mục đích App Functionality/Product Personalization, không tracking/quảng cáo, không ephemeral vì có lưu. Google Shared dự kiến không, chỉ chốt sau khi xác minh bên hạ tầng đạt ngoại lệ service provider. HTTPS/TLS và đường deletion/withdrawal cần kiểm bản phát hành. Không tự coi mã hóa là miễn collection. Apple/Google nguồn hiện hành chưa được kiểm trong lượt offline.

`/privacy` cần bổ sung trước bật: loại dữ liệu, mục đích, nơi xử lý, lịch sử mã hóa, metadata, retention, quyền rút/xóa/xuất và giới hạn share/giữ việc/feedback. Chủ trương này chưa phải câu privacy mới, và #709 không sửa trang đó. Owner phải duyệt nội dung. Store form/manifest cần khớp binary và cấu hình bật thực tế, không đổi khai báo bản hiện hành chỉ vì có tài liệu dự kiến.

## 8. Nghiên cứu G1 và nguồn (AC5)

### Đã đọc tại máy trong lượt này

| Nguồn | Phần đã đối chiếu và kết luận dùng trong quyết định |
|---|---|
| [PRD §7.2](../foundation/la-lanh-prd.md), [SRS §7](../foundation/la-lanh-srs.md), [product plan §7](../foundation/la-lanh-product-plan-v2.md) | Consent riêng/version hóa; encrypted private data và export chính chủ; không gom dữ liệu cho mục đích tương lai |
| [US-03 §21–23](../user-stories/US-03-doc-note-hom-nay.md), [US-05](../user-stories/US-05-luu-va-chia-se-note.md), [US-02](../user-stories/US-02-khai-ngay-sinh-reveal-la-khai-sinh.md), [US-23](../user-stories/US-23-sua-thong-tin-sinh.md) | AC22–30/33–35, POST/encrypted revision, share snapshot, giữ việc/feedback, 18+ và sửa ngày sinh; các gap G1 ở mục 5/10 |
| [models.py](../../apps/api/app/domains/readings/models.py), [application.py](../../apps/api/app/domains/readings/application.py), [postgres.py](../../apps/api/app/domains/readings/postgres.py) | Enum hiện chưa có money; hash lens/toàn plan/scope/revision, identity validators; deterministic rendering; reader `ReadingPlan.model_validate` chưa đọc enum mới |
| [daily_notes.py](../../apps/api/app/api/v1/routes/daily_notes.py), [crypto.py](../../apps/api/app/infrastructure/crypto.py), [guest/tables.py](../../apps/api/app/domains/guest/tables.py) | DTO context đã forbid extra; HMAC phân miền và khóa ≥32 byte; bảng consent có purpose/version/thời điểm |
| [share/service.py](../../apps/api/app/domains/share/service.py), [experiments/service.py](../../apps/api/app/domains/experiments/service.py), [resonance/service.py](../../apps/api/app/domains/resonance/service.py) | Share chụp hook/manifestation, experiment và feedback có tham chiếu revision/lens, nên phải khóa provenance |
| [ConsentPage.tsx](../../apps/web/src/features/consent/ConsentPage.tsx), [birth/service.py](../../apps/api/app/domains/birth/service.py), [data map](../legal/store-privacy-data-map.md) | Privacy đang 18+, server kiểm ngày sinh; retention/receipt/export/journal có vòng đời khác nhau |
| [verify-privacy.mjs](../../scripts/verify-privacy.mjs), [research-sources.mjs](../../scripts/research-sources.mjs), [CI scope](../../.github/workflows/pr-check.yml) | Privacy guard hiện chưa có money_situation; research gate CI chỉ kiểm docs/research, không xác minh link/luật |

### Nguồn ngoài cần xác minh lại khi có mạng

Các link dưới lấy từ kế hoạch đã thống nhất và hồ sơ repo. Chưa mở chúng trong lượt này; không ghi là "đã đọc". Nghiên cứu ngoài còn thiếu của G1/AC4/AC5 phải được bổ sung bằng nguồn chính thức và ngày kiểm, không suy từ URL rằng nội dung vẫn đúng.

| Nguồn chính thức | Cần đối chiếu / quyết định dự kiến dùng |
|---|---|
| [Luật 91/2025/QH15, Công báo](https://congbao.cdnchinhphu.vn/CongBaoCP/VanBan/2025/6/45578/57730-1-2025971-97291-2025-qh15.pdf) | Điều 9/11/20–22/24; dữ liệu cá nhân, consent, hồ sơ tác động, chuyển và trẻ em ở mục 6–7 |
| [Nghị định 356/2025/NĐ-CP, bản ký số](https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/01/356-nd.signed.pdf) | Điều 4/6 và nghĩa vụ hồ sơ; đối chiếu lại OCR cũ và ngoại lệ miễn trừ |
| [Luật Trẻ em, bản hợp nhất](https://datafiles.chinhphu.vn/cpp/files/vbpq/2025/9/108-vbhn-vpqh.pdf) | Điều 1 và giới hạn tuổi; không dùng nội dung thứ cấp làm xác nhận bản hiện hành |
| [Apple App Privacy](https://developer.apple.com/app-store/app-privacy-details/) | Collection vượt request, linked/financial/user content/purposes; map bảo thủ ở mục 7 |
| [Google Data Safety](https://support.google.com/googleplay/android-developer/answer/10787469), [User Data](https://support.google.com/googleplay/android-developer/answer/10144311) | Collected/shared, provider exception, optional, ephemeral, encryption/deletion; disclosure trước thu |
| [RFC 2104](https://datatracker.ietf.org/doc/html/rfc2104) | HMAC có khóa; không phải ẩn danh; so với hash tập đóng ở mục 4 |
| [OWASP MASVS-STORAGE-2](https://mas.owasp.org/MASVS/controls/MASVS-STORAGE-2/), [MASTG](https://mas.owasp.org/MASTG/), [Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html) | Native cache/file/backup và log leakage, kiểm riêng với web |
| [Pydantic config extra](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.extra) | Giữ forbid tại DTO hiện có, không đổi contract client cũ ngoài phạm vi |

Prior art tại repo: encrypted revision hiện có và `SecretHasher`, cùng [quyết định việc nhẹ](2026-11-17-viec-nhe-hon-daily.md) về snapshot/rollback. So sánh RAM, prose-only và encrypted revision ở mục 3; không thêm thư viện hay sao chép tài sản bên ngoài.

## 9. Cờ tắt, điều kiện mở và quay lui (AC5)

#711 dựng cờ máy chủ mặc định off. Khi tắt không nhận consent mới, tạo plan/revision, job hoặc metadata `money`; #712 chỉ hiện luồng khi máy chủ xác nhận sẵn sàng. Tách ba trạng thái:

- Tắt kỹ thuật: dừng thu mới, giữ đọc/xuất/xóa dữ liệu còn hợp lệ.
- Chưa đồng ý: không tạo/xử lý `money` cho người đó.
- Đã rút: chặn nội dung và xóa theo mục 6.

Trước bật phải đủ nội dung #710 đã duyệt đúng phiên bản; #711/#712, consent và #690 có bằng chứng; owner duyệt privacy/consent và nhận dữ liệu mới theo R2; retention/backup/restore, hồ sơ tác động và store khớp cấu hình; không còn gap share/giữ việc/feedback; diễn tập rollback đạt. Phát hành theo R12, chưa thực hiện trong #709.

| Owner action | Khoảng trống | Mặc định |
|---|---|---|
| Dữ liệu mới | Cho phép nhận chuyện tiền, revision và receipt consent | Không ghi mới |
| Chữ nhạy cảm | Privacy/disclosure/consent và rút/xóa | Không viết mới/phục vụ trong #709 |
| Phát hành | Người thật, main/deploy, khai báo store bản phát hành | Chưa thực hiện |
| Chi phí/quyền | Không đề xuất dịch vụ mới; nếu phát sinh phải ghi riêng | Không mua, bật provider, đổi IAM/secret |

Đây là cổng bật/phát hành. Tài liệu hoặc phần dựng tắt có thể vào integration sau review theo quy trình; chưa có verdict đúng bản thay đổi này.

Quay lui:

1. Tách reader tương thích enum/schema/HMAC khỏi ghi và UI. Trước lần ghi thật đầu tiên chỉ về code cũ khi có bằng chứng chưa tồn tại dữ liệu mới.
2. Sau ghi đầu tiên, tắt thu mới và giữ reader hiểu `money`. Không về HEAD hiện tại vì `ReadingPlan.model_validate` từ chối enum mới. #711 phải ghi SHA tối thiểu cho rollback gồm reader, keyed identity, export, withdrawal và deletion; chưa có SHA đó ở #709.
3. Không thay khóa hoặc bỏ identity validation để rollback qua. Không xóa/viết lại dữ liệu chỉ để vượt kiểm quay lui kỹ thuật. Điều này không cản xóa vì quyền người dùng hoặc xử lý sự cố theo quy trình áp dụng.
4. Cờ tắt giữa phiên: hủy request đang chờ, xóa lựa chọn chưa gửi; bài đã nhận chỉ được xem khi quyền còn hợp lệ. Chuyển bản nền phải rõ ràng, không giả đó là bài tiền mới. Câu UI mới pending theo R15, không giải thích enum/khóa/lỗi máy chủ.
5. Diễn tập bốn chuyện tổng hợp, bản lưu/export, phiên cũ, đồng thời và withdrawal. Kiểm reader cũ/mới và quyền xóa sau tắt cờ; không dùng dữ liệu thật.

## 10. Ma trận AC, kiểm chứng và bàn giao

| AC #709 | Bằng chứng tài liệu | Nơi làm và test runtime bắt buộc, chưa chạy |
|---|---|---|
| AC1 | Mục 2: money, bốn mã, payload chọn đơn, Daily | #711 contract/planner/API: bốn chuyện; thiếu/sai/nhiều lựa chọn bị từ chối; lens cũ và voice giữ hợp lệ; purpose ngoài Daily bị chặn |
| AC2 | Mục 3–6: lưu mã hóa, HMAC, downstream, vòng đời; data map inventory | #711 repository/application/owner: replay/đồng thời/khác chủ, identity validation, DB metadata; #690 canary cache/log/share; read/save/export/delete và restore |
| AC3 | Mục 2: không số tiền/free text/suy luận trước hoặc sau chọn | #711 input/no-auto-select; #710 note/việc nhẹ/việc thường bốn chuyện cùng #705; facts/evidence/precision/confidence giữ nguyên |
| AC4 | Mục 6–8; data map có inventory, phân loại store, consent, tuổi, /privacy | Task consent chưa có số: cancel zero rows, version/revoke/race/reaccept/delete; #711 tuổi/legacy; pháp luật/store hiện hành chưa kiểm lại, còn thiếu |
| AC5 | Mục 3/8/9: phương án, nguồn, rollback floor và giữa phiên | #711 fixture cũ/mới, flag off giữa phiên/sau ghi, export/withdraw/delete sau rollback; G1 nguồn ngoài còn thiếu lượt xác minh |

| Đơn vị bàn giao | Phạm vi và điều kiện |
|---|---|
| #709 | Hai file tài liệu; review AC/diff và nguồn trên đúng bản thay đổi. Không tính test guard nền là test tính năng |
| #710 | Nội dung và hai mức việc; pending không phục vụ, AC3 sau chọn; không soạn chữ nhạy cảm trong task này |
| #711 | Contract/encrypted storage/HMAC, flags, consent integration, no-store, downstream/AI fencing, reader/delete. Mở rộng tests readings, share, experiments, resonance, history, privacy/data-export; `verify-privacy.mjs` phải kiểm trường mới, provider allowlist và public contract |
| Task consent chưa tạo | Claude thực hiện/Codex review dự kiến; xác nhận phân công, AC mục 6, owner copy/version, API/UI/withdrawal/tests trước triển khai |
| #712 | Chọn đơn, consent, stale response/session, off giữa phiên, preview nền, 360/390 px, bàn phím/screen reader, target ≥44 px; mở rộng kiểm AC30 theo US hiện hành |
| #690 / trước bật | Canary mã lẫn prose ở log/network/URL/referrer/error/cache/filename/share image; cố ý rò một ca để chứng minh kiểm báo đỏ; native riêng iOS/Android, restore và backup |

AI tests phải bật cấu hình AI chung và chứng minh application enqueue, worker, adapter/provider đều không nhận `money`. DB tests kiểm không có mã/prose plaintext hoặc hash không khóa của bốn chuyện. Guard tĩnh không thay kiểm request và prose thật. Chạy `research-sources.mjs` theo scope CI `docs/research/`; hai file #709 nằm ngoài scope, nên zero files không chứng minh nguồn đúng. Reviewer kiểm từng link và tối thiểu hai kết luận với nguồn. PR runtime cần contract/privacy và `pnpm check`; ca chưa chạy không ghi PASS.

Sáu điểm phản biện được xử lý trong quyết định: toàn bộ định danh phụ thuộc dùng HMAC (mục 4); thừa nhận lịch sử, so RAM và chốt share/giữ việc/feedback (3/5); consent/withdrawal/store cụ thể (6/7/data map); no-store mọi đường và Daily-only/AI chung (2/5); forbid cục bộ/AC3 sau chọn/tuổi/guard và nguồn (2/7/8/10); reader độc lập, tắt giữa phiên, phân biệt xóa quyền với rollback (9).

Nguồn đã kiểm trong lượt này là file repo ở mục 8. Nguồn ngoài/GitHub chưa kiểm lại do không mạng. Rủi ro còn lại: chưa có runtime `money`, bằng chứng consent/retention/backup/native/pháp lý/store, gap US về downstream, SHA rollback tối thiểu, task consent chưa tạo và review độc lập đúng bản thay đổi. Không có dữ liệu hoặc chi phí mới từ hai file này. #709 chưa có biên nhận hoàn tất; AC4 xác minh hiện hành và AC5 nghiên cứu ngoài chưa đủ, DoD review đúng HEAD/GitHub chưa xong. Không tuyên bố tính năng sẵn sàng bật.

### Kiểm tra offline của thay đổi tài liệu

| Lệnh/kiểm tra | Kết quả và giới hạn |
|---|---|
| `node --test scripts/research-sources.test.mjs` | 3/3 PASS; kiểm cổng nguồn, không xác minh nguồn ngoài |
| `node scripts/verify-privacy.mjs` | PASS trên runtime hiện có; chưa có `money` nên không phải bằng chứng bảo vệ luồng mới |
| `node scripts/research-sources.mjs --base HEAD --head HEAD` | 0 file, 0 lỗi; CI chỉ kiểm `docs/research/`, không kiểm hai file này hay phần sửa chưa commit |
| Kiểm link tương đối và anchor Markdown của quyết định/phần data map mới bằng Python tại máy | 35 link; sửa anchor US-03 bị sai, chạy lại đạt. Không kiểm URL mạng |
| `git diff --check` và đọc lại hai file theo AC/threat model | Không lỗi whitespace; chỉ hai file tài liệu đổi. AC/runtime tests ở bảng trên chưa chạy; chưa có `pnpm check`, Author check hay verdict độc lập đúng HEAD |

Không đăng biên nhận lên GitHub vì lệnh không mạng/không commit/push. Phiên nối mạng sau cần đối chiếu lại nguồn và task, bổ sung bằng chứng rồi xin review theo đúng bản đã commit; không dùng bảng này thay verdict.
