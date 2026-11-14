# Thử nghiệm workflow 3 + 3 ngày (14–19.11.2026)

Owner 13.11.2026 (sau khi xem phương án nhẹ và phản biện của Codex, `docs/reviews/2026-11-13-lighter-control-options.md`): "3 ngày đi từ hướng Claude đề xuất, 3 ngày đi theo hướng Codex đề xuất, Claude vẫn thực thi. Sau đó đo lường lại kết quả và nhìn nhận tối ưu hơn về workflow."

Tài liệu này chốt **trước khi chạy**: lịch, luật của từng cách, số đo và cách so sánh. Nó được sửa qua PR có Codex review. Không được đổi số đo sau khi đã thấy kết quả. Nếu buộc phải đổi, ghi rõ lý do và giữ cả số theo định nghĩa cũ.

## 1. Lịch

| Giai đoạn | Ngày (giờ VN) | Cách chạy |
|---|---|---|
| Đo nền | 11–13.11 (đã qua) | Cách cũ, đo lại từ log và GitHub để có mốc so sánh |
| Cách 1: hướng Claude | 14.11 (T7) – 16.11 (T2) | Mục 2 |
| Cách 2: hướng Codex | 17.11 (T3) – 19.11 (T5) | Mục 3 |
| Nhìn lại | 20.11 (T6) | Mục 5 |

Một ngày tính từ 00:00 tới 23:59. Claude thực thi ở cả hai cách. Codex review PR như hiện nay ở cả hai cách.

## 2. Cách 1: hướng Claude (14–16.11)

- **Mức rủi ro do người làm khai:** mức S/M/L ghi trong PR. S và M làm như hiện nay. L, việc đụng quy trình vòng tự động, quyền riêng tư và bảo mật thì Claude gửi kế hoạch cho Codex phản biện **trước khi** làm.
- **Luật bất đồng, bản Claude:** Claude đề xuất kèm bằng chứng; Codex đồng ý, sửa hoặc bác; Claude được cãi lại **một lần** với bằng chứng mới; Codex trả lời lần cuối; còn khác ý thì làm theo Codex. **Claude tự ghi** mỗi bất đồng (một dòng: thời điểm, PR/việc, ý Claude, ý Codex, bên thắng) vào `~/.cache/la-lanh-collab/disagreements.jsonl` trên máy owner; soát đêm đọc file này và đối chiếu với comment trên GitHub. Việc chỉ owner quyết vẫn về owner.
- **Soát đêm:** mỗi đêm Codex đối chiếu từ nguồn gốc (GitHub, CI, log, sổ lời hứa) rồi ghi số đo ở mục 4.
- **Đường merge giữ như hiện nay.** Rủi ro được chấp nhận trong cách này: Claude về kỹ thuật vẫn giả được comment duyệt. Soát đêm chỉ phát hiện sau, không chặn trước.

## 3. Cách 2: hướng Codex (17–19.11)

- **Mức rủi ro do máy xếp theo file thay đổi**, không theo mức PR tự khai. Ví dụ một dòng sửa quyền merge vẫn là việc phải xét trước.
- **Luật bất đồng, bản Codex:**
  - tối đa hai vòng;
  - bên nào cũng được mở bất đồng;
  - **máy lưu nguyên văn** câu trả lời của cả hai bên;
  - "sửa", "bác", điều kiện chưa đáp ứng, hay im lặng đều tính là **chưa thống nhất**;
  - được chỉ ra lỗi suy luận dựa trên bằng chứng cũ;
  - còn khác ý thì Codex chốt có lý do;
  - trong lúc chưa chốt thì giữ bước đang tranh chấp và làm việc khác.
