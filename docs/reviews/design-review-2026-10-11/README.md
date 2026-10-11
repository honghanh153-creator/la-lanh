# Design review — lớp "vitality" ngày 11/10/2026

Người review: agent thiết kế (chỉ đọc code, không sửa source). Chuẩn so sánh: [Ultraviolet Paper](../../design-directions/ultraviolet-paper-2026-10-06/README.md) và `reference.png` mà bạn đã chọn.

**Kết luận ngắn:** UI xấu đi vì lớp vitality **chồng thêm đồ** lên một hệ vốn dựa vào sự tiết chế. Có năm lý do chính:

1. Bong bóng Lá chen lên trên card tím nên card chính bị đẩy xuống.
2. Màu lá Tarot (olive, xanh baby, cam, teal) nằm ngoài bảng màu.
3. Skin Roast đổi accent toàn app sang đỏ cam và thêm viền mực kiểu sticker.
4. Foil, tia sáng, sao, hologram, sticker xoay rải khắp nơi.
5. Màn Home có thêm ba khối nữa: nhìn lại tuần (đang rỗng), nhắc nền tối và trăng.

Từng thứ riêng lẻ không tệ, nhưng cộng lại thì app trông "bận và rẻ hơn" chứ không "rực mà huyền bí". Phần lớn chỉ cần **xóa hoặc thu nhỏ**, không phải vẽ lại.

## Cách kiểm tra

- **SAU:** dev server `localhost:5173` (code đang sửa).
- **TRƯỚC:** worktree `HEAD` (468a004) chạy ở cổng 5191, dùng chung API local. Worktree đã gỡ sau khi chụp.
- **Môi trường chụp:** Playwright Chromium, 390×844 @2x, chụp thêm 360×740, nền tối và Roast. Mỗi phiên dùng một context mới.
- **Dữ liệu và luồng:** dữ liệu giả (15/06/1995, câu hỏi Tarot mẫu). Không dùng dữ liệu thật, không đăng nhập Google. Luồng: Welcome → Ngày sinh → Reveal → Home → Mood → Note → Tarot (hỏi, xòe, chọn 3, nghi thức, kết quả) → `/card` → `/birth-card` → `/profile` → `/radar` → `/saved`. Có chụp thêm lúc chờ phiên và Home lúc 22h10.
- **Lưu ý:** hôm nay là Chủ nhật nên thẻ "nhìn lại tuần" hiện ra. Nội dung Note ở cột TRƯỚC đôi khi khác vì đó là phiên khách khác, phần này không phải khác biệt UI.
- **Ảnh so sánh:** `compare/*.jpg` (cột trái TRƯỚC, giữa SAU, phải SAU·Roast nếu có). Ảnh zoom nằm ở `detail/`.

## 1. Kết luận từng màn

