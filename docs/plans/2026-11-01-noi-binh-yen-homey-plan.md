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
| §7.5 checklist (2) | "không người, khuôn mặt…" | Thêm: không bàn tay, cánh tay hay bộ phận cơ thể nào, kể cả thoáng qua ở mép khung; người duyệt xem từng giây. Video H3 ngày 01.11 có một bàn tay thả rèm |
| §7.5 checklist (6) | "màu ngả phim, pastel ấm, vùng tối được nâng" | **Màu thật như mắt nhìn**: cân bằng trắng đúng, độ bão hòa và tương phản tự nhiên, vùng tối sạch, không ngả cam, không bạc màu. Chủ sản phẩm 01.11: "mình muốn màu sắc thật, cảm giác sống động chứ không phải giống như đang có một filter" |
| §7.6 bước 3 và script `nby-media.sh` (PR #68) | Script "chỉnh màu mềm": `eq=contrast=0.94:saturation=0.9:gamma=1.04`, `curves` nâng vùng tối, `colorbalance` ngả ấm | **Bỏ bước chỉnh màu mặc định**; chỉ giữ cắt, lặp, đổi kích thước và chuyển mã. Nếu cần sửa một clip cụ thể thì dùng tùy chọn riêng, có ghi lý do. Phải sửa trong #68 trước khi merge |
| §3.2 Cảnh | "Video AI … gần như tĩnh" | Đổi thành "máy đứng yên, cảnh sống động": chuyển động của gió, mưa, nước, ánh sáng thấy rõ và liên tục, nhưng không bão, không giật (chủ sản phẩm 01.11). Đồng thời sửa §0 ("gần như tĩnh") và §7.5 (3), (4) theo cùng ý. Thêm thẻ cảnh `goc_nha` / `thien_nhien`. Thư viện khởi đầu ≥ 14 clip, trong đó ≥ 8 clip góc nhà. |
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
- Chủ sản phẩm chọn làm lại 3 video bằng 60 credit còn lại: hiên mưa (H2), góc đọc có mèo (H3), bếp sáng (H1). Cả 3 đã xong (8 giây, khung đầu = khung cuối, prompt video thêm `true-to-life natural colors, no color grading, no film look`). Khung giữa của cả 3 giữ đúng bố cục, màu thật, không vật mới. Hơi trà ở bếp giờ mỏng.
- Gói Flow đã hết credit tới 21.11. Sân gạch hoa giấy (H6) mới có ảnh màu thật, video vẫn là bản màu cũ.

**Góp ý của chủ sản phẩm sau khi xem 3 video làm lại (01.11):**

- Góc đọc có mèo: "kì quá, tự dưng lại có cái tay thả rèm". Có bàn tay người trong cảnh nên **loại** (vi phạm NBY-AI-AC07 và §7.5 (2)).
- Hai video còn lại: "thiếu sự sống động của những hình ảnh xung quanh, kiểu có gió thì phải lay động, còn mưa thì lá phải như nào".
- Nguyên nhân: prompt video xin chuyển động "rất nhỏ, gần như không thấy" theo PRD "gần như tĩnh"; prompt H3 tả rèm "thở" mà không nói nguồn chuyển động.
- Đã sửa: khung video mới và từ vựng chuyển động ở [thư viện prompt](../operations/nby-scene-prompt-library.md) §3, ba prompt H1, H2, H3 viết sẵn ở §5, luật "không bàn tay" ở §6 và §7. Đề xuất sửa PRD §3.2, §0, §7.5 (2)–(4) ở §3.

Điều kiện xong của giai đoạn 1 (≥ 4 clip đạt §7.5): **chưa có clip nào đạt.** Gói Flow hết credit tới 21.11, nên chưa chạy được prompt mới. Chủ sản phẩm chọn: chờ 21.11, hay làm qua Vertex (D24).

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

**Grok Imagine (xAI), kiểm ngày 01.11 theo câu hỏi của chủ sản phẩm.** Nguồn chính: điều khoản Consumer của xAI, "Last Updated: October 27, 2026", https://x.ai/legal/terms-of-service (công ty nay ghi tên "SpaceXSI").

- Người dùng giữ quyền sở hữu đầu vào và đầu ra (§4).
- Khi dùng đầu ra phải "attribute your generation of the Output to the Service" theo Brand Guidelines. Ghi công này đặt được trong tấm ⓘ (PRD §8.6).
- Người dùng cấp cho xAI quyền "irrevocable, perpetual, transferable, sublicensable, royalty-free, and worldwide" với nội dung gửi lên: được dùng, sửa, công bố, làm tác phẩm phái sinh "for any purpose". Prompt và ảnh khung đầu của Lá Lành không có dữ liệu cá nhân, nhưng cảnh của thư viện có thể bị xAI dùng lại.
- Không có bồi thường IP. Ngược lại, người dùng phải bồi thường cho xAI (§11).
- Watermark: chưa đọc được nguồn chính. Các nguồn thứ cấp mâu thuẫn nhau (có dấu Grok, có thể không gỡ được).
- Kết luận: Grok dùng được **để thử** nếu chủ sản phẩm đã có tài khoản. Không đề xuất cho clip phát hành, vì giấy phép rộng cho xAI, không có bồi thường và chưa rõ watermark. D24 không đổi.

**Thử Grok Imagine (01.11, tài khoản Grok của chủ sản phẩm, qua Chrome của chủ sản phẩm).**

- Một video hiên mưa (H2), text-to-video, 6 giây, 480p, khung dọc. Màu thật hơn bản Flow; không thấy watermark trên khung hình; không có tay người.
- Chủ sản phẩm xem: "nhìn vẫn giả và mắc lỗi như cũ"; cụ thể: "lá cây bị mưa mà không động, giọt mưa thì chỉ tập trung một số chỗ" (mưa chỉ thành dòng ở mép mái, không rơi khắp khung).
- Lần thử thứ hai (cận cảnh lá là chủ thể, mưa rơi khắp khung, mỗi lá nhún rồi bật lại) không chạy được: gói miễn phí hết lượt; 720p và lượt tiếp theo đòi gói trả phí. Không mua gì.
- Nhận định: cả Veo và Grok cùng yếu ở đúng chỗ chủ sản phẩm cần, là chuyển động vật lý nhỏ và dày (mưa đập lá, lá nhún). Có thể đây là giới hạn của video AI hiện tại, không phải của prompt. Phương án thay thế: **video quay thật** (kho có license, hoặc tự quay bằng điện thoại đặt cố định). PRD §8.4 vốn cho phép "tự quay"; clip quay thật không cần nhãn "Cảnh tạo bằng AI" nhưng vẫn qua checklist §7.5 và sổ đăng ký (§8.3).

### So sánh Google Flow và Grok Imagine (01.11)

Chủ sản phẩm nâng cấp tài khoản Grok (tự trả phí, ngoài Lá Lành) và yêu cầu so sánh. Claude chạy 3 cảnh trên Grok bằng prompt "cảnh sống động" (thư viện prompt §3), text-to-video, 720p, 6 giây, 9:16.

**Cách đo chuyển động.** Lấy một khung mỗi 0,25 giây, thu nhỏ còn 180×320, so từng điểm ảnh với khung trước. Hai chỉ số:
- *Độ thay đổi trung bình*: chênh lệch màu trung bình mỗi điểm ảnh, thang 0–255.
- *% điểm ảnh chuyển động*: phần điểm ảnh đổi hơn 6 đơn vị.

Hai chỉ số chỉ đo **lượng** chuyển động, không đo chuyển động có **thật** hay không. Người duyệt vẫn phải xem.

| Cảnh | Công cụ, prompt | Độ phân giải, độ dài | Độ thay đổi TB | % điểm ảnh chuyển động | Nhận xét |
|---|---|---|---|---|---|
| Hiên mưa | Flow Veo 3.1 Fast, prompt màu thật (cũ, ít chuyển động) | 720×1280, 8 giây | 1,60 | 4,3% | Các khung gần như giống hệt nhau. Chủ sản phẩm: lá không động |
| Hiên mưa | Grok, prompt toàn cảnh | 416×752, 6 giây | 4,10 | 12,3% | Mưa chỉ thành dòng ở mép mái. Chủ sản phẩm: "vẫn giả" |
| Hiên mưa cận lá | Grok, prompt sống động | 720×1280, 6 giây | 9,23 | 27,7% | Mưa rơi khắp khung, lá đổi vị trí giữa các khung, vũng nước gợn |
| Bếp sáng | Flow Veo 3.1 Fast, prompt màu thật (cũ) | 720×1280, 8 giây | 1,47 | 4,5% | Gần như đứng im. Chủ sản phẩm: thiếu sống động |
| Bếp sáng | Grok, prompt sống động | 720×1280, 6 giây | 6,68 | 22,0% | Hơi trà bốc, bóng lá trên bàn đổi; cây ngoài cửa lay ít |
| Góc đọc có mèo | Flow Veo 3.1 Fast, prompt màu thật (cũ) | 720×1280, 8 giây | 4,56 | 14,8% | Có **bàn tay** thả rèm, nên bị loại; phần lớn chuyển động là do tay và rèm |
| Góc đọc có mèo | Grok, prompt sống động | 720×1280, 6 giây | 6,84 | 19,7% | Rèm tự bay phồng rõ, bóng lá chạy trên sàn, mèo ngủ yên, không có tay |

**Đọc kết quả:**
- Grok dùng prompt mới, còn Flow dùng prompt cũ. So sánh này vì thế **chưa công bằng** về prompt. Flow cần chạy lại prompt mới sau 21.11 thì mới kết luận được về công cụ.
- Dù vậy, Grok với prompt mới cho lượng chuyển động gấp khoảng 4–6 lần ở cảnh mưa và bếp, và không lỗi tay người trong 3 clip.
- Trên các khung đã xem, không thấy watermark của Grok; chữ "HD" là giao diện của trang. Flow có dấu ✦ bắt buộc ở Việt Nam.
- Màu: cả hai đều ra màu thật khi dùng khung §2.
- Điều khoản: Grok vẫn như trên (giấy phép rộng cho xAI, không bồi thường, phải ghi công). Flow (gói cá nhân) không có bồi thường. Chỉ Vertex có bồi thường.
- Chủ sản phẩm cần xem 3 clip Grok để chấm cảm giác "thật". Số liệu không thay được mắt người.

**Vòng 2 trên Grok theo góp ý của chủ sản phẩm (01.11):**

- Góp ý: mèo "vẩy nhẹ đuôi một cái"; mưa "hơi kỳ vì có cái chậu cây lá to, mà màu bị đậm tối"; hơi trà "nhìn hơi bất thường, trắng quá"; và nhận xét chung "thiếu chú ý tới tiểu tiết, các action nhìn khá đều đều trong khi thực tế thì có lẽ không như vậy".
- Góc đọc có mèo: đuôi vẫy một lần ở giây 2,8–3,3 rồi cuộn lại; mèo ngủ yên, rèm tự bay.
- Hiên mưa: cây nhỏ, ánh sáng sáng hơn, prompt chuyển động không đều. Chuyển động giảm còn 4,7% điểm ảnh, độ lên xuống (hệ số biến thiên giữa các khung) 0,17. Có một chiếc lá xanh tự rơi xuống bàn, không có trong prompt.
- Bếp sáng: hơi trà mỏng, trong, lúc có lúc tan; gió từng cơn. Chuyển động 10,2%, độ lên xuống 0,26.
- Bài học đã chép vào [thư viện prompt](../operations/nby-scene-prompt-library.md) §3: chuyển động không đều và bảng chi tiết nhỏ.
- Chủ sản phẩm chỉ ra: "cái lá rơi sao mà bật lên bàn được". Soi từng 0,2 giây: lá rời cây chanh ở giây 1,0, chạm sàn ở 1,4, rồi trôi ngang và bật ngược lên mặt bàn ở 1,6–2,4. Claude đã bỏ sót vì chỉ xem 6 khung cách 1 giây. Quy trình duyệt nay soi từng 0,2 giây (thư viện prompt §1 bước 3).
- Làm lại cảnh mưa (mưa vừa, "mọi thứ dính nguyên chỗ"): 30 khung không có vật rơi; chuyển động 8,4% điểm ảnh, nhưng đều (hệ số biến thiên 0,07). Bố cục lạ: hiên như tấm sàn nổi, vườn hiện cả trên lẫn dưới. Chưa đạt.
- Thử lại theo yêu cầu của chủ sản phẩm, tả rõ bố cục "nhìn từ trong nhà ra hiên" (máy đặt thấp trong nhà, khung cửa gỗ hai bên, sàn gạch nối liền ra hiên, mép mái phía trên, vườn sau một bậc). Kết quả: bố cục đúng; 30 khung (mỗi 0,2 giây) không có vật rơi hay vật đổi chỗ. Nhưng gần như đứng im: 2,8% điểm ảnh chuyển động; so ba khung giây 1, 3, 5 thì lá chuối và chậu cây gần như trùng khít, chỉ có vệt mưa và giọt từ mái. Có hai lớp mái chồng nhau (mái nhà và mái hiên) nhìn hơi rối. Chưa đạt.
- Chủ sản phẩm xem bản "nhìn từ trong nhà": "bố cục ổn hơn rồi". Giữ bố cục này.
- Lần 5: giữ bố cục, đặt máy ngay ngưỡng cửa để khung cửa chỉ là viền mỏng, chỉ một lớp mái, vườn chuối chiếm phần lớn khung. Kết quả: 30 khung (mỗi 0,2 giây) không có vật rơi hay đổi chỗ; chuyển động tăng từ 2,8% lên 7,2% điểm ảnh; lá chuối đổi góc rõ giữa giây 1, 3 và 5. Mưa vẫn khá đều (hệ số biến thiên 0,08). **Chủ sản phẩm duyệt: "Mình đã xem clip mưa mới, đạt rồi."** Prompt lưu làm mẫu chuẩn ở [thư viện prompt](../operations/nby-scene-prompt-library.md) §4a.
- Nhận định sau bốn lần thử đầu: sửa được lỗi này thì lỗi khác xuất hiện (lá không động → lá bay ngược → sàn nổi → đứng im). Lần 5 là bản đầu tiên không có lỗi đã biết, và đã được duyệt. D29 (quay thật) không còn cần cho cảnh mưa; giữ làm phương án dự phòng.

**Tình trạng giai đoạn 1 (01.11, cuối ngày): XONG, 4/4 clip đạt** (đều làm trên Grok Imagine; prompt lưu nguyên văn ở thư viện prompt §4a).

| Cảnh | Clip | Tình trạng |
|---|---|---|
| H2 hiên mưa | Grok, lần 5 | **Đạt** (chủ sản phẩm duyệt) |
| H3 góc đọc có mèo | Grok, vòng 2, đuôi vẫy một lần | **Đạt** (chủ sản phẩm duyệt) |
| H1 bếp sáng | Grok, vòng 2, hơi trà mỏng | **Đạt** (chủ sản phẩm duyệt) |
| H6 sân gạch hoa giấy | Grok, lần 2 (hoa giấy trên tường xa) | **Đạt** (chủ sản phẩm duyệt) |

**H6 sân gạch hoa giấy trên Grok (01.11), làm theo mẫu §4a:**

- Lần 1 (giàn hoa giấy ngay trên đầu máy): soi từng 0,2 giây thấy vài cánh hoa rơi ở giây 0,9–1,7 rồi **biến mất giữa không trung** ở giây 1,9, dù prompt cấm vật rơi. Loại.
- Lần 2 (hoa giấy mọc trên bức tường xa, "flowers firmly attached", cấm vật "appears or disappears"): soi 30 khung và phóng to vùng tường mỗi 0,5 giây, không có cánh hoa rơi hay vật đổi chỗ. Chuyển động 7,1% điểm ảnh, hệ số biến thiên 0,22 (gió từng cơn). **Chủ sản phẩm duyệt.**
- Bài học: vật dễ rụng (hoa giấy, lá khô) ở gần máy hay bị AI cho rơi. Đặt chúng ở xa và ghi rõ "firmly attached".

**Lưu ý cho giai đoạn 2 trở đi:** 4 clip đạt đều làm trên Grok, nên chịu điều khoản của xAI (giấy phép rộng cho xAI, phải ghi công, không bồi thường). Dùng để thử với người dùng ở giai đoạn 2 thì được. Đưa vào app (giai đoạn 4) vẫn cần chủ sản phẩm chốt D24. Grok chưa thấy watermark trên khung hình, nhưng chưa kiểm metadata nguồn gốc (C2PA, SynthID-tương đương) trong file.

## 7. Quyết định cần chủ sản phẩm

| ID | Câu hỏi | Đề xuất | Trạng thái |
|---|---|---|---|
| D23 | Chủ thể của thư viện | "Góc nhà bình yên" là chính (≥ 8/14 clip đầu), thiên nhiên là phụ | **Hướng đã chọn** 01.11 ("tôi thấy đẹp đấy"); tỷ lệ chờ duyệt |
| D29 | Nguồn cảnh: AI hay quay thật | Thử song song một bộ nhỏ quay thật (3–4 clip mưa, gió) để so với AI trước khi chốt; D8 ("video AI") có thể đổi thành "video thật là chính, AI là phụ" | Chờ chủ sản phẩm |
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
