# Nhìn lại thử nghiệm workflow 3 + 3 (14–19.11.2026)

Codex viết bản này ngày 21.11.2026, trễ hạn 20.11 một ngày. Nguồn chính là các bản ghi soát đêm cuối ngày (`~/.cache/la-lanh-collab/experiment/<ngày>.json` trên máy owner, do `scripts/collab-audit-night.mjs` ghi; không đưa lên repo), gồm bản Claude kiểm lại M2 ngày 15.11. Bản so sánh theo thiết kế tại [`docs/operations/workflow-experiment-2026-11.md`](../operations/workflow-experiment-2026-11.md), đối chiếu code, bài học và retro trong checkout. Claude đã phản biện (mục cuối): đồng ý nội dung, sửa hai chỗ biên tập. Owner chưa chốt kết quả theo §5.

## Kết luận

- Giữ soát đêm, review đúng head và Author check. Các bước này cung cấp bằng chứng để phát hiện cả lỗi báo cáo lẫn lỗi bộ thu số đo.
- Giữ hướng phân loại rủi ro theo file và kiểm toán sau merge để thử tiếp. Chưa đủ dữ liệu để kết luận cách 2-nhẹ tốt hơn cách 1.
- Bỏ kết luận rằng ngày 15.11 có 23 PR merge thiếu verdict. Giữ số gốc 23 cạnh số hiệu chỉnh 0, theo bản kiểm lại của Claude.
- Không dùng số PR thay cho việc đạt AC, số fix-forward thay cho lỗi mới lọt, hoặc sổ bất đồng bằng 0 làm bằng chứng hai bên luôn thống nhất.
- Làm bộ xếp lịch theo đồ thị sau khi giảm WIP và sửa số đo. Độ tin cậy khi chọn bên thắng thấp: mỗi cách chỉ có ba ngày, nhiều luật đổi giữa kỳ và nhiều chỉ số chưa đo được.

## Chất lượng số đo

Định nghĩa gốc nằm ở §4 của [`docs/operations/workflow-experiment-2026-11.md`](../operations/workflow-experiment-2026-11.md). Cách thu nằm trong [`scripts/collab-audit.mjs`](../../scripts/collab-audit.mjs) và [`scripts/collab-audit-night.mjs`](../../scripts/collab-audit-night.mjs).