| Màn | So với HEAD | Ảnh | Lý do chính |
|---|---|---|---|
| Welcome | **Như cũ** (Direct) / **tệ hơn** (Roast) | [welcome](compare/welcome.jpg) | Direct không đổi. Roast: dấu `*` của logo, link "Đăng nhập" và icon chuyển sang đỏ `#c2361b`, CTA có viền mực và bóng lệch |
| Ngày sinh | Như cũ | [birth](compare/birth.jpg), [loading](compare/reveal-loading.jpg) | — |
| Chờ phiên | **Tốt hơn** | [session-loading](compare/session-loading.jpg) | Thay dòng chữ trơn bằng Lá, câu chờ và khung xương nhấp nháy |
| Reveal | **Tệ hơn** | [reveal](compare/reveal.jpg), [tối](compare/reveal-dark.jpg) | Ba tiêu điểm chồng nhau: hành tinh minh họa, Lá + bong bóng, vòng cung 96px phát sáng nhấp nháy trong card. Card cao thêm khoảng 200px, CTA bị đẩy xuống |
| Home | **Tệ hơn rõ** | [fold](compare/home-fold.jpg), [full](compare/home-full.jpg), [360](compare/home-fold-360.jpg), [22h](compare/home-night-full.jpg), [mood](compare/home-after-mood.jpg) | Card Note bị đẩy xuống **110px**. Ở 360×740, hàng Đọc thêm/👍/👎/share rơi khỏi màn đầu. Đường cung trang trí giờ đâm vào bong bóng. Chip trăng là một chấm đen. Foil tạo vệt mờ ở góc card. Thẻ Chủ nhật hiện ở trạng thái rỗng. Sau 21h có thêm card tối thứ hai ngay dưới card tím |
| Note chi tiết | Như cũ | [note](compare/note-detail.jpg) | Thêm "Vì sao hôm nay?" là đúng, nhưng khoảng trống dưới link hơi thừa |
| Tarot – hỏi | **Tệ hơn** | [ask](compare/tarot-ask.jpg), [360](compare/tarot-ask-360.jpg) | Bong bóng Lá đẩy CTA "Xòe 3 lá" khỏi màn đầu. Câu của Lá không thêm thông tin |
| Tarot – xòe/chọn | **Lẫn lộn** | [fan](compare/tarot-fan.jpg), [đã chọn 2](compare/tarot-fan-picked2.jpg), [tối](compare/tarot-fan-picked2-dark.jpg) | Tốt: ô vị trí có preview lá. Xấu: 78 mặt lưng hoa văn vàng–lime lặp dày đặc. Mặt lá theo bộ có màu olive, xanh baby, cam hồng, nằm ngoài bảng màu |
| Tarot – nghi thức | **Lẫn lộn** | [ceremony](compare/tarot-ceremony.jpg), [late](compare/tarot-ceremony-late.jpg) | Lật ra lá thật là ý đúng. Nhưng ba lá sát mép và sát nhau, màu olive/xanh baby phá nền tím |
| Tarot – kết quả | **Lẫn lộn** | [result](compare/tarot-result.jpg), [360](compare/tarot-result-360.jpg) | Hàng spread trên đầu là ý tốt. Nhưng thumbnail lặp lại trong danh sách, tên lá in hai lần, màu lệch bảng |
| Thẻ Note `/card` | **Tốt hơn, nhưng ồn** | [card](compare/card-full.jpg), [tối](compare/card-fold-dark.jpg), [zoom](detail/zoom-share.jpg) | Hook to, đọc được ngay, đúng chất ảnh để share. Nhưng có 40 ngôi sao, emblem hologram cầu vồng, sticker xoay, wordmark "lalanh" sai nhận diện, hàng chấm pha trăng không có nghĩa |
| Thẻ khai sinh `/birth-card` | **Tốt hơn, nhưng ồn** | [birth-card](compare/birthcard-full.jpg) | Giống `/card`. Có hai sticker xoay ngược chiều nhau |
| Mình `/profile` | **Tệ hơn về craft** | [fold](compare/profile-fold.jpg), [full](compare/profile-full.jpg), [360](compare/profile-fold-360.jpg), [zoom](detail/zoom-profile.jpg) | Card danh tính nhồi khoảng 12 phần tử. Chữ 11px trong ô khóa. Hai lớp màu loang làm texture đục và ngả xanh. Picker vibe dùng emoji hệ điều hành. Gom cài đặt là đúng, nhưng toggle nền tối bị giấu |
| Hợp gu `/radar` | Như cũ (Roast tệ hơn: tim và nav đỏ) | [radar](compare/radar-fold.jpg) | — |
| Đã lưu | Như cũ | [saved](compare/saved-fold.jpg) | — |
| Nền tối | Như cũ, có lỗi cũ | [home tối](compare/home-full-dark.jpg), [profile tối](compare/profile-fold-dark.jpg) | Nút lime "Thêm giờ & nơi sinh" có chữ `#c9aeff` trên nền `#dfff4f`, tương phản **1.69:1**. Lỗi có từ HEAD, vẫn chưa sửa |

## 2. Top 10 vấn đề (xếp theo tác động thị giác)

**1. Lá + bong bóng chen lên trên vùng trọng tâm (Home, Tarot hỏi, Reveal)**

- **Ở đâu:**
  - `features/home/HomePage.tsx:308` (`section.home-la`) và `home-vitality.css` (`.home-la`, `.home-la .la-says__bubble`).
  - `features/tarot/TarotPage.tsx:397` (`<TarotWhisper step="ask" />`) và `:340`.
  - `features/reveal/RevealPage.tsx:86` (`LaSays.reveal-la`).
- **Vấn đề:** bong bóng rộng khoảng 290px, nền tint tím, nằm giữa header và card tím nên thành khối thứ hai tranh tiêu điểm. Câu nói là câu đệm ("Chiều rồi. Xem nhanh…"), không có thông tin.
- **Sửa:**
  - Xóa `section.home-la` khỏi Home.
  - Chỉ giữ lời chào dưới dạng **một dòng chữ** thay dòng ngày: `Chủ Nhật, 11.10 · Trăng mới`. Lời chào theo giờ nếu muốn thì đặt trong `aria-live`, 15px, màu `--uv-muted`, không bong bóng, không mascot.
  - Tarot: xóa `TarotWhisper step="ask"`. Nếu cần gợi ý, dùng helper 13px **dưới** CTA.
  - Reveal: xóa `LaSays.reveal-la`.
  - Mascot chỉ xuất hiện ở trạng thái chờ, trạng thái rỗng và khoảnh khắc ăn mừng, không bao giờ nằm trên card tím.

