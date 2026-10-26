# Dòng game: nhãn quyền riêng tư trên store, nháp chính sách và lời giải thích trong app (26/10/2026)

> **BẢN NHÁP — chỉ áp dụng khi tính năng ra mắt; owner và counsel duyệt.**
>
> Đây là bản đồ khai báo do kỹ thuật soạn, không phải ý kiến pháp lý. Chưa trò nào có code (giai đoạn 3 chưa mở theo
> [`docs/plans/2026-10-23-privacy-content-game-plan.md`](../plans/2026-10-23-privacy-content-game-plan.md)). Mọi câu trả lời
> trên App Store Connect và Play Console phải đối chiếu lại với bản build đã ký, luồng dữ liệu production, từng SDK và câu chữ
> của console tại thời điểm nộp, giống quy tắc ở đầu [`store-privacy-data-map.md`](store-privacy-data-map.md).

## 0. Phạm vi và cách dùng

- **Nguồn dữ liệu duy nhất:** hợp đồng dữ liệu chung của dòng game (brief chung ngày 26/10/2026). Mọi trường và thời hạn lưu
  ở đây chép đúng hợp đồng đó. DPIA ([`2026-10-26-game-line-dpia.md`](2026-10-26-game-line-dpia.md)), các SRS trong
  [`docs/foundation/game-line/`](../foundation/game-line/README.md) và tài liệu này phải khớp nhau. Nếu SRS đổi một trường,
  sửa cả ba.
- **Hai nhà, hai bề mặt:**
  - **Tri Kỷ** (kèm trò đố Hiểu Nhau Không?) nằm **trong app Lá Lành** (Capacitor iOS/Android và web). Nó làm thay đổi nhãn App
    Privacy, Data safety và trang `/privacy` của Lá Lành.
  - **Lá Úp** (tên đề xuất — chờ owner, D1) gồm Hết Cứu %, Tam Sao Thất Bản, Phiên Tòa Tủ Lạnh, Sĩ Số +1. Đây là **web trước**
    (PWA/trình duyệt), không nằm trong binary của app Lá Lành. Người chơi và host không có tài khoản, chỉ có biệt danh.
- **Không sửa file hiện có.** Các sửa cần làm được liệt kê chính xác ở mục 8.
- Tên trường của Apple và Google giữ nguyên tiếng Anh như trong console.

## 1. Nguồn chính thức đã kiểm (26/10/2026)

| Nguồn | URL | Đã kiểm điều gì | Ghi chú |
|---|---|---|---|
| Apple, App Privacy Details | https://developer.apple.com/app-store/app-privacy-details/ | Định nghĩa "collect"; bốn điều kiện để được miễn khai; danh sách data type (Sensitive Info, Contacts gồm cả "social graph", Gameplay Content, Other User Content, User ID gồm "screen name, handle", Device ID, Product Interaction, Other Data Types); purposes; "linked"; "tracking"; dữ liệu chỉ xử lý theo thời gian thực; dữ liệu thu qua web traffic | Trang không ghi ngày cập nhật (chỉ ©2026) |
| Apple, App Review Guidelines | https://developer.apple.com/app-store/review/guidelines/ | 1.2 (bộ lọc, báo cáo, chặn, liên hệ công khai; app dùng chủ yếu cho chat ngẫu nhiên/ẩn danh, chấm điểm người thật kiểu "hot-or-not", bắt nạt có thể bị gỡ không báo trước); 4.7, 4.7.1–4.7.5 (HTML5 mini game trong app); 5.1.1(i)(ii)(iii)(v)(viii)(ix); 5.1.2(i)–(v) | Trang không ghi ngày cập nhật. 1.1.1, 4.3 không đọc lại lần này |
| Google Play, Data safety | https://support.google.com/googleplay/android-developer/answer/10787469 | "Collection", "sharing" và bốn ngoại lệ; ephemeral processing; optional vs required; encryption in transit; deletion badge (có cơ chế yêu cầu xoá **hoặc** tự xoá/ẩn danh trong 90 ngày); danh sách data type (Name gồm cả nickname; Other info gồm ngày sinh; Other user-generated content; Other actions gồm gameplay; Device or other IDs); WebView do app kiểm soát phải khai | Mục changelog mới nhất trên trang: 05/12/2023 |
| Google Play, account deletion | https://support.google.com/googleplay/android-developer/answer/13327111 | App cho tạo tài khoản phải có đường xoá trong app **và** một link web; app không có tài khoản không bị yêu cầu này | Không ghi ngày cập nhật |
| Google Play, User Data policy | https://support.google.com/googleplay/android-developer/answer/10144311 | Prominent disclosure & consent (trong app, ngay trước khi xin đồng ý, cần hành động khẳng định, bấm ra ngoài không phải đồng ý); privacy policy phải gắn nhãn rõ là "privacy policy", công khai, không phải PDF, có thông tin nhà phát triển và kênh liên hệ | — |
| Google Play, User-generated content | https://support.google.com/googleplay/android-developer/answer/9876937 | Phải chấp nhận điều khoản trước khi đăng UGC; kiểm duyệt liên tục; báo cáo trong app; chặn khi có tương tác 1:1 hoặc UGC công khai; cấm nội dung nhằm bêu riếu một người | Trang không nói rõ biệt danh trong game có tính là UGC hay không |
| Nghị định 356/2025/NĐ-CP | Bản tóm tắt EY (03/2026) và LuatVietnam qua tìm kiếm; bài Tạp chí Luật sư Việt Nam https://lsvn.vn/phuong-thuc-the-hien-su-dong-y-cua-chu-the-du-lieu-ca-nhan-a167945.html | Ban hành 31/12/2025, hiệu lực 01/01/2026, thay Nghị định 13/2023; Điều 4 có nhóm "đời sống riêng tư, bí mật cá nhân"; Điều 6: phương thức đồng ý phải kiểm chứng được, bên kiểm soát chịu trách nhiệm chứng minh; không được thiết lập phương thức "mặc định đồng ý" | **Nguồn thứ cấp.** Bản toàn văn trên thuvienphapluat.vn trả 403. Chưa đọc lại văn bản gốc trên vbpl.moj.gov.vn hay Công báo |
| Luật 91/2025/QH15 | Theo dossier [`2026-10-22-privacy-counsel-dossier.md`](2026-10-22-privacy-counsel-dossier.md) | Hiệu lực 01/01/2026 | Không kiểm lại lần này. Số điều về quyền của chủ thể dữ liệu để counsel điền |
| Nghị định 147/2024/NĐ-CP (game) | — | **Chưa kiểm** | Câu hỏi giấy phép G1 vẫn mở |

Những gì **không** kiểm trong đợt này: câu hỏi xếp hạng tuổi hiện hành của App Store Connect và IARC (mục "Simulated Gambling"),
và nguyên văn changelog Guideline 1.2 ngày 06/02/2026.

## 2. Kết luận ngắn

1. **Tri Kỷ** thêm một data type mới vào nhãn Apple của Lá Lành: **Gameplay Content**, dùng cho câu trả lời và kỷ lục của
   Hiểu Nhau Không?. Lá đôi là dữ liệu suy luận, nên khai vào hàng **Other Data Types** đã có. Lời mời, đồng ý và giải tán khai vào
   các hàng **Other User Content** và **Product Interaction** đã có. Tracking: **No**. Tri Kỷ **không theo dõi từng người và không
   phân tích nội dung**, nhưng có **bộ đếm tổng hợp theo ngày không định danh** (TK SRS §10). Có phải khai bộ đếm này là Analytics
   "Not Linked to You" hay không: **chờ counsel và owner**, hai phương án ở 3.2 (Q-9).
2. **Tri Kỷ** trên Google: thêm **Personal info → Name** cho biệt danh hiện cho người kia, **App activity → Other actions** cho
   câu trả lời trò đố, và **App activity → App interactions** cho trạng thái mời/nhận/chia sẻ/giải tán. Lá đôi khai vào
   **Personal info → Other info**. Shared: **No**, vì người kia nhận lá do chính hai người chủ động, nên rơi vào ngoại lệ
   "user-initiated action". Không có ephemeral. Tính năng là **Optional**.
3. **Lá Úp hiện nằm ngoài nhãn App Store và Data safety**, vì nó chạy trên web, không nằm trong app nào trên store. Phải khai
   ngay khi một trong các điều sau xảy ra: app Lá Lành mở Lá Úp trong WebView hay route Capacitor; Lá Úp được đóng gói thành app
   (kể cả Trusted Web Activity trên Play); hoặc Lá Úp thành HTML5 mini game trong app (Guideline 4.7). Bảng khai sẵn cho trường hợp
   đó nằm ở 3.4 và 4.3.
