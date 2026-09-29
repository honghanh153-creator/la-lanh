# Lá Lành

Thư mục dự án trung tâm của Lá Lành.

## Giấy phép và mã nguồn

Toàn bộ sản phẩm được phát hành theo **GNU Affero General Public License v3.0 or later
(AGPL-3.0-or-later)**. Người dùng tương tác với Lá Lành qua mạng có thể lấy Corresponding Source
tại repository này. Xem [`LICENSE`](LICENSE), [`NOTICE`](NOTICE) và các thông báo gốc của Swiss
Ephemeris trong [`vendor/swisseph`](vendor/swisseph).

## Tài liệu nền tảng

Các tài liệu trong [`docs/foundation`](docs/foundation) là bộ tài liệu định hướng chính cho mọi hoạt động sản phẩm và kỹ thuật:

1. [`la-lanh-product-plan-v2.md`](docs/foundation/la-lanh-product-plan-v2.md) — **Tại sao:** tầm nhìn, nguyên tắc sản phẩm và kế hoạch launch 6 tháng.
2. [`la-lanh-prd.md`](docs/foundation/la-lanh-prd.md) — **Làm gì:** yêu cầu sản phẩm, phạm vi release và tiêu chí hoàn thành.
3. [`la-lanh-srs.md`](docs/foundation/la-lanh-srs.md) — **Xây thế nào:** yêu cầu hệ thống, kiến trúc, dữ liệu và luồng kỹ thuật.
4. [`la-lanh-astro-engine-spec.md`](docs/foundation/la-lanh-astro-engine-spec.md) — **Tính thế nào:** source of truth Astro Engine v2, Western/Jyotish, uncertainty, provenance, accuracy và release gates cho US-07 trở đi.

Trước khi bật content provider hoặc phát hành app native, dùng [`chart-synthesis-release-runbook.md`](docs/operations/chart-synthesis-release-runbook.md) làm checklist Go/No-Go, rollout, monitoring và rollback. Các quyết định UX đã chốt nằm ở [`2026-09-07-chart-synthesis-ux-first-decisions.md`](docs/decisions/2026-09-07-chart-synthesis-ux-first-decisions.md).

Khi đưa ra quyết định mới, cần kiểm tra sự nhất quán với bốn tầng: **tại sao → làm gì → xây thế nào → tính thế nào**. Nếu có mâu thuẫn, ưu tiên làm rõ và cập nhật tài liệu nền tảng trước khi triển khai.

## Chạy bản web MVP

Bản web hiện là bản preview/mobile-web để kiểm chứng sản phẩm. Sản phẩm chính vẫn được định hướng là app; web không nên được xem là đích cuối về phân phối.

Không mở trực tiếp `apps/web/index.html` bằng `file://` vì React Router, API proxy và service worker cần chạy qua server.

### Mở bản QA hoàn chỉnh

Nhấp đúp `Open Lá Lành QA.command`, hoặc chạy:

```bash
pnpm qa
```

Launcher sẽ build web, khởi động API + web trên máy và tự mở trình duyệt sau khi cả hai đã sẵn sàng. Nếu một bản QA đang chạy, launcher dùng lại bản đó thay vì tạo thêm tiến trình:

- Sản phẩm QA: http://127.0.0.1:5180/qa (tự chuyển về màn bắt đầu)
- Kiểm tra readiness: http://127.0.0.1:5180/__qa/ready

Môi trường QA chỉ bind vào `127.0.0.1`; máy khác trong mạng không thể truy cập. Dừng bằng `Ctrl+C` trong cửa sổ launcher.
QA giữ một database local riêng theo project và port để phiên review không biến mất khi restart. Thư mục chỉ cho user hiện tại truy cập (`0700`), nằm trong thư mục tạm của hệ điều hành và không dùng chung với database development/production.

- Cần một phiên sạch: chạy với `LA_LANH_QA_RESET=1`.
- Cần database tự xoá khi dừng: chạy với `LA_LANH_QA_EPHEMERAL=1`.
- Cần QA với database chỉ định: dùng `LA_LANH_QA_DATABASE_URL`; biến database chung vẫn bị bỏ qua để tránh chạm nhầm dữ liệu thật.

Chạy full stack development (cần Docker/PostgreSQL):

```bash
cp .env.example .env
# Điền POSTGRES_PASSWORD bằng một secret local ngẫu nhiên trước lần chạy đầu.
pnpm dev
```

Sau đó mở:

- Web app: http://127.0.0.1:5173
- API docs: http://127.0.0.1:8000/docs

Build production web:

```bash
pnpm web:build
```

Kiểm tra toàn bộ trước khi demo:

```bash
pnpm check
```

## Build app iOS và Android

`apps/mobile` là target Capacitor chính thức dùng cùng React UI và API contract; web ở trên chỉ là companion/QA reference. Native build không được dùng API tương đối vì `/v1` trong WebView sẽ trỏ vào bundle cục bộ. Cung cấp API HTTPS đã version hóa rồi build và sync:

```bash
VITE_API_BASE_URL=https://api.example.com/v1 pnpm mobile:sync
```

Lệnh này từ chối URL tương đối, HTTP, URL chứa credential/query/fragment; sau đó mới build web và copy bundle vào iOS/Android. Cấu hình native tắt release logging/WebView debugging, chặn cleartext/mixed content, không cho WebView điều hướng sang host ngoài, bật native HTTP/cookie và kèm Privacy Manifest iOS.

Mở source native sau khi sync:

```bash
pnpm --filter @la-lanh/mobile open:ios
pnpm --filter @la-lanh/mobile open:android
```

Lưu ý app-first:

- Ngày sinh, giờ sinh, nơi sinh và rich reading không nằm trong localStorage, URL share hoặc card public; xử lý riêng tư vẫn ở API.
- `pnpm mobile:sync` chỉ chứng minh bundle/config đồng bộ. Binary release còn cần production domain/CORS-cookie integration, signing, Xcode/Android toolchain, simulator/device QA, privacy report/store forms và các release gate trong `docs/legal`.
- Không bật provider sinh nội dung production hoặc generated Jyotish chỉ vì native build chạy; deterministic reading vẫn là đường chạy đầy đủ và an toàn mặc định.
- Public share/invite phải gửi `Cache-Control: no-store`, `Referrer-Policy: no-referrer` và `X-Robots-Tag: noindex, nofollow, noarchive` ở cả API lẫn web host.
