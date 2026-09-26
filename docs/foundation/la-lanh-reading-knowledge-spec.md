# Lá Lành Reading Knowledge Engine — đặc tả v4

Trạng thái: implemented foundation, cần user benchmark trước public release  
Ngày rà soát: 2026-09-23  
Phạm vi: Daily Note và Reading Detail; Western trước, Jyotish fail-closed

## 1. Value proposition

USP của Lá Lành không phải “một horoscope mỗi ngày”. Sản phẩm phải làm được điều các app horoscope đại trà thường không làm rõ:

> Biến lá số cá nhân thật + bầu trời hiện tại thành một tình huống đời thường, giải thích cơ chế bên dưới, cho một thử nghiệm nhỏ, và cho phép người dùng xem căn cứ đã tạo nên bản đọc.

Một note đạt chuẩn phải trả lời năm câu:

1. Có điều gì đáng chú ý với tôi?
2. Vì sao hai nhu cầu/pattern này cùng xuất hiện?
3. Nó thường lộ ra ở vùng đời sống nào?
4. Tôi có thể thử gì mà không giao quyền quyết định cho app?
5. App dựa vào dữ kiện chart nào để nói vậy?

“Tín hiệu vũ trụ”, lời tiên tri hoặc một placement đứng riêng không phải value.

## 2. Kiến trúc bắt buộc

```text
Swiss Ephemeris facts
  → normalized natal/transit facts
  → factor planner (allowlist + salience + tradition)
  → versioned knowledge atoms
  → synthesis frame
  → evidence / anti-influence / editorial / privacy gates
  → immutable revision
  → user explicitly activates an available update
```

| Lớp | Trách nhiệm | Không được làm |
|---|---|---|
| Calculation | Tính longitude, sign, house, angle, aspect, orb, phase, nakshatra/drishti theo config | Viết lời khuyên |
| Factor planner | Chọn factor đủ bằng chứng, ưu tiên theo purpose, giữ 70% natal/30% transit khi có transit | Trộn Western/Jyotish |
| Knowledge | Cung cấp atom hành tinh/cung/nhà/góc/độ/orb/transit đã version | Đọc raw DOB/tọa độ/ID |
| Synthesis | Ghép atom thành một tension hoặc pattern dễ hiểu | Bịa thêm chart fact |
| Gates | Chặn claim sai, xúi giục, văn sáo và PII | Sửa âm thầm factual claim |
| Projection | Giữ bản đang đọc ổn định; đưa bản mới thành quà mở khóa | Hot-swap giữa lúc user đọc |

## 3. Knowledge matrices v4

Runtime catalog: `western-interpretation-matrix-v4`. Phương pháp nguồn và ranh giới bản quyền nằm tại `docs/foundation/la-lanh-interpretation-corpus-methodology.md`.

### 3.1 Hành tinh / điểm

Mỗi body có ba atom: `drive` (nhu cầu/chức năng), `stress` (phản xạ dễ lộ khi quá tải), và `action` (thử nghiệm nhỏ, có thể đảo ngược).

Độ phủ launch: Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto, Chiron, True/Mean/South Node.

### 3.2 Cung

Mỗi cung có `style`, `stress`, ba hook đời thường và ba practice. Coverage test bắt buộc đủ 12 cung và mỗi cung phải sinh được candidate qua bốn content gate.

### 3.3 Nhà

Mỗi nhà có `arena` và `manifestation`. Nhà chỉ được dùng khi giờ sinh chính xác và house calculation hợp lệ. Nhà trả lời “pattern lộ ra ở đâu”, không phải nhãn tính cách.

### 3.4 Góc natal

