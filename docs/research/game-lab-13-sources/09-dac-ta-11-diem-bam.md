# Đặc tả 11 điểm bấm của hiện trường cà phê

Ngày: 27/10/2026. Trạng thái: bản đặc tả chờ duyệt tương tác và phương án hình. Chưa tích hợp runtime.

Hình tổng thể là nơi thao tác chính. Người chơi chọn một vật, chọn **Nhìn kỹ** hoặc **Khám xét**, rồi quay lại đúng vị trí trên hình. Không có sân khấu animation nhân vật rời.

## 1. Nguồn và giới hạn

Tài liệu này đối chiếu các nguồn sau:

- [05: bản đồ, quyền biết và ba mốc](05-ban-do-hien-tai-qua-khu.md).
- [06: sự thật kín và chuỗi chứng cứ](06-ca-phe-su-that-kin-cho-tac-gia.md). Nguồn dành cho tác giả, có đáp án, không phát cho người chơi.
- [07: hiện trường và các nơi khám xét](07-hien-truong-va-kham-xet-v2.md).
- [08: ba phương án và giới hạn của bản thử](08-cac-option-va-kham-xet.md).
- Bản thử trong chat: `coffee-scene-inspection.html`. Tên điểm và thứ tự số trong §4 giữ nguyên bản thử.

GT là sự thật kín do tác giả cố định. EV là thông tin đã kiểm chứng từ nguồn được phép xem. CL là lời khai, HY là giả thuyết. Các loại này giữ nguyên ý nghĩa trong tài liệu 05.

Đặc tả này không thêm GT, không cấp EV mới và không sửa EV00 đến EV04. Mã HS là mã điểm bấm. Mã A và B trong yêu cầu hình là góc minh họa cần vẽ, không phải mã chứng cứ mới.

Một vật có trong ảnh concept chưa mặc nhiên có vai trò trong vụ án. Đồ trong cặp, đồ trong túi, chữ trên giấy và các chi tiết ảnh AI vẫn là đề xuất hình. Chúng không được dùng để chấm lời giải. Các cổng riêng tư và pháp lý trước đây không thay đổi.

## 2. Luồng thao tác chung

### 2.1. Hai hành động có kết quả khác nhau

| Thao tác | Kết quả | Không xảy ra |
|---|---|---|
| Bấm vật trên hình | Chọn đúng vật, hiện tên và hai hành động | Không tự mở cận cảnh, nội dung riêng hoặc chứng cứ |
| Nhìn kỹ | Phóng gần đúng phần đang được phép quan sát | Không xuyên qua ngăn đóng, lật giấy, mở màn hình hoặc hiện quá khứ |
| Khám xét | Mở góc kiểm tra đã được tác giả chuẩn bị, trong quyền xem hiện có | Không tự sinh nội dung, di chuyển vật hoặc tạo một sự kiện mới trong GT |
| Đóng cận cảnh | Về hình tổng thể, giữ vật đang chọn và mốc hiện tại | Không xóa điều đã biết, không đóng vật thật và không tạo một bản sao vật |
| Chọn vật khác | Đóng cận cảnh trước, đổi điểm chọn | Không mang nội dung riêng của vật trước sang vật mới |

Không có góc khám xét hợp lệ thì hành động vẫn có phản hồi rõ ràng: "Phần này chưa có dữ liệu khám xét". Không thay bằng "Không có gì" hoặc "Không tìm thấy manh mối".

### 2.2. Ba loại trạng thái phải tách riêng

| Loại trạng thái | Giá trị được mô tả | Quy tắc |
|---|---|---|
| Khung giao diện | Chưa chọn, đã chọn, đang nhìn kỹ, đang khám xét, đã đóng khung | Chỉ mô tả giao diện của người xem |
| Phần vật được nguồn cho thấy | Mặt ngoài, mặt đang lộ, ngăn được phép xem, phần chưa biết | Không suy ra bên trong từ hình mặt ngoài. Không đồng nhất trạng thái khóa màn hình với việc điện thoại đang úp |
| Kiến thức và quyền xem | Chưa quan sát, đã quan sát một phần, chưa có quyền, thiếu dữ liệu | Đóng khung không làm mất phần đã quan sát. Có quyền chưa có nghĩa đã xem hết |

Ví dụ, "đóng cửa sổ cặp" không phải "đóng khóa kéo của cặp". Animation mở ngăn trong cận cảnh chỉ trình bày phạm vi được xem. Nó không ghi thêm một hành động vật lý vào lịch sử vụ án. Nếu sau này cho người chơi cầm, lật hoặc chuyển vật thật trong game, đó là phạm vi thiết kế khác, chưa được duyệt ở đây.

