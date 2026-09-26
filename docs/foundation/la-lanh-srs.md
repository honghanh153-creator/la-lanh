# Lá Lành — Software Requirements Specification (SRS)

> Phiên bản: 1.0 · Cập nhật: tháng 6/2026
> Tài liệu này là tầng kỹ thuật của PRD (`la-lanh-prd.md`). PRD trả lời "tính năng gì, vì sao". SRS này trả lời "hệ thống nào xử lý, dữ liệu chảy ra sao, ai gọi ai".
>
> **Quyết định kiến trúc nền tảng đã chốt:**
> 1. **Tách rõ Compute (BE tính toán) và Generation (AI viết nội dung)** — không bao giờ để AI tự tính vị trí hành tinh, không bao giờ để BE tự viết câu văn cảm xúc.
> 2. **Content sinh theo mô hình cache-first** — LLM sinh 1 lần cho mỗi combination phổ biến, cache lại; chỉ gọi LLM live cho trường hợp hiếm.
> 3. **Modular monolith** — 1 service, module boundary rõ, sẵn sàng tách microservice khi tải tăng.
>
> **Astro Engine v2:** phần 2 dưới đây còn chứa contract v1 Western-only. Chuẩn có hiệu lực cho triển khai mới, US-07 và các consumer về sau là [`la-lanh-astro-engine-spec.md`](./la-lanh-astro-engine-spec.md): Western Tropical và Jyotish Sidereal là hai snapshot độc lập; date-only dùng uncertainty interval; Aura/readings dùng multi-factor provenance. Mọi điểm mâu thuẫn về phép tính ưu tiên engine spec cho đến khi SRS được migrate hoàn toàn.

---

## 1. Kiến trúc hệ thống tổng quan

### 1.1. Sơ đồ kiến trúc cấp cao

```
                                ┌─────────────────────────┐
                                │      Client Apps         │
                                │  (iOS / Android / Web)   │
                                └───────────┬──────────────┘
                                            │ HTTPS/REST + WebSocket (chat)
                                            ▼
                                ┌─────────────────────────┐
                                │       API Gateway         │
                                │  (auth, rate limit,       │
                                │   request routing)        │
                                └───────────┬──────────────┘
                                            │
        ┌───────────────┬───────────────────┼───────────────────┬───────────────┐
        ▼               ▼                   ▼                   ▼               ▼
┌──────────────┐ ┌──────────────┐  ┌──────────────────┐ ┌──────────────┐ ┌──────────────┐
│ Identity &    │ │ Astro Engine  │  │ Content           │ │ Matching      │ │ Marketplace   │
│ Profile       │ │ Module        │  │ Generation        │ │ Module        │ │ Module        │
│ Module        │ │ (Compute)     │  │ Module (AI)       │ │               │ │ (v0.5+)       │
└──────┬───────┘ └──────┬───────┘  └─────────┬─────────┘ └──────┬───────┘ └──────┬───────┘
       │                │                     │                  │                │
       └────────────────┴─────────┬───────────┴──────────────────┴────────────────┘
                                   ▼
                       ┌───────────────────────┐
                       │   Shared Data Layer     │
                       │  PostgreSQL (chính)     │
                       │  Redis (cache + queue)  │
                       │  Object Storage (ảnh)   │
                       └───────────────────────┘
                                   │
                       ┌───────────┴───────────┐
                       ▼                       ▼
              ┌─────────────────┐   ┌─────────────────────┐
              │ Ephemeris        │   │  LLM Provider         │
              │ Calculation Lib  │   │  (Claude API)          │
              │ (internal, BE)   │   │  (external, qua queue) │
              └─────────────────┘   └─────────────────────┘
```

### 1.2. Nguyên tắc thiết kế module (Modular Monolith)

Toàn bộ nằm trong một codebase modular monolith nhưng có ít nhất hai process triển khai được độc lập: API và worker. Mỗi module **chỉ giao tiếp qua interface/package nội bộ đã định nghĩa** (không query thẳng bảng của module khác); API có thể gọi đồng process, worker import cùng Astro Engine package. Đây là điều kiện để có thể tách microservice sau này mà không viết lại nghiệp vụ.

