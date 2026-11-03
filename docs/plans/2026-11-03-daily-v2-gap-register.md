# Daily v2 — sổ lỗ hổng sau rà soát toàn diện

Ngày: 2026-11-03 · Đi kèm: `docs/plans/2026-11-02-daily-v2-content-quality-plan.md`

## Cách rà

Bốn cuộc rà chạy độc lập với nhau, cộng phần rà tay trước đó:

| Mảng | Phạm vi | Mã |
|---|---|---|
| Rà tay | Engine chọn góc C2a (#178) | K-1…K-13 |
| Phương pháp chiêm tinh | `sky_selection.py`, engine transit, so với thực hành phổ biến | AS-1…AS-22 |
| Toàn bộ luồng Daily | Từ engine tới màn hình, US-03/US-21, plan | PL-1…PL-36 |
| Cổng nội dung và thiết kế A/B | C1 (#179), spec cổng, C3, C4, C5 | GT-1…GT-39 |
| Bảo mật và quyền riêng tư | Theo ba cổng của `AGENTS.md` | PV-1…PV-28 |

Mọi số đo đều chạy trên lá số giả lập (giờ sinh ngẫu nhiên, tọa độ Việt Nam, seed cố định). Không
dùng dữ liệu sinh thật. Script và số liệu thô nằm ngoài repo.

Có 138 mục. Sau khi gộp các mục trùng nhau còn khoảng 75 lỗ hổng, sắp theo PR ở mục 2.

## 1. Mười điều làm kế hoạch phải đổi

1. **Người không có giờ sinh chính xác gần như không có note riêng.**
   - Người chỉ có ngày sinh: mỗi cung hoàng đạo có đúng một tình huống cho cả năm (PL-2).
   - Người có giờ gần đúng: cả nhóm đọc cùng một chủ đề mãi mãi (PL-1).
   - Người dùng Jyotish: hôm nào cũng một gợi ý kỹ thuật; 2/30 lá số bị từ chối mỗi ngày (PL-3).
   - Daily v2 hiện chưa có note cho cả ba nhóm (PL-14).
   - Sửa được, vì vị trí Mặt Trời tới Sao Hỏa chỉ lệch ≤0,35° khi giờ sinh sai ±2 giờ (AS-1).
2. **Daily hiện tại hầu như không nói về bầu trời hôm nay.** Phần transit chỉ hiện khoảng 1/10 ngày
   (258/2.700 note), vì gate hay từ chối và lùi về bản chỉ dựa trên lá số gốc. Headline nào cũng là
   một vấn đề (90/90), kể cả hôm góc chiếu thuận (PL-4, PL-5).
3. **Cách xếp hạng chưa theo ý nghĩa.**
   - Sự kiện hiếm bị Mặt Trăng đè (K-3).
   - Hành tinh chậm chạm đúng trong ngày không được đưa lên (K-2).
   - 39–40% số ngày cả ba lựa chọn đều là Mặt Trăng (K-4).
   - Không có tông nền cho ngày nặng (K-1).
   - Một sự kiện trên trời bị tách thành hai thẻ (AS-4).
   - "Mấy ngày này" thực ra kéo dài nhiều tuần (AS-7).
4. **Giờ hiện trên chip thường là giờ giả.**
   - Khoảng 35% lựa chọn hiện 00:00 hoặc 23:30 (AS-5).
   - 42% lựa chọn đứng đầu rơi vào giờ ngủ (K-5).
   - Mặt Trăng chưa có khung giờ thật (AS-6).
5. **Dữ liệu sinh có lỗi gốc.**
   - Người sinh ở miền Bắc từ 1960 đến 13/6/1975 bị lệch một giờ, vì cơ sở dữ liệu múi giờ dùng
     UTC+8. Cung Mọc sai khoảng 15° (AS-9, đã tự kiểm tra lại).
   - Giờ HH:MM nào cũng bị coi là chính xác. Nếu giờ sai ±15 phút thì 25% hành tinh đổi nhà
     (AS-10).
6. **Khoảng ngày của xu hướng bị cắt sai.** 53% xu hướng quay lại trong vòng 270 ngày sau ngày kết
   thúc đã hiện, vì engine không nối các lần đi qua do nghịch hành (AS-2).
7. **C2d không thể vừa lưu lịch sử 30 ngày vừa giữ thời hạn 24 giờ của Daily.** Mã mảnh còn để lộ
   đầu nhà, từ đó suy ra giờ sinh. Cách sửa: chọn biến thể không cần lưu trạng thái, bằng HMAC theo
   người, theo góc và theo chu kỳ trăng (PV-1, PL-17).
8. **A/B chưa làm được như plan.**
   - Domain `experiments` là tính năng "việc nhỏ", không phải công cụ A/B (GT-32, PL-15, PV-3).
   - App chưa có sự kiện đo nào (PL-16).
   - Khoảng 50 người mỗi nhánh chỉ phát hiện được chênh lệch cỡ 27 điểm (GT-33).
   - Đo theo từng người là theo dõi hành vi, thuộc dữ liệu nhạy cảm theo Nghị định 356 (PV-4).
9. **Cổng lớp A bỏ lọt gần hết câu xấu.**
   - 44/48 câu xấu viết thử lọt qua mọi lớp kiểm tra (GT-17).
   - Các luật đã ghi "chặn cứng" mới chỉ được ratchet (GT-1).
   - PR có thể tự nâng baseline (GT-2).
   - Ratchet đếm tổng nên một lỗi mới có thể trốn sau một lần sửa lỗi khác (GT-3).
   - Corpus chỉ phủ 35/≥176 headline của Daily (GT-6).
10. **Thiếu an toàn cho ngày nặng.** Chưa có luật cho câu gây sợ, câu chẩn đoán, câu khủng hoảng, và
    chưa có đường dẫn tới hỗ trợ (GT-23, GT-24, PV-10).

## 2. Sổ lỗ hổng theo PR

Mức: **P1** là thông điệp chính sai hoặc thiếu, hỏng chức năng, hoặc phải sửa trước khi ship PR đó.
**P2** là note yếu đi thấy rõ. **P3** là đánh bóng.

### C1 — sửa tiếp cổng lớp A (#179)

| Mã | Lỗ hổng | Mức | Sửa |
|---|---|---|---|
| GT-1 | A11/A14/A4 vẫn chỉ ratchet (Daily A14=5, Khám phá A11=132) | P1 | Đếm >0 là trượt, bất kể baseline; dọn các lỗi đang có |
| GT-2 | Một PR tự nâng baseline trong diff của chính nó | P1 | CI so với baseline của nhánh đích; chỉ tăng qua file ngoại lệ chủ sản phẩm duyệt |
| GT-3 | Ratchet đếm tổng, lỗi mới trốn sau lỗi đã sửa | P1 | Ratchet theo tập khóa câu vi phạm |
| GT-6, GT-7 | Seed và ngày cố định; corpus Daily nghiêng về ngày có transit | P1 | Lint mọi chuỗi nguồn và mọi mảnh; chạy hằng tuần với seed xoay |
| GT-8 | Bề mặt mới và giọng A/C không được lint | P1 | Thêm `daily_home`/`daily_detail` × `voice_a`/`voice_c`; test mọi trường chữ mới đều qua lint |
| GT-10 | A9, A13, A15, A16 chưa chạy | P1 | Làm A16 (chữ nhà/cung/chủ tinh/góc trong thân bài), A9, A15 |
| GT-14 | Danh sách câu khẳng định quá khứ, tiếng Anh, placeholder còn hẹp; "lúc nãy" thoát A14 | P1 | Mở rộng bằng mẫu đã/vừa/mới + từ chỉ thời gian; regex placeholder |
| GT-4, GT-5 | Cải thiện không được khóa; A6 không đo độ lan | P2 | Ép hạ baseline khi số lỗi giảm; ratchet `readings_flagged` |
| GT-11, GT-15 | Chưa chuẩn hóa NFC, ký tự zero-width; thuật ngữ chỉ khớp đúng chữ | P2 | Chuẩn hóa trước khi lint; thêm từ đồng nghĩa |
| GT-12, GT-13, GT-16, GT-9 | Xuống dòng và câu đệm lách luật; danh sách rào đón; baseline macOS so với Linux; Radar không ghi giọng | P3 | Như báo cáo |

### C2a — chọn góc (#178, mở rộng phạm vi)

| Mã | Lỗ hổng | Mức | Số đo | Sửa |
|---|---|---|---|---|
| AS-1, PL-14 | Giờ gần đúng hoặc không có giờ thì không có yếu tố cá nhân | P1 | 100% nhóm này | Dùng `orb_bounds` cho Mặt Trời…Diêm Vương gốc; Mặt Trăng gốc chỉ khi biết khung giờ, orb rộng hơn; không dùng nhà |
| K-1 | Không có tông nền cho ngày nặng | P1 | 34% số ngày | Trường `tone` suy từ hình học khi tính, không lưu (PV-11) |
| K-2, AS-3 | Hành tinh chậm chạm đúng trong ngày, hoặc yếu tố nhanh kích hoạt một xu hướng đang chạy | P1 | ~19% / 58% số ngày | Đưa lên lựa chọn chính; liên kết `triggers_trend` |
| K-3, AS-14, AS-19 | Sự kiện hiếm thua Mặt Trăng; không phân biệt góc đang tiến hay đang tách; không tính nhiều góc cùng dồn vào một điểm | P1 | Sự kiện hiếm vắng mặt hẳn ở 48% số ngày có nó; ngày sinh nhật vắng 43% | Xếp hạng theo trọng số hành tinh × điểm gốc × độ hiếm; ưu tiên góc đang tiến; cộng điểm khi dồn |
| K-4, PL-22, AS-15 | Cả ba lựa chọn là Mặt Trăng; orb rộng | P2 | 39–40% số ngày | Tối đa 1–2 Mặt Trăng; orb chặt 1° để xếp hạng và làm chip |
| AS-4, PL-19 | Một sự kiện thành hai thẻ; hai chip cùng lĩnh vực | P2 | 23% / 36% số ngày | Gộp thành một yếu tố "góc gốc được kích hoạt"; mỗi lĩnh vực một chip |
| K-5, AS-5, AS-6, PL-21, PL-27 | Giờ giả, giờ ngủ, Mặt Trăng không có khung giờ | P2 | ~35% lựa chọn | `time_kind`; khung vào/ra và đỉnh (orb ≤1°); ưu tiên giờ thức |
| AS-7 | Tầng chỉ theo hành tinh; Sao Hỏa có lúc kéo dài 58 ngày | P2 | Sao Hỏa >14 ngày: 22% | Đặt tầng theo độ dài thật |
| K-7, K-8, AS-18, AS-17, K-11, AS-22 | Trạm, trăng non/tròn, thực, đổi cung, Trăng vô hướng, nghịch hành, sinh nhật | P2 | Đổi cung 12,9%; Trăng vô hướng ≥4 giờ thức 30% | Thêm "sự kiện bầu trời"; ưu tiên sinh nhật và trạm trên điểm gốc |
| K-10 | Mặt Trăng đổi cung giữa ngày nhưng chỉ lấy lúc 12 giờ | P2 | 43% số ngày | Trả về cả hai cung kèm giờ đổi |
| AS-11, AS-12, K-9 | Dự phòng rơi vào điểm mỏng; Nút Bắc đối = Nút Nam hội; góc thế hệ | P3 | 10,9% / 2,5% / 38% | Thứ tự dự phòng mới; đổi nhãn Nút Nam; loại góc ngoài–ngoài |
| AS-13 | Nhãn "chính xác" cả ngày; hai ngưỡng 0,3° và 0,2° | P3 | 67% lựa chọn | Một ngưỡng, có giờ tham chiếu |
| PL-13 | Sky Chapter cũ tính mỗi request, cảnh không theo góc | P3 | | Thay bằng C2a |

### C2b — nhà, chủ tinh, góc với cung Mọc/Thiên Đỉnh

| Mã | Lỗ hổng | Mức | Sửa |
|---|---|---|---|
| K-6 | Không tính góc với cung Mọc (ASC) và Thiên Đỉnh (MC) (43% số ngày có) | P1 | Thêm điểm góc, chỉ khi giờ sinh đủ tin cậy |
| AS-10, AS-21 | Giờ nào cũng coi là chính xác; tọa độ lấy theo tâm tỉnh | P1 | Chỉ dùng nhãn nhà khi nhãn không đổi trong khoảng sai số giờ |
| PL-20 | Chưa định nghĩa nhà nào quyết định lĩnh vực của chip | P2 | Quy tắc: nhà transit đi qua hay nhà của điểm gốc; ghi vào plan |
| AS-20 | Placidus không tính được ở vùng cực | P3 | Đổi hệ nhà khi có nơi sinh nước ngoài |

### HM — nghĩa của nhà (phản hồi owner 03.11.2026; làm trong C2b và C3a)

Một nhà có nhiều nghĩa. Ví dụ của owner: Sao Mộc qua nhà 5 có thể là có con, không phải "hẹn hò mở rộng". Thiết kế mới ở plan mục 1.1.

| Mã | Lỗ hổng | Mức | Cách sửa |
|---|---|---|---|
| HM-1 | Plan bản 927811b gán mỗi nhà một chip cố định (nhà 5 = "Hẹn hò") | P1 | Đã bỏ. Nhà là chùm nghĩa; chủ đề do cặp hành tinh × nhà, lá số gốc và độ dài transit chọn |
| HM-2 | `knowledge.py` `HOUSES[5]` thiếu con cái; `_short_arena` gộp nhà 6+10, 4+12, 7+11 | P1 | Thay bằng bảng chùm nghĩa đủ 12 nhà và bảng hành tinh × nhà (C3a) |
| HM-3 | `daily_personalization.py` `HOUSE_ARENAS` dồn 12 nhà vào 4 nhóm (5 → SELF_CARE, 9 → WORK) | P1 | Bỏ khi C2a/C4 thay Daily cũ; cho tới lúc đó ghi là nợ đã biết |
| HM-4 | Không có luật chặn đoán sự kiện đời người (mang thai, cưới, chia tay, mất việc, bệnh, mất người thân) và giả định hoàn cảnh (độc thân, có con, giới tính) | P1 | Luật chặn cứng mới trong C1/C3a; bốn persona (độc thân; có gia đình và con; đang mong con/hiếm muộn; lớn tuổi) cho cổng lớp C |
| HM-5 | Mang thai và khả năng có con là dữ liệu sức khỏe nhạy cảm | P1 | Không suy ra, không lưu, không hỏi; chỉ nói "chuyện con cái" ở dạng khả năng tích cực |
| HM-6 | Chủ đề đời người có thể đến từ hành tinh nhanh | P2 | Chỉ hành tinh chậm, trong tag "Xu hướng hiện tại" |
| HM-7 | Không rõ giờ sinh: Sao Kim gốc bị gán "Hẹn hò hoặc Đối tác" | P2 | Dùng chùm nghĩa của hành tinh gốc, nói rộng |

| HM-8 | Bản 9423dae lệch sách ở sáu chỗ: tình yêu ở nhà 5 chỉ có nguồn hiện đại; "học trò" không có nguồn; Mặt Trăng "vài giờ" (thật ra khoảng 2 ngày một nhà), Sao Kim "vài ngày" (thật ra vài tuần); chủ tinh hiện đại dùng chọn nghĩa không có nguồn cổ điển; câu mặc định có con; C3a đòi nguồn hiện đại chưa kiểm | P1 | **Đã chốt 03.11.2026** (plan mục 1.1, luật N-1…N-8, A-6…A-8; nghiên cứu `docs/research/2026-11-03-sach-chiem-tinh-nha-va-transit.md`) |
| HM-9 | Hand và Sasportas chưa đối chiếu với sách thật; số câu Phaladeepika lấy từ OCR chưa soát | P2 | Đối chiếu trước khi C3a xong; tới lúc đó nghĩa chỉ có nguồn hiện đại không đứng đầu |
| HM-10 | Câu nhiều cửa dễ thành câu đúng với ai cũng được | P2 | Luật đo câu chung chung trong cổng lớp C |

### C2c — khoảng ngày của xu hướng

| Mã | Lỗ hổng | Mức | Sửa |
|---|---|---|---|
| AS-2 | Cửa sổ dừng ở lần ra khỏi orb đầu tiên, mất các lần đi qua do nghịch hành | P1 | Nối các khoảng hở ngắn hơn một chu kỳ (~400 ngày); trả về mọi lần chạm đúng |
| AS-8, PL-23 | Nút/Chiron đứng đầu 26,7% số ngày; trung vị 6,5 ứng viên; 55% không mang tính cá nhân | P2 | Trọng số hành tinh × góc × điểm gốc; chọn 1–2 tag |
| AS-16 | "Ngày rõ nhất" không phải ngày chạm đúng (19%) | P3 | Trả kèm orb, nhãn "gần nhất" hoặc "chính xác" |

### C2d — chống lặp (đổi thiết kế)

| Mã | Lỗ hổng | Mức | Sửa |
|---|---|---|---|
| PV-1, PL-17, PV-2 | Lưu 30 ngày mâu thuẫn với thời hạn 24 giờ; mã mảnh để lộ giờ sinh | P1 | Không lưu gì: biến thể = HMAC(khóa, hồ sơ, mã góc, số chu kỳ trăng) |
| PL-18, PL-7 | Quỹ mảnh không đủ cho "0 lặp trong 30 ngày"; US-21 đòi 90 ngày | P1 | Tính số biến thể cần cho mỗi loại thẻ từ số lặp đo được (≥10 cho thẻ Mặt Trăng); chốt một cửa sổ |

### C3a — bộ chuẩn và bộ mẫu vàng

| Mã | Lỗ hổng | Mức | Sửa |
|---|---|---|---|
| GT-17, PV-10, GT-24 | Không có luật an toàn; không có đường dẫn hỗ trợ | P1 | Luật hạng A chặn cứng: sức khỏe, chẩn đoán, tai nạn, tiền bạc, pháp lý, "chắc chắn", ngôn ngữ khủng hoảng. Dòng hỗ trợ tĩnh chỉ dùng số đã xác minh (115, 111) |
| GT-23, PL-5 | Không có giọng mềm cho ngày nặng; headline nào cũng là vấn đề | P1 | Tối đa 2 thẻ căng; câu trang chủ không bao giờ chỉ căng; hạn mức thẻ không phải vấn đề |
| GT-21, GT-22 | Câu Barnum (đúng với ai cũng được), câu không kiểm chứng được, "sẽ + kết quả" | P2 | Bốn phép thử độ riêng (mục 3); chỉ nói xu hướng hoặc điều kiện |
| GT-25 | Giọng C không phân biệt trêu và trách | P2 | Trêu tình huống, không trêu con người |
| GT-27, GT-31 | Bộ mẫu vàng quá nhỏ, chỉ một người chấm; luật Q2 chưa chốt | P2 | Kappa ≥0,6; ≥50 mẫu mỗi giọng; điều kiện xong của C3a là chủ sản phẩm duyệt một lần |
| PL-24, PL-25, PL-26, PL-34 | A/C đụng giọng Thẳng/Cà khịa; plan mâu thuẫn chuẩn tiếng Việt dễ hiểu; thiếu vế "vì"; 60 âm tiết tính gì | P2 | Ghi rõ luật nào thắng; thêm một vế "vì" bằng lời thường; ngân sách cho từng phần |

### C3b — nhà máy nội dung

| Mã | Lỗ hổng | Mức | Sửa |
|---|---|---|---|
| GT-18 | Giám khảo chỉ chấm một phần mảnh | P1 | Chấm 100% (~1.100 mảnh) offline |
| GT-19, GT-20 | Tông và lĩnh vực không được đối chiếu với góc; note ghép từ mảnh có thể tự mâu thuẫn | P1 | Gắn tag góc/tông/lĩnh vực/lập trường; luật ghép; lint note đã ghép cho 200+ lá số × 365 ngày |
| GT-28 | Luật nghiệm thu chưa rõ: một note 10 mảnh với 3% mảnh lỗi thì 26% note lỗi | P1 | Lấy mẫu note đã ghép, 0/100 mỗi giọng; định nghĩa "lỗi nghiêm trọng" |
| PV-15 | LLM tạo mảnh rồi đi thẳng qua vòng tự merge | P1 | Lint mảnh (NFC, không URL/số điện thoại/placeholder); manifest; CODEOWNERS; không tự merge; bật qua revision của studio sau khi chủ sản phẩm duyệt |
| GT-26 | Giám khảo cùng họ model với người viết | P2 | Giám khảo khác họ, ghim phiên bản, trích dẫn phải khớp đúng chuỗi |
| GT-29, GT-30 | Người đọc giả lập thay cho người thật; vòng viết lại học cách lách lint | P2 | Người đọc giả lập chỉ để lọc trước; giữ bộ luật ẩn mà vòng viết lại không thấy |
| PV-16 | Dữ liệu sinh thật có thể lọt vào bộ mẫu vàng hoặc giám khảo | P2 | Chỉ dùng persona tổng hợp, CI kiểm tra |
| PL-6, PL-9 | Câu của Lá lặp; note dự phòng cùng headline mỗi ngày, thiếu nhãn "Note tạm thời" | P2 | Đưa vào nhà máy; thay SIGN_COPY/AURA_COPY |

### C4 — API và giao diện

| Mã | Lỗ hổng | Mức | Sửa |
|---|---|---|---|
| PV-5 | Tính lại lựa chọn ở mỗi GET, không giới hạn tần suất | P1 | Tính một lần cho mỗi (snapshot, ngày), lưu trong note đã mã hóa; thêm policy `daily-read` |
| PV-6 | Trường v2 nằm ở cột không mã hóa | P1 | Mọi trường v2 vào envelope; test bảng không có cột mới ở dạng rõ |
| PV-28 | Đường viết lại bằng LLM lúc chạy vẫn nằm cạnh Daily; allowlist có `house` | P2 | Loại Daily v2 khỏi registry viết lại; test |
| PL-8, PL-10, PL-12 | Cảnh mất ở trang chi tiết; không làm mới sau nửa đêm; ngày UTC lúc đang tải | P2 | Sửa cùng UI v2 |
| PL-30, PL-31, PL-32, PL-33 | Lưu note, chia sẻ, lịch sử; ngày triển khai; bộ chọn ngữ cảnh; "việc nhỏ" | P2 | Ghi điều kiện xong cho từng mục |
| PV-13, PV-21, PV-22, PV-23 | Chia sẻ không được mang trường v2; cache sống lâu hơn lệnh xóa; khóa trên thiết bị; log | P2 | Test cho từng mục |
| PL-35, PL-11 | Trợ năng của chip; offline ẩn hết | P3 | |

### C4a (mới) — gán nhánh A/B và đo

| Mã | Lỗ hổng | Mức | Sửa |
|---|---|---|---|
| GT-32, PL-15, PV-3, PV-17, GT-36, PL-28 | Không có công cụ A/B; nhánh không cố định theo người | P1 | Nhánh = HMAC(khóa, "daily-voice-v1", mã hồ sơ ổn định) mod 2; không lưu, không cho client chọn; loại traffic của chủ sản phẩm và QA |
| PL-16, PV-4, PV-25 | Không có sự kiện đo; đo theo người là dữ liệu nhạy cảm | P1 | Chỉ bộ đếm tổng hợp (ngày, nhánh, chỉ số, số lượng); thông báo kèm nút tắt; consent riêng nếu cần |
| GT-33, GT-34, GT-37 | Thiếu cỡ mẫu; chỉ số thưởng cho sự tò mò; hai nhánh khác nhau không chỉ ở giọng | P1 | Đăng ký trước chỉ số và quy tắc dừng; chọn A hay C chủ yếu bằng phép thử với người đọc (mục 3), A/B live chỉ làm rào chắn; đông cứng kho mảnh trong lúc test |

### C5 — tín hiệu từ người đọc

| Mã | Lỗ hổng | Mức | Sửa |
|---|---|---|---|
| PV-7, GT-39 | IDOR; một nhóm khách có thể rút nội dung hàng loạt | P1 | Chỉ nhận cờ cho mảnh đã thực sự hiện trong note của chính người đó; cần nhiều khách đủ ≥7 ngày tuổi; rút bằng danh sách chặn |
| PV-8, GT-38 | Lưu cờ có thể nối ngược về người và về lá số | P1 | Mã mờ, chỉ lưu tổng hợp; khóa HMAC xoay mỗi ngày |
| K-13, GT-35, PV-9, PL-29 | Không đo được "khớp với ngày của mình"; trùng với tính năng cảm nhận đang có | P2 | Dùng lại hit/miss của tính năng cảm nhận; câu hỏi chọn note của mình giữa hai note; làm C5 trước A/B |

### Mới — sửa ngay trên production (độc lập với v2)

| Mã | Lỗ hổng | Mức | Sửa |
|---|---|---|---|
| AS-9 | Sinh ở miền Bắc 1960–13/6/1975 lệch một giờ | P1 cho nhóm này | Chọn offset theo tỉnh và ngày: UTC+7 cho các tỉnh phía Bắc; đánh dấu giai đoạn chưa chắc |
| PL-3 | Jyotish: 2/30 lá số bị từ chối mỗi ngày và ghi log lỗi | P1 | Tìm nguyên nhân, sửa |
| PL-1, PL-2 | Note của người có giờ gần đúng hoặc chỉ có ngày gần như cố định | P1 | Trước mắt xoay nhiều tình huống hơn; giải pháp gốc là AS-1 |
| PL-37 | Không có lựa chọn cho người sinh 00–06h. "Đêm (sau 22h)" được lưu thành 23:00 của ngày đã nhập, nên người sinh 3h sáng bị tính lệch khoảng 20 giờ | P1 | **Owner chốt 03.11.2026:** thêm "Rạng sáng 00–06h" (lưu 03:00), "Đêm" thành 22–24h; không báo người dùng vì đang thử nghiệm. Engine chọn góc coi 03:00 là khung hẹp, còn bản ghi "Đêm" cũ vẫn theo luật rộng (#178) |
| AS-10 | Hỏi "bạn biết giờ sinh từ đâu" và cho chọn theo canh giờ (Tý…Hợi) | P2 | Cần review quyền riêng tư trước, vì đây là trường mới |
| PV-24 | `/metrics` mở công khai | P3 | Trả 404 ở Caddy hoặc yêu cầu token |
| PV-26 | Nhãn persona và mood lưu dạng rõ | P3 | Đưa vào envelope ở lần migration tới |

### Hồ sơ pháp lý và app native

| Mã | Lỗ hổng | Mức | Sửa |
|---|---|---|---|
| PV-18, PV-20 | Lời giải thích quyền riêng tư, xcprivacy, Play Data Safety, bản đồ dữ liệu, xuất dữ liệu | P2 | Cập nhật cùng PR làm phát sinh dữ liệu; thêm kiểm tra vào `verify-privacy.mjs` |
| PV-19 | Hồ sơ chuyển dữ liệu ra nước ngoài và DPIA (hạn khoảng 25–26/11) chưa có dữ liệu v2 | P2 | Bổ sung, hoặc ghi "không lưu theo người" nếu áp dụng PV-1/3/4/8 |
| PV-14, PL-36 | Màn hình khóa, push, widget | P2 | Chỉ chữ chung chung; ẩn nội dung xem trước |
| PV-27 | Apple 4.3(b) và độ tuổi | P3 | Khai 18+; giải thích giá trị riêng khi nộp review |

## 3. Đo "khớp" mà không dựa vào cảm nhận chung chung

Hỏi "thấy đúng mình không?" thì note chung chung vẫn được khoảng 4,3/5 (hiệu ứng Barnum). Bốn
phép thử thay thế:

1. Câu đứng đầu không xuất hiện ở quá 5% của 1.000 lá số trong cùng một ngày.
2. Đưa người đọc 1 note thật và 3 note mồi; họ chọn đúng note của mình ≥60% trong ≥100 lượt.
3. Đổi góc chiếu thì verdict phải đổi.
4. Giám khảo đánh dấu "đúng với ai cũng được" ở ≤10% số mảnh.

## 4. Đã kiểm tra, không có vấn đề

- Năm góc chính khớp thực hành phổ biến.
- Góc chạm đúng gần nửa đêm được tính cho đúng một ngày.
- Giờ đỉnh tính lại lệch ≤1,06 phút so với quét 2 phút một lần.
- Có đủ 3 lựa chọn ở 99,9% số ngày.
- Lựa chọn đứng đầu trùng hôm trước 4,0%.
- Kết quả xác định, chỉ phụ thuộc lá số và ngày.
- Nút thật khớp astro.com.
- Từ chỉ góc khớp loại góc: "hỗ trợ" chỉ dùng cho góc thuận.
- Cùng khách cùng ngày luôn ra cùng note.
- Ranh giới ngày ở server là nửa đêm giờ Việt Nam.
- Service worker không cache API; note chỉ nằm trong bộ nhớ.
- Không có thông báo nào mang chữ của note.
- Bảo mật:
  - prose của Daily được mã hóa AES-GCM;
  - token chia sẻ chỉ lưu dạng hash, có `no-store` và `noindex`;
  - xóa khách thì xóa theo dây chuyền;
  - cổng 18+ nằm ở server.
- Corpus của C1 cho cùng kết quả dưới hai hash seed, chạy khoảng 2 giây.

## 5. Chưa kiểm chứng

- Ratchet có cho cùng số đếm trên Linux CI như trên macOS không.
- Tỷ lệ người dùng thật theo nhóm: giờ chính xác, giờ gần đúng, chỉ ngày sinh, Jyotish. Cần một
  truy vấn tổng hợp.
- Đường dây nóng sức khỏe tinh thần chính thức của Việt Nam. Chỉ 115 và 111 được xác minh.
- Văn bản chính thức của Nghị định 356/2025 (trang vbpl.moj.gov.vn không truy cập được, phải đọc qua
  bản sao), Nghị định 392/2026 sửa đổi, và việc Điều 4.1(l) có bao gồm log tương tác trong app hay
  không. Bản rà này áp dụng cách hiểu an toàn hơn.
- Giao diện chưa được xem trên trình duyệt.

## 6. Nguồn chính

- Astrodienst: orb dự báo (`astro.com/cgi/xa.cgi/faq/fq_sh_fore_e.htm`), kiểu chart
  (`fq_fh_owstyle_e.htm`), Swiss Ephemeris (`astro.com/swisseph/swephprg.htm`).
- Danh sách thư tz, Treindl 2020: `mm.icann.org/pipermail/tz/2020-June/029136.html`.
- Astrotheme: các góc chiếu và nút Mặt Trăng.
- CDC Clear Communication Index (user guide); AHRQ PEMAT-P.
- Kohavi, Tang, Xu — *Trustworthy Online Controlled Experiments*, chương 21.
- arXiv 2404.13076 (giám khảo thiên vị bài của chính mình); arXiv 2306.05685 (thiên lệch của LLM khi
  làm giám khảo).
- Quy tắc ba (JAMA); WHO, hướng dẫn đưa tin an toàn (9789240076846).
- Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15; Nghị định 356/2025/NĐ-CP.
- Apple App Review Guidelines 1.4.1, 4.3(b), 5.1.1, 5.1.2(ii); Google Play Data safety.
