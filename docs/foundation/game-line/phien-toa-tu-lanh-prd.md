# Phiên Tòa Tủ Lạnh — PRD

> Phiên bản: 0.1 (nháp) · Cập nhật: 26/10/2026 · Trạng thái: **chờ owner duyệt, chưa được duyệt để triển khai.**
> Giai đoạn 3 (game) chưa bắt đầu; bây giờ chỉ làm tài liệu và chơi thử bằng giấy (kế hoạch owner 23/10/2026).
> Owner chốt ngày 26/10/2026: **Phiên Tòa Tủ Lạnh và Sĩ Số +1 là hai trò riêng.** Phiên Tòa **không có ma** ở bất kỳ chế
> độ nào.
> Tài liệu liên quan: [SRS](phien-toa-tu-lanh-srs.md) · [hạ tầng phòng](shared-room-platform-srs.md) · user story G31–G37
> và G01–G09 trong [`docs/user-stories/game/`](../../user-stories/game/) · [README dòng game](README.md).
> Nền nghiên cứu: báo cáo "Chốt năm trò, giữ trọn chữ Lành" (26/10/2026), mục "Phiên Tòa Tủ Lạnh: xử các vụ hài, vai do game
> chia, không ai bị loại"; `research_notes/Chốt trò chơi nhóm Lá Lành/comedy_courtroom_formats.md`.

> **"Hộp xôi trong tủ lạnh đã biến mất. Thủ phạm đang ngồi trong phòng này."**

## 0. Tóm tắt một đoạn

Phiên Tòa Tủ Lạnh là trò hài công đường cho 15–50 người trong một phòng thật, chơi bằng một màn chiếu và điện thoại của mọi
người, dài 25–35 phút. Mỗi người trả lời 5 câu vô hại về mình, rồi nhận đội (đặt tên theo hành tinh) và một vai bí mật. Tòa
xử ba vụ án hư cấu về tội vặt ("chiếm đoạt trái phép một (01) hộp xôi gà có ghi tên"). Thủ Phạm là **vai do game chia ngẫu
nhiên**; câu trả lời vô hại thật của họ thành manh mối đã mã hoá. Các đội giải mã, buộc tội, hô **"Phản đối!"**, rồi cả phòng
bỏ phiếu cùng lúc. Thẩm Phán Lá (chạy bằng mẫu câu, không AI) tuyên một bản án tượng trưng luôn kèm nút **"Miễn án"**, rồi
kể "Sự thật là…". Không ai bị loại. Cuối buổi là **Đại Án**: "Ai đứng sau cả ba vụ?" — đi tìm Kẻ Chủ Mưu. Buổi chơi kết bằng
cảnh **tòa tiêu huỷ hồ sơ** ngay trên màn hình.

## 1. Bối cảnh và bằng chứng

- **Tòa hài có sức kéo thương mại.** Amazon ra hai bản Courtroom Chaos với thẩm phán AI (Snoop Dogg 10/2025, Arnold
  Schwarzenegger 6/2026); người chơi thích nhất việc thẩm phán phản ứng mạnh và **nhớ người chơi qua các vụ** (báo cáo; research
  note §1, §3, dẫn ComicBook và Entertainment Now). Amazon chưa công bố số người chơi.
- **Bắt mâu thuẫn là lõi của trò tòa.** Ace Attorney đạt khoảng 15 triệu bản; Shu Takumi chia "một mâu thuẫn cho cả phiên" thành
  nhiều nhịp nhỏ vì bản mẫu đầu quá khó (research note §1, §3). Đây là lý do mỗi vụ có nhịp "Phản đối!" ngắn.
- **Người Việt quen khuôn này.** "Phiên tòa giả định" quen với sinh viên luật và được dùng ở trường phổ thông để phòng chống bạo
  lực học đường (Tạp chí Tòa án; Tuổi Trẻ 12/2025). Táo Quân là khuôn "đem sự cố cả năm ra trước một vị quan oai vệ", được báo
  là đã dừng sau 22 năm, nên khoảng trống "xử sự cố cuối năm" đang bỏ ngỏ; lời chê "kịch bản rời rạc" của bản 2024 là lý do
  phải có kho vụ xoay vòng và cấu trúc chặt (báo cáo; research note §2).
- **Quy mô 15–50 cần đội song song và khán giả.** Mọi trò ẩn vai vượt khoảng 10 người đều tách nhóm song song (Ultimate Werewolf
  tới ba làng) hoặc biến người thừa thành khán giả bỏ phiếu (Jackbox tới 10.000 khán giả) (research note §1, §5).
- **Host phải kick được người phá; phải có dự phòng khi AI sập.** Bài học tự rút của Death by AI (research note §1). Phiên Tòa
  chạy bằng mẫu câu nên không có điểm sập này.
- **Văn phòng là nơi dễ phát sinh khiếu nại quấy rối.** Luật sư lao động khuyên tránh trêu chọc và nhận xét ngoại hình ở tiệc
  cuối năm (ABA Journal, research note §4). Mọi lằn ranh ở §9 xuất phát từ điểm này.

Suy luận (không phải số liệu đo được): cái buồn cười đến từ (1) giọng công đường áp vào tội vặt, (2) nhịp "Phản đối!" chia nhỏ,
(3) thẩm phán nhớ vụ trước ("lại là Đội Sao Hỏa!"), và (4) khoảnh khắc "sao nó biết" không cần AI: giải xong "Thủ phạm mặc áo
xanh dương" là cả phòng quay sang nhìn áo nhau.

## 2. Mục tiêu, phi mục tiêu và nguyên tắc

### 2.1. Mục tiêu