| Module | Trách nhiệm | Không được làm |
|---|---|---|
| **Identity & Profile** | User, BirthData, ProfileLevel, Consent | Không tính toán chiêm tinh, không sinh content |
| **Astro Engine** (Compute) | Tính NatalChart, TransitChart, Synastry, Composite — thuần toán học/thiên văn | Không viết câu văn, không gọi LLM |
| **Content Generation** (AI) | Nhận dữ liệu chart có cấu trúc từ Astro Engine → sinh nội dung tự nhiên, quản lý cache | Không tự tính chart, không bao giờ suy diễn vị trí hành tinh |
| **Matching** | Cohort pool, multidimensional relationship evidence (gọi Astro Engine), slate diversity, Vòng Lá, Mutual/Chat | Không tự tính Synastry, không chẩn đoán tâm lý và không tạo compatibility verdict |
| **Marketplace** (v0.5+) | Room, Lá Dẫn, Booking, Payout | Không tự tính chart — gọi Astro Engine cho Composite Chart |
| **Notification** | Push, in-app banner, email | — |

**Quy tắc giao tiếp giữa module:** mọi consumer gọi Astro Engine qua internal package interface, không qua public client API. API call trực tiếp trong process; worker dùng cùng package trong worker process. Khi tách microservice, interface adapter có thể chuyển thành gRPC/REST mà không đổi contract phía consumer.

---

## 2. Module — Astro Engine (Compute Layer)

> Đây là module quan trọng nhất hệ thống. Mọi sai số ở đây lan ra toàn bộ sản phẩm — vì Content Generation (AI) tin tưởng tuyệt đối vào dữ liệu module này trả về, không tự kiểm tra lại.

### 2.1. Trách nhiệm

Tính toán thuần túy, xác định, không có yếu tố "sáng tạo". Input là dữ liệu sinh + thời điểm, output là vị trí hành tinh/house/aspect dưới dạng số liệu có cấu trúc.

### 2.2. Các hàm tính toán (Compute Functions)

```
computeNatalChart(birthDate, birthTime?, birthPlace?) → NatalChartResult
computeTransitSnapshot(date) → TransitSnapshotResult       // dùng chung toàn hệ thống, không theo từng user
computeUserTransitImpact(natalChart, transitSnapshot) → UserTransitImpactResult
computeSynastry(natalChartA, natalChartB) → SynastryResult
computeComposite(natalChartA, natalChartB) → CompositeChartResult
```

**Quy tắc bắt buộc cho mọi hàm trên** (tham chiếu PRD Chương 0.5):
- Hệ tọa độ: **Western Tropical** — không có tham số chọn Sidereal trong 6 tháng đầu, hardcode để tránh nhầm lẫn vận hành
- House system: tham số `houseSystem: 'whole_sign' | 'placidus'` — mặc định `whole_sign`, chỉ Marketplace module (đọc 1-1 với Lá Dẫn) được truyền `placidus`
- Orb: tham số theo bảng 0.5.4 trong PRD, không hardcode trong từng lời gọi mà đọc từ config tập trung `OrbConfig`

### 2.3. Data flow chi tiết — "BE gen chart" (Compute Pipeline)

```
[1] Request vào: { userId, birthDate, birthTime?, birthPlace? }
        │
        ▼
[2] Validate input
    - birthDate hợp lệ (không tương lai, không quá 120 năm trước)
    - Nếu có birthPlace → gọi Geocoding API lấy { lat, lng, timezone }
        │
        ▼
[3] Gọi Ephemeris Calculation Library (nội bộ, không qua network)
    - Input: { julianDate (tính từ birthDate+birthTime+timezone), lat, lng }
    - Output thô: vị trí độ-phút-giây của Sun/Moon/Mercury/Venus/Mars/
                  Jupiter/Saturn/Uranus/Neptune/Pluto tại thời điểm đó
        │
        ▼
[4] Map vị trí độ sang Sign (12 cung, mỗi cung 30°)
        │
        ▼
[5] NẾU có birthTime + birthPlace:
    - Tính Ascendant (cung mọc) từ giờ sinh + vĩ độ/kinh độ
    - Tính 12 House theo houseSystem được chọn (Whole Sign hoặc Placidus)
    - Gán mỗi hành tinh vào House tương ứng
        │
        ▼
[6] Tính Aspect giữa các cặp hành tinh (góc chiếu, theo Orb config)
        │
        ▼
[7] Output: NatalChartResult (JSON có cấu trúc — xem schema 2.4)
        │
        ▼
[8] Ghi vào bảng NatalChart (persist) — đây là nguồn sự thật duy nhất,
    Content Generation Module KHÔNG được tính lại, chỉ đọc từ đây
```

### 2.4. Schema dữ liệu output (Compute → Content Generation contract)

Đây là **API contract** giữa Astro Engine và Content Generation — phải giữ ổn định, mọi thay đổi field phải version hóa.