- **M1 dùng được có giới hạn cho 11–19.11.** Đây là số câu sai tìm thấy trong các báo cáo đã soát. Trường `of` đếm báo cáo, không đếm câu. Vì vậy không được gọi số câu sai chia số báo cáo là tỷ lệ câu sai. Ngày 20.11 chưa đo được vì thiếu nội dung comment, có `body=null`.
- **M2 phải hiệu chỉnh ngày 15.11.** Bản ghi là **23/39 PR**. Bản Claude kiểm lại ngày 21.11 xác nhận cả 23 PR có trusted `APPROVE @ final head` và `Author check: PASS`; số hiệu chỉnh là **0/39**. Các PR này merge từ 00:16 đến 10:09 ngày 15.11, trước mốc đổi luật khoảng 18:00. Đây là lỗi thu số đo, không phải bằng chứng việc bỏ cổng owner gây merge thiếu duyệt. Nguyên nhân chính xác chưa kiểm được; lỗi đọc comment hoặc phân trang mới là giả thuyết.
- **M2 không chứng minh reviewer độc lập.** Hàm `receipt` còn kiểm output Codex và mã băm. Checkout này không có bộ output gốc để kiểm lại độc lập. Theo §0, cách 2-nhẹ vẫn cho Claude cùng quyền trên máy; kiểm toán sau merge chỉ phát hiện sự không nhất quán.
- **M3 dùng được để mô tả số mục được ghi nhận, không dùng trực tiếp làm tỷ lệ lỗi lọt.** Các mục được tính trong dữ liệu đều là `fixforward#…`. Nhiều lỗi đã được Codex thấy trước merge và cho sửa sau theo chính sách P2 không chặn. Cùng một vấn đề còn có thể sinh nhiều issue, như #574, #577 và #578 quanh PR #572. M3 đo cả chính sách ghi nợ, mức thực thi quy trình và lỗi lọt. Trường `of` là số ứng viên được xét, không phải số PR đã duyệt.
- **M4 dùng được như bản chụp sổ, có giới hạn về bằng chứng đóng.** Nền 11–13.11 chưa có sổ tương ứng nên chưa đo được. Các ngày sau có số `done`, nhưng còn `unconfirmed`. Riêng ngày 15.11, M1 đã chỉ ra báo cáo về L13 thiếu bằng chứng là sai vì bằng chứng đã có từ 10:16. Không thể coi mọi mục `done` là đã xác minh, hoặc mọi mục `unconfirmed` là thật sự thiếu bằng chứng. Không cộng các bản chụp hằng ngày thành tổng lời hứa.
- **M5 chưa đo được ở mọi ngày.** Bộ thu ghi thiếu mã việc và tiêu chí đạt trong plan. Không thể so sánh số việc hoàn thành hoặc năng suất theo AC.
- **M6 dùng được để mô tả thời gian của PR đã merge.** Đơn vị là **giờ**. Mỗi giá trị là **trung vị từ mở PR tới merge của các PR merge trong ngày đó**. PR còn mắc trong hàng chưa đi vào số đo. Dữ liệu không có thời gian từng PR nên không tính được trung vị chung của từng cách. Không lấy trung bình hoặc trung vị các trung vị ngày để thay thế.
- **M7 dùng được có điều kiện.** Đây là trung vị số verdict tự động trước merge trên từng PR. Nó dùng cùng nguồn comment với M2, nên cần kiểm lại độ đầy đủ sau khi sửa lỗi đọc comment. Trung vị bằng 1 cũng che các PR cần nhiều vòng.
- **M8 chỉ dùng được để nói sổ đã ghi gì.** Nền chưa đo được. Từ 14–20.11, số bất đồng ghi sổ luôn là 0. Nhưng ngày 19.11, `judgement_unrecorded` ghi **1 bất đồng chưa vào sổ** trên PR #738 về quyền ưu tiên khi giữ chỗ merge. Nhiều ngày khác không đối chiếu đủ vì comment bị bỏ khỏi gói bằng chứng. Không thể kết luận không có bất đồng, bên nào thường thắng, hoặc owner có phải lật quyết định hay không.
- **M9 dùng được cho lượt đã được vòng ghi nhận.** Lượt ngoài bộ đếm có thể thiếu. Ngày 14.11 có 2 lượt đo nền trong tổng 39, giữ nguyên theo thiết kế. Đây chưa phải token, thời gian tính toán hay chi phí tiền. Mốc ≤32 trong bảng đăng ký đã cũ sau các lần nâng trần lên 60 rồi 80; dữ liệu cũng không đủ để kết luận ngày nào vượt trần được phép.
- **M10 chưa đo được ở mọi ngày.** Watchdog chỉ giữ beat mới nhất, chưa có lịch sử câu hỏi gửi owner và các lần kẹt quá một giờ. Không thể kết luận cách nào ít hỏi owner hoặc ít kẹt hơn.

Vì vậy, chưa thể so sánh năng suất theo việc đạt AC, gánh nặng của owner, hiệu quả xử lý bất đồng, tỷ lệ lỗi mới lọt, chi phí đầy đủ hoặc tác dụng của người gác độc lập. Cũng không thể tách chính xác trước và sau 15.11 khoảng 18:00 từ các tổng theo ngày.

## So sánh

Nguồn số là bản ghi soát đêm cuối ngày nói ở đầu bài. Các dãy số đi theo thứ tự ngày trong tiêu đề cột. Bảng theo thứ tự ưu tiên §5: trung thực, chất lượng, tốc độ, rồi chi phí. M8 giữ vị trí theo mã nhưng không dùng để xếp hạng.