| ID | Mục tiêu | Cách biết đã đạt (chơi thử giấy rồi bản web) |
|---|---|---|
| PT-G1 | Host kéo 15–50 người vào cuộc trong vài phút | Quét QR tới hành động đầu tiên: trung vị ≤ 60 giây (báo cáo) |
| PT-G2 | Ai cũng có phần, kể cả người ngại nói | ≥ 70% người chơi có ít nhất một lần nói hoặc dùng thẻ chứng cứ (quan sát chơi thử) |
| PT-G3 | Cả phòng cười to nhiều lần | ≥ 3 lần mỗi buổi cả phòng cười to hoặc có người rút điện thoại quay (quan sát) |
| PT-G4 | Không ai thấy bị nhắm vào | Câu khảo sát "Có lúc nào bạn thấy bị nhắm vào không?": mục tiêu 0 "Có"; số báo cáo "Tôi thấy bị nhắm vào" = 0 |
| PT-G5 | Người chơi muốn tự làm host | Số lần bấm "Tôi muốn tự làm host" ở màn kết thúc (vòng lặp Kahoot: tại Việt Nam khoảng 70.000 giáo viên dùng trong một năm, ván ở nơi làm việc tăng hơn 80% — báo cáo, dẫn Kahoot!) |
| PT-G6 | Không tạo rủi ro riêng tư mới | Dữ liệu theo người chơi xoá khi kết thúc, chậm nhất 2 giờ sau khi bắt đầu; không SDK bên thứ ba |

### 2.2. Phi mục tiêu

- Không có ma, không yếu tố rợn, không Người thứ 31 (đó là Sĩ Số +1).
- Không loại người chơi.
- Không xử chuyện thật, người thật, đồng nghiệp có tên thật, sếp thật.
- Không chữ tự do ngoài biệt danh; không thẻ "tự thú" ở MVP.
- Không AI, không LLM ở MVP (D7).
- Không bản án bằng tiền, đồ ăn mua thật, rượu bia, thử thách thể chất hay biểu diễn bắt buộc.
- Không điểm mang sang buổi sau, không bảng xếp hạng người qua các buổi, không streak, không coin/XP.
- Không bản cho người dưới 18 tuổi.

### 2.3. Nguyên tắc thiết kế

1. **Phán quyết nhắm vào vai, không nhắm vào người.** Mọi câu tuyên án nói "vai Thủ Phạm do X đảm nhận", không bao giờ "X đã
   lấy hộp xôi".
2. **Bị bắt cũng là được khen.** Thủ Phạm bị kết án nhận danh hiệu "Thủ Phạm Xuất Sắc".
3. **Mọi bản án là tượng trưng và có Miễn án.** Người vô tội bị kết án oan được miễn án tự động.
4. **Không ai bị ép nói.** Mọi lượt nói có thẻ soạn sẵn thay thế.
5. **Nhịp ngắn, cấu trúc chặt.** Mỗi pha 20–90 giây; mỗi vụ 6–8 phút.
6. **Hư cấu rõ ràng.** Mọi vụ là mẫu có chỗ trống, chủ đề đời thường vô hại.
7. **Tiêu huỷ hồ sơ là cảnh kết.** Vừa là tuân thủ Luật 91/2025, vừa là cảnh đáng quay nhất (báo cáo, kết luận).

## 3. Người dùng và bối cảnh chơi

Chỉ người từ 18 tuổi (đại học, văn phòng).

| Persona | Mô tả | Cần gì |
|---|---|---|
| **Host văn phòng** — chị Hà, 29, phụ trách hành chính công ty 40 người | Lo tất niên, không muốn trò "quá đà" làm ai phật lòng | Mở nhanh, có nút đổi vụ, kết thúc an toàn, không phải thu thông tin ai |
| **Host lớp đại học** — Thảo, 20, lớp trưởng | Buổi sinh hoạt cuối kỳ 30–45 người | Vui, ồn, hợp ký túc xá, căn tin, nhóm bài tập |
| **Người chơi ngại nói** — Minh, 24, nhân viên mới | Không quen ai, sợ bị chú ý | Thẻ chứng cứ thay lời nói, chỉ xem nếu muốn, không bị gọi tên |
| **Trưởng nhóm** — anh Tuấn, 35 | Có thứ bậc trong phòng | Không bị đặt vào thế "sếp bị xử thật"; vụ chỉ nói "sếp" chung chung |

Bối cảnh: tất niên (12/2026–1/2027 là cơ hội chơi thử không tốn tiền — báo cáo), cuối kỳ, team building. Một màn chiếu hoặc
TV, Wi-Fi hội trường có thể yếu.

## 4. Luật chốt

### 4.1. Dòng chảy một buổi (25–35 phút)

| Hồi | Bước | Thời lượng |
|---|---|---|
| Mở màn | QR trên màn chiếu (G01, G02). Tiếng búa gõ, cảnh "camera an ninh tủ lạnh, 6:47 sáng" rè hình (qua kiểm nhấp nháy). Thẩm Phán Lá: "Tòa triệu tập. Bị cáo có mặt trong phòng này." | 2 phút |
| Khai báo | 5 câu vô hại chung (G03). Điện thoại báo đội và vai (G04, G32) | 3 phút |
| Mỗi vụ (×3) | Xem §4.2 | 6–8 phút mỗi vụ |
| Đại Án | "Ai đứng sau cả ba vụ?" Ghép ba chữ bị đổi thành gợi ý về Kẻ Chủ Mưu, đề cử, cả phòng bỏ phiếu. Tuyên án cuối, trao danh hiệu. **Tòa tiêu huỷ hồ sơ** (G07) | 4–5 phút |

### 4.2. Một vụ

| # | Pha | Diễn biến | Thời lượng mặc định |
|---|---|---|---|
| 1 | Cáo trạng | Thẩm Phán Lá đọc cáo trạng giọng công đường từ mẫu vụ | 30 s |
| 2 | Câu hỏi phụ | Một câu chọn hư cấu trên điện thoại ("Nếu phải giấu hộp rỗng, bạn để ở đâu?"). Thủ Phạm có một **ràng buộc bí mật**: buộc phải chọn phương án game đưa. Kẻ Chủ Mưu cài chữ, Đồng Phạm tráo chi tiết, Thư Ký chọn manh mối để kiểm | 60 s |
| 3 | Lật manh mối | Màn chiếu lật các manh mối đã mã hoá (Caesar, câu đố emoji, câu thiếu chữ) gồm manh mối thật và manh mối giả của Đồng Phạm. Số đếm câu hỏi phụ hiện theo phương án (nhóm dưới 3 người gộp lại). Nhân Chứng nhận riêng một manh mối thật | 75 s |
| 4 | Thảo luận + buộc tội | Đội thảo luận, rồi bỏ phiếu trong đội để buộc tội một người | 90 s |
| 5 | Ra tòa | Ghế bị cáo hiện những người bị buộc tội. Luật Sư chọn thẻ ngoại phạm cho bị cáo. Mỗi đội một nút **"Phản đối!"** và 20 giây bào chữa, có thẻ chứng cứ cho người ngại nói | 15 s + 20 s × số đội (tối thiểu 60 s) |
| 6 | Bỏ phiếu | Cả phòng bỏ phiếu cùng lúc (G05) | 20 s |
| 7 | Tuyên án | Bản án tượng trưng + nút **"Miễn án"**; lá Justice (Công Lý) làm "án lệ" (hình tĩnh, không dữ liệu cá nhân). Rồi **"Sự thật là…"**: manh mối nào thật, manh mối nào bị cài, chữ nào bị đổi, ai đóng vai gì trong vụ | 45–60 s |

