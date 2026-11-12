# Claude tự phản biện vòng 1 (độc lập với Codex)

## 1. Lệch so với cách Lauren làm

| Lauren | Thiết kế hiện tại | Đánh giá |
|---|---|---|
| Skill kiểm chứng là **thứ đầu tiên** | P2, sau policy | **Lệch không có lý do.** Nên chạy song song với P1, vì mọi quyền tự merge UI đều dựa vào nó |
| Hàng rào cứng làm rất mạnh: 600+ PR refactor trước khi thôi đọc code | T0.3 chỉ vài luật | **Thiếu tầm cỡ.** Repo đang có file 1.300–2.000 dòng (`clarity_lint.py` 2.056, `context_readings.py` 1.957, `radar/reading.py` 1.767, web `client.ts` 1.544). Đúng là "greenfield" đang mọc kiến trúc tự phát. Cần một chương trình refactor có đo: kích thước file, ranh giới import, trần độ phức tạp |
| Song song cao: 10+ điều phối, 1–10 verifier mỗi PR | WIP 1+1 cho toàn hệ | **Một phần đúng** (cap Codex, một Mac). Nhưng thắt cổ chai thật là lượt review của Codex chứ không phải sức Claude. Nên **review theo tầng**: loại ít rủi ro chỉ qua cổng máy + verifier; Codex dành cho loại rủi ro. WIP tính theo **lượt Codex**, không theo số việc |
| Eval skill sớm, chạy lại khi skill hay model đổi | P7 | **Lệch.** Vòng hiện chạy bằng SKILL.md (autopilot, morning-prep), mà các skill này vẫn còn ghi "20 PR". Skill hỏng thì cả vòng hỏng, nên eval cho skill của chính vòng phải đưa lên P3 |
| Đọc lại transcript để sinh skill | P7 | Có thể làm sớm, chi phí thấp: lấy phiên hôm nay (owner sửa mình nhiều lần) làm nguồn |
| Không giao mục tiêu kinh doanh cho agent | Có tầng mục tiêu | **Lệch có lý do** (owner muốn), nhưng phải hãm như Lauren: mục tiêu chỉ chạy khi đã có thước đo kiểm được, và có cảnh báo chỉ số thay thế. Đã có |
| Xem lại main mỗi sáng | Tóm tắt sáng + phiên mỗi 2–3 ngày | **Lệch đúng** (sức chứa của owner), bù bằng kiểm mẫu và ma trận lòng tin |

## 2. Mong muốn của owner: đạt / một phần / chưa

| Mong muốn | Trạng thái | Khoảng hở |
|---|---|---|
| Chạy khi ngủ | Một phần (P4) | Chưa có **mốc thời gian**; phụ thuộc Mac thức và sandbox |
| Auto hết mà giữ chất lượng | Một phần (P8) | Xa; chưa có **cách chứng minh cổng bắt được lỗi** (xem mục 4) |
| Chỉ nói mục tiêu | Một phần (P5) | Chỉ "UX tốt hơn" đo được ngay |
| Chỉ số → hành động | Đạt về thiết kế | Chưa chạy |
| Phản biện plan của owner | Đạt về thiết kế (P3) | — |
| Báo cáo | Một phần | #451 chưa merge; owner chưa bật thông báo |
| Không bị quá tải | Một phần | Sức chứa chưa đo; thiếu **công tắc dừng từ điện thoại** |
| Ý tưởng vào app | Một phần | 4 PR đang chờ |

## 3. Tốt hơn nữa: 7 việc, xếp theo tác động

1. **Kiểm chính cổng bằng lỗi cài sẵn.** Mỗi tuần máy tự mở vài PR có lỗi cài sẵn: lộ dữ liệu sinh vào log, câu dự đoán sự kiện, vỡ layout 360px, AC sai, sửa policy. Đo **tỷ lệ cổng bắt được**. Đây là bằng chứng duy nhất để nói "chất lượng được đảm bảo", và là điều kiện để nâng lòng tin. *Nghiệm thu*: ≥ 95% lỗi cài bị bắt trước merge; lỗi lọt thì sinh luật mới.
2. **Đưa skill kiểm chứng + bản đồ tính năng lên ngay P1**, chạy song song với policy. *Nghiệm thu*: mọi PR UI có bằng chứng chạy thật.
3. **Chương trình hàng rào cứng có đo**: trần kích thước file và độ phức tạp, ranh giới import, kiểu bất biến. Mỗi tuần tách 1–2 file lớn nhất. *Nghiệm thu*: không file mới > 600 dòng; số file > 1.000 dòng giảm dần.
4. **Review theo tầng, WIP theo lượt Codex**: loại ít rủi ro chỉ cần cổng máy + verifier + mẫu; Codex dồn cho loại rủi ro. *Nghiệm thu*: thông lượng tăng mà lỗi lọt không tăng.
5. **Eval cho skill của chính vòng** (autopilot, morning-prep, viết nội dung) ở P3, thư mục tên trung tính, giám khảo khác model; đồng thời sửa ngay chỗ SKILL còn ghi "20 PR". *Nghiệm thu*: skill có bộ eval, chạy lại khi đổi.
6. **Chạy lại dữ liệu lịch sử cho `decide()`**: cho nó quyết định lại 14 ngày đã qua, so với việc người thật đã làm và các sự cố đã xảy ra. Có chứng cứ trước khi chạy bóng. *Nghiệm thu*: giải thích được mọi khác biệt.
7. **Công tắc dừng và mốc thời gian**: owner bình luận `/dừng` hoặc `/tiếp` trên issue plan; mỗi giai đoạn có ngày dự kiến và báo trễ. *Nghiệm thu*: `/dừng` làm đóng băng trong ≤ 1 tick.

## 4. Có đảm bảo chất lượng khi chạy auto không? Trả lời thật

- **Bảo đảm tuyệt đối thì không.** Không hệ thống nào làm được, kể cả Lauren: chị vẫn đọc lại mỗi sáng và quay lui.
- **Bảo đảm được (bằng code, có test):**
  - không merge khi thiếu bằng chứng ở đúng SHA;
  - cửa một chiều không bao giờ tự đi (manifest có chữ ký);
  - mọi thay đổi tự động đều quay lui được;
  - phát hiện hồi quy trong ≤ 1 đêm (UAT);
  - không vượt ngân sách.
- **Chỉ giới hạn được (bằng thống kê):** tỷ lệ lỗi lọt cho mỗi loại thay đổi. Lòng tin chỉ mở cho loại có lỗi lọt thấp với khoảng tin cậy, và có bằng chứng cổng bắt được lỗi cài sẵn.
- **Không đo được bằng máy:** "hay", "đúng gu". Phải có so cặp của owner, tester, và nhãn chỉ số thay thế.
- **Tối thiểu trước khi merge tự động ban đêm:**
  - verify + UAT xanh;
  - khoá diff + manifest có chữ ký;
  - chạy bóng 100% bất biến an toàn;
  - kiểm cổng bằng lỗi cài sẵn ≥ 95%;
  - quay lui một lệnh;
  - công tắc dừng.
- **Tối thiểu trước khi phát hành tự động:** thêm
  - diễn tập quay lui có dữ liệu;
  - canary đủ power;
  - lệnh thường trực có chữ ký;
  - lịch sử lỗi lọt đủ mẫu.