| Aspect | Vai trò diễn giải | Guardrail |
|---|---|---|
| Conjunction | Hai chức năng bật cùng lúc/khuếch đại | Không mặc định tốt/xấu |
| Opposition | Hai đầu cần thương lượng | Không đổ một đầu lên người khác |
| Square | Ma sát khó bỏ qua | Không gọi là tai họa |
| Trine | Dòng chảy thuận tay | Luôn nêu blind spot của quán tính |
| Sextile | Khả năng hợp tác khi chủ động | Không hứa cơ hội tự tới |
| Quincunx | Nhu cầu phải điều chỉnh liên tục | Không kết luận bất tương thích |

Một aspect hero phải giữ hai placement con trong plan để renderer giải thích được “hai phần nào” đang tương tác.

### 3.5 Độ và orb

- `degree_in_sign` được giữ trong evidence nhưng không tự tạo kết luận tâm lý theo dải đầu/giữa/cuối cung.
- Degree chỉ được đưa lại vào prose khi có corpus chuyên biệt, expert review và benchmark chứng minh nó làm bản đọc hữu ích hơn.
- Orb `≤1°`: rất sát; `≤3°`: đáng theo dõi; lớn hơn: nét phụ.
- Aspect salience vẫn dùng orb policy của engine. Prose chỉ nói mức ưu tiên bằng lời đời thường, không dùng shorthand như “sắc độ nền”.
- Không hỗ trợ critical degree, decan, bound/term, Sabian symbols ở v1. Muốn mở phải có corpus/version/source/test riêng.

### 3.6 Transit tới natal

Transit chỉ được dùng khi natal chart có giờ chính xác, config/tradition trùng natal, contact vượt salience threshold, và timing chỉ nói `approaching`, `exact`, `separating`. Transit là lớp 30%: giải thích vì sao pattern natal dễ thấy hơn lúc này; không được dự báo event hoặc lấn át bản đọc natal 70%.

### 3.7 Lăng kính và cấu trúc mở rộng

- Planet có thêm năm perspective: `protection`, `relationships`, `work`, `regulation`, `growth_question`.
- 12 cung map sang 4 element và 3 modality; element/modality là nhịp vận hành, không phải nhãn tốt/xấu.
- 12 nhà map thêm `angular/succedent/cadent` để phân biệt cách pattern được đưa ra hành động, giữ ổn định hoặc phân phối/diễn giải.
- Motion direct/retrograde ở evidence, không tự sinh kết luận tâm lý. Applying/separating chỉ thêm nuance khi giúp câu rõ hơn; không được viết thành yếu, xấu hoặc định mệnh.
- Full chart có sáu lens: inner pattern, relationships, work, regulation, communication và growth. Một note chỉ chọn một lens để tránh nhét cả chart vào một đoạn.

## 4. Synthesis grammar

### Date-only Vibe

`Sun sign + local_date editorial seed → hook + style + stress + practice`.

### Daily novelty contract

“Note mới” phải khác ở cấp ý, không phải chỉ đổi vài từ. Daily renderer dùng lịch biên tập mixed-radix gồm `hero factor × interpretive lens × editorial mode × micro-action × reflection cue`; với date-only, tổ hợp tương đương là `hook × practice × editorial mode × closing × reflection cue`. Cùng một ngày địa phương luôn replay đúng một bản, còn 365 ngày liên tiếp phải có 365 tổ hợp prose khác nhau và đều qua bốn quality gates.

Năm editorial mode là: cơ chế đang chạy, điểm dễ kẹt, nguồn lực có thể dùng, phân biệt nguồn lực với phản xạ quá tay, và một thử nghiệm nhỏ. Sáu lens vẫn là inner pattern, relationships, work, regulation, communication và growth. Reflection cue đổi thứ cần quan sát trong đời thực. Transit và hero-factor rotation tạo thêm biến thiên theo bầu trời và chart nhưng không được dùng để thay thế cam kết chống lặp của lịch biên tập.

Chống lặp là stateless: server suy ra một semantic signature từ ngày địa phương và version của lịch; không tạo bảng lịch sử, không lưu nguyên văn note, birth input hay background mới chỉ để so trùng. Khi đổi catalog phải tăng knowledge/content version và chạy lại golden 90-day suite.

