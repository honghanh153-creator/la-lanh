# Lá Lành — Product Requirements Document (PRD)

> Phiên bản: 1.0 · Cập nhật: tháng 6/2026
> Tài liệu này map trực tiếp từ Playbook Sản phẩm & Launch 6 tháng. Mọi quyết định "tại sao" đã được giải thích ở đó — PRD này tập trung vào "làm gì, làm thế nào, biết khi nào xong".

---

## 0. Tổng quan release

| Release | Tên | Map tháng | Mục tiêu chính | Tầng sản phẩm |
|---|---|---|---|---|
| v0.1 | Lá Khai Sinh | Tháng 1 | Identity artifact + Daily Astro engine | Tầng 1 |
| v0.2 | Lá Chứng & Pitch | Tháng 2 | Social proof từ bạn thân | Tầng 2 |
| v0.3 | Lá Ghép & Transit | Tháng 3 | Relationship invite + transit engine thật | Tầng 2→3 |
| v0.4 | Vòng Lá | Tháng 4 | Matching theo cohort, có giới hạn thời gian | Tầng 3 |
| v0.5 | Lá Mai Room | Tháng 5 | Marketplace, Lá Dẫn, reader booking | Tầng 4 |
| v0.6 | Season Recap | Tháng 6 | Wrapped-style recap + Premium beta | Tầng 1–4 hoàn thiện |

**Nguyên tắc release:** mỗi version phải chạy độc lập được — không version nào phá vỡ hoặc làm gián đoạn version trước. v0.4 (Vòng Lá) không được làm v0.1 (Daily Astro) ngừng hoạt động; đây là lý do kiến trúc 4 tầng tồn tại (xem Playbook, Phần 3).

---

## 0.5. Astrology Engine Foundation — quy tắc bắt buộc cho mọi feature

> Đây là chương nền tảng. Mọi feature từ v0.1 đến v0.6 đều phải tuân theo quy tắc ở đây. Nếu một feature mới phát sinh sau này cần đọc chart theo cách khác, phải sửa chương này trước, không được tự ý lệch trong code của riêng feature đó.

### 0.5.1. Vì sao chương này tồn tại

Có hai lăng kính được hỗ trợ — Western Tropical và Jyotish Sidereal — và chúng không tương thích ở cấp snapshot/cách diễn giải. Hai hệ có thể cho vị trí cung khác nhau vì dùng mốc zodiac khác nhau. Vì vậy app không trộn placement, aspect, thuật ngữ hay content của hai hệ; thay vào đó, người dùng chủ động chuyển **Hệ đọc**, mỗi hệ có snapshot, preset và provenance riêng. UI phải giải thích “hai lăng kính” thay vì ngụ ý một kết quả đúng còn kết quả kia sai.

**Quyết định rollout đã được cập nhật ngày 2026-09-04:** Western Tropical vẫn là preset nội dung đầu tiên; hệ thống đồng thời hỗ trợ kiến trúc và product switch cho Jyotish Sidereal như một preset độc lập, không phải một nhãn cấu hình trên chart Western. Jyotish chỉ public khi golden tests và domain-expert content review đạt gate. Contract chi tiết và thứ tự ưu tiên nằm tại [`la-lanh-astro-engine-spec.md`](./la-lanh-astro-engine-spec.md).

### 0.5.2. House system — quy tắc chọn theo dữ liệu sẵn có

| Điều kiện dữ liệu user | House system dùng | Lý do |
|---|---|---|
| Có ngày sinh, KHÔNG có giờ sinh chính xác | Không tính House — chỉ hiển thị Sun/Venus/Mars sign | Không thể tính House nếu thiếu giờ sinh, hiển thị sai sẽ phá vỡ trust |
| Có giờ sinh dạng "khoảng" (sáng/trưa/chiều/tối) | **Whole Sign** | Whole Sign chỉ cần Ascendant rơi vào đúng 1 cung là tính được cả 12 nhà — chịu sai số giờ sinh tốt hơn nhiều so với Placidus, vốn nhạy cảm với từng phút |
| Có giờ sinh chính xác (user xác nhận từ giấy khai sinh) | **Placidus** (nâng cấp, chỉ áp dụng cho Premium/Reader reading) | Placidus chia nhà không đều theo thời gian thực tế — chính xác hơn nhưng đòi hỏi dữ liệu đầu vào chính xác đến từng phút, nếu sai sẽ lệch toàn bộ nhà |

**Quy tắc bắt buộc:** Whole Sign là mặc định cho TOÀN BỘ tính năng tự động (Daily Astro, Transit Engine, Vòng Lá). Placidus chỉ bật thủ công khi Lá Dẫn/reader làm reading sâu 1-1 và xác nhận trực tiếp với user về độ chính xác giờ sinh. Hai house system không được trộn trong cùng một lần đọc cho cùng một user.

### 0.5.3. Bốn loại chart và mục đích sử dụng — bảng tra cứu bắt buộc

| Loại chart | Cần dữ liệu gì | Dùng cho feature nào | Output chính |
|---|---|---|---|
| **Natal Chart** | Ngày sinh (bắt buộc), giờ + nơi sinh (optional, tăng độ chính xác) | F1.1 Astro Profile, F1.2 Daily Astro, F1.3 Lá Khai Sinh Card | Sun/Moon/Rising/Venus/Mars sign, House placement (nếu đủ dữ liệu) |
| **Transit Chart** | Natal Chart của user + vị trí hành tinh tại thời điểm hiện tại | F1.2 Daily Astro, F3.1 Transit Engine | Hành tinh nào đang ở House nào của user, đang tạo góc chiếu (aspect) gì với natal chart |
| **Synastry Chart** | Natal Chart của 2 người (A và B) | F3.2 Lá Ghép, F4.1 Compatibility Score | So sánh trực tiếp placement của A lên House của B và ngược lại — ra điểm hợp ở từng lĩnh vực (tình cảm, giao tiếp, xung đột) |
| **Composite Chart** | Natal Chart của 2 người, tính điểm giữa (midpoint) của từng hành tinh | F5.2 Reader Booking (đọc sâu mối quan hệ đã xác lập) | Một "chart thứ ba" đại diện cho bản chất mối quan hệ — KHÔNG dùng cho matching tự động vì cách đọc phức tạp, chỉ phù hợp khi có con người (reader) diễn giải trực tiếp |

**Quy tắc áp dụng theo mục đích — tránh dùng sai chart cho sai việc:**

- Muốn biết "tôi là ai" → Natal Chart
- Muốn biết "tại sao hôm nay/tháng này tôi cảm thấy vậy" → Transit Chart (luôn áp lên Natal Chart của user, không bao giờ đọc Transit một mình)
- Muốn biết "tôi và người này có hợp không" (trước khi quen, đang tìm hiểu) → Synastry Chart — đây là chart dùng cho TOÀN BỘ tính năng matching tự động (Lá Ghép, Vòng Lá compatibility score)
- Muốn biết "mối quan hệ này có bản chất gì" (đã yêu nhau, đã là bạn thân lâu năm) → Composite Chart — CHỈ dùng trong bối cảnh có Lá Dẫn/reader diễn giải, không tự động hóa vì dễ đọc sai nếu không có con người kiểm soát ngữ cảnh

### 0.5.4. Aspect (góc chiếu) — quy tắc orb dùng trong tính toán

Aspect là góc giữa 2 hành tinh, quyết định chúng "hợp" hay "căng" với nhau. Mỗi loại tính năng cần độ rộng orb (sai số cho phép) khác nhau:

| Tính năng | Orb áp dụng | Lý do |
|---|---|---|
| Daily Astro (Transit nhanh — Moon) | ±6° | Moon di chuyển nhanh (~13°/ngày), orb rộng để bắt được ảnh hưởng cả ngày |
| Transit Engine (Saturn/Jupiter/Pluto — chậm) | ±2° cho exact aspect, ±5° cho "đang tới gần/đang rời xa" | Transit chậm cần chính xác cao vì ảnh hưởng kéo dài hàng tháng/năm, sai orb sẽ báo sai cả giai đoạn |
| Synastry compatibility (Lá Ghép, Vòng Lá) | ±3° cho Sun/Moon/Venus/Mars aspect | Cân bằng giữa độ chính xác và việc không loại bỏ quá nhiều cặp tiềm năng do orb quá hẹp |

### 0.5.5. "Skill" tham chiếu bắt buộc — gắn vào từng feature

Từ chương này trở đi, mỗi feature trong PRD có dòng **"Astro Skill áp dụng"** ngay dưới Acceptance Criteria, chỉ rõ: loại chart nào, house system nào, orb nào, và cách đọc kết quả thành content. Đây không phải optional — dev và content team phải tham chiếu đúng dòng này khi implement, không tự suy diễn.

---

## 1. v0.1 — Lá Khai Sinh (Tháng 1)

### 1.1. Mục tiêu release

Tạo ra một artifact cá nhân hóa (Lá Khai Sinh Card) đủ chính xác và đủ "trúng" để người dùng đầu tiên tự nguyện share — không cần cơ chế ép buộc nào. Đây là nền móng của toàn bộ growth loop sau này.

### 1.2. Danh sách feature

#### F1.1 — Onboarding & Astro Profile Basic

**User story:**
> Là một người dùng mới, tôi muốn nhập ngày sinh của mình và ngay lập tức thấy được một bản mô tả cá nhân hóa, để tôi cảm thấy app này "biết gì đó" về tôi chỉ sau vài giây.

**Acceptance criteria:**
- [ ] User có thể tạo tài khoản bằng số điện thoại hoặc email, không bắt buộc cả hai
- [ ] Sau khi nhập ngày sinh (bắt buộc) → hệ thống tính được Sun sign trong < 2 giây
- [ ] User KHÔNG bị bắt nhập giờ sinh/nơi sinh ở bước onboarding — chỉ có nút "Thêm sau" rõ ràng, không bị ẩn
- [ ] Astro Profile Basic hiển thị: Sun sign, nguyên tố (lửa/đất/khí/nước), 1 đoạn mô tả tính cách (~80-120 từ) áp dụng đúng 4 quy tắc viết content (xem Playbook Phần 5)
- [ ] Consent screen hiển thị TRƯỚC khi nhập ngày sinh, giải thích rõ: dữ liệu dùng để làm gì, lưu ở đâu, user có thể xóa khi nào
- [ ] Toàn bộ flow onboarding (mở app → thấy Astro Profile Basic) hoàn thành trong ≤ 90 giây cho 90% user (đo bằng analytics)

**Data model:**