```json
// NatalChartResult — output của computeNatalChart()
{
  "chartId": "uuid",
  "userId": "uuid",
  "zodiacSystem": "western_tropical",
  "houseSystem": "whole_sign",          // hoặc "placidus", hoặc null nếu chưa đủ dữ liệu
  "dataCompleteness": "sun_only | sun_moon | full_chart",
  "placements": {
    "sun":     { "sign": "scorpio", "degree": 14.32, "house": 7 },
    "moon":    { "sign": "cancer",  "degree": 2.10,  "house": 9 },
    "rising":  { "sign": "leo",     "degree": 0.5 },
    "venus":   { "sign": "scorpio", "degree": 28.0,  "house": 7 },
    "mars":    { "sign": "libra",   "degree": 11.2,  "house": 6 }
    // ... các hành tinh khác nếu cần (Mercury, Jupiter, Saturn dùng cho Transit sau này)
  },
  "houses": {
    "house_1": "leo", "house_2": "virgo", "...": "..."   // null nếu chưa có house data
  },
  "aspectsNatal": [
    { "planetA": "venus", "planetB": "mars", "aspectType": "square", "orb": 1.8 }
  ],
  "computedAt": "2026-06-20T10:00:00Z",
  "ephemerisVersion": "swisseph-2.10"
}
```

```json
// UserTransitImpactResult — output của computeUserTransitImpact()
{
  "userId": "uuid",
  "snapshotDate": "2026-06-20",
  "impacts": [
    {
      "transitPlanet": "saturn",
      "transitSign": "pisces",
      "affectsUserHouse": 7,                 // house nào của user đang bị transit này tác động
      "aspectToNatal": [
        { "natalPlanet": "venus", "aspectType": "square", "orb": 1.2, "exact": true }
      ],
      "transitSpeed": "slow",                 // "fast" (Moon) | "medium" (Mercury-Mars) | "slow" (Jupiter-Pluto)
      "startDate": "2026-03-01",
      "endDate": "2026-11-15",
      "isExactNow": true                      // orb hẹp nhất, đang ở đỉnh điểm ảnh hưởng
    }
  ]
}
```

```json
// SynastryResult — output của computeSynastry()
{
  "synastryId": "uuid",
  "userAId": "uuid", "userBId": "uuid",
  "dataCompletenessA": "full_chart", "dataCompletenessB": "sun_only",
  "interAspects": [
    { "planetA": "venus", "ownerA": "A", "planetB": "mars", "ownerB": "B",
      "aspectType": "trine", "orb": 2.1, "category": "harmonious" },
    { "planetA": "mars", "ownerA": "A", "planetB": "saturn", "ownerB": "B",
      "aspectType": "square", "orb": 2.8, "category": "tense" }
  ],
  "dimensions": {
    "communication": {"strongestStrength": 0.82, "evidenceIds": ["synastry:mercury:moon:trine"]},
    "emotional": {"strongestStrength": 0.64, "evidenceIds": ["synastry:moon:venus:sextile"]},
    "friction": {"strongestStrength": 0.48, "evidenceIds": ["synastry:mars:saturn:square"]}
  },
  "scalarScoreEligible": false,
  "methodVersion": "synastry-v2",
  "computedAt": "2026-06-20T10:00:00Z"
}
```

### 2.5. Thư viện kỹ thuật đề xuất

| Hạng mục | Đề xuất | Ghi chú |
|---|---|---|
| Ephemeris calculation | Thư viện ephemeris mở dạng Swiss Ephemeris (hoặc tương đương) | Cần research license — bản miễn phí có thể giới hạn năm; cần xác nhận trước sprint v0.1 |
| House system calculation | Tự implement Whole Sign (đơn giản — chia đều theo Ascendant); dùng thư viện có sẵn cho Placidus (phức tạp hơn về toán) | |
| Geocoding | Bất kỳ provider geocoding thương mại nào hỗ trợ trả về timezone | Cần cho bước 2 trong pipeline 2.3 |
| Ngôn ngữ/runtime cho Compute | Khuyến nghị tách thành internal package riêng (không phụ thuộc framework web) để dễ test toán học độc lập | |

---

## 3. Module — Content Generation (AI Layer)

### 3.1. Trách nhiệm

Nhận `NatalChartResult` / `UserTransitImpactResult` / `SynastryResult` (dữ liệu đã tính xong, đã đúng) → viết thành nội dung tự nhiên theo đúng 4 quy tắc viết content (PRD/Playbook). **Không bao giờ tự suy luận số liệu chiêm tinh** — nếu thiếu dữ liệu, trả lỗi rõ ràng thay vì đoán.