**2. Màu mặt lá Tarot lệch hẳn bảng màu**

- **Ở đâu:** `features/tarot/tarotArtSpec.ts:61–69`:
  - pentacles `#a9c53a→#5a6416` (olive)
  - swords `#a48ff2→#3d68c9` (xanh baby)
  - wands `#ff9b5e→#c7365a` (cam hồng)
  - cups `#2ec4bd→#1f4fa6` (teal)
- **Vấn đề:** số La Mã màu kem trên nền olive chỉ đạt **1.86:1**, trên wands **1.98:1**.
- **Sửa:**
  - Mọi mặt lá dùng chung nền `#4c2e8e→#2a1159` (giống `major`), mực `#fff9e9`.
  - Phân biệt bộ bằng **màu icon** chỉ trong `#dfff4f` / `#ffd36e` / `#fff9e9`, không bằng nền.
  - Bỏ lớp foil cầu vồng (`TarotCardArt.tsx:81–85`, `:577–580`). Nếu giữ thì để opacity ≤ 0.08.

**3. Skin Roast đổi màu cả app và trông kiểu sticker rẻ**

- **Ở đâu:** `shared/styles/vibe-roast.css`.
  - `--uv-accent: #c2361b` khiến dấu `*` logo, tab nav đang chọn, link, icon tạm dừng và chữ "Thêm giờ & nơi sinh" thành đỏ.
  - Viền mực 2px với `box-shadow: 3px 3px 0`.
  - Card tím có `6px 6px 0 var(--roast-coral)`.
  - Eyebrow có `::after " · 🔥 roast"`.
- **Sửa:**
  - **Xóa toàn bộ phần thị giác** trong file này: đổi accent, viền và bóng, bóng coral, foil coral, nhãn 🔥.
  - Roast **chỉ khác ở lời** (copy).
  - Nếu cần một tín hiệu nhỏ, giữ biểu cảm nhướng mày của mascot ở trạng thái chờ là đủ.

**4. Home quá dài, quá nhiều khối**

- **Ở đâu:** `features/home/HomeRituals.tsx` (`.home-week-recap`, `.home-night-nudge`) và `home-vitality.css`.
- **Vấn đề:**
  - Thẻ Chủ nhật hiện cả khi chưa có note nào được lưu (*"Tuần này chưa có note nào được giữ"*), tức là một khối rỗng chiếm 150px.
  - Gợi ý nền tối là **card tối thứ hai** (`linear-gradient(135deg,#1d1736,#3b2475)`) ngay dưới card tím, và lặp "Khuya rồi" với câu của Lá.
- **Sửa:**
  - Chỉ render recap khi `thisWeek.length ≥ 1`, và đặt nó dưới hai lối Tarot/Hợp gu.
  - Gợi ý nền tối thành **một dòng nền kem**, viền `--uv-line`, cao 48px, icon trăng 20px, một nút chữ "Bật nền tối" màu `--uv-accent`, nút ✕ 44×44px. Đặt **dưới** hai lối Tarot/Hợp gu, không đặt dưới Note.
  - Dưới Note chỉ có tối đa: Tarot/Hợp gu và một card ngữ cảnh.

**5. Foil và tia sáng trên card Note trông như màn hình bẩn**

- **Ở đâu:** `home-vitality.css`, gồm `.home-daily-signal__paper::after` (foil 7.5s lặp vô hạn) và `[data-ritual="today"] .home-daily-signal::before` (chấm sáng ngẫu nhiên).
- **Vấn đề:** ở khung tĩnh, foil là một vệt tím mờ ở góc trên trái. Tia sáng thành các chấm rơi lả tả trên chữ. Xem [zoom](detail/zoom-home.jpg) và [home-loading](compare/home-loading.jpg).
- **Sửa:**
  - Xóa foil.
  - Giữ nghi thức lật card nhưng ngắn lại: 500ms, `rotateX(-14deg)`, **bỏ** `filter: brightness(1.6)`, **bỏ** chấm sáng.
  - Foil trên `.profile-identity::after` xử lý giống vậy.