```
User {
  id: UUID
  phone_or_email: string (encrypted)
  display_name: string
  created_at: timestamp
  consent_version: string         // version của consent text user đã đồng ý
  consent_timestamp: timestamp
}

BirthData {
  user_id: UUID (FK → User)
  birth_date: date                // bắt buộc
  birth_time: time | null         // optional, Level 2
  birth_time_precision: enum('exact','approximate','unknown') | null
  birth_place: string | null      // optional, Level 3 — cần geocode để tính house
  birth_place_lat: float | null
  birth_place_lng: float | null
  birth_place_timezone: string | null
  profile_level: int              // 1-5, tính từ dữ liệu đã có (xem F1.4)
  updated_at: timestamp
}

NatalChart {
  user_id: UUID (FK → User)
  sun_sign: enum(12 cung)
  moon_sign: enum(12 cung) | null      // null nếu chưa có birth_time
  rising_sign: enum(12 cung) | null    // null nếu chưa có birth_place
  venus_sign: enum(12 cung)
  mars_sign: enum(12 cung)
  houses: JSON | null              // null nếu chưa có đủ birth_time + birth_place
  computed_at: timestamp
  ephemeris_version: string        // version của bộ dữ liệu thiên văn dùng để tính
}
```

**Edge case cần xử lý:**
- User không biết giờ sinh chính xác → cho phép chọn "khoảng" (sáng/trưa/chiều/tối) thay vì bắt từ chối hoàn toàn, độ chính xác Moon sign giảm nhưng vẫn cho ước tính
- User nhập ngày sinh không hợp lệ (tương lai, quá xa quá khứ) → validate và báo lỗi rõ ràng, không crash

**Astro Skill áp dụng** *(xem quy tắc đầy đủ ở Chương 0.5):*
- Chart: **Natal Chart**, hệ **Western Tropical**
- House system: KHÔNG tính House ở bước này (user chỉ vừa nhập ngày sinh) — chỉ tính Sun sign từ ngày sinh
- Cách đọc: map ngày sinh → Sun sign theo lịch Tropical cố định (không phụ thuộc giờ/nơi sinh) → lấy `ContentTemplate` loại `sun` tương ứng

**Screen Flow:**

```
[Splash] 
   ↓
[Welcome — 2 slide giới thiệu ngắn, không giải thích chiêm tinh dài dòng]
   ↓
[Consent Screen — hiển thị TRƯỚC khi xin bất kỳ dữ liệu nào]
   "Lá Lành dùng ngày sinh để tính Astro Profile. Bạn xem được, xóa được bất cứ lúc nào."
   [Đồng ý & tiếp tục]
   ↓
[Nhập số điện thoại/email] → [Xác thực OTP]
   ↓
[Nhập ngày sinh — date picker]
   (Không có trường giờ/nơi sinh ở màn này — giữ đúng nguyên tắc progressive profiling)
   ↓
[Loading — "Đang đọc bầu trời lúc bạn sinh ra..." ~2 giây]
   ↓
[Astro Profile Basic Reveal]
   Hiển thị: Sun sign + nguyên tố + đoạn mô tả 80-120 từ
   [Nút: Lưu Lá Khai Sinh] [Nút: Bỏ qua, vào app]
   ↓
[Home — Daily Astro card hiển thị đầu tiên]
```

**User flow note:** Màn "Astro Profile Basic Reveal" là khoảnh khắc quan trọng nhất của toàn bộ onboarding — đây là nơi quyết định user có cảm thấy "app này biết gì đó về mình" hay không. Không được rush qua màn này bằng cách auto-skip; phải có animation/pacing đủ chậm để tạo cảm giác "đang được đọc", không phải "đang load dữ liệu".

---

#### F1.2 — Daily Astro (transit engine, ưu tiên kỹ thuật cao)

**User story:**
> Là một người dùng đã có Astro Profile, tôi muốn mỗi ngày mở app và thấy một insight khác với hôm qua, dựa trên những gì đang thực sự xảy ra trên bầu trời — không phải một câu generic lặp lại.

**Acceptance criteria:**
- [ ] Hệ thống tính được vị trí các hành tinh chính (Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn) tại thời điểm hiện tại, theo ngày thực
- [ ] Daily Astro content được sinh ra dựa trên: transit hiện tại × Sun sign của user (Level 1), nâng cấp lên × Moon sign nếu có (Level 2)
- [ ] Nội dung Daily Astro của 2 ngày liên tiếp KHÔNG được trùng nhau quá 70% (kiểm tra bằng similarity check trước khi launch)
- [ ] Daily Astro hiển thị kèm mood check-in — user chọn cảm xúc hiện tại, lưu lại để cá nhân hóa các lần sau
- [ ] Card Daily Astro phải có nút "Lưu" và "Chia sẻ" rõ ràng, không ẩn trong menu phụ

**Data model:**

```
DailyTransitSnapshot {
  date: date
  planetary_positions: JSON       // { "saturn": {"sign": "...", "house_trigger": [...]}, ... }
  computed_at: timestamp
  cached: boolean                 // snapshot này tính 1 lần/ngày dùng chung cho mọi user, KHÔNG tính riêng từng user
}

DailyAstroContent {
  id: UUID
  date: date
  sun_sign: enum(12 cung)
  moon_sign: enum(12 cung) | null
  content_text: string
  content_template_id: UUID (FK → ContentTemplate)
  generated_at: timestamp
}

UserDailyView {
  user_id: UUID
  daily_astro_content_id: UUID
  viewed_at: timestamp
  mood_selected: enum('vui','mệt','lo','ổn','mông lung',...)
  shared: boolean
  saved: boolean
}

ContentTemplate {
  id: UUID
  placement_type: enum('sun','moon','venus','mars','transit_house')
  placement_value: string          // ví dụ "saturn_house7" hoặc "moon_cancer"
  template_text: string
  tone_tags: array<string>         // ['identity_mirror','targeted_tag',...] map sang trigger ở Playbook Phần 4
  written_by: string
  reviewed: boolean
}
```

**Kỹ thuật quan trọng:**
- `DailyTransitSnapshot` tính 1 lần/ngày cho TOÀN BỘ hệ thống (không phải tính riêng theo từng user) — đây là tối ưu hiệu năng bắt buộc, vì vị trí hành tinh giống nhau cho mọi người tại cùng thời điểm, chỉ khác ở cách nó tương tác với natal chart riêng từng user
- Cần research/mua ephemeris data (dữ liệu thiên văn) đáng tin cậy — đây là phụ thuộc bên ngoài cần chốt sớm nhất trong toàn bộ dự án

**Rủi ro đã biết (xem Playbook Phần 1.4):** Tránh lặp lại lỗi của Co-Star — không được "flatten" transit phức tạp (Saturn thay đổi theo năm, Moon thay đổi theo ngày) thành một câu chung. `ContentTemplate` phải phân biệt rõ transit nhanh (Moon, hàng ngày) và transit chậm (Saturn/Jupiter/Pluto, hàng tháng/năm) — không trộn lẫn tốc độ thay đổi.

**Astro Skill áp dụng:**
- Chart: **Transit Chart** áp lên **Natal Chart**, hệ **Western Tropical**
- House system: Level 1-2 user (chưa có House) → chỉ đọc Transit-to-Sign (hành tinh transit đang ở cung nào, so với Sun/Moon sign của user — không cần House); Level 3+ user → đọc Transit-to-House đầy đủ
- Orb: Moon transit dùng ±6° (transit nhanh); nếu sau v0.3 có Saturn/Jupiter/Pluto thì dùng ±2°/±5° theo bảng 0.5.4
- Cách đọc: lấy `DailyTransitSnapshot` hôm nay → với mỗi user, tính hành tinh nào đang tạo aspect với Sun/Moon natal của họ trong orb cho phép → chọn `ContentTemplate` loại `transit` khớp nhất → nếu nhiều transit cùng lúc, ưu tiên transit có orb hẹp nhất (đang "exact" nhất)

**Screen Flow:**

```
[Home] 
   ↓ (mở app, hoặc tap vào card Daily Astro)
[Daily Astro Card — hiển thị ngay trên Home, không cần điều hướng thêm]
   Nội dung: 1 đoạn ngắn (transit hôm nay) + emoji/icon mood
   [Tap để xem chi tiết hơn]
   ↓
[Daily Astro Detail Screen]
   - Đoạn nội dung đầy đủ
   - Mood check-in: chọn 1 trong 5-6 emoji cảm xúc
   - [Nút Lưu] [Nút Chia sẻ]
   ↓ (nếu chọn Lưu)
[Toast nhẹ: "Đã lưu vào Lá của bạn"] → quay lại Home
   ↓ (nếu chọn Chia sẻ)
[Share Sheet — native, tạo card ảnh tự động trước khi mở]
```

**User flow note:** Daily Astro PHẢI là màn hình đầu tiên user thấy mỗi lần mở app (không phải feed, không phải danh sách menu) — đây là cơ chế tạo thói quen quay lại hàng ngày, tương tự cách BeReal dùng notification daily nhưng khác ở chỗ nội dung thực sự thay đổi mỗi ngày nhờ Transit Engine, không lặp lại format rỗng.

---

#### F1.3 — Lá Khai Sinh Card (shareable artifact)

**User story:**
> Là một người dùng vừa xem xong Astro Profile của mình, tôi muốn có một hình ảnh đẹp, đúng phong cách của mình, để tôi có thể lưu hoặc gửi cho bạn bè mà không cảm thấy ngại.

**Acceptance criteria:**
- [ ] Card tự động generate dưới dạng hình ảnh (PNG/JPG), tỷ lệ phù hợp Instagram Story (9:16) và post vuông (1:1)
- [ ] Card có 4 phần nội dung cố định: "Kiểu người", "Điểm mạnh", "Điểm dễ mệt", "Lời nhắn" — mỗi phần áp dụng Quy tắc 1 (đặt tên vòng lặp, không kết luận) từ Playbook
- [ ] Card KHÔNG hiển thị tên thật hoặc thông tin định danh nếu user không bật tùy chọn "hiện tên"
- [ ] User có thể chia sẻ trực tiếp ra Instagram Story/Threads/Messenger qua native share sheet
- [ ] Card có watermark nhỏ, không phá hỏng thẩm mỹ (học từ case Spotify Wrapped — branding nhẹ nhưng đủ nhận diện khi được share lại)
- [ ] Track được số lượt share theo từng kênh (để đo hiệu quả viral loop)

**Data model:**

```
LaKhaiSinhCard {
  id: UUID
  user_id: UUID (FK → User)
  card_image_url: string
  content_snapshot: JSON          // lưu lại nội dung tại thời điểm tạo, vì NatalChart có thể update sau
  show_name: boolean
  created_at: timestamp
  share_count: int
  share_channels: JSON             // {"instagram_story": 3, "threads": 1, ...}
}
```

