# Lá Lành — quyết định UX-first cho Chart Synthesis

Ngày chốt: 2026-09-07  
Phạm vi: Daily Note, Aura, Insight sâu, provider sinh nội dung, lưu/chia sẻ/xóa và app Capacitor.

Tài liệu này chốt các điểm còn mở của kế hoạch chart synthesis. Khi có xung đột giữa tốc độ phát hành, độ “wow” và quyền lợi người dùng, ưu tiên khả năng hiểu, quyền kiểm soát, tính riêng tư và khả năng dùng app ngay cả khi provider ngoài bị lỗi.

## 20 quyết định đã chốt

1. **App cho giá trị trước đăng nhập.** Người dùng đi từ onboarding đến Vibe, Daily Note và mood check-in bằng guest session; chỉ yêu cầu tài khoản ở hành động cần danh tính bền vững.
2. **Một nguồn nội dung duy nhất.** Home, Note Detail, Aura và Insight dùng cùng immutable reading revision; không còn copy Moon/placement tự ghép ở client.
3. **Deterministic là sản phẩm thật.** Note đầy đủ phải xuất hiện ngay khi mở app, không phụ thuộc provider AI hoặc mạng đến provider.
4. **AI chỉ tạo ứng viên.** Kết quả provider phải qua schema intake và bốn gate cục bộ trước khi được lưu ở trạng thái `available`.
5. **Không hot-swap.** Note đang đọc không tự đổi; bản tốt hơn xuất hiện như một món quà và chỉ trở thành active sau thao tác rõ ràng của người dùng.
6. **Vibe và Aura phải khác dễ nhận biết.** Vibe dùng dữ liệu ngày sinh với độ chính xác tương ứng; Aura chỉ mở sau giờ và nơi sinh đủ điều kiện, đồng thời nêu rõ lớp thông tin mới.
7. **Đọc đời thường trước, astro sau.** Hook, biểu hiện và việc nhỏ để thử đứng trước; factor/evidence nằm trong phần “Vì sao Lá nói vậy?” do người dùng chủ động mở.
8. **Disclaimer tinh tế nhưng luôn có.** Surface dùng một câu ngắn; disclosure đầy đủ nằm ở detail, không dựng bảng cảnh báo lớn cạnh mọi đoạn nội dung.
9. **Nội dung gợi mở, không điều khiển.** Cấm tiên tri chắc chắn, chẩn đoán, gây sợ, gây tội lỗi, tạo phụ thuộc hoặc xúi quyết định y tế, pháp lý, tài chính, an toàn và quan hệ quan trọng.
10. **70% natal / 30% transit là mục tiêu, không phải quota giả.** Chỉ có phần transit khi engine có tín hiệu đủ mạnh; nếu không, reading là 100% natal và không render bonus rỗng.
11. **Background chỉ là lens.** Context tùy chọn chỉ chọn ví dụ gần người dùng hơn; không được tăng confidence, trở thành evidence hoặc khiến hệ thống giả vờ “đoán trúng”.
12. **Không chatbot ở MVP.** Không memory hội thoại, tools hoặc lời khuyên theo lượt; tập trung vào reading một chiều đã được kiểm duyệt để giảm persuasion và dependency risk.
13. **Western generated trước, Jyotish generated đóng.** Người dùng vẫn có thể switch hệ tính/đọc dữ liệu chart, nhưng prose Jyotish chỉ mở sau expert sign-off và corpus riêng.
14. **Provider-neutral ở domain.** Domain chỉ biết closed result union; model/SDK/vendor nằm sau adapter và có kill switch.
15. **Một request, không state.** Provider call dùng Responses một lượt, non-streaming, `store=false`, không conversation, background mode, tools, files hoặc retrieval.
16. **Payload tối thiểu.** Provider chỉ nhận ReadingPlan đã allowlist; không ngày/giờ/nơi sinh thô, tọa độ, tên, contact, guest/account/session/chart ID hoặc free text.
17. **Retry có một chủ.** Worker là nơi duy nhất quyết định retry; timeout sau khi đã gửi không retry mơ hồ để tránh hai nội dung cạnh tranh cho cùng key.
18. **Exact revision cho lưu/chia sẻ.** Lưu và link share luôn đóng băng đúng bản người dùng đã thấy; update sau đó không sửa ký ức hoặc link cũ.
19. **Offline không giữ prose riêng tư mới.** Queue chỉ lưu session epoch, note/revision ID và last intent; rich reading ở memory hoặc server-owned snapshot, xóa guest dọn toàn bộ key liên quan.
20. **App-first phải fail closed.** Native build chỉ được coi là dùng được khi có HTTPS API origin rõ ràng, cookie/session transport đã test, navigation allowlist, release logging tắt và store/privacy evidence; `cap sync` hoặc web pass không đủ để gọi là app release-ready.

## 6 đề xuất được chấp nhận để triển khai tuần tự

1. **Shadow Western:** chạy provider ở môi trường nội bộ, đo gate result bằng enum/count và tuyệt đối không publish text cho người dùng trước Go/No-Go.
2. **Benchmark tiếng Việt:** corpus phải đo unsupported fact, genericness, usefulness, repetition, tone và safety; ưu tiên “hiểu và dùng được” hơn văn phong bay bổng.
3. **Governance provider:** khóa model/SDK đã test, timeout, ngân sách, retention/DPA/region/subprocessor/cross-border; thay model phải chạy lại lifecycle review.
4. **Native transport hardening:** build app với HTTPS API origin, native cookies/HTTP theo tài liệu Capacitor và kiểm chứng guest + CSRF + delete trên simulator/device.
5. **Store privacy pack:** sinh data inventory dùng cho Apple App Privacy, Privacy Manifest và Google Play Data Safety từ hành vi/SDK thực tế, không khai theo ý định.
6. **Operational rollback:** một kill switch đưa toàn bộ sản phẩm về deterministic mà vẫn giữ nguyên saved/shared snapshots và không làm gián đoạn Daily Note.

## 3 lưu ý không được che giấu

1. **`store=false` không phải Zero Data Retention.** Nó tắt application-state storage của Responses; abuse-monitoring retention mặc định vẫn có thể tới 30 ngày nếu tổ chức chưa được duyệt ZDR/MAM.
2. **Native source chưa đồng nghĩa binary phát hành được.** Máy build phải có Xcode/Simulator và JDK/Android toolchain; production API domain, signing, associated domains, privacy report và device QA vẫn cần bằng chứng thật.
3. **Astrology là công cụ phản tư.** Consent cho mục đích cá nhân hóa không biến suy luận thành sự thật khách quan và không cho phép hệ thống thay người dùng đưa ra quyết định.

## Liên kết thực thi

- Kế hoạch: `docs/plans/2026-09-06-1954-feat-chart-synthesis-agent-plan.md`
- Product contract: R1–R25, F1–F5, AE1–AE13.
- App design: Cosmic Glass Signal, Be Vietnam Pro, một note chính trong viewport và evidence mở theo nhu cầu.
- Release posture: provider production off; deterministic path production-capable; generated Jyotish off.