### 4.3. Kết án, điểm đội và danh hiệu

- Phòng 15–24 có 1 Thủ Phạm mỗi vụ: mỗi người chọn 1 bị cáo. Phòng 25–50 có 2–3 Thủ Phạm (mỗi người một "hồ sơ"): mỗi người chọn
  tối đa bằng số Thủ Phạm.
- Bị cáo bị kết án khi nằm trong nhóm nhiều phiếu nhất (bằng số Thủ Phạm) **và** được ít nhất 1/4 số người bỏ phiếu chọn. Hoà ở
  ranh giới: "Tòa chưa đủ chứng cứ", không kết án người hoà.
- Người vô tội bị kết án: bản án **tự động Miễn án**, Thẩm Phán Lá xin lỗi bằng một câu vui (PT-D3).
- Điểm đội chỉ sống trong buổi: +1 khi đội buộc tội đúng một Thủ Phạm, +1 nữa nếu Thủ Phạm đó bị kết án; +2 khi đội đề cử đúng
  Kẻ Chủ Mưu ở Đại Án. Điểm về 0 khi phòng kết thúc.
- Danh hiệu (luôn tích cực, theo vai): "Đội Phá Án" (đội nhiều điểm nhất, hoà thì cùng nhận), "Thủ Phạm Xuất Sắc" (Thủ Phạm bị kết
  án), "Cao Thủ Thoát Án" (Thủ Phạm không bị kết án), "Đồng Phạm Lém Lỉnh" (manh mối giả khiến ít nhất 1/4 phòng bầu nhầm), "Thư
  Ký Tinh Mắt" (kiểm trúng một manh mối giả), "Bóng Đen Tủ Lạnh" (Kẻ Chủ Mưu không bị lộ) hoặc "Kẻ Chủ Mưu Lộ Diện" (bị lộ).

### 4.4. Ba chế độ, không chế độ nào có ma

| Chế độ | Vụ dùng | Ghi chú |
|---|---|---|
| **Văn phòng** | Vụ đời sống công sở (gắn nhãn VP ở §6.1) | "Sếp" luôn là sếp chung chung |
| **Lớp học** (đại học, 18+) | Ký túc xá, nhóm bài tập, căn tin (nhãn LH) | |
| **Tất niên – Đại án cuối năm** | Mọi vụ, đóng khung "sự cố hài của năm" (nhãn TN) | Vẫn chỉ từ mẫu hư cấu; lấp khoảng trống Táo Quân |

Host có thêm công tắc **"Tránh chủ đề lấy đồ"** (bỏ các vụ có nhãn "lấy đồ") và nút **"Đổi sang vụ con vịt cao su"** trước hoặc
trong lúc đọc cáo trạng, cho nơi vừa xảy ra mất đồ thật (báo cáo, lằn ranh).

## 5. Vai

### 5.1. Danh sách vai

| Vai | Số lượng | Việc | Thắng / được khen khi |
|---|---|---|---|
| **Bồi Thẩm – Thám Tử** | Đa số, chia vào 3–6 đội hành tinh (Sao Thủy, Sao Kim, Sao Hỏa, Sao Mộc, Sao Thổ, Sao Thiên Vương) | Giải manh mối theo đội, buộc tội, bỏ phiếu | Đội buộc tội đúng |
| **Thủ Phạm** | 1–3 mỗi vụ, đổi người theo vụ, rải khắp các đội | Câu trả lời vô hại thật thành manh mối; câu hỏi phụ có ràng buộc bí mật; lý sự để thoát | Thoát án (hoặc bị kết án vẫn là "Thủ Phạm Xuất Sắc") |
| **Đồng Phạm** | 2–4 mỗi vụ | Mỗi vụ tráo một chi tiết của Thủ Phạm với chi tiết của chính mình để cài manh mối giả | Phòng bầu nhầm |
| **Kẻ Chủ Mưu** | 1 cho cả buổi, bí mật | Mỗi vụ đổi một chữ trong một manh mối bằng chữ game giao (là chữ cái đầu của một câu trả lời của chính mình) | Tới Đại Án không bị lộ |
| **Nhân Chứng** | 1 mỗi đội mỗi vụ | Nhận riêng một manh mối thật đã mã hoá | Đội buộc tội đúng |
| **Thư Ký Tòa** | 1 cho cả buổi | Mỗi vụ kiểm một manh mối: thật, giả hay bị sửa (chỉ mình biết) | Đội buộc tội đúng; "Thư Ký Tinh Mắt" |
| **Luật Sư** | Chọn ngẫu nhiên khi ra tòa, 1 cho mỗi bị cáo, từ Bồi Thẩm không ngồi ghế bị cáo | Chọn 1 trong 3 thẻ ngoại phạm cho bị cáo | — (vai vui) |
| **Thẩm Phán Lá** | Hệ thống | Đọc cáo trạng, phản ứng, tuyên án, nhớ vụ trước | — |

Không ai bị loại. Không ai làm Thủ Phạm hai lần trong một buổi. Kẻ Chủ Mưu và Thư Ký không bao giờ nhận vai Thủ Phạm hay Đồng
Phạm. Nhân Chứng không phải Thủ Phạm hay Đồng Phạm trong cùng vụ.

### 5.2. Bảng số vai theo quy mô