| Số đo | Nền 11–13 | Cách 1 14–16 | Cách 2-nhẹ 17–19 | 20.11 riêng |
|---|---|---|---|---|
| M1, câu báo cáo sai | 0; 0; 2. **Tổng 2**, soát 33 báo cáo | 3; 3; 3. **Tổng 9**, soát 113 báo cáo | 1; 1; 4. **Tổng 6**, soát 105 báo cáo | Chưa đo được |
| M2, merge thiếu biên nhận | 0/13; 0/15; 0/13. **Tổng 0/41** | Gốc: 0/9; **23/39**; 0/34, tổng **23/82**. Hiệu chỉnh: 0/9; **0/39**; 0/34, tổng **0/82** | 0/31; 0/14; 0/8. **Tổng 0/53** | 0/11 |
| M3, mục lỗi hoặc nợ sửa sau | 0; 0; 0. **Tổng 0** | 7; 10; 21. **Tổng 38** | 19; 7; 5. **Tổng 31** | 8 |
| M4, ghi xong / mở / quá hạn | Chưa đo được | 6/14/0; 22/5/0; 24/5/0 | 37/7/1; 42/5/1; 45/4/1. Mục quá hạn là L13 | 46/4/1. Mục quá hạn là L13 |
| M5, việc đạt AC | Chưa đo được | Chưa đo được | Chưa đo được | Chưa đo được |
| M6, trung vị giờ mở tới merge | 2,1; 9,2; 8,6. Số PR: 13; 15; 13 | 14,9; 6,6; 0,7. Số PR: 9; 39; 34 | 1,6; 3,1; 23,7. Số PR: 31; 14; 8 | 9,7 giờ; 11 PR |
| M7, trung vị vòng review mỗi ngày | 1; 1; 1 | 1; 1; 1 | 1; 1; 1 | 2 |
| M8, bất đồng ghi sổ | Chưa đo được | 0; 0; 0. Tổng ghi sổ 0 | 0; 0; 0. Tổng ghi sổ 0; ngày 19 có 1 bất đồng chưa ghi | 0 ghi sổ; chưa đối chiếu đủ |
| M9, lượt Codex đã ghi nhận | 19; 21; 26. **Tổng 66** | 39; 81; 61. **Tổng 181**, gồm 2 lượt đo nền ngày 14 | 69; 41; 34. **Tổng 144** | 49 |
| M10, câu hỏi owner và lần kẹt | Chưa đo được | Chưa đo được | Chưa đo được | Chưa đo được |

M4 là số tại thời điểm chụp khoảng 23 giờ, không phải tổng phát sinh trong ngày. Các mục chưa xác minh gồm L21–L23 ngày 14, L13 ngày 15, rồi L11 và L13 từ ngày 16 đến 20.

- **Trung thực chưa có bên thắng rõ.** Cách 2-nhẹ ghi ít câu sai hơn cách 1, 6 so với 9, nhưng số báo cáo và nội dung khác nhau. Ngày 19 vẫn có 4 câu sai. Sau hiệu chỉnh, M2 không phân biệt được hai cách. Các số 0 cũng không giải quyết rủi ro cùng quyền trên máy đã nêu ở §0.
- **Chất lượng chưa chứng minh cải thiện.** M3 giảm từ tổng 38 xuống 31, nhưng cả hai chủ yếu đang đếm fix-forward theo chính sách P2. Số PR merge cũng khác, 82 và 53. Không lấy hai tổng này làm tỷ lệ lỗi. M4 ghi xong tăng, nhưng sổ có thêm mục và có lỗi đối chiếu bằng chứng.
- **Cách 1 phải tách thành ba phần khi diễn giải.** Ngày 14 ở trước thay đổi; ngày 15 trộn trước và sau khoảng 18:00; ngày 16 ở sau quyết định nhưng gói sửa §0c còn được đưa vào dần. M6 là 14,9; 6,6; 0,7 giờ và M9 là 39; 81; 61 lượt. Không quy toàn bộ mức thay đổi này cho cách 1.
- **Các mốc code xác nhận cách 1 không ổn định.** Lịch sử Git ghi #560 merge ngày 15 lúc 18:21. Ngày 16, #590 và #591 merge lúc 14:26 và 14:35, plan tự chạy #594 lúc 14:47, khóa PR #597 lúc 17:06, hai việc nặng #599 lúc 18:47, trần 80 #601 lúc 21:42, hai làn #604 lúc 22:22 và mã ops riêng #603 lúc 23:19. Không có số đo theo từng khoảng này để tách tác dụng. Đây là giới hạn khi thực hiện yêu cầu §0b và §0c, không được tự chia tổng ngày.
- **Cách 2-nhẹ cũng đổi giữa kỳ.** R7 thêm làn Daily trong thử 18–19.11. L50 thêm giữ chỗ merge ngày 18; L51 sửa việc hết hạn; L53 sửa PR đã sẵn sàng bị PR cùng file giữ lại tối 19.11. M6 ngày 19 là 23,7 giờ trên 8 PR, nhưng chưa đủ để gán nguyên nhân cho một thay đổi. Nguồn là [`scripts/collab-lessons.json`](../../scripts/collab-lessons.json), L50, L51, L53, và [`scripts/collab-turn.mjs`](../../scripts/collab-turn.mjs).
- **Chi phí ghi nhận thấp hơn, chưa biết hiệu suất tốt hơn.** Tổng M9 là 144 so với 181, nhưng M5 thiếu nên không tính được lượt trên một việc đạt AC. Cách 2 chạy sau và hưởng phần học, phần code đã làm trong cách 1. Giờ dựng riêng chưa kiểm được. §5 còn nêu khối lượng việc khác nhau và 14–15.11 là cuối tuần.
- **Ngày 20 đứng riêng.** Đây là ngày nhìn lại và có phát hành production theo bối cảnh giao việc. Không đưa số ngày này vào cách 2-nhẹ hoặc quy M3 ngày này cho phát hành. M1 còn thiếu nên chưa đánh giá đủ tính đúng của báo cáo ngày 20.

