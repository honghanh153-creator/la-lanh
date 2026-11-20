# Máy kiểm không lộ dữ liệu (leak canary)

Việc #690 và #691, kế hoạch 7 tuần, tuần 1. Điều kiện bắt đầu số 8: trước khi bật một tính năng mới, máy tự kiểm rằng dữ liệu riêng không lọt ra những chỗ không được phép.

Yêu cầu gốc: US-03 AC12 và mục 21 (DoD delta: network, URL, history, log, cache không chứa ngày sinh, token, chữ riêng); US-04 AC09.

## Nó làm gì

1. Chạy bản web đã build cùng API thật trên máy, với cơ sở dữ liệu SQLite tạm (xoá sau khi chạy).
2. Một trình duyệt đi qua app như người mới, dùng một hồ sơ giả có "dấu" dễ tìm:

| Dữ liệu | Dấu | Đi qua đâu |
|---|---|---|
| Ngày sinh | một ngày giả cố định | màn nhập ngày sinh |
| Giờ sinh | một giờ giả cố định | màn giờ và nơi sinh |
| Nơi sinh | một tỉnh cố định, cả chữ gõ tìm và mã nơi | màn giờ và nơi sinh |
| Mood | một lựa chọn cố định | Home |
| Câu hỏi Tarot | một từ bịa | màn Tarot |
| Chữ gõ vào lớp an toàn | một từ bịa, kèm câu mà lớp an toàn chặn | màn Tarot (API trả 422) |
| Cookie phiên và mã CSRF | đọc lúc chạy | mọi màn |

3. Tìm các dấu đó, ở mọi cách viết (có dấu, không dấu, mã hoá URL một hoặc hai lần, chữ hoa), trong:

| Chỗ tìm | Lấy từ đâu |
|---|---|
| Nhật ký máy chủ | toàn bộ stdout và stderr của API và máy chủ QA |
| Đường mạng | URL và query của mọi request |
| Header Referer | mọi request |
| Request ra ngoài app | bất kỳ request nào tới nơi khác đều tính là lỗi |
| Báo lỗi | mọi dòng console và lỗi trang |
| Câu trả lời lỗi của API | nội dung mọi câu trả lời từ 400 trở lên |
| Lịch sử trình duyệt | mọi lần đổi địa chỉ của trang |
| URL hiện tại | sau mỗi bước |
| Bộ nhớ trình duyệt | localStorage, sessionStorage, mọi mục trong Cache (địa chỉ, header và nội dung câu trả lời đã lưu), tiêu đề trang |
| Tên file | tên file khi tải ảnh note, tải Lá Khai Sinh, tải dữ liệu của tôi; tên file app đưa vào bảng chia sẻ; header `Content-Disposition` của mọi câu trả lời |
| Ảnh chia sẻ | bản SVG mà ảnh được vẽ từ đó, chữ mô tả ảnh (alt), tiêu đề màn, tiêu đề và chữ app đưa vào bảng chia sẻ |
| Thông tin kèm trong ảnh PNG | mọi phần của file PNG tải về không phải điểm ảnh: chữ (tEXt, zTXt, iTXt), EXIF, giờ sửa file, hồ sơ màu, phần lạ |