**Astro Skill áp dụng:**
- Chart: **Natal Chart** (Sun/Venus/Mars sign), hệ **Western Tropical**
- Không cần House — Card chỉ dùng placement cấp 1 (Sun/Venus/Mars), không đụng đến House system
- Cách đọc: ghép 3 `ContentTemplate` (Sun → "Kiểu người", Venus → bổ sung sắc thái "Điểm mạnh", Mars → "Điểm dễ mệt") thành 1 bộ nội dung card duy nhất, không lấy riêng lẻ từng template gốc mà phải có bước "blend" để câu văn liền mạch

**Screen Flow:**

```
[Astro Profile Basic Reveal] (tiếp nối từ F1.1)
   ↓
[Card Preview Screen]
   Hiển thị card full màn hình, 4 phần: Kiểu người / Điểm mạnh / Điểm dễ mệt / Lời nhắn
   [Toggle: Hiện tên] [Toggle: Ẩn tên]
   [Nút Lưu về máy] [Nút Chia sẻ ngay]
   ↓ (nếu Chia sẻ)
[Chọn nền tảng — Instagram Story / Threads / Messenger / Zalo]
   ↓
[Mở native share sheet của hệ điều hành với ảnh đã generate sẵn]
```

---

#### F1.4 — Progressive Profiling Engine (unlock ladder)

**User story:**
> Là một người dùng, tôi muốn được mời thêm thông tin (giờ sinh, nơi sinh) đúng lúc tôi đang tò mò muốn biết nhiều hơn — không phải bị ép ngay từ đầu khi tôi chưa tin tưởng app.

**Acceptance criteria:**
- [ ] Hệ thống tính `profile_level` (1-5) tự động dựa trên dữ liệu đã có (xem Data model F1.1)
- [ ] Mỗi lần user đạt một mốc tương tác cụ thể (xem bảng trigger bên dưới), hệ thống hiển thị lời mời nhập thêm dữ liệu — gắn với một "cảnh" cụ thể, không phải form trống
- [ ] User luôn có thể bỏ qua (skip) — không bao giờ chặn flow chính vì thiếu dữ liệu optional
- [ ] Copy mời nhập dữ liệu phải nêu rõ lợi ích cụ thể ngay trong câu (ví dụ: "Thêm giờ sinh để mở Moon sign — cách bạn xử lý cảm xúc khi không ai nhìn")

**Bảng trigger mời nhập dữ liệu:**

| Mốc đạt được | Dữ liệu mời thêm | Copy mẫu |
|---|---|---|
| Đọc Daily Astro 3 ngày liên tiếp | Giờ sinh | "Muốn lời nhắn đúng hơn? Thêm giờ sinh để mở Moon sign." |
| Tạo Lá Ghép lần đầu (v0.3) | Nơi sinh | "Mở Bản Đồ Kết Nối đầy đủ — thêm nơi sinh." |
| Muốn vào Vòng Lá (v0.4) | Intent kết nối + ảnh | "Để ghép đúng vibe, chọn mục đích kết nối của bạn." |

**Data model:**

```
ProfileLevelEvent {
  user_id: UUID
  trigger_event: enum('3day_streak','first_la_ghep','wants_vong_la',...)
  prompted_at: timestamp
  data_requested: enum('birth_time','birth_place','intent','photo')
  user_response: enum('provided','skipped','dismissed')
  responded_at: timestamp | null
}
```

**Astro Skill áp dụng:**
- Không tự nó là một chart riêng — đây là cơ chế điều phối, quyết định khi nào user đủ dữ liệu để chuyển từ đọc Sun-only sang đọc Moon (cần giờ sinh) sang đọc House (cần nơi sinh)
- Quy tắc bắt buộc: KHÔNG được hiển thị bất kỳ insight nào dựa trên House nếu user chưa đạt Level 3 — thà không hiển thị còn hơn hiển thị sai do thiếu dữ liệu

**Screen Flow (ví dụ 1 trigger — sau 3 ngày đọc Daily Astro):**

```
[Daily Astro Card ngày thứ 3] 
   ↓
[Bottom sheet nhẹ trượt lên, KHÔNG full-screen modal — tránh cảm giác bị chặn]
   "Muốn lời nhắn đúng hơn? Thêm giờ sinh để mở Moon sign — 
    cách bạn xử lý cảm xúc khi không ai nhìn."
   [Nút: Thêm giờ sinh] [Nút: Để sau]
   ↓ (nếu Thêm giờ sinh)
[Time picker — có lựa chọn "Tôi không nhớ chính xác" → hiện 4 lựa chọn khoảng giờ]
   ↓
[Loading ngắn → Moon sign reveal, tương tự pacing của F1.1]
   ↓ (nếu Để sau)
[Đóng bottom sheet, không hỏi lại trong 3 ngày tiếp theo]
```

### 1.3. Out of scope cho v0.1 (cố tình loại bỏ)

- Matching/dating feature — chưa có đủ pool, để dành v0.4
- Lá Ghép — cần ở v0.3, sau khi content engine đã ổn định
- Bất kỳ tính năng thu phí nào — v0.1 hoàn toàn free để tối đa hóa activation

### 1.4. KPI release v0.1

| Metric | Target |
|---|---|
| Profile Level 1 hoàn thành | 3.000 user |
| D3 retention | ≥ 40% |
| % user share Lá Khai Sinh Card ít nhất 1 lần | ≥ 30% |
| Thời gian onboarding trung bình | ≤ 90 giây |

---

## 2. v0.2 — Lá Chứng & Pitch Card (Tháng 2)

### 2.1. Mục tiêu release

Đưa bạn bè vào vòng lặp như nguồn social proof — kích hoạt Trigger "Information Gap" và "Identity Mirror" (xem Playbook Phần 4) thông qua cơ chế mà người nhận *bắt buộc* phải tò mò.

### 2.2. Danh sách feature

#### F2.1 — Lá Chứng (bạn thân xác nhận tính cách)

**User story:**
> Là một người dùng, tôi muốn mời bạn thân chọn những câu mô tả đúng về tôi từ một danh sách có sẵn, để profile của tôi có thêm một lớp "được người khác xác nhận", không chỉ do app tự nói.

**Acceptance criteria:**
- [ ] User A chọn một người bạn (từ danh bạ/link chia sẻ) để gửi yêu cầu Lá Chứng
- [ ] Người bạn B nhận link, KHÔNG cần tài khoản Lá Lành để chọn câu (giảm friction bước đầu) — nhưng sẽ được mời tạo tài khoản sau khi hoàn thành
- [ ] B chọn 3-5 câu từ danh sách có sẵn theo từng nhóm chủ đề (tình cảm, giao tiếp, cảm xúc, bạn bè) — KHÔNG cho phép tự do nhập text (chống toxic/bắt nạt)
- [ ] Sau khi B hoàn thành, A nhận thông báo và xem được các câu đã chọn
- [ ] A có thể tích lũy Lá Chứng từ nhiều bạn — hệ thống hiển thị "X/Y bạn đã xác nhận [câu mô tả]" nếu trùng nhau ≥ 2 người

**Data model:**

```
LaChungRequest {
  id: UUID
  requester_user_id: UUID (FK → User)
  target_contact: string           // số điện thoại/email người được mời, có thể chưa có tài khoản
  share_link_token: string (unique)
  status: enum('pending','completed','expired')
  created_at: timestamp
  expires_at: timestamp             // 7 ngày
}

LaChungResponse {
  id: UUID
  request_id: UUID (FK → LaChungRequest)
  respondent_user_id: UUID | null   // null nếu respondent chưa tạo tài khoản
  respondent_contact: string
  selected_statements: array<UUID>  // FK → StatementBank
  responded_at: timestamp
}

StatementBank {
  id: UUID
  category: enum('tinh_cam','giao_tiep','cam_xuc','ban_be')
  statement_text: string
  tone_check: boolean               // đã review để đảm bảo không toxic
}
```

**Astro Skill áp dụng:**
- Không trực tiếp dùng chart — `StatementBank` là nội dung do bạn bè chọn thủ công
- Liên kết phụ (không bắt buộc v0.2): đối chiếu câu B chọn với Natal Chart của A để hiển thị thêm dòng xác nhận chéo "Lá Lành cũng đọc thấy điều tương tự ở Mars Thiên Bình của Hạnh"

**Screen Flow:**

```
[Profile của A] → [Nút "Mời bạn xác nhận"]
   ↓
[Chọn liên hệ — từ danh bạ hoặc copy link]
   ↓
[Gửi link cho B qua share sheet]

--- (phía B, có thể chưa cài app) ---

[B mở link] → [Landing screen web view — "Hạnh mời bạn xác nhận vài điều về cô ấy"]
   ↓
[4 nhóm câu hỏi, mỗi nhóm 4-6 lựa chọn dạng chip — B chọn 3-5 câu tổng]
   ↓
[Màn xác nhận: "Hạnh sẽ thấy những câu này."]
   [Nút: Tải Lá Lành để xem A nói gì về bạn] ← điểm chuyển đổi cài app
   ↓
[A nhận push notification ngay lập tức]
```

---

#### F2.2 — Pitch Card (bạn thân pitch vào Vòng Lá)

**User story:**
> Là một người dùng, tôi muốn "pitch" một người bạn độc thân của mình vào một theme cụ thể, để họ có động lực tham gia mà không phải tự viết về bản thân từ đầu.

**Acceptance criteria:**
- [ ] A chọn theme có sẵn (ví dụ: "Người chậm mà sâu", "Overthinker cần người ấm") — danh sách theme do team content quản lý, mở rộng dần
- [ ] A chọn 5 câu mô tả B từ `StatementBank` (dùng chung với F2.1)
- [ ] Hệ thống tạo Pitch Card — preview bị che/blur một phần cho đến khi B mở
- [ ] B nhận notification dạng "tin nhắn bạn thân", không dạng thông báo hệ thống (xem copy mẫu ở Playbook Phần 4, Trigger 2)
- [ ] Khi B mở Pitch Card → bắt buộc nhập ngày sinh (nếu chưa có tài khoản) để xem đầy đủ — đây là điểm chuyển đổi (conversion point) chính của feature này
- [ ] B có quyền "Accept" (vào theme đó) hoặc "Chỉ xem, không tham gia" — không ép buộc

**Data model:**