- **Một chương trình riêng giữ ba thứ:**
  - biên nhận review thật, gắn đúng commit và nhánh đích (nối từ #456);
  - merge chỉ đi qua cổng;
  - trạng thái "xong" của lời hứa: cần đạt tiêu chí, có test bắt lỗi cũ và có bằng chứng chạy thật đúng bản.
- **Soát đêm** như cách 1.
- **Điều kiện bắt đầu:** #456 đã merge và chương trình giữ biên nhận đã chạy. Nếu tới 17.11 chưa sẵn sàng, cách 2 lùi lại và ghi rõ trong báo cáo, **không** chạy cách 2 thiếu phần này rồi vẫn gọi là "hướng Codex". Owner có thể phải bật luật GitHub chặn merge ngoài cổng; Claude chuẩn bị sẵn và hỏi owner.

## 4. Số đo (giống nhau ở mọi giai đoạn)

Lấy từ nguồn gốc, không từ lời tự kể của agent. Nguồn nào không đọc được thì ghi "chưa đo được", không ước lượng.

| # | Số đo | Nguồn | Hướng tốt |
|---|---|---|---|
| M1 | Câu trong báo cáo cho owner sai với nguồn | Soát đêm của Codex | thấp |
| M2 | Merge không có biên nhận review thật đúng head | GitHub + soát đêm | 0 |
| M3 | Lỗi lọt sau khi Codex duyệt (fix-forward, revert, ops-alert do thay đổi đã merge) | GitHub issue/PR, log | thấp |
| M4 | Lời hứa đóng có bằng chứng / quá hạn | `scripts/collab-lessons.json` + GitHub | đóng cao, quá hạn thấp |
| M5 | Việc đạt tiêu chí trong ngày (nhiều PR một việc tính một) | plan ngày + GitHub | cao |
| M6 | Thời gian từ mở PR tới merge (trung vị) | `collab-metrics` | thấp |
| M7 | Số vòng review mỗi PR | comment verdict | thấp |
| M8 | Bất đồng: số lần, bên thắng, lần owner lật lại | sổ bất đồng | ghi nhận |
| M9 | Lượt Codex mỗi ngày | state ngày | ≤ 32 |
| M10 | Câu hỏi gửi owner, và lần vòng tự động bị kẹt quá 1 giờ | báo cáo, watchdog | thấp |

Cách đo:
- Soát đêm (`scripts/collab-audit-night.mjs`, tick gọi `runNightAudit`): dữ kiện M2–M10 lấy từ nguồn; Codex chấm M1, M3 và bất đồng chưa ghi sổ. Bản tạm tính lúc 23:00, bản chốt sau nửa đêm, mỗi bản 1 lượt Codex.
- Nền so sánh 11–13.11 (L23): `node scripts/collab-audit-night.mjs --baseline 2026-11-11..2026-11-13` chạy cùng bộ thu thập. Kết quả là một bảng M1–M10 theo ngày, đăng một lần trên issue kế hoạch.

## 5. Cách so sánh ngày 20.11

- Thứ tự ưu tiên: **trung thực** (M1, M2), rồi **chất lượng** (M3, M4), rồi **tốc độ** (M5–M7), rồi **chi phí** (M9, M10).
- Codex viết bản so sánh từ số đo; Claude phản biện theo luật bất đồng của cách 2; owner quyết.
- **Yếu tố gây nhiễu**, ghi ra chứ không giấu:
  - khối lượng việc mỗi ngày khác nhau;
  - 14–15.11 là cuối tuần;
  - cách 2 chạy sau nên được hưởng phần học từ cách 1;
  - công dựng chương trình của cách 2 làm trong lúc chạy cách 1 (giờ dựng được ghi riêng).
- Ba ngày mỗi cách là mẫu nhỏ, nên kết quả để chọn hướng tiếp, không phải bằng chứng thống kê.

## 6. Việc phải có và hạn

Theo dõi trong `scripts/collab-lessons.json` (L21–L24):
- L21: soát đêm do Codex ghi số đo M1–M10, chạy lần đầu tối 14.11 (cần cho cả hai cách);
- L22: sổ bất đồng bản Claude, trước 14.11 08:00;
- L23: đo nền 11–13.11, trước 16.11;
- L24: chương trình giữ biên nhận, merge và trạng thái "xong" cho cách 2, trước 17.11 00:00.
