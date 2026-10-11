# Tarot: sửa nghĩa, tổng hợp cả bài và kiểm soát trước khi hiển thị

Ngày rà: 2026-10-08. Trạng thái: **đề xuất sau khi đọc code và nghiên cứu**, chưa triển khai hoặc deploy. Không gọi API tính phí trong lượt này. CMS không phải điều kiện để engine chạy.

## 1. Kết luận

Không chỉ sửa prompt. Nguồn nghĩa đang quá chung, phần tổng hợp chưa đọc đủ trải bài, và gate chưa đánh giá người đọc có hiểu bài hay không. AI viết lại từ nguồn này có thể tạo câu trôi chảy nhưng vẫn sai trọng tâm.

Hướng đề xuất: **nghĩa riêng từng lá → bối cảnh đã biết → tổng hợp cả trải bài → viết ngắn, trực tiếp → gate độc lập → hiển thị**. Không đạt thì dùng bản đã biên tập, không đưa bản bị từ chối ra UI và không tự gọi AI lặp lại.

## 2. Vấn đề đã xác nhận ở nguồn

| Chỗ hiện tại | Vì sao người dùng khó hiểu | Cần thay đổi |
| --- | --- | --- |
| `apps/api/app/domains/tarot/knowledge.py`: 56 lá phụ ghép từ số + chất | Nhiều lá dùng một cơ chế giống nhau; Ba Gậy bị biến thành chia việc cho nhóm | Có nghĩa riêng cho đủ 78 lá; số/chất chỉ là thuộc tính phụ |
| `engine.py`: `_summary` lấy lá đầu | Tóm tắt không giải thích mối liên hệ giữa cả ba/năm lá | Tổng hợp đủ lá và vai trò từng vị trí |
| `engine.py`: cảnh và hành động theo nhóm chủ đề | Nhắn tin chậm, đoán ý và viết hai dòng xuất hiện ở nhiều bài không liên quan | Chỉ chọn cảnh phù hợp với câu hỏi/bối cảnh đã biết; không tự bịa sự kiện |
| `rewrite.py`: AI sửa `meaning_here` | Cảnh và hành động cũ vẫn hiện bên cạnh văn mới | Kiểm tra và viết lại toàn bộ phần đọc nhìn thấy, không chỉ một đoạn |
| `engine.py`: gate bắt từ cấm/phần trống; audit chủ yếu cấu trúc | Một bài đủ trường vẫn có thể lặp, sai nghĩa, không trả lời câu hỏi | Thêm kiểm tra nghĩa, bối cảnh, tổng hợp và độ dễ hiểu |
| `TarotPage.tsx`: tóm tắt đã nằm trước chi tiết, nhưng tiêu đề/chi tiết đều dài | Chỉ đổi vị trí không giải quyết được bài tóm tắt từ một lá và màn quá nhiều chữ | Khối “Tóm tắt bài của bạn” rõ ràng; chi tiết từng lá mở khi cần |

Các nguồn chính: `apps/api/app/domains/tarot/{knowledge,engine,rewrite,models}.py`, `apps/api/app/domains/content/review_agent.py`, `apps/api/scripts/audit_tarot_knowledge.py`, `apps/web/src/features/tarot/TarotPage.tsx`, `apps/web/src/shared/styles/ultraviolet.css`, `docs/foundation/la-lanh-tarot-engine-spec.md`.

## 3. Kiến thức phải đúng trước khi viết hay

Mỗi lá cần một bản ghi do người biên tập duyệt:

- ID lá, tên Việt/Anh, bộ bài, chiều lá; hiện tại chỉ triển khai nghĩa xuôi nếu hệ thống chưa hỗ trợ đảo.
- 1–2 ý chính riêng của lá, hình ảnh gợi nghĩa, điểm cần chú ý. Không mặc định nghĩa tiêu cực ở mọi lá.
- Nghĩa theo vị trí và chủ đề; những cách diễn giải không được suy ra.
- Nguồn tham chiếu, phiên bản, trạng thái duyệt, ví dụ đúng và ví dụ sai.

Ví dụ kiểm tra ba lá người dùng gửi:

- **Vua Cốc:** giữ bình tĩnh, cảm thông và xử lý cảm xúc chín chắn. Không mặc định thành kiểm soát người khác. [Tham chiếu của tác giả Biddy Tarot](https://biddytarot.com/tarot-card-meanings/minor-arcana/suit-of-cups/king-of-cups/).
- **Ba Gậy:** nhìn xa hơn, theo dõi điều đã bắt đầu và chờ kết quả. Không đồng nhất với chia việc/cộng tác của Ba Tiền. [Tham chiếu Ba Gậy](https://biddytarot.com/tarot-card-meanings/minor-arcana/suit-of-wands/three-of-wands/).
- **Sáu Tiền:** cho và nhận, sự hỗ trợ, mức độ cân bằng trong trao đổi. Không mặc định một bên đang tạo món nợ ngầm. [Tham chiếu Sáu Tiền](https://biddytarot.com/tarot-card-meanings/minor-arcana/suit-of-pentacles/six-of-pentacles/).

Đây là hệ diễn giải Tarot, không phải bằng chứng về sự kiện hoặc suy nghĩ của người khác. Các sách phục vụ phương pháp và đối chiếu; không tuyên bố đã đọc/nạp toàn bộ sách hoặc sao chép nguyên văn vào sản phẩm.

## 4. Bối cảnh và bản hướng dẫn nghĩa cho writer

Không đưa một đoạn văn chung chung rồi yêu cầu Luna làm hay hơn. Gửi bản hướng dẫn có cấu trúc:

| Thành phần | Nội dung |
| --- | --- |
| Câu hỏi cần trả lời | Ý hỏi đã chuẩn hóa; dữ kiện nào thực sự có, điều nào chưa biết |
| Bối cảnh | Chủ đề và tình huống người dùng chọn; ví dụ đang làm quen hoặc muốn nói rõ một chuyện |
| Lá và vị trí | ID/chiều/vai trò/ID nghĩa được phép dùng; không cho writer đổi lá hoặc trải bài |
| Mối liên hệ | Các ý hỗ trợ, khác nhau hoặc bổ sung giữa các lá; chưa có cơ sở thì không cố dựng xung đột |
| Kết quả cần viết | Một câu chốt, tóm tắt cả bài, ý ngắn từng lá, tối đa một hành động chung |
| Giới hạn | Không đọc hộ suy nghĩ người khác; không khẳng định sự kiện chưa có; không thêm lời khuyên hệ trọng |

“Với 1 người” chưa đủ để biết muốn hỏi gì. Gợi ý chọn một ý ngắn: “Cách hai người nói chuyện”, “Mình nên nói rõ điều gì”, “Công sức hai bên có cân không”. Không bắt khai tên, thông tin nhạy cảm hay kéo dài onboarding.

Câu hỏi gốc ở backend, mã hóa và có thời hạn. Writer nhận bối cảnh tối thiểu đã chuẩn hóa; không mặc định gửi tên, ngày/giờ/nơi sinh hoặc câu hỏi thô ra ngoài. Bối cảnh mới cần danh sách trường cho phép và cập nhật consent/data map trước khi triển khai.

## 5. Gate trước khi publish

Gate chạy ở backend cho cả bản xác định sẵn và bản AI. Frontend không tự quyết bài đạt hay không.

1. **Đúng dữ liệu:** đúng ID/số/chiều/vị trí lá, phiên bản nghĩa, chủ đề; không thay bài đã rút.
2. **Đúng nghĩa:** các luận điểm phải gắn với nghĩa đã duyệt. Có fixture âm cho Ba Gậy thành chia việc, Vua Cốc xuôi thành thao túng, các lá khác nhau dùng cùng một đoạn.
3. **Trả lời cả bài:** tóm tắt phản ánh đủ 1/3/5 lá theo vai trò, không chỉ lá đầu; không biến thành các bài giải nghĩa rời rạc.
4. **Dễ hiểu:** câu ngắn, chủ ngữ/hành động rõ; bỏ cụm ghép như “khi xử lý ... cách đón nhận ...”. Không lặp ý giữa tiêu đề, nghĩa, ví dụ và hành động. Không bắt mỗi lá có đủ mọi loại đoạn nếu chỉ làm bài dài hơn.
5. **An toàn và privacy:** không khẳng định ý định người khác, bệnh lý, kết quả tài chính hay tương lai chắc chắn. Quyền sử dụng dữ liệu phải còn hiệu lực lúc gửi và lúc ghi kết quả.

JSON schema, ID nghĩa và luật độ dài hỗ trợ kiểm tra, nhưng **không chứng minh được câu có ý nghĩa**. Cần bộ mẫu chuẩn do người biên tập duyệt và kiểm tra mức hiểu với người dùng thật. Judge AI, nếu dùng sau này, không phải người duyệt cuối và không tự có quyền publish.

Ngân sách hiện nhỏ: dùng luật + bộ mẫu chuẩn + review biên tập trước. Không tự bật một lần gọi judge AI thứ hai. Mỗi tác vụ viết lại có reservation, giới hạn và kết quả gate; lỗi thì không regenerate vô hạn.

Nếu gate không đạt: giữ các lá đã rút, hiển thị bản dự phòng đã duyệt cho đúng lá/chủ đề/vị trí. Nếu chưa có bản phù hợp, báo phần đọc đang chưa sẵn sàng; không lấp bằng văn chung chung. Việc từ chối văn không được làm rollback lá cuối hoặc buộc người dùng rút lại.

## 6. Nội dung mẫu — chưa phải kết quả sản phẩm

Giả sử câu hỏi là “Mình nên nói rõ hay chờ thêm?”, với ba lá xuôi Vua Cốc, Ba Gậy, Sáu Tiền:

> **Có thể nói rõ, không cần nói dồn.**
>
> Bài này gợi ý bạn nói điều mình muốn một cách bình tĩnh, rồi để người kia có thời gian trả lời. Vua Cốc nói về cách giữ bình tĩnh; Ba Gậy nhắc đến việc chờ phản hồi; Sáu Tiền đặt câu hỏi về công sức hai bên. Không chỉ nhìn việc bạn đã làm — hãy xem người kia có đáp lại bằng hành động không.

Ý ngắn từng lá:

- Vua Cốc — **Nói điều bạn cảm thấy, không biến nó thành lời buộc tội.**
- Ba Gậy — **Sau khi nói rõ, cho cuộc trò chuyện thời gian đi tiếp.**
- Sáu Tiền — **Nhìn cả phần bạn cho và phần bạn nhận.**

Một bước chung, không ba lời khuyên nối tiếp: “Chọn một điều muốn nói rõ trong lần trò chuyện tới. Sau đó xem câu trả lời và hành động thực tế.”

Lưu ý ở UI riêng, không chen vào mỗi đoạn: “Tarot gợi một cách nhìn; không cho biết chắc người kia nghĩ gì.” Không trình bày ví dụ này như trải bài thật khi chưa biết câu hỏi cụ thể của người dùng.

## 7. Bố cục kết quả

Thứ tự mong muốn:

1. Câu hỏi của bạn — chữ thường, ngắn; câu dài có mở rộng.
2. **Tóm tắt bài của bạn** — headline khoảng 6–12 từ, thân bài khoảng 50–80 từ cho ba lá. Không ép độ dài nếu làm mất nghĩa.
3. Ba/năm thẻ nhỏ: tên lá + vai trò + một ý ngắn. Các lá là dữ liệu đã chọn, không được đổi khi reload.
4. “Đọc từng lá” — mở chi tiết bằng accordion; tên lá là heading, không đưa nguyên câu mô tả core dài thành heading.
5. Một bước có thể thử; lưu ý nhỏ nhưng đủ tương phản, nằm riêng dưới phần đọc.

Một font, ba cấp chữ chính, không all caps cho đoạn dài. Giữ cream / ultraviolet / lime của concept hiện tại; lớp thần bí chỉ tập trung ở phần mở bài, không làm nền đọc tối và rối hơn. Kiểm tra 360/390/430 px, chữ lớn 200%, bàn phím và screen reader.

## 8. Màn bước vào Tarot

Luồng đề xuất: **rèm mở → nhập câu hỏi → xòe bài → chọn/lật → tóm tắt → chi tiết**.

- Khung tím có chiều sâu: rèm hoặc bóng tối tách nhẹ sang hai bên, ánh sáng ở mặt bàn, hạt sáng rất ít. Không thêm màn đăng nhập/consent mới nếu chưa cần.
- CTA “Vào trải bài”, kèm “Bỏ qua phần mở đầu”. Không bắt chờ animation hoặc giả làm tính toán.
- Chuyển cảnh khoảng 0,7–1,2 giây. Xòe/lật bài là chuyển động theo thao tác; không xoay/lắc toàn màn liên tục.
- Không tự phát âm thanh; không flash; chế độ giảm chuyển động dùng fade nhẹ hoặc không animation. Khi mở lại kết quả, đi thẳng đến bài đọc.
- Trạng thái đã xem chỉ là cờ giao diện; không lưu câu hỏi/tên người trong URL, analytics hoặc cờ local storage.
- Animation tự chạy dài hơn năm giây phải có cơ chế dừng phù hợp. Tham chiếu [W3C: animation from interactions](https://www.w3.org/WAI/WCAG21/Understanding/animation-from-interactions) và [CSS reduced motion](https://www.w3.org/WAI/WCAG22/Techniques/css/C39).

## 9. Tiền, key và data privacy: điều kiện trước pilot

Security scan của nguồn hiện tại đã chốt **11 phát hiện: 9 medium, 2 low**, coverage một phần (96/1142 file). Không tìm thấy key thật hay đường charge trực tiếp lên thẻ trong nguồn đã rà. Không kiểm tra live VPS, migration đã áp dụng, quyền key hay billing ở lượt này. Không có bản vá bảo mật hoặc deploy mới.

Các nhóm cần xử lý: TLS phải xác minh đúng DB server; giới hạn body trước parse và cardinality telemetry; sổ chi tiêu ngày không bị xóa cùng dữ liệu; rút consent/xóa guest/xóa precision phải chặn tác vụ rewrite tương ứng; payload hàng đợi phải được xóa theo retention.

API key chỉ ở worker là kiểm soát tốt nhưng chưa đủ. Key bị đánh cắp có thể được dùng ngoài ledger app. Cần giới hạn quyền key, kiểm tra giới hạn ở nhà cung cấp, tắt auto-reload theo lựa chọn chủ tài khoản và có kill switch. Không tự đổi billing/key. [OpenAI API key safety](https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety), [spend limits](https://developers.openai.com/api/docs/guides/spend-limits), [OWASP API resource consumption](https://api-security.owasp.org/editions/2023/en/0xa4-unrestricted-resource-consumption/).

Pilot theo 20 guest sessions hiện không phải danh sách 20 người được chủ app mời. Đề xuất quyền dùng rewrite trả phí do operator cấp riêng; giữ trải nghiệm khách cho tính năng không trả phí. Không dùng số người test như một cam kết chống abuse.

`store:false` không đồng nghĩa Zero Data Retention; phải kiểm tra chế độ dữ liệu nhà cung cấp và thông báo đúng cho người dùng. [OpenAI data controls](https://developers.openai.com/api/docs/guides/your-data). Pháp luật Việt Nam cần đối chiếu thêm theo dữ liệu gửi ra ngoài; [Luật 91/2025/QH15](https://congbao.chinhphu.vn/van-ban/luat-so-91-2025-qh15-45578.htm) có hiệu lực 01/01/2026. Tài liệu này không kết luận tuân thủ pháp lý.

## 10. Thứ tự triển khai và tiêu chí nghiệm thu

### A. Chặn rủi ro trước test trả phí

Chỉ thực hiện bản vá sau khi người dùng cho phép. Kiểm thử bằng provider giả: xóa/rút consent trong lúc đang chờ, không gửi mới hoặc publish sau rút quyền; không hồi quota khi xóa. TLS sai hostname/chứng chỉ bị từ chối; body lớn bị chặn trước parser; method lạ không tạo nhãn mới vô hạn. Kiểm tra live riêng, không mặc định nguồn local đã lên production.

### B. Engine và nội dung

- Nghĩa riêng đủ 78 lá được biên tập; ưu tiên sửa bộ ba bị phản ánh, sau đó kiểm tra toàn bộ.
- Bộ kiểm thử bao phủ lá/chủ đề/vai trò, trải 1/3/5 lá và các tổ hợp mâu thuẫn. Audit một lá không đại diện chất lượng ba/năm lá.
- Gate từ chối đúng các đoạn người dùng đã phản ánh; bộ mẫu tốt vẫn qua. Bản AI và bản không AI đều được kiểm tra.
- Tóm tắt phản ánh đủ trải bài; không khẳng định sự kiện ngoài dữ kiện hoặc kết luận thay người dùng.
- Không thay lá/câu hỏi khi viết lại, reload, timeout hoặc gate thất bại; kết quả cũ không bị âm thầm sửa.

### C. UI, animation và kiểm tra người dùng

- Người dùng nhìn thấy tóm tắt trước chi tiết; mở/đóng từng lá được bằng bàn phím, không layout overflow.
- Có bỏ qua intro và reduced motion; đường quay lại kết quả không diễn animation từ đầu.
- Mời 10–20 người thật đọc bài rồi nói lại bằng lời của họ: bài nói gì, từng lá thêm điều gì, điều nào chỉ là gợi ý. Mục tiêu thử nghiệm: ít nhất 80% hiểu đúng ý chính, không đọc thành sự thật về người kia. Chưa thực hiện test này.
- Chỉ mở pilot/deploy sau kiểm tra nội dung + UX + security/DP; mọi lời gọi trả phí nằm trong giới hạn đã được chủ tài khoản cho phép.

Các AC trên hiện là điều kiện triển khai, **chưa hoàn thành**. Không có cam kết loại bỏ tuyệt đối mọi nội dung khó hiểu: theo dõi phản hồi, dùng bản biên tập dự phòng và có quyền dừng publication khi gate/nguồn nghĩa sai.
