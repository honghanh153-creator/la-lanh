# Thế giới pixel ghép đôi: nghiên cứu sâu (07/11/2026)

Ý tưởng của owner:
- Một thế giới pixel kiểu "sim". Người lớn chủ động đăng ký sẽ hiện thành avatar.
- Trong các buổi ghép đôi theo lịch, ai muốn làm gì thì làm: làm trò khùng điên, đọc sách, đi dạo...
- Có hai cách ghép:
  - **Thấy rồi muốn làm quen.** Cả hai bên phải đồng ý.
  - **Tới giờ hệ thống tự ghép.**
- Ghép xong thì hai người ngồi nói chuyện, tương tác và chơi một hoạt động nhỏ với nhau.

Đây là tài liệu nghiên cứu, chưa phải PRD. Chưa có code. KS-26 vẫn BLOCK.

Cách làm:
- Chạy workflow deep-research: 5 hướng tìm kiếm, 22 nguồn, 96 claim. Mỗi claim được 3 agent kiểm chứng độc lập; 22 claim qua, 3 claim bị bác.
- Claude tự đọc văn bản gốc Nghị định 147/2024 (bản DOC trên Công báo) và Điều 4 Nghị định 356/2025, vì không claim pháp lý Việt Nam nào trong workflow qua được bước kiểm chứng.

## 1. Bằng chứng (đã kiểm)