### 3.2. Chiến lược cache-first — lý do và cách vận hành

**Vấn đề cần giải:** gọi LLM live cho mỗi user mỗi ngày (100.000 DAU × 1 Daily Astro/ngày) là chi phí không kiểm soát được. Nhưng phần lớn combination (Sun sign × Moon sign × transit hôm nay) sẽ LẶP LẠI giữa nhiều user — vì số lượng combination hữu hạn, trong khi user là vô hạn.

**Giải pháp:**

```
combination_key = hash(sun_sign, moon_sign, active_transit_ids, intent_type)

NẾU combination_key đã có trong Content Cache (Redis + bảng GeneratedContent):
    → trả ngay nội dung đã cache, KHÔNG gọi LLM
NẾU chưa có:
    → gọi LLM (Claude API) sinh nội dung mới
    → lưu vào cache với key này, dùng lại cho mọi user trùng combination sau
```

**Số lượng combination cần cache trước (pre-warm), tính từ data model:**

| Loại content | Số chiều combination | Số lượng tối đa | Chiến lược |
|---|---|---|---|
| Daily Astro (Sun-level) | 12 Sun sign × ~10 transit Moon/ngày | ~120/ngày | Pre-generate batch mỗi đêm cho TOÀN BỘ 12 Sun sign — không chờ user request |
| Daily Astro (Moon-level, Level 2+) | 12 Sun × 12 Moon × transit | ~1.440/ngày | Pre-generate cho các combination ĐÃ TỪNG xuất hiện trong user base (không generate hết 144 tổ hợp nếu chưa ai cần) |
| Transit Insight theo House | 12 House × ~5 transit chậm đang active | ~60 đang active tại 1 thời điểm | Pre-generate khi `TransitEvent` mới bắt đầu (vd Saturn vào house mới), cache tồn tại suốt thời gian transit đó |
| Lá Ghép Synastry | Không cache theo combination chung — mỗi cặp A-B là duy nhất | N/A | Gọi LLM live, nhưng cache theo `synastryId` cụ thể (nếu A và B xem lại nhiều lần, không generate lại) |
| Lá Khai Sinh Card (Sun+Venus+Mars blend) | 12×12×12 = 1.728 tổ hợp | 1.728 | Pre-generate dần theo "lazy cache" — generate khi gặp lần đầu, cache vĩnh viễn vì nội dung tĩnh sign-level |

**Trường hợp gọi LLM live (không qua cache):**
- Lá Ghép Synastry — mỗi cặp người dùng cụ thể là duy nhất, nhưng cache lại theo `synastryId` sau lần đầu
- Season Recap (F6.1) — narrative tổng hợp hành vi cá nhân trong mùa, không thể cache chung
- Reader 1-1 reading (qua Lá Dẫn, không phải sản phẩm tự động — đây là con người viết/nói, không qua AI)

### 3.3. Data flow — "AI gen content từ chart data"

```
[1] Trigger: batch job hàng đêm (Daily Astro) HOẶC user action (tạo Lá Ghép)
        │
        ▼
[2] Content Generation Module nhận structured data từ Astro Engine
    (KHÔNG tự gọi Ephemeris — luôn qua Astro Engine module)
        │
        ▼
[3] Tính combination_key từ structured data
        │
        ▼
[4] Check cache (Redis trước, fallback PostgreSQL GeneratedContent table)
        │
        ├─── HIT ──→ [7] Trả nội dung cached
        │
        └─── MISS ─→ [5] Build prompt cho LLM
                          - System prompt: 4 quy tắc viết content (PRD Phần 5)
                            + ví dụ few-shot từ ContentTemplate đã review
                          - User data: structured JSON từ bước [2]
                              ▼
                     [6] Gọi Claude API
                          - Input: structured chart data + prompt instructions
                          - Output: text content
                          - QUAN TRỌNG: prompt cấm LLM tự bịa thêm placement
                            không có trong structured data đầu vào
                              ▼
                     [6.5] Content Safety Check (tự động + sample review thủ công)
                          - Check không chứa tên thật/thông tin định danh
                          - Check tone không toxic, không phán xét tuyệt đối
                          - Nếu fail → fallback về 1 template tĩnh dự phòng
                              ▼
                     [7] Lưu vào cache (GeneratedContent table + Redis)
                              │
                              ▼
                     [8] Trả nội dung cho user
```

### 3.4. Prompt Contract (system-level, áp dụng mọi lời gọi LLM)