**6. Card danh tính ở Mình bị nhồi nhét và đục màu**

- **Ở đâu:** `features/profile/profile-identity.css` và `ProfilePage.tsx`.
- **Vấn đề:**
  - Hai lớp `radial-gradient` (màu nguyên tố, ví dụ air `#8fc7ff`, cộng thêm lime 18%) chồng lên texture làm card ngả xanh và đục.
  - Chữ ô khóa `em` 11px, nhãn `small` 12px.
  - Có ba nhãn trùng ý nhau ("Nguyên tố Khí", "Vibe: Lanh", rồi lại "Nguồn: Mặt Trời Song Tử…").
  - Có mascot nhỏ trong card, hai nút xếp dọc.
- **Sửa:**
  - Bỏ cả hai radial và `::after`.
  - Bỏ `LaSpirit` trong card.
  - Bỏ dòng "Nguồn…" (chuyển vào Cài đặt & dữ liệu).
  - Ba ô: số đo nhỏ nhất 13px. Ô khóa chỉ ghi "Thêm giờ sinh" 13px, icon khóa 18px, viền dashed `rgb(223 255 79 / 40%)`.
  - Trong card chỉ giữ **một** CTA lime "Tạo thẻ khoe vibe". "Note đã lưu" chuyển thành dòng danh sách ngay dưới card.
  - Đưa toggle "Chế độ tối" ra khỏi disclosure, thành một dòng ngay dưới card. Ultraviolet yêu cầu toggle nằm thấy được trong Mình.

**7. Thẻ share ồn**

- **Ở đâu:** `features/card/shareArt.ts`.
  - `starField(…, 26|40)` ở `:468`.
  - Emblem `url(#ll-foil)` cầu vồng ở `:342–345`.
  - `sticker(… rotate: -4 / 8 …)` ở `:374–388`.
  - Wordmark `lalanh` ở `:506`.
  - `moonPhases` ở `:507`.
  - Vòng tròn accent ở góc dưới phải ở `:502`.
- **Sửa:**
  - Giữ bố cục hook-first và chữ to (đây là phần tốt nhất của đợt này).
  - Số sao ≤ 6, chỉ ở mép trên.
  - Emblem đổi thành đĩa kem `#fff9e9` + vòng lime 4px + glyph tím `#4c2e8e`, không gradient cầu vồng.
  - Chỉ **một** sticker, `rotate: 0`.
  - Wordmark đúng là "Lá Lành*".
  - Bỏ hàng chấm pha trăng và vòng tròn góc.

**8. Reveal có ba tiêu điểm chồng nhau**

- **Ở đâu:** `features/reveal/reveal-vitality.css` (`.reveal-emblem span` 96px, `box-shadow` phát sáng, pulse 3.2s vô hạn, radial màu nguyên tố) cộng với ảnh hành tinh sẵn có cộng với Lá.
- **Sửa:**
  - Bỏ Lá (xem vấn đề 1).
  - Emblem còn 64px, viền lime 1.5px, nền `rgb(255 249 233 / 10%)`, **không** glow, **không** pulse, chỉ animation vào 600ms một lần.
  - Bỏ radial màu nguyên tố.
  - Có emblem trong card thì thu ảnh hành tinh phía trên còn 96px, hoặc bỏ hẳn.

**9. Mascot Lá vẽ còn thô**

- **Ở đâu:** `shared/ui/la/LaSpirit.tsx`.
- **Vấn đề:**
  - Gân lá lime chạy thẳng qua giữa mặt, đè lên miệng, nên đọc như mặt bị rạch. Xem [zoom](detail/zoom-la.jpg).
  - Mắt khoảng 5px ở size 48.
  - Vòng `glow` lime quanh thân thành vệt bẩn trên nền kem.
  - Float, glow, twinkle và blink chạy đồng thời và vô hạn.
  - Ở 48px nó đọc như quả cà tím hơn là chiếc lá.
- **Sửa (nếu còn giữ Lá):**
  - Gân dừng ở `y≤24`, phía trên mắt. Bỏ ba gân phụ.
  - Bỏ `la-spirit__glow`.
  - Mắt `rx 3.2 / ry 3.8`.
  - Chỉ giữ blink và chỉ ở trạng thái chờ.
  - Tốt hơn: thay bằng bạn đồng hành C (xem mục 4) và dùng Lá chỉ cho trạng thái chờ.

**10. Chip trăng và đường cung trang trí**