Ảnh tổng thể và ảnh cận cảnh phải cùng danh tính vật, cùng mốc và cùng phạm vi cho phép. Nếu hình tổng thể đã lộ nội dung riêng thì không được dùng một ngăn kéo giao diện để giả vờ giấu lại. Ảnh đó cần được sửa trước khi duyệt.

### 2.3. Mốc thời gian

- Điểm bấm mặc định thuộc T2, 09:00. T0 là 08:55, T1 là 08:57.
- Bấm hoặc khám xét vật tại T2 không tự mở một phần quá khứ.
- T0 và T1 chỉ hiện các quan sát do EV01, EV02 hoặc EV04 đã kiếm được bao phủ. EV03 vẫn là sổ mượn, không biến thành lịch sử vị trí.
- Không sao chép 11 điểm T2 sang T0 hoặc T1 cùng vị trí và nội dung. Vật hoặc ngăn chưa xuất hiện trong nguồn quá khứ tiếp tục là chưa biết.
- Đủ chứng cứ không tự phát GT. Chỉ cuối ván mới tái hiện toàn bộ theo tài liệu 05 và 06.

### 2.4. Khác biệt cần xử lý so với bản thử

| Bản thử hiện tại | Yêu cầu của đặc tả này |
|---|---|
| Chưa có kiểm quyền Q1, đồ trong túi có thể hiện khi bấm | Kiểm quyền trước khi trả nội dung hoặc hình riêng. Bản thử không phải bằng chứng đã bảo vệ dữ liệu |
| Ảnh tổng thể có cặp hé lộ đồ, cận cảnh khám xét lại bắt đầu bằng cặp đóng | Chốt một phạm vi nhìn thấy nhất quán. Không để hình nền công khai lộ đồ cần Q1, không dùng đóng khung để thay trạng thái vật |
| Các ảnh cắt từ concept có chữ hoặc chi tiết AI chưa duyệt | Chỉ dùng để thử vị trí và thao tác. Hình chính thức dùng nội dung tác giả đã kiểm |
| Nhiều điểm khám xét báo chưa có dữ liệu | Giữ phản hồi này tới khi có nguồn hợp lệ. Không điền bí mật cho đủ hai hành động |

Đây là danh sách việc cần làm sau duyệt, không phải thay đổi đã được áp dụng vào bản thử. Nội dung riêng chưa được cấp quyền không được gửi sẵn trong ảnh, chú thích hoặc dữ liệu mà người xem có thể mở. Cách bảo vệ khi triển khai chưa được thực hiện ở tài liệu này.

## 3. Quyền xem dùng cho từng điểm

Các quyền dưới đây là đề xuất tương tác để duyệt, không phải kết luận pháp lý hoặc quyền đọc dữ liệu người thật.

| Quyền | Phần được xem | Điều kiện và giới hạn |
|---|---|---|
| Q0: phần hiện trường công khai | Mặt hoặc vùng đã hiện công khai tại T2 | Mọi người trong ván được xem cùng nguồn. Vật công khai không làm mọi nội dung bên trong công khai |
| Q1: nội dung riêng của vai | Đúng ngăn, túi hoặc nội dung hư cấu đã được cấp quyền | Luật nhánh và phạm vi cấp quyền phải được chốt trước. Với vai do người thật nhận, người giữ vai tự xác nhận phần được chia sẻ. A không xác nhận thay B. Profile tham gia không cấp quyền khám đồ riêng |
| Q2: đối chiếu chứng cứ đã kiếm | Phần nguồn người xem đã có quyền biết | Có thể đặt cạnh vật để đối chiếu. Nút khám xét không tự kiếm EV01 đến EV04 hoặc mở thêm phạm vi của chúng |

Trong solo, quyền của NPC chỉ áp dụng cho đồ hư cấu đã được kịch bản cho phép. Không coi NPC là sự đồng ý của một người thật. Trong chơi nhóm, thẻ vai riêng không tự đẩy nội dung lên bản đồ chung.

Khi chưa có Q1, phản hồi là "Bạn chưa có quyền xem nội dung này". Không hiển thị số món, hình mờ, hình xem trước, tên tệp, mô tả ảnh, thông báo kết quả hoặc trạng thái mở của người khác. Phản hồi không thay đổi theo việc ngăn kín có chứa vật quan trọng hay không.

Quyền xem được xét trước nội dung và tình trạng ảnh. Chỉ người đã có quyền mới thấy phản hồi thiếu dữ liệu của một ngăn riêng. Khi quyền không còn hiệu lực, mở lại khung phải kiểm lại quyền. Đóng khung không tự cấp lại hoặc gia hạn quyền.