```
ROLE: Bạn là content writer cho Lá Lành, viết theo đúng 4 quy tắc:
  1. Đặt tên vòng lặp, không kết luận
  2. Đặc thù theo placement, không chung theo cung  
  3. Gắn với thời điểm thật, có deadline cụ thể (nếu có endDate trong input)
  4. Hài hước = khoảng cách an toàn, không né tránh điều đau

INPUT: chỉ được dùng dữ liệu trong structured JSON cung cấp.
  KHÔNG được suy diễn thêm placement, KHÔNG được bịa thêm hành tinh/house
  không có trong input.

OUTPUT FORMAT: JSON { "content_text": string, "tone_tags": array }

CONSTRAINT: 80-150 từ, tiếng Việt, không dùng tên thật, 
  không dùng ngôn ngữ tuyệt đối ("luôn luôn", "chắc chắn sẽ").
```

### 3.5. Data model bổ sung cho module này

```
GeneratedContent {
  id: UUID
  combination_key: string (unique, indexed)   // hash của input chiêm tinh
  content_type: enum('daily_astro','transit_insight','la_khai_sinh','synastry_la_ghep','season_recap')
  content_text: string
  source_structured_data: JSON                 // snapshot input đã dùng để sinh — audit trail
  generated_by: enum('llm_live','llm_prewarmed','static_fallback')
  llm_model_version: string | null
  quality_reviewed: boolean
  created_at: timestamp
  hit_count: int                               // bao nhiêu lần cache này được dùng lại — đo hiệu quả cache
}

ContentSafetyFlag {
  generated_content_id: UUID (FK)
  flag_reason: enum('contains_pii','toxic_tone','absolute_language','other')
  auto_detected: boolean
  resolved: boolean
}
```

---

## 4. Data Flow tổng hợp — theo từng tính năng chính

### 4.1. Daily Astro (F1.2) — batch job hàng đêm

```
[Cron job 2:00 sáng]
        │
        ▼
Astro Engine: computeTransitSnapshot(today) 
  → 1 lần DUY NHẤT cho toàn hệ thống (không lặp theo user)
        │
        ▼
Với mỗi user active (đã có NatalChart):
  Astro Engine: computeUserTransitImpact(user.natalChart, todaySnapshot)
        │
        ▼
Content Generation: check combination_key
  → Cache hit (đa số trường hợp, vì Sun sign chỉ có 12 giá trị)
  → Cache miss → gọi LLM → lưu cache
        │
        ▼
Lưu vào UserDailyView (chờ sẵn) — user mở app vào sáng thấy ngay, không phải chờ tính toán
        │
        ▼
[6:00 sáng] Push notification: "Daily Astro hôm nay đã sẵn sàng"
```

### 4.2. Lá Ghép (F3.2) — real-time, có 2 bước tách thời gian (A tạo, B mở sau)

```
[A nhập ngày sinh B] 
        │
        ▼
API: POST /la-ghep { type, targetBirthDate, initiatorUserId }
        │
        ▼
Astro Engine: computeNatalChart(targetBirthDate, null, null)
  → chỉ có Sun/Venus/Mars (chưa đủ giờ/nơi sinh)
        │
        ▼
Astro Engine: computeSynastry(A.fullChart, B.partialChart)
  → SynastryResult với dataCompletenessB = "sun_only"
        │
        ▼
Content Generation: gọi LLM live (Lá Ghép luôn unique, không cache chung)
  → sinh "Vibe chính" (dùng được dù B chưa đủ data)
  → "Điểm hút" / "Điểm cần chú ý" → CHƯA sinh, vì cần aspect Venus/Mars chính xác hơn
        │
        ▼
Lưu LaGhep { status: 'partial' } + LaGhepResult { preview_unlock_percent: 35 }
        │
        ▼
Trả về A: preview với phần bị blur
        │
        ▼
[A gửi link cho B] ──── (có thể cách vài giờ/ngày) ────►
        │
        ▼
[B mở link, nhập birthTime + birthPlace]
        │
        ▼
API: PATCH /la-ghep/{id}/complete { birthTime, birthPlace }
        │
        ▼
Astro Engine: computeNatalChart(B.birthDate, birthTime, birthPlace)
  → full chart cho B
        │
        ▼
Astro Engine: computeSynastry(A.fullChart, B.fullChart)  
  → SynastryResult đầy đủ, có House-based aspects
        │
        ▼
Content Generation: gọi LLM live → sinh đầy đủ 3 phần + chọn lá tarot đại diện
        │
        ▼
Update LaGhep { status: 'completed' }, LaGhepResult { preview_unlock_percent: 100 }
        │
        ▼
Notification: push cho CẢ A và B đồng thời ("Kết quả đầy đủ đã sẵn sàng")
```