```
PitchCard {
  id: UUID
  pitcher_user_id: UUID (FK → User)
  target_contact: string
  target_user_id: UUID | null
  theme_id: UUID (FK → ThemeBank)
  selected_statements: array<UUID>  // FK → StatementBank
  status: enum('sent','viewed','accepted','declined')
  created_at: timestamp
  viewed_at: timestamp | null
  responded_at: timestamp | null
}

ThemeBank {
  id: UUID
  theme_name: string                // "Người chậm mà sâu"
  theme_description: string
  active: boolean
  created_at: timestamp
}
```

**Edge case:** Nếu B đã từ chối 1 Pitch Card, hệ thống không gửi thêm Pitch Card từ cùng người pitcher trong 14 ngày (chống spam, bảo vệ trải nghiệm).

**Astro Skill áp dụng:**
- Không trực tiếp dùng chart ở bước pitch — tương tự F2.1, nội dung do A chọn thủ công
- Sau khi B accept và nhập ngày sinh, hệ thống tự động tính **Natal Chart** (Western Tropical) cho B ngay lập tức để B có Astro Profile của riêng mình song song với Pitch Card — không bắt B đi qua lại flow F1.1 từ đầu

**Screen Flow:**

```
[A — Home] → [Nút "Pitch một người bạn"]
   ↓
[Chọn theme từ danh sách ThemeBank — dạng card cuộn ngang]
   ↓
[Chọn liên hệ B]
   ↓
[Chọn 5 câu mô tả B — cùng UI chip như F2.1]
   ↓
[Xác nhận gửi — "Hạnh chưa thấy lại nội dung này sau khi gửi"]
   (Cố tình ẩn nội dung khỏi A sau khi gửi — giữ tính bất ngờ cho B)

--- (phía B) ---

[B nhận notification: "Hạnh vừa viết về bạn. Mở xem được không?"]
   ↓
[Mở app/web view — Pitch Card hiện dạng BLUR toàn bộ 5 câu]
   "Hạnh đã chọn 5 câu để mô tả bạn"
   [Nút: Nhập ngày sinh để đọc]
   ↓
[Date picker — nếu B chưa có tài khoản, tạo nhanh bằng SĐT/email]
   ↓
[Loading — "Đang mở Lá của bạn..."]
   ↓
[Reveal đồng thời 2 thứ cạnh nhau: 5 câu Pitch Card của A (đã hết blur) + Astro Profile Basic mới tính cho B]
   → Đây là khoảnh khắc so sánh "bạn thân nói gì vs app nói gì" — phải đặt 2 khối nội dung này gần nhau trên cùng 1 màn
   ↓
[Nút: Tham gia theme này] [Nút: Chỉ xem, chưa tham gia]
```

### 2.3. KPI release v0.2

| Metric | Target |
|---|---|
| Tổng user | 10.000 |
| % user có ít nhất 1 Lá Chứng | ≥ 25% |
| Trung bình Pitch Card/user (người gửi) | ≥ 1.5 |
| Tỷ lệ B hoàn thành signup sau khi mở Pitch Card | ≥ 35% |

---

## 3. v0.3 — Lá Ghép & Transit Engine (Tháng 3)

### 3.1. Mục tiêu release

Đây là release nặng kỹ thuật nhất 6 tháng. Hai việc song song: (1) build transit engine thật theo house — nền tảng cho 3/7 trigger tâm lý mạnh nhất, và (2) ra mắt Lá Ghép — viral loop quan hệ chính của sản phẩm.

### 3.2. Danh sách feature

#### F3.1 — Transit Engine (House mapping)

**User story:**
> Là một người dùng đã có đủ ngày/giờ/nơi sinh, tôi muốn được biết chính xác hành tinh nào đang ảnh hưởng đến lĩnh vực nào trong đời sống của tôi ngay bây giờ — không phải một câu chung chung.

**Acceptance criteria:**
- [ ] Hệ thống tính được House system (12 nhà) cho user có đủ birth_time + birth_place
- [ ] Hệ thống xác định được transit hiện tại (Saturn, Jupiter, Pluto, Mercury) đang đi qua house nào của TỪNG user
- [ ] Có engine sinh content riêng cho transit chậm (Saturn/Jupiter/Pluto — theo tháng/năm) khác với transit nhanh (Moon — theo ngày), KHÔNG dùng chung 1 template
- [ ] Mỗi transit insight phải có ngày bắt đầu và ngày kết thúc dự kiến hiển thị rõ (đáp ứng Quy tắc 3 — deadline cụ thể)
- [ ] Insight về transit chỉ hiển thị cho user có đủ Level 3 (có house data) — user Level 1-2 thấy thông báo mời nâng cấp thay vì insight sai/thiếu chính xác

**Data model:**

```
HouseSystem {
  user_id: UUID (FK → User)
  house_1_sign: enum(12 cung)
  house_2_sign: enum(12 cung)
  ... // house_3 đến house_12
  computed_at: timestamp
}

TransitEvent {
  id: UUID
  planet: enum('saturn','jupiter','pluto','mercury','venus','mars')
  transit_type: enum('house_ingress','retrograde_start','retrograde_end','aspect')
  start_date: date
  end_date: date | null            // null nếu đang diễn ra, chưa biết ngày kết thúc chính xác
  affected_house_per_user: relation  // tính riêng cho từng user dựa trên HouseSystem
}

UserTransitInsight {
  id: UUID
  user_id: UUID (FK → User)
  transit_event_id: UUID (FK → TransitEvent)
  affected_house: int               // 1-12
  content_text: string
  content_template_id: UUID (FK → ContentTemplate)
  generated_at: timestamp
  viewed: boolean
  shared: boolean
  forwarded_to_contact: string | null  // nếu user gửi insight này cho người khác (Trigger Social Currency)
}
```

**Phụ thuộc kỹ thuật quan trọng:** Đây là feature cần research/đối tác ephemeris data chính xác nhất trong toàn bộ dự án. Nên chốt nguồn dữ liệu thiên văn (mua license hoặc tự build từ thư viện ephemeris mở) từ trước khi bắt đầu code v0.3 — không để đến giữa sprint mới phát hiện thiếu dữ liệu.

**Astro Skill áp dụng:**
- Chart: **Transit Chart** áp lên **Natal Chart**, hệ **Western Tropical**
- House system: **Whole Sign bắt buộc** (theo quy tắc 0.5.2) — không dùng Placidus cho tính năng tự động này dù user có giờ sinh chính xác, để giữ nhất quán house giữa các tính năng tự động khác trong app
- Orb: transit chậm (Saturn/Jupiter/Pluto) dùng ±2° cho exact aspect, ±5° cho giai đoạn "đang tới/đang rời" (bảng 0.5.4)
- Cách đọc: với mỗi user đủ Level 3 → lấy `HouseSystem` (Whole Sign) → với mỗi `TransitEvent` đang active → xác định hành tinh transit rơi vào House số mấy của user → ghép `ContentTemplate` loại `transit_house` (vd "saturn_house7") → tính ngày bắt đầu/kết thúc dự kiến để hiển thị deadline cụ thể (Quy tắc 3, Playbook Phần 5)
- **Cấm tuyệt đối:** không tạo `UserTransitInsight` cho user chưa đủ Level 3 — feature này ẩn hoàn toàn với user Level 1-2, thay bằng lời mời nâng cấp profile

**Screen Flow:**

```
[Home — Tab "Vận Hạn" hoặc banner nổi bật trên Daily Astro]
   ↓
[Nếu user < Level 3]
   [Card mờ — "Có một transit đang ảnh hưởng bạn. Thêm nơi sinh để xem đó là gì."]
   [Nút: Thêm nơi sinh] → dẫn vào lại flow F1.4
   ↓
[Nếu user ≥ Level 3]
[Transit Insight Card — hiển thị transit active nhất, orb hẹp nhất trước]
   "Saturn đang đi qua House 7 của bạn"
   [Đoạn nội dung đầy đủ]
   [Thanh tiến trình thời gian: ngày bắt đầu → hiện tại → ngày kết thúc dự kiến]
   [Nút: Gửi cho người khác] [Nút: Lưu]
   ↓ (Gửi cho người khác — kích hoạt Trigger Social Currency)
[Chọn liên hệ B] → [Nhập ngày sinh B nếu lần đầu]
   ↓
[Preview transit insight cho B — tính riêng theo Natal Chart B nếu đã có]
   ↓
[Gửi qua share sheet — copy: "Có transit liên quan đến bạn. [Tên A] vừa xem."]
```

---

#### F3.2 — Lá Ghép (relationship invite)

**User story:**
> Là một người dùng, tôi muốn nhập ngày sinh của một người tôi quan tâm (crush, bạn thân, người yêu) và xem được mức độ hợp nhau giữa hai người — nhưng phải mời được họ tham gia để xem đầy đủ.

**Acceptance criteria:**
- [ ] A chọn loại Lá Ghép (crush/BFF/couple/ex/team/bí mật) — mỗi loại có hook và tông giọng riêng (xem Playbook Phần 3, bảng Lá Ghép)
- [ ] A nhập ngày sinh của B (bắt buộc) — giờ/nơi sinh optional ở bước này
- [ ] Hệ thống sinh ra preview kết quả — chỉ hiển thị 30-40% nội dung, phần còn lại bị blur có overlay "Cần [dữ liệu cụ thể] của [tên B] để mở phần này"
- [ ] A có thể gửi link cho B qua share sheet (SMS, Messenger, Zalo...)
- [ ] B mở link → thấy phần "của B đang chờ" → nhập ngày sinh (nếu chưa có TK) hoặc xác nhận thông tin (nếu đã có TK) → cả hai nhận kết quả đầy đủ
- [ ] Khi B hoàn thành, A nhận notification ngay lập tức: "[Tên B] vừa mở Lá Ghép. Kết quả đầy đủ đã sẵn sàng."
- [ ] Lá Ghép loại "Bí mật" — B KHÔNG thấy tên người gửi cho đến khi B đồng ý mở (tăng information gap tối đa)
- [ ] Có Share Card riêng cho Lá Ghép — hiển thị 1-2 câu gợi mở (không lộ hết), dùng để post công khai (khác với link gửi riêng 1-1)

**Data model:**

```
LaGhep {
  id: UUID
  type: enum('crush','bff','couple','ex','team','bi_mat')
  initiator_user_id: UUID (FK → User)
  target_contact: string
  target_user_id: UUID | null
  target_birth_date: date           // nhập bởi initiator, có thể chưa chính xác
  target_birth_time: time | null    // nhập bởi target sau khi mở link
  target_birth_place: string | null
  share_link_token: string (unique)
  status: enum('pending','partial','completed')
  hide_initiator_name: boolean      // true cho loại "bi_mat"
  created_at: timestamp
  completed_at: timestamp | null
}

LaGhepResult {
  la_ghep_id: UUID (FK → LaGhep)
  compatibility_summary: string
  vibe_chinh: string
  diem_hut: string
  diem_can_chu_y: string
  la_chung_tarot: string             // 1 lá tarot đại diện chung
  preview_unlock_percent: int        // 30-40 cho trạng thái pending/partial
  full_result_generated: boolean
}

LaGhepShareCard {
  la_ghep_id: UUID (FK → LaGhep)
  card_image_url: string
  preview_text: string               // 1-2 câu gợi mở, không lộ hết
  share_count: int
}
```

