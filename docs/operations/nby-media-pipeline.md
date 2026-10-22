# Nơi bình yên — xử lý media trên máy quản trị

Trạng thái: công cụ cho PRD [Nơi bình yên v0.7](../foundation/la-lanh-noi-binh-yen-prd.md) NBY-09 AC02 và §7.6. Tính năng `noiBinhYen` vẫn tắt; tài liệu này không bật gì ở production.

Script [scripts/media/nby-media.sh](../../scripts/media/nby-media.sh) chạy trên máy của chủ sản phẩm, chỉ cần `ffmpeg` (có `libx264`, `libx265`, `aac`). Nó không tải file lên đâu, không gọi dịch vụ nào và không cần tài khoản.

## Trước khi chạy

1. **Video** do chủ sản phẩm tự tạo bằng công cụ AI, trên gói cho phép dùng thương mại (PRD §8.6). Máy đứng yên, khung đầu gần giống khung cuối, 8–30 giây, H.264/HEVC/ProRes, ≤ 200 MB. Không người, khuôn mặt, chữ, logo hay địa danh nhận diện được (PRD §7.5).
2. **Nhạc** (tùy chọn) có bằng chứng license **dùng trong app**, cho phép chỉnh sửa (PRD §8.3). License chỉ cho mạng xã hội/YouTube không đủ.
3. **Âm thanh cảnh** (tùy chọn) theo PRD §8.3: tự thu, Freesound CC0, NPS public domain, Sonniss GDC.
4. Lưu **bản gốc** đúng như công cụ xuất, ảnh chụp điều khoản tại ngày tạo, và ghi dòng mới vào sổ đăng ký asset. Sổ không chứa hóa đơn, thông tin thanh toán hay số tiền.

## Chạy

```bash
scripts/media/nby-media.sh -v canh-suoi-sang.mp4 -g "Tên công cụ" -a suoi.m4a -m nhac-dem.m4a -o out/canh-suoi-sang
```

| Cờ | Ý nghĩa |
|---|---|
| `-v` | Video nguồn. Bắt buộc đi cùng `-g` |
| `-g` | Tên công cụ AI đã tạo video; ghi vào thẻ nguồn gốc AI và mục manifest (tấm ⓘ đọc trường này) |
| `-a` | Âm thanh cảnh → vòng lặp 60 giây, −23 LUFS |
| `-m` | Nhạc → vòng lặp 60 giây, −32 LUFS (thấp hơn âm thanh cảnh khoảng 9 LU; app trộn bằng hai thanh trượt) |
| `-o` | Thư mục ra (mặc định `./out`) |
| `-t` | Số giây tối đa lấy từ video nguồn (mặc định 16; vòng lặp ra dài `t − x`) |
| `-x` | Độ dài đoạn hòa ở chỗ nối, giây (mặc định 1) |

Có thể chạy riêng từng phần, ví dụ chỉ `-m` cho một bản nhạc mới. Mỗi cảnh mất khoảng 20 giây trên máy Apple Silicon với preset mặc định.

## Script làm gì

- **Kiểm đầu vào** trước khi xử lý: video phải đúng codec, kích thước, thời lượng; âm thanh phải có rãnh audio và ≤ 50 MB. Sai thì dừng với mã 2 và không tạo thư mục ra.
- **Video:** cắt ≤ `t` giây; hòa `x` giây cuối vào đầu để lặp liền mạch (không ping-pong); phóng và cắt về 1080×1920, 24 fps, SAR 1:1; chỉnh màu mềm (giảm tương phản và bão hòa nhẹ, nâng vùng tối, ấm hơn một chút); xuất `<id>.h264.mp4` (mọi nền tảng) và `<id>.hevc.mp4` (thẻ `hvc1` cho Apple), **không có rãnh âm thanh**; poster `<id>.poster.jpg` là khung đầu.
- **Metadata:** xóa toàn bộ metadata gốc (vị trí, thiết bị, thẻ của công cụ, chương), rồi ghi một thẻ `comment`: `AI-generated (trainedAlgorithmicMedia); tool=<công cụ>; processed by la-lanh nby-media`.
- **Âm thanh:** lặp nguồn đủ 63 giây, chuẩn hóa EBU R128 (TP −2 dBTP), 48 kHz stereo, rồi hòa 3 giây cuối vào đầu; AAC 128 kb/s.
- **Mục manifest** `<id>.manifest-entry.json`: tên file, SHA-256 từng file, độ dài vòng lặp, `ai_label` (`tool`, `digital_source_type`) và loudness. Tên file và giá trị JSON chỉ gồm `[A-Za-z0-9._-]` (tên công cụ cho phép thêm dấu cách); ký tự khác thành `_`.

## Script chưa làm (phải có trước khi bật flag)

- Metadata IPTC/XMP `digitalSourceType` cho video và poster, và **ký lại C2PA** cho file phát hành với bản gốc làm thành phần (PRD NBY-AI-AC04). Chuyển mã luôn làm mất C2PA của bản gốc; nếu điều khoản công cụ cấm xóa Content Credentials thì chưa được xuất bản trước khi ký lại (NBY-AI-AC05).
- Kiểm nhấp nháy tự động (WCAG 2.3.1, PRD NBY-09 AC03).
- Đổi tên file theo hash nội dung, ký manifest, tải lên media origin: bước của Studio (PRD D14, §7.7). Script không có quyền ghi media origin.

## Duyệt sau khi chạy

Xem `<id>.h264.mp4` lặp liền 3 vòng (ví dụ `ffplay -loop 0`), kiểm chỗ nối có "bóng ma" không, tick checklist PRD §7.5 và lỗi AI, nghe vòng lặp âm thanh qua chỗ nối. Nếu khung đầu và cuối của nguồn khác xa, tăng `-x` hoặc tạo lại video.

## Kiểm thử

```bash
cd apps/api && .venv/bin/python -m pytest -q tests/scripts/test_nby_media_pipeline.py
```

Test chạy script thật với ffmpeg thật trên đầu vào tổng hợp, và tự bỏ qua nếu máy không có ffmpeg đủ encoder. Test kiểm: tên file an toàn, 1080×1920 24 fps, không rãnh âm thanh, độ dài vòng lặp, chỗ nối không lớn hơn ba lần bước khung thông thường (một nhát cắt thẳng của cùng đầu vào đo được gấp khoảng 70 lần), metadata vị trí bị xóa, thẻ AI có mặt, loudness ±1 LU, SHA-256 khớp, và từ chối đầu vào sai. Test không đánh giá được cảnh AI thật trông thế nào; việc đó vẫn là cổng duyệt của người.

## Bảo mật

ffmpeg phân tích file do công cụ bên thứ ba tạo. Chỉ chạy với file của chính chủ sản phẩm, giữ ffmpeg cập nhật bản vá, không chạy với quyền quản trị máy, không chạy trên máy chủ production.
