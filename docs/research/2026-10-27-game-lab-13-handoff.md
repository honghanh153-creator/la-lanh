# Game lab 13: bàn giao cho Claude

Ngày 27/10/2026. Người làm: Codex. Reviewer và người nghiên cứu mở rộng được đề nghị: Claude. Đây là PR prototype, không phải duyệt triển khai hoặc release.

## Quyết định và phạm vi

Owner yêu cầu tự chốt tính cách mặc định, bổ sung Sĩ số +1 kiểu phá án, làm rõ cách suy luận người thừa, thêm lên màn và đồ họa, rồi bàn giao bằng PR. Owner đã chọn **chỉ bàn giao trong PR, không tạo thêm Issue**. Không tự đánh thức Claude hay chạy agent trả phí.

Đã chốt cho bản thử: toàn bộ nhân vật là hư cấu 18+, archetype cung và tarot do tác giả gán; tendency chỉ đổi cách đối đáp. Sĩ số +1 mở mặc định option ảnh điểm danh; option hành trình vẫn có thể thử ngay. Mỗi option có ba vụ riêng, không XP, coin, streak hay manh mối trả phí. Chưa có phương án mỹ thuật cuối được owner chọn.

Bản chạy bắt đầu ở [prototype/game-lab-13/index.html](../../prototype/game-lab-13/index.html). Có liên kết qua vụ cà phê, hai bộ hình riêng, nhân vật tách lớp, popup profile/khám nguồn/tarot/kết thúc và tiến độ mở vụ. Câu thoại, đồ vật và nguồn đều là fixture tác giả, không hồ sơ người dùng thật.

## Chốt tính cách mặc định

| Vai | Archetype minh họa | Tính cách và tendency |
|---|---|---|
| Hạnh | Cự Giải / Temperance | Chu đáo; nghe hết câu hỏi, nhắc không quy chụp |
| Quân | Song Tử / The Magician | Tò mò; nói nhiều ý, hợp hỏi từng bước |
| Minh | Thiên Bình / Justice | Khéo nói; hỏi cụ thể để giữ đúng phạm vi |
| An | Xử Nữ / Justice | Ngăn nắp; hỏi nguồn và mốc trước |
| Bình | Song Tử / The Magician | Hoạt ngôn; đề xuất nhiều cách giải thích |
| Chi | Sư Tử / The Sun | Nhiệt tình; hợp câu hỏi ngắn từng ý |
| Duy | Kim Ngưu / The Emperor | Điềm tĩnh; muốn kiểm lại quy tắc |
| Hà | Cự Giải / Temperance | Quan tâm nhóm; tách lỗi dữ liệu khỏi đánh giá người |
| Linh | Bảo Bình / The Star | Tò mò; thích thử từng giả thuyết |

Các cung không được tính từ dữ liệu sinh; không phải tuyên bố về người thuộc một cung trong đời thật. Popup nói rõ điều này. Cả ba kiểu Hỏi nhẹ/Hỏi thẳng/Trêu nhẹ chỉ đổi giọng, không thêm sự kiện hoặc alibi. Tính cách không là đầu vào solver.

## Sĩ số +1 là nhánh khám phá, không thay luật gốc

Nguồn so sánh là PR93 tại `0c3a2ab3266ab764a2474265ca7081df27562705`, `docs/foundation/game-line/si-so-cong-1-prd.md`, SRS và G41–G47. Bản gốc là Ma Sói 15–50 người, 4/5 vòng; người thứ N+1 là bản ghép hệ thống. Các vai Kẻ Bị Nhập/Hồn, trục xuất và Akinator không được triển khai ở đây.

Nhánh lab dùng sáu hồ sơ mô phỏng của năm vai hư cấu; đúng một hồ sơ do máy ghép thừa. Tìm hồ sơ lỗi, không chọn ai trong một tập thể thật là người không thuộc về. Mỗi vụ có mã nguồn/thời điểm mới; đổi đạo cụ hoặc lịch quét giữa các vụ không sửa quá khứ của vụ trước.

### Option ảnh, mặc định

| Vụ | Nguồn cần kiếm và ghim | Phép suy luận | Đáp án fixture |
|---|---|---|---|
| P1, 09:10 | Một ảnh huy hiệu | Bỏ một hồ sơ để khớp 3 Sao, 2 Trăng, 0 Tam giác | Linh |
| P2, 10:20 | Ảnh huy hiệu và bìa sổ cùng lần điểm danh | Mỗi nguồn riêng cho nhiều ứng viên, giao hai điều kiện mới duy nhất | Bình |
| P3, 11:30 | Ba ảnh huy hiệu, bìa sổ, mũi tên trên phiếu | Hai bảng đầu còn An/Duy; bảng thứ ba mới tách | Duy |