| Người chơi | Đội | Thủ Phạm / vụ (= số hồ sơ) | Đồng Phạm / vụ | Nhân Chứng / vụ | Kẻ Chủ Mưu | Thư Ký | Bồi Thẩm thường (ước) |
|---|---|---|---|---|---|---|---|
| 15–19 | 3 | 1 | 2 | 3 | 1 | 1 | 7–11 |
| 20–24 | 3 | 1 | 2 | 3 | 1 | 1 | 12–16 |
| 25–34 | 4 | 2 | 3 | 4 | 1 | 1 | 14–23 |
| 35–44 | 5 | 2 | 3 | 5 | 1 | 1 | 23–32 |
| 45–50 | 6 | 3 | 4 | 6 | 1 | 1 | 30–35 |
| Trên 50 | Người vào sau làm khán giả bỏ phiếu (mô hình Jackbox); phiếu khán giả hiện riêng, không quyết định ở MVP | | | | | | |

Nguồn: báo cáo (15–24: 3 đội, 1 Thủ Phạm, 2 Đồng Phạm; 25–50: 4–6 đội, 2–3 Thủ Phạm, 3–4 Đồng Phạm); chia nhỏ theo bậc là đề xuất
của tài liệu này, chờ chơi thử.

## 6. Ngân hàng nội dung

> **Nháp, chờ owner duyệt văn phong.** Mọi vụ là hư cấu. "Sếp" luôn là sếp chung chung. Không vụ nào chạm ngoại hình, tình cảm,
> tiền bạc thật, sức khoẻ, vùng miền, tôn giáo, chính trị, gia đình, rượu bia, người thật có tên. Vụ "trà sữa ghi nợ" của bản gốc
> đã đổi thành "trà sữa ghi tên" vì chạm chủ đề tiền (báo cáo, phần bàn giao). Giọng "Bao đại nhân xử án" chung chung; không dùng
> logo, nhạc hiệu hay hình diễn viên của Táo Quân hay Bao Thanh Thiên.

### 6.1. Kho bảy vụ (mẫu có chỗ trống `{do_vat}`, `{dia_diem}`, `{tinh_tiet}`)

**Vụ 1 — Vụ hộp xôi tủ lạnh** · Nhãn: VP, LH, TN · Lấy đồ: có

- Cáo trạng: "Bị cáo bị truy tố về tội chiếm đoạt trái phép một (01) `{do_vat}` có ghi tên tại `{dia_diem}`, với tình tiết tăng
  nặng: `{tinh_tiet}`."
- `{do_vat}`: hộp xôi gà · hộp xôi xéo · hộp xôi lạc · hộp xôi ngũ sắc
- `{dia_diem}`: tủ lạnh tầng 3 · tủ lạnh pantry · tủ lạnh phòng trọ chung · tủ lạnh căn tin
- `{tinh_tiet}`: để lại hộp rỗng đúng chỗ cũ · ăn xong còn dán lại tờ giấy ghi tên · ra tay lúc 6:47 sáng, trước cả giờ mở cửa ·
  để lại đúng một hạt lạc làm tin
- Câu hỏi phụ: "Nếu phải giấu hộp rỗng, bạn để ở đâu?" — ngăn kéo · chậu cây · sau máy in · túi áo khoác

**Vụ 2 — Vụ "seen không rep"** · Nhãn: VP, LH, TN · Lấy đồ: không

- Cáo trạng: "Bị cáo bị truy tố về tội để `{do_vat}` trong `{dia_diem}` ở trạng thái 'đã xem' rồi im lặng, với tình tiết tăng
  nặng: `{tinh_tiet}`."
- `{do_vat}`: tin nhắn hỏi trưa nay ăn gì · ảnh con mèo của cả nhóm · lời rủ đi uống trà chanh · sticker con vịt vẫy tay
- `{dia_diem}`: nhóm chat "Trưa ăn gì" · nhóm chat lớp · nhóm chat dự án · nhóm chat phòng trọ
- `{tinh_tiet}`: im lặng đúng 3 tiếng 47 phút · vẫn kịp thả tim một tin khác · trả lời bằng đúng một chữ "ok" lúc cả nhóm đã gọi
  món · đổi ảnh đại diện trong lúc chưa trả lời
- Câu hỏi phụ: "Bạn trả lời muộn bằng sticker nào?" — con vịt · ngón cái · mèo cúi đầu · bông hoa
- Ghi chú an toàn: vụ này có thể chạm ấm ức thật giữa đồng nghiệp; đặt nhãn "nhạy cảm vừa", không chọn mặc định khi host bật
  "Tránh chủ đề lấy đồ" (để host có một bộ vụ "an toàn nhất").

**Vụ 3 — Vụ trà sữa ghi tên** · Nhãn: VP, LH, TN · Lấy đồ: có

- Cáo trạng: "Bị cáo bị truy tố về tội uống mất một (01) `{do_vat}` đã ghi tên rõ ràng, đặt tại `{dia_diem}`, với tình tiết tăng
  nặng: `{tinh_tiet}`."
- `{do_vat}`: ly trà sữa trân châu size M · ly trà đào ít đá · ly sữa tươi trân châu đường đen · ly trà chanh
- `{dia_diem}`: bàn lễ tân · bàn họp nhóm · kệ căn tin · bậu cửa sổ ký túc xá
- `{tinh_tiet}`: uống còn đúng một hạt trân châu · xoay ly để giấu tên · cắm thêm ống hút thứ hai · để lại mảnh giấy "cảm ơn nha"
- Câu hỏi phụ: "Bạn giấu ly rỗng ở đâu?" — thùng giấy in · sau màn chiếu · trong ngăn bàn · cạnh bình nước

**Vụ 4 — Vụ con vịt cao su trên bục giảng** · Nhãn: VP, LH, TN · Lấy đồ: không · **Vụ an toàn (nút đổi vụ)**

- Cáo trạng: "Bị cáo bị truy tố về tội đặt trái phép `{do_vat}` tại `{dia_diem}`, khiến `{tinh_tiet}`."
- `{do_vat}`: một (01) con vịt cao su vàng · ba (03) con vịt cao su xếp hàng · một con vịt cao su đội mũ · một con vịt cao su biết
  kêu