**Astro Skill áp dụng:**
- Chart: **Synastry Chart** giữa Natal Chart A và Natal Chart B, hệ **Western Tropical**
- House system: Whole Sign nếu cả hai có đủ giờ+nơi sinh (Level 3); nếu một trong hai chỉ có ngày sinh, hệ thống tự giảm xuống chỉ so Sun/Venus/Mars sign (bỏ qua House) — KHÔNG được nội suy/đoán House khi thiếu dữ liệu
- Orb: ±3° cho Sun/Moon/Venus/Mars aspect giữa hai chart (theo bảng 0.5.4)
- Cách đọc: tính aspect giữa hành tinh của A và hành tinh của B (vd Venus của A square Mars của B) → map sang `ContentTemplate` loại `synastry` → sinh 3 đoạn cố định: "Vibe chính" (tổng hợp aspect quan trọng nhất), "Điểm hút" (aspect hài hòa — trine/sextile), "Điểm cần chú ý" (aspect căng — square/opposition) → chọn 1 lá tarot đại diện dựa trên tổng điểm hòa hợp
- Quy tắc hiển thị preview: 30-40% nội dung hiện = luôn hiện "Vibe chính", luôn blur "Điểm hút" và "Điểm cần chú ý" cho đến khi B nhập đủ dữ liệu

**Screen Flow:**

```
[Home] → [Nút "Tạo Lá Ghép"]
   ↓
[Chọn loại — Crush / BFF / Couple / Ex / Team / Bí mật — dạng card lựa chọn]
   ↓
[Nhập tên gọi B (nickname, không cần tên thật)] → [Nhập ngày sinh B]
   ↓
[Loading — "Đang xem hai Lá có hợp không..."]
   ↓
[Preview Result Screen]
   - Hiện đầy đủ: "Vibe chính" 
   - Blur: "Điểm hút" và "Điểm cần chú ý" — overlay "Cần giờ sinh của [B] để mở phần này"
   - Lá tarot đại diện hiện mờ, úp ngược
   [Nút: Gửi cho B để mở đầy đủ]
   ↓
[Share sheet — link kèm preview card image]

--- (phía B) ---

[B mở link] → [Landing — "[A] vừa tạo Lá Ghép với bạn"]
   (Nếu loại "Bí mật" — KHÔNG hiện tên A ở bước này)
   ↓
[Thấy preview giống A đã thấy — phần của B cũng đang blur]
   [Nút: Nhập giờ sinh để mở phần của bạn]
   ↓
[Time picker → nếu chưa có tài khoản, tạo nhanh song song]
   ↓
[Loading — "Đang mở Lá Ghép đầy đủ..."]
   ↓
[Full Result Reveal — cả A và B đều nhận push notification cùng lúc]
   Hiện đầy đủ 3 phần + lá tarot lật ngửa
   [Nút: Lưu] [Nút: Tạo Share Card riêng (ẩn danh, đăng công khai)]
```

---

#### F3.3 — Pending State Notification (Zeigarnik mechanism)

**User story:**
> Là người dùng A đã gửi Lá Ghép nhưng B chưa mở, tôi muốn được nhắc nhẹ nhàng để biết Lá Ghép vẫn đang "treo" — và muốn B cũng cảm thấy điều tương tự.

**Acceptance criteria:**
- [ ] Nếu Lá Ghép ở trạng thái `pending` quá 24h, gửi notification nhắc nhẹ cho A: "Lá Ghép với [tên/nickname B] vẫn đang chờ."
- [ ] Nếu B đã click vào link nhưng chưa hoàn thành nhập liệu (trạng thái `partial`), gửi 1 reminder cho B sau 12h (không spam nhiều lần)
- [ ] Tối đa 2 lần nhắc cho mỗi bên trong vòng đời 1 Lá Ghép — tránh gây khó chịu, đi ngược nguyên tắc "không ép buộc"
- [ ] Sau 14 ngày không hoàn thành, Lá Ghép chuyển trạng thái `expired`, A có thể tạo lại nếu muốn

### 3.3. KPI release v0.3

| Metric | Target |
|---|---|
| Tổng user | 25.000 |
| Lá Ghép tạo mới/ngày | ≥ 500 |
| Tỷ lệ B hoàn thành sau khi mở link | ≥ 35% |
| Paid conversion (Full Lá Ghép) | ≥ 8% trong số đã hoàn thành |
| % user forward transit insight cho người khác | ≥ 10% (đo Social Currency trigger) |

---

## 4. v0.4 — Vòng Lá (Tháng 4)

### 4.1. Mục tiêu release

Matching theo cohort với giới hạn thời gian thật (không phải dating app 24/7). Đây là feature rủi ro cao nhất về safety — cần review kỹ trước khi launch.

### 4.2. Danh sách feature

#### F4.1 — Cohort Matching Engine

**User story:**
> Là một người dùng đã đủ điều kiện matching-ready, tôi muốn mỗi tối thứ 7 nhận 5 kiểu kết nối đáng thử trong khu vực — không phải một bảng xếp hạng người hay lướt vô tận.

**Acceptance criteria:**
- [ ] User chỉ được đưa vào matching pool nếu đạt Profile Level 4 trở lên (có intent + ảnh xác minh)
- [ ] Matching chạy 1 lần/tuần, kích hoạt tự động lúc 19:30 thứ 7 (30 phút trước khi mở cho user); hard safety/preference filters luôn chạy trước mọi tính toán chiêm tinh
- [ ] User có thể chọn `weekly_intent` tùy chọn (`de_noi_chuyen`, `di_cham`, `goc_moi`, `de_la_can`); lựa chọn tự hết hạn sau recap và không được suy ra từ hành vi
- [ ] Astro Engine trả `RelationshipBundle` đa chiều (`communication`, `emotional`, `relating`, `drive`, `growth`, `friction`) cùng evidence; không tạo hoặc hiển thị một compatibility/soulmate score tổng
- [ ] Mỗi user nhận đúng 5 gợi ý ("5 lá úp") khi pool đủ; bộ năm tối ưu độ đa dạng kiểu kết nối và exposure fairness, không phải top-5 theo một điểm giảm dần
- [ ] Mỗi card có một `energy_slot` và “Vì sao có lá này?” truy được về intent overlap + tối đa 3 evidence thật; không lặp một luận điểm cho cả năm lá
- [ ] Vòng Lá chỉ mở từ 20:00 đến 23:00 thứ 7 — ngoài khung giờ này, user không thấy được 5 lá (nhưng vẫn dùng được Daily Astro, Lá Ghép bình thường)
- [ ] Nếu pool trong 1 khu vực < 20 user active, hệ thống mở rộng bán kính tự động và thông báo cho user biết

**Data model:**

```
MatchingPool {
  id: UUID
  week_starting: date
  region: string                    // thành phố hoặc quận, KHÔNG lưu tọa độ chính xác
  status: enum('preparing','open','closed')
  opens_at: timestamp                // 20:00 thứ 7
  closes_at: timestamp               // 23:00 thứ 7
}

MatchingPoolMember {
  pool_id: UUID (FK → MatchingPool)
  user_id: UUID (FK → User)
  intent: enum('hen_ho','ban_moi','ca_phe','hoc_chung')
  age_range_preference: JSON | null
  joined_at: timestamp
}

PairRelationshipEvidence {
  id: UUID
  pool_id: UUID (FK → MatchingPool)
  user_a_id: UUID
  user_b_id: UUID
  intent_match: boolean
  dimension_strengths: JSON           // 6 chiều, dùng cho slate diversity; không phải xác suất
  evidence_ids: JSON                  // factor ids có provenance
  eligible_energy_slots: JSON         // các slot có đủ evidence
  relationship_method_version: string
  computed_at: timestamp
}

VongLaCard {
  id: UUID
  user_id: UUID (FK → User)          // người nhận 5 lá
  pool_id: UUID (FK → MatchingPool)
  card_position: int                  // 1-5
  candidate_user_id: UUID
  energy_slot: enum('de_noi_that','khac_ma_hut','di_cham','bat_y_tuong','goc_moi')
  card_label: string                  // động theo evidence thật trong slot
  evidence_ids: JSON                  // tối đa 3 evidence được phép giải thích
  opened: boolean
  opened_at: timestamp | null
  request_sent: boolean
}
```

**Astro Skill áp dụng:**
- Candidate discovery: **Synastry Chart** giữa từng cặp user trong `MatchingPool`, hệ **Western Tropical**; Composite/Davison không dùng để xếp hoặc loại candidate
- House system: Whole Sign, chỉ tính cho cặp mà CẢ HAI đều đạt Level 3+ (yêu cầu bắt buộc để vào pool — xem F4.1 Acceptance Criteria, Level 4 đã bao gồm Level 3)
- Orb: policy versioned `synastry-orbs-v2`; luminary 5°/4°/3°, các contact khác chặt hơn. UI luôn giữ exact orb/provenance nội bộ và không biến strength thành phần trăm hợp nhau
- Cách đọc: với mỗi cặp qua prefilter → tính Synastry đầy đủ, house overlay hai chiều khi đủ dữ liệu → map evidence vào 6 dimensions → xác định các `eligible_energy_slots` → bộ chọn tối ưu cả slate 5 card để tăng sự đa dạng và fairness. Hard preference/safety không bao giờ được nới để lấp slot
- Sau mutual: có thể mở **Lá Nối** bằng Synastry + midpoint Composite; Davison chỉ xuất hiện như bonus khi cả hai có giờ/nơi chính xác và đồng ý dùng dữ liệu cho mục đích này. D9/Jyotish là factual expert-gated, không dùng cho ranking/copy tự động ở v0.4
- **Quan trọng:** `energy_slot` là cấu trúc của bộ năm; `card_label` vẫn phải động theo evidence của đúng cặp. Hai card cùng slot ở hai tuần không được mặc định dùng cùng một lời giải thích

**Screen Flow:**