Mũi tên in trên phiếu không phải tay thuận. Bìa sổ không phải màu áo avatar. Thứ tự vật trong các ảnh cận độc lập không dùng để nối danh tính. Các con số được render trực tiếp từ fixture, không đọc chữ sinh trong tranh. Mỗi bộ đếm đủ năm vật và ảnh có phạm vi kiểm đầy đủ, giả định này hiện trước khi chơi.

### Option hành trình

Sơ đồ chung: Thư viện —1 phút— Sảnh —2 phút— Phòng máy —1 phút— Lớp. Không lối tắt, có thể chờ. Mỗi dòng hồ sơ là hai lượt quét máy cùng định danh, không phải lời khai được phép nói dối.

| Vụ | Ràng buộc mới | Phép suy luận | Đáp án fixture |
|---|---|---|---|
| R1, 08:50 | Thời gian tối thiểu | Một hồ sơ đi đoạn cần 4 phút trong 2 phút | Linh |
| R2, 09:40 | Cả 5 hành trình thật phải qua P | Tính cả đoạn quay lại, S→P→S→T cần 5 phút, không phải 4 | Hà |
| R3, 08:50 | Cổng S↔P ngừng nhận lượt mới 08:51–08:54; mở 08:55 | Lượt 08:50 được hoàn tất; người tới trễ phải chờ; L→T tới sớm nhất 08:58 chứ không 08:57 | Duy |

Giờ đến muộn hơn mức tối thiểu vẫn hợp lệ vì có thể chờ. Solver dùng nguồn trong vụ, không một cờ hung thủ kín. Prototype client-side không giữ bí mật chống người đọc source; cần kiến trúc riêng nếu làm multiplayer thật.

## AC riêng của prototype

| ID | Điều kiện | Trạng thái bằng chứng |
|---|---|---|
| LAB-01 | Tính cách có default và 3 giọng; không đổi kết quả solver | Test model và DOM; cần owner đọc/chơi |
| LAB-02 | Hai bộ ảnh phòng/nhân vật riêng, có animation trong hiện trường | Asset đã xem, CSS có chuyển động; browser timing/layout chưa kiểm |
| LAB-03 | Sáu vụ đều có đúng một nghiệm từ các nguồn | 33 test model |
| LAB-04 | Thiếu nguồn hoặc ghim thiếu: không chấm đúng/sai danh tính | Model + DOM, mọi ứng viên và mỗi nguồn thiếu |
| LAB-05 | Sai không mất lượt, đúng mới mở vụ kế; hai option giữ tiến độ riêng | Model + DOM đi hết sáu vụ |
| LAB-06 | Thử bỏ hồ sơ chỉ tác động bảng giả thuyết, không sửa nguồn | Pure model + trạng thái UI riêng |
| LAB-07 | Tarot không nói tên đáp án hoặc mở nguồn chưa kiếm | Rà copy; không nối tarot vào solver |
| LAB-08 | Coffee giữ GT/EV, 11 điểm, Q1, T2; không tự điền đồ riêng | 22 vòng DOM; đối chiếu nguồn 05–09 |
| LAB-09 | Keyboard, focus popup, reduced motion, dừng cử động | DOM/stylesheet; thiết bị/browser thật chưa kiểm |
| LAB-10 | Không thu dữ liệu thật/API/SDK/storage xuyên phiên | Rà source, không backend; không phải audit deployment |

AC production gốc, G41–G47, multiplayer, chống gian lận, sự đồng ý người thật, deletion/retention production và nhãn kho chưa được chứng minh. Các quyết định owner/counsel và KS-19/KS-26 của nguồn giữ nguyên; không dùng prototype để mở gate pháp lý.

## Security, privacy và chi phí

Inventory chỉ có tên vai hư cấu, archetype, thoại, props/bản ghi tác giả và trạng thái trong bộ nhớ của tab. Không form tên thật, ảnh thật, ngày/giờ/nơi sinh, chart, mood hoặc quan hệ; không cookie, persistent storage, analytics, external SDK, invite token, API hoặc backend. Reload/reset bỏ trạng thái runtime, không tuyên bố xóa dữ liệu browser/cache bằng hiệu ứng giao diện.

Ảnh tạo bằng công cụ sinh ảnh tích hợp, prompt và asset nằm trong PR. Không gọi API trả phí của app, không chạy Claude tự động, không production/server/DB/IAM/Luna, không merge/deploy. File font/script/image đều local. Không có endpoint công khai mới hoặc thay API/schema/store declarations.