- Cùng ngày replay y hệt.
- Ngày kế tiếp xoay hook và practice theo chu kỳ đảm bảo, không random runtime.
- Luôn nói rõ đây chỉ là một yếu tố; không được nhắc Moon, nhà, Cung Mọc hay personalized transit.

### Full chart

Thứ tự ưu tiên: aspect/drishti đủ mạnh có hai child factors; hai placement liên quan; một nhà làm context nếu hợp lệ; degree giữ trong evidence; tối đa một transit nổi bật làm current activation.

| Section | Công thức |
|---|---|
| Hook | Hai nhu cầu thật đang kéo/cộng hưởng |
| Thesis | Gọi đúng hai hành tinh → nói nhu cầu riêng → loại góc → mức ưu tiên từ orb |
| Manifestation | Nhà hoặc background lens → tình huống đời thường |
| Micro-action | Một thử nghiệm nhỏ, không chỉ thị quyết định |
| Current activation | Transit × natal + aspect + phase, nếu đủ điều kiện |
| Evidence | Claim template từ factor refs trong plan |

V4 không dùng mọi dimension trong cùng một note. Lens quyết định dimension nào được foreground; `knowledge_refs` ghi lại methodology, lens và atom đã dùng. Background opt-in thắng lịch xoay; nếu không có background, Daily Note xoay lens theo ngày địa phương nhưng giữ nguyên chart facts.

## 5. Chống rập khuôn mà vẫn kiểm soát được

- Variability đến từ factor selection thật, house/context, date seed và tập atom đã duyệt; không đến từ random prose vô hạn.
- Không thay synonym để giả mới nếu insight không đổi.
- Mỗi ngày ưu tiên một domain khác khi chart có đủ candidate: core, emotions, mind, relating, drive.
- Background của user là enum opt-in; chỉ thay ví dụ biểu hiện, không thay chart fact.
- Feedback “trúng / chưa trúng” trong tương lai chỉ điều chỉnh ranking sau consent; không huấn luyện từ free text trong MVP.

## 6. Tradition isolation

- Western: tropical zodiac, Western aspect catalog và house systems được cấu hình.
- Jyotish: sidereal zodiac + ayanamsa bắt buộc, whole-sign mặc định, nakshatra và graha drishti.
- Validator chặn Western aspect trong Jyotish plan và chặn nakshatra/drishti trong Western plan.
- `western-interpretation-matrix-v4` không được quảng bá là corpus Jyotish hoàn chỉnh. Generated Jyotish và diễn giải gochara/transit Jyotish giữ OFF cho tới khi có catalog riêng, chuyên gia review và golden corpus.

## 7. Quality gates

Candidate chỉ publish khi qua đủ evidence, anti-influence, editorial và privacy gates. Editorial gate chặn lặp section, văn sáo và “tín hiệu vũ trụ”. Privacy gate chặn DOB, giờ/nơi/tọa độ, email, token và UUID trong prose.

Editorial gate v3 còn chặn hai lỗi từng lọt qua QA:

- hai vế gần như trùng nhau trong cùng một section, kể cả khi chỉ đổi tiền tố “một bên/bên kia”;
- shorthand nội bộ không giải thích được điều gì cho người dùng, gồm “nhu cầu nào đang cầm lái” và “góc rộng: chỉ là sắc độ nền”.

Regression suite bắt buộc quét các tổ hợp cùng nguyên tố qua đủ 6 aspect và 3 dải orb. Label validation phải giữ dấu tiếng Việt để không nhầm “Hải Vương” với aspect “vuông”.

MVP chỉ gọi deterministic renderer. Free-form provider output chưa được bật trên product path; trước khi mở cần đổi response contract sang chọn `template_id`/`factor_ref` đóng thay vì trả câu chữ tùy ý, rồi bổ sung semantic-binding tests.

