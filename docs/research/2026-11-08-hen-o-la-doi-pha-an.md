# Hẹn ở Lá · Đội đôi phá án (08/11/2026)

Ý owner (08/11/2026):
- Hai người đang tìm hiểu nhau thành **một đội**.
- Cùng nhau vượt thử thách và **cùng về đích**.
- Thử thách dùng lại game phá án đã định nghĩa (vụ cà phê) và **Sĩ số +1**, đi theo level.
- Hai mode: **hài** hoặc **kinh dị**.
- Chưa làm tin nhắn; dùng **giấy note**.

Tài liệu này là thiết kế, chưa phải code. Nó nối với bản thử `prototype/hen-o-la` (5 màn) và các tài liệu vụ cà phê (05–09) ở PR #104, kèm phản hồi format vòng 2 của Codex ngày 28/10.

## 1. Bằng chứng: điều gì làm hai người lạ thấy gần nhau hơn

Hai nhánh nghiên cứu chạy song song, đọc nguồn gốc khi truy cập được. Mức tin cậy được ghi rõ.

| Điều | Bằng chứng | Độ tin | Dùng thế nào |
|---|---|---|---|
| Hỏi đáp tự bộc lộ, sâu dần | Aron 1997 (bộ 36 câu); Sprecher 2021 làm lại; Kardas, Kumar & Epley 2021 (12 thí nghiệm, hơn 1.800 người): người lạ tưởng nói chuyện sâu sẽ ngượng hơn thực tế | **Mạnh nhất**, dù phần lớn do cùng nhóm tác giả | Giữa các level, mỗi người có một câu hỏi tuỳ chọn, sâu dần qua từng level, luôn bỏ qua được |
| Hợp tác, mỗi người làm được việc người kia không làm được | Roseth 2008 (gộp 148 nghiên cứu): mục tiêu hợp tác cho quan hệ tốt hơn. Depping & Mandryk 2017: trong game giải đố hai người, hợp tác và phụ thuộc lệch nhau đều tăng tin tưởng. Greitemeyer & Cox 2013 | Phân tích gộp mạnh; nghiên cứu game nhỏ, chưa ai làm lại | Mỗi người giữ manh mối hoặc khả năng riêng |
| Cười cùng nhau | Fraley & Aron 2004 (96 người lạ cùng giới): trải nghiệm hài chung tăng gần gũi. Kurtz & Algoe 2015: cười *cùng nhau* dự đoán chất lượng quan hệ | Nghiên cứu đơn, khá nhất quán | Mode hài có bằng chứng tốt hơn mode kinh dị |
| Hoạt động mới lạ, hồi hộp | Aron 2000 với các cặp đôi. Lewandowski & Aron 2004 với người lạ: hoạt động hồi hộp tăng hấp dẫn, **chỉ mới lạ thôi thì không** | Nghiên cứu đơn | Level cần có nhịp hồi hộp, không chỉ là đố mẹo |
| Sợ thì dễ thích nhau ("cây cầu treo") | Dutton & Aron 1974 bị Kenrick 1979 làm lại **thất bại**. Phân tích gộp Foster 1998: có hiệu ứng nhưng mất khi người ta biết rõ mình hồi hộp vì đâu. Meston & Frohlich 2003: chỉ có tác dụng khi không đi cùng người yêu | **Yếu, dễ vỡ** | Không quảng bá kiểu "sợ cùng nhau là yêu". Kinh dị chỉ là một màu chơi |
| Kinh dị khi chơi đôi | Nghiên cứu co-op Dark Pictures (HICSS 2024): chơi đôi khó chịu hơn chơi một mình, vì còn lo cho bạn chơi | Một nghiên cứu | Kinh dị nhẹ hơn game solo, mặc định mức thấp |
| Thất bại chung | Worchel 1977: hợp tác mà thất bại có thể giảm thiện cảm. Hudson & Cairns 2016: thua làm giảm cảm giác "cùng đội". Allen 2015: lỗi bị đổ lên người có bước quyết định | Nghiên cứu đơn | Cho thắng sớm, thất bại nhẹ, không bảng điểm cá nhân, không chỉ ra ai làm sai |

Các mẫu thiết kế game, lấy từ phát biểu của nhà làm game:
- **Keep Talking and Nobody Explodes:** một người thấy quả bom, người kia cầm sách hướng dẫn. Nói chuyện chính là câu đố.
- **We Were Here:** hai người ở hai phòng, chỉ liên lạc qua bộ đàm.
- **Portal 2 co-op:** Valve loại mọi câu đố một người giải được, và thêm nút chỉ chỗ, đếm 3-2-1, cử chỉ.
- **Game của Hazelight (It Takes Two):** viết cho hai người từ đầu; mỗi người một khả năng khác, đổi theo màn.
- **Return of the Obra Dinn, The Case of the Golden Idol:** kiểm lời giải theo cụm để không đoán mò được.
- **Frictional (Amnesia):** sợ đến từ khoảng trống, từ thứ không nhìn thấy, không từ hù dọa bất ngờ.
- **Lethal Company:** sợ hãi khi chơi chung hay chuyển thành tiếng cười.
- **Moving Out:** chế độ hỗ trợ không phạt người dùng.
- **Công cụ an toàn trong nhập vai:** X-Card, Lines & Veils, Script Change.

