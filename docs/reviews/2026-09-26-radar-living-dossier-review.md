---
title: "Radar Living Relationship Dossier — implementation and QA review"
date: 2026-09-26
status: implemented-for-local-review
scope: radar-private-check-and-consented-invite
---

# Radar Living Relationship Dossier — implementation and QA review

## Kết luận

Phương án 1 đã được triển khai trên đúng flow Radar hiện tại. Kết quả không còn là bốn đoạn diễn giải rời rạc từ một góc chiếu nổi bật nhất. Backend gom nhiều bằng chứng chart thành các cụm có chủ đề, dựng một Pair Signature có cả nguồn lực lẫn điểm cần thương lượng, rồi trả về bốn chương đọc theo tình huống đời thường. UI giữ lớp scan nhanh ở đầu trang và cho mở sâu từng chương khi người dùng muốn.

Bản này sẵn sàng để review nội bộ/local QA. Nó chưa được coi là đủ điều kiện phát hành công khai cho đến khi hoàn tất các release gate ở cuối tài liệu.

## Trải nghiệm đã triển khai

- Hero nêu Pair Signature của đúng cặp đang xem, không dùng một headline chung thay tên cung.
- Ba chỉ số `Bắt sóng`, `Dễ phối hợp`, `Lực cấn` vẫn độc lập, không cộng thành 100 và mỗi chỉ số có receipts giải thích nguồn số liệu.
- Mục lục bốn chương giúp scan nhanh; chương đầu mở sẵn, ba chương còn lại không kéo trang dài mặc định.
- Mỗi chương đi theo thứ tự: ý nghĩa chính → các pattern cụ thể → cảnh đời thường / hai phía cảm nhận / điều nên quan sát → bằng chứng chart.
- Thuật ngữ hành tinh, góc, orb và house overlay nằm sau disclosure `Vì sao Lá đọc vậy?`; người không biết astrology vẫn hiểu phần chính.
- Báo cáo cũ cùng version `radar-result-v2` vẫn có fallback và tiếp tục render.
- Trạng thái rút consent được hiển thị thành terminal state rõ ràng thay vì để trang trống hoặc hành động cũ còn hoạt động.

## Engine và content matrix

Runtime mới sử dụng các theme cluster có giới hạn và deterministic thay cho việc chọn một contact đơn lẻ. Mỗi highlight bắt buộc có một hoặc nhiều evidence IDs nâng đỡ; không có paragraph được thêm chỉ để đủ độ dài.

Các nhánh chính hiện được đọc từ:

- Synastry contacts để tìm nhịp hợp, lực hút, giao tiếp và điểm dễ kích hoạt nhau.
- House overlays hai chiều để tách `bạn có thể cảm thấy`, `người kia có thể cảm thấy` mà không khẳng định nội tâm của người kia.
- Composite aspects để mô tả nhịp chung của hai người khi có đủ evidence.
- Context quan hệ (`crush`, `friend`, …) chỉ đổi cách đưa pattern vào đời thường; không đổi chart facts, Pair Signature hoặc các chỉ số.

Khi evidence mỏng, báo cáo chủ động ngắn lại và nói rõ giới hạn. Trường hợp không có contact đủ điều kiện không còn trả lỗi hoặc chèn nội dung chung chung.

## Sửa lỗi về đúng người đang xem

Trong luồng có consent, hệ thống hiện lưu projection theo góc nhìn chủ hồ sơ A→B nhưng trả ngay cho người nhận projection B→A. Nhờ vậy `bạn` và `người kia` không bị đảo.

Các hành động chấp nhận, từ chối và rút consent được bind với đúng `request_id`. Một tab cũ không thể vô tình tác động lên lời mời hoặc kết quả vừa mở ở tab khác.

## An ninh và data privacy

Không thêm loại dữ liệu, mục đích xử lý, public result endpoint, analytics event, external generation provider hoặc share artifact.

