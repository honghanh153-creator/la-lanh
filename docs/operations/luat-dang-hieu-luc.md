# Luật owner đang hiệu lực

Đây là **nguồn chuẩn duy nhất** cho các luật làm việc owner đã chốt (owner 16.11.2026: "hãy cùng codex cải thiện tình hình trí nhớ"). Mọi agent đọc file này trước mỗi task và trước khi cần hỏi owner.

- Tài liệu khác, prompt tác vụ hẹn giờ, trí nhớ riêng của agent: chỉ **trỏ tới Id** ở đây, không chép lại nội dung luật. Chỗ nào khác ý file này thì file này đúng, chỗ kia là bản cũ phải sửa.
- Bản chạy là file trên `collab/integration` (máy đọc từ clone ops, `~/.cache/la-lanh-collab/ops`). Đổi luật bằng PR nhỏ qua vòng review thường. Giữ Id, đổi ngày, chuyển câu cũ sang cột "Thay thế".
- Repo công khai: không ghi dữ liệu cá nhân của owner, số tiền ngân sách hay đường dẫn riêng ở đây.
- Loại nguồn: **owner** = lời owner (trích hoặc ghi lại trên hub #2); **code** = đã chạy, có PR đã merge; **agent** = agent tự kể, chưa có kiểm chứng.
- Trạng thái: **chạy** = code/tác vụ đã làm theo; **đã quyết** = owner đã chốt, code chưa theo kịp (ghi PR đang làm).

Kiểm bằng máy: `node scripts/collab-rules.mjs` (khối `rules-facts` cuối file phải khớp hằng số trong code; test trong `pnpm collab:test`).

| Id | Phạm vi | Luật | Nguồn | Hiệu lực | Thay thế | Trạng thái |
|---|---|---|---|---|---|---|
| R1 | Mọi PR vào `collab/integration` | Owner không phải bước duyệt bắt buộc. Mỗi việc có tổ hợp 3 vai: Claude viết, Anti phản biện, Codex quyết; Codex viết, Claude phản biện, Anti quyết; Anti viết, Codex phản biện, Claude quyết. Người quyết không là người viết hay người phản biện; thiếu vai thì chờ. Máy merge theo cổng (biên nhận đúng head, author check, không có lỗi chặn). Lời duyệt giữ qua đồng bộ chỉ khi phần sửa y nguyên và file nó gọi tới, phần dùng chung không đổi ("giữ từ lần trước"). Owner kiểm ngẫu nhiên. | owner, [hub #2 15.11][h15]; owner 28.11 (#977) | 28.11.2026 | Codex duyệt mọi PR; lời duyệt gắn một head; owner duyệt plan 9h, mỗi PR | đã quyết (#977): PR Claude viết vẫn do Codex quyết |
| R2 | Review, nhãn, báo cáo | Chỉ 4 loại việc chờ owner: (1) chi phí, dịch vụ mới hoặc quyền truy cập; (2) phát hành cho người dùng thật (`main`, deploy); (3) chữ privacy/consent/crisis/safety: chặn phát hành, không chặn merge; (4) bật thu dữ liệu cá nhân mới: làm sẵn và để tắt. Bài đầu khóa Học và danh sách lằn ranh đỏ do Codex duyệt. Review không tự gửi PR cho owner; Codex ghi 4 loại vào `owner_actions`: giữ merge → `needs-owner`; chữ nhạy cảm → `owner-release-check` (merge được, chờ phát hành). | owner, [hub #2 15.11][h15] và [16.11 mục 1][h16]; code #590, #591 | 16.11.2026 | `needs-owner` sau 2 vòng REQUEST_CHANGES; PR quá lớn → owner | chạy (#611 xong ở #637) |
| R3 | Mọi phiên Claude | Không hỏi owner trong chat (không hộp câu hỏi, không câu hỏi cuối lượt). Việc cần owner gửi phiên điều phối, ghi vào file việc chờ duyệt trên máy owner (`docs/reviews/viec-cho-chi-duyet.md` ở checkout `la-lanh` cũ, không đưa lên Git) với 5 phần: chuyện gì / vì sao cần chị / các lựa chọn / mình khuyên / chị trả lời, kèm mặc định an toàn. File chỉ còn mục đang mở. | owner trong chat 15.11, nhắc lại 16.11 (ghi trên máy owner) | 15.11.2026 | Hỏi trong chat | chạy khi hook đã cài (L37): chặn hộp câu hỏi, câu hỏi cuối lượt; chưa chặn câu hỏi viết thường |
| R4 | Bất đồng | Sau 2 vòng, người quyết của tổ hợp làm trọng tài. Lỗi chặn thật: một vòng 3 (sửa đúng lỗi đó, người phản biện chỉ kiểm chỗ sửa, người quyết quyết); vẫn chưa được thì tạm dừng, không hạ lỗi chặn. Chỉ hỏi owner (R3) cho 4 loại việc ở R2. | owner + Codex 14.11; L25; owner 28.11 (#977) | 28.11.2026 | 2 vòng rồi hỏi owner; 30 phút → theo Codex; "Codex luôn thắng" | đã quyết (#977): L25, #520 chạy tới khi có thẻ tổ hợp |
| R5 | Báo cáo cho owner | 07:00 bản chính có ảnh (tác vụ `la-lanh-bao-cao-7h`); 14:00 và 22:00 (`la-lanh-owner-report`); kẹt thì báo ngay. Không có bản 08:00, không báo cáo cuối tuần. Tiếng Việt đơn giản, ngắn, không mã. | owner, [hub #2 15.11][h15] và [16.11 mục 4][h16] | 16.11.2026 | Báo cáo 08/14/22; prompt dán sẵn | chạy |
| R6 | Plan buổi sáng | Plan chạy ngay khi đăng; owner nói "Giữ" bất cứ lúc nào. Plan là 3–5 việc theo tiêu chí đạt (US/AC), không đếm PR. | owner, [hub #2 16.11 mục 2][h16]; Autopilot v2 12.11 (3–5 việc) | 16.11.2026 | Cổng 08:50/10:00; "20 PR/ngày" | chạy |
| R7 | Hàng việc | Một hàng việc chung; làn chỉ là thứ tự ưu tiên: sự cố/an toàn → kế hoạch 7 tuần → Daily (`daily-lane`) → quy trình. WIP theo tổ hợp: 1 đang làm + 1 đang review. Mỗi ngày ít nhất 2 việc kế hoạch. Từ 15 PR mở trở lên: plan chỉ có việc dở, sự cố, an toàn. | owner, [hub #2 16.11 mục 5][h16]; owner 17.11 (Daily); owner 28.11 (#977) | 28.11.2026 | Hai làn, mỗi làn WIP 1 + 1 (16.11); ops → content → privacy → tính năng (23.10/30.10) | đã quyết (#977): WIP theo làn (#604, #843) chạy tới khi có thẻ tổ hợp; dọn PR: #978 |
| R8 | Mọi lượt Codex | Trần 80 lượt/ngày, chạy tay và tự động tính chung, giữ lượt cho soát đêm. Lượt chạy tay ghi `codexRuns` + `ownerExtraCodex.log` trong `~/.cache/la-lanh-collab/state/<ngày>.json`. Owner cho thêm lượt trong ngày thì ghi `ownerExtraCodex.granted` kèm `base: 80` (trần ngày = `dayCap`). Vượt trần chỉ với `--over-cap "<lời owner>"`. Codex chỉ đọc khi phản biện hoặc quyết; khi viết, chỉ ghi trong worktree riêng của việc. Anti chỉ trả bản vá chữ, máy áp. | owner, [hub #2 16.11 mục 3][h16]; code #585, #587, #589, #601; owner 28.11 (#977) | 28.11.2026 | Trần 12/32/40/60; Codex luôn read-only | chạy; Codex viết, Anti vá: đã quyết (#977) |
| R9 | Mọi phiên | Làm tới 23:59. Không dời việc sang "mai" khi còn giờ và còn lượt Codex. Vòng tự động không bắt đầu việc mới từ 23:35, dừng 23:59. | owner trong chat 16.11 (ghi trên máy owner); code `lastStartAt`/`cutoffAt` | 16.11.2026 | Dừng 23:00 / 23:30 | chạy |
| R10 | Máy owner | Mỗi PR chỉ một phiên sửa (`collab-pr-claim.mjs --claim N` trước khi sửa). Tối đa 2 việc nặng cùng lúc, mỗi việc có cổng, khóa và cổng mạng riêng (`collab-test-guard.mjs`). Author check đọc CI. | owner, [hub #2 16.11 mục 3][h16]; code #597, #598, #599 | 16.11.2026 | Mỗi lúc một việc nặng | chạy (#603) |
| R11 | Ngày có đổi app | Cuối ngày 200 người giả bốc ngẫu nhiên trong 1000 chạy thử (đầu ngày so với cuối ngày), kết quả vào báo cáo 07:00. Đây là mô phỏng, không phải người dùng thật. | owner, [hub #2 15.11][h15] | 15.11.2026 | — | chạy (`personas-nightly.md`) |
| R12 | Phát hành | Hotfix nhỏ được phát hành khi đủ 6 điều kiện có bằng chứng, tới hết 29.11 (owner có thể gia hạn hoặc thu hồi). Mọi phát hành khác, merge `main`, deploy cần owner đồng ý mới. Lịch phát hành: mỗi sáng thứ Sáu máy chuẩn bị một bản phát hành từ `collab/integration` kèm bằng chứng (kiểm toàn bộ, ảnh 360/390, người giả, cách quay lại, việc còn chặn phát hành) và đưa một mục vào file việc chờ duyệt (R3); owner trả lời "phát hành" hoặc "giữ" cho từng lần. Bước chuẩn bị không merge, không deploy. | owner 15.11 (file việc chờ duyệt, mục F); owner 18.11 "AC1" (mục AC, ghi trên máy owner) | 15.11–29.11.2026 (hotfix); từ 20.11.2026 (lịch thứ Sáu) | Phát hành khi xong việc tuần 1 (không có lịch) | chạy (tác vụ hẹn giờ `la-lanh-release-candidate`, thứ Sáu 04:30) |
| R13 | Mọi phiên | Việc miễn phí, trên máy, đảo ngược được, không đụng dữ liệu riêng: tự quyết và báo lại. Không bao giờ tự làm: API trả phí, nhà cung cấp, IAM, secret, ngân sách, server/DB thật khi chưa có lệnh rõ. | owner 29.10 (ghi trên máy owner) | 29.10.2026 | — | chạy |
| R14 | GitHub, AI bên ngoài | Repo công khai: không dữ liệu cá nhân của owner (ngày sinh, email…), không số tiền ngân sách. Không gửi file riêng của owner (trí nhớ, transcript) cho Codex hay dịch vụ AI khác; chỉ gửi bản tóm tắt đã lược. | owner 03.11 (sự cố lộ dữ liệu) | 03.11.2026 | — | chạy (`private-guard` trước push) |
| R15 | Câu chữ cho người dùng | Tiếng Việt đời thường, ngắn, cụ thể; không câu thơ; không giải thích nguyên nhân kỹ thuật (vd múi giờ). | owner 03.11 và 10.11 | 10.11.2026 | Lời văn bay bổng | chạy (Codex chấm) |
| R16 | Mọi việc | Ý tưởng phải thành code chạy được có bằng chứng; không nói "đã có" khi chưa có chỗ gọi và test. Không tự cắt phạm vi; owner quyết phần cắt. | owner 12.11 | 12.11.2026 | — | chạy |
| R17 | Sự cố và góp ý | Mỗi sự cố hoặc góp ý của owner thành một kiểm tra bằng máy: bài học trong `scripts/lessons/` (bài cũ: `scripts/collab-lessons.json`) có test đỏ khi lỗi quay lại. | owner 03.11 và 13.11; code #481 | 13.11.2026 | Ghi chú chỉ trong trí nhớ/retro | chạy |

[h15]: https://github.com/honghanh153-creator/la-lanh/issues/2#issuecomment-6893191704
[h16]: https://github.com/honghanh153-creator/la-lanh/issues/2#issuecomment-6904505088

## Số máy đọc

Các số này phải bằng hằng số trong code (`scripts/collab-trust.mjs`, `scripts/collab-review-policy.mjs`). Đổi luật thì đổi cả hai trong cùng PR.

```json rules-facts
{
  "codexDailyCap": 80,
  "planOpensAt": "06:50",
  "lastStartAt": "23:35",
  "cutoffAt": "23:59",
  "reportSlots": ["07:00", "14:00", "22:00"],
  "retiredReportSlots": ["08:00"],
  "ownerKinds": ["cost_access", "release", "sensitive_copy", "data_collection"]
}
```