### Khoa học
- **Hồ sơ tĩnh dự đoán kém người mình sẽ thích khi gặp thật.**
  - Finkel et al. 2012 (Psychological Science in the Public Interest, tổng quan) viết rằng hồ sơ biến người ba chiều thành màn hình hai chiều, đánh mất sự ăn ý và hài hước.
  - Eastwick & Finkel 2008 (speed-dating, N=163): sở thích tự khai khớp kém với người thật mà mình thích.
  - Độ tin: vừa. Li et al. 2013 phản bác một phần. Mẫu chỉ gồm sinh viên Mỹ.
  - Nguồn: [PubMed 26173279](https://pubmed.ncbi.nlm.nih.gov/26173279/), [Eastwick & Finkel 2008](https://faculty.wcas.northwestern.edu/eli-finkel/documents/MatePrefs_FINAL6-5-07.pdf).
- **Avatar và không gian di chuyển được có thể gần với gặp thật hơn so với chat chữ.**
  - Đây mới là *giả thuyết* của Finkel et al. 2012, chưa phải kết quả thực nghiệm.
  - Bài báo cũng cảnh báo: nói chuyện qua máy quá lâu trước khi gặp dễ khiến người ta vẽ ra hình ảnh lý tưởng rồi vỡ mộng.
- **Không có bằng chứng thuật toán ghép đôi hiệu quả.** Độ tin: cao.
  - Thông tin có trước khi gặp giải thích rất ít sự hấp dẫn giữa hai người cụ thể (Finkel 2012; Joel, Eastwick & Finkel 2017; Joel et al. 2020, PNAS, 43 bộ dữ liệu).
  - Hệ quả: chế độ "tới giờ tự ghép" chỉ được gọi là **cơ hội gặp**. Không gọi là "hợp nhau", không gắn điểm hợp cung hoàng đạo.

### Tiền lệ và an toàn
- **Habbo Hotel (2012):**
  - Channel 4 phát hiện chat tình dục và nguy cơ grooming, dù Habbo có hơn 225 người kiểm duyệt.
  - Habbo tắt toàn bộ chat. Khi mở lại, người dùng phải làm quiz an toàn trước khi được nói, rồi mở dần quyền chat.
  - Bài học: **quyền chat tự do phải được mở dần, không cho ngay.** Nguồn: [Channel 4](https://www.channel4.com/news/what-is-happening-in-habbo-hotel).
- **Quấy rối trong thế giới avatar đang tăng.** Mute và chặn thường bị đánh giá là chưa đủ.
  - Nguồn: Weerasinghe et al. 2025, IEEE TVCG ([eprints](https://eprints.gla.ac.uk/346393)). Khảo sát 100 người dùng social VR, không phải game pixel 2D.
- **Nevermet (app hẹn hò VR):**
  - Hồ sơ chỉ có avatar, không có mặt người. Chỉ ghép khi cả hai cùng thích. Chỉ cho người 18+.
  - Mọi hồ sơ được người kiểm duyệt duyệt tay.
  - Nguồn duy nhất là trang tự mô tả trên [App Store](https://apps.apple.com/app/id1601331019), nên không chứng minh được hiệu quả.

### Chính sách kho ứng dụng
- **Apple 1.2:** app có nội dung người dùng tạo ra phải có đủ bốn thứ:
  - Lọc nội dung trước khi hiện.
  - Báo cáo và phản hồi kịp thời.
  - Chặn người dùng.
  - Thông tin liên hệ công khai.

  Apple có thể gỡ app không báo trước nếu app chủ yếu dùng cho "random or anonymous chat"; cụm này được thêm vào khoảng tháng 2/2026. 1.1.4 cấm app tìm quan hệ tình dục chóng vánh (hookup). Nguồn: [App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/).
- **Google Play:**
  - App có chức năng chính là hẹn hò phải bật Restrict Minor Access.
  - App mà hẹn hò chỉ là tính năng phụ được miễn, nếu có cơ chế kiểm tuổi hiệu quả. Cổng tuổi dễ lách (chỉ tick 18+ hoặc nhập ngày sinh) có thể không được chấp nhận.
  - Child Safety Standards áp dụng cho app Social, Dating và chat ngẫu nhiên, kể cả app chỉ dành cho 18+.
  - Nguồn: [16838200](https://support.google.com/googleplay/android-developer/answer/16838200?hl=en), [16926792](https://support.google.com/googleplay/android-developer/answer/16926792?hl=en), [14747720](https://support.google.com/googleplay/android-developer/answer/14747720?hl=en).

### Pháp lý Việt Nam (Claude đọc văn bản gốc)
- **Có thể là "mạng xã hội" dù không phải game.**
  - Theo Nghị định 147/2024, Điều 3 khoản 25, mạng xã hội là hệ thống "cho phép người sử dụng dịch vụ cung cấp, trao đổi, tương tác, chia sẻ thông tin với nhau". Ghép đôi xong ngồi nói chuyện khớp định nghĩa này.
  - Nếu có hoạt động nhỏ kiểu game thì có thể đồng thời là "trò chơi điện tử trên mạng" (khoản 34). Khi đó KS-26 áp dụng.
  - Đây là suy luận, cần luật sư chốt.
- **Nghĩa vụ của mạng xã hội trong nước:**
  - Điều 24 khoản 6 và Điều 25:
    - Phải là tổ chức hoặc doanh nghiệp.
    - Phải có giấy xác nhận thông báo. Khi đạt từ 10.000 lượt truy cập hoặc hơn 1.000 người dùng thường xuyên mỗi tháng thì cần giấy phép.
    - Chỉ mạng xã hội có giấy phép mới được có hoạt động phát sinh doanh thu.
  - Điều 27 khoản 2–3:
    - Lưu thông tin tài khoản, giờ đăng nhập, đăng xuất và IP **ít nhất 2 năm**.
    - Có ít nhất một máy chủ tại Việt Nam.
    - Lưu họ tên, ngày sinh, số điện thoại của người dùng.
    - **Xác thực tài khoản bằng số điện thoại Việt Nam.** Chỉ tài khoản đã xác thực mới được đăng hay bình luận.
    - Có cơ chế lọc thông tin vi phạm.
- **Dữ liệu nhạy cảm** (Nghị định 356/2025, Điều 4 khoản 1; đọc qua bản trên LuatVietnam, chưa đối chiếu Công báo):
  - điểm c: đời sống riêng tư. Ý định hẹn hò có thể thuộc nhóm này.
  - điểm e: đời sống tình dục, xu hướng tình dục. Câu hỏi "muốn gặp nam/nữ/ai cũng được" để lộ thông tin này.
  - điểm h: vị trí xác định qua dịch vụ định vị.
  - **điểm l: dữ liệu theo dõi hành vi, hoạt động sử dụng mạng xã hội và dịch vụ trực tuyến.** Ghi lại ai đang làm gì trong thế giới chính là loại dữ liệu này.

  Hệ quả: cốt lõi của sản phẩm ("thấy người ta làm gì") là dữ liệu nhạy cảm. Cần đồng ý riêng, phân quyền truy cập và đánh giá tác động.
- **Mức phạt:** Nghị định 174/2026 (từ 01/7/2026) có mức phạt cho game (Điều 98–99). Chưa đọc được điều khoản phạt riêng cho mạng xã hội.

## 2. Bị bác hoặc chưa có bằng chứng
- **Bị bác 0-3:** "Nhiều lựa chọn khiến chọn tệ hơn" (Fisman 2006). Không dùng làm lý do cho nhóm nhỏ.
- **Chưa có nghiên cứu nào kiểm:** xem avatar pixel làm trò có dự đoán được sự hấp dẫn không. Đây là giả thuyết của owner, cần chơi thử để biết.
- **Workflow không xác minh được:** nghiên cứu của Aron về hoạt động mới lạ chung, hiệu ứng gần gũi, số liệu lừa đảo tình cảm ở Việt Nam, và các tiền lệ Club Penguin, ZEPETO, Gather, Bumble/Hinge.

## 3. Đề xuất format (ý kiến của Claude, chưa kiểm)

Xếp từ ít rủi ro đến nhiều rủi ro:

| Format | Mô tả | Vướng luật (suy luận) | Riêng tư |
|---|---|---|---|
| **F1. Sự kiện gặp mặt thật + màn chiếu pixel** | Host tổ chức buổi gặp thật. Thế giới pixel chạy trên một máy chiếu lên màn hình. Mỗi người chọn hành động cho avatar của mình bằng thẻ hoặc host bấm hộ. Ghép bằng "vẫy tay" trên thẻ giấy, rồi nói chuyện trực tiếp | Thấp nhất: không tài khoản, không tương tác qua mạng | Không lưu gì sau buổi |
| **F2. Phòng online theo lịch, nhóm nhỏ, không chat tự do** | 8–12 người, 30–45 phút. Mỗi người chỉ dùng hành động có sẵn và câu nói có sẵn. Ghép khi cả hai vẫy tay. Sau đó cùng chơi một hoạt động nhỏ 10 phút; chat tự do chỉ mở khi cả hai muốn tiếp | Gần như chắc chắn là mạng xã hội, có thể cả game. Cần doanh nghiệp, giấy xác nhận thông báo, xác thực số điện thoại, lưu nhật ký 2 năm. KS-26 | Hành vi trong buổi là dữ liệu nhạy cảm (điểm l). Chỉ giữ trong buổi, không chấm điểm hành vi |
| **F3. Thế giới mở luôn chạy** | Lúc nào cũng có người đi lại, ai cũng thấy ai | Như F2, nặng hơn về kiểm duyệt | Rủi ro bị đeo bám cao nhất. Không nên làm |

Claude đề xuất:
1. Thử **F1** trước, ngay ở buổi gặp thật của owner. Mục đích là kiểm giả thuyết "thấy người ta khùng điên thì muốn làm quen" mà không cần xin phép gì.
2. Chỉ làm **F2** sau khi luật sư trả lời và owner chấp nhận định danh người dùng.

Nguyên tắc thiết kế cho cả F1 và F2:
- **Không có vị trí thật.** Thế giới là hư cấu, không có bản đồ thành phố, không có "người ở gần bạn".
- **Tự thể hiện bằng hành động, không bằng chữ:** đọc sách, tưới cây, nhảy, làm bánh, ngồi ngắm mưa... Bảng hành động đủ ngớ ngẩn để vui, nhưng không có hành động động chạm vào avatar người khác.
- **Vùng cá nhân mặc định.** Mỗi người có một nút "rời đi" luôn hiện.
- **Ghép do người dùng chủ động:** chỉ lộ cho nhau khi cả hai cùng vẫy tay. Người không vẫy lại không bao giờ biết mình đã được vẫy.
- **Ghép tự động:** gọi là "một cơ hội gặp", có thể từ chối không cần lý do, không hiện điểm hợp.
- **Sau khi ghép:** cùng chơi một hoạt động nhỏ, ví dụ ghép tranh hoặc cùng rút một lá tarot. Lá tarot chỉ để đổi giọng câu chuyện, không phải "điềm". Chat tự do mở sau, khi cả hai cùng muốn (rút kinh nghiệm Habbo).
- **Mặt thật:** không hiện trước khi ghép (theo Nevermet). Sau khi ghép, mỗi người tự quyết.
- **Giữ bình yên:** không chuỗi ngày, không xếp hạng, không "X người đang xem bạn". Buổi có giờ kết thúc.

## 4. Câu hỏi cho luật sư (gộp vào Q15–Q17)
1. Thế giới pixel có avatar, ghép đôi và chat 1:1 nằm trong app Lá Lành thì là mạng xã hội, trò chơi điện tử trên mạng, hay cả hai (Nghị định 147 Điều 3 khoản 25, 34)? Bỏ điểm, xếp hạng, vật phẩm thì có thoát diện game không?
2. Nếu chỉ dùng hành động và câu có sẵn, không chat tự do, có còn là "trao đổi, tương tác thông tin" không?
3. F1 (một máy của host chiếu lên màn hình ở buổi gặp thật, người chơi không có tài khoản) có phải cung cấp dịch vụ trên mạng không?
4. Nghĩa vụ lưu nhật ký 2 năm (Điều 27 khoản 2 điểm b) xung đột với tối thiểu hóa dữ liệu theo Luật Bảo vệ dữ liệu cá nhân thế nào? Có được giữ ít hơn không?
5. Ý định hẹn hò, giới muốn gặp và hành vi trong thế giới có phải dữ liệu nhạy cảm theo Nghị định 356 Điều 4 khoản 1 điểm c, e, l không? Cần đồng ý riêng và đánh giá tác động ra sao?
6. Kiểm tuổi 18+ bằng cách nào (VNeID, giấy tờ, ước lượng tuổi) để vừa đạt chuẩn của Google vừa ít dữ liệu nhất?
7. Mức phạt của Nghị định 174/2026 cho mạng xã hội không có giấy xác nhận thông báo, hoặc không xác thực số điện thoại?

## 5. Nguồn chưa kiểm hết
- Nghị định 356/2025: mới đọc bản trên [LuatVietnam](https://luatvietnam.vn/dan-su/nghi-dinh-356-2025-nd-cp-quy-dinh-chi-tiet-luat-bao-ve-du-lieu-ca-nhan-422896-d1.html), chưa đối chiếu Công báo.
- Có tin Google sẽ áp quy tắc chặn trẻ vị thành niên cho app chat ngẫu nhiên từ 26/8/2026, không còn miễn cho tính năng phụ. Chưa xác nhận từ nguồn chính thức của Google.
- Không áp dụng cho Ma Sói lớp học của PR #93 hay game lab 14. Đây là một hướng sản phẩm riêng.