### 4.3. Vòng Lá Matching (F4.1) — batch job tuần, tải tính toán lớn nhất hệ thống

```
[Cron job 19:30 thứ 7, 30 phút trước khi mở Vòng Lá]
        │
        ▼
Lấy danh sách MatchingPoolMember active trong region đó (vd: 5.000 user/pool)
        │
        ▼
⚠️ ĐIỂM NGHẼN TIỀM NĂNG: tính Synastry cho MỌI CẶP trong pool
  = N×(N-1)/2 lần gọi computeSynastry
  Với N=5.000 → ~12.5 triệu cặp → KHÔNG khả thi tính hết
        │
        ▼
[Tối ưu bắt buộc — xem 4.4 bên dưới]
        │
        ▼
Sau khi có candidate set K cho mỗi user (K~20-30, đã lọc sơ bộ):
  Astro Engine: computeSynastry() đầy đủ chỉ cho các cặp đã lọc
        │
        ▼
Map evidence vào 6 relationship dimensions và các energy slot đủ điều kiện
        │
        ▼
Slate optimizer chọn tối đa 5 candidate khác nhau, tối ưu diversity + exposure fairness
(KHÔNG xếp top-5 theo một compatibility score)
        │
        ▼
Content Generation: sinh card_label cho mỗi cặp dựa trên aspect nổi bật
  (cache theo aspect pattern — nhiều cặp có pattern aspect giống nhau
   dù là người khác nhau, vẫn dùng được cache ở mức "loại aspect")
        │
        ▼
[20:00] Push notification mở Vòng Lá cho toàn bộ pool
```

### 4.4. Tối ưu bắt buộc cho Matching Engine (kỹ thuật quan trọng, cần review kỹ trước v0.4)

Tính Synastry đầy đủ cho mọi cặp trong pool lớn là **không khả thi về mặt tính toán**. Cần 2 lớp lọc trước khi gọi `computeSynastry()` đầy đủ. Không dùng bảng “cung nào hợp cung nào” vì lớp lọc đó loại người bằng một giả thuyết chiêm tinh phẳng trước khi engine đầy đủ được chạy:

```
Lớp lọc 1 — Lọc cứng (rẻ, làm bằng SQL query thường, không cần Astro Engine):
  - Cùng region
  - Cùng/giao nhau intent
  - Trong khoảng tuổi mong muốn
  → Giảm pool từ "toàn bộ user" xuống "vài trăm candidate/user"

Lớp lọc 2 — Candidate sampling vận hành (rẻ, không dùng astrology verdict):
  - reciprocal preference eligibility, active/verified state, block/report re-check
  - exposure fairness và deterministic weekly rotation; không dùng popularity score
  - `weekly_intent` chỉ điều chỉnh relevance mềm, không nới preference cứng
  → Giảm từ "vài trăm candidate" xuống set K~20-30 có thể kiểm toán

Lớp lọc 3 — Synastry đầy đủ (đắt, chỉ chạy cho candidate đã qua lọc 1+2):
  - computeSynastry() đầy đủ, có House overlay khi đủ dữ liệu, exact orb + provenance
  - map dimensions → eligible energy slots; chọn slate 5 có diversity và fairness
  - không tạo total score; không dùng Composite/Davison/D9 để loại candidate
  → Tạo tối đa 5 VongLaCard ổn định cho cả phiên
```

**Ước tính tải:** với pool 5.000 user/region, sau lọc 1+2 còn ~20-30 candidate/user → computeSynastry đầy đủ chạy ~150.000 lần thay vì 12.5 triệu — khả thi để chạy trong cửa sổ 30 phút.

---

## 5. API Contract — các endpoint chính

> Danh sách rút gọn các endpoint cốt lõi để dev FE/BE thống nhất sớm. Chưa bao gồm toàn bộ CRUD phụ trợ (profile settings, notification preferences...).

### 5.1. Identity & Profile Module

```
POST   /auth/signup                      { phoneOrEmail }
POST   /auth/verify-otp                  { otp, sessionToken }
POST   /users/me/birth-data              { birthDate, birthTime?, birthPlace? }
GET    /users/me/profile-level           → { level: 1-5, missingFor: {...} }
POST   /users/me/consent                 { consentVersion }
DELETE /users/me/data                    { scope: 'full_account'|'birth_data'|... }
```

### 5.2. Astro Engine Module (internal — KHÔNG expose trực tiếp ra client, chỉ gọi qua module khác)