- `{dia_diem}`: bục giảng phòng B204 · giữa bàn họp lớn · ngay cạnh máy chiếu · trên nóc tủ hồ sơ
- `{tinh_tiet}`: cả phòng cười suốt 4 phút thuyết trình · ai cũng tưởng là quà sinh nhật · con vịt kêu đúng lúc chuyển slide · con
  vịt nhìn thẳng vào camera họp online
- Câu hỏi phụ: "Bạn sẽ đặt tên con vịt là gì?" — Vịt Trưởng Phòng · Vịt Lớp Phó · Vịt Bí Ẩn · Vịt Số 7

**Vụ 5 — Vụ ghế xoay của sếp** · Nhãn: VP, TN · Lấy đồ: có (chiếm dụng)

- Cáo trạng: "Bị cáo bị truy tố về tội chiếm dụng trái phép `{do_vat}` của sếp tại `{dia_diem}`, với tình tiết tăng nặng:
  `{tinh_tiet}`."
- `{do_vat}`: chiếc ghế xoay có tựa đầu · ghế xoay có gối lưng hình con mèo · ghế xoay ngả được 135 độ · ghế xoay bánh xe kêu cót két
- `{dia_diem}`: phòng họp tầng 5 · góc cửa sổ · khu pantry · cuối hành lang
- `{tinh_tiet}`: xoay đủ 17 vòng liên tục · mang ghế vào họp online "cho lên hình sang" · hạ ghế xuống thấp nhất rồi để lại · dán
  tên mình lên tựa ghế
- Câu hỏi phụ: "Bạn trả ghế về đâu?" — đúng chỗ cũ · phòng bên cạnh · cạnh thang máy · giữa phòng họp

**Vụ 6 — Vụ máy lạnh 16 độ** · Nhãn: VP, LH, TN · Lấy đồ: không

- Cáo trạng: "Bị cáo bị truy tố về tội tự ý chỉnh `{do_vat}` xuống 16 độ tại `{dia_diem}`, với tình tiết tăng nặng: `{tinh_tiet}`."
- `{do_vat}`: máy lạnh phòng họp · máy lạnh phòng lab · máy lạnh phòng trọ · máy lạnh thư viện
- `{dia_diem}`: phòng họp lớn · phòng lab tầng 2 · phòng 302 ký túc xá · khu tự học
- `{tinh_tiet}`: giấu điều khiển trong hộp bút · cả phòng phải mặc áo khoác giữa tháng Năm · chỉnh xong còn bật thêm quạt · đổi luôn
  chế độ gió sang "bão"
- Câu hỏi phụ: "Bạn giấu điều khiển ở đâu?" — hộp bút · ngăn kéo · dưới chậu cây · trên nóc tủ

**Vụ 7 — Vụ karaoke 2 giờ sáng ở ký túc xá** · Nhãn: LH, TN · Lấy đồ: không

- Cáo trạng: "Bị cáo bị truy tố về tội tổ chức `{do_vat}` lúc 2 giờ sáng tại `{dia_diem}`, với tình tiết tăng nặng: `{tinh_tiet}`."
- `{do_vat}`: một buổi karaoke bolero · một đêm nhạc acoustic bằng ca nhựa · một buổi song ca bằng loa bluetooth · một cuộc thi hát nhép
- `{dia_diem}`: phòng 302 ký túc xá · hành lang tầng 4 · phòng sinh hoạt chung · cạnh phòng giặt
- `{tinh_tiet}`: hát đúng một bài 11 lần · dùng cây chổi làm micro · mời cả bác bảo vệ chấm điểm · tặng hoa bằng gói mì
- Câu hỏi phụ: "Bạn chọn bài mở màn nào?" — bolero · nhạc thiếu nhi · nhạc phim · nhạc Tết

Chế độ Tất niên thêm câu dẫn trước cáo trạng: "Trong năm qua, tòa đã ghi nhận một sự cố nghiêm trọng." và gọi vụ cuối là "Đại án
cuối năm".

### 6.2. Manh mối (mẫu)

Mỗi hồ sơ có 2 manh mối thật lấy từ hai câu trả lời khác nhau (không `skip`) của Thủ Phạm, 1 manh mối từ lựa chọn bắt buộc ở câu
hỏi phụ, và mỗi Đồng Phạm của hồ sơ thêm 1 manh mối giả. Mẫu bản rõ:

| Câu | Mẫu manh mối |
|---|---|
| Bữa sáng | "Sáng nay Thủ Phạm ăn `{bua_sang}`." |
| Loại nhạc | "Bài cuối Thủ Phạm nghe là `{loai_nhac}`." |
| Chỗ ngồi | "Thủ Phạm đang ngồi `{cho_ngoi}`." |
| Màu áo | "Thủ Phạm mặc áo `{mau_ao}`." |
| Món trong túi | "Trong túi Thủ Phạm có `{mon_trong_tui}`." |
| Câu hỏi phụ | "Thủ Phạm đã chọn: `{lua_chon}`." |

Ba kiểu mã hoá, giải được trong 75 giây theo đội: **Caesar** (dịch mỗi chữ một bước, có bảng chữ in trên điện thoại), **câu đố
emoji** (mỗi phương án có một emoji cố định, ví dụ 🥖 = bánh mì), **câu thiếu chữ** ("Thủ Phạm mặc áo X_NH D_ƠNG").

### 6.3. Thẩm Phán Lá — mẫu câu (nháp, ≥ 20 câu)

Quy tắc slot: chỉ dùng `{ten_doi}`, `{ten_vu}`, `{do_vat}`, `{dia_diem}`, `{tinh_tiet}`, `{so_phieu}`, `{ban_an}`, `{so_vu}`,
`{so}` (số thứ tự manh mối), `{danh_hieu}`.
`{biet_danh}` **chỉ** được dùng trong câu có nhãn "đóng vai" hoặc "khen", luôn đi với tên vai. Không câu nào nói một người "đã
làm" việc trong vụ.