Kết quả riêng chỉ xuất hiện cho người có quyền. Chia sẻ chỉ công khai đúng phần quan sát được chọn, không công khai toàn bộ túi, profile hoặc lịch sử. Việc chia sẻ phải nằm trong phạm vi được cấp. Đường kiếm chứng cứ quyết định vẫn có cách tiếp cận độc lập như tài liệu 05, không phụ thuộc chủ đồ chịu mở cặp hoặc thú nhận.

## 4. Đặc tả từng điểm

Mỗi mục giữ cùng thứ tự trường để đối chiếu giữa người viết nội dung, người vẽ và người kiểm. Các vị trí thuộc cùng bản đồ P, I, D, L. Tọa độ vùng bấm trong bản thử không phải tọa độ hình chính thức.

### HS01. Cốc cà phê

| Trường | Đặc tả |
|---|---|
| Đối chiếu bản thử | Số 1, `cup`, bàn D tại T2 |
| Nhìn kỹ | Phóng gần thân, quai và miệng cốc đang lộ, cùng ranh giới vết cà phê sát cốc |
| Khám xét | Kiểm các phần đang được EV00 bao phủ. Có thể đối chiếu EV01 hoặc EV02 nếu đã kiếm. Không tự lật cốc hoặc hiện mặt đáy chưa có nguồn |
| Đóng và mở | Cốc giữ trạng thái đã đổ. Chỉ khung cận cảnh mở hoặc đóng. Phần đáy bị che vẫn là chưa biết |
| Quyền xem | Q0 cho hiện tại. Q2 cho ảnh quá khứ đã kiếm. Không dùng quyền chủ cốc để mở lịch sử |
| Góc cận cảnh cần vẽ | HS01-A: góc sát mặt bàn, thấy quai và vết đổ, có vị trí D. HS01-B: góc kiểm chi tiết những mặt đã được nguồn xác nhận, không vẽ thêm mặt đáy. Giữ hướng quai đồng nhất giữa các góc |
| Phần chưa biết | Ai đặt cốc, ai cầm cốc trước đó, mặt đáy bị che, nguyên nhân và người gây đổ nếu chưa đủ chứng cứ |
| Phạm vi kết luận | EV00 xác nhận hiện trạng. EV01 và EV02 giải thích cơ chế trong đúng phạm vi của chúng. Xem cốc hiện tại không nhận dạng người gây chuyện |

### HS02. Cặp trên ghế

| Trường | Đặc tả |
|---|---|
| Đối chiếu bản thử | Số 2, `bag`, ghế cạnh D tại T2. Ảnh 07 gắn cặp với Hạnh ở mức đề xuất minh họa, chưa phải xác nhận chủ cặp bằng EV |
| Nhìn kỹ | Xem mặt ngoài, quai cặp, ghế và mép ngăn đang được phép lộ. Không phóng ảnh tổng thể tới mức nhìn xuyên nội dung riêng |
| Khám xét | Với Q1, mở đúng phạm vi ngăn đã được duyệt. Nếu nội dung ngăn chưa được chốt, báo thiếu dữ liệu, không cấp bộ đồ mà ảnh concept tự vẽ |
| Đóng và mở | Tách khung ngoài với khung bên trong ngăn. Mở ngăn chính không mở túi phụ. Đóng khung không xóa điều đã quan sát. Không dùng ảnh cặp đóng và mở có thân cặp hoặc số vật không khớp |
| Quyền xem | Q0 cho mặt ngoài. Q1 cho từng ngăn. Tên chủ cặp chỉ hiện khi nguồn công khai hoặc quyền vai cho phép, không suy từ vị trí ghế |
| Góc cận cảnh cần vẽ | HS02-A: mặt ngoài trên đúng ghế. HS02-B: góc nhìn vào ngăn được phép xem, rõ mép ngăn và vùng chưa kiểm. Mỗi trạng thái dùng cùng cặp, cùng vật. Khăn, giấy ăn, chìa khóa, giấy mua hàng và sổ trong concept chưa là danh mục chứng cứ được duyệt |
| Phần chưa biết | Nội dung chưa được chốt, ngăn chưa được xem, ai từng sử dụng đồ, thời điểm và mục đích sử dụng |
| Phạm vi kết luận | Vị trí cặp không chứng minh chủ cặp ở D lúc T1. Một món trong ngăn chỉ xác nhận vị trí quan sát tại mốc đó nếu nguồn đã được duyệt. Không chứng minh món đã gây hoặc lau sự cố |

### HS03. Máy in

