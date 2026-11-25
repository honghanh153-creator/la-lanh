# PR #932: xử lý phản biện Antigravity vòng 1

Ngày kiểm: 25.11.2026. Agent sửa: Codex theo yêu cầu owner, Claude điều phối/mở PR theo body PR. Task gốc #709 giao Claude thực hiện/Codex review. Antigravity đã phản biện; bản sửa này vẫn cần người review độc lập, không tự duyệt.

Biên bản lịch sử vòng 1. Đã đối chiếu lại GitHub ngày 25.11.2026: bản sửa vòng 1 đã lên PR #932 tại commit `b411421e1425a9c86c7e0c1f52c5c4b43ee71485`; Issue consent và /privacy là [#935](https://github.com/honghanh153-creator/la-lanh/issues/935). Issue ghi chưa ai nhận việc; không coi metadata phân công là xác nhận. Kết quả lượt sửa cuối ở [biên bản vòng 2](2026-11-25-pr-932-antigravity-round-2.md). Chỉ tài liệu; không triển khai hoặc bật money.

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
| 4, P1: export/restore/receipt | Đồng ý | ADR §6/data map: export và mọi list/read/write cùng fence; hủy/dọn file khi rút thắng; nguồn journal độc lập DB restore; hạn receipt/marker hữu hạn L/B/D, không reset sau restore | Issue #935 đã tạo; xác nhận người nhận, căn cứ và giá trị L/B, proof retention, backup/restore/race tests chưa có; hạ tầng/quyền mới nếu cần phải owner |
| 5, P1: DoD/task/vai trò | Đồng ý | Sửa vai trò theo task gốc và PR; dời nhật ký khỏi ADR; đã có Issue #935; đã thử pnpm check | Chưa có pnpm/dependencies, Author check/verdict đúng commit cuối; #935 chưa có người nhận xác nhận. Chưa đủ điều kiện tuyên bố hoàn tất/merge |
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

Phiếu đã được thay bằng [Issue chính thức #935](https://github.com/honghanh153-creator/la-lanh/issues/935), kiểm ngày 25.11.2026. Không tạo Issue trùng. Issue có AC1–AC8, nhưng ghi chưa ai nhận việc; điều phối cần xác nhận người thực hiện và reviewer độc lập trước triển khai. Thiết kế bổ sung của vòng 2 nằm trong ADR §4/6/9/10 và data map; cần đưa vào triển khai #935/#711/#712, chưa phải runtime đã chạy.

## Khoảng trống cần owner và điều phối

| Người xử lý | Khoảng trống | Mặc định an toàn |
|---|---|---|
| Owner, R2/R13 | Cấp khóa HMAC riêng/key ring; xác định nguồn journal độc lập có cần quyền/dịch vụ/chi phí mới | Chỉ thiết kế, không tạo secret/IAM/mua dịch vụ |
| Owner, R2 | Chữ privacy/consent/disclosure/rút/xóa và cho phép dữ liệu mới | Không soạn/phục vụ chữ nhạy cảm mới, không thu |
| Owner, R12 | Phát hành và khai báo store theo bản được duyệt | Không main/deploy/release |
| Điều phối | Xác nhận người làm/review độc lập cho #935; cập nhật bàn giao #709/PR #932 | Issue đã tạo, chưa có xác nhận nhận việc |
| Điều phối/reviewer độc lập | Commit/push theo quy trình ở lượt được phép; chạy pnpm check/CI, review delta và verdict/Author check đúng SHA cuối | Không tự ghi APPROVE hay PASS |

AC1–AC3 đã có quyết định và test bàn giao; AC4/AC5 đã bổ sung nghiên cứu nguồn chính thức và rollback. DoD #709 còn thiếu kiểm toàn bộ và review độc lập đúng commit cuối do vòng tự động hoàn tất sau khi điều phối đẩy; #935 còn thiếu xác nhận phân công trước triển khai/bật. Các AC runtime trong ma trận vẫn chưa thực hiện. Không có P1 nào bị bác; chấp nhận phản biện không đồng nghĩa mọi cổng đã hoàn tất.