- **Ở đâu:** `.home-sky-chip` (margin-left 58px, chấm `#3a2a5c` đặc khi trăng mới) và `MoonGlyph`.
- **Vấn đề:** trăng mới hiện như một chấm đen hoặc bullet. Chip lơ lửng, không thẳng hàng với gì. Đường cung từ avatar giờ cắm vào mép trên bong bóng thay vì nối vào card.
- **Sửa:**
  - Gộp vào dòng ngày: `Chủ Nhật, 11.10 · ◐ Trăng mới`.
  - Glyph 14px chỉ có nét viền `--uv-accent` khi illumination < 0.05.
  - Bỏ `.home-sky-chip` riêng.
  - Khi bỏ khối Lá, đường cung tự nối lại vào card như `reference.png`.

**Ngoài top 10:**

- **Lưng lá khi xòe** (`TarotCardBack`): hoa văn mandala vàng–lime lặp 78 lần, quá dày. Nên dùng lưng giấy tím texture + một ngôi sao lime 14px như HEAD, giữ vòng cung nhưng mỗi lá lộ ít nhất 24px.
- **Mood trigger** hiện emoji raster ở 1.55rem. Chấp nhận được vì sheet vốn dùng emoji, nhưng nên giảm về 22px trong vòng tròn 44px.
- **Picker vibe** (`shared/vibe/VibePicker.tsx`) dùng emoji 🌿🔥 hệ điều hành. Nên đổi sang icon Phosphor nét như phần còn lại.

## 3. Nên giữ

- `LaLoading` cho trạng thái chờ phiên và chờ dữ liệu, hiện sau 220ms. Có thể thu mascot xuống 40px.
- Lật ra **lá thật** trong nghi thức và hàng spread trên trang kết quả, sau khi đổi màu theo vấn đề 2.
- Ô vị trí có preview lá đã chọn khi xòe bài.
- Bố cục share **hook-first**, chữ lớn, không kèm ngày/giờ/nơi sinh.
- Gom cài đặt vào "Cài đặt & dữ liệu" (nhưng đưa toggle tối ra ngoài) và bỏ vibe khỏi Welcome.
- Vi tương tác nhỏ: nút co lại khi bấm, icon 👍 nảy. Không gây ồn, đã tôn trọng reduced-motion.
- Link "Vì sao hôm nay?" và câu mẫu trong picker vibe.

## 4. Bạn đồng hành và vibe

**Companion lab** đã có tại `/companion-lab`. Xem [ảnh](detail/companion-lab-full.jpg) và [zoom](detail/zoom-companions.jpg).

- **B · Mầm Aura: không nên dùng.**
  - Slime xanh neon (khác hẳn lime `#dfff4f`) cộng hoa hồng, má hồng, răng nanh và hào quang cam.
  - Đây là ngôn ngữ game casual, đối nghịch với "giấy tím huyền bí".
  - Nó cạnh tranh trực tiếp với màu lime dùng cho hành động.
- **C · Cửa sổ trời: hướng đúng, cần siết bảng màu.**
  - Khung vòm và viền tím hợp với Ultraviolet.
  - Nhưng nền đồi olive và đất vàng nâu làm cây trông úa.
  - Sửa: trời ban ngày gradient `#c9aeff→#fff9e9`, đêm `#2a1159→#4c2e8e`. Đồi `#3a2470` hoặc tím nhạt. Lá cây lime `#dfff4f` + kem. Mặt trời/trăng kem. Bỏ olive và nâu.
- **Lab chưa đổi theo nền tối:** trang vẫn sáng khi đặt `la-lanh-theme-v1=dark`. Cần kiểm tra lại trước khi duyệt C ở nền tối.
- **Chỗ đặt C:**
  - **Không đặt trên card Note.**
  - Ở Mình: thay vị trí mascot, 96–120px, là "nhà" của bạn đồng hành, kèm câu tăng trưởng 13px.
  - Ở Home: nhiều nhất là avatar 40px thay icon ở header, hoặc trạng thái chờ.
  - Chỉ dùng một bạn đồng hành, không để cả Lá lẫn cây.

**Vibe (Direct/Roast):**

- **Chỗ đặt:** chỉ trong Mình, ở một dòng "Giọng của Lá" mở ra segmented control 2 lựa chọn (cao 44px, selected nền `--uv-violet` chữ kem), kèm câu mẫu ngay bên dưới. Không dùng card lớn, không emoji.
- **Giao diện:** Roast **giống hệt** Direct. Chỉ copy khác.
- **Lỗi môi trường:** khi chọn Roast, `POST /v1/tarot/sessions` trả **422** (`voice` "Extra inputs are not permitted"), nên chưa xòe được bài. Source đã nhận `voice`, nhưng tiến trình uvicorn chạy từ 12:49, không `--reload`, nên còn chạy code cũ. Cần restart API trước khi thử Roast. Tôi không restart theo chỉ dẫn.

