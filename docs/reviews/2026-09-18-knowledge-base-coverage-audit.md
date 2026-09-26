# Audit knowledge base và relationship engine

Ngày: 2026-09-18  
Kết luận: nền tính toán có chiều sâu tốt cho natal/transit và relationship facts, nhưng chưa đủ để gọi là corpus public hoàn chỉnh nếu thiếu expert review, provenance vận hành và các lớp timing nâng cao.

## 1. Những gì đang có thật

### Fact engine

- Western Tropical natal: hành tinh, góc, nhà, aspect, retrograde, applying/separating.
- Daily transit và transit-to-natal với orb/phase versioned.
- Jyotish Sidereal: D1, Lahiri preset, Rahu/Ketu, 27 nakshatra/pada và classical graha drishti.
- Relationship: Western Synastry v2, house overlay hai chiều khi đủ dữ liệu, midpoint Composite, uncorrected Davison và factual D9/Navāṁśa.
- Matching projection: sáu dimension; không dùng scalar compatibility score ở UI/ranker.

### Daily reading corpus

- 10+ planet/function meanings, 12 sign meanings, 12 house meanings và aspect meanings.
- Sáu interpretive lens × năm editorial mode × action/reflection slots.
- Evidence, anti-influence, editorial và privacy gates.
- Daily seed deterministic nhưng có semantic rotation; không chỉ thay từ đồng nghĩa.

### Relationship corpus sau audit này

- 10 nguồn được đăng ký bằng official URL và class riêng cho psychology/dating/communication/astrology.
- 23/23 concept id đã có executable editorial rule; trước audit chỉ 5/23.
- Mỗi rule có source id, relationship dimension, prompt cụ thể và safety boundary.
- Bốn voice profile do người dùng chọn: `straight_warm`, `gentle_specific`, `playful_grounded`, `deep_dive`.
- `build_editorial_plan` chọn tối đa ba prompt khác dimension, deterministic, evidence-bound và luôn có disclaimer; không render verdict.

## 2. Coverage matrix

| Lớp | Coverage | Đánh giá |
|---|---|---|
| Natal planets/signs/houses/aspects | Có | Tốt cho Western launch |
| Degree/orb/applying/separating/motion | Có phần lớn | Tốt; stationary cần policy/body threshold rõ hơn |
| Transit-to-natal | Có | Tốt cho Daily/current sky |
| Transit event boundaries/duration | Spec có, runtime chưa đầy đủ | Cần trước timeline dài hạn |
| Synastry contacts/overlays | Có | Đủ làm fact layer US-12/15 |
| Composite points/aspects | Có | Chỉ dùng sau mutual; chưa có houses chuẩn |
| Davison | Có bản uncorrected, gắn caveat | Không được quảng bá parity với Astro.com |
| Jyotish D1/nakshatra/drishti | Có fact layer | Content public cần expert sign-off |
| D9 | Có fact, interpretation disabled | Fail-closed đúng |
| Vimshottari dasha/yoga/Ashtakoota | Chưa runtime hoặc intentionally gated | Không launch claim |
| Progressions/solar arc/solar return/lunar return | Chưa có | Roadmap, không blocker core Daily |
| Eclipses/lunations/event solver | Chưa product-wired | Nên thêm cho seasonal/current-sky depth |
| Relationship psychology | 23 rule có provenance | Đủ để compose prompt, chưa phải clinical advice |
| User voice preference | 4 explicit profiles | Tốt; cần UI/profile persistence để dùng thật |
| Vietnamese editorial QA | Gate tự động có | Cần human corpus review và near-neighbor benchmark |

## 3. Thiếu gì trước khi knowledge đi vào US-12–18

### P0 — Chặn public output

1. Renderer relationship phải nhận `RelationshipEditorialPlan`, cite evidence/concept trong metadata và qua content gate giống Daily Note.
2. Mỗi output cần lưu `knowledge_version`, chart/config version, source concept ids, evidence ids và voice choice.
3. Golden fixtures cần phủ missing-time degradation, orb boundary, 0° composite midpoint, two-way overlay và mixed-config rejection.
4. Human/domain-expert review cho Jyotish; D9/Vimshottari/Ashtakoota tiếp tục off cho generated copy.
5. Không được nói “học từ 10 sách” như một claim về quyền sử dụng toàn văn. Registry chỉ dùng khái niệm paraphrase, không lưu excerpt.

### P1 — Tăng chiều sâu có ích

- Thêm event solver cho ingress, exact transit, station và multi-pass để giải thích *khi nào nhịp đổi*, không dự đoán sự kiện.
- Thêm lunation/eclipses như collective context, không dùng làm lời phán cá nhân.
- Thêm relationship timing sau mutual bằng transit-to-Composite/Davison, luôn opt-in và không dùng pre-match.
- Thêm aspect patterns/chart ruler/dispositor/dignity chỉ sau khi method + fixtures được version hóa.
- Thêm near-neighbor benchmark: hai chart gần nhau phải có đủ điểm khác; một chart qua nhiều ngày không lặp thesis/action quá sớm.

### Không nên thêm chỉ để “nhiều hơn”

- Compatibility percentage, soulmate/karmic verdict, marriage prediction.
- Attachment diagnosis hoặc suy trauma/intent/sexual willingness từ chart.
- Ashtakoota 36 điểm dùng để rank/reject candidate.
- Composite/Davison/D9 trước mutual hoặc khi thiếu consent/precision.

## 4. Nguồn kỹ thuật và policy đã đối chiếu

- Swiss Ephemeris official documentation cho planet, sidereal mode, houses và house-position APIs.
- Astrodienst mô tả Synastry, midpoint Composite và khác biệt với Davison; Composite là construction, không phải real sky moment.
- Official publisher/author pages của 10 nguồn trong registry; không sao chép nội dung sách.
- Gottman official material cho repair/turning toward được dùng như conversation concepts, không biến thành hidden score.

## 5. Gate kết luận

Knowledge base hiện **đủ để bắt đầu xây renderer cho Lá Ghép/Lá Nối và icebreaker**, chưa đủ để tự động public mọi technique đang nêu trong spec. Các lớp chưa đạt expert/golden gate phải bị tắt bằng capability flag, không fallback sang lời văn chung chung.