| Trường | Đặc tả |
|---|---|
| Đối chiếu bản thử | Số 3, `printer`, khu I tại T2 |
| Nhìn kỹ | Xem mặt ngoài máy, khay đang lộ và phần giấy thấy được |
| Khám xét | Kiểm đúng khay hoặc mặt máy đã có hình và quyền. Không thêm lịch sử in, tài khoản, file in, bản ghi âm hoặc nguồn nhận dạng |
| Đóng và mở | Khung giao diện có thể mở. Nắp máy và khay kín không tự đổi trạng thái. Chưa có hình bên trong thì vẫn chưa kiểm, không phải máy trống |
| Quyền xem | Q0 cho mặt ngoài và giấy công khai. Nội dung giấy riêng áp dụng Q1. Không được dùng giao diện máy in để vượt quyền của tài liệu |
| Góc cận cảnh cần vẽ | HS03-A: mặt máy và khay đang lộ. HS03-B: phạm vi kiểm khay đã được duyệt. Không thêm bảng log trên màn hình hoặc chữ trên giấy có giá trị suy luận |
| Phần chưa biết | Dữ liệu trong máy, người gửi lệnh, giờ in, nội dung trang bị che và hành động tại I trong quá khứ |
| Phạm vi kết luận | Thấy máy và Quân ở I hiện tại không xác nhận CL03 về T1. Không đổi sổ mượn EV03 thành nhật ký máy in |

### HS04. Túi quần vai Quân

| Trường | Đặc tả |
|---|---|
| Đối chiếu bản thử | Số 4, `pocket`, vai Quân tại I ở T2 |
| Nhìn kỹ | Xem vị trí và mặt ngoài túi trên avatar mặc đủ quần áo. Không hiển thị khay đồ bên trong |
| Khám xét | Chỉ mở khay đồ hư cấu khi có Q1 và danh mục được tác giả duyệt. Không có thao tác lục người thật, chụp túi thật hoặc lấy đồ từ profile |
| Đóng và mở | Ban đầu nội dung chưa được xem. Mở đúng một túi không khám mọi túi. Nếu minh họa lấy đồ ra khay, khay là cách trình bày cùng các món, không tạo bản sao hoặc đổi lịch sử |
| Quyền xem | Q0 cho mặt ngoài avatar. Q1 riêng cho nội dung túi. Người khác không tự khai Quân đã đồng ý. Trong solo chỉ dùng quyền NPC hư cấu đã được định trước |
| Góc cận cảnh cần vẽ | HS04-A: phần quần áo có túi, không phơi cơ thể. HS04-B: đúng túi và khay kiểm kê, rõ món thuộc túi nào. USB, giấy sinh nhật, kẹo và phiếu lấy giấy trong concept là ứng viên, chưa được dùng làm chứng cứ |
| Phần chưa biết | Danh mục đã duyệt, các túi chưa kiểm, lịch sử sử dụng, nội dung giấy chưa duyệt và quan hệ giữa đồ cầm trên tay với đồ trong túi |
| Phạm vi kết luận | Đồ hiện tại trong túi không xác nhận Quân ở đâu tại T1. Không dùng USB để tự sinh log hoặc giấy sinh nhật để tự xác nhận CL03 |

### HS05. Bộ tarot

| Trường | Đặc tả |
|---|---|
| Đối chiếu bản thử | Số 5, `tarot`, bàn D tại T2, vật minh họa theo tài liệu 07 |
| Nhìn kỹ | Xem hình trên mặt đang lộ và cách các lá đang xếp trong nguồn được duyệt |
| Khám xét | Xem riêng mặt đã lộ. Các lá úp, thứ tự bộ bài và thông điệp chưa viết tiếp tục chưa biết. Không tự rút ngẫu nhiên hoặc sinh lời tiên đoán để giải vụ án |
| Đóng và mở | Khung chi tiết mở, bộ bài không tự xáo hoặc lật lá kín. Đóng khung giữ nguyên mặt đã quan sát |
| Quyền xem | Q0 cho mặt công khai. Q1 nếu sau này có thẻ riêng của vai, chưa được cấp ở đặc tả này. Chỉ đối chiếu Q2 từ chứng cứ đã kiếm |
| Góc cận cảnh cần vẽ | HS05-A: bộ bài trên bàn. HS05-B: mặt lá đang lộ, đủ đọc hình, không có tên hung thủ, đường đi hoặc đáp án trong hoa văn |
| Phần chưa biết | Các lá bị che, người đặt bộ bài, thời điểm đặt và lịch sử dùng bộ bài |
| Phạm vi kết luận | Tarot gợi câu hỏi hoặc nơi cần khảo sát theo tài liệu 05, không tạo EV và không nhận dạng người gây chuyện. Lá số hoặc tính cách không thay bằng chứng |

### HS06. Điện thoại úp