| ID | Nhịp | Câu |
|---|---|---|
| TPL-01 | Khai mạc | "Tòa triệu tập. Bị cáo có mặt trong phòng này." |
| TPL-02 | Khai mạc | "Mời cả phòng ngồi thẳng lưng. Phiên tòa hôm nay xử `{so_vu}` vụ, không vụ nào có thật." |
| TPL-03 | Khai mạc (Tất niên) | "Một năm trôi qua, tủ lạnh đã chứng kiến quá nhiều. Hôm nay tòa xử hết." |
| TPL-04 | Cáo trạng | "Vụ `{ten_vu}`. Mời cả phòng nghe cáo trạng." |
| TPL-05 | Câu hỏi phụ | "Tòa có một câu hỏi nhỏ. Trả lời thật lòng, hoặc trả lời như Thủ Phạm." |
| TPL-06 | Lật manh mối | "Bằng chứng đã được niêm phong bằng mật mã. Các đội mở niêm phong đi." |
| TPL-07 | Lật manh mối | "Có manh mối thật, có manh mối bị cài. Tòa không nói cái nào là cái nào." |
| TPL-08 | Thảo luận | "Các đội có 90 giây. Nhìn áo nhau cũng được, tòa không cấm." |
| TPL-09 | Buộc tội | "Mời các đội đưa bị cáo lên ghế. Ghế hơi lạnh, mong bị cáo thông cảm." |
| TPL-10 | Phản đối | "Phản đối được ghi nhận. Đội `{ten_doi}`, tòa cho 20 giây." |
| TPL-11 | Phản đối | "Lại là Đội `{ten_doi}`! Tòa bắt đầu nhớ mặt đội này rồi." |
| TPL-12 | Phản đối | "Phản đối… được chấp nhận một nửa. Nửa còn lại tòa đang suy nghĩ." |
| TPL-13 | Luật Sư | "Luật sư bào chữa đã chọn chứng cứ ngoại phạm. Tòa xin nghe." |
| TPL-14 | Bỏ phiếu | "Mời cả phòng bỏ phiếu. Không ai biết bạn chọn ai, kể cả tòa." |
| TPL-15 | Tuyên án | "Với `{so_phieu}` phiếu, tòa tuyên: vai Thủ Phạm đã bị bắt. Bản án: `{ban_an}`." |
| TPL-16 | Tuyên án (đóng vai) | "Người đóng vai Thủ Phạm hôm nay là `{biet_danh}`. Diễn quá đạt, tòa suýt tin." |
| TPL-17 | Miễn án | "Bị cáo đã chọn Miễn án. Tòa đồng ý, búa gõ cho vui." |
| TPL-18 | Án oan | "Tòa vừa xử nhầm người vô tội. Bản án được miễn ngay. Tòa xin lỗi, tòa cũng là lá thôi." |
| TPL-19 | Thoát án | "Vai Thủ Phạm đã thoát. Hộp xôi vẫn chưa về với chủ." |
| TPL-20 | Chưa đủ chứng cứ | "Phiếu hoà. Tòa chưa đủ chứng cứ, tạm thả tất cả." |
| TPL-21 | Sự thật là | "Sự thật là… manh mối số `{so}` là thật. Manh mối số `{so}` do một Đồng Phạm cài vào." |
| TPL-22 | Sự thật là | "Có một chữ đã bị đổi trong manh mối. Ai đổi? Đại Án sẽ trả lời." |
| TPL-23 | Gọi lại vụ trước | "Vụ trước Đội `{ten_doi}` đoán trúng. Vụ này tòa để mắt kỹ hơn." |
| TPL-24 | Gọi lại vụ trước | "Lại là `{do_vat}`! Tòa nghi tủ lạnh này có vấn đề." |
| TPL-25 | Nhắc giờ | "Còn 10 giây. Tòa bắt đầu gõ búa nhẹ." |
| TPL-26 | Tạm dừng | "Tòa tạm nghỉ. Mọi người uống nước, tòa chờ." |
| TPL-27 | Đại Án | "Ba vụ, ba chữ bị đổi. Ai đứng sau cả ba vụ?" |
| TPL-28 | Đại Án | "Ba chữ này là chữ cái đầu trong ba câu trả lời của Kẻ Chủ Mưu. Các đội ghép lại đi." |
| TPL-29 | Đại Án — lộ | "Kẻ Chủ Mưu đã lộ diện: vai này do `{biet_danh}` đảm nhận. Kế hoạch rất công phu." |
| TPL-30 | Đại Án — thoát | "Kẻ Chủ Mưu vẫn chưa lộ mặt. Tủ lạnh tầng 3 sẽ còn chuyện." |
| TPL-31 | Danh hiệu (khen) | "Danh hiệu `{danh_hieu}` thuộc về `{biet_danh}`. Cả phòng vỗ tay." |
| TPL-32 | Tiêu huỷ | "Tòa tiêu huỷ hồ sơ. Câu trả lời của mọi người được xoá ngay bây giờ." |
| TPL-33 | Bế mạc | "Phiên tòa kết thúc. Không ai có tội thật. Hẹn gặp lại ở tủ lạnh." |

### 6.4. Bản án tượng trưng (nháp)

Mọi bản án hiện kèm dòng "Bản án mang tính tượng trưng" và nút **Miễn án**:

1. Rửa cốc cho cả phòng một tuần (tượng trưng).
2. Hát một câu karaoke bất kỳ.
3. Đặt tên cho máy in của phòng.
4. Làm động tác con vịt trong 5 giây.
5. Chọn nhạc nền cho buổi chơi sau.
6. Khen một câu cho đội bên cạnh.
7. Đứng dậy cúi chào tòa.
8. Đọc to lời hứa: "Tôi sẽ ghi tên lên hộp xôi của mình."
9. Kể một món ăn sáng mình thích nhất.
10. Làm "Thủ Phạm danh dự" ở vụ tiếp theo, chỉ để đứng lên vẫy tay.

Đã loại: mời trà sữa hay bất kỳ thứ gì phải trả tiền thật (báo cáo), rượu bia, thử thách thể chất, nhận xét ngoại hình.

### 6.5. Thẻ ngoại phạm và thẻ chứng cứ (nháp)