Nguồn đầy đủ ở mục 9.

## 2. Đội đôi: lập đội và cùng về đích

**Lập đội**, giữ hai cách ghép của owner:
- **Thấy rồi muốn:** ở Màn 1, hai người cùng vẫy tay mời nhau thì thành đội. Phải cả hai cùng mời.
- **Tới giờ hệ thống ghép:** ai chưa có đội thì được xếp cặp, như xoay bàn.

**Cùng về đích:**
- Lời giải là **một câu điền chỗ trống**. **Mỗi người chỉ giữ một nửa số mảnh chữ**, nên không ai nộp một mình được.
- Nộp cần **cả hai bấm "Chốt"**. Một người bấm thì người kia thấy "đang đợi bạn".
- Theo phản hồi của Codex, mỗi pha chứng cứ chỉ có **một lượt nộp chính thức**. Sai thì nhận một câu chung, không chỉ ô nào sai, và vẫn điều tra tiếp.

**Giữa các đội trong cùng một buổi:**
- Không có bảng xếp hạng.
- Có một **mục tiêu chung cả quán**: mỗi đội về đích thắp một ngọn đèn trên mái. Khi đèn sáng đủ, cả quán xem phần tái hiện vụ án cùng nhau.
- Đây là "mục tiêu chung lớn hơn", thay cho đua nhau.

## 3. Thang level

Mỗi level dài 8–15 phút. Hai người **đổi vai sau mỗi level**, để không ai luôn là người chỉ huy.

| Level | Nội dung (dùng lại những gì đã có) | Phụ thuộc lẫn nhau | Thời lượng |
|---|---|---|---|
| L0 · Phá băng | Ghép nửa lá tarot (đã có trong bản thử) | Mỗi người giữ một nửa | 2 phút |
| L1 · Sĩ số +1 | Ảnh lớp có một người thừa: P1, P2 của lab 14 | A cầm máy ảnh, B cầm sổ điểm danh và máy quét. Phải đọc cho nhau nghe | 5–8 phút, thắng sớm |
| L2 · Sĩ số +1 khó | Ảnh qua gương (P4), cửa thoát hiểm một chiều (R4) | Công tắc giữ của lab 14: một người đứng giữ, người kia mở nguồn bị khóa | 8–10 phút |
| L3 · Vụ cà phê | Bốn chứng cứ của tài liệu 05/06: ghép ảnh T0, sắp ba khung T1, sổ mượn dây X, góc cửa | A mở ảnh và sổ mượn, B mở chuỗi khung và góc cửa. Góc cửa cần một người giữ đèn hoặc công tắc | 12–15 phút |
| L4+ | Vụ mới, viết sau | Mỗi level một khả năng mới (theo cách của Hazelight) | Sau |

**Vụ cà phê khi chơi đôi:**
- Lời giải là **cách gây án**: vật, hành động, mốc thời gian. Ví dụ: "dây X mắc qua quai cốc, bị kéo về phía cửa lúc T1". Không hỏi danh tính, theo phản hồi của Codex.
- Danh tính Minh chỉ lộ ở phần tái hiện cuối.
- **Vai hung thủ kín kiểu Ma Sói không dùng khi chơi đôi**, vì hai người cùng một đội. Để dành cho chế độ nhóm sau này.

**Sĩ số +1** giữ hướng S2 mà Codex chọn: sáu bóng là hồ sơ hư cấu, không ai đóng. Không bao giờ chọn một người thật trong buổi là "người thừa".

## 4. Hai mode trên cùng một câu đố

Câu đố, chứng cứ và đáp án giữ nguyên; chỉ đổi màu chơi. Vì vậy chỉ cần kiểm tính duy nhất của lời giải một lần.