| Trường | Đặc tả |
|---|---|
| Đối chiếu bản thử | Số 6, `phone`, bàn D tại T2, vật minh họa theo tài liệu 07 |
| Nhìn kỹ | Xem lưng, viền và vị trí điện thoại đang úp |
| Khám xét | Chỉ kiểm mặt đang được nguồn cho thấy. Không lật máy, bật màn hình, đọc thông báo hoặc tin nhắn khi chưa có nội dung và quyền riêng được duyệt |
| Đóng và mở | Trạng thái biết được là đang úp, không phải đã xác nhận máy khóa, tắt hoặc hết pin. Mở cận cảnh không mở khóa thiết bị |
| Quyền xem | Q0 cho mặt ngoài công khai. Q1 là điều kiện cần nếu có nội dung hư cấu riêng, nhưng hiện chưa có nội dung được duyệt. Không yêu cầu quyền truy cập điện thoại thật |
| Góc cận cảnh cần vẽ | HS06-A: lưng và vị trí trên bàn. HS06-B: chi tiết viền đang lộ. Không vẽ màn hình sáng hoặc hình thông báo có thể lộ dữ liệu chưa được phép |
| Phần chưa biết | Chủ máy, màn hình, trạng thái khóa, tin nhắn, ứng dụng, lịch sử sử dụng và thời điểm đặt máy |
| Phạm vi kết luận | Điện thoại đang ở bàn trong minh họa. Không dùng vị trí điện thoại làm vị trí chủ máy tại T1 hoặc tạo ảnh chụp thay EV01 |

### HS07. Tài liệu dính cà phê

| Trường | Đặc tả |
|---|---|
| Đối chiếu bản thử | Số 7, `paper`, bàn D tại T2 |
| Nhìn kỹ | Phóng gần vùng cà phê, mép tờ giấy và phần đang lộ, giữ rõ quan hệ với cốc |
| Khám xét | Kiểm phạm vi trang hiện tại được nguồn bao phủ. Không lật trang, khôi phục chữ bị che, hiện chữ dưới vết bẩn hoặc tự thêm hóa đơn có dấu giờ |
| Đóng và mở | Tài liệu vẫn nằm theo hiện trường. Chỉ khung giao diện mở. Các trang dưới, mặt sau và phần bị cốc che không tự thành đã kiểm |
| Quyền xem | Q0 cho vết đổ công khai. Nội dung giấy không mặc nhiên công khai vì có vết cà phê. Nội dung riêng cần Q1 và phải được tác giả duyệt |
| Góc cận cảnh cần vẽ | HS07-A: mặt bàn nhìn rõ vết cà phê trên tài liệu. HS07-B: cận vùng trang được phép xem. Cốc và vết đổ khớp HS01, không để chữ AI hoặc biểu đồ trên giấy thành manh mối ngoài kịch bản |
| Phần chưa biết | Nội dung chữ chưa duyệt, trang dưới, mặt sau, ai đặt hoặc đọc tài liệu, thời điểm tài liệu xuất hiện |
| Phạm vi kết luận | EV00 xác nhận tài liệu có vết cà phê. Không suy ra ai làm đổ, ai sở hữu tài liệu hoặc tài liệu từng ở đâu |

### HS08. Sổ trên bàn

| Trường | Đặc tả |
|---|---|
| Đối chiếu bản thử | Số 8, `notebook`, bàn D tại T2, vật minh họa theo tài liệu 07 |
| Nhìn kỹ | Xem bìa, gáy và vị trí của sổ đang đóng |
| Khám xét | Kiểm mặt ngoài. Trang bên trong chưa có nội dung duyệt thì hiện trạng thái thiếu dữ liệu. Không tự viết nhật ký, danh sách mượn đồ hoặc lời thú nhận |
| Đóng và mở | Sổ vẫn đóng. Mở khung không mở sổ. Xem bìa không xác nhận đã đọc hoặc kiểm hết sổ |
| Quyền xem | Q0 cho mặt ngoài công khai. Q1 cho trang riêng nếu có nội dung được duyệt sau này. Sổ này không mặc nhiên là sổ trong cặp |
| Góc cận cảnh cần vẽ | HS08-A: bìa và gáy tại D. HS08-B: chi tiết mặt ngoài được kiểm. Giữ riêng danh tính sổ bàn và sổ cặp, không sao chép đồ hoặc tự xác nhận hai sổ là một |
| Phần chưa biết | Chủ sổ, trang trong, lịch sử dùng và quan hệ với các sổ khác trong concept |
| Phạm vi kết luận | Chỉ mô tả được mặt ngoài trong minh họa. Không đổi sổ này thành sổ mượn EV03 khi nguồn 05 và 06 chưa đặt nó ở đây |

### HS09. Bình nước

