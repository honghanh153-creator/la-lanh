# Kế hoạch Nơi bình yên: hướng "góc nhà bình yên"

Ngày soạn: 01.11.2026.

Trạng thái: **đề xuất, chờ chủ sản phẩm và Codex review.** Kế hoạch này không đổi code app, API hay cấu hình.

Tài liệu gốc vẫn là [PRD Nơi bình yên](../foundation/la-lanh-noi-binh-yen-prd.md): bản 0.6 trên `collab/integration`, bản 0.7 trong PR #68 (đang chờ chủ sản phẩm). Kế hoạch này đề xuất phần sửa cho bản 0.8. Phần sửa chỉ được viết vào PRD sau khi #68 đã có kết luận, để hai PR không sửa cùng một file.

Thứ tự ưu tiên của chủ sản phẩm vẫn là: nội dung → quyền riêng tư → tính năng mới. Ngày 01.11, chủ sản phẩm cho làm tài liệu và bản mẫu ("hãy làm đi"). Phần xây vào app (giai đoạn 5) vẫn chờ chủ sản phẩm mở lại tính năng.

## 1. Vì sao có kế hoạch này

Ngày 01.11, chủ sản phẩm nhận xét:

- Nơi bình yên "chưa đủ hấp dẫn, chưa đủ animation, chưa cảm giác được vì sao phải làm".
- Bản mẫu vẽ bằng code "hoạt hình quá", không giống các reel tham chiếu. Ba bản mẫu ngày 21.10 cũng bị đánh giá "giả, không relax" vì lý do này.

Sau đó Claude thử tạo ảnh và video bằng Google Flow, trong tài khoản của chủ sản phẩm:

- 5 clip thử: hơi trà bốc lên; cửa sổ gỗ mở ra rồi mặt trời lên; bờ hoa nhìn biển kiểu R1; rèm lanh bay trong phòng nhìn ra biển; cốc trà trên hiên nhìn ra biển.
- 16 ảnh tĩnh, trong đó có 8 ảnh cảnh trong nhà: bếp buổi sáng, góc đọc sách, hiên mưa mái ngói, ban công.

Chủ sản phẩm nói rõ điều họ muốn: "thực chất ko cần là 1 cửa sổ, 1 hiên nhà, tôi chỉ muốn đem lại cảm giác bình yên nên cần những hình ảnh mang tính gần gũi, homey". Với các ảnh cảnh trong nhà, chủ sản phẩm nhận xét: "tôi thấy đẹp đấy".

Kết luận:

1. Hình ảnh phải là video chân thực (tạo bằng AI hoặc quay thật). Code chỉ điều khiển việc phát video và vẽ lớp phủ phía trên.
2. Chủ thể chính đổi từ **phong cảnh để ngắm** sang **những góc nhỏ gần gũi như ở nhà**.

## 2. Vì sao làm tính năng này

| Lý do | Giải thích |
|---|---|
| Đúng thời điểm người dùng đã mở app | Mỗi sáng người dùng đã mở Lá Lành để đọc Note hôm nay. Nơi bình yên nằm ngay sau Note nên không cần nhắc, không cần thông báo. |
| Lấp phần còn trống của bản chất Lá Lành | §0.1 của PRD chia bản chất thành ba phần: "được hiểu" (Note), "vui vẻ" (Mầm), "bình yên". Phần "bình yên" chưa có bề mặt nào trong app. |
| Khác app bói | Store đã có rất nhiều app tử vi và tarot (Apple Guideline 4.3(b) nói về nhóm app bão hòa). Một chỗ để ngồi yên, không đoán, không bán, giúp Lá Lành có lý do tồn tại riêng. |
| Người dùng mang theo được cảm giác | Lời hứa vẫn như PRD §2.5: **một khoảng lặng nhỏ đầu ngày**, không hứa "năng lượng cho cả ngày". |

