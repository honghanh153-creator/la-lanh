# Thử nghiệm workflow 3 + 3 ngày (14–19.11.2026)

Owner 13.11.2026 (sau khi xem phương án nhẹ và phản biện của Codex, `docs/reviews/2026-11-13-lighter-control-options.md`): "3 ngày đi từ hướng Claude đề xuất, 3 ngày đi theo hướng Codex đề xuất, Claude vẫn thực thi. Sau đó đo lường lại kết quả và nhìn nhận tối ưu hơn về workflow."

Tài liệu này chốt **trước khi chạy**: lịch, luật của từng cách, số đo và cách so sánh. Nó được sửa qua PR có Codex review. Không được đổi số đo sau khi đã thấy kết quả. Nếu buộc phải đổi, ghi rõ lý do và giữ cả số theo định nghĩa cũ.

## 0. Đổi đăng ký ngày 14.11 (trước khi cách 2 bắt đầu)

Owner quyết trong chat tối 14.11. Codex phản biện cùng tối: cả ba điểm **SỬA**. Claude nhận đủ, không có bất đồng. Bản phản biện nằm ở ghi chú phiên làm việc. Các mục dưới đây thay phần tương ứng ở §2, §3 và §5. Số đo M1–M10 không đổi.

- **Không có người gác độc lập.** Owner nói "không muốn cài gì cũng không tạo ứng dụng" và giao Claude với Codex tự thống nhất.
  - 17–19.11 chạy **"cách 2-nhẹ, không có người gác độc lập"**, coi là thử nghiệm thăm dò. Gồm:
    - xếp rủi ro theo file;
    - luật bất đồng mới (dưới đây);
    - soát đêm;
    - kiểm toán sau merge: merge vào integration mà thiếu verdict tự động đúng head thì báo ops-alert và ghi M2 đúng một lần (L26). Kiểm toán này (`scripts/collab-merge-audit.mjs`) chỉ đối chiếu sự nhất quán giữa verdict, file output Codex và chính sách, không chứng minh Codex đã review độc lập: cùng quyền trên máy, Claude vẫn sửa được output, comment hoặc chính chương trình.
  - Báo cáo 20.11 **không** được coi đây là phép so sánh với cách 2 gốc ở §3. Rủi ro còn nguyên: Claude vẫn đọc được khóa, tự đăng verdict và merge được. Kiểm toán sau merge chỉ phát hiện, không chặn trước.
  - L17 và L24 ghi trạng thái `declined-owner`, kèm lý do và rủi ro còn lại. Hai mục này không tính là đã sửa xong.
- **Luật bất đồng mới, thay câu "còn khác ý thì làm theo Codex" ở §2 và câu "Codex chốt" ở §3 (L25):**
  - tối đa hai vòng;
  - còn khác ý thì giữ bước đang tranh chấp và hỏi owner **một lần** cho mỗi quyết định;
  - ban ngày, owner không trả lời sau 30 phút kể từ lúc gửi thành công thì làm theo kết luận cụ thể của Codex và ghi "chốt do hết giờ";
  - ban đêm thì giữ tới sáng, gửi lại rồi mới tính 30 phút;
  - không hỏi lại cùng một tranh chấp khi chưa có gì thay đổi thực chất;
  - hết giờ không trao quyền của owner và không bỏ qua cổng chặn nào. Việc chỉ owner quyết (ví dụ L05) vẫn chờ owner.
- **Người lập plan ngày (L18):**
  - Claude lập 16–22.11, Codex lập 23–29.11;
  - Q1–Q5, ưu tiên nợ quá hạn và luật vòng review thứ 3 trở đi giống nhau ở cả hai tuần; chỉ đổi người lập;
  - lịch này không đổi người lập trong 14–19.11, nên không thêm nhiễu cho thử nghiệm 3+3.
- **Kiểm chính Codex mỗi tuần (L20):**
  - Codex review một bản chụp có cài lại lỗi #451/#462, đặt trong môi trường riêng, không có đường merge vào integration;
  - mô tả kỹ thuật trung thực; đáp án nằm ngoài ngữ cảnh của reviewer;
  - lỗi lọt ghi riêng cho L20, **không** cộng vào M3.
- **Giờ chạy và trần Codex** (owner 14.11, PR #514): bắt đầu PR lúc 08:00 thay 10:00, kết thúc 23:59; trần 60 lượt/ngày, tính chung plan, review, soát đêm và tranh luận. Thay đổi giữa cách 1 nên thêm vào danh sách yếu tố gây nhiễu ở §5 cho M5 và M6.

## 0b. Thay đổi giữa thử nghiệm ngày 15.11 (owner quyết, cách 1 đang chạy)

- **Lúc nào:** 15.11.2026, khoảng 17:00–18:00, trong ngày thứ hai của cách 1 (Claude làm, 14–16.11). Ghi ở hub #2.
- **Đổi gì:** owner không còn là bước duyệt bắt buộc. Claude làm, Claude và Codex phản biện nhau, Codex duyệt, máy merge qua cổng cũ (author check PASS và APPROVE có biên nhận, cả hai đúng head). `needs-owner` chỉ còn cho 4 loại việc: chi phí hoặc dịch vụ mới, phát hành, chữ privacy/consent/crisis/safety, bật tính năng thu dữ liệu mới. Owner kiểm QA ngẫu nhiên. Chi tiết ở `collab-auto-loop-plan.md` §2.
- **Gây nhiễu:** thay đổi này rơi vào giữa cách 1 và trước cách 2 (17–19.11). Nó tác động trực tiếp tới:
  - M5: số việc đạt trong ngày có thể tăng vì bớt chờ owner;
  - M6: thời gian tới lúc merge;
  - M10: câu hỏi gửi owner và số lần bị kẹt;
  - có thể cả M7.
  Báo cáo 20.11 ghi nó vào danh sách yếu tố gây nhiễu ở §5 và tách số đo trước và sau 15.11 18:00 khi so sánh.
- **Số đo giữ định nghĩa cũ:** M1–M10 không đổi định nghĩa, nguồn hay hướng tốt. Riêng M10 vẫn đếm mọi câu hỏi gửi owner, kể cả câu thuộc 4 loại còn lại.

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
  - giờ chạy đổi sang 08:00–23:59 và trần Codex lên 60 lượt từ 15.11 (§0), giữa cách 1;
  - cách 2 chạy bản nhẹ, không có người gác độc lập (§0).
- Ba ngày mỗi cách là mẫu nhỏ, nên kết quả để chọn hướng tiếp, không phải bằng chứng thống kê.

## 6. Việc phải có và hạn

Theo dõi trong `scripts/collab-lessons.json` (L21–L24):
- L21: soát đêm do Codex ghi số đo M1–M10, chạy lần đầu tối 14.11 (cần cho cả hai cách);
- L22: sổ bất đồng bản Claude, trước 14.11 08:00;
- L23: đo nền 11–13.11, trước 16.11;
- L24: chương trình giữ biên nhận, merge và trạng thái "xong" cho cách 2, trước 17.11 00:00.
