# Góc Tiền bạc: kiến trúc và bản đồ dữ liệu (#709)

Ngày: 25.11.2026. Task gốc giao Claude thực hiện, Codex review. PR #932 ghi Codex soạn tài liệu, Claude điều phối và mở PR; Antigravity phản biện vòng 1. Bản sửa này do Codex thực hiện theo yêu cầu owner. Review và Author check phải khớp commit cuối theo quy trình, không dùng người soạn làm reviewer độc lập cho chính bản sửa của mình.

## 1. Phạm vi và trạng thái

Quyết định này chốt thiết kế cho tuần 2 của [kế hoạch 7 tuần](../plans/2026-11-15-ke-hoach-7-tuan-moc-do.md), điều kiện bắt đầu số 5, hub [#686](https://github.com/honghanh153-creator/la-lanh/issues/686), task [#709](https://github.com/honghanh153-creator/la-lanh/issues/709). Phạm vi tài liệu gồm quyết định, delta US-03/US-05, biên bản bàn giao và [bản đồ dữ liệu](../legal/store-privacy-data-map.md#money-context-design-delta--2026-11-25-not-implemented). Chưa thêm enum vào code, API, UI, schema, consent hay cờ; chưa thu dữ liệu thật, chưa cho phép bật hoặc phát hành.

Issue ghi cỡ S; áp dụng mức thẩm định M cho phần tài liệu theo kế hoạch đã chốt, có G1/G4/G6/G7/G8 và threat model ở mục 5. Phần runtime sau này đổi API và dữ liệu cá nhân phải phân loại L theo [quy trình](../operations/product-development-process.md), không kế thừa nhánh docs-only để giảm cổng. G2/G3/G5 runtime được bàn giao, G9 chưa thực hiện, G10 chưa cấp dịch vụ/chi phí/quyền mới; thiết kế khóa riêng ở mục 4 cần owner trước cấp secret. Theo [checklist](../operations/decision-checklist.md), Q2/Q3 có điều kiện trước bật; Q1/Q4/Q5 không phát sinh hành động bị cấm trong thay đổi tài liệu này. Áp dụng R1–R17 từ [luật đang hiệu lực](../operations/luat-dang-hieu-luc.md).

Nguồn GitHub kiểm ngày 25.11.2026: [task #709](https://github.com/honghanh153-creator/la-lanh/issues/709), hub #686, #710–#712, #690 và [phản biện PR #932](https://github.com/honghanh153-creator/la-lanh/pull/932#issuecomment-7164631937). Các issue runtime còn mở, chưa phải bằng chứng triển khai. [Verdict PR #395](https://github.com/honghanh153-creator/la-lanh/pull/395#issuecomment-6765202453) yêu cầu đánh giá thay đổi hợp đồng dữ liệu ít nhất mức M; không dùng việc cờ tắt để giảm cổng privacy. Bằng chứng thao tác và khoảng trống DoD nằm trong [biên bản phản hồi](../reviews/2026-11-25-pr-932-antigravity-round-1.md).

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
- Lens cũ, gồm `voice`, giữ hợp lệ và hành vi cũ. Với `money`, chỉ `voice=direct` hoặc vắng mặt được nhận, đều dùng bộ dựng xác định sẵn, không AI/rewrite. `voice=roast` bị từ chối 422 trước planner/enqueue; không âm thầm bỏ qua lựa chọn.
- Kiểm mọi route public trong `apps/api/app/api` ngày 25.11.2026: bốn request DTO nhận `background_lens` là `ContextProjectionRequest`, `ResonanceRequest`, `ExperimentChooseRequest` trong `daily_notes.py` và `ShareArtifactRequest` trong `share_artifacts.py`. Cả bốn hiện có `extra="forbid"`. Chỉ context POST được thêm `money_situation`; ba DTO còn lại phải từ chối lens `money` và mọi trường chuyện con, đồng thời kiểm provenance revision để không vượt bằng ID + lens giả. `SavedNoteRequest` chỉ nhận revision ID, cũng forbid extra, nhưng vẫn cần kiểm provenance khi save. Các trường cùng tên ở response không phải đầu vào. Không có đầu vào public khác nhận `background_lens`/`money_situation` trong mã đã kiểm. #711 phải đối chiếu lại toàn OpenAPI khi triển khai; DTO mới nhận các trường này cũng phải forbid extra. Không siết DTO không liên quan.
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

Chọn HMAC-SHA-256 với **khóa riêng cho định danh đọc**, không tái sử dụng `guest_hash_key`. `SecretHasher` hiện chỉ giữ một khóa, không phải key ring; `DataKeyProvider` là khóa mã hóa, không tự trở thành khóa HMAC. #711 phải có key ring phiên bản cho money, gồm một khóa ghi và các khóa chỉ đọc/tra cứu còn cần thiết. Mỗi khóa ngẫu nhiên ít nhất 32 byte, tách khỏi DB. Cấp secret/quyền là khoảng trống cần owner theo R2/R13; #709 chỉ thiết kế, không tạo secret/IAM/dịch vụ. RFC 2104 §2–3 được kiểm ở mục 8.

Đặt `H(k, domain, parts)` là HMAC-SHA-256 trả 64 hex, canonical encoding có kiểu, độ dài/phân cách không nhập nhằng và version scheme cố định. `O` là owner, `P` profile, `E` định danh lần consent hiện hành không tái sử dụng sau rút, `C` nguồn chart/snapshot cùng provenance, `T` ngày địa phương/múi giờ/mốc scope chuẩn hóa, `U` purpose. `S` là chuyện con; `V` là bộ phiên bản nội dung/renderer/schema/rules/gates. `E` được lấy từ receipt được xác thực, không từ client; nếu cần schema mới phải review trước triển khai.

| Cột | Canonical riêng | Ý nghĩa |
|---|---|---|
| `lens_variant` | `H(k, "reading-lens/v1", [O,P,E,"money"])` | Chỉ định danh góc trong phạm vi chủ/profile/lần consent. Không chuyện con, ngày hay content version; lọc/đối chiếu lịch sử phải tra tất cả phiên bản khóa còn giữ |
| `scope_key` | `H(k, "reading-scope/v1", [O,P,E,C,T,U,"money"])` | Một phạm vi active chung cho cả bốn chuyện và mọi content version. Không `S`/`V`, không nhúng `lens_variant` đang xoay khóa |
| `plan_key` | `H(k, "reading-plan/v1", [O,P,E,C,T,U,"money",S,canonical_plan])` | Toàn plan xác định sẵn, gồm các phiên bản thực sự ảnh hưởng plan. Không đưa key ID hoặc metadata lúc lưu vào canonical plan |
| `revision_key` | `H(k, "reading-revision/v1", [O,P,E,C,T,U,"money",S,canonical_plan,V,canonical_accepted_content])` | Đúng nội dung và provenance của revision đã nhận; không hash lại bằng SHA không khóa |

Không lưu chuỗi `"money"`, `background_lens`, mã chuyện, prose hay nhãn tương đương vào **bất kỳ cột plaintext** của plan/revision/projection/saved-note. Chúng chỉ nằm trong envelope mã hóa và đầu vào HMAC. Các cột renderer/content/schema/rules/gate version công khai phải dùng phiên bản chung, không mang tên money hoặc phân biệt bốn chuyện. Fingerprint/digest của plan hay prose cũng phải có khóa; không thêm situation index, bảng dedupe hay lịch sử lựa chọn. HMAC là metadata liên kết được, không phải ẩn danh.

Scheme và `key_id` của HMAC nằm trong payload mã hóa được AAD ràng buộc owner/source, không thêm tiền tố money ở cột định danh. Đọc theo ID phải giải mã, chọn đúng khóa và kiểm lại từng identity bằng canonical tương ứng; thiếu khóa thì từ chối, không bỏ validation hoặc fallback sang hash không khóa. Giữ canonical/serialization của lens cũ nguyên vẹn.

**Replay khi xoay khóa:** trước khi tạo bản ghi, tính các ứng viên scope/plan/revision trên **mọi khóa còn được chấp nhận** từ cấu hình key ring, không đợi đọc `key_id` trong một bản ghi chưa tìm thấy. Tìm trong cùng owner/profile/source, giải mã và xác thực bản khớp; dùng lại identity/phiên bản gốc khi replay. Chỉ ghi khóa mới khi không có bản tương ứng trên cả ring. Không rekey lúc mở bài. Giữ khóa cũ tới khi mọi bản còn sống, kể cả saved-note và backup còn phục hồi, đã hết hạn/xóa hoặc có migration được kiểm; chưa có bằng chứng thì không bỏ khóa.

**Đồng thời:** #711 mở rộng mẫu khóa guest hiện có ở `readings/postgres.py` (`GuestSessionRow ... with_for_update`) cho toàn giao dịch lookup đa khóa, tạo mới và chuyển active, kèm kiểm profile/phiên bản quyền. Chưa có giao dịch money này trong runtime. Khóa giao dịch không phụ thuộc khóa HMAC đang active, `S` hoặc `V`; không chỉ dựa unique index của một scope hash. Mọi scope hash ở các phiên bản khóa là alias của cùng phạm vi logic. Hai chuyện đồng thời phải tuần tự chuyển active, chỉ có một active trong phạm vi; response gắn đúng revision/chuyện đã yêu cầu. Replay bản cũ trả đúng bản đó và trạng thái active hiện tại, không tự giành active lại; đổi active dùng expected revision theo contract hiện có. Khác chủ không dùng chung dấu. Sau rút/đồng ý lại, `E` mới và deletion fence ngăn dùng lại bản đã xóa.

DB cộng khóa cùng lộ vẫn cho phép thử tập giá trị. Không log/xuất/gửi HMAC sang AI. Nếu #711 cần lưu thêm chuyện hoặc dấu suy ra ngoài các vị trí góc hiện có, dừng phần đó theo AC2, ghi khoảng trống cần owner. Khóa riêng và key ring chỉ là thiết kế, chưa chứng minh chạy được.

## 5. Ranh giới downstream và threat model (AC2, G7/G8)

| Đường dữ liệu | Quyết định thiết kế |
|---|---|
| POST context | Kiểm chủ, CSRF/trusted Origin, giới hạn lạm dụng, input đóng, cờ và consent trước lập plan hoặc ghi |
| Plan/revision | Envelope mã hóa; kiểm AAD, chủ và nguồn dữ liệu; dữ liệu sinh/chart không có thêm bản sao do `money` |
| Client | Chỉ memory gắn phiên/request; hủy hoặc chặn response cũ khi đổi phiên, rút consent hay rời luồng |
| Cache | Không Web Storage, IndexedDB, service worker, Capacitor Preferences hay HTTP cache cho `money`, kể cả ID của ý định lưu offline |
| Lịch sử | Chính chủ đọc revision còn được giữ; không dùng để gợi ý lại chuyện con |
| Lưu riêng | Giữ đúng revision mã hóa trong `SavedNote`; con này có thể giữ hidden root lâu hơn Daily history. Danh sách chỉ hiện ngày và nhãn chung đã duyệt, không snippet/nhãn chuyện tiền; mở chi tiết mới trả nội dung sau kiểm quyền. Lọc góc nếu cần chỉ qua POST riêng/memory và lookup HMAC đa phiên bản, không URL/preference/cột plaintext |
| Xuất dữ liệu của tôi | Chỉ lựa chọn và nội dung còn thuộc phạm vi xuất của chính chủ; không internal plan, ID, HMAC, token hay dữ liệu người khác |
| Log/trace/báo lỗi/analytics | Không mã chuyện, prose, body, HMAC hay exception chứa chúng |
| AI/bên thứ ba | Không job/enqueue/worker/adapter/provider nhận dữ liệu `money`. Hosting hiện có vẫn là bên xử lý dữ liệu, không được coi là đã loại mọi chuyển xuyên biên giới |

### Chia sẻ, link và ảnh

Không chia sẻ revision `money`. Dựng lại bản nền không có góc tiền từ dữ kiện nền được phép dùng, rồi preview trước khi người dùng xác nhận. Không lấy snapshot bài tiền rồi chỉ xóa `money_situation`: hook, manifestation, action và nội dung suy ra đều không tái sử dụng. Share record không tham chiếu revision `money`. API kiểm nguồn revision, từ chối cả ID bài tiền đi kèm lens giả. Giữ bảo vệ capability token, thu hồi link, no-cache/no-index/no-referrer hiện hành.

[US-05 §21](../user-stories/US-05-luu-va-chia-se-note.md#21-delta-góc-tiền-bạc-2026-11-25) ghi delta chính thức để review: từ bài tiền phải mở bản nền riêng, xem preview rồi mới tạo share của bản nền. Không gọi đó là chia sẻ bài tiền hoặc âm thầm thay snapshot. Contract cũ vẫn áp dụng nguyên vẹn cho bài nền; bài tiền không có public share. Delta chưa được duyệt độc lập thì chặn bật, không coi là được miễn AC.

### Việc đang giữ và phản hồi

Việc nhẹ/thường của #710 được hiển thị trong bài tiền, nhưng không ghi việc đó, action key hoặc revision `money` vào bảng việc đang giữ. Muốn giữ việc nền phải mở bản nền và xác nhận việc đang thấy. Không âm thầm đổi việc khi bấm giữ. API kiểm provenance revision thay vì tin lens client.

Không ghi feedback cho revision `money` trong đợt này, kể cả chỉ `revision_id` hoặc digest. Không gán feedback bài tiền sang bài nền. UI không hiện nút gửi feedback trực tiếp trên bài tiền. Feedback nền giữ consent/TTL/reset/revoke hiện có.

[US-03 §25](../user-stories/US-03-doc-note-hom-nay.md#25-delta-góc-tiền-bạc-2026-11-25) ghi delta cho AC25/29/33–35: bài tiền chỉ hiển thị việc, không ghi held action/feedback; muốn dùng các chức năng này phải mở và xác nhận bản nền. Đây là đề xuất hợp đồng đã có chỗ review, chưa là runtime hoặc quyết định cắt phạm vi đã duyệt. Trước bật cần review delta US-03/US-05 và kiểm UX không âm thầm đổi bài.

### Cache, export và native

`Cache-Control: no-store` cho mọi phản hồi riêng có dữ liệu `money`: POST context, GET chi tiết, lịch sử, **GET danh sách và chi tiết `Lưu riêng`**, export và lỗi tương ứng. Khi danh sách có hoặc có thể có bản tiền, cả response danh sách phải no-store, không chỉ item. Danh sách lọc bỏ bản không còn quyền trước phân trang/count; không trả placeholder lộ từng dùng góc tiền. Client dùng chế độ không cache. Không ETag/304 giữ lại nội dung. Cờ tắt không làm các đường đọc cũ mất bảo vệ này.

File chính chủ tải là ngoại lệ lưu thiết bị có chủ đích. Không giữ bản sao server; filename cố định không chứa chuyện tiền. Native dùng file tạm app-private cache và dọn sau share sheet, kể cả hủy/lỗi, theo contract export hiện có. Lỗi dọn không được coi đã xóa; kiểm riêng trên iOS/Android, kể cả backup thiết bị, WebView cache, quyền và chuyển phiên. Không xin quyền nền tảng mới trong thiết kế này. MASVS/MASTG và logging sources ở mục 8 là căn cứ kiểm bàn giao.

| Đe dọa/đường hỏng | Biện pháp phải chứng minh trước bật |
|---|---|
| Người khác dùng ID/phiên cũ đọc bài | Owner/source check, chống enumeration, hủy response cũ, a11y không đọc nội dung cũ |
| Đoán bốn mã từ DB metadata | HMAC mọi định danh phụ thuộc, phân miền/chủ/scope; kiểm DB không có plaintext/hash tập đóng |
| Bài tiền lọt qua share/giữ việc/feedback hoặc cache | Kiểm provenance ở server, dựng nền mới/preview, từ chối ghi downstream; no-store và canary prose |
| AI chung bật hoặc lỗi validation ghi dữ liệu | Chặn tại application/worker/provider; lỗi redact; canary log/network/báo lỗi |
| Withdraw đua read/list/history/saved/export/write; restore hồi sinh dữ liệu | Khóa/phiên bản quyền chung, chặn truy cập trước dọn, journal và retry, kiểm restore |
| Rollback reader không hiểu enum/khóa mới | Giữ reader tương thích và sàn SHA, diễn tập có bản mới; không bỏ identity validation |

Không thêm auth/session, crypto implementation, dependency, storage service hoặc endpoint public trong #709. Test tĩnh hiện có không chứng minh threat model `money` đã đạt.

## 6. Consent, withdrawal và retention (AC4)

Consent riêng cho `money` là đầu việc còn thiếu trong chuỗi #709–#712. Consent birth-profile hoặc AI không đủ. [Phiếu consent và /privacy](../reviews/2026-11-25-pr-932-antigravity-round-1.md#phiếu-issue-consent-và-privacy) có phạm vi/AC/DoD để tạo Issue chính thức. Claude thực hiện, Codex review là phân công đề xuất, chưa có xác nhận nhận việc. Chưa có số Issue; đây là khoảng trống phải hoàn tất trước bật. R2 chặn bật trước approval dữ liệu mới.

AC của đầu việc consent:

- Owner cung cấp/duyệt chữ `/privacy`, disclosure và consent. #709 chỉ ghi yêu cầu kỹ thuật, không soạn câu mới.
- UI thông báo trước lần gửi lựa chọn đầu tiên, không đồng ý sẵn; từ chối vẫn đọc bản nền. Chữ/version chưa duyệt không được nhận consent.
- API accept/status/withdraw có owner, CSRF/Origin và phiên bản được duyệt; server kiểm consent hiện hành mỗi lần tạo, không tin cờ client.
- Tái sử dụng bảng `consents`, purpose dự kiến `money_context`, với chủ, purpose, version, `accepted_at`, `revoked_at`. Không chuyện con, số tiền hay revision. Version trỏ tới nội dung duyệt bất biến để chứng minh đã đồng ý điều gì. Bảng có trường cần thiết, chưa chốt thêm schema; cần thêm trường/nơi lưu phải thiết kế/review trước, không dùng log thay bằng chứng.
- Receipt là dữ liệu mới, mặc định tắt, có dòng riêng ở data map. Khi đang có hiệu lực, giữ bằng chứng tối thiểu theo hồ sơ. Sau rút, không giữ dấu plaintext `money_context`/`accepted_at`/`revoked_at` tới hết đời tài khoản. Trước bật, đầu việc consent phải chốt hai giá trị hữu hạn: `L` là thời gian giữ bằng chứng consent đã rút, có căn cứ mục đích/pháp lý; `B` là hạn tối đa phục hồi của mọi backup/dump/provider copy. Xóa receipt ở DB chính chậm nhất `revoked_at + L`, chỉ giữ marker xóa tối thiểu trong nguồn độc lập. Mọi backup có thể chứa receipt, kể cả tạo sau rút trước purge, phải hết khả năng phục hồi trước `D = revoked_at + L + B + 6 giờ`; xác nhận xóa/retry/replay và purge marker định danh chậm nhất `D`. Restore không khởi động lại hạn `L`/`B`; không tự gia hạn bằng lần đọc/export/đồng ý lại. Nghĩa vụ chứng minh consent theo NĐ 356 Điều 6 và thời hạn cụ thể phải được đối chiếu trong đầu việc đó, phản ánh bằng chữ owner duyệt. Nếu cần giữ lâu hơn phải có căn cứ, hạn và review riêng; không mặc định giữ vô hạn. Chưa biết hạn backup hoặc chưa chứng minh dọn đúng `D` thì không bật. Guest deletion vẫn cascade receipt; journal độc lập xử lý restore.
- Test cancel ghi zero rows, missing/stale/revoked version, gọi trực tiếp, khác chủ, rút trong request đang chạy, đồng ý lại và xóa tài khoản. Cờ tắt không nhận receipt mới.

### Rút đồng ý

1. Ngừng xử lý mới ngay, chặn request đang chờ ghi hoặc trả dữ liệu sau mốc rút.
2. Gỡ quyền hiển thị và xóa plan/revision `money`, projection, bản lưu riêng và bản sao phụ thuộc do app giữ, gồm hidden root riêng của tiền không còn con hợp lệ. Không xóa bản nền/chart/tài khoản chỉ vì rút consent tiền.
3. Dọn memory/file tạm app kiểm soát. Không hứa xóa file chính chủ đã lưu ngoài app.
4. Journal hoặc nguồn replay xóa bắt buộc **độc lập với snapshot DB được restore**, không chỉ là bảng trong chính DB đó. Ghi marker bền vững trước báo rút thành công; không chuyện con/prose. Khôi phục phải nạp marker mới nhất từ nguồn độc lập, replay xóa/receipt đã rút, xác minh xong mới mở traffic/job. Không có nguồn độc lập, hoặc không chứng minh restore trước thời điểm rút vẫn xóa được, thì không bật. Nếu cần dịch vụ/quyền mới là khoảng trống owner, không tự cấp.
5. Create/read/list/history/saved/save/export/withdraw dùng cùng khóa giao dịch hoặc phiên bản quyền của owner/purpose. Tất cả kiểm lại quyền tại điểm trả response/commit; không chỉ lúc bắt đầu. Export không stream plaintext trước fence cuối; giữ quyền đọc tới khi hoàn tất bàn giao response hoặc hủy trước khi withdrawal được xác nhận. Nếu withdrawal thắng, hủy export, xóa buffer/file tạm và không cấp link/file; nếu export đã hoàn tất trước mốc rút, file đã nhận ngoài app không thu hồi được. Native cũng kiểm quyền ngay trước mở system sheet và dọn khi cancel/lỗi/rút. Không xuất dữ liệu tiền ở export sau rút, kể cả receipt còn giữ tạm; không hứa xóa bytes đã giao.
6. Nếu dọn lỗi, trạng thái đã rút vẫn chặn nội dung, có retry; không báo đã xóa xong sớm. Lỗi purge hoặc vượt hạn `D` phải được ghi nhận như sự cố, không tự đổi TTL. Đồng ý lại tạo lần quyền mới, không hồi sinh dữ liệu cũ.

Đây là lựa chọn sản phẩm cần phản ánh trong chữ owner duyệt, không phải khẳng định pháp luật buộc mọi withdrawal xóa tức thời.

### Thời hạn và backup

Kế thừa vòng đời đang mô tả ở [data map](../legal/store-privacy-data-map.md#accounthistory-delta--2026-10-10-not-a-store-submission): Daily history tự động hiển thị tối đa 24 giờ, đủ điều kiện dọn từ 18 giờ khi không còn Note hôm nay, job mỗi sáu giờ. Chưa chứng minh hạn xóa vật lý tuyệt đối 24 giờ. Note hiện tại/bản lưu có ngoại lệ theo vòng đời hồ sơ; không kéo dài hạn vì xem lại, đổi góc hoặc thêm `money`.

Root có thể bị giữ ẩn khi con còn hạn. `money` không tạo con share/experiment/feedback nhưng **có con `saved_note`** khi chính chủ lưu. Con này giữ đúng revision và root theo vòng đời hồ sơ cho tới bỏ lưu, rút consent hoặc xóa hồ sơ/tài khoản; không thuộc hạn Daily 18–24 giờ. Bỏ lưu xóa snapshot/con và dọn root nếu không còn con hợp lệ hay Note hiện tại; không tạo bản sao lịch sử mới. Mục 5 khóa danh sách/nhãn/no-store/offline. Thu hồi consent phải xóa cả saved-note và mọi hidden root riêng của money, không được giữ bằng cớ có bản lưu. Hồ sơ legacy chưa có retention policy không được ghi `money` tới khi policy có hiệu lực rõ; không tự nhận consent lịch sử. Backup có vòng đời riêng; thời hạn và restore của mọi bên xử lý chưa xác minh đủ là điều kiện chặn bật. Journal hiện mô tả mặc định 15 ngày; số mặc định không chứng minh phủ mọi backup còn phục hồi. Phải có nguồn replay độc lập và hạn `D` hữu hạn ở trên, đối chiếu cấu hình thực tế cùng một lần restore; không suy từ code ra vận hành.

## 7. Pháp luật, tuổi, store và /privacy (AC4)

Lựa chọn gắn hồ sơ, prose suy ra và HMAC đều là dữ liệu cá nhân theo thiết kế, kể cả khi mã hóa. Không mặc nhiên coi bốn mã là dữ liệu khách hàng tổ chức tín dụng. Dự án áp dụng mức bảo vệ nhạy cảm vì có thể tiết lộ đời sống riêng tư; đối chiếu NĐ 356 Điều 4.1(c), không suy từ tên tính năng thành khách hàng tổ chức tín dụng ở Điều 4.1(k).

Nguồn chính thức được mở và đối chiếu ngày **25.11.2026**, ghi điều khoản và đường dẫn tại mục 8. Luật 91/2025/QH15 Điều 9/11 chi phối đồng ý trước thu, Điều 12 vẫn coi dữ liệu mã hóa là dữ liệu cá nhân; Điều 10 phân biệt rút đồng ý với xử lý đã diễn ra. Điều 20–22 điều chỉnh hồ sơ tác động/chuyển; Điều 24 về trẻ em. NĐ 356 Điều 6 yêu cầu consent kiểm chứng được, không mặc định và thông báo khi nhạy cảm. Kết luận thiết kế là giữ consent riêng, mặc định tắt; kiểm nguồn không thay bằng chứng thực hiện nghĩa vụ.

Hosting ngoài Việt Nam vẫn cần hồ sơ chuyển dù không gọi AI. Trước bật phải xác định hồ sơ đánh giá tác động xử lý/chuyển cần lập mới hay cập nhật, đơn vị chịu trách nhiệm và bằng chứng thực hiện. Không tự nhận miễn trừ doanh nghiệp nhỏ khi xử lý có thể nhạy cảm; thiếu bằng chứng thì giữ tắt.

Giữ 18+ theo US-02, `/privacy` trong `ConsentPage.tsx` và `_require_adult_date` trong `birth/service.py`, cùng kiểm sửa ngày sinh US-23. Học phí không chứng minh là trẻ em hay đã thành niên. Kiểm gọi trực tiếp, legacy và sửa ngày sinh; không thu thêm giấy tờ/tuổi/người đại diện. Muốn mở cho người chưa thành niên phải có việc riêng/owner duyệt. Luật Trẻ em Điều 1 phân biệt trẻ dưới 16, không gộp mọi người dưới 18 thành cùng một nhóm pháp lý; đã kiểm Điều 1 bản hợp nhất 108/VBHN-VPQH, không thay giới hạn 18+ của sản phẩm.

Phân loại store cụ thể được ghi ở data map: chuyện tiền là Apple Financial Info → Other Financial Info, Google Financial info → Other financial info; prose là Other User Content/Other Data Types và Other user-generated content, kèm tài chính khi tiết lộ hoàn cảnh; metadata/receipt là User ID/Product Interaction và User IDs/App interactions theo dữ liệu thực tế. Đây là phân loại thận trọng của dự án, không phải store nêu đích danh bốn mã.

Khi bật: collected có, linked có cả guest, optional, mục đích App Functionality/Product Personalization, không tracking/quảng cáo, không ephemeral vì có lưu. Google Shared dự kiến không, chỉ chốt sau khi xác minh bên hạ tầng đạt ngoại lệ service provider. HTTPS/TLS và đường deletion/withdrawal cần kiểm bản phát hành. Không tự coi mã hóa là miễn collection. Đã đối chiếu định nghĩa nguồn Apple/Google ngày 25.11.2026 ở mục 8; mapping là suy luận của dự án, chưa là khai báo store đã nộp.

`/privacy` cần bổ sung trước bật: loại dữ liệu, mục đích, nơi xử lý, lịch sử mã hóa, metadata, retention, quyền rút/xóa/xuất và giới hạn share/giữ việc/feedback. Chủ trương này chưa phải câu privacy mới, và #709 không sửa trang đó. Owner phải duyệt nội dung. Store form/manifest cần khớp binary và cấu hình bật thực tế, không đổi khai báo bản hiện hành chỉ vì có tài liệu dự kiến.

## 8. Nghiên cứu G1 và nguồn (AC5)

### Tài liệu và mã đối chiếu

| Nguồn | Phần đã đối chiếu và kết luận dùng trong quyết định |
|---|---|
| [PRD §7.2](../foundation/la-lanh-prd.md), [SRS §7](../foundation/la-lanh-srs.md), [product plan §7](../foundation/la-lanh-product-plan-v2.md) | Consent riêng/version hóa; encrypted private data và export chính chủ; không gom dữ liệu cho mục đích tương lai |
| [US-03 §21–23](../user-stories/US-03-doc-note-hom-nay.md), [US-05](../user-stories/US-05-luu-va-chia-se-note.md), [US-02](../user-stories/US-02-khai-ngay-sinh-reveal-la-khai-sinh.md), [US-23](../user-stories/US-23-sua-thong-tin-sinh.md) | AC22–30/33–35, POST/encrypted revision, share snapshot, giữ việc/feedback, 18+ và sửa ngày sinh; delta G1 ở US-03 §25, US-05 §21 và test mục 10 |
| [models.py](../../apps/api/app/domains/readings/models.py), [application.py](../../apps/api/app/domains/readings/application.py), [postgres.py](../../apps/api/app/domains/readings/postgres.py) | Enum hiện chưa có money; hash lens/toàn plan/scope/revision, identity validators; deterministic rendering; reader `ReadingPlan.model_validate` chưa đọc enum mới |
| [daily_notes.py](../../apps/api/app/api/v1/routes/daily_notes.py), [crypto.py](../../apps/api/app/infrastructure/crypto.py), [guest/tables.py](../../apps/api/app/domains/guest/tables.py) | DTO context đã forbid extra; HMAC phân miền và khóa ≥32 byte; bảng consent có purpose/version/thời điểm |
| [share/service.py](../../apps/api/app/domains/share/service.py), [experiments/service.py](../../apps/api/app/domains/experiments/service.py), [resonance/service.py](../../apps/api/app/domains/resonance/service.py) | Share chụp hook/manifestation, experiment và feedback có tham chiếu revision/lens, nên phải khóa provenance |
| [ConsentPage.tsx](../../apps/web/src/features/consent/ConsentPage.tsx), [birth/service.py](../../apps/api/app/domains/birth/service.py), [data map](../legal/store-privacy-data-map.md) | Privacy đang 18+, server kiểm ngày sinh; retention/receipt/export/journal có vòng đời khác nhau |
| [verify-privacy.mjs](../../scripts/verify-privacy.mjs), [research-sources.mjs](../../scripts/research-sources.mjs), [CI scope](../../.github/workflows/pr-check.yml) | Privacy guard hiện chưa có money_situation; research gate CI chỉ kiểm docs/research, không xác minh link/luật |

### Nguồn chính thức đã đối chiếu ngày 25.11.2026

Ngày kiểm là ngày mở/đọc, không phải ngày ban hành. Các kết luận dưới là yêu cầu thiết kế; không tuyên bố đã có consent, hồ sơ nộp, store submission hay kiểm native. Bản NĐ ký số dạng ảnh không trích được chữ qua web; đã đọc bản Công báo có văn bản để đối chiếu, không dùng OCR cũ làm bằng chứng mới.

| Nguồn đã đọc | Phần đọc và kết luận áp dụng |
|---|---|
| [Luật 91/2025/QH15, Công báo](https://congbao.cdnchinhphu.vn/CongBaoCP/VanBan/2025/6/45578/57730-1-2025971-97291-2025-qh15.pdf) | Điều 9–12, 20–22, 24, 38: đồng ý theo mục đích, trước thu, kiểm chứng được; rút không làm vô hiệu xử lý trước đó; mã hóa vẫn là dữ liệu cá nhân. Hosting ngoài nước cần xét nghĩa vụ hồ sơ/cập nhật, không suy miễn vì không AI. Hiệu lực 01.01.2026. Không dùng luật để hứa xóa tức thời mọi bản sao |
| [NĐ 356 bản ký](https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/01/356-nd.signed.pdf), [thuộc tính Chính phủ](https://vanban.chinhphu.vn/?docid=216387&pageid=27160), [Công báo số 18, tr. 5, 7–8, 19–24, 38](https://congbaocdn.chinhphu.vn/180507251028987904/2026/1/17/cong-bao-so-18-ngay-18-01-46924signed-1768637757042330005940.pdf) | Điều 4.1(c)/(k), 6, 17–20, 41–42: đời tư khác dữ liệu khách hàng tài chính; phải chứng minh consent, không chọn sẵn; hồ sơ có cập nhật mục đích. Không mặc nhiên dùng miễn trừ doanh nghiệp nhỏ khi xử lý nhạy cảm. Hiệu lực 01.01.2026, thay NĐ 13/2023. Hạn receipt cụ thể vẫn cần đánh giá nghĩa vụ chứng minh |
| [Luật Trẻ em, 108/VBHN-VPQH](https://datafiles.chinhphu.vn/cpp/files/vbpq/2025/9/108-vbhn-vpqh.pdf) | Điều 1, tr. 2: dưới 16 là trẻ em. Giữ sản phẩm 18+, không thu giấy tờ mới |
| [Apple App Privacy](https://developer.apple.com/app-store/app-privacy-details/), [App Review 5.1.1–5.1.2](https://developer.apple.com/app-store/review/guidelines/#privacy) | Đã đọc Data collection, Data types, Data use, Data linked, Tracking và privacy/consent. Retention vượt request phải khai collected, liên kết guest vẫn linked. Other Financial Info bao gồm thông tin tài chính khác; mapping bốn chuyện là suy luận thận trọng. Cần privacy/consent, retention/deletion và quyền rút phù hợp hành vi; mã hóa không miễn khai |
| [Google Data Safety](https://support.google.com/googleplay/android-developer/answer/10787469), [User Data, Full Policy](https://support.google.com/googleplay/android-developer/answer/10144311?hl=en) | Đã đọc Data collection/sharing, Data types, Purposes, Prominent Disclosure & Consent, privacy/deletion. Dữ liệu giả danh phải khai; ephemeral chỉ RAM cho request. Lưu revision nên không ephemeral; Other financial info là mapping dự án. Service-provider exception chỉ áp dụng khi xử lý thay theo chỉ dẫn; phải kiểm hợp đồng hạ tầng trước trả lời Shared. Disclosure trước consent khi ngoài kỳ vọng hợp lý; dự án chọn JIT riêng cho money |
| [RFC 2104](https://datatracker.ietf.org/doc/html/rfc2104) | §2–3: HMAC dùng khóa bí mật ngẫu nhiên và cần quản lý xoay khóa. Không quy định canonical/key ring/replay; đó là thiết kế dự án ở mục 4, phải có test trước bật |
| [OWASP MASVS-STORAGE-2](https://mas.owasp.org/MASVS/controls/MASVS-STORAGE-2/), [MASTG](https://mas.owasp.org/MASTG/), [Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html) | STORAGE-2/Related Weaknesses nêu leak qua backup/log/UI/WebView; MASTG có kiểm riêng iOS/Android. Logging, Data to exclude/Verification: loại dữ liệu nhạy cảm khỏi log và kiểm rò rỉ. Đây là căn cứ giao kiểm native/cache/file và canary, không phải kết quả kiểm app |
| [Pydantic config](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.extra) | `extra` mặc định ignore, forbid mới reject. `hide_input_in_errors` chỉ nói về in lỗi, không chứng minh HTTP JSON đã redact; #711 phải kiểm response 400/422 thực tế. Lens cũ giữ contract, mọi đầu vào money đóng như mục 2 |

Prior art tại repo: encrypted revision hiện có và `SecretHasher`, cùng [quyết định việc nhẹ](2026-11-17-viec-nhe-hon-daily.md) về snapshot/rollback. So sánh RAM, prose-only và encrypted revision ở mục 3; không thêm thư viện hay sao chép tài sản bên ngoài.

## 9. Cờ tắt, điều kiện mở và quay lui (AC5)

#711 dựng cờ máy chủ mặc định off. Khi tắt không nhận consent mới, tạo plan/revision, job hoặc metadata `money`; #712 chỉ hiện luồng khi máy chủ xác nhận sẵn sàng. Tách ba trạng thái:

- Tắt kỹ thuật: chặn nhận consent, tạo/regenerate, đổi sang chuyện tiền mới và **lưu riêng mới**. Vẫn đọc/reload đúng revision đã tạo, liệt kê lịch sử/bản lưu, xuất, bỏ lưu/rút/xóa nếu quyền còn hợp lệ; đọc không tạo bản thay thế hoặc kéo dài TTL. Save replay chỉ được trả trạng thái bản lưu đã có, không tạo lại bản đã bỏ.
- Chưa đồng ý: không tạo/xử lý `money` cho người đó.
- Đã rút: chặn nội dung và xóa theo mục 6.

Trước bật phải đủ nội dung #710 đã duyệt đúng phiên bản; #711/#712, consent và #690 có bằng chứng; owner duyệt privacy/consent và nhận dữ liệu mới theo R2; retention/backup/restore, hồ sơ tác động và store khớp cấu hình; delta US-03/US-05 đã review và tests downstream đạt; diễn tập rollback đạt. Phát hành theo R12, chưa thực hiện trong #709.

| Owner action | Khoảng trống | Mặc định |
|---|---|---|
| Dữ liệu mới | Cho phép nhận chuyện tiền, revision và receipt consent | Không ghi mới |
| Chữ nhạy cảm | Privacy/disclosure/consent và rút/xóa | Không viết mới/phục vụ trong #709 |
| Phát hành | Người thật, main/deploy, khai báo store bản phát hành | Chưa thực hiện |
| Chi phí/quyền | Khóa HMAC riêng/key ring, nguồn replay journal độc lập; xác nhận có dùng được hạ tầng hiện hành hay cần quyền/dịch vụ mới | Không cấp secret/IAM, không mua hoặc bật provider |

Đây là cổng bật/phát hành. Tài liệu hoặc phần dựng tắt có thể vào integration sau review và Author check đúng commit theo quy trình.

Quay lui:

1. Tách reader tương thích enum/schema/HMAC khỏi ghi và UI. Trước lần ghi thật đầu tiên chỉ về code cũ khi có bằng chứng chưa tồn tại dữ liệu mới.
2. Sau ghi đầu tiên, tắt thu mới và giữ reader hiểu `money`. Không quay về code trước khi hỗ trợ money vì `ReadingPlan.model_validate` ở đó từ chối enum mới. #711 phải ghi SHA tối thiểu cho rollback gồm reader, keyed identity, export, withdrawal và deletion; chưa có SHA đó ở #709. #712 cũng phải ghi SHA sàn UI hiểu enum/DTO/key identity mới ở màn đọc, history và saved. Nếu client không khai khả năng tương thích, API bỏ toàn bộ item money trước phân trang/count và giữ lối xuất/rút/xóa bằng client tương thích; không đưa enum mới cho client cũ. Không dùng cờ tắt để bỏ reader/UI tương thích.
3. Không thay khóa hoặc bỏ identity validation để rollback qua. Không xóa/viết lại dữ liệu chỉ để vượt kiểm quay lui kỹ thuật. Điều này không cản xóa vì quyền người dùng hoặc xử lý sự cố theo quy trình áp dụng.
4. Cờ tắt giữa phiên: hủy tạo/save mới đang chờ trước commit, xóa lựa chọn chưa gửi; vẫn giữ bài đã nhận và cho reload/read/export nếu consent còn hợp lệ, không tự đổi sang nền. Khi người dùng chủ động chọn bản nền thì mở rõ bản nền; không mô tả là bài tiền mới. Tắt kỹ thuật không phải rút đồng ý. Chữ giải thích trạng thái/nút mới pending theo R15, không viết mới privacy/consent/crisis/safety và không giải thích enum/khóa/lỗi máy chủ.
5. Diễn tập bốn chuyện tổng hợp, bản lưu/export, phiên cũ, đồng thời và withdrawal. Kiểm reader cũ/mới và quyền xóa sau tắt cờ; không dùng dữ liệu thật.

## 10. Ma trận AC, kiểm chứng và bàn giao

| AC #709 | Bằng chứng tài liệu | Test runtime bắt buộc, chưa chạy trong #709 |
|---|---|---|
| AC1 | Mục 2: money, bốn mã, chọn đơn, Daily-only, DTO và voice | #711: cả bốn chuyện; thiếu/sai/mảng/số tiền/free text/extra từ chối 400/422, JSON không `input`, body hay validation context riêng tư. Lens cũ với direct/roast vẫn như cũ. Money + direct/vắng voice chỉ renderer xác định sẵn; money + roast 422 trước plan/job/AI. Purpose khác Daily và ba DTO downstream từ chối money, kể cả lens giả + revision tiền |
| AC2 | Mục 3–6; US-03 §25, US-05 §21; data map | #711: replay đúng revision, hai chuyện/phiên bản đồng thời chỉ một active; đổi owner không trùng dấu; xoay k1→k2 đọc/replay/dedupe/lọc lịch sử đúng bản k1, đua rotation không nhân đôi active; key thiếu từ chối; DB không money/prose/chuyện plaintext hoặc hash không khóa. #712: reload/sang ngày không tự điền chuyện, save/list/open/unsave không queue offline; no-store cả list, không nhãn/snippet chuyện tiền; rút xóa toàn state kể cả response tới muộn |
| AC3 | Mục 2 và delta US | #710: cả bốn note/việc nhẹ/việc thường cùng #705, không số tiền/giả định thiếu/nợ/sự kiện. #711 validation JSON không phản chiếu input và evidence invariants giữ nguyên. #712: bốn nhãn và thông báo cờ tắt đạt AC3/R15, status pending không được phục vụ; không suy từ mood/history hoặc restore form khi reload/ngày mới |
| AC4 | Mục 6–8/data map: nguồn chính thức đọc 25.11.2026, privacy cần owner | Đầu việc consent: cancel zero rows, missing/stale/revoked/version/khác chủ, withdraw đua create/read/list/history/saved/save/export; test rút khi export đang tạo file/trước handoff, file tạm dọn và export sau rút không chứa dữ liệu tiền. Restore DB trước mốc rút với journal mới hơn nằm ngoài snapshot vẫn xóa; receipt purge đúng hạn hữu hạn, reaccept không hồi sinh; tuổi/legacy/account delete |
| AC5 | Mục 3/8/9: lựa chọn, nguồn đã kiểm, rollback BE và UI | #711/#712: fixture cũ/mới, tắt giữa phiên và sau ghi; read/reload/export/unsave/withdraw/delete tiếp tục, create/save mới bị chặn. Diễn tập SHA sàn BE+UI, client cũ nhận danh sách đã lọc, không crash/khôi phục bản đã rút |

| Đơn vị bàn giao | Phạm vi và điều kiện |
|---|---|
| #709 | Quyết định/data map, delta US-03/US-05; reviewer độc lập kiểm diff, từng nguồn và tối thiểu hai kết luận. Bằng chứng test tại [biên bản](../reviews/2026-11-25-pr-932-antigravity-round-1.md), chưa thay verdict đúng commit cuối |
| #710 | Nội dung/hai mức việc, bốn nhãn theo AC3/R15; status pending không phục vụ; không soạn chữ nhạy cảm |
| #711 | Contract DTO/voice/lỗi redact; regenerate OpenAPI/client; HMAC key ring/lookup đa khóa/đồng thời; không plaintext money; flags/consent fence mọi API kể cả export/list; no-store danh sách saved; lifecycle hidden root/saved; backend rollback floor. Test readings, share, experiments, resonance, history, saved, export, withdrawal/restore/receipt TTL. Guard privacy phải kiểm trường mới, provider allowlist/public contract |
| Đầu việc consent và /privacy | Chưa có Issue/người nhận xác nhận. [Phiếu đầy đủ](../reviews/2026-11-25-pr-932-antigravity-round-1.md#phiếu-issue-consent-và-privacy), AC mục 6, owner copy/version; export/withdraw race, nguồn journal độc lập và hạn receipt hữu hạn là điều kiện trước bật |
| #712 | Chọn đơn/consent/không tự điền sau reload/ngày mới; stale session/response; cờ tắt không tự đổi bài, chặn save mới; preview bản nền có xác nhận; saved list không nhãn/snippet tiền, no-store, không offline queue và clear khi rút; SHA sàn UI đọc/history/saved, client cũ ẩn an toàn; 360/390 px, keyboard/screen reader, target ≥44 px; copy pending AC3/R15 và AC30 |
| #690 / trước bật | Canary cả mã, money và prose ở DB plaintext/log/network/URL/referrer/error/cache/filename/share image; cố ý rò một ca để chứng minh báo đỏ. Native riêng iOS/Android: backup/cache/file tạm/permission/sheet cleanup; restore có journal ngoài snapshot |

AI tests phải bật cấu hình AI chung và chứng minh application enqueue, worker, adapter/provider không nhận money, kể cả voice=direct/roast và request bị từ chối. Guard nền không chứng minh runtime money. Tests ma trận này phải được cài và chạy ở task triển khai, không ghi PASS khi chưa có code. `pnpm check`, Author check và verdict phải chạy/đọc trên đúng commit cuối trước merge; kiểm bản phát hành/native/store cần cấu hình triển khai, chưa làm trong #709.

Cổng tài liệu có thiết kế và nguồn đối chiếu; còn review độc lập delta, issue consent/phân công, hạ tầng khóa/journal được phép, runtime tests, retention/backup/native và hồ sơ/store theo bản phát hành. Không thu dữ liệu, cấp quyền hay phát hành từ thay đổi tài liệu này.