```
[internal] computeNatalChart(birthDate, birthTime?, birthPlace?) → NatalChartResult
[internal] computeUserTransitImpact(userId) → UserTransitImpactResult
[internal] computeSynastry(userIdA, userIdB) → SynastryResult
[internal] computeComposite(userIdA, userIdB) → CompositeChartResult
```

### 5.3. Content Module (expose ra client qua các module nghiệp vụ, không gọi trực tiếp)

```
GET    /daily-astro/today                → { content, mood_options }
POST   /daily-astro/today/mood           { mood }
GET    /transit-insights                 → array<UserTransitImpactResult + content>
POST   /transit-insights/{id}/forward    { targetContact }
```

### 5.4. Lá Ghép Module

```
POST   /la-ghep                          { type, targetBirthDate, hideInitiatorName? }
        → { laGhepId, shareLink, previewResult }
GET    /la-ghep/{id}                     → trạng thái hiện tại + preview/full result
PATCH  /la-ghep/{shareLinkToken}/complete { birthTime?, birthPlace? }
        → trigger full Synastry + LLM generation
```

### 5.5. Vòng Lá Module

```
GET    /vong-la/status                   → { isOpen, opensAt, closesAt }
GET    /vong-la/my-cards                 → array<5 VongLaCard>   (chỉ trả khi isOpen=true)
POST   /vong-la/cards/{id}/open-request  → tạo VongLaRequest
GET    /vong-la/mutual-matches           → array<MutualMatch>
WS     /chat/{threadId}                  → WebSocket connection cho chat real-time
GET    /vong-la/recap                    → VongLaRecap (chủ nhật)
```

### 5.6. Marketplace Module (v0.5+)

```
POST   /rooms                            { themeId, maxParticipants, ticketPrice? }  [Lá Dẫn only]
GET    /rooms/{id}/ai-suggestions        → array<SynastryResult ranked>  [Lá Dẫn only]
POST   /rooms/{id}/intros                { userAId, userBId }  [Lá Dẫn only]
POST   /bookings                         { laDanUserId, slotId, readingType }
GET    /la-dan/{id}/payout-status        → array<PayoutCalculation>
```

---

## 6. Hạ tầng & Vận hành (Infrastructure)

### 6.1. Data store

| Store | Dùng cho | Lý do |
|---|---|---|
| PostgreSQL | Toàn bộ entity nghiệp vụ (User, NatalChart, LaGhep, VongLaCard, GeneratedContent...) | Cần transaction, relation rõ ràng (FK), phù hợp modular monolith |
| Redis | Cache layer cho GeneratedContent (lớp nhanh trước Postgres), session, rate limiting, Vòng Lá real-time state | Đọc cực nhanh, TTL tự nhiên cho cache content theo combination |
| Object Storage (S3-compatible) | Ảnh xác minh, Lá Khai Sinh Card image, Share Card image | Tách khỏi DB chính, CDN-friendly cho ảnh share ra ngoài |
| Message Queue (vd Redis Streams/SQS-equivalent) | Batch job Daily Astro, LLM generation queue (tránh gọi LLM đồng bộ chặn request user) | Đảm bảo gọi LLM không làm chậm response time của user-facing API |

### 6.2. Luồng hàng đợi cho LLM call (quan trọng — không gọi LLM đồng bộ trong request path)

```
User action cần content mới (vd: tạo Lá Ghép)
        │
        ▼
API trả response NGAY với trạng thái "đang xử lý" (status: pending)
        │
        ▼
Đẩy job vào Queue: { type: 'generate_la_ghep_content', laGhepId }
        │
        ▼
Worker process (riêng, scale độc lập) pull job từ Queue
        │
        ▼
Worker gọi Astro Engine (nếu chưa tính) → gọi LLM → lưu kết quả
        │
        ▼
Worker publish event "content_ready" → Notification module bắn push cho user
        │
        ▼
Client poll hoặc nhận WebSocket event để cập nhật UI khi content sẵn sàng
```

**Lý do bắt buộc kiến trúc này:** gọi LLM trực tiếp trong request-response cycle của API sẽ làm timeout khi LLM chậm (thường 2-8 giây), và không scale được khi nhiều user request cùng lúc (vd: Vòng Lá mở 20:00 thứ 7, hàng nghìn user cùng cần content trong vài phút).

### 6.3. Batch jobs bắt buộc (Cron schedule)