1. "Lúc 6:47 sáng, bị cáo đang xếp hàng mua bánh mì."
2. "Camera chỉ quay được một bàn tay, và bàn tay đó đeo găng rửa bát."
3. "Bị cáo không biết tủ lạnh tầng 3 mở bằng cách nào."
4. "Bị cáo đang họp online, có 12 người ngáp cùng làm chứng."
5. "Bị cáo đã ăn sáng no từ 6 giờ, cả phòng đều thấy."
6. "Con vịt cao su có thể làm chứng cho bị cáo."
7. "Bị cáo luôn đi cầu thang bộ, không thể có mặt ở tầng 3 nhanh như vậy."
8. "Bị cáo đề nghị tòa xem lại camera ở góc khác."
9. "Bị cáo chỉ uống trà đá, không bao giờ đụng trà sữa."
10. "Bị cáo đang tìm con mèo của cả nhóm."

## 7. Chỉ số

Chỉ số đếm trong sản phẩm là số đếm tổng hợp theo ngày (hạ tầng phòng §6.3), không gắn người.

| Chỉ số | Cách đo | Mục tiêu |
|---|---|---|
| Quét QR tới hành động đầu tiên | Trung vị thời gian vào phòng | ≤ 60 giây |
| Tỷ lệ phòng đi tới màn tiêu huỷ | Số phòng tới cảnh kết / số phòng bắt đầu | ≥ 80% |
| Tỷ lệ dùng "Phản đối!" | Số lượt / (số đội × số vụ) | Theo dõi; thấp nghĩa là nhịp không hấp dẫn |
| Tỷ lệ dùng Miễn án | Số lượt / số bản án | Theo dõi; cao bất thường là bản án gây ngại |
| Người từng lên tiếng | Quan sát chơi thử | ≥ 70% |
| Cười to / rút điện thoại quay | Quan sát chơi thử | ≥ 3 lần mỗi buổi |
| Muốn chơi lại / muốn làm host | Đếm lần bấm ở màn kết thúc | Theo dõi |
| Báo cáo khó chịu | Số báo cáo theo loại; câu khảo sát "bị nhắm vào" | 0 |
| Vụ bị host đổi hoặc bỏ qua | Đếm theo mã vụ | Vụ bị bỏ nhiều thì xem lại nội dung |

## 8. Phạm vi MVP và sau MVP

| MVP (khi giai đoạn 3 mở) | Sau MVP |
|---|---|
| Một gói 3 vụ + Đại Án | Mùa 6 vụ với Kẻ Chủ Mưu xuyên mùa (cần lưu dữ liệu qua buổi — mâu thuẫn với "xoá khi kết thúc", phải thiết kế lại riêng tư) |
| Thẩm Phán Lá bằng mẫu câu | Thẩm phán AI (D7): chỉ thấy nhãn vai và mã manh mối, không bao giờ thấy biệt danh; mọi đầu ra qua bộ lọc; đánh giá chuyển dữ liệu ra nước ngoài |
| 15–30 người chơi được kiểm trong cổng phát hành (hạ tầng hỗ trợ tới 50) | Khán giả trên 50 người |
| Đủ bộ nút host (G06), đổi vụ an toàn, tiêu huỷ hồ sơ | Thẻ "tự thú" do người chơi tự viết về chính mình, có bộ lọc và host duyệt |
| Ba chế độ Văn phòng, Lớp học, Tất niên | Thách đấu giữa các phòng ban |
| | Cầu nối lá Justice về Lá Lành (link thường, đồng ý riêng, không mang dữ liệu game) |

Trước khi có MVP: **chơi thử giấy** ở một buổi tất niên văn phòng 16–24 người trong tháng 12/2026 (Writer F,
`docs/playtests/2026-11-game-line/`). Host phát phiếu khai báo chỉ ghi số thứ tự, điền chữ vào mẫu mật mã in sẵn trong 5 phút giải
lao, trưởng nhóm đọc kịch bản Thẩm Phán, bỏ phiếu bằng giơ tay hoặc sticker, xé phiếu tại chỗ cuối buổi, khảo sát ba câu có câu
"có lúc nào bạn thấy bị nhắm vào không" (báo cáo).

## 9. Rủi ro và giảm thiểu

| Rủi ro | Mức | Giảm thiểu |
|---|---|---|
| **Quấy rối nơi làm việc:** một người thật bị "kết án" về chuyện trùng ấm ức có thật; trêu chọc vượt lằn ranh ở tiệc cuối năm (ABA Journal) | Cao | Phán quyết nhắm vai do game chia; vụ hư cấu từ mẫu; không chữ tự do, không @tên, không ảnh; bản án tượng trưng có Miễn án; án oan tự miễn; câu thoại không bao giờ nói một người "đã làm"; báo cáo "Tôi thấy bị nhắm vào"; host kick/đổi vụ/kết thúc |
| Thứ bậc: sếp hoặc trưởng nhóm bị xử, hoặc người dưới thấy bị ép | Trung bình | "Sếp" chung chung; vai chia ngẫu nhiên; không ai làm Thủ Phạm hai lần; chỉ xem luôn có |
| Nơi vừa mất đồ thật | Trung bình | Công tắc "Tránh chủ đề lấy đồ"; nút đổi sang vụ con vịt |
| Người ngại nói bị áp lực | Trung bình | Thẻ chứng cứ, thẻ ngoại phạm, không gọi tên ai phải nói |
| Bản án biểu diễn (hát) thành ép buộc | Trung bình | Miễn án luôn có, một chạm; không bản án nào cần tiền hay thể chất |
| Màn chiếu bị quay, đăng mạng kèm biệt danh và câu trả lời | Trung bình | Lời đồng ý nói rõ; chỉ câu trả lời vô hại; không xử chuyện thật |
| Pháp luật lao động Việt Nam về quấy rối (Bộ luật Lao động 2019, Nghị định 145/2020) | Chưa rõ | **Chưa kiểm**; cần counsel (báo cáo, rủi ro chưa giải quyết) |
| Sở hữu trí tuệ giọng điệu Táo Quân / Bao Công | Thấp–trung bình | Chỉ giọng "đại nhân" chung chung; không logo, nhạc, hình diễn viên; cần kiểm IP |
| Giấy phép G1 theo Nghị định 147/2024 | Chưa rõ | Chưa có hướng dẫn cho "công cụ party không lưu nội dung"; counsel |
| Trò quá khó giải mã ở phòng ồn 50 người | Trung bình | Ba kiểu mã có độ khó thấp; chơi thử đo; host thêm 30 giây |
| Nội dung cũ đi sau vài buổi (bài học Táo Quân) | Thấp | Kho vụ xoay vòng, chỗ trống ngẫu nhiên; thêm vụ theo mùa |

