# Swiss Ephemeris release gate

## Release decision — 2026-09-26

Chủ sản phẩm đã phê duyệt phát hành public-source theo AGPL. Toàn bộ combined/networked work dùng
Swiss Ephemeris được cấp phép AGPL-3.0-or-later, repository nguồn được public và link Corresponding
Source được hiển thị trong giao diện quyền dữ liệu. Release evidence phải ghi commit và image digest
thực tế sau khi deployment hoàn tất.

Lá Lành dùng Swiss Ephemeris native để tạo dữ liệu tính thật. Swiss Ephemeris có mô hình dual license: AGPL hoặc professional license. Việc chạy local cho phát triển không đồng nghĩa ứng dụng đóng source đã đủ quyền phân phối.

Trước khi public service hoặc gửi binary iOS/Android:

1. Legal chọn và ghi nhận một trong hai posture: toàn bộ work liên quan tuân AGPL, hoặc professional license còn hiệu lực bao phủ backend/binary được phân phối.
2. Lưu license proof, version, release commit và ephemeris checksum cùng release evidence.
3. Production startup từ chối bật chart service nếu license mode không được cấu hình.
4. Store listing và third-party notices khớp với lựa chọn pháp lý.

Web staging trên Cloud Run cũng là networked use và không được xem như chạy local. `Settings` từ
chối môi trường `staging`/`production` nếu `LA_LANH_SWISSEPH_LICENSE_MODE` vẫn là `development`;
script deploy còn yêu cầu bằng chứng vận hành tương ứng cho lựa chọn AGPL hoặc professional.

Nguồn chính thức: https://www.astro.com/swisseph/