Về file và ảnh (#691):

- App dựng một bản SVG, hiện nó lên màn và vẽ ảnh PNG từ chính bản đó. Máy kiểm đọc bản SVG này. Phần font nhúng trong SVG được bỏ ra trước khi tìm, vì đó không phải chữ.
- Trình duyệt chạy thử không có bảng chia sẻ. Máy kiểm đặt một bảng chia sẻ giả để ghi lại app đưa gì vào đó (tên file, tiêu đề, chữ, link).
- File "dữ liệu của tôi" chứa dữ liệu của chính người dùng theo đúng mục đích, nên chỉ tên file bị tìm, nội dung thì không.
- Lượt chạy phải lấy được đủ 5 thứ: ảnh note (tải, chia sẻ), Lá Khai Sinh (tải, chia sẻ), file dữ liệu. Thiếu một thứ thì lượt chạy đỏ.

Thân request gửi tới API là đường được phép, nên không bị tìm. Nó chỉ được dùng để chứng minh mỗi dấu đã thật sự tới API. Dấu nào chưa tới API thì lượt chạy đỏ, vì khi đó chưa kiểm được gì.

Giờ sinh được tìm ở mọi chỗ, cả khi viết kèm giây. Chỉ một thứ được bỏ qua: giờ ghi ở đầu dòng nhật ký máy chủ khi ngay sau nó là mức của dòng viết hoa (`INFO`, `WARNING`, `ERROR`…), vì đó là giờ của dòng nhật ký chứ không phải dữ liệu. Dòng nhật ký mở đầu bằng một giờ mà không có mức theo sau thì vẫn bị tìm, vì đó có thể chính là giờ sinh. Còn một trường hợp chưa phân biệt được: app in giờ sinh ở đầu dòng rồi viết ngay một chữ mức viết hoa sau nó. Nếu lượt chạy rơi đúng phút trùng giờ sinh giả và app ghi giờ hiện tại vào một chỗ tìm khác, lượt chạy có thể đỏ nhầm; khi đó xem chỗ tìm trong báo cáo rồi mới kết luận.

Nhật ký máy chủ được đọc sau khi API đã tắt hẳn và đóng đầu ra, nên các dòng ghi lúc tắt cũng được tìm. Nếu máy chủ không tắt trong 20 giây, lượt chạy hỏng (mã thoát 2), không tính là đạt.

Cơ sở dữ liệu của lượt chạy là một file tạm riêng, truyền cho máy chủ QA qua `LA_LANH_QA_DATABASE_URL`, và bị xoá khi chạy xong. Giá trị `LA_LANH_QA_DATABASE_URL` có sẵn trong môi trường của người chạy không được dùng.

## Cách chạy

```bash
pnpm qa:build
```

```bash
pnpm verify:leak
```

Lệnh này cũng chạy trong `pnpm qa:test`, nên có trong `pnpm check` và trong CI `pr-check` của mọi PR đổi code.

Mã thoát: `0` đạt; `1` thấy dấu hoặc lượt chạy chưa gửi đủ dấu; `2` lượt chạy hỏng (app không lên, một bước không bấm được).

Báo cáo chỉ in tên chỗ tìm, số mục đã tìm và loại dấu. Nó không in giá trị, URL hay dòng nhật ký, nên dán được vào PR công khai.

## Thử chính máy kiểm

Cố ý chèn một dấu vào một chỗ tìm. Lượt chạy phải đỏ (mã thoát 1):

```bash
node scripts/leak-canary.mjs --plant server-log
```

Tên chỗ tìm dùng được: `server-log`, `request-url`, `request-referer`, `external-request`, `error-report`, `error-response`, `browser-history`, `current-url`, `web-storage`, `file-name`, `share-image`, `image-metadata`.

Với `web-storage`, dấu được ghi vào Cache thật của trang (trong nội dung một câu trả lời đã lưu), nên lượt chạy chỉ đỏ khi phần đọc bộ nhớ thật sự đọc được nó. Với các chỗ tìm còn lại, dấu được thêm vào danh sách đã thu, nên chỉ thử được phần tìm dấu.

Riêng thông tin kèm trong ảnh PNG có test dựng một file PNG có chèn dấu ở từng loại phần (chữ, chữ nén, EXIF, giờ sửa file, phần lạ) và chờ máy kiểm báo đỏ.

Phần tìm dấu có test riêng, không cần trình duyệt: `node --test scripts/leak-canary-lib.test.mjs` (chạy trong `pnpm collab:test`).

## Khi lượt chạy đỏ

- Thấy dấu: đây là lỗi lộ dữ liệu, không sửa máy kiểm cho xanh. Tìm chỗ ghi ra (báo cáo cho biết chỗ tìm và loại dấu), sửa code, thêm test cho đúng chỗ đó.
- "chưa gửi dấu" hoặc "chưa lấy được": giao diện đã đổi nên kịch bản không còn đi tới bước đó. Sửa bước trong `scripts/leak-canary.mjs`.
- Mã thoát 2: xem dòng "bước xong" cuối cùng để biết hỏng ở bước nào.

## Chưa kiểm (không tính là đạt)

- Che nhanh, và màn tự che khi chuyền máy: app chưa có hai chức năng này.
- Chữ đã vẽ thành điểm ảnh trong ảnh PNG: máy không đọc chữ trong ảnh. Nó kiểm bản SVG mà ảnh được vẽ từ đó.
- File và ảnh chia sẻ trong app di động: lượt chạy dùng trình duyệt với bảng chia sẻ giả. Đường ghi file tạm của app di động chưa được chạy.
- Ảnh và link của trang chia sẻ công khai (safe link), và ảnh các màn khác ngoài note và Lá Khai Sinh.
- Tên hoặc biệt danh trong tên file: hành trình này chưa gõ tên nào.
- Nhật ký ở mức DEBUG, và nhật ký của máy chủ thật (staging, production): lượt chạy dùng mức nhật ký mặc định trên máy cục bộ với SQLite.
- Tên, biệt danh gõ ở Ghép đôi, Radar, Lá Chung (cũng đi qua lớp an toàn): lượt chạy mới gõ vào lớp an toàn qua màn Tarot.
- Trình duyệt WebKit và app di động.
- IndexedDB, và bộ nhớ của service worker (lượt chạy chặn service worker).

Khi thêm một màn nhận dữ liệu riêng, thêm dấu và bước cho màn đó vào `scripts/leak-canary-lib.mjs` và `scripts/leak-canary.mjs` trong cùng PR.
