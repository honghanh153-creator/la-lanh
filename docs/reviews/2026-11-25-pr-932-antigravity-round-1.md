# PR #932: xử lý phản biện Antigravity vòng 1

Ngày kiểm: 25.11.2026. Agent sửa: Codex theo yêu cầu owner, Claude điều phối/mở PR theo body PR. Task gốc #709 giao Claude thực hiện/Codex review. Antigravity đã phản biện; bản sửa này vẫn cần người review độc lập, không tự duyệt.

Branch `agent/codex/issue-709`, baseline/PR head khi đọc `04bb5a775682bed00ec590f67cdbbd52c7fa2068`. Thay đổi chưa commit/push theo yêu cầu. Chỉ tài liệu, không triển khai hoặc bật money, không đổi `.github`, `scripts/collab-*` hay luật owner. Claim PR hiện do phiên `coordinator` giữ; không giành/force-release, chỉ sửa trong checkout owner giao cho lượt này. Không sync hay sửa checkout khác.

## Nguồn và phạm vi đã kiểm

- Đã đọc AGENTS.md, luật owner R1–R17, quy trình cộng tác/phát triển/checklist, PRD §7.2, SRS §7, product plan, kế hoạch 7 tuần, US-02/03/05/23 và code được dẫn trong ADR §8.
- GitHub connector đã đọc #709, #710–#712, #690, hub #686, PR #932 và phản biện [7164631937](https://github.com/honghanh153-creator/la-lanh/pull/932#issuecomment-7164631937), verdict [PR #395](https://github.com/honghanh153-creator/la-lanh/pull/395#issuecomment-6765202453). Issue runtime còn mở; các assignee chưa được xác nhận, không coi metadata agent là đã nhận việc mới.
- Nguồn chính thức luật Việt Nam, Apple/Google, RFC 2104, OWASP và Pydantic đã mở ngày 25.11.2026; đường dẫn, phần đọc và kết luận trong [ADR §8](../decisions/2026-11-25-goc-tien-bac-kien-truc.md#8-nghiên-cứu-g1-và-nguồn-ac5). PDF NĐ bản ký không có text trích xuất; dùng bản Công báo chính thức đọc được thay cho OCR cũ. Không xác nhận hồ sơ pháp lý/store đã nộp hay đã đủ nghĩa vụ vận hành.

## Phản hồi từng điểm

| Điểm | Kết luận | Đã sửa | Phần còn thiếu |
|---|---|---|---|
| 1, P1: nguồn/G1/US | Đồng ý | ADR §7–8 và data map ghi ngày/link/kết luận chính thức; thêm US-03 §25, US-05 §21, liên kết ranh giới downstream | Review độc lập delta trước bật; hồ sơ pháp lý/store phải khớp triển khai thực tế |
| 2, P1: HMAC/canonical/rotation | Đồng ý | ADR §4, data map: lens theo góc, scope không chuyện/content version; plan/revision riêng; key ring độc lập guest key; tìm đa khóa trước insert, transaction fence không đổi khi rotation | #711 triển khai/tests; cấp secret/quyền là owner action, chưa làm |
| 3, P1: SavedNote/plaintext | Đồng ý | ADR §4–6, data map, US-05 §21: saved_note giữ hidden root lâu dài tới bỏ lưu/rút/xóa; neutral list/no-store cả list; cấm literal money ở mọi cột đọc/lưu/projection plaintext | Tests DB/retention/list/native ở #711/#712; ngoại lệ guest server-only cần review |
| 4, P1: export/restore/receipt | Đồng ý | ADR §6/data map: export và mọi list/read/write cùng fence; hủy/dọn file khi rút thắng; nguồn journal độc lập DB restore; hạn receipt/marker hữu hạn L/B/D, không reset sau restore | Issue consent chính thức, căn cứ và giá trị L/B, proof retention, backup/restore/race tests chưa có; hạ tầng/quyền mới nếu cần phải owner |
| 5, P1: DoD/task/vai trò | Đồng ý | Sửa vai trò theo task gốc và PR; dời nhật ký khỏi ADR; có phiếu Issue consent bên dưới; đã thử pnpm check | Chưa có pnpm/dependencies, Author check/verdict đúng commit cuối; công cụ tạo Issue và ghi PR bị chặn nên chưa có số Issue/người nhận xác nhận. Chưa đủ điều kiện tuyên bố hoàn tất/merge |
| 6, P2: flag-off/UI rollback | Đồng ý | ADR §9–10, data map, US: tắt kỹ thuật vẫn read/reload/list/export/unsave/rút/xóa, chặn create/save mới; không tự đổi bài. SHA sàn BE và UI, API lọc client cũ trước phân trang/count | SHA sàn và diễn tập chỉ có sau triển khai #711/#712, không phải đã chạy |
| 7, P2: DTO/voice | Đồng ý | ADR §2/data map/US: census đủ bốn DTO nhận lens hiện đều forbid; ba downstream reject money/provenance; SavedNoteRequest ID-only. Money direct deterministic, roast 422 trước planner/AI | Sinh lại và kiểm toàn OpenAPI/HTTP tests ở #711 |
| 8, P2: test matrix | Đồng ý | ADR §10 và AC delta US bổ sung JSON lỗi không input, money+voice, rotation, export/withdraw race, reload/ngày mới, copy pending/R15/AC3, saved/no-store/offline/clear-state | Đây là tiêu chí test giao triển khai, chưa có runtime money để chạy |
| 9, P3: nhật ký ADR | Đồng ý | Bỏ SHA/checkout/offline/commit/push/test diary khỏi ADR; giữ ngày nguồn, quyết định và cổng triển khai. Nhật ký/bằng chứng ở file này | Biên nhận cuối trên GitHub và review đúng commit do điều phối hoàn tất sau lượt sửa |

## Kiểm thử tại checkout

| Lệnh/kiểm tra | Kết quả thực tế | Giới hạn |
|---|---|---|
| `node --test scripts/research-sources.test.mjs scripts/verify-mobile-config.test.mjs` | PASS, 7/7 | Test guard nền, không xác minh runtime money |
| `node scripts/verify-privacy.mjs` | PASS | Runtime hiện chưa có money |
| `node scripts/verify-no-mock-runtime.mjs` | PASS | Không phải test tính năng money |
| `node scripts/verify-mobile-config.mjs` | PASS | Không thay smoke test iOS/Android |
| `git diff --check` | PASS | Kiểm whitespace, không thay review nội dung |
| Python kiểm link/anchor Markdown trên cả năm file | PASS, 54 link tương đối/anchor, 0 lỗi; không có đường dẫn máy bị cấm | Không xác minh URL mạng |
| Python AST census request DTO trong `apps/api/app/api` | PASS, đúng 4 DTO nhận lens, cả 4 có extra=forbid | Kiểm mã hiện có, không chứng minh HTTP money tương lai |
| `pnpm check` | Không chạy được, exit 127, `pnpm` chưa cài trong môi trường; cũng chưa có node_modules/venv của checkout | Cần môi trường CI/author-check có dependencies, không ghi PASS |
| `node scripts/collaboration-inbox.mjs` | Exit 1, CLI không kết nối api.github.com | Đọc task/PR bằng connector thay thế; không khẳng định inbox toàn repo đã kiểm hết |

Không dùng `research-sources --base HEAD --head HEAD` vì kiểm zero-file không chứng minh bản sửa hay nguồn. Không có code/runtime tests money trong #709; test matrix ADR §10 là việc phải thực hiện ở task triển khai. Các test không cần mạng ở trên đã xanh. Chưa có kết quả đầy đủ pnpm check, native/store/release, Author check hay verdict độc lập cho commit cuối.

## Phiếu Issue consent và /privacy

Trạng thái: **bản nháp để điều phối tạo Issue, chưa có số Issue, chưa có người nhận xác nhận**. Đã tìm Issue liên quan bằng connector; chưa tìm được task riêng tương ứng. Lần tạo Issue và lần đăng bàn giao PR đều bị công cụ từ chối: `MCP tool call requires approval, but approval policy is never`. Không coi là đã tạo/đăng, không lách sang đường ghi khác.

Tiêu đề: Góc Tiền bạc: consent riêng, withdrawal và yêu cầu cập nhật /privacy trước bật.

Thuộc hub #686, phụ thuộc quyết định #709, phối hợp #711/#712. Cỡ L vì có API/luồng dữ liệu cá nhân mới. Đề xuất Claude thực hiện, Codex review; điều phối phải xác nhận người nhận trước bắt đầu. Mặc định tắt; không cấp secret/IAM, không phát hành, không viết mới chữ privacy/consent/crisis/safety.

Tiêu chí đạt:

1. Owner cung cấp/duyệt chữ privacy/disclosure/consent và version bất biến; không tự viết mới. Consent riêng trước POST chuyện đầu tiên, không chọn sẵn, cancel zero rows và vẫn dùng bản nền. Owner bật thu dữ liệu mới theo R2.
2. API accept/status/withdraw kiểm owner, CSRF/Origin, version hiện hành; không tin client. Dữ liệu vẫn tắt khi chưa đủ approval; generation identity cho lần đồng ý mới phải có thiết kế schema được review.
3. Create/read/list/history/saved/save/export/withdraw cùng fence quyền tới response/commit/handoff. Export bị rút giữa lúc tạo hoặc trước giao phải hủy, dọn file/buffer; export sau rút không chứa dữ liệu tiền hay receipt chờ dọn. Không hứa thu hồi file ngoài app đã giao trước rút.
4. Xóa money plan/revision/projection/saved_note và hidden root không còn con, không xóa bản nền/chart/account. Retry không hồi sinh dữ liệu; reaccept dùng lần quyền mới.
5. Journal/replay độc lập DB snapshot restore, marker bền vững trước báo rút thành công; replay rồi mới mở traffic/jobs. Dịch vụ/quyền mới nếu cần là owner gap, không tự cấp.
6. Chốt căn cứ và giá trị hữu hạn L giữ bằng chứng consent đã rút, B hạn mọi backup còn phục hồi. Purge receipt chính trước rút + L; bản backup kể cả sau rút trước purge phải hết khả năng phục hồi, và marker phải được dọn trước D = rút + L + B + 6 giờ. Restore không làm lại đồng hồ. Kiểm nghĩa vụ chứng minh NĐ 356 Điều 6 và chữ owner duyệt. Chưa chứng minh hạn thì giữ tắt.
7. Tests: missing/stale/revoked/version, khác chủ/gọi trực tiếp/cancel; withdraw đua create/read/list/history/saved/save/export ở từng fence; file tạm cancel/lỗi/rút, purge đúng L/D; reaccept và account delete; restore trước rút vẫn không hồi sinh từ backup cũ. Native iOS/Android kiểm riêng.
8. Trước bật/phát hành, data map/privacy/store/hồ sơ xử lý và chuyển xuyên biên giới khớp cấu hình thật; tests và pnpm check đầy đủ trên commit cuối, Author check/verdict độc lập đúng SHA. Phiếu này không xác nhận đã nhận việc hoặc đã triển khai.

## Khoảng trống cần owner và điều phối

| Người xử lý | Khoảng trống | Mặc định an toàn |
|---|---|---|
| Owner, R2/R13 | Cấp khóa HMAC riêng/key ring; xác định nguồn journal độc lập có cần quyền/dịch vụ/chi phí mới | Chỉ thiết kế, không tạo secret/IAM/mua dịch vụ |
| Owner, R2 | Chữ privacy/consent/disclosure/rút/xóa và cho phép dữ liệu mới | Không soạn/phục vụ chữ nhạy cảm mới, không thu |
| Owner, R12 | Phát hành và khai báo store theo bản được duyệt | Không main/deploy/release |
| Điều phối | Tạo Issue consent từ phiếu, xác nhận người làm/review; đăng biên nhận lên #709/PR #932 khi công cụ ghi được phép | Không giả đã có Issue hay cam kết nhận việc |
| Điều phối/reviewer độc lập | Commit/push theo quy trình ở lượt được phép; chạy pnpm check/CI, review delta và verdict/Author check đúng SHA cuối | Không tự ghi APPROVE hay PASS |

AC1–AC3 đã có quyết định và test bàn giao; AC4/AC5 đã bổ sung nghiên cứu nguồn chính thức và rollback. DoD #709 còn thiếu kiểm toàn bộ, Issue consent/phân công và review độc lập đúng commit cuối. Các AC runtime trong ma trận vẫn chưa thực hiện. Không có P1 nào bị bác; chấp nhận phản biện không đồng nghĩa mọi cổng đã hoàn tất.