```
[Trước 20:00 thứ 7]
[Home — banner đếm ngược: "Vòng Lá mở lúc 20:00 tối nay"]
   ↓
[20:00 — Push notification: "Vòng Lá đã mở. 5 người hợp vibe nhất đang chờ bạn."]
   ↓
[Tap notification → Vòng Lá Screen]
[5 lá úp xếp dạng hàng ngang hoặc lưới — chỉ hiện card_label, KHÔNG hiện ảnh/tên]
   Lá 1 — "Người khiến bạn thấy dễ nói thật"
   Lá 2 — "Người khác vibe nhưng hút bạn theo cách khác"
   ... (5 lá)
   ↓ (tap vào 1 lá)
[Animation lật lá — pacing chậm, tạo cảm giác "đang mở"]
   ↓
[Card Detail — hiện ảnh, nickname, vài dòng compatibility (không hiện % cụ thể)]
   [Nút: Mở Lá này (gửi request)] [Nút: Đóng lại, xem lá khác]
   ↓ (nếu Mở Lá — giới hạn tối đa 3/5 lá mỗi tuần)
[Xác nhận: "Bạn đã mở 1/3 lá tuần này"]
   → Trạng thái request_sent = true, KHÔNG báo cho người kia biết ai đã gửi
   ↓
[Quay lại màn 5 lá — lá đã mở hiển thị trạng thái khác (đã lật, chờ phản hồi)]
```

---

#### F4.2 — Mutual Accept & Chat

**User story:**
> Là một người dùng đã mở một trong 5 lá và gửi yêu cầu, tôi muốn chỉ bắt đầu trò chuyện khi cả hai cùng đồng ý — không bị ép phải phản hồi người tôi không hứng thú.

**Acceptance criteria:**
- [ ] User mở tối đa 3/5 lá mỗi tuần (gửi request) — giới hạn cứng, không thể mua thêm ở v0.4 (giữ chất lượng over quantity)
- [ ] Request KHÔNG hiển thị cho người nhận biết là ai đã gửi cho đến khi họ tự mở lá tương ứng — tránh áp lực xã hội kiểu "ai đó đang chờ tôi"
- [ ] Chat chỉ mở khi CẢ HAI cùng accept (mutual) — một bên accept, một bên chưa thì không có gì xảy ra, không thông báo cho bên kia biết bị từ chối
- [ ] Sau khi mutual, hệ thống tự động sinh 3 câu gợi ý mở lời dựa trên Lá Ghép giữa hai người (tái dùng engine từ F3.2)
- [ ] Chat trong app, không lộ số điện thoại/thông tin liên hệ cho đến khi cả hai user tự nguyện share
- [ ] Có nút Block/Report ngay trong giao diện chat, hoạt động ngay từ tin nhắn đầu tiên

**Data model:**

```
VongLaRequest {
  id: UUID
  pool_id: UUID (FK → MatchingPool)
  from_user_id: UUID
  to_user_id: UUID
  status: enum('sent','mutual','expired')
  sent_at: timestamp
  responded_at: timestamp | null
}

MutualMatch {
  id: UUID
  user_a_id: UUID
  user_b_id: UUID
  matched_at: timestamp
  chat_thread_id: UUID (FK → ChatThread)
  icebreaker_suggestions: array<string>
}

ChatThread {
  id: UUID
  mutual_match_id: UUID (FK → MutualMatch)
  created_at: timestamp
  blocked_by: UUID | null
  reported: boolean
}
```

**Astro Skill áp dụng:**
- Chart: tái sử dụng **Synastry Chart** đã tính ở F4.1 cho cặp vừa mutual — không tính lại từ đầu
- Cách đọc: lấy aspect nổi bật nhất giữa Venus của A và Mars/Venus của B (hoặc ngược lại) → map sang 1 trong các mẫu câu mở lời theo `ContentTemplate` loại `icebreaker` → sinh đúng 3 câu, không nhiều hơn (tránh overload lựa chọn — Vòng Lá ưu tiên "ít nhưng sâu" theo định vị sản phẩm)

**Screen Flow:**

```
[B nhận request từ A — KHÔNG biết là A cho đến khi B tự mở lá tương ứng trong 5 lá của B]
   ↓
[Nếu B tap mở đúng lá đó] → [Card Detail của A] → [Nút: Mở Lá này]
   ↓ (Cả A và B đều đã accept → Mutual)
[Cả hai nhận push: "Hai bạn vừa mở cùng một Lá."]
   ↓
[Tap vào → Chat Thread mở ra lần đầu]
[Màn hình trống chat — hiện sẵn 3 gợi ý câu mở lời dạng chip phía trên ô nhập tin nhắn]
   "Bạn cần sự rõ ràng hay thích để mọi thứ tự nhiên?"
   "Gần đây điều gì làm bạn thấy nhẹ hơn?"
   "..."
   ↓ (tap 1 gợi ý hoặc tự gõ)
[Tin nhắn được gửi — input field chuyển sang chat thông thường]
   [Icon Report/Block luôn hiện ở góc trên, không ẩn trong menu phụ]
```

---

#### F4.3 — Recap Story (Open Ending)

**User story:**
> Là một người dùng vừa trải qua một tối Vòng Lá, tôi muốn nhận một bản tóm tắt cá nhân hóa vào chủ nhật, đủ thú vị để tôi muốn chia sẻ — nhưng không tiết lộ hết mọi thứ.

**Acceptance criteria:**
- [ ] Recap được sinh tự động vào 10:00 sáng chủ nhật cho mọi user đã tham gia Vòng Lá tối hôm trước
- [ ] Nội dung gồm: số lá đã mở, số request nhận được, 1 insight về "kiểu người hợp bạn tuần này" — KHÔNG tiết lộ kết quả cuối nếu chưa có (open ending theo Quy tắc viết content)
- [ ] Có thể export thành Share Card riêng để post lên Threads/Instagram
- [ ] Recap không bao giờ làm user cảm thấy bị "thua" nếu không có mutual match — tông giọng giữ tích cực, hướng tới tuần sau

**Data model:**

```
VongLaRecap {
  id: UUID
  user_id: UUID
  pool_id: UUID (FK → MatchingPool)
  lakhoten_count: int                // số lá đã mở
  requests_received_count: int
  mutual_count: int
  recap_text: string
  generated_at: timestamp
  shared: boolean
}
```

**Astro Skill áp dụng:**
- Không tính chart mới — tổng hợp dữ liệu từ `VongLaCard`, `VongLaRequest`, `MutualMatch` của tuần đó thành 1 đoạn narrative
- "Kiểu người hợp bạn tuần này" lấy từ aspect chiêm tinh chung nổi bật nhất trong số các `CompatibilityScore` cao nhất tuần đó — không bịa, phải truy ngược lại dữ liệu Synastry thật

**Screen Flow:**

```
[10:00 sáng Chủ nhật — Push notification: "Vòng Lá tuần này của bạn đã sẵn sàng"]
   ↓
[Recap Screen — dạng story/card trượt ngang, tối đa 4-5 card]
   Card 1: "Bạn đã mở X lá. Nhận Y request."
   Card 2: "Kiểu người hợp bạn nhất tuần này: [mô tả ngắn]"
   Card 3 (nếu có mutual): "1 Lá đã mở lại với bạn" — KHÔNG nói rõ kết quả tiếp theo (open ending)
   Card 4: CTA nhẹ "Vòng Lá tiếp theo: thứ 7 tới"
   ↓
[Nút Share ở mỗi card] → [Share sheet — tạo card ảnh riêng cho card đang xem]
```

### 4.3. Safety & Privacy requirements (bắt buộc, không thương lượng)

- [ ] KHÔNG BAO GIỜ lưu hoặc hiển thị tọa độ GPS chính xác của user — chỉ dùng thành phố/quận do user tự chọn
- [ ] KHÔNG hiển thị khoảng cách dạng số cụ thể (vd "300m") giữa 2 user trong bất kỳ trường hợp nào
- [ ] Mọi user trong matching pool phải qua bước xác minh ảnh cơ bản (không cần AI phức tạp ở v0.4, có thể là kiểm duyệt thủ công ban đầu)
- [ ] Report được xử lý trong vòng 24h, có quy trình escalation rõ ràng cho team vận hành
- [ ] User có thể rời khỏi matching pool bất kỳ lúc nào, dữ liệu vị trí/intent bị xóa ngay lập tức khỏi pool active

### 4.4. KPI release v0.4

| Metric | Target |
|---|---|
| Tổng user | 50.000 |
| % matching-ready (Level 4+) | ≥ 60% |
| Mutual match rate | ≥ 20% trên tổng request |
| Match/tuần | ≥ 5.000 |
| Report rate nghiêm trọng | < 1% pool active |

---

## 5. v0.5 — Lá Mai Room (Tháng 5)

### 5.1. Mục tiêu release

Mở marketplace — "Lá Dẫn" (reader/astrologer/creator) curate match theo theme, tạo kênh acquisition độc lập với viral loop hữu cơ.

### 5.2. Danh sách feature

#### F5.1 — Room Creation (cho Lá Dẫn)

**User story:**
> Là một Lá Dẫn (reader/creator có xác minh), tôi muốn tạo một "room" theo theme cụ thể, mời cộng đồng của tôi tham gia, và curate match thủ công thay vì để thuật toán quyết định hoàn toàn.

**Acceptance criteria:**
- [ ] Chỉ user có vai trò `la_dan` (cấp quyền thủ công bởi team vận hành ở giai đoạn đầu) mới tạo được room
- [ ] Lá Dẫn đặt tên room, mô tả theme, giới hạn số lượng tham gia (mặc định 40-80)
- [ ] User tham gia room cần đạt Profile Level cao hơn Vòng Lá thông thường (yêu cầu cả ảnh xác minh + giờ sinh)
- [ ] Lá Dẫn có dashboard riêng: danh sách người tham gia, AI gợi ý top match, công cụ để chọn/curate intro thủ công
- [ ] Sau khi Lá Dẫn chọn intro, cả hai user nhận "Lá Mai" — tương tự cơ chế mutual accept của Vòng Lá nhưng có thêm bước Lá Dẫn duyệt trước

**Data model:**

```
LaDan {
  user_id: UUID (FK → User)
  verified: boolean
  bio: string
  specialty: enum('astrology','tarot','creator','community')
  rating_avg: float
  approved_by: string                // admin đã duyệt
  approved_at: timestamp
}

Room {
  id: UUID
  la_dan_user_id: UUID (FK → LaDan)
  theme_name: string
  theme_description: string
  max_participants: int
  status: enum('open','running','closed')
  ticket_price: int | null           // null = free
  created_at: timestamp
}

RoomParticipant {
  room_id: UUID (FK → Room)
  user_id: UUID (FK → User)
  joined_at: timestamp
  profile_completeness_score: float
}

LaMaiIntro {
  id: UUID
  room_id: UUID (FK → Room)
  la_dan_user_id: UUID
  user_a_id: UUID
  user_b_id: UUID
  ai_suggested: boolean
  curated_by_la_dan: boolean
  status: enum('pending','mutual','declined')
  created_at: timestamp
}
```

