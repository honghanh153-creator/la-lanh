# PR #932: xử lý phản biện Antigravity vòng 2 (cuối)

Ngày kiểm: 25.11.2026. Người sửa: Codex theo yêu cầu owner; Claude điều phối. Chỉ sửa tài liệu trong checkout được giao, không commit/push, không tự cấp Author check hoặc verdict độc lập. Bản sửa vòng 1 đã lên PR tại `b411421e1425a9c86c7e0c1f52c5c4b43ee71485`, đã đối chiếu qua GitHub connector; thay đổi vòng 2 hiện cần điều phối đưa lên PR rồi vòng tự động kiểm đúng commit cuối. Đây không phải biên nhận merge hoặc triển khai.

## Phản hồi từng điểm

| Điểm | Kết luận | Đã sửa ở đâu | Phần còn thiếu |
|---|---|---|---|
| 1, P1: DoD, Issue, CI và biên nhận | Đồng ý về các cổng; cập nhật trạng thái theo bằng chứng mới | ADR §1/6/10, data map và biên bản vòng 1 thay phiếu nháp bằng Issue chính thức #935. Không coi cổng CI là lỗi phải tự đóng trong sandbox | Vòng 1 đã đẩy. Vòng 2 không commit/push theo yêu cầu. pnpm check, Author check và review độc lập đúng commit cuối do CI/vòng tự động sau khi điều phối đẩy; #935 chưa ai xác nhận nhận việc |
| 2.1, P1: generation và nâng version | Đồng ý | ADR §4/6, data map: một dòng bất biến mỗi E; reaccept/upgrade tạo E mới, retry không nhân đôi. Đọc bản cũ theo đúng E/receipt và quyền version cũ còn hợp lệ, không dùng E mới nhất. Withdrawal purpose đóng mọi E chưa rút; purge nhắm đúng E | #935/#711 migration unique constraint hiện tại, repository/idempotency, quyền version và tests; policy/chữ chưa duyệt giữ tắt |
| 2.2, P1: receipt hồi sinh sau hạn L | Đồng ý | ADR §6, data map: marker giữ mốc rút/purge/D gốc; restore từ purge_at trở đi phải xóa hẳn receipt đúng E, kể cả snapshot chưa có revoked_at. Restore lặp không reset hạn và không đụng E2 | Tests trước/tại/sau purge_at và trong (purge_at,D], restore thật còn thiếu; L/B và căn cứ chưa chốt |
| 2.3, P1: journal qua rotation, tránh xóa E2 | Đồng ý | ADR §6, data map: marker envelope mã hóa/xác thực riêng chứa O/purpose/E/mốc hạn/scheme/key_ids, thay root digest chưa rõ khóa. Tái tính lens HMAC cho mọi P được restore và khóa từng ghi E; xác thực E, xóa con/root đúng E1, giữ E2/nền. Registry/khóa độc lập DB, thiếu khóa/journal giữ traffic/job đóng | Hạ tầng/khóa/quyền cần owner nếu phát sinh; triển khai/replay/restore coverage ở #935/#711 chưa chạy |
| 3.1, P2: nhãn/lọc danh sách Lưu riêng | Đồng ý | ADR §5/10, data map, US-05 §21: nhãn trung tính giống hệt bài nền; DTO không lens/cờ/nhãn riêng/snippet; không lọc góc tiền trong đợt này | #711/#712 kiểm DTO và UI thực tế; không có nhãn mới được tự duyệt |
| 3.2, P2: header tiết lộ dữ liệu | Đồng ý | ADR §5/10, data map, US-05 §21: no-store vô điều kiện cho mọi response riêng tư/list/detail/lỗi, cả user không tiền/rỗng/chỉ nền/cờ tắt; không dò có tiền mới gắn header | HTTP/cache/native tests chưa có runtime money |
| 3.3, P2: lọc client cũ và thực hiện quyền | Đồng ý | ADR §9/10, data map, US-05 §21: tập lens HMAC đủ key/P/E, SQL loại trước sort/cursor/count/phân trang, join revision/root; không lộ số ẩn. Guidance dựa vào khả năng client, copy mới pending; lối web tương thích và xuất toàn bộ/xóa không phụ thuộc danh sách đã lọc là điều kiện bật | #711/#712 phải chứng minh query, count/rỗng/cursor, lối xuất/rút/bỏ lưu/xóa không cần cập nhật app; SHA sàn/diễn tập chỉ có sau triển khai |
| 4.1, P2: voice vắng kế thừa roast | Đồng ý | ADR §2/10, data map, US-03 §25: server luôn dùng direct khi vắng voice, bỏ qua preference/setting cũ; bổ sung ca setting cũ roast | #711 triển khai/HTTP tests; roast tường minh vẫn 422 trước planner/AI |
| 4.2, P2: SavedNoteRequest mơ hồ | Đồng ý | ADR §2/10, data map, US-05 §21: tách khỏi ba DTO cấm money; ID-only/forbid extra vẫn cho lưu money sau kiểm chủ/provenance/generation/cờ | #711 kiểm cả ca được lưu và từ chối; không đổi API runtime trong #709 |
| 4.3, P2: bấm lưu lúc cờ vừa tắt | Đồng ý | ADR §10 và bàn giao #712, data map, US-05 AC-MONEY-S04: bấm lưu mới/lưu lại sau bỏ trên bài đang mở, hủy pending write, không queue, giữ bài và kiểm thông báo R15; copy status: pending không phục vụ trước duyệt | #710/#712 soạn/duyệt câu thường và triển khai test; không viết câu privacy/consent/crisis/safety |
| 5, P3: diễn đạt và nhật ký ADR | Đồng ý | ADR §1 sửa thành cần owner duyệt/cấp secret trước khi bật; bỏ mọi liên kết ADR sang nhật ký phiên. Biên bản vòng 1 bỏ claim/checkout và phiếu nháp, cập nhật #935; chứng cứ phiên cuối ở file này | Điều phối giữ bằng chứng CI/review trên PR sau khi đẩy |