Retro [`docs/reviews/2026-11-17-collab-loop-retro.md`](2026-11-17-collab-loop-retro.md) bổ sung nguyên nhân cần đo: 52 lần tự đồng bộ, 72 kết quả author check và 3 lượt review lại khi phần tác giả không đổi. Đây là số riêng của retro, không thay cho M5, M6 hoặc M9 cuối ngày. Retro chụp 30 PR và 68 lượt Codex; bản cuối trong dữ liệu là 31 PR và 69 lượt.

## Quyết định về bộ xếp lịch theo đồ thị

**Khuyến nghị: làm sau khi làn quy trình trở về giới hạn WIP và có số đo hàng chờ đủ dùng.** Bản so sánh này hoàn thành bước nhìn lại đã dùng để hoãn thay đổi scheduler. Nó chưa đủ để bật cả graph v1.

Code đã đọc chỉ xác nhận cơ chế cục bộ. `fileBlocker` trong [`scripts/collab-turn.mjs`](../../scripts/collab-turn.mjs) xét file chung và thứ tự PR, có ngoại lệ L53. PR xếp chồng được nhận diện qua nhánh đích. Chưa thấy khai báo `Depends on #N`, kiểm chu trình hoặc xếp thứ tự tô pô trong đường điều phối đã đọc.

Có lý do để thử bước nhỏ. L49 cho thấy chờ PR từng bị báo nhầm thành chờ owner. L50 và L51 cho thấy PR cần CI dài bị mất lượt khi integration liên tục đổi. L53 cho thấy luật cùng file từng giữ cả PR đã sẵn sàng. Nhưng đây là các lỗi khác nhau. Thử merge không tự giải quyết hết việc thiếu công bằng trong hàng chờ hoặc phụ thuộc về hành vi.

Bước đầu nhỏ nhất là thực hiện S29 đã có trong [retro 17.11](2026-11-17-collab-loop-retro.md): chạy thử `git merge-tree` trên các PR đang bị giữ vì cùng file, rồi ghi kết quả cạnh quyết định hiện tại. Ban đầu chỉ quan sát, chưa thay quyền merge. Ghi rõ base SHA, head SHA, lý do giữ và kết quả thử. Thiếu Git object hoặc lỗi chạy phải là “không kiểm được”, không coi là merge sạch.

Điều kiện vào là làn quy trình không còn vượt **1 đang làm + 1 chờ review**, và có chỗ cho việc thử này. Bối cảnh giao việc nêu khoảng 20 đang làm và 11 chờ review; số hiện tại **không kiểm được** từ checkout. Retro 17.11 đã ghi 2 và 6, cũng vượt trần. Cần xử lý hàng đang mở trước khi mở thêm PR scheduler.

Đề nghị chốt phép đo sau trước khi bật thay đổi:

- Đo một tuần trước và một tuần sau khi thay luật. Đây là lịch đo đề xuất, chưa phải kết quả.
- Số PR bị giữ chỉ vì cùng file dù thử merge sạch phải giảm. Nguồn là log `fileBlocker` và kết quả `merge-tree`.
- Trung vị thời gian từ đủ Author check và APPROVE tới merge phải giảm. Nguồn là thời điểm receipt, trạng thái hàng chờ và merge. M6 theo từng PR dùng làm số bổ sung.
- Số sự cố xung đột cần sửa sau merge và số vụ bỏ đói mỗi tuần không được tăng. Ghi cả số PR đủ điều kiện trong tuần để thấy khối lượng việc. Nguồn là log giữ chỗ, tick và issue sự cố gắn PR.
- Replay phải bắt lại được L50, L51 và L53. Giữ cổng đúng head, đúng base, Author check và review. Merge sạch về văn bản không thay cho test tương thích hành vi.

Chỉ sau bước này mới xét khai báo `Depends on #N`, kiểm tham chiếu thiếu hoặc chu trình, rồi xếp thứ tự tô pô. Thứ tự đó phải giữ ưu tiên làn đã được duyệt. Nội dung PR là dữ liệu không tin cậy; khai báo phụ thuộc không được trở thành lệnh thực thi.

Hai preprint arXiv `2607.04697` và `2610.07261` là nguồn được nêu trong đề bài. Toàn văn và kết quả **không kiểm được** trong lượt không mạng này. Không dùng chúng để suy ra mức xung đột hoặc hiệu quả dự kiến cho Lá Lành.

Theo R1, R2, R7 và R13 trong [`docs/operations/luat-dang-hieu-luc.md`](../operations/luat-dang-hieu-luc.md), đo local, viết test và sửa scheduler có thể hoàn tác qua review không cần owner duyệt riêng. Đổi trần WIP, đổi ưu tiên owner đã chốt hoặc kéo dài thử ba làn cần owner quyết. Chi phí, dịch vụ hoặc quyền mới, phát hành và các việc khác thuộc R2 vẫn theo cổng owner. Việc chốt kết quả thử nghiệm này vẫn thuộc owner theo §5.

## Việc tiếp theo

Mọi lỗi thu số đo dưới đây cần bài học riêng trong [`scripts/collab-lessons.json`](../../scripts/collab-lessons.json) và test đỏ khi lỗi quay lại, theo R17. Chưa tạo bài học hay sửa code trong lượt chỉ đọc này.

1. **Sửa M2 đọc thiếu hoặc đọc sai comment. Mức M.** Sai số 23 có thể đảo kết luận thử nghiệm. Tái hiện bằng dữ liệu tổng hợp có APPROVE và PASS cuối cùng, REQUEST_CHANGES cũ, phân trang và lỗi đọc nguồn. Test phải đỏ với lỗi hiện tại; nguồn thiếu phải trả “chưa đo được”. Giữ bản gốc và bản hiệu chỉnh có nguồn.

2. **Sửa gói bằng chứng M1 và đường ghi M8. Mức M.** Comment bị bỏ làm mất M1 ngày 20 và che bất đồng; ngày 19 đã có một bất đồng ngoài sổ. Tách bài học cho lỗi thiếu bằng chứng và lỗi không ghi bất đồng. Test gói vượt giới hạn phải báo độ phủ thiếu; replay bất đồng #738 phải tạo đúng một bản ghi, chạy lại không nhân đôi.

3. **Sửa đối chiếu bằng chứng M4. Mức S.** L13 từng bị báo thiếu bằng chứng dù đã có. Test theo thời điểm phải đỏ khi bỏ sót bằng chứng hợp lệ, xanh khi đọc đủ, và không dùng trạng thái sổ hôm nay để dựng lại ngày cũ.

4. **Làm đủ M5, M10 và kiểm độ phủ M9. Mức M.** Chưa thể đo việc đạt AC, gánh nặng owner hoặc lượt trên mỗi việc. Mỗi thiếu sót có bài học và test riêng. Một việc qua nhiều PR chỉ tính một lần khi AC đạt; câu hỏi gửi thành công và khoảng kẹt có lịch sử; lượt tay và tự động cùng vào bộ đếm mà không trùng.

5. **Đưa WIP về R7 trước khi nhận việc scheduler mới. Mức M.** Hàng vượt trần làm tăng chờ và khó đọc kết quả. Ưu tiên hoàn tất việc đang mở; kiểm bằng báo cáo hàng việc. Test nhận việc phải từ chối khi làn đầy, đồng thời giữ ngoại lệ sự cố theo luật.

