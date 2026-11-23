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
| R1 | Mọi PR vào `collab/integration` | Owner không phải bước duyệt bắt buộc. Claude làm; Claude và Codex phản biện; Codex duyệt; máy merge theo cổng (biên nhận đúng head, author check, không có lỗi chặn). Owner kiểm ngẫu nhiên. Claude tuần từ 85%: chỉ làm sự cố, an toàn. Từ 95% (giữ 5% cho việc gấp): Codex sửa thay Claude, chỉ merge PR nhỏ ops/test, PR khác nhãn `cho-claude`. Antigravity được phép phản biện và sửa PR, trước Gemini web (sửa PR chỉ bật khi có hộp cát không mạng; R14). PR Codex sửa cần phản biện thứ hai (Antigravity, Claude, Gemini web). | owner, [hub #2 15.11][h15]; owner 22.11: Codex thay khi Claude gần hết; "ngoài ra tôi vừa bật antigravity trên máy cũng có thể sử dụng để phản biện và làm các PR, ưu tiên anti hơn gemini" | 15.11.2026; 22.11.2026 | Owner duyệt plan 9h; owner duyệt mỗi PR | chạy |
| R2 | Review, nhãn, báo cáo | Chỉ 4 loại việc chờ owner: (1) chi phí, dịch vụ mới hoặc quyền truy cập; (2) phát hành cho người dùng thật (`main`, deploy); (3) chữ privacy/consent/crisis/safety: chặn phát hành, không chặn merge; (4) bật thu dữ liệu cá nhân mới: làm sẵn và để tắt. Bài đầu khóa Học và danh sách lằn ranh đỏ do Codex duyệt. Review không tự gửi PR cho owner; Codex ghi 4 loại vào `owner_actions`: giữ merge → `needs-owner`; chữ nhạy cảm → `owner-release-check` (merge được, chờ phát hành). | owner, [hub #2 15.11][h15] và [16.11 mục 1][h16]; code #590, #591 | 16.11.2026 | `needs-owner` sau 2 vòng REQUEST_CHANGES; PR quá lớn → owner | chạy (#611 xong ở #637) |
| R3 | Mọi phiên Claude | Không hỏi owner trong chat (không hộp câu hỏi, không câu hỏi cuối lượt). Việc cần owner gửi phiên điều phối, ghi vào file việc chờ duyệt trên máy owner (`docs/reviews/viec-cho-chi-duyet.md` ở checkout `la-lanh` cũ, không đưa lên Git) với 5 phần: chuyện gì / vì sao cần chị / các lựa chọn / mình khuyên / chị trả lời, kèm mặc định an toàn. File chỉ còn mục đang mở. | owner trong chat 15.11, nhắc lại 16.11 (ghi trên máy owner) | 15.11.2026 | Hỏi trong chat | chạy khi hook đã cài (L37): chặn hộp câu hỏi, câu hỏi cuối lượt; chưa chặn câu hỏi viết thường |
| R4 | Claude ⇄ Codex | Bất đồng: tối đa 2 vòng; còn khác ý thì hỏi owner một lần (theo R3). Ban ngày 30 phút không trả lời → theo kết luận Codex, ghi "chốt do hết giờ"; ban đêm giữ tới sáng. | owner + Codex 14.11; bài học L25 | 14.11.2026 | "Codex luôn thắng" | chạy (L25, #520) |
| R5 | Báo cáo cho owner | 07:00 bản chính có ảnh (tác vụ `la-lanh-bao-cao-7h`); 14:00 và 22:00 (`la-lanh-owner-report`); kẹt thì báo ngay. Không có bản 08:00, không báo cáo cuối tuần. Tiếng Việt đơn giản, ngắn, không mã. | owner, [hub #2 15.11][h15] và [16.11 mục 4][h16] | 16.11.2026 | Báo cáo 08/14/22; prompt dán sẵn | chạy |
| R6 | Plan buổi sáng | Plan chạy ngay khi đăng; owner nói "Giữ" bất cứ lúc nào. Plan là 3–5 việc theo tiêu chí đạt (US/AC), không đếm PR. | owner, [hub #2 16.11 mục 2][h16]; Autopilot v2 12.11 (3–5 việc) | 16.11.2026 | Cổng 08:50/10:00; "20 PR/ngày" | chạy |
| R7 | Hàng việc | Hai làn song song: kế hoạch 7 tuần và quy trình, mỗi làn WIP 1 đang làm + 1 đang review. Ở hàng Codex và merge dùng chung, làn kế hoạch đi trước; sự cố và việc an toàn chen lên trước. Mỗi ngày ít nhất 2 việc kế hoạch. Làn Daily (nhãn `daily-lane`, WIP 1 + 1); thứ tự hàng chung: sự cố/an toàn → kế hoạch 7 tuần → Daily → quy trình. | owner, [hub #2 16.11 mục 5][h16]; kế hoạch 7 tuần 15.11; owner 17.11 (thêm làn Daily) | 16.11.2026; Daily từ 18.11 | Thứ tự ops → content → privacy → tính năng (23.10/30.10); thử 3 làn 18–19.11 | chạy: WIP theo làn (#604); tick làm theo thứ tự làn, làn bị bỏ 2 tick liền lên đầu (#843) |
| R8 | Mọi lượt Codex | Trần 80 lượt/ngày, chạy tay và tự động tính chung, giữ lượt cho soát đêm. Lượt chạy tay ghi `codexRuns` + `ownerExtraCodex.log` trong `state/<ngày>.json`. Owner cho thêm lượt trong ngày thì ghi `ownerExtraCodex.granted` kèm `base: 80` (trần ngày = `dayCap`). Vượt trần chỉ với `--over-cap "<lời owner>"`. Codex review chỉ read-only; sửa thay Claude (R1) ghi được file, không mạng, tối đa 20 lần/ngày trong trần. | owner, [hub #2 16.11 mục 3][h16]; owner 22.11; code #585, #587, #589, #601 | 16.11.2026; 22.11.2026 | Trần 12/32/40/60 | chạy |
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
  "ownerKinds": ["cost_access", "release", "sensitive_copy", "data_collection"],
  "claudeSavingAt": 85,
  "claudeFallbackAt": 95,
  "codexFallbackCap": 20
}
```