## Nguồn đã kiểm

- Nội bộ: AGENTS.md; luật owner R1–R17; quy trình cộng tác/phát triển và checklist; PRD, SRS §7, product plan; ADR và US-03 §25/US-05 §21; `ConsentRow` trong `apps/api/app/domains/guest/tables.py` xác nhận unique `(guest_id,purpose)` hiện tại, chưa hỗ trợ đa generation.
- GitHub connector ngày 25.11.2026: [#709](https://github.com/honghanh153-creator/la-lanh/issues/709), [PR #932](https://github.com/honghanh153-creator/la-lanh/pull/932), [#935](https://github.com/honghanh153-creator/la-lanh/issues/935) và toàn bộ comments #935 (rỗng). Không coi phân công trong body là xác nhận đã nhận việc. CLI inbox không kết nối được GitHub; chưa kiểm được inbox toàn repo.

Đã mở lại nguồn chính thức bằng công cụ web ngày **25.11.2026**:

| Nguồn | Phần đối chiếu và kết luận cho bản sửa |
|---|---|
| [Luật 91/2025/QH15, Công báo](https://congbao.cdnchinhphu.vn/CongBaoCP/VanBan/2025/6/45578/57730-1-2025971-97291-2025-qh15.pdf) | Điều 9–12: giữ bằng chứng theo mục đích; mã hóa vẫn là dữ liệu cá nhân. Không coi reaccept là cho phép hồi sinh dữ liệu đã rút |
| [NĐ 356/2025/NĐ-CP, Công báo số 18](https://congbaocdn.chinhphu.vn/180507251028987904/2026/1/17/cong-bao-so-18-ngay-18-01-46924signed-1768637757042330005940.pdf) | Điều 6, tr. 7–8: consent phải kiểm chứng được, lưu bằng chứng, không mặc định. Nguồn không ấn định L/B của thiết kế; chưa chốt giá trị thay owner/đầu việc pháp lý |
| [Apple App Privacy](https://developer.apple.com/app-store/app-privacy-details/) | Data collection/types: lưu quá request phải xét collected; phân loại tài chính giữ như ADR, không miễn vì mã hóa |
| [Apple App Review 5.1.1](https://developer.apple.com/app-store/review/guidelines/#privacy) | Privacy policy cần nêu retention/deletion; rút consent phải dễ tiếp cận. Client cũ phải còn lối thực hiện quyền được kiểm |
| [Google Data Safety](https://support.google.com/googleplay/android-developer/answer/10787469?hl=en) | Data collection/ephemeral: lưu revision không chỉ xử lý RAM cho request; vẫn cần khai đúng bản phát hành |
| [Google User Data](https://support.google.com/googleplay/android-developer/answer/10144311?hl=en) | Prominent Disclosure & Consent, dòng Full Policy: disclosure/consent trước xử lý khi ngoài kỳ vọng hợp lý. Chữ nhạy cảm vẫn cần owner |

Mô hình generation, SQL lọc và journal là lựa chọn kỹ thuật của dự án, không phải schema/thuật toán do luật hoặc cửa hàng bắt buộc. Đối chiếu nguồn không chứng minh đã triển khai, nộp hồ sơ hay đáp ứng nghĩa vụ vận hành.

## Kiểm tra tại checkout

| Lệnh/kiểm tra | Kết quả | Giới hạn |
|---|---|---|
| `node --test scripts/research-sources.test.mjs scripts/verify-mobile-config.test.mjs` | PASS, 7/7 | Guard nền, không phải test runtime money |
| `node scripts/verify-privacy.mjs` | PASS | Runtime hiện chưa có money |
| `node scripts/verify-no-mock-runtime.mjs` | PASS | Không chứng minh contract money |
| `node scripts/verify-mobile-config.mjs` | PASS | Không thay kiểm thiết bị iOS/Android |
| `git diff --check` | PASS | Whitespace |
| Python kiểm link tương đối/anchor và phạm vi file sửa | PASS: 50 link/anchor, đúng 6 file tài liệu; không đường dẫn máy bị cấm, không link ADR tới nhật ký hoặc trạng thái số Issue lỗi thời | Kiểm tài liệu, không kiểm URL mạng hay runtime |
| `pnpm check` | Không chạy được, exit 127: pnpm chưa cài; checkout không có dependencies | CI/vòng tự động chạy trên đúng commit cuối sau khi điều phối đẩy; không ghi PASS |
| `node scripts/collaboration-inbox.mjs` | Exit 1: không kết nối GitHub | Đã đọc task/PR/#935 qua connector; không giả inbox toàn repo đã đạt |

## Việc còn thiếu và bàn giao

- AC1–AC5 có chỗ trong ADR §2–10, data map và delta US; bản sửa đã khép các điểm thiết kế được nêu. DoD #709 vẫn chờ pnpm check/Author check và reviewer độc lập trên commit cuối; không tự tuyên bố merge-ready. Điều phối cập nhật PR body còn mô tả trạng thái trước vòng 1 và đưa bản sửa này lên PR theo lượt được phép.
- #935 đã tạo nhưng chưa có người nhận xác nhận; điều phối chốt người làm/review độc lập. #710/#711/#712/#935 còn toàn bộ tests runtime trong ma trận ADR §10. Chỉ triển khai mới có thể ghi SHA sàn, kiểm query/HTTP/restore/retention và diễn tập rollback; native/store cần bản build và cấu hình thật. Không nói đã làm sau merge/CI khi chưa có bằng chứng.
- Khoảng trống cần owner: khóa/quyền/chi phí hoặc dịch vụ journal nếu mới; chữ privacy/consent/crisis/safety và version/tính tương thích gắn nội dung đó; cho phép bật thu dữ liệu mới; phát hành/main/deploy. Không tự cấp secret/IAM, chọn dịch vụ hoặc quyết câu chữ. Mặc định không thu và giữ tắt.
- Rủi ro còn mở trước bật: L/B và mọi bản backup phục hồi được chưa xác minh; chưa có migration đa generation, journal/key ring độc lập, purge/restore proof, HTTP/UI/native tests hoặc hồ sơ/store khớp cấu hình. Biên bản này không thay các cổng đó.

## Còn khác ý

không có