| Trường | Đặc tả |
|---|---|
| Đối chiếu bản thử | Số 9, `water`, bàn D tại T2, vật minh họa theo tài liệu 07 |
| Nhìn kỹ | Xem thân, phần nắp đang lộ và vị trí cạnh giấy tờ |
| Khám xét | Kiểm bề mặt được hình bao phủ. Không mở nắp, đổ nước, cân bình, lấy dấu vân tay hoặc sinh kiểm nghiệm chất lỏng |
| Đóng và mở | Không suy kín hoặc hở nắp từ một hình thiếu rõ. Mở khung không mở bình. Đáy và bên trong vẫn chưa biết nếu chưa có nguồn |
| Quyền xem | Q0 cho bề mặt công khai. Q1 nếu một chi tiết sau này thuộc nội dung riêng, chưa cấp trong đặc tả này |
| Góc cận cảnh cần vẽ | HS09-A: thân và vị trí trên bàn. HS09-B: mặt nắp đang lộ, không tự thêm vết bẩn, mã hoặc ký hiệu quyết định |
| Phần chưa biết | Chủ bình, chất lỏng bên trong, lượng nước, thời điểm sử dụng và việc có ai chạm vào cốc |
| Phạm vi kết luận | Có bình trong minh họa. Không kết luận ai đã uống, bình gây sự cố hoặc bình sạch nên chủ bình vô can |

### HS10. Bồn rửa

| Trường | Đặc tả |
|---|---|
| Đối chiếu bản thử | Số 10, `sink`, pantry P tại T2 |
| Nhìn kỹ | Xem lòng bồn, vòi và phần mặt bàn đang lộ trong góc hiện tại. Hạnh ở P theo EV00 |
| Khám xét | Kiểm vùng nhìn thấy. Không mở tủ kín, lục cống, bật vòi, lấy mẫu hoặc thêm vết cà phê chưa có trong nguồn |
| Đóng và mở | Khung cận cảnh mở. Tủ, khoang dưới bồn và cống không tự thành đã khám. Đóng khung không thay hiện trường |
| Quyền xem | Q0 cho vùng công khai. Đồ riêng hoặc tủ chưa được cấp không nằm trong quyền này. Không tự dùng quyền xem Hạnh để đọc thông tin riêng của vai |
| Góc cận cảnh cần vẽ | HS10-A: góc bồn và vị trí P. HS10-B: cận bề mặt đã được nguồn cho phép. Không thêm khăn ướt, vết bẩn, giờ dùng nước hoặc dấu sử dụng để giải thích GT |
| Phần chưa biết | Ai dùng bồn, dùng khi nào, các vùng bị che và hành động tại P trong quá khứ |
| Phạm vi kết luận | EV00 cho vị trí Hạnh ở P hiện tại. Không xác nhận hay bác bỏ CL02, không suy Hạnh đã ở P suốt T1 hoặc đã rửa đồ |

### HS11. Dây Minh đang cầm

| Trường | Đặc tả |
|---|---|
| Đối chiếu bản thử | Số 11, `cable`, lối ra L tại T2 |
| Nhìn kỹ | Xem đoạn dây đang lộ và vai đang giữ nó, không hiện hành động quá khứ |
| Khám xét | Kiểm phần dây trong phạm vi EV00. Đối chiếu với EV01 hoặc EV03 chỉ khi người xem đã kiếm nguồn đó. Không sinh mã mới, ảnh lịch sử hoặc sổ mượn từ đầu cắm |
| Đóng và mở | Cận cảnh mở, dây không tự tháo cuộn hoặc được kéo lại trên bàn. Phần bị tay che vẫn chưa biết. Đóng khung không đổi người cầm |
| Quyền xem | Q0 cho phần công khai, Q2 cho đối chiếu nguồn đã kiếm. Không cần vai chịu thú nhận mới có đường kiếm EV04 |
| Góc cận cảnh cần vẽ | HS11-A: dây cùng tay cầm, đủ định vị tại L. HS11-B: phần chi tiết cần đối chiếu, chỉ hiển thị mã X nếu nguồn người chơi được phép xem thực sự cho đọc mã. Tác giả biết danh tính dây không thay ảnh hoặc quyền của người chơi |
| Phần chưa biết | Đoạn bị che, ai đặt hoặc kéo dây trước đó, lịch sử chuyển tay và danh tính người kéo nếu chưa có chuỗi nhận dạng |
| Phạm vi kết luận | EV00 mô tả hiện tại. EV03 xác nhận người nhận dây theo sổ, không phải người kéo. Chỉ chuỗi EV02 với EV04 hỗ trợ nhận dạng hành động, không phải việc giữ dây tại T2 |

## 5. Kế hoạch hình và chuyển động

Mỗi HS cần góc A để nhìn kỹ và góc B để kiểm phạm vi đã được phép xem. Góc B có thể dùng lại vùng hình A nếu không có dữ liệu bổ sung. Không bắt người vẽ tạo thêm nội dung kín chỉ để đủ hai ảnh. Có 22 ô yêu cầu góc, không phải cam kết 22 ảnh mới hoặc 22 chứng cứ.