6. **Thử S29 bằng `merge-tree` sau khi đủ điều kiện vào. Mức M.** Cần biết luật cùng file đang giữ nhầm bao nhiêu PR trước khi làm cả đồ thị. Chứng minh bằng phép đo đã nêu, test merge sạch và xung đột thật, cùng replay L50, L51, L53. Chỉ đề xuất bước phụ thuộc và tô pô sau khi có kết quả.

Claude cần phản biện bản này theo §5 và luật bất đồng hiện hành. Sau đó trình owner chốt, không coi bản Codex là quyết định cuối.

## Giới hạn

- Checkout được kiểm tại commit `a4b8a658`; số đo là bản Claude chép từ bản ghi soát đêm cuối ngày ngày 21.11, Codex đọc ở dạng file không đưa lên repo. Không kiểm được chuỗi sao chép từ hồ sơ soát đêm gốc.
- Không dùng mạng nên không chạy inbox GitHub, đọc lại từng PR hoặc đăng bàn giao lên Issue/PR. Số M2 hiệu chỉnh dựa trên bản Claude kiểm lại trong dữ liệu, chưa phải một lần kiểm độc lập của Codex.
- Không có đầy đủ log máy vận hành, output Codex gốc, lịch sử hàng chờ hoặc thời gian từng PR để dựng lại trung vị theo cách và tách các mốc giữa ngày.
- Không kiểm được WIP hiện tại, giờ dựng công cụ riêng hoặc bằng chứng phát hành production ngày 20.11 từ checkout này.
- Không chạy test vì lượt này chỉ phân tích và viết nội dung; môi trường không có lệnh `node`. Các test đỏ đề nghị ở trên chưa được thực hiện.
- Đã đối chiếu hợp đồng thử nghiệm, luật owner, code thu số đo, L49–L53 và retro 17.11. Bản này sửa cách diễn giải số liệu, chưa sửa lỗi runtime. Không thay đổi sản phẩm, quyền hoặc luồng dữ liệu cá nhân.
- Phần còn thiếu của §5 là phản biện Claude và quyết định owner. Rủi ro cùng quyền trên máy vẫn còn theo §0 và trạng thái `declined-owner` của L17, L24. Thử nghiệm này không chứng minh cách 2 gốc có người gác độc lập đạt yêu cầu.

## Phản biện của Claude (21.11.2026)

Theo §5 và luật bất đồng hiện hành (R4). Một vòng, không còn khác ý.

- **Đồng ý** với cả bảng số, phần chất lượng số đo và khuyến nghị về bộ xếp lịch: chỉ quan sát bằng `merge-tree` (S29) sau khi làn quy trình về lại giới hạn WIP; chưa bật khai báo phụ thuộc hay xếp tô pô.
- **Bằng chứng cho M2 ngày 15.11:** Claude kiểm từng PR trong 23 PR bằng `gh pr view` ngày 21.11. PR nào cũng có comment OWNER cuối cùng `Review verdict: APPROVE @ <head cuối>` và `Author check: PASS @ <head cuối>`. Ví dụ #537, #531, #495, #456.
- **Hai chỗ đã sửa (biên tập, không đổi ý):**
  - Bản nháp trỏ link tới file dữ liệu tạm không có trong repo. Nay ghi nguồn là bản ghi soát đêm trên máy owner.
  - Câu "Claude chưa phản biện" được cập nhật.
- **Câu hỏi còn mở về M3:** nền 11–13.11 bằng 0, dù chính sách "P2 không chặn thì mở fix-forward" đã có từ 30.10. Chưa rõ vì sao: do ít PR, do bộ thu chỉ xét ứng viên từ một mốc nào đó, hay lý do khác. Mục này gộp vào việc tiếp theo 1–4.
- **Việc tiếp theo 1–4** (sửa bộ thu số đo) được theo dõi ở issue #828. Mỗi lỗi thêm bài học vào `scripts/collab-lessons.json` cùng PR sửa, kèm test đỏ (R17). Lượt này không sửa file bài học, để tránh chặn PR khác đang mở trên cùng file.