**Astro Skill áp dụng:**
- Chart: **Synastry Chart** (engine dùng chung với F3.2/F4.1) cho phần "AI gợi ý top match"; Lá Dẫn xem được điểm Synastry thô trong dashboard để hỗ trợ quyết định, không phải đoán mò
- House system: Whole Sign, đồng bộ toàn hệ thống
- Lá Dẫn có quyền xem chi tiết aspect (không chỉ điểm tổng) trong dashboard — đây là khác biệt so với user thường chỉ thấy `card_label` mô tả ở F4.1, vì Lá Dẫn cần đủ thông tin để curate thủ công

**Screen Flow (phía Lá Dẫn — dashboard riêng, không chung UI với user thường):**

```
[Lá Dẫn Dashboard] → [Nút "Tạo Room mới"]
   ↓
[Đặt tên room, mô tả theme, giới hạn số người, giá vé (hoặc free)]
   ↓
[Room mở — chia sẻ link mời cộng đồng của Lá Dẫn]
   ↓
[Người tham gia vào room → Lá Dẫn thấy danh sách trong dashboard]
   Mỗi người hiện: profile_completeness_score, ảnh, thông tin cơ bản
   ↓
[Lá Dẫn bấm "Xem gợi ý AI"] → [Danh sách cặp được AI xếp hạng theo Synastry score]
   Mỗi cặp hiện: điểm tổng + breakdown Sun/Moon/Venus/Mars + aspect nổi bật
   ↓
[Lá Dẫn chọn cặp muốn curate] → [Xác nhận tạo Lá Mai Intro]
   ↓
[Cả hai user A và B nhận thông báo: "[Lá Dẫn] nghĩ hai bạn hợp nhau trong room [tên]"]
```

---

#### F5.2 — Reader Booking

**User story:**
> Là một người dùng muốn hiểu sâu hơn về Lá Ghép hoặc birth chart của mình, tôi muốn đặt lịch một buổi đọc 15 phút với một Lá Dẫn cụ thể.

**Acceptance criteria:**
- [ ] Lá Dẫn thiết lập lịch trống (availability) trong dashboard riêng
- [ ] User chọn slot, thanh toán trước khi xác nhận booking
- [ ] Có nhắc lịch tự động cho cả 2 bên trước 30 phút
- [ ] Sau buổi đọc, user có thể đánh giá (rating 1-5 + review text optional)

**Data model:**

```
ReaderAvailability {
  id: UUID
  la_dan_user_id: UUID
  slot_start: timestamp
  slot_end: timestamp
  booked: boolean
}

Booking {
  id: UUID
  user_id: UUID
  la_dan_user_id: UUID
  availability_slot_id: UUID (FK → ReaderAvailability)
  price_paid: int
  status: enum('confirmed','completed','cancelled','no_show')
  rating: int | null
  review_text: string | null
}
```

**Astro Skill áp dụng:**
- Chart: tùy mục đích booking — nếu user muốn hiểu bản thân sâu hơn → **Natal Chart** (Placidus được phép ở đây nếu user xác nhận giờ sinh chính xác, theo quy tắc 0.5.2); nếu muốn hiểu một mối quan hệ đã xác lập (đã yêu nhau/bạn thân lâu năm) → **Composite Chart**
- Composite Chart CHỈ xuất hiện như một lựa chọn trong booking với Lá Dẫn — không bao giờ tự động hóa cho user thường, đúng theo quy tắc 0.5.3 (cần con người diễn giải vì cách đọc phức tạp)
- Cách đọc Composite: tính midpoint của từng cặp hành tinh tương ứng giữa Natal Chart A và B → dựng thành 1 chart thứ ba → Lá Dẫn dùng chart này để đọc trực tiếp với khách trong buổi booking, không qua `ContentTemplate` tự động

**Screen Flow:**

```
[User — Profile Lá Dẫn] → [Nút "Đặt lịch đọc"]
   ↓
[Chọn loại reading]
   ① "Hiểu bản thân sâu hơn" (Natal Chart)
   ② "Hiểu một mối quan hệ" (Composite Chart — cần nhập thêm thông tin người kia)
   ↓ (nếu chọn ②)
[Nhập ngày/giờ/nơi sinh của người kia — hoặc chọn từ Lá Ghép đã có sẵn nếu đã từng tạo]
   ↓
[Chọn slot trống của Lá Dẫn — calendar view]
   ↓
[Thanh toán]
   ↓
[Xác nhận booking — nhắc lịch tự động trước 30 phút cho cả 2 bên]
   ↓ (sau buổi đọc)
[Màn đánh giá — rating 1-5 sao + review text optional]
```

---

#### F5.3 — Payout Engine (anti-fraud)

**User story:**
> Là một Lá Dẫn, tôi muốn nhận thưởng dựa trên kết quả thật đã được xác minh — không phải dựa trên con số report tôi tự khai.

**Acceptance criteria:**
- [ ] KHÔNG BAO GIỜ trả thưởng ngay lập tức khi room/match được tạo — mọi payout đều có `hold_period`
- [ ] Payout chỉ tính cho `MatchingPoolMember`/`RoomParticipant` đạt đủ điều kiện: profile đủ Level yêu cầu + đã tham gia thật (có activity log) + không bị report trong 72h
- [ ] Hệ thống tự động phát hiện duplicate (cùng device/IP) trong room — loại khỏi payout calculation
- [ ] Payout được giải ngân theo lịch: T+1 (base nếu đạt ngưỡng tối thiểu), T+7 (bonus theo qualified participant), T+14 (bonus chất lượng sau khi xác minh không có report/fraud)

**Data model:**

```
PayoutCalculation {
  id: UUID
  la_dan_user_id: UUID
  room_id: UUID (FK → Room) | null
  calculation_type: enum('base','qualified_bonus','quality_bonus')
  amount: int
  status: enum('calculated','held','released','rejected')
  hold_until: timestamp
  fraud_check_passed: boolean | null
  released_at: timestamp | null
}

FraudFlag {
  id: UUID
  user_id: UUID
  flag_type: enum('duplicate_device','duplicate_ip','suspicious_pattern','report_received')
  detected_at: timestamp
  reviewed_by: string | null
  resolution: enum('confirmed_fraud','false_positive','pending') | null
}
```

### 5.3. KPI release v0.5

| Metric | Target |
|---|---|
| Tổng user | 75.000 |
| Lá Dẫn active | ≥ 10 |
| Room/tháng | ≥ 20 |
| Paid room conversion | ≥ 5% |
| Booking repeat rate (lần 2 trở lên) | ≥ 15% |

---

## 6. v0.6 — Season Recap & Premium (Tháng 6)

### 6.1. Mục tiêu release

Đóng gói toàn bộ dữ liệu 6 tháng thành một trải nghiệm Wrapped-style, đồng thời ra mắt monetization có cấu trúc (Premium tier).

### 6.2. Danh sách feature

#### F6.1 — Season Recap

**User story:**
> Là một người dùng đã dùng app từ đầu mùa, tôi muốn nhận một bản tổng kết cá nhân hóa, đẹp, đủ để tôi muốn chia sẻ như một cách thể hiện bản thân — giống Spotify Wrapped nhưng cho hành trình cảm xúc của tôi.

**Acceptance criteria:**
- [ ] Recap tổng hợp dữ liệu từ toàn bộ chu kỳ (6 tuần/mùa, KHÔNG đợi 1 năm như Spotify) — đây là điểm khác biệt cố ý để recap trở thành growth loop lặp lại
- [ ] Nội dung gồm: lá tarot xuất hiện nhiều nhất, chủ đề hỏi nhiều nhất, kiểu người được ghép nhiều nhất, số Lá Ghép đã mở, 1 "lời nhắn của mùa" cá nhân hóa
- [ ] Thiết kế dạng card trượt (story format) — nhiều card nhỏ thay vì 1 ảnh dài, tối ưu cho việc share từng phần lên story
- [ ] Mỗi card có thể share riêng lẻ hoặc share trọn bộ
- [ ] Recap available cho TẤT CẢ user (kể cả chưa từng trả phí) ở mức cơ bản — bản đầy đủ (Full Season Report) là tính năng trả phí

**Data model:**

```
Season {
  id: UUID
  season_number: int
  start_date: date
  end_date: date                    // 6 tuần
}

SeasonRecap {
  id: UUID
  user_id: UUID
  season_id: UUID (FK → Season)
  most_frequent_tarot_card: string
  top_topic: string
  most_matched_type: string
  la_ghep_opened_count: int
  vong_la_participated_count: int
  season_message: string
  is_premium_unlocked: boolean
  generated_at: timestamp
}
```

**Astro Skill áp dụng:**
- Không tính chart mới — tổng hợp lại toàn bộ `DailyTransitSnapshot`, `UserTransitInsight`, `CompatibilityScore` của user trong suốt mùa (6 tuần)
- "Kiểu người được ghép nhiều nhất" lấy từ trung bình các `card_label`/aspect nổi bật xuất hiện trong các `MutualMatch` của mùa đó — đảm bảo đây là dữ liệu thật đã xảy ra, không phải mô tả chung chung theo Sun sign

**Screen Flow:**

```
[Cuối mùa (tuần 6) — Push notification: "Mùa Lá đầu tiên của bạn đã sẵn sàng"]
   ↓
[Season Recap — dạng story trượt, học theo format Spotify Wrapped]
   Card 1: Lá tarot xuất hiện nhiều nhất trong mùa
   Card 2: Chủ đề bạn hỏi/quan tâm nhiều nhất
   Card 3: Kiểu người được ghép nhiều nhất với bạn
   Card 4: Số Lá Ghép đã mở trong mùa
   Card 5: "Lời nhắn của mùa" — cá nhân hóa, kết bằng tông mở (không kết luận tuyệt đối)
   [Nếu chưa Premium] Card cuối: preview Full Season Report bị blur, nút nâng cấp
   ↓
[Mỗi card có nút Share riêng — tối ưu để share từng card lên story]
   ↓
[Cuối chuỗi card — CTA: "Mùa tiếp theo bắt đầu [ngày]"]
```

---

#### F6.2 — Premium Tier

**User story:**
> Là một người dùng đã gắn bó với app, tôi muốn trả phí để có trải nghiệm sâu hơn — nhưng không bao giờ phải trả phí chỉ để nói chuyện với người tôi đã match.