Mọi góc cần giữ mã vật, mã vùng, mốc, hướng nhìn và phạm vi nhìn thấy. Phần bị che phải tiếp tục bị che. Không nhúng chữ, tên file, mô tả ảnh hoặc hình xem trước làm lộ đáp án.

Các yêu cầu chuyển động thuộc cùng hiện trường:

| Tình huống | Chuyển động đề xuất | Ranh giới |
|---|---|---|
| Chọn vật | Viền chọn ngắn, tên vật và hai hành động xuất hiện | Không nhấp nháy để gợi vật quan trọng |
| Nhìn kỹ | Phóng về vật trong khoảng 180 đến 260 ms | Không đổi mặt vật hoặc mở ngăn |
| Khám xét | Chuyển sang góc kiểm đã được cấp. Ngăn cặp chỉ mở phần được phép xem | Không thêm hành động vào GT, không làm lộ các ngăn khác |
| Đóng khung | Trở lại đúng điểm chọn và mốc | Không chạy lại sự cố, không xóa kiến thức |
| Giảm chuyển động | Đổi trạng thái trực tiếp, giữ đủ thông tin | Không mất khả năng khám xét hoặc cần thao tác chính xác theo thời gian |

Nhân vật không di chuyển để trang trí trong snapshot T2. Chớp mắt hoặc cử động tại chỗ chỉ là đề xuất mỹ thuật sau khi chọn hình. Không xem chúng là lời khai, thông tin trạng thái cảm xúc thật hoặc bằng chứng. Không ghép lại sân khấu nhân vật rời.

## 6. Đối chiếu chứng cứ mà không tạo chứng cứ mới

| Nguồn giữ nguyên | Điểm liên quan | Giới hạn |
|---|---|---|
| EV00: hiện trường T2 | HS01, HS07, HS11. Vị trí vai ở P và I là bối cảnh HS10 và HS03 | Chỉ các sự kiện hiện tại tài liệu 06 đã mô tả. Không mở rộng EV00 sang toàn bộ đồ và chữ trong concept |
| EV01: ảnh T0 của bàn D | HS01 và HS11 khi nguồn đã kiếm được | Không cho nhìn kỹ hiện tại tự thay hành động ghép ảnh |
| EV02: chuỗi T1 chưa rõ danh tính | HS01 và HS11 khi nguồn đã kiếm được | Không nhận dạng bằng quần áo hoặc tâm trạng của avatar |
| EV03: sổ mượn phụ kiện | HS11 để đối chiếu sau khi đã kiếm | Không tự đặt sổ ở HS03, HS06 hoặc HS08. Người nhận dây không đương nhiên là người kéo |
| EV04: chuỗi nối D tới L | Đối chiếu với HS11 sau khi đã kiếm | Không cần chủ dây mở túi. Không phát toàn bộ GT trước khi kết thúc |

Khăn trong cặp hoặc đồ trong túi không tự xác minh CL02 hoặc CL03. Tác giả biết một lời khai đúng cũng không biến nó thành EV cho người chơi.

Đặc tả này chưa gắn vị trí khởi động bốn challenge vào một trong 11 vật. Vị trí vào challenge cần được chốt riêng trước triển khai, dùng đúng vật liệu và cách kiếm trong tài liệu 05. Không giải quyết khoảng trống này bằng cách tự thêm ảnh, log, tờ giấy hoặc nguồn thứ sáu.

## 7. Tiêu chí duyệt đặc tả và bản thử tiếp theo

Các tiêu chí sau chưa phải kết quả test runtime.