- Projection và metadata không chứa ngày sinh, giờ sinh, nơi sinh, tọa độ hoặc chart input thô.
- Evidence chỉ giữ dữ liệu suy diễn tối thiểu cần cho giải thích, như body/aspect/house category/orb.
- Result tiếp tục được mã hóa khi lưu; TTL, owner delete, recipient withdrawal và no-store behavior giữ nguyên.
- Nickname được render như text và chuỗi dài đã được kiểm tra không phá layout.
- Nội dung vẫn dùng ngôn ngữ có điều kiện; ba chỉ số được mô tả là bản đồ tương tác, không phải xác suất quan hệ thành công.

Đối chiếu đã dùng: [OWASP MASVS-PRIVACY](https://mas.owasp.org/MASVS/12-MASVS-PRIVACY/), [W3C Privacy Principles](https://www.w3.org/TR/privacy-principles/), [Apple Privacy HIG](https://developer.apple.com/design/human-interface-guidelines/privacy) và [Luật số 91/2025/QH15](https://vanban.chinhphu.vn/?classid=1&docid=214590&pageid=27160&typegroup=).

## Verification đã chạy

| Gate | Kết quả |
|---|---|
| Radar API tests | 12 passed |
| Radar web component tests | 3 passed |
| Full web test suite, single worker | 31 files / 98 tests passed |
| API format, lint và typecheck cho phần sửa | Passed |
| Web lint và typecheck cho phần sửa | Passed |
| Production web build | Passed; còn cảnh báo chunk >500 kB đã có từ trước |
| Privacy verifier | Passed |
| Diff whitespace check | Passed |

Full API suite chạy 2026-09-26 còn 5 failures ngoài Radar: bốn test Daily Note và một local product-flow test. Cùng nguyên nhân: reading candidate bị content gate từ chối, route fallback về legacy note nhưng test tiếp tục truy cập projection `None`. Đây là nợ hiện hữu ở Daily Note; toàn bộ Radar suite vẫn pass. Không nên gọi toàn sản phẩm là release-clean cho tới khi nhóm lỗi này được sửa.

## Browser QA

QA được chạy trên một private-check result thật với backend và database local, không dùng mock response.

- Viewport mobile 390 px: `clientWidth = 390`, `scrollWidth = 390`, không có horizontal overflow.
- Có đúng bốn chapter; một chapter mở mặc định.
- Có ba metric evidence disclosure và bốn chapter evidence disclosure.
- Chapter thứ hai mở được bằng phím Enter.
- Console không có warning hoặc error.
- Chuỗi nickname dài và nested evidence không làm vỡ card.

Web là bề mặt QA nhanh; cùng React surface này được đóng gói bằng Capacitor cho iOS/Android, nên sản phẩm đích vẫn là app.

## Code review

Code review: harness-native fallback

Các file Radar trong scope đang là file untracked hoặc nằm giữa một working tree lớn có nhiều thay đổi của các vòng trước. Portable review không thể bao phủ chúng nếu không stage vào index của người dùng, nên không thực hiện thao tác đó. Thay vào đó, sáu lượt review độc lập theo correctness, testing, standards, security, API contract và adversarial đã được chạy trên scope hiện tại.

Các lỗi review tìm được và đã sửa gồm: missing evidence receipts, metric không trace về contact thật, hướng người xem bị đảo, filler ở sparse chart, lặp scene, stale-request substitution giữa nhiều tab, thiếu trạng thái sau withdrawal, nickname dài tràn layout và fallback gắn sai nhãn evidence source.

## Release gates còn lại

1. Sửa 5 lỗi Daily Note trong full API suite để toàn sản phẩm có một baseline xanh.
2. Hoàn tất legal review cho luồng check kín bằng dữ liệu người khác trước public launch, bao gồm purpose, retention, data-subject handling và disclosure copy.
3. Xác nhận scheduled physical purge thực sự chạy trong môi trường production, không chỉ logical expiry.
4. Bổ sung abuse/rate-limit monitoring và runbook xử lý report/withdrawal trước khi mở lượng người dùng lớn.
5. Share Capsule/full-report link vẫn ngoài scope; chỉ triển khai sau khi có consent và disclosure purpose riêng.

## Verdict

`READY FOR PRODUCT REVIEW / LOCAL APP QA`

`NOT YET PUBLIC-RELEASE CLEAN` vì năm lỗi Daily Note và các operational/legal gate nêu trên, không phải vì Radar Dossier còn lỗi chức năng đã biết.