| Job | Lịch chạy | Module | Mô tả |
|---|---|---|---|
| Daily Transit Snapshot | 2:00 sáng hàng ngày | Astro Engine | Tính 1 lần `TransitSnapshotResult` cho toàn hệ thống |
| Daily Astro Generation | 2:15 sáng (sau snapshot) | Content Generation | Generate/cache content cho mọi Sun/Moon sign combination active |
| Vòng La Pre-matching | 19:30 thứ 7 | Matching | Pipeline lọc 3 lớp (4.4) → tạo VongLaCard |
| Vòng La Recap | 10:00 chủ nhật | Content Generation | Tổng hợp + sinh Recap Story |
| Transit Event Detection | Hàng ngày | Astro Engine | Quét xem có `TransitEvent` mới bắt đầu/kết thúc không (vd Saturn đổi house) → trigger pre-warm cache mới |
| Payout Calculation | Hàng ngày | Marketplace | Tính `PayoutCalculation`, áp dụng hold period (PRD F5.3) |
| Season Recap Generation | Cuối mỗi mùa (6 tuần) | Content Generation | Generate Season Recap cho toàn bộ user active |

### 6.4. Khả năng mở rộng (Scalability notes)

- **Astro Engine** là module thuần CPU-bound (toán học), không gọi network ngoài (trừ Geocoding khi cần) — dễ scale ngang bằng cách thêm worker instance
- **Content Generation** bị giới hạn bởi rate limit của LLM provider — chiến lược cache-first (Phần 3.2) là bắt buộc, không phải tối ưu hóa tùy chọn
- **Matching Module** là nơi có rủi ro tải đột biến lớn nhất (toàn bộ pool cùng tính 1 lúc mỗi tối thứ 7) — cần queue + lọc 3 lớp (4.4) để tránh nghẽn
- Khi tách microservice trong tương lai: Astro Engine nên tách đầu tiên (ranh giới rõ nhất, ít phụ thuộc nhất), Content Generation tách thứ hai (đã có hàng đợi sẵn từ đầu)

---

## 7. Bảo mật & quyền truy cập dữ liệu (bổ sung kỹ thuật cho PRD Phần 7.2)

| Loại dữ liệu | Mã hóa | Ai truy cập được |
|---|---|---|
| birthDate, birthTime, birthPlace | Encrypt at rest (cột riêng, key quản lý tập trung) | Chỉ Astro Engine module qua internal call; không expose API trả thẳng dữ liệu thô này ra client sau khi đã tính chart |
| NatalChart/reading suy ra (sign/house/aspect/factor) | Encrypt at rest; đây vẫn là personal data và có thể giúp suy ngược dữ liệu sinh | Chỉ module/consumer được allowlist theo purpose; public/share dùng DTO đã redact |
| Ảnh xác minh | Object Storage riêng, access qua signed URL có TTL ngắn | Chỉ hệ thống kiểm duyệt, không public |
| GPS/live device location | Không thu hoặc lưu cho birth chart; matching chỉ dùng region user chọn | Theo yêu cầu Safety ở PRD Phần 4.3 |
| Tọa độ city-centroid của nơi sinh | Được lưu private/encrypted khi cần tái lập house calculation; không phải GPS hiện tại, không public/log/analytics | Astro Engine theo purpose consent; xóa cùng birth place |

---

## 8. Việc cần làm ngay để bắt đầu sprint (Technical kickoff checklist)

1. **Chốt ephemeris library/license** (PRD 7.4, đã nhấn mạnh là rủi ro cao nhất) — Astro Engine không thể bắt đầu code nếu chưa có cái này
2. **Dựng khung Modular Monolith** với 5 module boundary đã định nghĩa ở Phần 1.2 — kể cả khi code bên trong còn rỗng, interface phải tách đúng từ đầu để tránh nợ kỹ thuật phải refactor giữa chừng
3. **Build Compute Pipeline (Phần 2.3) trước Content Generation** — không có dữ liệu chart đúng thì không thể test prompt LLM có đúng không
4. **Thiết lập Queue + Worker cho LLM calls** (Phần 6.2) trước khi viết bất kỳ tính năng nào gọi LLM — tránh viết code đồng bộ rồi phải refactor sang async sau
5. **Build deterministic candidate sampler + slate-diversity fixtures** (Phần 4.4, Lớp lọc 2–3) sớm — hard filters và exposure fairness phải kiểm thử độc lập trước khi nối Astro Engine

---

*Tài liệu SRS này là tầng triển khai kỹ thuật của `la-lanh-prd.md`. Mọi entity/feature nhắc tới ở đây tham chiếu trực tiếp định nghĩa trong PRD — không định nghĩa lại business logic, chỉ bổ sung kiến trúc, data flow, và contract giữa các module.*