| ID | Tình huống | Kết quả cần đạt |
|---|---|---|
| HS-AC01 | Đối chiếu danh mục với bản thử | Đủ 11 điểm, đúng số và đúng `id`, không có điểm bí mật thứ 12 |
| HS-AC02 | Chưa chọn vật | Chưa hiện hai hành động như đã được thực hiện |
| HS-AC03 | Chọn một vật | Chỉ vật đó được chọn, hiện Nhìn kỹ và Khám xét, chưa mở dữ liệu |
| HS-AC04 | Nhìn kỹ | Chỉ phóng phần đang được phép xem, không dùng lại ảnh khám xét chứa thông tin kín |
| HS-AC05 | Khám xét nơi chưa có dữ liệu | Báo chưa có dữ liệu, không báo rỗng, sạch hoặc đã kiểm hết |
| HS-AC06 | Đóng khung rồi mở lại | Giữ điều đã biết, kiểm lại quyền hiện hành, không đổi vật hoặc sinh lại nội dung |
| HS-AC07 | Chưa có Q1 ở cặp hoặc túi | Không lộ món, số món, chủ thể chưa công khai hoặc trạng thái khám của người khác |
| HS-AC08 | A tự khai B đã đồng ý | Không cấp quyền xem nội dung vai B |
| HS-AC09 | Đã mở một ngăn | Chỉ ngăn đó được quan sát, các ngăn khác chưa biết |
| HS-AC10 | Chia sẻ một kết quả riêng | Chỉ phạm vi được phép chia sẻ hiện cho nhóm, không có dữ liệu riêng kèm theo |
| HS-AC11 | Khám HS02 hoặc HS04 ở hình concept | Không ghi đồ đề xuất thành EV mới hoặc tự xác minh lời khai |
| HS-AC12 | Khám HS03 hoặc HS08 | Không có nhật ký in hoặc sổ mượn mới, EV03 giữ đúng nguồn |
| HS-AC13 | Khám HS06 | Không mở nội dung điện thoại thật hoặc tự tạo tin nhắn hư cấu |
| HS-AC14 | Đổi sang T0 hoặc T1 khi chưa có nguồn | Không sao chép vị trí, vật hoặc ngăn từ T2 sang quá khứ |
| HS-AC15 | Có EV01 hoặc EV02 nhưng chưa có EV04 | Không nhận dạng người kéo từ cận cảnh hiện tại hoặc nhãn giấu trong ảnh |
| HS-AC16 | Có EV03 | Chỉ xác nhận người nhận dây theo sổ, không tự kết tội người giữ dây |
| HS-AC17 | Chủ đồ không cho xem nội dung riêng | Đường kiếm chứng cứ quyết định độc lập vẫn còn, không cần thú nhận |
| HS-AC18 | Đã đủ chứng cứ nhưng chưa chốt ván | Không mở GT hoặc tự phát tái hiện toàn bộ |
| HS-AC19 | Quay lại bản đồ | Giữ đúng mốc và điểm chọn. Cốc không đứng lại hoặc đổ lần nữa |
| HS-AC20 | Hình nhỏ, dùng bàn phím hoặc màn hình cảm ứng | Chọn được đủ 11 mục bằng điểm bấm hoặc danh sách. Nhãn không chỉ dựa vào màu. Vùng chọn nhỏ không chồng nhau |
| HS-AC21 | Bật giảm chuyển động | Xem đủ cùng thông tin bằng chuyển trạng thái trực tiếp |
| HS-AC22 | So ảnh tổng thể với ảnh cận cảnh | Cùng vật, cùng mốc, không có bản sao đồ hoặc nội dung riêng lộ sẵn trên ảnh nền |
| HS-AC23 | Thiếu hình hoặc hình tải lỗi | Không đổi nội dung bằng suy đoán, không coi chưa tải là không có đồ |
| HS-AC24 | Chỉ thay tên vai hoặc chọn phương án hình khác | Không sửa GT, EV hoặc phạm vi quyền xem đã duyệt |

## 8. Những phần còn chờ duyệt

| Phần | Trạng thái hiện tại |
|---|---|
| Phương án hình tổng thể | Chưa chọn. Ba ảnh trong tài liệu 08 chưa phải hướng được duyệt |
| Hai hành động và 11 điểm bấm | Đã có đặc tả trong tài liệu này, chờ người dùng duyệt tương tác |
| Quyền Q1 và phạm vi chia sẻ | Đề xuất chờ duyệt. Không mặc định cho phép tất cả |
| 22 ô góc cận cảnh | Đã ghi yêu cầu, chưa có bộ hình chứng cứ chính thức được duyệt |
| Nội dung kín của cặp, túi, sổ, điện thoại | Chưa được chốt thành nguồn của vụ mẫu. Không cần điền bí mật để hoàn tất hình |
| Vị trí khởi động challenge | Chưa chốt, không đổi cách kiếm EV01 đến EV04 |
| Runtime | Không bắt đầu cho tới khi người dùng chọn phương án hình và duyệt tương tác. Các quyền và hình liên quan cũng phải đủ trước khi phần tương ứng chạy |

Hoàn tất tài liệu không có nghĩa mọi nội dung đã sẵn sàng để triển khai. Tài liệu 05 đến 08 và bản thử được giữ nguyên trong lần bổ sung này.

## 9. Prompt tiếp cho Claude

Đọc tài liệu 09 và các nguồn 05 đến 08. Rà đủ HS01 đến HS11 và HS-AC01 đến HS-AC24. Chỉ báo chỗ còn mâu thuẫn hoặc thiếu nguồn, không tạo thêm chứng cứ, nội dung túi, tin nhắn, log hoặc sửa GT. Sau khi người dùng chọn phương án hình và duyệt tương tác, lập danh sách góc A và B cần vẽ theo đúng phạm vi quyền xem. Chưa viết hoặc tích hợp runtime trước hai phê duyệt đó, không tạo sân khấu animation nhân vật rời.