Chưa kiểm layout/animation trong browser; công cụ quan sát file cục bộ bị chặn ở phiên trước, không lách qua bề mặt khác để quan sát. Phân biệt DOM test với visual QA. Tài liệu GT06 dành cho tác giả nằm trong docs nguồn, không nạp vào client coffee hay đường preview. Source PR công khai chứa đáp án fixture, nên không thể dùng làm ván bí mật thật.

## Claude cần nghiên cứu mở rộng

1. Chơi cả sáu vụ và hai bộ hình, không chỉ đọc code. Kiểm người mới hiểu được trong 30 giây phải tìm cái gì, bằng gì, khi nào đủ kết luận. Đo thời gian tới phép suy luận đầu tiên, số lần đoán mò và tỷ lệ hoàn thành.
2. Stress-test suy luận: bài có một nghiệm không, thông tin đã mở có đủ không, có đáp án rò qua art/đối đáp/tarot/tên file không, có trường hợp người thật hợp lệ bị coi là hồ sơ thừa do thiếu dữ liệu không. Tách thử giả thuyết, nguồn đã kiểm chứng và lời nói.
3. Đề xuất lộ trình nhiều vụ có thay đổi kỹ năng chứ không chỉ đổi số: đối chiếu nguồn, chuỗi thời gian, checkpoint, góc nhìn/ảnh phản chiếu có provenance, ghép lịch sự kiện. Mỗi đề xuất cần dữ liệu mẫu và chứng minh một nghiệm, không chỉ pitch.
4. Nghiên cứu primary sources về game suy luận/co-op và viral loop. Phân biệt bằng chứng hiệu quả với suy đoán. Đề xuất 2–3 format thử nhóm 2–6 người/solo, thời lượng, cơ chế trao đổi thông tin và phép thử kéo bạn bè; không ép chia sẻ hoặc đăng chuyện cá nhân.
5. Tìm cách chiêm tinh/tarot xuyên suốt bằng nhân vật, lời thoại, cách đặt câu hỏi và ngôn ngữ mỹ thuật. Không biến cung thành định kiến hoặc năng lực biết đáp án. Cần thử xem lớp này giúp nhớ game hay làm người mới khó hiểu.
6. Lập ma trận art production: phòng, sprite idle/blink, đạo cụ, góc cận cảnh và source ảnh trước/sau challenge. Ưu tiên một hướng được owner chọn, giữ vị trí/đạo cụ nhất quán; không dùng tranh sinh làm nguồn tự phát. Kiểm mobile 360/390, keyboard, tương phản và reduced motion bằng browser thật.
7. Đối chiếu với PR93, privacy và luật/platform từ nguồn chính thức nếu đề xuất xử lý dữ liệu người thật hoặc phát hành. Mặc định tiếp tục chỉ nhân vật hư cấu 18+. Không coi request chốt personality là duyệt thu thập hoặc khai thác profile thật.
8. Trả báo cáo có khuyến nghị giữ/bỏ từng option, rủi ro, bằng chứng và kế hoạch nhỏ tiếp theo. Chưa sửa apps/web/apps/api, chưa thực hiện multiplayer/backend/AI hoặc tự duyệt ngân sách.

## Prompt gửi Claude

> Đọc AGENTS.md, CLAUDE.md và quy trình cộng tác, chạy inbox trước. Nhận PR game-lab-13 tại SHA head thực tế do owner gửi. Chỉ bàn giao trong PR, không tạo Issue mới. Đọc brief `docs/research/2026-10-27-game-lab-13-handoff.md`, README/AGENTS scoped, model và prototype. Mở bản chạy, thử Sĩ số +1 cả hai option và sáu vụ, hai bộ hình, cùng personality/đối đáp vụ cà phê. Chạy `node --test prototype/game-lab-13/model.test.cjs`, `node prototype/game-lab-13/ui-check.cjs`, `node prototype/game-lab-13/coffee/check.cjs`. Test DOM không phải visual QA. Rà tính duy nhất của lời giải, nguồn thiếu, rò đáp án, tăng độ khó thực chất, UX/mobile và cách gắn tarot/chiêm tinh không dùng làm chứng cứ. Nghiên cứu mở rộng theo 8 mục trong brief, có nguồn primary và tách kết quả đã thử khỏi giả định. Giữ nguyên nhánh Ma Sói PR93, GT/EV cà phê và toàn bộ gate owner/counsel/KS-19/KS-26. Không thu profile/ngày sinh/ảnh thật, không sửa runtime sản phẩm, merge, deploy, gọi provider hoặc agent trả phí. Đăng nhận xét và bàn giao trong PR; nếu review thay đổi hiện tại, ghi `Review verdict: APPROVE | REQUEST_CHANGES @ <full SHA>` đúng head. Sau nghiên cứu chỉ đề xuất phạm vi tiếp theo chờ owner chọn.