## 10. Dữ liệu và quyền riêng tư (tóm tắt; chi tiết ở SRS §7)

Theo hợp đồng dữ liệu chung: biệt danh, định danh phiên gắn thiết bị, 5 câu trả lời chọn sẵn, cờ đồng ý "câu trả lời có thể hiện
trên màn hình chung" (không tick sẵn), vai, phiếu (gồm lựa chọn câu hỏi phụ và lượt chọn bí mật theo vai), lượt "Phản đối!", dấu
thời gian. Xoá khi buổi kết thúc, chậm nhất 2 giờ sau khi bắt đầu. Chỉ giữ số đếm tổng hợp không định danh. Không ngày sinh, không
dữ liệu chiêm tinh; lá Justice chỉ là hình tĩnh. Phải khớp DPIA (Writer D) và nháp nhãn cửa hàng/chính sách (Writer E).

## 11. Quyết định chờ owner

| ID | Câu hỏi | Đề xuất — chờ owner |
|---|---|---|
| D7 (chung) | AI làm thẩm phán ở MVP? | Không |
| D1 (chung) | Tên thương hiệu phụ | Lá Úp |
| PT-D1 | Số người tối thiểu | 15; bản phòng nhỏ 8–14 để sau |
| PT-D2 | Danh hiệu có hiện biệt danh không | Có, chỉ với danh hiệu tích cực và người đã đồng ý hiện trên màn chiếu |
| PT-D3 | Người vô tội bị kết án có tự động Miễn án | Có |
| PT-D4 | Ai bấm Miễn án | Bị cáo trên điện thoại, hoặc host; mặc định hiện cho cả hai |
| PT-D5 | Dùng tên và hình "Lá" (linh vật Lá Lành) cho Thẩm Phán trong sản phẩm Lá Úp | Dùng tên "Thẩm Phán Lá" như báo cáo; hình riêng cho Lá Úp; owner chốt ranh giới thương hiệu |
| PT-D6 | Phiếu khán giả có quyết định khi hoà | Không ở MVP |
| PT-D7 | Cầu nối lá Justice ở MVP | Sau MVP |
| PT-D8 | Vụ "seen không rep" có trong bộ mặc định cho văn phòng | Có, nhưng gắn "nhạy cảm vừa" và bị bỏ khi bật "Tránh chủ đề lấy đồ" |
| PT-D9 | Ngưỡng kết án | Top k và ≥ 1/4 số phiếu (SRS PT-FR-56); chơi thử đo |
| PT-D10 | Cho đội buộc tội người cùng đội | Có |
| PT-D11 | Màn chiếu có hiện danh sách tên theo đội | Không; điện thoại báo đội, người chơi tự gọi nhau |

## 12. Bàn giao cho user story

| Story | Nội dung | Dựa vào hạ tầng |
|---|---|---|
| [G31](../../user-stories/game/G31-mo-phien-toa-chon-che-do-va-goi-vu.md) | Host chọn chế độ, gói vụ, đổi vụ an toàn | G01, G06 |
| [G32](../../user-stories/game/G32-nhan-doi-va-vai-phien-toa.md) | Chia đội hành tinh và vai Phiên Tòa | G03, G04 |
| [G33](../../user-stories/game/G33-dieu-tra-mot-vu.md) | Cáo trạng, câu hỏi phụ, manh mối, thảo luận, buộc tội | G05 |
| [G34](../../user-stories/game/G34-ra-toa-phan-doi-va-bo-phieu.md) | Ghế bị cáo, Luật Sư, "Phản đối!", bỏ phiếu | G05 |
| [G35](../../user-stories/game/G35-tuyen-an-mien-an-su-that-la.md) | Tuyên án, Miễn án, Sự thật là | — |
| [G36](../../user-stories/game/G36-dai-an-ke-chu-muu-va-tieu-huy.md) | Đại Án, danh hiệu, tiêu huỷ hồ sơ | G05, G07 |
| [G37](../../user-stories/game/G37-tham-phan-la-mau-cau.md) | Thẩm Phán Lá chạy bằng mẫu câu | — |

## 13. Bàn giao theo AGENTS.md

**Nguồn đã kiểm tra:** báo cáo "Chốt năm trò, giữ trọn chữ Lành" (toàn văn, nhất là mục Phiên Tòa); research note
`comedy_courtroom_formats.md` (§1–§5); `risks_privacy_policy.md` (§1–§5); brief chung 26/10/2026; `AGENTS.md`; chuẩn nội dung
tiếng Việt dễ hiểu; kế hoạch 23/10/2026; mẫu PRD Nơi bình yên. Apple App Review Guidelines 1.1.1 và 1.2 đọc lại ngày 26/10/2026.
Luật 91/2025, Nghị định 356/2025, Nghị định 147/2024, Bộ luật Lao động 2019 và Nghị định 145/2020 **chưa** được đối chiếu nguyên
văn trong lượt này.

**Phát hiện đã xử lý:** án oan được miễn tự động; mọi câu tuyên án nói về vai; câu hỏi phụ là câu chọn hư cấu (không thêm dữ liệu
cá nhân, lưu như phiếu); thẻ ngoại phạm loại các chi tiết sức khoẻ, ăn chay (có thể gợi tôn giáo), dị ứng; bản án bỏ mọi thứ tốn
tiền; địa điểm vụ karaoke bỏ "sân thượng"; thêm công tắc "Tránh chủ đề lấy đồ"; "Kẻ Chủ Mưu xuyên mùa" được ghi rõ là mâu thuẫn
với xoá khi kết thúc.

**Rủi ro chưa giải quyết:** pháp luật lao động về quấy rối; IP giọng Táo Quân/Bao Công; G1; PT-D5 ranh giới thương hiệu; độ khó
mã hoá ở phòng 50 người; cân bằng điểm và ngưỡng kết án chưa qua chơi thử.

**AC/DoD chưa hoàn tất:** toàn bộ. Chưa chơi thử giấy; ngân hàng nội dung chưa được owner duyệt văn phong; chưa có DPIA được duyệt,
nhãn cửa hàng, chính sách quyền riêng tư, ý kiến counsel.