Test release tối thiểu:

- 12/12 cung, 12/12 nhà, tất cả body launch, 6 aspect, 3 transit phase;
- same-day deterministic, 365 ngày liên tiếp không trùng tổ hợp prose;
- golden chart Western/Jyotish không trộn thuật ngữ;
- candidate adversarial corpus;
- full update activation từ Home và Note detail;
- benchmark người dùng: ≥70% thấy chart-specific, “chung chung” <15%.

## 8. Provenance và versioning

Mỗi revision cần truy ngược được `engine/config_hash`, `rules_version`, `knowledge_version`, `renderer_version`, `content_version`, `gate_policy_version` và immutable evidence factor refs.

Thay matrix hoặc rule phải tạo plan/revision mới. Bản đang active không bị sửa; bản mới thành `available_update` để user chủ động mở.

## 9. Security và data privacy

- Knowledge catalog là static code, không chứa dữ liệu cá nhân.
- Raw birth input, chart snapshot và plan được xử lý server-side; client chỉ nhận projection/evidence tối thiểu.
- Không log raw birth data, tọa độ, plan factors, reading text, prompt hay identifier.
- Không lưu DOB trong localStorage/cache note/analytics.
- Không lưu lịch sử prose hoặc dữ liệu hành vi mới chỉ để chống lặp Daily Note; lịch biên tập được suy ra stateless từ ngày địa phương và version.
- External generation mặc định OFF. Cấu hình hệ thống chưa đủ để gửi dữ liệu: mỗi lần enqueue còn cần một purpose authorization riêng của người dùng; nếu thiếu, deterministic matrix tiếp tục chạy tại server và không gọi provider.
- Consent cho “tính và diễn giải chart cá nhân” bao phủ deterministic synthesis cùng purpose; mục đích mới như training, quảng cáo hoặc matching vẫn cần căn cứ/consent riêng.
- Disclaimer ngắn luôn cạnh nội dung: “Lá gợi một góc nhìn — quyền quyết định vẫn ở bạn.” Framework disclosure sâu nằm trong evidence accordion.

## 10. Sources and boundaries

Calculation reference:

- [Swiss Ephemeris documentation](https://www.astro.com/swisseph/swisseph.htm)
- [Swiss Ephemeris programmer interface](https://www.astro.com/swisseph/swephprg.htm?lang=n)

Interpretation structure reference:

- [Astrodienst introduction: planets, signs, houses and aspects](https://www.astro.com/astrology/in_intro_e.htm)
- [Astrodienst aspects reference](https://www.astro.com/astrowiki/en/Aspects)
- [Astrodienst transit reference](https://www.astro.com/astrowiki/en/Transit)
- [Robert Hand introduction to transits](https://www.astro.com/astrologie/in_hand2_introduction_e.htm)

Privacy/security release baseline:

- [Vietnam Law 91/2025/QH15](https://vanban.chinhphu.vn/?docid=214590&pageid=27160)
- [Vietnam Decree 13/2023/ND-CP](https://vanban.chinhphu.vn/?classid=1&docid=207759&pageid=27160)
- [OWASP MASVS](https://mas.owasp.org/MASVS/)
- [OWASP MASVS Privacy](https://mas.owasp.org/MASVS/12-MASVS-PRIVACY/)
- [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)

Các nguồn trên hỗ trợ mô hình calculation, khái niệm và governance. Copy tiếng Việt trong matrix là nội dung sản phẩm tự biên tập, không sao chép diễn giải có bản quyền và không được trình bày như bằng chứng khoa học.

## 11. Open limits

- Chưa có expert-approved Jyotish interpretation catalog.
- Chưa có user benchmark 20 người cho specificity/usefulness.
- Chưa có production KMS, native device evidence và distributed edge controls.
- Chưa có personalized adaptation từ feedback “trúng/chưa trúng”.
- Swiss Ephemeris licensing vẫn là release gate riêng.