| Thành phần | Hài | Kinh dị (nhẹ) |
|---|---|---|
| Sĩ số +1: bóng thừa | Có kẻ lạ chen vào ảnh lớp tạo dáng | Một bóng mờ đứng sau hàng cuối. Đèn tối dần chậm, không nhấp nháy |
| Vụ cà phê: tiếng nhạc lạ | Quân tập hát sinh nhật lạc tông cả buổi | Tiếng hát rền rĩ từ khu máy in. Cuối vụ lộ ra là bản nhạc sinh nhật phát chậm: căng thẳng biến thành tiếng cười |
| Ánh sáng | Chiều ấm | Đêm, đèn pin. Hai người đứng xa nhau quá 2 ô thì đèn pin tối dần, phải đi sát nhau |
| Khi sai hay ngã | Trượt chân, đổ cà phê, cả hai cùng cười | Đèn tắt một nhịp rồi về phòng an toàn |
| Kết level | Ảnh chụp tạo dáng ngớ ngẩn | Lộ ra con mèo đen là thủ phạm của tiếng động |

**Luật của mode kinh dị:**
- Mỗi level kết thúc bằng một **cú lộ hài** và một phòng an toàn.
- Dựa vào thứ không nhìn thấy, không hù dọa bất ngờ.
- Không máu me, không nhấp nháy. Âm thanh tắt mặc định.

## 5. An toàn: ai cũng thoát được, không ai phải giải thích

- **Mức gan:** mỗi người chọn trong thư mời. Hai người vào cùng đội thì **lấy mức nhẹ hơn** (theo Lines & Veils).
- **Nút "Mình sợ quá" / "Bỏ qua cảnh này"** luôn hiện:
  - Bấm vào thì cả hai cùng bỏ qua cảnh đó, hoặc quán sáng đèn lên.
  - **Người kia không biết ai bấm** (theo X-Card).
- Báo trước nội dung ở đầu mỗi level. Có chế độ **Thư thả**: thêm thời gian, bỏ qua level không bị phạt (theo Moving Out).
- Mode kinh dị bắt đầu ở mức thấp nhất.

## 6. Nói chuyện không cần tin nhắn

- **Bong bóng lời nói** (≤ 40 ký tự, như bản thử).
- **Cử chỉ nhanh:** chỉ vào đây, 3-2-1, vẫy tay, đập tay, "đợi mình". Theo cách Portal 2 giải chuyện giải thích vị trí quá lâu.
- **Giấy note:**
  - Dán vào thế giới, tối đa 60 ký tự.
  - Đây là cách truyền manh mối giữa hai nửa thông tin: A đọc ảnh rồi dán note "dây đi qua quai cốc" lên bảng cho B.
  - Cuối buổi thành **sổ note** để giữ lại.
  - Không có trả lời qua lại, nên không thành chat.

## 7. Nghỉ giữa level: chỗ để tìm hiểu nhau

Sau mỗi level là một **góc nghỉ không tính giờ**: ngồi bên lò sưởi, hoặc bàn cạnh cửa sổ ở mode hài.
1. Mỗi người có **một câu hỏi tuỳ chọn** cho người kia, sâu dần theo level, luôn bỏ qua được. Ví dụ:
   - L1: "Món ăn làm bạn nhớ nhà?"
   - L3: "Điều gì gần đây làm bạn thấy được hiểu?"
2. Một **trận phụ 1–2 phút cho vui**, như các minigame trong It Takes Two.
3. Mỗi người bấm kín **"Đi tiếp cùng nhau?"**:
   - Cả hai đồng ý thì sang level sau cùng đội.
   - Nếu không, cả hai quay lại quán để ghép đội mới. Không ai biết ai đã chọn không. Màn hình chỉ báo "lượt xoay mới".

Lựa chọn "đi tiếp cùng nhau" là một tín hiệu đồng ý hai chiều nhẹ nhàng, ngay trong lúc chơi. Màn 4 Thả đèn vẫn là nơi chốt cuối.

## 8. Ghép vào buổi "Hẹn ở Lá"

| Màn hiện tại | Sau khi có đội đôi |
|---|---|
| 1 · Tự do | Giữ nguyên, thêm vẫy tay mời lập đội |
| 2 · Xoay bàn | Thành **Thử thách đôi**: hai lượt L1 ngắn với hai đội khác nhau (hệ thống ghép), rồi các đội tự chọn đi tiếp L2–L3 |
| 3 · Thư giữa giờ | Thành **dán note**, có lẫn note truyện của quán |
| 4 · Thả đèn | Giữ nguyên, có thêm đèn chung của cả quán |
| 5 · Ly cuối | Có thêm cảnh **tái hiện vụ án** cho cả quán, rồi ly cuối |

**Kế hoạch dựng bản thử** (chạy trên máy, khách hư cấu làm đồng đội):
1. Lập đội, nút "Đi tiếp cùng nhau?", cử chỉ nhanh và giấy note.
2. L1 Sĩ số +1 bản đôi, chia thông tin lệch nhau, NPC làm đồng đội biết đọc lại manh mối.
3. Hai màu hài/kinh dị cho L1, kèm mức gan và nút "Mình sợ quá".
4. L3 vụ cà phê để sau, khi hình chứng cứ đã duyệt (tài liệu 07–09).