**Acceptance criteria:**
- [ ] Gói Plus và Premium theo bảng phân định Free/Paid ở Playbook Phần 8 — implement đúng ranh giới: KHÔNG đưa chat cơ bản sau mutual vào paywall dưới bất kỳ hình thức nào
- [ ] Subscription quản lý qua App Store/Google Play in-app purchase, tuân thủ chính sách nền tảng
- [ ] Có trang quản lý subscription rõ ràng — user tự hủy được mà không cần liên hệ support
- [ ] Free trial 7 ngày cho user mới để giảm rào cản dùng thử

**Data model:**

```
Subscription {
  id: UUID
  user_id: UUID
  tier: enum('free','plus','premium')
  started_at: timestamp
  renews_at: timestamp | null
  cancelled_at: timestamp | null
  platform: enum('ios','android')
  platform_transaction_id: string
}
```

#### F6.3 — Consent & Data Management Dashboard

**User story:**
> Là một người dùng, tôi muốn xem được toàn bộ dữ liệu app đang lưu về tôi và có thể xóa bất kỳ phần nào tôi muốn, để tôi tin tưởng vào việc dùng app lâu dài.

**Acceptance criteria:**
- [ ] User xem được danh sách đầy đủ dữ liệu cá nhân đang lưu (birth data, natal chart, lịch sử Lá Ghép, ảnh xác minh...)
- [ ] User có thể xóa từng loại dữ liệu riêng lẻ hoặc xóa toàn bộ tài khoản
- [ ] Khi xóa, hệ thống xử lý trong vòng 30 ngày theo quy định pháp luật, có email xác nhận khi hoàn tất
- [ ] Tuân thủ Luật Bảo vệ dữ liệu cá nhân Việt Nam (hiệu lực 01/01/2026) — consent gắn với mục đích cụ thể, có thể rút lại bất kỳ lúc nào

**Data model:**

```
DataDeletionRequest {
  id: UUID
  user_id: UUID
  scope: enum('full_account','birth_data','la_ghep_history','photos','all')
  requested_at: timestamp
  status: enum('pending','processing','completed')
  completed_at: timestamp | null
}
```

### 6.3. KPI release v0.6 (mục tiêu cuối kỳ 6 tháng)

| Metric | Target |
|---|---|
| DAU | 100.000 |
| D30 retention | ≥ 30% |
| Paid conversion | 5-8% |
| Lá Dẫn active | ≥ 50 |
| % user tạo Season Recap Card | ≥ 40% |

---

## 7. Yêu cầu kỹ thuật xuyên suốt (Non-functional requirements)

### 7.1. Performance

- Tính toán natal chart (Sun/Moon/Rising/Venus/Mars) phải hoàn thành trong < 2 giây sau khi user nhập đủ dữ liệu
- Daily Astro content phải sẵn sàng trước 6:00 sáng mỗi ngày cho toàn bộ user base (batch job chạy ban đêm)
- Vòng Lá matching calculation (F4.1) phải hoàn thành cho toàn bộ pool trong vòng 15 phút trước giờ mở (19:30 → 20:00)

### 7.2. Bảo mật & Privacy (áp dụng toàn hệ thống)

- Birth data (ngày/giờ/nơi sinh) phải được encrypt at rest
- Không bao giờ log hoặc expose tọa độ GPS chính xác trong bất kỳ API response nào liên quan đến matching/Vòng Lá
- Mọi tính năng thu thập dữ liệu mới phải có consent screen riêng, version hóa được (để biết user đồng ý phiên bản nào)

### 7.3. Content Operations

- `ContentTemplate` (F1.2) và `StatementBank` (F2.1) cần quy trình review nội bộ trước khi publish — không tự động generate bằng AI mà không qua kiểm duyệt con người, đặc biệt với nội dung liên quan tarot/tâm lý
- Cần tối thiểu 12 template cho mỗi placement type (Sun, Moon, Venus, Mars) trước khi launch v0.1 — theo đúng yêu cầu ở Playbook Phần 10

### 7.4. Phụ thuộc bên ngoài cần chốt sớm

| Phụ thuộc | Cần cho | Deadline đề xuất |
|---|---|---|
| Ephemeris data provider — phải hỗ trợ **Western Tropical zodiac** + tính được cả **Whole Sign** và **Placidus** house system (xem Chương 0.5) | F1.2, F3.1, F3.2, F4.1, F5.2 | Trước khi bắt đầu sprint v0.1 — đây là phụ thuộc rủi ro tiến độ cao nhất toàn dự án |
| Geocoding API (cho birth_place → lat/lng/timezone, cần cho House calculation) | F1.1 Level 3 | Trước v0.1 launch |
| Push notification service | F1.2, F2.2, F3.3, F4.3 | Trước v0.1 launch |
| In-app purchase integration (iOS/Android) | F6.2 | Trước v0.6 |
| Ảnh xác minh (kiểm duyệt thủ công hoặc AI) | F4.1 | Trước v0.4 |
| Web view landing page (cho Hành trình C — nhận link chưa cài app, xem Chương 7.5) | F2.1, F2.2, F3.1, F3.2 | Trước v0.2 launch |

---

### 7.5. User Flow toàn trình — hành trình xuyên suốt nhiều release

> Các Screen Flow ở từng feature mô tả chi tiết trong 1 tính năng. Chương này nối chúng lại thành hành trình thật của một user từ ngày đầu đến tháng thứ 6 — dùng để team design/QA kiểm tra tính liền mạch giữa các release.

### Hành trình A — User thường (không phải Lá Dẫn)

```
THÁNG 1
[Cài app] → [Onboarding F1.1] → [Astro Profile Basic] → [Lá Khai Sinh Card F1.3]
   → [Share card] → [Quay lại app hàng ngày qua Daily Astro F1.2]

THÁNG 2
[Sau 3 ngày streak] → [Prompt thêm giờ sinh F1.4] → [Mời bạn xác nhận F2.1]
   → [Nhận Pitch Card từ bạn khác F2.2] → [So sánh bạn thân nói vs app nói]

THÁNG 3
[Tạo Lá Ghép với crush F3.2] → [Preview bị blur] → [Gửi cho crush]
   → [Prompt thêm nơi sinh để mở Transit Engine F3.1] → [Nhận transit insight cá nhân]
   → [Gửi transit insight cho bạn thân — Trigger Social Currency]

THÁNG 4
[Đủ Level 4 — được mời vào Vòng Lá] → [Tối thứ 7: nhận 5 lá úp F4.1]
   → [Mở 2-3 lá] → [Mutual với 1 người F4.2] → [Chat với icebreaker gợi ý]
   → [Chủ nhật: nhận Recap Story F4.3] → [Share recap lên Threads]

THÁNG 5
[Thấy quảng cáo Room từ 1 Lá Dẫn mình follow] → [Vào Room F5.1]
   → [Nhận Lá Mai Intro do Lá Dẫn curate] → [Có thể book reading 15 phút F5.2]

THÁNG 6
[Nhận Season Recap F6.1] → [Share từng card] → [Prompt nâng cấp Premium F6.2]
   → [Có thể vào Data Management xem/xóa dữ liệu bất kỳ lúc nào F6.3]
```

### Hành trình B — Lá Dẫn (reader/creator)

```
THÁNG 5 (Lá Dẫn chỉ xuất hiện từ v0.5)
[Được team duyệt thủ công thành Lá Dẫn] → [Vào Lá Dẫn Dashboard riêng]
   → [Tạo Room đầu tiên F5.1] → [Mời cộng đồng của mình]
   → [Dùng AI gợi ý Synastry để curate match] → [Theo dõi payout có hold period F5.3]

THÁNG 6
[Mở thêm Reader Booking slot F5.2] → [Nhận booking, đọc Composite Chart trực tiếp]
   → [Theo dõi rating/review tích lũy]
```

### Hành trình C — User chỉ nhận, chưa từng cài app trước đó (qua referral)

> Đây là hành trình quan trọng nhất để đo hiệu quả viral loop — vì đây chính là người dùng MỚI mà toàn bộ chiến lược referral (Playbook Phần 4) nhắm tới.

```
[Nhận link Lá Ghép/Pitch Card/Transit insight từ bạn — KHÔNG có app]
   ↓
[Mở link → Landing web view, KHÔNG bắt buộc tải app ngay]
   ↓
[Thấy preview bị blur — đủ tò mò để tương tác tiếp]
   ↓
[Nhập ngày sinh (và giờ sinh nếu cần) ngay trên web view]
   ↓
[Thấy kết quả của riêng mình — đây là khoảnh khắc "aha"]
   ↓
[CTA: "Tải Lá Lành để xem thêm" — chỉ xuất hiện SAU khoảnh khắc aha, không trước]
   ↓
[Cài app → tự động đăng nhập bằng SĐT/email đã nhập ở web view, KHÔNG bắt nhập lại]
   ↓
[Vào thẳng Home với Astro Profile đã có sẵn — không phải onboarding từ đầu]
```

**Yêu cầu kỹ thuật quan trọng cho Hành trình C:** Toàn bộ landing page nhận link (Lá Ghép, Pitch Card, Transit forward) phải hoạt động được trên web view KHÔNG cần cài app trước — đây là yêu cầu bắt buộc xuyên suốt F2.1, F2.2, F3.1, F3.2. Nếu bắt user tải app trước khi thấy bất kỳ giá trị nào, toàn bộ cơ chế Information Gap (Trigger 1, Playbook Phần 4) sẽ gãy ngay từ bước đầu.

---

## 8. Bảng tổng hợp Out-of-scope toàn dự án (6 tháng đầu)

Những thứ CỐ TÌNH không làm trong 6 tháng đầu, để team không bị cám dỗ mở rộng scope:

- Dating app dạng swipe tự do 24/7 — mâu thuẫn trực tiếp với nguyên tắc scarcity của Vòng Lá
- Hiển thị vị trí GPS chính xác hoặc khoảng cách dạng số — vi phạm Safety requirement (Phần 4.3)
- Thu phí để xem ai thích mình / để chat sau mutual — vi phạm Nguyên tắc 3 (Playbook)
- Cho phép Lá Chứng/Pitch Card nhập text tự do — rủi ro toxic/bắt nạt
- Trả thưởng Lá Dẫn ngay khi có signup/match — rủi ro fraud, vi phạm nguyên tắc payout (F5.3)
- Event offline có quản trò trực tiếp — chưa đủ nguồn lực vận hành, để giai đoạn sau tháng 6

---

*Tài liệu PRD này map trực tiếp từ "Lá Lành — Playbook Sản phẩm & Launch 6 tháng". Mọi thay đổi scope cần đối chiếu lại với Phần 0-2 của Playbook để đảm bảo không phá vỡ nguyên tắc thiết kế gốc.*
