# Việc nhẹ hơn của Daily: nguồn bên ngoài cho quyết định mức L (#636)

Ngày: 17.11.2026. Người viết: Claude. Dùng cho `docs/decisions/2026-11-17-viec-nhe-hon-daily.md` (#627, PR #634, #640).

Phạm vi: chỉ kiểm ba quyết định 1B, 2C, 3B và đường lùi bản với nguồn bên ngoài. Không có dữ liệu người dùng trong truy vấn tìm kiếm.

## Kết luận

- Thêm trường tùy chọn `lighter_action` vào câu trả lời Daily là bước "mở rộng": bản cũ và bản mới cùng chạy được, và bản phát hành nào cũng dừng được ở bước này. Người đọc chỉ lấy phần mình cần thì không hỏng khi bên gửi thêm trường. [S1] [S2] [S5]
- Note đã lưu không theo được cách đó: bản phát hành trước đọc bản chụp bằng hợp đồng chặt, gặp trường lạ thì từ chối. Nguồn nói rõ kiểu đọc theo lược đồ chặt hay hỏng khi bên gửi thêm trường. Vì vậy quyết định 3B (không ghi `lighter_action` vào bản chụp) là đúng; có test đọc lại bản chụp bằng hợp đồng của bản trước. [S2] [S6]
- Việc nhẹ đang giữ là chỗ duy nhất phá quy tắc "bản cũ vẫn đọc được": bản mới chấp nhận thêm khóa `lighter_action` trong dữ liệu đã mã hóa, bản cũ đòi đúng bộ khóa cũ. Theo mẫu mở rộng rồi thu hẹp, bên cũ phải được hỗ trợ cho tới khi không còn ai dùng; ở đây không làm được, nên giới hạn lùi bản phải nằm trong runbook phát hành. Runbook đã có mục này. [S1] [S8] [S10]
- Khóa "giữ việc" do thiết bị gửi lên được máy chủ kiểm lại theo danh sách cho phép (đúng chủ, đúng revision đang hiện, đúng câu của ô đang được duyệt). Cách này khớp yêu cầu kiểm đầu vào ở tầng dịch vụ tin cậy và kiểm theo danh sách giá trị cho phép. Thiết bị chỉ chọn câu nào hiện ra; nó không tự tạo được câu để giữ. [S3] [S8]
- Máy chủ chọn câu việc nhẹ chỉ từ mã revision; hàm chọn không nhận mood. Quyết định 1B vì thế không thêm mục đích dùng mới cho mood ở máy chủ. [S5]
- Nút đổi qua lại cao ít nhất 44 px trong test ở 360 và 390 px, lớn hơn mức tối thiểu 24 × 24 px của tiêu chí 2.5.8 (mức AA). [S4] [S7]
- Luật Bảo vệ dữ liệu cá nhân có hiệu lực từ 01/01/2026, nên thay đổi này phải xét theo luật đó chứ không theo nghị định cũ. [S9]

## Nguồn đã đọc

- S1: https://martinfowler.com/bliki/ParallelChange.html — đọc: ba bước expand, migrate, contract; đoạn nói bản phát hành có thể dừng ở bất kỳ bước nào và bên cung cấp phải hỗ trợ hai phiên bản trong lúc chuyển
- S2: https://martinfowler.com/bliki/TolerantReader.html — đọc: đoạn khuyên bên đọc chỉ lấy dữ liệu mình cần, và đoạn nói đọc theo lược đồ chặt hỏng khi bên gửi thêm trường
- S3: https://raw.githubusercontent.com/OWASP/ASVS/v5.0.0/5.0/en/0x11-V2-Validation-and-Business-Logic.md — đọc: yêu cầu 2.2.1 (kiểm theo danh sách cho phép) và 2.2.2 (kiểm ở tầng dịch vụ tin cậy), đều mức 1
- S4: https://raw.githubusercontent.com/w3c/wcag/main/guidelines/sc/22/target-size-minimum.html — đọc: tiêu chí 2.5.8, mức AA, 24 × 24 CSS pixel, năm ngoại lệ
- S5: apps/api/app/domains/readings/lighter_action.py — đọc: `lighter_action_for(revision_id)` và `LIGHTER_CATALOG`; hàm chỉ nhận mã revision
- S6: apps/api/tests/saved/test_snapshot_rollback.py — đọc: hai test đọc bản chụp bằng hợp đồng của bản phát hành trước
- S7: apps/web/tests/e2e/lighter-action-width.spec.ts — đọc: hàm `expectFits` (không tràn ngang, không bị cắt, nút cao từ 44 px) ở 360 và 390 px
- S8: apps/api/app/domains/experiments/postgres.py — đọc: kiểm chủ sở hữu và revision trước khi nhận khóa giữ việc; dòng kiểm bộ khóa của dữ liệu đã mã hóa cho phép thêm `lighter_action`
- S9: https://xaydungchinhsach.chinhphu.vn/quoc-hoi-da-thong-qua-luat-bao-ve-du-lieu-ca-nhan-119250626153701582.htm — đọc: câu nêu Luật có hiệu lực thi hành từ ngày 01/01/2026
- S10: docs/operations/hetzner-supabase-release-runbook.md — đọc: mục "Rollback limit: kept lighter Daily actions (#627, not released)"

## Bị bác / chưa có nguồn

- Nguyên tắc "chỉ xử lý đúng phạm vi, mục đích" của Luật 91/2025/QH15 (Điều 3): chưa đọc được nguyên văn. Bản Công báo là PDF máy này không mở được; chỉ thấy đoạn trích qua kết quả tìm kiếm. Chưa dùng làm căn cứ. Cần đọc lại trước khi sửa câu chữ privacy cho mood.
- Mood có thuộc nhóm dữ liệu nhạy cảm theo luật hay không: chưa có nguồn đã đọc.
- Tiêu chí 2.5.5 (mức AAA, 44 px): chưa đọc nguyên văn, không dùng làm căn cứ.
- Dự án mã nguồn mở có cách làm tương tự (hai gợi ý, thiết bị chọn theo trạng thái cục bộ): chưa tìm.
- Nghiên cứu hành vi về việc đưa việc nhỏ hơn khi người dùng mệt: chưa tìm; mốc 90% là chỉ số nội bộ của #627.