"Góc nhà" đúng hơn "ô cửa sổ" vì cảm giác bình yên đến từ dấu hiệu của sự sống thường ngày: hơi trà bốc lên, mưa nhỏ giọt trên mái ngói, nắng sớm trên mặt bàn gỗ. Đây là những thứ người Việt trẻ nhớ về nhà, hoặc muốn có trong căn phòng thuê của mình. Phong cảnh đẹp thì YouTube đã có rất nhiều và miễn phí. Một góc nhà gần gũi, có Mầm ngồi cùng và có câu của ngày thì chưa ai làm.

## 3. Đề xuất sửa PRD (cho bản 0.8)

| Mục PRD 0.7 | Hiện tại | Đề xuất |
|---|---|---|
| §0, §2.3 nguyên tắc 2 | "Note là trang giấy, nơi bình yên là ô cửa sổ" | "Note là trang giấy, nơi bình yên là **một góc nhà**". Ô cửa sổ chỉ là một trong nhiều cảnh. |
| §0 tóm tắt | "một video thiên nhiên chân thực" | "một góc nhà hoặc cảnh thiên nhiên chân thực, gần gũi" |
| §2.4 tham chiếu | Chỉ có R1–R6 (Facebook reels) | Thêm nhóm "góc nhà" H1–H6 theo [thư viện prompt](../operations/nby-scene-prompt-library.md). Thư viện ghi phong cách, không dùng reel làm ảnh đầu vào. |
| §7.5 checklist (1) | "chủ thể thiên nhiên hoặc góc nhà yên tĩnh" | Giữ. Thêm các tiêu chí: (11) có ít nhất một dấu hiệu sống thường ngày (hơi nước, mưa, nắng di chuyển, rèm, lá cây); (12) cảnh trong nhà mang chất Việt Nam (gạch men, mái ngói, ấm trà, đồ tre, cây trong chậu), không giống căn hộ châu Âu; (13) đồ vật gọn, không bừa bộn, không có nhãn hàng. |
| §7.5 checklist (6) | "màu ngả phim, pastel ấm, vùng tối được nâng" | **Màu thật như mắt nhìn**: cân bằng trắng đúng, độ bão hòa và tương phản tự nhiên, vùng tối sạch, không ngả cam, không bạc màu. Chủ sản phẩm 01.11: "mình muốn màu sắc thật, cảm giác sống động chứ không phải giống như đang có một filter" |
| §7.6 bước 3 và script `nby-media.sh` (PR #68) | Script "chỉnh màu mềm": `eq=contrast=0.94:saturation=0.9:gamma=1.04`, `curves` nâng vùng tối, `colorbalance` ngả ấm | **Bỏ bước chỉnh màu mặc định**; chỉ giữ cắt, lặp, đổi kích thước và chuyển mã. Nếu cần sửa một clip cụ thể thì dùng tùy chọn riêng, có ghi lý do. Phải sửa trong #68 trước khi merge |
| §3.2 Cảnh | "Video AI … gần như tĩnh" | Giữ. Thêm thẻ cảnh `goc_nha` / `thien_nhien`. Thư viện khởi đầu ≥ 14 clip, trong đó ≥ 8 clip góc nhà. |
| NBY-02 thẻ video | ngày/đêm | Thêm thẻ thời tiết `mua` / `nang` để biên tập cân bằng. Thẻ chỉ dùng khi duyệt, **không** chọn theo thời tiết thật (giữ §2.2). |
| NBY-12 (mới, chờ thử) | Chưa có | "Thở cùng cảnh": xem §4. Chỉ vào PRD nếu bản mẫu đạt ở giai đoạn 2. |
| §8.6 công cụ | Yêu cầu chung cho mọi công cụ | Ghi kết quả kiểm Google Flow và Vertex Veo (§6, D24). |
| §12 quyết định | D1–D22 | Thêm D23–D27 (§7). |

Những điều **không** đổi: không người trong cảnh; không AI lúc chạy; không streak; không chọn cảnh hay câu theo cung, mood hay thời tiết thật; nhãn "Cảnh tạo bằng AI"; chữ người dùng viết không rời máy; đồ họa kiểu A (D21); không thêm tích hợp vào app (D22).

## 4. Trải nghiệm đề xuất (60–90 giây)

Phần này trả lời nhận xét "chưa đủ animation": thêm **một khoảnh khắc có chuyển biến** nhưng vẫn là video thật.

1. **Bước vào.** Đọc xong Note, chạm "Sáng nay ở nơi bình yên". Video góc nhà của hôm nay mở toàn màn hình. Âm thanh cảnh (mưa, chim, tiếng ấm nước) tăng dần trong 3 giây.
2. **Thở cùng cảnh** (tùy chọn, NBY-12 đề xuất). Một vòng tròn giấy kiểu A hiện ở giữa: "Thở cùng mình ba hơi nhé?". Mỗi hơi khoảng 4 giây hít vào, 6 giây thở ra. Cảnh có chuyển biến thật qua từng hơi. Bản mẫu thử hai cách:
   - **Cách 1, một clip chuyển biến:** clip có ánh sáng ấm dần, ví dụ nắng sớm lan trên bàn hoặc đèn bàn bật lên. Hơi thở kéo clip chạy tới một đoạn rồi dừng.
   - **Cách 2, chỉnh màu nhẹ trên video lặp:** mỗi hơi thở tăng độ ấm và độ sáng của video, dùng bộ lọc CSS. Rẻ hơn, nhưng có thể trông giả.

   Người dùng bỏ qua được bằng "Để sau". Cách nào bị người thử nói "giả" thì bỏ.
3. **Câu của ngày.** Sau hơi thứ ba (hoặc sau 3–5 giây nếu bỏ qua), Mầm trong thanh phụ đề đưa lên câu của ngày, như NBY-04.
4. **Ngồi tiếp hoặc làm một việc nhỏ.** Các việc nhỏ đã có: rót một cốc (NBY-05), viết rồi thả đi (NBY-07), cảnh khác ≤ 2 lần (NBY-02).
5. **Rời đi.** "Đi nhẹ nhé." Âm thanh nhỏ dần, quay về Home.

**Mầm** vẫn chỉ ở thanh phụ đề. Mầm không đứng trong cảnh, vì đặt nhân vật vẽ lên video thật sẽ lộ "hoạt hình".

**An toàn:**
- Hướng dẫn thở không hứa trị liệu, không đếm điểm.
- Có "Mình thấy không ổn" mọi lúc (NBY-08).
- Chế độ giảm chuyển động tắt chuyển biến ánh sáng, chỉ giữ chữ.

Bằng chứng cho phần thở ở mức khiêm tốn: tổng quan hệ thống của Zaccaro và cộng sự (2018, Frontiers in Human Neuroscience) thấy thở chậm (dưới 10 nhịp mỗi phút) đi kèm cảm giác thư giãn và bớt lo âu trong ngắn hạn, nhưng các nghiên cứu nhỏ và khác nhau nhiều. Vì vậy copy không được nói "giảm căng thẳng" hay "chữa lành". Chỉ dùng chữ mời: "Thở cùng mình ba hơi nhé?".

## 5. Các giai đoạn

| GĐ | Việc | Ai | Điều kiện xong | Cần chủ sản phẩm |
|---|---|---|---|---|
| 0 | Kế hoạch này và [thư viện prompt](../operations/nby-scene-prompt-library.md) | Claude | Codex APPROVE; chủ sản phẩm đọc | Đọc, chọn D23–D27 |
| 1 | Thư viện thử: tạo video cho 6 cảnh góc nhà H1–H6 bằng Flow (Veo 3.1 Fast, Frames, khung đầu = ảnh đã duyệt) | Claude làm trong tài khoản của chủ sản phẩm | Chủ sản phẩm chọn ≥ 4 clip đạt checklist §7.5 | Đồng ý dùng credit Flow; xem từng clip |
| 2 | Bản mẫu chạy được trên điện thoại: video lặp, âm thanh, thở cùng cảnh (cả hai cách), câu của ngày, thả đi; thử với 8–12 người 18–25 tuổi | Claude dựng; chủ sản phẩm mời người thử | Đạt G1 (≥ 70% nói "dịu, yên"), G2 (≥ 70% không thấy lỗi hình) và G3 (≥ 70% muốn mở lại sáng mai); chọn cách thở hoặc bỏ NBY-12 | Cho phép tải clip về máy; mời người thử |
| 3 | PRD 0.8: đưa §3 vào PRD sau khi #68 có kết luận; viết NBY-12 nếu đạt | Claude | Codex APPROVE | Duyệt các D |
| 4 | Sản xuất thư viện: ≥ 14 clip đã duyệt, qua script `scripts/media/nby-media.sh` (PR #68), nhãn AI, metadata nguồn gốc, âm thanh có license | Chủ sản phẩm tạo; Claude chạy script và kiểm | Đủ NBY-09, NBY-AI-AC04/AC05, sổ đăng ký §8.3 | Chốt D24 (công cụ cho clip phát hành) |
| 5 | Xây vào app theo NBY-01…NBY-10, cờ `noiBinhYen` tắt mặc định, chạy offline, trợ năng; staging; release | Claude/Codex theo vòng collab | DoD §10.1 của PRD và ba cổng AGENTS.md | **Lệnh mở lại tính năng**; lệnh merge, deploy |

Giai đoạn 1–2 không đụng code của app, nên làm song song với việc nội dung mà không đổi thứ tự ưu tiên. Mỗi giai đoạn có điểm dừng: chủ sản phẩm xem kết quả rồi mới sang giai đoạn sau.

**Bản mẫu ở giai đoạn 2:**
- Là một trang tĩnh. Không backend, không analytics, không gửi dữ liệu đi đâu.
- Không đưa clip vào repo công khai: clip chưa có license phát hành, và file lớn. Clip nằm ở thư mục local ngoài git.
- Nếu cần cho người thử mở trên điện thoại của họ: dùng một trang riêng tư, không công khai, không index, gỡ sau đợt thử. Cần chủ sản phẩm đồng ý trước khi đưa lên.

## 5a. Kết quả giai đoạn 1 (01.11)

Chủ sản phẩm cho làm ngày 01.11 ("làm đi"). Claude làm trong tài khoản Flow của chủ sản phẩm:

- 6 ảnh góc nhà mới: góc đọc có mèo, ban công chung cư, bàn học buổi tối, sân gạch hoa giấy (mỗi cảnh 1–2 biến thể). Các cảnh sửa theo chất Việt Nam đã ra đúng chất.
- 4 video 8 giây, khung đầu và khung cuối là cùng một ảnh: bếp sáng (H1), hiên mưa (H2), góc đọc có mèo (H3), sân gạch hoa giấy (H6). Kết quả từng cảnh ở [thư viện prompt](../operations/nby-scene-prompt-library.md) §4.
- Dừng ở 4 video thay vì 6 để giữ credit: gói còn 60 credit tới lần cộng 21.11. Ban công (H4) và bàn học (H5) mới có ảnh.
- Chưa tải clip về máy, nên chưa kiểm chỗ nối và nhấp nháy.

**Góp ý của chủ sản phẩm sau khi xem 4 video (01.11):** "mình muốn màu sắc thật, cảm giác sống động chứ không phải giống như đang có một filter".

- Nguyên nhân: khung prompt cũ có `warm muted film colors`; script #68 còn chỉnh màu thêm theo cùng hướng.
- Đã sửa: khung ảnh mới ở [thư viện prompt](../operations/nby-scene-prompt-library.md) §2, tạo lại 4 ảnh H1, H2, H3, H6 (không tốn credit). Ảnh mới xanh tươi, trắng sạch, vùng tối rõ. Đề xuất sửa §7.5 (6), §7.6 và script ở §3.
- Chưa làm lại 4 video: cần 80 credit, gói còn 60 tới 21.11. Chủ sản phẩm chọn: làm lại 3 video bây giờ, chờ 21.11, hay làm qua Vertex (D24).

Điều kiện xong của giai đoạn 1 (≥ 4 clip đạt §7.5) chưa đạt: chờ video làm lại theo màu thật.

## 6. Công cụ tạo video: đã biết gì

Đây là dữ liệu cho D24. Nguồn chính là ghi chú nghiên cứu `research_notes/Nơi bình yên video AI/ai_video_tools_terms.md` (ngày 21.10, nằm ngoài git), cùng phần kiểm thêm ngày 01.11.

| | Google Flow (gói Google AI của chủ sản phẩm) | Veo 3.1 GA trên Vertex AI |
|---|---|---|
| Dùng để | Thử ý tưởng nhanh, chọn khung hình | Có thể dùng cho clip phát hành |
| Quyền sở hữu đầu ra | Google ToS: Google không nhận quyền với đầu ra | Service Specific Terms §20(a): đầu ra là Customer Data |
| Bồi thường IP | Không có (gói cá nhân) | Có, cho model GA, đầu ra chưa chỉnh sửa, có điều kiện |
| Watermark nhìn thấy | Clip thử có dấu Veo ✦. Menu tài khoản Flow của chủ sản phẩm (01.11) có công tắc "Visible watermarking" bị khóa, ghi "Visible watermarking is required in your region": **ở Việt Nam không tắt được** | Không có |
| Watermark ẩn, nguồn gốc | SynthID (Flow FAQ) | SynthID và C2PA do Google ký |
| Giới hạn tuổi | Người dùng Flow phải từ 18 tuổi | §20(d) cấm dùng dịch vụ AI tạo sinh trong dịch vụ hướng tới người dưới 18 tuổi. Lá Lành chỉ tạo clip ngoài app rồi phát như file tĩnh, không gọi API trong app |
| Chi phí | Credit trong gói đang dùng | Trả theo giây video, chủ sản phẩm tự trả. Số tiền không ghi vào repo |
| Ảnh hưởng tới D22 | Không thêm tích hợp | Không thêm tích hợp vào app: theo §2.2 PRD, công cụ chủ sản phẩm tự dùng bên ngoài không phải tích hợp. Nhưng cần mở tài khoản Google Cloud, nên là việc của chủ sản phẩm |

Theo NBY-AI-AC05, không được xóa watermark nhìn thấy được. Vì clip Flow ở Việt Nam luôn có dấu ✦, Flow chỉ dùng để thử. Clip phát hành tạo qua Vertex (D24), hoặc chủ sản phẩm chấp nhận để dấu ✦ trong cảnh.

## 7. Quyết định cần chủ sản phẩm

| ID | Câu hỏi | Đề xuất | Trạng thái |
|---|---|---|---|
| D23 | Chủ thể của thư viện | "Góc nhà bình yên" là chính (≥ 8/14 clip đầu), thiên nhiên là phụ | **Hướng đã chọn** 01.11 ("tôi thấy đẹp đấy"); tỷ lệ chờ duyệt |
| D24 | Công cụ cho clip phát hành | Flow chỉ để thử, vì dấu ✦ không tắt được ở Việt Nam. Clip phát hành tạo qua Veo 3.1 GA trên Vertex, dùng lại ảnh khung đầu đã duyệt trong Flow | Chờ chủ sản phẩm (việc trả phí, tài khoản nhà cung cấp) |
| D25 | Có "Thở cùng cảnh" (NBY-12) trong v1 không | Quyết định sau giai đoạn 2, theo kết quả thử | Chờ thử |
| D26 | Con vật trong cảnh | Cho phép con vật nhà ngủ yên, nhỏ trong khung, không nhìn vào máy quay (ví dụ mèo cuộn tròn trong nắng). Không có người | Chờ duyệt |
| D27 | Cách thử bản mẫu | 8–12 người 18–25 tuổi, đồng ý bằng lời, ghi chú không tên; không ghi âm, ghi hình người thử | Chờ duyệt |

## 8. Ba cổng của AGENTS.md cho kế hoạch này

**Tài liệu và hợp đồng sản phẩm**
- Mọi thay đổi đều trỏ về mục PRD tương ứng (§3).
- AC mới (NBY-12) chỉ là đề xuất, chưa có hiệu lực.
- Copy mới không dùng "chữa lành" hay "năng lượng tích cực", và không hứa kết quả.

**Bảo mật**
- Kế hoạch không thêm endpoint, dịch vụ hay quyền truy cập nào.
- Bản mẫu là trang tĩnh, không backend.
- Clip tải từ Flow là dữ liệu không tin cậy. Chúng được đặt trong thư mục riêng và chỉ xử lý bằng ffmpeg đã vá, theo `nby-media-pipeline.md`.
- Không đưa link project Flow, tài khoản hay mật khẩu vào repo.

**Quyền riêng tư**
- Prompt tạo ảnh và video không chứa dữ liệu cá nhân.
- Cảnh không có người.
- Tài khoản Google dùng để tạo là của chủ sản phẩm. Dữ liệu tạo nội dung chịu chính sách của Google, chủ sản phẩm đã đồng ý ngày 01.11.
- Với người thử bản mẫu, chỉ ghi câu trả lời không tên, không ghi âm, không ghi hình, không lưu vào repo. Người dưới 18 tuổi không tham gia.
- Tính năng trong app vẫn không thêm trường dữ liệu cá nhân nào. Nhãn privacy của Apple và Google không đổi.

## 9. Bàn giao

**Nguồn đã kiểm:**
- PRD 0.6 trên `collab/integration` và PRD 0.7 trong PR #68.
- `ai_video_tools_terms.md` (21.10).
- Trang trợ giúp Google Flow (01.11, chỉ đọc được mục lục): https://support.google.com/flow
- Kết quả tìm kiếm về watermark của Flow (nguồn thứ cấp, mâu thuẫn nhau).
- Google Cloud Service Specific Terms: https://cloud.google.com/terms/service-terms

**Đã sửa trong kế hoạch so với đề xuất trong chat:**
- Đề xuất trong chat gọi phần sửa là "PRD 0.5", nhưng PRD đã ở 0.7. Kế hoạch đổi thành đề xuất cho 0.8 và không sửa trực tiếp PRD, để tránh xung đột với #68.

**Rủi ro còn mở:**
- Đã kiểm trong cài đặt Flow: dấu ✦ không tắt được ở Việt Nam. Quyền dùng thương mại của gói Flow vẫn chưa đọc được trên trang chính thức; không ảnh hưởng nếu chọn Vertex cho clip phát hành.
- Ảnh khung đầu tạo bằng Nano Banana trong Flow có thể cũng mang dấu nhìn thấy hoặc SynthID; trước khi dùng làm khung đầu cho Vertex phải kiểm file ảnh.
- Veo 3.1 GA trên Vertex ghi ngày ngừng là "November 17, 2026 or later". Cần kiểm lại model hiện hành trước giai đoạn 4.
- Bảo hiểm bồi thường IP của Vertex chỉ áp dụng cho đầu ra chưa chỉnh sửa, mà script lặp có chỉnh sửa. Vì vậy phải giữ bản gốc và prompt.
- Cách 2 của "Thở cùng cảnh" có thể trông giả.

**AC/DoD chưa hoàn tất:** toàn bộ NBY-01…NBY-12 và DoD §10.1 của PRD. Kế hoạch này chỉ là tài liệu.