## 5. Kế hoạch sửa một lượt (theo thứ tự ưu tiên)

1. **`vibe-roast.css`:** xóa mọi rule thị giác. File chỉ còn `data-vibe` để JS đọc.
2. **Home:**
   - Xóa `section.home-la`, gộp ngày + trăng thành một dòng, xóa `.home-sky-chip` riêng.
   - Xóa foil `::after` và chấm sáng `::before`. Nghi thức còn 500ms, không brightness.
   - Recap chỉ hiện khi có note lưu. Gợi ý nền tối thành một dòng nền kem dưới hai lối Tarot/Hợp gu.
3. **Tarot:**
   - `tarotArtSpec.ts`: mọi bộ dùng nền violet, phân biệt bộ bằng màu icon trong kem/lime/vàng.
   - Bỏ foil cầu vồng. Lưng lá dùng texture + một ngôi sao.
   - Xóa `TarotWhisper step="ask"`.
   - Thêm gutter ≥ 12px giữa các lá ở nghi thức và trang kết quả.
   - Bỏ tên lá in trong thumbnail khi tên đã có ở bên cạnh.
4. **Reveal:** bỏ Lá. Emblem 64px, không glow, không pulse. Bỏ radial màu nguyên tố.
5. **Mình:**
   - Card danh tính: bỏ radial, foil, mascot và dòng nguồn. Chữ tối thiểu 13px. Một CTA.
   - Toggle tối ra ngoài disclosure. Picker vibe thành segmented control.
6. **Share (`shareArt.ts`):** sao ≤ 6, emblem đĩa kem + vòng lime, một sticker không xoay, wordmark "Lá Lành*", bỏ chấm trăng và vòng góc.
7. **Lá:** sửa gân, mắt và glow theo vấn đề 9. Chỉ dùng trong `LaLoading`.
8. **Lỗi cũ nhưng P1:** nút lime ở nền tối dùng chữ `#341b62` thay `--uv-accent` (`.ultraviolet-app` dark). Tương phản hiện tại 1.69:1, cần ≥ 4.5:1.
9. **Kiểm tra lại:** chụp lại 390 và 360 cho Home, Tarot và Mình. Mục tiêu: card Note với hàng hành động nằm trọn trong màn đầu ở 360×740.

## Báo cáo bàn giao (theo AGENTS.md)

**Nguồn đã đọc:**

- `AGENTS.md`
- Ultraviolet Paper README và `reference.png`. Không tìm thấy `design-qa.md` trong thư mục direction.
- `docs/design-directions/vitality-2026-10-11/README.md`
- Diff `apps/web/src` và các file mới: `shared/ui/la/*`, `vitality.css`, `vibe-roast.css`, `home-vitality.css`, `profile-identity.css`, `reveal-vitality.css`, `tarotArtSpec.ts`, `TarotCardArt.tsx`, `shareArt.ts`, `HomeRituals.tsx`, `shared/ui/companion/*`, `/companion-lab`.
- Báo cáo nghiên cứu `reports/Bạn đồng hành cây lớn dần.md` chỉ được tham chiếu qua nội dung lab, chưa đọc toàn văn.

**Đã sửa:** không có. Review này chỉ đọc code.

**Rủi ro còn mở:**

- API local chạy code cũ nên Roast Tarot lỗi 422.
- Tương phản nút lime ở nền tối 1.69:1 (lỗi cũ).
- Số La Mã trên mặt lá Tarot có tương phản < 3:1.
- Lab companion chưa hỗ trợ nền tối.

**Bảo mật và quyền riêng tư:** không phát hiện dữ liệu cá nhân mới trong phần UI đã xem. Thẻ share vẫn không kèm ngày/giờ/nơi sinh. Không phát hiện vấn đề P0/P1 mới. Đây không phải audit bảo mật đầy đủ.

**AC/DoD chưa xong:**

- Chưa có QA thủ công cho nhánh Home có giờ sinh chính xác (Mặt Trăng/Cung Mọc mở).
- Chưa chụp Roast trên Tarot do lỗi 422.
- Chưa so sánh `/share/:token` công khai.
- Chưa có QA reduced-motion bằng ảnh.