**Còn mở:**
- Chế độ nhóm có hung thủ kín kiểu Ma Sói: để sau, theo phản hồi của Codex.
- Ghép đội lại khi có người từ chối mà không làm ai thấy bị bỏ rơi: cần chơi thử.
- Chơi thật với người thật online thì cần tài khoản và lưu tiến độ giữa các level. Bản thử vẫn chạy trên máy.

## 9. Nguồn

Khoa học:
- [Aron et al. 2000](https://pubmed.ncbi.nlm.nih.gov/10707334/)
- [Lewandowski & Aron 2004](https://sbp-journal.com/index.php/sbp/article/view/1335)
- [Dutton & Aron 1974](https://pubmed.ncbi.nlm.nih.gov/4455773/)
- [FORRT replication atlas](https://forrt.org/flora-replication-atlas/doi/10.1037/h0037031/)
- [Meston & Frohlich 2003](https://doi.org/10.1023/a:1026037527455)
- [Pettigrew & Tropp 2006](https://pubmed.ncbi.nlm.nih.gov/16737372/)
- [Paluck et al. 2019](https://www.cambridge.org/core/journals/behavioural-public-policy/article/contact-hypothesis-reevaluated/142C913E7FA9E121277B29E994124EC5/core-reader)
- [Greitemeyer & Cox 2013](https://zendy.io/title/10.1002/ejsp.1940)
- [Depping & Mandryk 2017](https://bibtex.github.io/CHI-PLAY-2017-DeppingM.html)
- [Kurtz & Algoe 2015](https://pubmed.ncbi.nlm.nih.gov/26957946/)
- [Treger et al. 2013](https://zendy.io/title/10.1002/ejsp.1962)
- [McFarland et al. 2013](https://sites.socsci.uci.edu/~lpearl/courses/readings/McFarlandEyAl2013_SocialBonding.pdf)
- [Sprecher 2021](https://oa.mg/work/10.1177/0265407521996055)
- [Kardas et al. 2021](https://www.apa.org/news/press/releases/2021/09/deep-conversations-strangers)
- [Worchel et al. 1977](https://prejudicereduction.princeton.edu/publications/intergroup-cooperation-and-intergroup-attraction-effect-previous-interaction-and)
- [Hudson & Cairns 2016](https://dblp.org/rec/journals/chb/HudsonC16.html)
- [Procházka et al. 2022](https://www.psychologicalscience.org/journals/psychological-science/09567976211040745/)

Thiết kế game:
- [Keep Talking (GDC)](https://gdcvault.com/play/1023113/Designing-Asymmetric-Gameplay-For-Keep)
- [We Were Here](https://www.gamedeveloper.com/disciplines/road-to-the-igf-total-mayhem-games-i-we-were-here-i-)
- [Portal 2 co-op](https://www.gamedeveloper.com/design/synthesizing-i-portal-2-i-)
- [Josef Fares](https://www.theringer.com/2021/4/22/22396763/josef-fares-it-takes-two-interview-co-op-gaming)
- [Lovers in a Dangerous Spacetime](https://gamedeveloper.com/design/co-op-communication-in-i-lovers-in-a-dangerous-spacetime-i-)
- [Frictional: 9 bài học về kinh dị](https://frictionalgames.blogspot.com/2019/10/9-years-9-lessons-on-horror.html)
- [Kinh dị co-op (HICSS 2024)](https://aisel.aisnet.org/hicss-57/dsm/games_and_gaming/6)
- [Lethal Company](https://pcgamer.com/lethal-companys-co-op-horror-comedy-is-like-phasmophobia-but-immediately-more-chaotic-and-deadly)
- [Moving Out, hỗ trợ](https://caniplaythat.com/2023/06/05/moving-out-2-accessibility-and-assist-modes-detailed/)
- [X-Card](https://docs.google.com/document/d/1SB0jsx34bWHZWbnNIVVuMjhDkrdFGo1_hSC2BWPlI3A)
- [Lines & Veils](https://blog.roll20.net/posts/guest-blog-an-introduction-to-lines-and-veils/)
- [TTRPG Safety Toolkit](https://ttrpgsafetytoolkit.com)
- [Alan Wake 2: giảm mức hù](https://www.videogameschronicle.com/news/alan-wake-2-update-1-15-adds-chapter-select-turns-down-scares/)
- [Golden Idol](https://www.gamasutra.com/design/case-of-the-golden-idol)
- [Obra Dinn](https://en.wikipedia.org/wiki/Return_of_the_Obra_Dinn)
- [Nicholson 2015, khảo sát phòng thoát hiểm](http://scottnicholson.com/pubs/erfacwhite.pdf)
- [36 câu hỏi](https://aru.ac.uk/news/can-36-questions-really-change-your-love-life)