4. **Lá Úp vẫn cần chính sách quyền riêng tư riêng** (Luật 91; lời hứa của web). Nháp ở 5.2.
5. **Chính sách hiện tại của Lá Lành là trang `/privacy`** (component `ConsentPage` ở chế độ chi tiết, tiêu đề "Lá Lành dùng dữ liệu
   thế nào?"). Google yêu cầu chính sách phải gắn nhãn rõ là privacy policy và có thông tin nhà phát triển. Trang hiện tại không có
   chữ "Chính sách quyền riêng tư" và không nêu pháp nhân. Đây là phát hiện có trước dòng game. Xem mục 8, F-5.
6. **Bốn chỗ lệch cần chốt trước khi viết code** (chi tiết ở mục 9): (a) "khoảnh khắc" cuối mùa của Hết Cứu % không được trích
   lại % thô đã phải xoá sau 72 giờ; (b) chưa có cách giữ bằng chứng đồng ý cho người chơi không tài khoản, trong khi dữ liệu phòng
   bị xoá khi hết buổi; (c) cặp Tri Kỷ có thể bị coi là "social graph" (Apple Contacts / Google Contacts); (d) Lá Úp chưa có nút
   chặn ở cấp người chơi, trong khi Guideline 4.7.1 và 1.2 đòi có nếu sau này vào app.

## 3. Apple App Privacy (nhãn dinh dưỡng)

### 3.1 Tri Kỷ — thay đổi so với nhãn hiện tại của Lá Lành

Nhãn hiện tại: [`store-privacy-data-map.md` mục "Apple Privacy Manifest / App Privacy mapping"](store-privacy-data-map.md).
Bảng dưới chỉ ghi phần Tri Kỷ thêm vào. "Có sẵn" nghĩa là category đã khai, chỉ mở rộng mô tả.

| Apple category → data type | Dữ liệu Tri Kỷ | Mới hay có sẵn | Linked to you | Used to track you | Purposes |
|---|---|---|---:|---:|---|
| Identifiers → User ID | ID khách/chủ sở hữu của **mỗi** người trong cặp; bản ghi mời/nhận gắn hai ID | Có sẵn | Yes | No | App Functionality |
| User Content → Other User Content | Ngày/giờ sinh **của từng người, từ hồ sơ mà chính người đó đã đồng ý**, được dùng lại để tính lá đôi (không thu mới, không ai nhập hộ ai) | Có sẵn (hàng "birth date/time…"), **không thu mới** | Yes | No | App Functionality, Product Personalization |
| Other Data → Other Data Types | Lá đôi: ba khối nội dung, nhãn bậc, lá tarot của cặp. Đây là dữ liệu suy luận về quan hệ, xử lý như dữ liệu nhạy cảm "đời sống riêng tư" | Có sẵn (hàng "derived natal/transit factors… astrology profile"), mở rộng mô tả | Yes | No | App Functionality, Product Personalization |
| Location → Precise Location | Toạ độ nơi sinh trong hồ sơ của từng người (không phải GPS) được dùng lại để tính lá đôi | Có sẵn, **không thu mới** | Yes | No | App Functionality, Product Personalization |
| User Content → Other User Content | Biệt danh A hiện cho B trên lời mời; bản ghi đồng ý mục đích Tri Kỷ; bằng chứng đồng ý chia sẻ của từng người (ai, lúc nào, phiên bản câu chữ, bản ảnh; không có ảnh) | Có sẵn (giống hàng Radar) | Yes | No | App Functionality |
| **User Content → Gameplay Content** | Hiểu Nhau Không?: mã lựa chọn của từng câu (của mình và câu đoán về người kia), gắn với cặp nên Lá Lành xử lý như dữ liệu nhạy cảm; xoá khi cả hai đã xem kết quả, muộn nhất 7 ngày sau khi lượt xong. Sau đó chỉ còn kỷ lục x/7 (và tháng) của cặp | **Mới** | Yes | No | App Functionality |
| Usage Data → Product Interaction | Trạng thái mời, nhận, chia sẻ, giải tán | Có sẵn | Yes | No | App Functionality |

**Lý do chọn Gameplay Content:** Apple định nghĩa type này gồm "saved games, multiplayer matching or gameplay logic, or
user-generated content in-game". Câu trả lời trò đố và kỷ lục của cặp khớp đúng định nghĩa đó. Khai vào Other User Content cũng
không sai, nhưng Gameplay Content cho người đọc biết đây là dữ liệu trò chơi. Counsel hoặc người nộp app có thể chọn một trong hai.
Không được bỏ cả hai.

### 3.2 Những category Tri Kỷ không khai, và lý do

| Category | Không khai vì | Điều kiện phải xem lại |
|---|---|---|
| Contacts | Không đọc danh bạ. Lời mời gửi qua bảng chia sẻ của hệ điều hành, mỗi lần một người (5.1.2(v)). Không tải danh bạ, không gợi ý người để mời | Apple tính cả "social graph" vào Contacts. Một cặp Tri Kỷ là một cạnh quan hệ giữa hai người dùng. Lời mời Radar đang khai là Other User Content, và tài liệu này theo cùng tiền lệ đó. Nếu counsel coi cặp là social graph, phải thêm Contacts cho **cả Radar lẫn Tri Kỷ cùng lúc** (câu hỏi Q-3) |
| Sensitive Info | Danh sách của Apple gồm chủng tộc, xu hướng tính dục, thai sản, khuyết tật, tôn giáo/triết lý, công đoàn, chính trị, di truyền, sinh trắc. Tri Kỷ chặn khung yêu đương ("không phải chuyện yêu đương") và không suy ra những điều này | Câu hỏi Q-4: lá số chiêm tinh có bị coi là "religious or philosophical beliefs" không. Nhãn hiện tại của Lá Lành không khai, nên giữ nhất quán cho tới khi counsel trả lời. Luật Việt Nam xếp "đời sống riêng tư" vào nhóm nhạy cảm, nhưng đó là nghĩa vụ theo luật, không phải category của Apple |
| Usage Data → Product Interaction với mục đích Analytics (**chưa chốt**) | Tri Kỷ không có analytics theo người hay theo nội dung, không SDK. PRD §6 và TK SRS §10 có bộ đếm tổng hợp theo ngày: `invite_created`, `invite_accepted`, `pair_built`, `invite_profile_created_in_flow`, `share_requested`, `share_approved`, `pair_dissolved_lt30d`, `pair_dissolved_ge30d`, `invite_reported{reason}`, `inviter_blocked`, `build_failed{code}`; không ID, ẩn ô < 3 (KS-04), báo cáo chỉ ô ≥ 10, thời hạn theo DPIA X7 | **Hai phương án, chờ counsel và owner (Q-9):** (A) bộ đếm chỉ tăng một số nguyên, không lưu sự kiện từng lần, nên counsel có thể kết luận không cần khai → giữ như hiện tại, không thêm Analytics. (B) khai thận trọng: thêm "Usage Data → Product Interaction, **Not Linked to You**, Analytics". Đề xuất mặc định: (B), cùng cách với Lá Úp ở 3.4. Tài liệu này không đề xuất xây thêm analytics nào |
| Identifiers → Device ID | Token lời mời là token năng lực (capability) được băm, không phải ID thiết bị | — |
| Purchases, Financial Info | Không thu phí xem, không có gói "ai chọn bạn" | Không bao giờ thêm (bài học NGL) |
| Contact Info → Name | Biệt danh là tên hiển thị trong app, Apple xếp "screen name" vào User ID | — |

### 3.3 Privacy manifest của app

`apps/mobile/ios/App/App/PrivacyInfo.xcprivacy` hiện khai `UserID`, `PreciseLocation`, `OtherUserContent`, `ProductInteraction`,
`OtherDataTypes`, tất cả `Linked=true`, `Tracking=false`. Khi Hiểu Nhau Không? ra mắt phải thêm
`NSPrivacyCollectedDataTypeGameplayContent` (Linked `true`, Tracking `false`, Purpose `AppFunctionality`). Lá đôi (không có trò đố)
không cần thêm type mới. `NSPrivacyTracking` giữ `false`. Nếu Q-9 chốt phương án (B), manifest cần thêm một mục `NSPrivacyCollectedDataTypeProductInteraction` với Linked `false`, Purpose `Analytics` cho bộ đếm tổng hợp của Tri Kỷ; phương án (A) thì không đổi. **Chờ chốt.**

### 3.4 Lá Úp và nhãn App Store

**Hiện tại: ngoài phạm vi.** Nhãn App Privacy gắn với một app trên App Store. Lá Úp chạy trên web, không nằm trong binary của
Lá Lành, nên không có nhãn nào phải khai. Một số điểm nối với app Lá Lành không đổi kết luận này:

- **Cầu nối từ Lá Úp sang Lá Lành** (lá tarot của tuần, chú thích Sao Thủy, lá Justice) mở Lá Lành bằng một URL **không chứa** mã
  phòng, biệt danh, token hay câu trả lời. App Lá Lành không nhận dữ liệu game, nên không có gì mới để khai.
- **Nút "Chơi Lá Úp" trong app Lá Lành** (nếu có): mở bằng trình duyệt hệ thống, không mở trong WebView của app. Nếu mở trong
  WebView hay một route Capacitor, Apple tính đó là "data collected via web traffic" do app kiểm soát, và phải khai theo bảng dưới.

**Bảng khai sẵn khi Lá Úp vào một app iOS.** Áp dụng khi: (a) Lá Úp được đóng gói thành app riêng; (b) Lá Úp chạy trong WebView
hoặc Capacitor của Lá Lành; hoặc (c) Lá Úp thành HTML5 mini game theo Guideline 4.7.

| Apple category → data type | Dữ liệu | Trò | Linked | Tracking | Purposes |
|---|---|---|---:|---:|---|
| Identifiers → User ID | `nickname` (screen name) | Cả bốn | Yes | No | App Functionality |
| Identifiers → Device ID | `host_session`, `player_session`, phiên thành viên (ID ngẫu nhiên gắn thiết bị) | Cả bốn | Yes | No | App Functionality |
| Identifiers → Device ID | Endpoint đăng ký web push | Hết Cứu % (chỉ khi bật thông báo) | Yes | No | App Functionality |
| User Content → Gameplay Content | Vai được chia, phiếu bầu, mốc thời gian | Cả bốn | Yes | No | App Functionality |
| User Content → Gameplay Content | 5 câu tự khai vô hại, cờ đồng ý hiện trên màn hình chung, lượt dùng "Phản đối!" | Phiên Tòa | Yes | No | App Functionality |
| User Content → Gameplay Content | 5 câu tự khai, cờ đồng ý, lời thì thầm (Kẻ Bị Nhập chọn câu trả lời nào) | Sĩ Số +1 | Yes | No | App Functionality |
| User Content → Gameplay Content | Các bước trong chuỗi (mã ý định, mã cách diễn đạt, mã mood, mã câu đoán) | Tam Sao | Yes | No | App Functionality |
| User Content → Gameplay Content | % từng mức, mã thẻ "lời khai", phiếu đoán và số lá đặt, cờ tình nguyện Nhân Vật Chính, "ẩn % của tôi", "tuần này đừng đoán tôi", danh hiệu và khoảnh khắc | Hết Cứu % | Yes | No | App Functionality |
| Usage Data → Product Interaction | Số đếm tổng hợp (số phòng, thời lượng, tỉ lệ hoàn tất, số báo cáo) | Cả bốn | **No** | No | Analytics |
| Diagnostics → Other Diagnostic Data | Log lỗi thô, không có biệt danh, câu trả lời hay token | Cả bốn | **No** | No | App Functionality |

Ghi chú cho bảng:

- **Không dùng ngoại lệ "real time".** Apple chỉ miễn khai khi dữ liệu bị bỏ ngay sau khi phục vụ xong một request. Dữ liệu phòng
  sống qua nhiều request, tới khi phòng kết thúc (muộn nhất 2 giờ), nên vẫn là "collected". Các phòng xoá sớm vẫn phải khai.
- **Số đếm tổng hợp.** Apple yêu cầu khai cả dữ liệu không gắn danh tính ("Data Not Linked to You"). Nếu số đếm được tạo từ sự
  kiện của người chơi trên máy chủ thì khai như bảng. Nếu bộ đếm chỉ tăng một số nguyên và không bao giờ lưu sự kiện, counsel quyết
  có cần khai hay không.
- **Câu "ngồi gần cửa sổ hay cửa ra vào"** là câu trả lời trò chơi, không phải vị trí địa lý. Không khai Location.
- **Không bao giờ khai:** Contacts, Location, Sensitive Info, Photos or Videos, Audio Data, Emails or Text Messages, Purchases. Hợp
  đồng dữ liệu cấm những thứ này ở MVP.
- **Khi vào app, các Guideline sau trở thành bắt buộc:** 4.7.1 (bộ lọc, báo cáo, **chặn người dùng**), 4.7.3 (không chia dữ liệu
  hay quyền cho phần mềm con khi chưa có đồng ý từng lần), 4.7.4 (mục lục và universal link cho từng trò), 4.7.5 (cơ chế giới hạn
  tuổi dựa trên tuổi đã xác minh hoặc tự khai). Nếu đóng gói thành app riêng, còn có 4.2 (không chỉ là website đóng gói lại).

### 3.5 Đối chiếu App Review Guidelines theo từng trò

| Guideline | Yêu cầu | Tri Kỷ | Lá Úp (khi vào app) |
|---|---|---|---|
| 1.2 | Bộ lọc, báo cáo, chặn, liên hệ công khai; không chấm điểm người thật, không chat ẩn danh, không bắt nạt | Không chữ tự do ngoài biệt danh; không %, không xếp hạng; giải tán im lặng thay cho chặn. Cần nút báo cáo lời mời | Biệt danh được lọc; host kick/đổi tên; người chơi báo cáo, rời, "chỉ xem". **Thiếu:** nút chặn ở cấp người chơi (Q-6) |
| 5.1.1(i) | Link chính sách trong metadata và trong app; nêu dữ liệu, cách thu, mọi mục đích, thời hạn, cách rút đồng ý và yêu cầu xoá | Mục 5.1 | Mục 5.2 |
| 5.1.1(ii) | Đồng ý trước khi thu, rút đồng ý dễ | Ô đồng ý riêng cho từng người, không tick sẵn (mục 6.7) | Ô hiện câu trả lời lên màn hình chung không tick sẵn; thông báo tự bật (mục 6) |
| 5.1.1(iii) | Chỉ thu dữ liệu cần cho việc đang làm; ưu tiên share sheet | Share sheet, mỗi lần một người | Không danh bạ, không ảnh, không giọng nói |
| 5.1.1(v) | Không bắt đăng nhập khi không cần | Theo luồng Lá Chứng hiện có (bước tạo link cần đăng nhập, xem US-08) | Không tài khoản |
| 5.1.1(viii) | Không tổng hợp thông tin cá nhân không lấy trực tiếp từ người đó hoặc không có đồng ý rõ ràng | Mỗi người tự dùng hồ sơ của mình và tự đồng ý. **Chặn lối Check kín của US-12** | Không có dữ liệu về người thứ ba (đã bỏ câu "bạn ngồi cạnh ai") |
| 5.1.1(ix) | App cần thông tin nhạy cảm nên do pháp nhân nộp | Câu hỏi Q-10 (áp cho cả Lá Lành) | — |
| 5.1.2(i)(ii) | Không dùng dữ liệu khi chưa xin phép; không đổi mục đích khi chưa xin lại | Hồ sơ sinh dùng cho Tri Kỷ cần đồng ý mục đích riêng, tách khỏi `birth-profile-v1` | Cầu nối không mang dữ liệu game sang Lá Lành |
| 5.1.2(iii) | Không lén dựng hồ sơ người dùng | Không có bảng "ai chọn bạn", không bản đồ cặp | Không ghép phiên giữa các phòng |
| 5.1.2(v) | Không chọn tất cả danh bạ; mô tả rõ tin nhắn sẽ hiện thế nào | Preview lời mời trước khi gửi | Link phòng chia qua QR/share sheet |

## 4. Google Play Data safety

### 4.1 Tri Kỷ — thay đổi so với Data safety hiện tại của Lá Lành

Data safety hiện tại: [`store-privacy-data-map.md` mục "Google Play Data Safety mapping"](store-privacy-data-map.md).

| Category → data type | Dữ liệu Tri Kỷ | Collected | Shared | Ephemeral | Required / Optional | Purposes |
|---|---|---:|---:|---:|---|---|
| Personal info → User IDs | ID khách/chủ sở hữu của mỗi người; bản ghi mời/nhận | Yes (có sẵn) | No | No | Optional (cả tính năng là tuỳ chọn) | App functionality, Security |
| Personal info → Other info | Ngày/giờ sinh từ hồ sơ của từng người (có sẵn, không thu mới); lá đôi suy luận | Yes | No | No | Optional | App functionality, Personalization |
| Location → Precise location | Toạ độ nơi sinh trong hồ sơ (có sẵn, không thu mới, không phải vị trí thiết bị) | Yes (có sẵn) | No | No | Optional | App functionality, Personalization |
| **Personal info → Name** | Biệt danh A hiện cho B trên lời mời và lá đôi | **Yes (mới)** | No | No | Optional | App functionality |
| **App activity → Other actions** | Hiểu Nhau Không?: mã lựa chọn, điểm x/7, kỷ lục của cặp | **Yes (mới)** | No | No | Optional | App functionality |
| App activity → App interactions | Mời, nhận, cờ đồng ý chia sẻ, giải tán | Yes (có sẵn) | No | No | Optional | App functionality |

Lý do từng ô:

- **Shared = No.** Google định nghĩa "sharing" là chuyển cho bên thứ ba. Hetzner và Supabase là bên cung cấp dịch vụ (ngoại lệ
  "service providers"). B nhìn thấy lá đôi vì cả A và B chủ động tạo lá, và việc chia ảnh ra ngoài chỉ xảy ra khi cả hai bấm đồng
  ý, qua share sheet do người dùng mở (ngoại lệ "user-initiated action or consent").
- **Ephemeral = No.** Lá đôi sống tới khi một người giải tán. Câu trả lời trò đố sống tới khi cả hai đã xem kết quả, muộn nhất 7 ngày sau khi lượt xong, tức là qua nhiều request.
- **Bộ đếm tổng hợp (chưa chốt, Q-9):** (A) không khai nếu counsel kết luận bộ đếm số nguyên không lưu sự kiện không phải "collection"; (B) thêm mục đích **Analytics** vào hàng App activity → App interactions. Đề xuất mặc định: (B). Không có trả lời "No" vô điều kiện cho câu hỏi này cho tới khi chốt.
- **Name.** Google ghi rõ type này gồm cả "nickname". Hàng Radar hiện khai biệt danh dưới "Personal info / User-generated content".
  Tri Kỷ khai cụ thể hơn là Name. Nên sửa luôn hàng Radar cho thống nhất (mục 8, F-1).
- **Contacts:** không khai, cùng lý do và cùng câu hỏi Q-3 như phần Apple. Google cũng tính "social graph data such as usernames"
  vào Contacts.

### 4.2 Security practices của Lá Lành sau khi có Tri Kỷ

| Câu hỏi trong Play Console | Câu trả lời | Căn cứ |
|---|---|---|
| Is all of the user data collected by your app encrypted in transit? | Yes | Bản native production bắt buộc API HTTPS; Android tắt cleartext (data map, mục "Runtime posture") |
| Do you provide a way for users to request that their data is deleted? | Yes | Xoá khách trong app; giải tán lá xoá cứng dữ liệu cặp; rút đồng ý Tri Kỷ |
| Account deletion web link | **Phải kiểm** | Lá Lành cho liên kết tài khoản (Google/email), nên Play yêu cầu một link web để yêu cầu xoá tài khoản mà không cần cài lại app. Data map chưa ghi link này (mục 8, F-2) |
| Independent security review | Không chọn | Không có đánh giá MASA |
| Target audience | 18+ | Lá Lành dành cho người từ 18 tuổi (trang `/privacy`). Không thuộc Families |

### 4.3 Lá Úp và Data safety

**Hiện tại: ngoài phạm vi.** Data safety chỉ áp cho app trên Google Play. Lá Úp chạy trên web. Phải khai khi Lá Úp được đóng gói
lên Play (kể cả Trusted Web Activity, vì app kiểm soát nội dung web), hoặc chạy trong WebView do app Lá Lành kiểm soát.

**Bảng khai sẵn khi Lá Úp vào một app Android:**

| Category → data type | Dữ liệu | Trò | Collected | Shared | Ephemeral | Required / Optional | Purposes |
|---|---|---|---:|---:|---:|---|---|
| Personal info → Name | `nickname` | Cả bốn | Yes | No | No | Required (để vào phòng/nhóm) | App functionality |
| Device or other IDs | `host_session`, `player_session`, phiên thành viên | Cả bốn | Yes | No | No | Required | App functionality, Fraud prevention, security, and compliance |
| Device or other IDs | Endpoint web push | Hết Cứu % | Yes | Q-7 | No | Optional | Developer communications |
| App activity → Other actions | Vai, phiếu bầu, mốc thời gian; "Phản đối!" (Phiên Tòa); lời thì thầm (Sĩ Số +1); bước trong chuỗi (Tam Sao); %, mã lời khai, phiếu đoán, lá, cờ tình nguyện, hai nút riêng tư, danh hiệu (Hết Cứu %) | Cả bốn | Yes | No | No | Required (trừ cờ tình nguyện và hai nút riêng tư: Optional) | App functionality |
| App activity → Other user-generated content | 5 câu tự khai và cờ đồng ý hiện trên màn hình chung | Phiên Tòa, Sĩ Số +1 | Yes | No | No | **Optional** (không tick thì không hỏi 5 câu) | App functionality |
| App activity → App interactions | Số đếm tổng hợp | Cả bốn | Yes (khai thận trọng) | No | No | Required | Analytics |
| App info and performance → Diagnostics | Log lỗi thô, không biệt danh/câu trả lời/token | Cả bốn | Yes | No | No | Required | App functionality |

Security practices nếu có app Lá Úp:

- **Encrypted in transit:** Yes (HTTPS/TLS; payload web push được mã hoá theo chuẩn Web Push).
- **Deletion:** Yes. Dữ liệu phòng tự xoá khi phòng kết thúc, muộn nhất 2 giờ sau khi bắt đầu. Tam Sao bản chat xoá 48 giờ sau khi
  lật. Hết Cứu % xoá % thô sau 72 giờ, phần còn lại muộn nhất hết mùa + 30 ngày (khoảng 86 ngày với mùa 8 tuần). Như vậy đạt nhánh
  "tự xoá trong 90 ngày" của badge, **trừ** endpoint push (giữ tới khi tắt) và trường hợp mùa bị kéo dài. Vì thế vẫn cần nút "Xoá
  dữ liệu của tôi" trong game để đạt nhánh "có cơ chế yêu cầu xoá" (Q-8).
- **Account deletion link:** không áp dụng, vì không có tài khoản.
- **UGC policy:** nếu coi biệt danh là UGC, người chơi phải chấp nhận điều khoản trước khi đặt biệt danh, và phải có báo cáo trong
  app. Hết Cứu % là nhóm có thành viên cố định, nên thuộc loại "verified or registered" và cần báo cáo. Chặn chỉ bắt buộc khi có
  tương tác 1:1 hoặc UGC công khai, mà Lá Úp không có cả hai (Q-6).

### 4.4 Đối chiếu chính sách Google theo từng trò

| Chính sách | Yêu cầu | Tri Kỷ | Lá Úp (khi vào app) |
|---|---|---|---|
| User Data — Prominent disclosure | Thông báo trong app, ngay trước khi xin đồng ý, không gộp với nội dung khác; cần hành động khẳng định | Mục 6.7: màn đồng ý riêng trước khi dùng hồ sơ cho lá đôi | Mục 6.1–6.5 |
| User Data — Privacy policy | Gắn nhãn "privacy policy", công khai, không phải PDF, có thông tin nhà phát triển và kênh liên hệ | Trang `/privacy` hiện thiếu nhãn và pháp nhân (F-5) | Trang chính sách riêng của Lá Úp (mục 5.2) |
| Account deletion | Có tài khoản thì có link web | F-2 | Không áp dụng |
| UGC | Điều khoản, kiểm duyệt, báo cáo, chặn | Không có UGC công khai | Như 4.3 |

## 5. Chính sách quyền riêng tư — bản nháp

### 5.0 Cấu trúc hiện tại và cách ghép

Chính sách hiện tại của Lá Lành nằm ở route `/privacy`, do `apps/web/src/features/consent/ConsentPage.tsx` dựng ở chế độ chi tiết.
Trang gồm năm thẻ tóm tắt và một danh sách mục mở/đóng (`<details>`), mỗi mục có một câu hỏi làm tiêu đề ("Radar check kín", "Lời
mời Radar", "Xoá và bản sao lưu", "Dữ liệu beta đi đâu?"…) và một đoạn văn ngắn. Trang ghi "Chính sách áp dụng: birth-profile-v1"
và có kênh liên hệ về dữ liệu.

Nháp dưới đây theo đúng khuôn đó: một câu hỏi làm tiêu đề, rồi một đoạn ngắn nói ai, cái gì, bao lâu, ai thấy, xoá thế nào.

- **Tri Kỷ** thêm thành mục mới trong `/privacy` của Lá Lành (5.1).
- **Lá Úp** cần một trang chính sách riêng trên bề mặt web của Lá Úp (5.2), vì đó là một bề mặt khác, người chơi không qua màn
  đồng ý của Lá Lành.

### 5.1 Mục thêm vào chính sách của Lá Lành: Tri Kỷ

> **BẢN NHÁP — chỉ áp dụng khi tính năng ra mắt; owner và counsel duyệt.**

**Tri Kỷ dùng dữ liệu gì?**
Tri Kỷ tạo một lá đôi cho hai người. Lá chỉ mở khi cả hai cùng đồng ý. Lá Lành dùng ngày, giờ và nơi sinh trong hồ sơ **của từng
người**, do chính người đó nhập và đồng ý. Không ai nhập thông tin sinh hộ người khác. Lá đôi gồm điều hai bạn chung, cách hai bạn bù
nhau, một việc nhỏ để thử và lá tarot của hai bạn. Lá không có phần trăm độ hợp và không xếp hạng ai.

**Vì sao cần đồng ý riêng?**
Lá đôi là thông tin suy ra về mối quan hệ của hai người, nên Lá Lành coi đây là dữ liệu nhạy cảm về đời sống riêng tư. Lá Lành
nói điều này ngay trên ô đồng ý, ở màn của người mời và màn của người nhận. Đồng ý dùng hồ sơ cho bản đọc của riêng bạn không tự
bật Tri Kỷ. Mỗi người tick một ô riêng, không tick sẵn, cho đúng một lá với đúng một người.

**Ai thấy lá đôi?**
Chỉ hai bạn. Lá không hiện trong thông báo, không hiện trong ảnh xem trước của link. Lá Lành không theo dõi riêng từng người và
không phân tích nội dung lá; Lá Lành chỉ đếm tổng số theo ngày, ví dụ có bao nhiêu lời mời được nhận, không gắn với ai. Ảnh lá
đôi chỉ chia ra ngoài được khi cả hai cùng bấm đồng ý. Ảnh có biệt danh, không có ngày, giờ hay nơi sinh. Mỗi lần một bạn đồng ý
chia sẻ, Lá Lành ghi lại ai đồng ý, lúc nào và cho ảnh nào (không lưu ảnh); bản ghi này giữ khi lá còn và bị xoá khi giải tán.
Yêu cầu chia sẻ đã xong được xoá sau 7 ngày.

**Lời mời hoạt động thế nào?**
Bạn gửi lời mời cho từng người qua bảng chia sẻ của điện thoại. Lá Lành không đọc danh bạ. Link mời có hạn (7 ngày), bạn thu hồi
được, và link không chứa thông tin sinh hay mã định danh. Link là quyền mở lời mời, nên chỉ gửi cho đúng người. Người nhận có thể
chặn người mời hoặc báo cáo lời mời; danh sách chặn giữ tới khi bỏ chặn, báo cáo giữ 30 ngày. Lời mời đã kết thúc được giữ thêm 30
ngày để chống lạm dụng rồi xoá.

**Hiểu Nhau Không? lưu gì?**
Câu bạn chọn cho mình và câu bạn đoán về người kia. Câu trả lời gắn với hai bạn nên Lá Lành xử lý như dữ liệu nhạy cảm. Câu
trả lời bị xoá khi cả hai đã xem kết quả, muộn nhất 7 ngày sau khi lượt chơi xong. Sau đó Lá Lành chỉ giữ kỷ lục tốt nhất của hai
bạn, dạng x/7, kèm tháng đạt kỷ lục, tới khi một bạn tắt trò đố hoặc lá đôi bị giải tán.

**Giữ bao lâu, xoá thế nào?**
Lá đôi còn tới khi một trong hai người giải tán. Ai cũng giải tán được bất cứ lúc nào trong Tri Kỷ. Khi giải tán, lá và mọi dữ
liệu của cặp bị xoá, người kia không nhận thông báo. Xoá hồ sơ Lá Lành của bạn cũng giải tán mọi lá Tri Kỷ của bạn. Thời hạn dọn
bản sao lưu theo mục "Xoá và bản sao lưu".

**Dữ liệu đi đâu?**
Như mọi dữ liệu của Lá Lành: máy chủ Hetzner tại Đức và cơ sở dữ liệu Supabase tại Frankfurt, Đức. Tri Kỷ không gửi gì cho AI.

### 5.2 Chính sách quyền riêng tư của Lá Úp (trang riêng)

> **BẢN NHÁP — chỉ áp dụng khi tính năng ra mắt; owner và counsel duyệt.** Tên "Lá Úp" chờ owner chốt (D1).

**Chính sách quyền riêng tư của Lá Úp**

**Lá Úp là gì, ai chịu trách nhiệm?**
Lá Úp là các trò chơi nhóm, một sản phẩm của Lá Lành. Bên chịu trách nhiệm về dữ liệu là [tên pháp nhân và địa chỉ — chờ owner,
Q-10]. Chính sách này áp dụng cho Hết Cứu %, Tam Sao Thất Bản, Phiên Tòa Tủ Lạnh và Sĩ Số +1.

**Lá Úp không cần gì của bạn?**
Không cần tài khoản, email, số điện thoại, ngày sinh, ảnh hay giọng nói. Lá Úp không đọc danh bạ, không hỏi vị trí, không có chat,
không có quảng cáo và không dùng công cụ phân tích của bên thứ ba.

**Khi vào phòng, Lá Úp lưu gì?**
Biệt danh bạn tự đặt (2–20 ký tự, có lọc), một mã ngẫu nhiên gắn với trình duyệt của bạn để nhận ra bạn trong phòng, vai game
chia cho bạn, phiếu bạn bầu và thời điểm bạn làm các việc đó. Mã phòng có 6 ký tự. Link phòng chứa một mã truy cập; máy chủ chỉ
lưu bản đã băm của mã này. Host có thể đổi biệt danh của bạn hoặc mời bạn ra khỏi phòng.

**Phòng giữ dữ liệu bao lâu?**
Khi phòng kết thúc, màn "tiêu huỷ hồ sơ" xoá ngay dữ liệu của từng người chơi. Nếu host quên kết thúc, phòng tự đóng và xoá muộn
nhất 2 giờ sau khi bắt đầu. Lá Úp chỉ giữ số đếm chung không nhận ra ai: số phòng, thời lượng, số ván chơi hết, số lượt báo cáo.

**Phiên Tòa Tủ Lạnh lưu thêm gì?**
Nếu bạn tick ô "câu trả lời có thể hiện trên màn hình chung", game hỏi bạn 5 câu vô hại: bữa sáng, bài hát nghe gần nhất, ngồi
gần cửa sổ hay cửa ra vào, màu áo, một món trong túi. Bạn chọn từ danh sách có sẵn. Câu trả lời của Thủ Phạm thành manh mối trên
màn hình chung. Game còn lưu lượt dùng nút "Phản đối!" của đội. Không tick thì bạn vào ở chế độ "chỉ xem": game không hỏi 5 câu,
bạn không nhận vai, vẫn xem và bỏ phiếu khán giả nếu phòng cho phép. Đã tick mà không muốn trả lời câu nào thì chọn "Không muốn
nói". Mọi thứ bị xoá khi buổi kết thúc. Màn hình chung chỉ hiện số đếm, ví dụ "áo xanh: 11 người"; nhóm dưới 3 người không hiện số.

**Sĩ Số +1 lưu thêm gì?**
Cũng 5 câu vô hại và ô đồng ý như trên, không tick sẵn. Kẻ Bị Nhập có thể chọn một câu trả lời của bạn để "con ma" đọc lên màn
hình chung. Cuối buổi, màn hình giải thích con ma biết bằng cách nào: câu nào đã được đọc, và câu đó do "một Kẻ Bị Nhập" chọn.
Biệt danh của người chọn chỉ hiện khi chính người đó tự bật lúc lật. Mọi thứ bị xoá khi buổi kết thúc. Bạn có thể chọn "chỉ xem"
để không nhận vai.

**Tam Sao Thất Bản lưu gì?**
Biệt danh và các lựa chọn của bạn trong chuỗi: ý định, cách diễn đạt, mood và câu đoán, đều chọn từ ngân hàng câu soạn sẵn, cùng
thời điểm chọn. Phòng trực tiếp xoá khi phòng kết thúc. Bản nhóm chat dùng một link nhóm; máy chủ chỉ lưu bản băm của link. Các
chuỗi bị xoá 48 giờ sau màn lật. Khi phát lại, bước bạn chọn hiện là "Người chơi A, B…", trừ khi bạn tick ô hiện biệt danh ở bước
của mình. Biệt danh của bạn chỉ nằm trên thẻ lật khi bạn tick một ô riêng. Hai ô này không tick sẵn và bỏ tick được tới trước giờ
lật. Thẻ lật chỉ có biệt danh của người đã đồng ý và câu trong ngân hàng. Người chơi khác có thể lưu hoặc gửi thẻ lật; ảnh đã gửi
thì không thu lại được. Báo cáo trong bản nhóm chat không lưu người báo cáo và bị xoá cùng ván.

**Hết Cứu % lưu gì?**
Nhóm có 4–12 người, vào bằng link mời riêng mà host thu hồi được. Lá Úp lưu biệt danh và một mã ngẫu nhiên gắn với trình duyệt
của bạn. Mỗi sự kiện tuần, Lá Úp lưu % bạn tự khai cho từng mức, thẻ "lời khai" bạn chọn, phiếu đoán và số lá bạn đặt, cùng các
lựa chọn tuỳ ý: tình nguyện làm Nhân Vật Chính, "ẩn % của tôi", "tuần này đừng đoán tôi". "Lá" chỉ dùng trong một sự kiện, không
mua được, không đổi được, không cộng dồn *(chờ owner chốt, D3)*. % và phiếu đoán bị xoá 72 giờ sau màn lật tối thứ Sáu. Nhóm chỉ
giữ danh hiệu và khoảnh khắc của từng sự kiện tới hết mùa cộng 30 ngày, rồi xoá. Không ai thấy ai đã đoán ai. Nếu hết mùa cộng 30
ngày mà nhóm không mở mùa mới, nhóm và danh sách thành viên bị xoá *(chờ owner, HC-D4)*. Mã gắn trình duyệt bị xoá sau 120 ngày
không dùng. Báo cáo không lưu người báo cáo và bị xoá sau 30 ngày hoặc khi đã xử lý xong.

**Thông báo của Hết Cứu %**
Chỉ khi bạn tự bật. Tối đa một thông báo mỗi tuần cho mỗi nhóm; bạn chọn nhận lúc sự kiện mới lên (thứ Hai) hoặc lúc lật kết quả
(thứ Sáu). Lá Úp lưu địa chỉ nhận thông báo của trình duyệt tới khi bạn tắt hoặc rời nhóm. Thông báo đi qua dịch vụ đẩy của hãng
làm trình duyệt bạn đang dùng (Apple, Google hoặc Mozilla). Nội dung thông báo là câu cố định, không có biệt danh, con số hay kết
quả. Tam Sao Thất Bản, Phiên Tòa Tủ Lạnh và Sĩ Số +1 không gửi thông báo nào.

**Cầu nối sang Lá Lành**
Mỗi trò có một lối tuỳ chọn sang Lá Lành: lá tarot của tuần (Hết Cứu %), chú thích Sao Thủy (Tam Sao), lá Công Lý (Phiên Tòa).
Bạn phải bấm đồng ý trước khi mở. Lá Úp **không** gửi biệt danh, câu trả lời, mã phòng hay bất kỳ dữ liệu game nào sang Lá Lành.
Nếu bạn dùng tính năng cá nhân của Lá Lành, Lá Lành sẽ hỏi bạn riêng theo chính sách của Lá Lành.

**Dữ liệu đi đâu?**
Dữ liệu được truyền từ Việt Nam tới máy chủ Hetzner tại Đức và lưu trong cơ sở dữ liệu Supabase tại Frankfurt, Đức. Lá Úp không
bán dữ liệu và không dùng cho quảng cáo. Lá Úp không dùng AI.

**Lá Úp bảo vệ dữ liệu thế nào?**
Kết nối dùng HTTPS/TLS. Link phòng, link nhóm và link mời không được lập chỉ mục, không lưu cache, không gửi địa chỉ trang sang
trang khác, có hạn và thu hồi được. Log lỗi không chứa biệt danh, câu trả lời hay mã truy cập. Số lần đoán mã phòng bị giới hạn.

**Quyền của bạn**
Bạn có quyền được biết, đồng ý, rút đồng ý, xem, sửa, yêu cầu xoá và phản đối việc xử lý dữ liệu của mình *(counsel điền căn cứ
theo Luật 91/2025/QH15 và Nghị định 356/2025/NĐ-CP)*. Vì Lá Úp không có tài khoản, cách nhanh nhất là làm ngay trong game:

- Rời phòng hoặc rời nhóm bất cứ lúc nào.
- Bỏ tick ô đồng ý hoặc tắt thông báo.
- Bấm "Xoá dữ liệu của tôi" hoặc xem "Dữ liệu của tôi" trong nhóm Hết Cứu % (HC-FR-49, HC-FR-50).

Lá Úp không xác minh được bạn qua email khi không có tài khoản, nên yêu cầu gửi qua email có thể cần bạn mở lại link nhóm trên
chính máy đó *(chờ counsel, Q-2)*.

**Độ tuổi**
Lá Úp dành cho người từ 18 tuổi.

**Liên hệ về dữ liệu**
[Dùng cùng kênh liên hệ đang ghi ở trang `/privacy` của Lá Lành.] Không gửi mật khẩu hay mã truy cập trong email.

**Phiên bản:** `la-up-privacy-v1` *(đề xuất)*, ngày hiệu lực [khi ra mắt].

## 6. Lời giải thích và màn đồng ý trong app — bản nháp

Quy tắc chung cho mọi màn:

- Mỗi mục đích một ô riêng, **không tick sẵn**. Không gộp với điều khoản hay nội dung khác (Google prominent disclosure; Nghị định
  356 cấm "mặc định đồng ý").
- Nút từ chối có cùng độ nổi với nút đồng ý. Bấm quay lại hay bấm ra ngoài **không** được coi là đồng ý.
- Từ chối không chặn trải nghiệm chính khi mục đích đó không bắt buộc (ví dụ không tick ô 5 câu thì vẫn chơi được).
- Câu ngắn, có chủ thể, nói rõ ai thấy gì và giữ bao lâu, theo chuẩn nội dung tiếng Việt dễ hiểu.
- Mã phiên bản đồng ý dưới đây là **đề xuất**. SRS của từng trò chốt tên cuối cùng.
- **Bản chuẩn của câu chữ nằm trong SRS:** RP §8.1 (vào phòng), SRS Tam Sao §8.2 (C-TS-01…06), SRS Hết Cứu % §8.2 (C-HC-00…05),
  SRS Tri Kỷ §7 và PRD Tri Kỷ §5. Các màn dưới đây là bản tóm tắt cho store và chính sách. Khi lệch, sửa theo SRS rồi cập nhật cả
  DPIA và tài liệu này trong cùng một PR (RP-PRV-09).

### 6.1 Vào phòng Lá Úp (chung cho bốn trò)

> **Vào phòng**
> Đặt một biệt danh để mọi người trong phòng nhận ra bạn. Đừng dùng họ tên đầy đủ.
>
> [ô nhập biệt danh, 2–20 ký tự]
>
> ☐ Tôi từ 18 tuổi trở lên.
>
> Lá Úp lưu biệt danh, vai, phiếu bầu của bạn tới khi phòng kết thúc, muộn nhất 2 giờ. Không cần tài khoản, ngày sinh hay danh bạ.
> [Đọc chính sách quyền riêng tư]
>
> [Vào phòng]  [Chỉ xem]

Ghi chú: ô 18+ là điều kiện để vào phòng (tự khai tuổi). Nút "Vào phòng" chỉ bật khi đã tick. Nếu Lá Úp vào app, đây là cơ chế
giới hạn tuổi theo tuổi tự khai của Guideline 4.7.5.

### 6.2 Phiên Tòa Tủ Lạnh

> **Câu trả lời của bạn có thể thành manh mối**
> Game sẽ hỏi 5 câu vô hại: bữa sáng, bài hát nghe gần nhất, ngồi gần cửa sổ hay cửa ra vào, màu áo, một món trong túi.
> Nếu bạn là Thủ Phạm, câu trả lời của bạn sẽ hiện trên màn hình chung như manh mối. Cả phòng đều thấy.
>
> ☐ Câu trả lời của tôi có thể hiện trên màn hình chung.
>
> Không tick: bạn vào ở chế độ chỉ xem. Game không hỏi 5 câu, bạn không nhận vai, vẫn xem và bỏ phiếu khán giả nếu phòng cho phép.
> Đã tick vẫn chọn được "Không muốn nói" cho từng câu.
> Mọi câu trả lời bị xoá khi tòa tiêu huỷ hồ sơ cuối buổi.
>
> [Tiếp tục]

Thông báo ngắn ở màn tuyên án:

> Phán quyết dành cho vai trong game, không dành cho người thật. Bản án là trò đùa, ai cũng bấm "Miễn án" được.

### 6.3 Sĩ Số +1

> **Câu trả lời của bạn có thể được "con ma" đọc lên**
> Game sẽ hỏi 5 câu vô hại: bữa sáng, bài hát nghe gần nhất, ngồi gần cửa sổ hay cửa ra vào, màu áo, một món trong túi.
> Kẻ Bị Nhập có thể chọn một câu của bạn để con ma đọc trên màn hình chung. Cuối buổi, màn hình cho biết câu nào đã được đọc và nói
> "một Kẻ Bị Nhập đã chọn". Tên người chọn chỉ hiện khi chính họ tự bật.
>
> ☐ Câu trả lời của tôi có thể hiện trên màn hình chung.
>
> Không tick: bạn vào ở chế độ chỉ xem. Game không hỏi 5 câu và không ai chọn được câu của bạn.
> Mọi câu trả lời bị xoá khi buổi kết thúc.
>
> [Tiếp tục]  [Chỉ xem]

Thông báo ngắn ở màn lật mặt:

> Con ma không biết gì cả. Nó chỉ đọc lại câu mà người chơi đã chọn. Bây giờ hồ sơ sẽ bị tiêu huỷ.

### 6.4 Tam Sao Thất Bản

Phòng trực tiếp: màn vào phòng dùng bản rút gọn của RP §8.1 (ô 18+; biệt danh có thể hiện ở sảnh và danh sách người chơi). Hiện
biệt danh cạnh từng bước khi phát lại cần một ô riêng, và tên trên thẻ lật cần thêm một ô riêng nữa (`ts-live-v1`, SRS Tam Sao §8.2):

> Khi phát lại, Tam Sao Thất Bản cho cả phòng xem từng câu đã đi qua chuỗi.
> ☐ Hiện biệt danh của tôi ở bước tôi đã chọn khi phát lại. *(Không tick: hiện "Người chơi A, B…")*
> ☐ Cho biệt danh của tôi nằm trên thẻ lật. Ai trong phòng cũng có thể tải thẻ và gửi ra ngoài; ảnh đã gửi thì không thu lại được.

Bản nhóm chat (chỉ khi D4 cho vào MVP):

> **Chơi qua link nhóm**
> Link này mở lượt chơi cho cả nhóm. Gửi đúng nhóm, đừng đăng công khai. Host thu hồi link được.
> Các chuỗi bị xoá 48 giờ sau màn lật. Thẻ lật chỉ có biệt danh của người đã đồng ý và câu trong ngân hàng.
> ☐ Hiện biệt danh của tôi ở bước tôi đã chọn khi lật. *(không bắt buộc)*
> ☐ Cho biệt danh của tôi nằm trên thẻ lật. Ảnh đã gửi ra ngoài thì không thu lại được. *(không bắt buộc)*
>
> [Nhận lượt]

Bản đầy đủ có ô 18+ và ô đồng ý lưu dữ liệu: C-TS-02 (SRS Tam Sao §8.2).

### 6.5 Hết Cứu %

Vào nhóm:

> **Vào nhóm Hết Cứu %**
> Mỗi tuần một sự kiện bựa. Bạn tự khai %, cả nhóm đoán. Tối thứ Sáu lật kết quả trong nhóm.
> Nhóm thấy: biệt danh, % bạn khai (trừ khi bạn chọn ẩn), thẻ lời khai, danh hiệu. Nhóm không bao giờ thấy ai đã đoán ai.
> % và phiếu đoán bị xoá 72 giờ sau màn lật. Danh hiệu và khoảnh khắc giữ tới hết mùa cộng 30 ngày.
>
> ☐ Tôi từ 18 tuổi trở lên.
> ☐ Tôi đồng ý cho Lá Úp lưu và dùng các dữ liệu trên để chơi trong nhóm này.
>
> [Vào nhóm]  [Không vào]

Bản đầy đủ: C-HC-01 (`hc-join-v1`, SRS Hết Cứu % §8.2).

Trên màn tự khai, ngay cạnh nút gửi (mặc định tắt):

> ☐ Ẩn % của tôi. Nhóm chỉ thấy cao, vừa hay thấp.
> ☐ Tuần này đừng đoán tôi.
> ☐ Tôi tình nguyện làm Nhân Vật Chính tuần này. Cả nhóm sẽ ước lượng % của tôi ở mức 3.

Thông báo (một màn riêng, chỉ hiện khi người chơi bấm "Nhắc tôi khi có sự kiện mới"):

> **Nhận một thông báo mỗi tuần?**
> Chọn một lúc: ○ Khi sự kiện mới lên (thứ Hai 9:00) ○ Khi lật kết quả (thứ Sáu 20:00)
> Tối đa một thông báo mỗi tuần cho nhóm này. Thông báo là câu cố định, không có biệt danh, con số hay kết quả.
> Lá Úp lưu địa chỉ nhận thông báo của trình duyệt tới khi bạn tắt. Tắt bất cứ lúc nào trong nhóm.
>
> ☐ Tôi muốn nhận thông báo này.

Bản đầy đủ: C-HC-04 (`hc-push-v1`, SRS Hết Cứu % §8.2), có thêm câu về dịch vụ đẩy và về iPhone (chỉ chạy khi đã thêm vào Màn hình chính).
>
> [Lưu]  [Để sau]

Sau đó trình duyệt mới hiện hộp xin quyền của hệ thống.

### 6.6 Cầu nối sang Lá Lành (mỗi trò một lối)

> **Mở Lá Lành?**
> Bạn sắp mở [lá tarot của tuần / chú thích Sao Thủy / lá Công Lý] trong Lá Lành.
> Lá Úp không gửi biệt danh, câu trả lời hay mã phòng sang Lá Lành. Nếu bạn muốn bản đọc cá nhân, Lá Lành sẽ hỏi bạn riêng.
>
> [Mở Lá Lành]  [Ở lại]

Yêu cầu kỹ thuật đi kèm (cho SRS): URL đích không có tham số mang mã phòng, biệt danh hay mã định danh duy nhất;
`Referrer-Policy: no-referrer`. Hành động bấm "Mở Lá Lành" là đồng ý cho đúng lần mở đó. Không lưu bản ghi đồng ý, vì không có dữ
liệu cá nhân nào đi qua.

### 6.7 Tri Kỷ (trong Lá Lành)

A mở Tri Kỷ:

> **Tri Kỷ**
> Tri kỷ là người hiểu mình — không phải chuyện yêu đương, không có bảng xếp hạng.
> Bạn mời một người. Khi người đó đồng ý, hai bạn nhận một lá đôi. Chỉ hai bạn thấy.
>
> Lá còn tới khi một trong hai người giải tán.
>
> Lá đôi là dữ liệu nhạy cảm vì nó nói về đời sống riêng tư của hai bạn. Lá Lành chỉ tạo khi cả hai cùng đồng ý, và chỉ hai bạn xem được.
> ☐ Dùng hồ sơ sinh của tôi để tạo lá Tri Kỷ với người tôi mời.
>
> [Tạo lời mời]

Câu "dữ liệu nhạy cảm" nằm **ngay trên** ô, không có nội dung nào chen giữa (FR-TK-005). Câu là nháp, chờ owner duyệt; counsel xem
có đủ cho Nghị định 356 Điều 6 khoản 4 không. Phải qua test copy T-TK-23 trước khi build.

Trước khi gửi (preview lời mời, theo US-08):

> Người nhận sẽ thấy: biệt danh [biệt danh A] mời họ tạo lá Tri Kỷ. Link không chứa ngày sinh của bạn.
> Link có hạn, bạn thu hồi được. Gửi cho đúng một người.

B mở link:

> **[Biệt danh A] mời bạn tạo lá Tri Kỷ**
> Nếu đồng ý, Lá Lành dùng thông tin sinh trong hồ sơ của **bạn** để tạo lá đôi. [Biệt danh A] không thấy ngày, giờ hay nơi sinh
> của bạn. Chỉ hai bạn thấy lá đôi.
>
> Lá đôi là dữ liệu nhạy cảm vì nó nói về đời sống riêng tư của hai bạn. Lá Lành chỉ tạo khi cả hai cùng đồng ý, và chỉ hai bạn xem được.
> ☐ Dùng thông tin sinh của tôi cho lá Tri Kỷ với [biệt danh A].
>
> [Đồng ý]  [Không, cảm ơn]

Màn của B dùng cùng câu, cũng đặt ngay trên ô (FR-TK-033); thiếu câu thì nút "Đồng ý" không bật.

Nếu B chưa có hồ sơ, B đi qua màn đồng ý hồ sơ sinh hiện có của Lá Lành (`birth-profile-v1`) trước, rồi mới thấy ô Tri Kỷ.
Hai đồng ý tách riêng.

Hiểu Nhau Không?:

> 7 câu vô hại. Bạn trả lời cho mình và đoán câu của người kia.
> Câu trả lời gắn với hai bạn nên Lá Lành xử lý như dữ liệu nhạy cảm.
> ☐ Lưu câu trả lời của tôi cho lượt chơi này. Câu trả lời bị xoá khi cả hai bạn đã xem kết quả, muộn nhất 7 ngày sau khi lượt xong; chỉ giữ kỷ lục của hai bạn.
>
> [Bắt đầu]

Chia sẻ ảnh:

> Ảnh lá đôi có biệt danh của hai bạn, không có thông tin sinh. Ảnh chỉ chia được khi cả hai cùng đồng ý. Ảnh đã chia ra ngoài
> thì Lá Lành không thu lại được. Lá Lành ghi lại bạn đã đồng ý cho ảnh này (không lưu ảnh) tới khi lá bị giải tán.
>
> ☐ Tôi đồng ý chia sẻ ảnh lá đôi này.
>
> [Gửi yêu cầu cho [biệt danh B]]

Giải tán:

> **Giải tán lá Tri Kỷ?**
> Lá và mọi dữ liệu của cặp sẽ bị xoá, kể cả kỷ lục Hiểu Nhau Không?. [Biệt danh B] không nhận thông báo, nhưng sẽ không còn thấy lá.
>
> [Giải tán]  [Giữ lại]

### 6.8 Màn "tiêu huỷ hồ sơ" (Phiên Tòa, Sĩ Số +1, Tam Sao trực tiếp)

> **Hồ sơ đã tiêu huỷ**
> Biệt danh, câu trả lời, vai và phiếu bầu của buổi này đã bị xoá. Lá Úp chỉ giữ số đếm chung, không nhận ra ai.

## 7. Ma trận nhất quán

Ký hiệu: **RT** = runtime dự kiến (hợp đồng dữ liệu); **App** = lời giải thích trong app (mục 6); **CS** = chính sách (mục 5);
**Apple** = nhãn App Privacy (mục 3; với Lá Úp là bảng khai sẵn 3.4); **Google** = Data safety (mục 4; với Lá Úp là bảng khai sẵn 4.3).
"—" nghĩa là không thu, nên không khai.

### 7.1 Chung cho phòng Lá Úp

| Trường | RT: lưu bao lâu | App | CS | Apple | Google |
|---|---|---|---|---|---|
| `room_id` | Tới khi phòng kết thúc, muộn nhất 2 giờ | — (nội bộ) | "Phòng giữ dữ liệu bao lâu?" | Gắn vào Gameplay Content, không khai riêng | Gắn vào Other actions |
| Mã phòng 6 ký tự + token năng lực đã băm trong URL | Như trên; giới hạn số lần đoán | 6.1 (gián tiếp) | "Khi vào phòng…", "bảo vệ" | Không phải dữ liệu người dùng | Không phải dữ liệu người dùng |
| `host_session` | Như trên | — | "mã ngẫu nhiên gắn với trình duyệt" | Device ID | Device or other IDs |
| `player_session` | Như trên | — | Như trên | Device ID | Device or other IDs |
| `nickname` | Như trên | 6.1 | "Khi vào phòng…" | User ID | Personal info → Name |
| Vai được chia | Như trên | 6.1 | Như trên | Gameplay Content | Other actions |
| Phiếu bầu | Như trên | 6.1 | Như trên | Gameplay Content | Other actions |
| Mốc thời gian | Như trên | — | Như trên | Gameplay Content | Other actions |
| Bản ghi đồng ý (`consent_display`, phiên bản câu chữ, thời điểm) **[bổ sung]** | Rời/kick/kết thúc; sau buổi chỉ giữ phiên bản câu chữ và số đếm theo ngày (RP-D5, Q-2) | 6.1–6.3 | "Khi vào phòng…" | Gameplay Content | Other actions |
| Bản ghi báo cáo (loại, slot bị báo cáo, mã nội dung) **[bổ sung]** | Xoá khi kết thúc; chỉ giữ số đếm theo loại và mã nội dung; không lưu người gửi | — | "Phòng giữ dữ liệu bao lâu?" (số lượt báo cáo) | Gameplay Content | Other actions |
| Khoá giới hạn tần suất (hash IP có muối xoay theo ngày + phiên trình duyệt) **[bổ sung]** | Chỉ trong bộ nhớ, tối đa 24 giờ, không ghi log | — | "bảo vệ" (giới hạn đoán mã) | Không lưu quá một ngày; counsel xem có cần khai (Q-5) | Fraud prevention (nếu phải khai) |
| Log lỗi thô (không biệt danh/câu trả lời/token) | Theo chính sách log của host (Q-5) | — | "bảo vệ" | Other Diagnostic Data, Not linked | Diagnostics |
| Số đếm tổng hợp | Theo DPIA X7 (mặc định chỉ ghi ở đó, chờ owner), không định danh, ẩn ô < 3 (KS-04) | 6.8 | "Phòng giữ dữ liệu bao lâu?" | Product Interaction, Not linked, Analytics | App interactions, Analytics |

### 7.2 Phiên Tòa Tủ Lạnh

| Trường | RT | App | CS | Apple | Google |
|---|---|---|---|---|---|
| 5 câu tự khai | Xoá khi hết buổi | 6.2 | "Phiên Tòa… lưu thêm gì?" | Gameplay Content | Other user-generated content (Optional) |
| Cờ đồng ý "hiện trên màn hình chung" (mặc định tắt) | Xoá khi hết buổi (Q-2) | 6.2 | Như trên | Gameplay Content | Other user-generated content |
| Lượt dùng "Phản đối!" | Xoá khi hết buổi | — | Như trên | Gameplay Content | Other actions |
| Số đếm trên màn hình chung (ẩn nhóm dưới 3 người, PT-PRV-03) | Chỉ hiện trong buổi | 6.2, 6.8 | Như trên | Không lưu riêng | Không lưu riêng |
| + mọi trường chung ở 7.1 | | | | | |

### 7.3 Sĩ Số +1

| Trường | RT | App | CS | Apple | Google |
|---|---|---|---|---|---|
| 5 câu tự khai | Xoá khi hết buổi | 6.3 | "Sĩ Số +1 lưu thêm gì?" | Gameplay Content | Other user-generated content (Optional) |
| Cờ đồng ý (mặc định tắt) | Xoá khi hết buổi (Q-2) | 6.3 | Như trên | Gameplay Content | Other user-generated content |
| Lời thì thầm (Kẻ Bị Nhập chọn câu nào) | Xoá khi hết buổi; màn lật nêu câu và "một Kẻ Bị Nhập", không nêu tên trừ khi người đó tự bật (SS-D10, DP-1) | 6.3 | Như trên | Gameplay Content | Other actions |
| Công tắc "Hiện tên tôi ở lời thì thầm" (mặc định tắt) | Chỉ trong màn lật | 6.3 | Như trên | Gameplay Content | Other actions |
| Bản sao ghép (số đếm, ẩn phương án dưới 3 người, SS-FR-81) | Tính lúc lật, không lưu | — | Như trên | Không lưu riêng | Không lưu riêng |
| Chế độ "bật đèn" (D6) | Cấu hình phòng, không phải dữ liệu cá nhân | — | — | — | — |
| + mọi trường chung ở 7.1 | | | | | |

### 7.4 Tam Sao Thất Bản

| Trường | RT | App | CS | Apple | Google |
|---|---|---|---|---|---|
| `nickname` | Trực tiếp: xoá khi hết phòng. Chat: xoá cùng chuỗi, 48 giờ sau màn lật | 6.1, 6.4 | "Tam Sao… lưu gì?" | User ID | Name |
| Bước trong chuỗi (mã ý định, mã cách diễn đạt, mã mood, mã câu đoán) | Như trên | 6.4 | Như trên | Gameplay Content | Other actions |
| Mốc thời gian | Như trên | — | Như trên | Gameplay Content | Other actions |
| Hai cờ hiện biệt danh `show_name_on_screen`, `show_name_on_card` (không tick sẵn) **[bổ sung]** | Như `nickname` | 6.4 | Như trên | Gameplay Content | Other actions (Optional) |
| `ts_report` (bản chat; biệt danh bị báo cáo nếu có) **[bổ sung]** | Tới khi ván bị xoá (lật + 48 giờ); sau đó chỉ mã nội dung + số đếm; không lưu người báo cáo | — | Như trên | Gameplay Content | Other actions |
| Link nhóm (token năng lực đã băm, bản chat) | Tới khi host thu hồi hoặc ván bị xoá (lật + 48 giờ, hoặc host "Kết thúc và xoá") | 6.4 | Như trên | Không phải dữ liệu người dùng | Không phải dữ liệu người dùng |
| Thẻ lật (biệt danh của người đã tick `show_name_on_card` + câu trong ngân hàng) | Không lưu trên máy chủ sau khi xoá chuỗi; bản người chơi tự lưu thì nằm ngoài tầm kiểm soát | 6.4 | Như trên | Bản dựng trên máy chủ: Gameplay Content | Other actions; chia qua share sheet là do người dùng chủ động |

### 7.5 Hết Cứu %

| Trường | RT | App | CS | Apple | Google |
|---|---|---|---|---|---|
| Nhóm (4–12) + link mời riêng, thu hồi được | Nhóm: hết mùa + 30 ngày nếu không có mùa mới, hoặc host xoá (HC-FR-45, HC-D4 **[bổ sung]**, chờ owner). Link mời: tới hết hạn/thu hồi + 7 ngày | 6.5 | "Hết Cứu % lưu gì?" | Không phải dữ liệu người dùng (token đã băm) | — |
| Phiên thành viên (gắn thiết bị) | Tới khi rời nhóm / nhóm bị xoá; phiên thiết bị xoá sau 120 ngày không hoạt động **[bổ sung]** | — | Như trên | Device ID | Device or other IDs |
| `nickname` | Như trên | 6.5 | Như trên | User ID | Name |
| % từng mức (bước 5%) | Xoá 72 giờ sau màn lật thứ Sáu | 6.5 | Như trên | Gameplay Content | Other actions |
| Mã thẻ "lời khai" | 72 giờ sau màn lật | 6.5 | Như trên | Gameplay Content | Other actions |
| Phiếu đoán + số lá đặt | 72 giờ sau màn lật | 6.5 | Như trên | Gameplay Content | Other actions |
| Cờ tình nguyện Nhân Vật Chính | 72 giờ sau màn lật (Q-12) | 6.5 | Như trên | Gameplay Content | Other actions (Optional) |
| "Ẩn % của tôi", "tuần này đừng đoán tôi" | 72 giờ sau màn lật (Q-12) | 6.5 | Như trên | Gameplay Content | Other actions (Optional) |
| Danh hiệu và khoảnh khắc từng sự kiện | Hết mùa + 30 ngày | 6.5 | Như trên | Gameplay Content | Other actions |
| `hc_report` (biệt danh bị báo cáo nếu có) **[bổ sung]** | 30 ngày hoặc khi xử lý xong; không lưu người báo cáo | — | "Hết Cứu % lưu gì?" | Gameplay Content | Other actions |
| `hc_reaction_count` (số đếm cảm xúc, không gắn thành viên) **[bổ sung]** | Lật + 72 giờ | — | — (không phải dữ liệu cá nhân) | Không khai riêng | Không khai riêng |
| Endpoint web push, khoá `p256dh`, `auth` (chỉ khi tự bật) | Tới khi tắt, rời nhóm, nhóm bị xoá, hoặc dịch vụ đẩy trả 404/410. Bên nhận: dịch vụ đẩy của hãng trình duyệt (DPIA §15, Q13) | 6.5 | "Thông báo của Hết Cứu %" | Device ID | Device or other IDs (Optional; Shared: Q-7) |

### 7.6 Tri Kỷ (trong Lá Lành)

| Trường | RT | App | CS | Apple | Google |
|---|---|---|---|---|---|
| Hồ sơ sinh của A (hồ sơ A tự đồng ý) | Theo thời hạn hồ sơ Lá Lành; dùng cho lá khi A đồng ý mục đích Tri Kỷ | 6.7 (A) | 5.1 "dùng dữ liệu gì?" | Other User Content + Precise Location (có sẵn) | Other info + Precise location (có sẵn) |
| Hồ sơ sinh của B (hồ sơ B tự đồng ý) | Như trên, với B | 6.7 (B) | Như trên | Như trên | Như trên |
| Bản ghi mời/nhận | Lời mời chờ 7 ngày, thu hồi được; hàng lời mời đã kết thúc giữ 30 ngày **[bổ sung]** (TK SRS §8); bản ghi cặp tới khi giải tán | 6.7 (preview) | "Lời mời hoạt động thế nào?" | User ID, Other User Content | User IDs, App interactions |
| Tên hiển thị (A chọn cho lời mời; mỗi người chọn trong cặp) **[bổ sung]** | Như lời mời / tới khi giải tán | 6.7 | Như trên | Other User Content | Name |
| Danh sách chặn của B (HMAC người mời, tên A lúc bị chặn, mã hoá) **[bổ sung]** | Tới khi bỏ chặn hoặc hồ sơ người chặn bị xoá | — (cần thêm một câu ở 5.1) | "Lời mời hoạt động thế nào?" | Other User Content | App interactions |
| Báo cáo lời mời **[bổ sung]** | 30 ngày; không lưu IP, thiết bị, token | — | Như trên | Other User Content | App interactions |
| Lá đôi (dữ liệu suy luận, nhạy cảm) | Tới khi một người giải tán; giải tán = xoá cứng, không báo người kia | 6.7 | "Ai thấy…", "Giữ bao lâu…" | Other Data Types | Other info |
| Hàng yêu cầu chia sẻ (vận hành: người xin, trạng thái, hạn) | 72 giờ chờ, 24 giờ xuất; hàng xoá 7 ngày sau trạng thái cuối (TK SRS §8) | 6.7 (chia sẻ) | "Ai thấy lá đôi?" | Other User Content | App interactions |
| Bằng chứng đồng ý chia sẻ của từng người (`tri_ky_share_consents`: thành viên, thời điểm, phiên bản câu chữ, `layout_version`, `card_hash`; không ảnh) | Khi lá còn; xoá khi giải tán hoặc xoá hồ sơ. Giữ lâu hơn hay không: chờ counsel (Q-16) | 6.7 (chia sẻ) | "Ai thấy lá đôi?" | Other User Content | App interactions |
| Câu trả lời Hiểu Nhau Không? (mã lựa chọn, gắn với cặp, **dữ liệu nhạy cảm**) | Xoá ngay khi cả hai đã xem kết quả, muộn nhất 7 ngày sau khi lượt hoàn tất; lượt không đủ hai người xoá sau 7 ngày; giải tán xoá hết | 6.7 (trò đố) | "Hiểu Nhau Không? lưu gì?" | Gameplay Content (**mới**) | Other actions (**mới**) |
| Kỷ lục của cặp (`quiz_best_score` x/7, `quiz_best_month` **[bổ sung]**) | Khi cặp còn; tắt trò đố hoặc giải tán thì xoá; không có điểm riêng từng người | 6.7 | Như trên | Gameplay Content | Other actions |
| Bản ghi đồng ý mục đích Tri Kỷ (`tri-ky-pair-v1`, trên hàng cặp) | Tới khi giải tán hoặc xoá hồ sơ. Giữ lâu hơn hay không: chờ counsel (Q-16) | 6.7 (câu "dữ liệu nhạy cảm" ngay trên ô) | "Vì sao cần đồng ý riêng?" | Other User Content | App interactions |
| Bộ đếm tổng hợp theo ngày (danh sách ở TK SRS §10; không ID, không nội dung) | Theo DPIA X7 (chờ owner); ẩn ô < 3, báo cáo chỉ ô ≥ 10 | — | "Ai thấy lá đôi?" (chỉ đếm tổng số) | **Chưa chốt (Q-9):** (A) không khai; (B) Product Interaction, Not Linked, Analytics. Đề xuất (B) | **Chưa chốt (Q-9):** (A) không khai; (B) thêm Analytics vào App interactions. Đề xuất (B) |
| Analytics theo người, analytics nội dung, nội dung thông báo, ảnh xem trước link | **Không có** | — | "Ai thấy lá đôi?" | — | — |

## 8. Việc cần sửa ở file hiện có (chưa sửa trong đợt này)

| # | File | Sửa gì | Khi nào |
|---|---|---|---|
| F-1 | `docs/legal/store-privacy-data-map.md` | Thêm mục "Game line delta (draft)" trỏ về tài liệu này: (a) bảng Apple thêm hàng `User Content → Gameplay Content` cho Hiểu Nhau Không? và mở rộng mô tả các hàng Other Data Types / Other User Content / Product Interaction cho Tri Kỷ; (b) bảng Google thêm `Personal info → Name` và `App activity → Other actions`, đổi hàng Radar từ "Personal info / User-generated content" sang `Personal info → Name` cho biệt danh để thống nhất; (c) một câu "Lá Úp is web-only and outside App Privacy / Data safety until packaged or embedded"; (d) thêm câu hỏi social graph (Q-3) cho cả Radar invite; (e) thêm Guideline 4.7 và trang account deletion (answer 13327111) vào "Official sources" | Khi Tri Kỷ vào sprint, cùng PR với SRS đã duyệt |
| F-2 | `docs/legal/store-privacy-data-map.md` | Ghi link web yêu cầu xoá tài khoản mà Play Console bắt buộc cho app có tài khoản. Nếu chưa có link, đây là gate trước khi phát hành native (không riêng game) | Trước lần nộp Play tiếp theo |
| F-3 | `apps/mobile/ios/App/App/PrivacyInfo.xcprivacy` | Thêm `NSPrivacyCollectedDataTypeGameplayContent` (Linked true, Tracking false, Purpose AppFunctionality) | Cùng PR runtime của Hiểu Nhau Không? |
| F-4 | `apps/web/src/features/consent/ConsentPage.tsx` | Thêm một `<details>` "Tri Kỷ" theo mục 5.1 (rút gọn còn một đoạn, trỏ sang trang chính sách đầy đủ nếu F-5 làm) | Cùng PR runtime Tri Kỷ; owner duyệt copy |
| F-5 | `apps/web/src/features/consent/ConsentPage.tsx` / route `/privacy` | **Có trước dòng game.** Google yêu cầu privacy policy gắn nhãn rõ "privacy policy", công khai, có thông tin nhà phát triển. Trang hiện có tiêu đề "Lá Lành dùng dữ liệu thế nào?", không nêu pháp nhân. Cần một trang "Chính sách quyền riêng tư" công khai (hoặc đổi tiêu đề), có tên bên kiểm soát dữ liệu, và dùng URL đó trong App Store Connect và Play Console | Giai đoạn 1 (privacy); owner và counsel |
| F-6 | `docs/legal/2026-10-22-privacy-counsel-dossier.md` | Thêm các câu hỏi Q-1 đến Q-12 ở mục 9 vào phần câu hỏi cho counsel, kèm tham chiếu DPIA game | Khi chuyển gói câu hỏi cho counsel |
| F-7 | `apps/web/public/_headers` (Lá Lành) và file header tương đương của bề mặt Lá Úp | Link mời đặt token trong fragment, nên request HTTP chỉ tới **đúng đường không có token**. Tri Kỷ: link `/tri-ky/i#<token>` → request tới `/tri-ky/i` (không dấu `/` cuối, token không nằm trong path; TK SRS §9). Luật header phải khớp **chính xác** `/tri-ky/i` (thêm `/tri-ky/i/` nếu router chuẩn hoá dấu `/`, và mọi route con thật nếu SRS thêm sau); mẫu `/tri-ky/i/*` một mình **không** khớp `/tri-ky/i`. Header: `Cache-Control: no-store, max-age=0`, `Referrer-Policy: no-referrer`, `X-Robots-Tag: noindex, nofollow, noarchive`. Lá Úp, cùng luật đường chính xác: `/j` (Hết Cứu %, HC-FR-05), `/t` (Tam Sao bản chat, TS-FR-16), trang vào phòng và trang màn chiếu (RP-FR-04, RP-FR-05; tên đường chốt khi build). Kiểm riêng, **không** thay bằng kiểm header API: (1) HTML cuối cùng trả cho trình duyệt; (2) mọi redirect và trang lỗi trên các đường đó; (3) service worker không cache và không trả từ cache các đường đó (kể cả app shell/navigation fallback); (4) header API (`/v1/public/tri-ky/*`, `POST /join/preview`…) kiểm riêng | Cùng PR runtime |
| F-8 | `docs/legal/privacy-security-flow-notes.md` | Thêm một dòng "Game line" trỏ tới DPIA và tài liệu này; ghi rằng câu 18+ của Lá Úp là tuổi tự khai, không phải xác minh tuổi | Tuỳ chọn, cùng F-1 |

## 9. Câu hỏi mở

| # | Câu hỏi | Cho ai | Đề xuất mặc định |
|---|---|---|---|
| Q-1 | Lá đôi Tri Kỷ là dữ liệu **suy luận** về quan hệ. Theo Điều 4 Nghị định 356, nó có thuộc nhóm "đời sống riêng tư" (nhạy cảm) không? | Counsel | Xử lý như nhạy cảm cho tới khi có câu trả lời |
| Q-2 | Điều 6 Nghị định 356 đặt trách nhiệm chứng minh đồng ý lên bên kiểm soát. Người chơi Lá Úp không có tài khoản, và dữ liệu phòng (cả cờ đồng ý) bị xoá khi hết buổi. Giữ bằng chứng thế nào mà không giữ dữ liệu cá nhân? Yêu cầu quyền qua email được xác minh thế nào? | Counsel, Writer D | Lưu một bản ghi không định danh: phiên bản câu chữ + số đếm đồng ý/từ chối theo phòng; xác minh bằng việc mở lại link trên chính máy đó |
| Q-3 | Một cặp Tri Kỷ (và lời mời Radar) có phải "social graph" theo Apple Contacts và Google Contacts không? | Counsel, người nộp app | Không khai, giữ tiền lệ Radar; nếu phải khai thì khai cho cả hai cùng lúc |
| Q-4 | Dữ liệu chiêm tinh có bị coi là "religious or philosophical beliefs" (Apple Sensitive Info) không? | Counsel | Giữ như nhãn hiện tại (không khai) |
| Q-5 | Log lỗi máy chủ: giữ bao lâu, có địa chỉ IP ở ingress không? Có cần khai Diagnostics cho cả app Lá Lành không (data map hiện chưa khai)? | Operator, counsel | Khai Diagnostics "Not linked" khi log được giữ lâu hơn một request |
| Q-6 | Lá Úp không có nút chặn ở cấp người chơi; host kick thay. Đủ cho web chưa? Nếu vào app, Guideline 4.7.1 đòi "block abusive users" | Owner, Writer B | Thêm "ẩn người này với tôi" trong phòng trước khi đóng gói vào app |
| Q-7 | Dịch vụ đẩy của trình duyệt (Google, Apple, Mozilla) nhận endpoint và payload đã mã hoá. Đó là bên xử lý, bên nhận, hay "sharing" theo Google? Có cần ghi trong hồ sơ chuyển dữ liệu ra nước ngoài không? | Counsel, Writer D | Ghi trong chính sách (đã làm ở 5.2); payload không có dữ liệu cá nhân |
| Q-8 | Hết Cứu %: có nút "Xoá dữ liệu của tôi" và xoá ngay khi rời nhóm không? Rời nhóm thì danh hiệu đã có tên mình xử lý sao? | Writer A, owner | **Đã có trong SRS:** HC-FR-48 (rời nhóm xoá ngay cả khoảnh khắc mang biệt danh), HC-FR-49 ("Xoá dữ liệu của tôi"), HC-FR-50 ("Dữ liệu của tôi") |
| Q-9 | Tri Kỷ không theo dõi từng người và không phân tích nội dung, nhưng PRD §6 và TK SRS §10 có bộ đếm tổng hợp theo ngày không ID (danh sách chuẩn ở SRS §10). Có phải khai bộ đếm này trên Apple (Analytics, Not Linked) và Google (Analytics trong App interactions) không? | Counsel, owner | **Chưa chốt.** Hai phương án ở 3.2 và 4.1: (A) không khai nếu bộ đếm chỉ là số nguyên, không lưu sự kiện; (B) khai thận trọng. Đề xuất mặc định (B). Ngưỡng ô nhỏ và thời hạn theo SRS §10 và DPIA X7 |
| Q-10 | Pháp nhân nào là bên kiểm soát dữ liệu ghi trong chính sách (Google bắt buộc có thông tin nhà phát triển; Apple 5.1.1(ix) muốn app cần dữ liệu nhạy cảm do pháp nhân nộp)? | Owner, counsel | — |
| Q-11 | Nhóm Hết Cứu % sang mùa mới thì biệt danh và phiên thành viên sống bao lâu? Hợp đồng chỉ ghi thời hạn cho dữ liệu sự kiện | Writer A, owner | **Đã có trong SRS, chờ owner:** HC-FR-45 / HC-D4 (hết mùa + 30 ngày không có mùa mới thì xoá nhóm, thành viên, link, thuê bao đẩy); phiên thiết bị 120 ngày không hoạt động |
| Q-12 | **Lệch giữa báo cáo và hợp đồng:** tổng kết mùa chiếu lại "Tuần 3 bạn khai 10%", tức là giữ % thô quá 72 giờ. Cờ tình nguyện và hai nút riêng tư cũng chưa có thời hạn trong hợp đồng | Writer A, owner | **Đã có trong SRS:** khoảnh khắc chỉ giữ số của Nhân Vật Chính khi người đó tick giữ (C-HC-03, `hc_moment.nvc_numbers`); ba cờ xoá cùng % sau 72 giờ (`hc_participation_flags`, `hc_claim.hide_pct`) |
| Q-13 | Khi một người rời phòng giữa buổi (Phiên Tòa, Sĩ Số +1), câu trả lời của người đó có bị xoá ngay không? | Writer B | **Đã có trong SRS:** RP-FR-82 (xoá ngay biệt danh, 5 câu, bản ghi đồng ý; vai và phiếu giữ ẩn danh "Người đã rời" tới hết buổi) |
| Q-14 | Cơ chế đặt "lá" của Hết Cứu % có bị xếp là "Simulated Gambling" trong câu hỏi xếp hạng tuổi của Apple và IARC khi vào app không? (D3) | Owner, counsel | Chưa kiểm; kiểm lại trước khi đóng gói |
| Q-15 | Tam Sao: có cho người chơi chọn "ẩn biệt danh của tôi trên thẻ lật" không? | Writer A | **Đã có trong SRS:** mặc định ẩn; hai ô riêng không tick sẵn `show_name_on_screen`, `show_name_on_card` (TS SRS §8.2, TS-FR-33, TS-FR-37) |
| Q-16 | Tri Kỷ: bản ghi đồng ý `tri-ky-pair-v1` và bằng chứng đồng ý chia sẻ hiện bị xoá cùng lá khi giải tán. Có phải giữ một bản tối thiểu lâu hơn để chứng minh đồng ý (Nghị định 356 Điều 6 khoản 2) không? | Counsel | **Chưa có câu trả lời.** Mặc định hiện tại: xoá cùng lá. Cùng câu với TK PRD Q-L7 và DPIA Q23 |

## 10. Bàn giao theo AGENTS.md

**Nguồn đã kiểm:**

- Trong repo: `AGENTS.md`; brief chung của dòng game; báo cáo "Chốt năm trò, giữ trọn chữ Lành"; `docs/foundation/game-line/README.md`;
  `docs/legal/store-privacy-data-map.md`; `docs/legal/2026-10-22-privacy-counsel-dossier.md`; `docs/legal/privacy-security-flow-notes.md`;
  `docs/foundation/la-lanh-plain-vietnamese-content-standard.md`; `docs/plans/2026-10-23-privacy-content-game-plan.md`;
  `docs/user-stories/US-08-gui-loi-moi-la-chung.md`; `apps/web/src/features/consent/ConsentPage.tsx` (trang `/privacy`);
  `apps/mobile/ios/App/App/PrivacyInfo.xcprivacy`; `apps/web/public/_headers`.
- Nguồn chính thức, kiểm ngày 26/10/2026: Apple App Privacy Details; Apple App Review Guidelines (1.2, 4.7, 5.1.1, 5.1.2);
  Google Play Data safety (changelog mới nhất 05/12/2023); Google Play account deletion; Google Play User Data policy;
  Google Play User-generated content. Nghị định 356/2025 chỉ qua nguồn thứ cấp (EY, LuatVietnam, Tạp chí Luật sư Việt Nam).
- **Chưa kiểm:** văn bản gốc Luật 91/2025 và Nghị định 356/2025 trên cổng chính thức; Nghị định 147/2024; câu hỏi xếp hạng tuổi
  của Apple và IARC.

**Phát hiện đã xử lý trong tài liệu này:**

- Biệt danh: khai là `User ID` bên Apple (Apple xếp "screen name" vào đây) và `Name` bên Google (Google ghi rõ gồm "nickname").
- Không dùng ngoại lệ "real time" hay "ephemeral" cho dữ liệu phòng, vì dữ liệu sống qua nhiều request.
- Thêm Gameplay Content cho Hiểu Nhau Không? và ghi việc phải sửa privacy manifest.
- Màn đồng ý của Phiên Tòa và Sĩ Số +1: không tick thì **không hỏi** 5 câu (tối thiểu hoá), thay vì hỏi rồi không hiện; người đó vào ở chế độ chỉ xem (RP-FR-12, RP-FR-22, RP-FR-83).
- Thông báo Hết Cứu % viết theo SRS: tối đa một lần mỗi tuần cho mỗi nhóm, tự bật, câu cố định, không phải ba lần như báo cáo; ba trò còn lại không gửi thông báo.
- Cầu nối sang Lá Lành: URL không mang dữ liệu game, có no-referrer, có màn xác nhận.

**Rà lại theo review Codex @ c1960a3 (26/10/2026):** câu trả lời Hiểu Nhau Không? xếp nhạy cảm và xoá khi cả hai đã xem, muộn
nhất 7 ngày (3.1, 4.1, 5.1, 6.7, 7.6); tách hàng yêu cầu chia sẻ (7 ngày) với bằng chứng đồng ý chia sẻ (khi lá còn, Q-16);
tách "không theo dõi từng người" khỏi bộ đếm tổng hợp, câu trả lời store về Analytics để hai phương án chờ chốt (Q-9); câu "dữ liệu
nhạy cảm" ngay trên ô đồng ý của A và B ở 6.7; F-7 viết lại theo đường chính xác `/tri-ky/i`, `/j`, `/t`.

**Rủi ro chưa giải quyết:** Q-1 đến Q-16, đặc biệt Q-2 (bằng chứng đồng ý khi không có tài khoản), Q-3 (social graph),
Q-12 (khoảnh khắc mùa giữ % thô) và F-5 (trang chính sách hiện tại chưa đạt yêu cầu nhãn của Google, có trước dòng game).

**AC/DoD còn thiếu:**

- Chưa có SRS nào được duyệt. Rà soát nhất quán ngày 26/10/2026 đã đối chiếu tài liệu này với sáu SRS và DPIA: thêm các trường
  [bổ sung] vào ma trận 7.x, sửa trần thông báo (1/tuần mỗi nhóm, chỉ Hết Cứu %), màn lật Sĩ Số +1 theo DP-1, hai ô biệt danh của
  Tam Sao, chế độ "chỉ xem" khi không tick ô 5 câu (RP-FR-12), và đánh dấu Q-8, Q-11, Q-12, Q-13, Q-15 đã có câu trả lời trong SRS.
- Bảng khai sẵn Apple/Google (3.4, 4.3) chưa thêm riêng các trường [bổ sung]; ma trận 7.x đã ghi category đề xuất.
- Owner chưa duyệt câu chữ màn đồng ý; counsel chưa duyệt chính sách.
- Chưa có bản build nào để tạo Xcode privacy report hay kiểm Data safety theo binary.
- F-1 đến F-8 chưa làm.
