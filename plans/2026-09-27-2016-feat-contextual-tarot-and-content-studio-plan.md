---
artifact_contract: ce-unified-plan/v1
product_contract_source: ce-brainstorm
execution: code
created_at: 2026-09-27T20:16:39+07:00
topic: contextual-tarot-and-content-studio
---

# Contextual Tarot and Content Studio

## Goal Capsule

- **Objective:** Người dùng có thể đi từ một Daily Note hoặc Radar sang một phiên Tarot có câu hỏi rõ, hiểu kết quả bằng ngôn ngữ đời thường, làm rõ đúng chỗ còn mơ hồ và lưu hoặc chia sẻ an toàn; đội nội dung có thể mở rộng kho diễn giải mà không làm giảm chất lượng.
- **Means:** Xây Tarot như một reflection domain đứng cạnh astrology, dùng Content Studio có cấu trúc để biên tập và phát hành knowledge.
- **Product authority:** Product owner quyết định positioning và scope; chuyên gia Tarot/astrology duyệt nội dung; safety/privacy reviewer có quyền chặn phát hành.
- **Open blockers:** Không có blocker để lập kế hoạch cho self-draw MVP. Deck artwork rights, reversal policy và reader marketplace được xử lý như quyết định riêng trước khi các phần đó đi vào production.

---

## Product Contract

### Summary

Lá Lành sẽ thêm `Lá Hỏi`: một lớp Tarot theo câu hỏi, mở từ Daily Note, Radar hoặc Khám phá. Release đầu gồm self-draw, một lần làm rõ có giới hạn, save/share riêng tư và Content Studio đủ để quản trị Tarot knowledge cùng các corpus hiện có. Reader marketplace là pha sau, không nằm trong self-draw MVP.

### Problem Frame

Daily Note và Radar hiện có thể mở ra đúng chủ đề nhưng chưa luôn trả lời phần người dùng đang tò mò nhất. Thêm nhiều đoạn diễn giải vào astrology làm report dài hơn mà không chắc hữu ích hơn. Tarot phù hợp để mở một góc reflection mới, nhưng sẽ gây hại nếu được trình bày như bằng chứng chart, cho phép rút đến khi vừa ý hoặc kích hoạt mua hàng lúc người dùng đang lo lắng.

Kho content hiện là catalog tĩnh trong code. Nó đã có version, gate và audit tốt, nhưng chưa có nơi để editor tạo, review, preview, phát hành và rollback nội dung có cấu trúc. Mở Tarot trước khi giải quyết khoảng trống này sẽ nhân thêm lỗi semantic và tăng chi phí QA.

### Key Decisions

- **Tarot là reflection sibling của astrology, không phải lớp chứng minh astrology.** (session-settled: user-directed — chosen over một tab Tarot tách rời: user muốn reading dựa trên question, context và nội dung lá, đồng thời dùng để làm rõ insight hiện có.) Governs R9, R13, R14.
- **Hai trục được tách riêng: ai bốc và bốc để làm gì.** Governs R7, R11.
- **Content Studio quản trị semantic blocks và release, không phải trang rich-text tổng quát.** Governs R1–R6.
- **Self-draw đi trước, reader live đi sau.** Reader operations, payment và moderation có carrying cost riêng; marketplace không được làm self-draw MVP chậm hoặc kém an toàn.
- **Tối ưu cho độ rõ và khả năng đối chiếu, không tối ưu số lần bốc.** Governs R11, R15, R17, R20.

### Actors

- **Người dùng:** đặt câu hỏi, chọn context, tự bốc, yêu cầu làm rõ, lưu và chia sẻ.
- **Content editor:** tạo semantic block, question prompt, spread và interpretation rule.
- **Chuyên gia duyệt:** xác nhận ý nghĩa Tarot/astrology, tradition và giới hạn sử dụng.
- **Safety/privacy reviewer:** duyệt influence risk, dữ liệu, retention và public projection.
- **Publisher:** tạo release bất biến, rollout, theo dõi và rollback.
- **Tarot reader:** actor của pha marketplace sau; không tham gia self-draw MVP.

### Requirements

**Content Studio và governance**

- R1. Content Studio phải quản lý knowledge theo block có type, gồm premise, interpretation, life scene, reflection question, micro-action, disclaimer và prohibited use.
- R2. Mỗi block phải có author, tradition, nguồn hoặc editorial rationale, quyền sử dụng, locale, precision eligibility, context compatibility và version.
- R3. Workflow phát hành phải đi qua `draft → specialist review → safety/privacy review → gate pass → approved release → retired`, với quyền riêng cho từng vai trò.
- R4. Editor phải preview một thay đổi trên fixture Daily, Radar và Tarot đại diện, xem gate failure, semantic diff và bề mặt bị ảnh hưởng trước khi publish.
- R5. Mỗi release phải bất biến, có staged activation và rollback về một release đã duyệt; nội dung đang được người dùng đọc không bị sửa ngầm.
- R6. CMS không được chứa raw birth data, câu hỏi riêng, reading history hoặc support case; dữ liệu vận hành người dùng thuộc console riêng có phân quyền chặt hơn.

**Lá Hỏi và self-draw**

- R7. Phiên Tarot phải lưu riêng hai chiều: `draw actor` là self hoặc reader, còn `draw purpose` là first reading hoặc clarifier.
- R8. Người dùng phải chọn hoặc xác nhận một câu hỏi và context trước khi bốc; app được gợi ý ba câu phù hợp với bề mặt vừa đọc nhưng không tự suy ra ý định.
- R9. Tarot draw phải thực sự ngẫu nhiên, được ghi nhận một lần cùng deck/spread version và luôn có nhãn tách khỏi astrology evidence.
- R10. MVP phải có một spread một lá và một spread ba lá với position thiên về reflection; không dùng cấu trúc dự đoán chắc chắn về quá khứ–hiện tại–tương lai.
- R11. Reading đầu phải giải thích lần lượt ý nghĩa lá trong position, liên hệ có điều kiện với câu hỏi và một điều có thể quan sát ngoài đời.
- R12. Giọng đọc phải do người dùng chọn từ voice profile hữu hạn; hệ thống không được suy voice từ chart, mood, câu hỏi hoặc hành vi.
- R13. Daily Note và Radar giữ nguyên fact, thesis và evidence; Tarot chỉ được tham chiếu đoạn người dùng chọn làm context và không được thay đổi chart result hoặc indicator.
- R14. User phải có thể bỏ qua phần context prefill, xóa phiên, chọn không lưu và dùng self-draw trước khi bị yêu cầu đăng nhập; auth xuất hiện khi lưu đồng bộ hoặc chia sẻ bền vững.

**Làm rõ, đối chiếu và share**

- R15. `Rút lá làm rõ` chỉ xuất hiện sau reading đầu, yêu cầu user chọn câu hoặc position chưa rõ và cho phép tối đa một clarifier trong session.
- R16. Clarifier phải nằm cạnh phần gốc, mang nhãn `góc bổ sung` và không được xóa, phủ định hoặc thay thế reading đầu.
- R17. Khi người dùng muốn bốc lại cùng một câu, app phải ưu tiên mở reading đã lưu, gợi ý đổi câu hỏi cụ thể hơn hoặc tạm dừng; không có streak, pay-per-card hay “cảnh báo bí mật” khóa sau paywall.
- R18. User có thể giữ một micro-action và đóng vòng bằng `Hữu ích`, `Không khác`, `Chưa thử` hoặc `Không hợp lúc này`; feedback không tự động tái huấn luyện hay đổi chart interpretation.
- R19. Share card chỉ gồm câu hỏi đã được người dùng duyệt, card/position, một reflection ngắn và provenance `Tự bốc` hoặc `Reader bốc cùng`; không có birth data, tên người thứ ba, chart evidence hay kết luận compatibility.

**Safety, privacy và quality**

- R20. Output không được dự đoán chắc chắn, đọc ý định người thứ ba, chẩn đoán, thúc ép chia tay/quay lại, đưa chỉ dẫn y tế–pháp lý–tài chính hoặc tạo khẩn cấp giả.
- R21. Câu hỏi nhạy cảm phải chuyển sang ngôn ngữ giữ quyền tự quyết, từ chối nội dung ngoài phạm vi và đưa resource phù hợp khi có tín hiệu khủng hoảng.
- R22. Emotion, repeated question, Radar friction và mood không được dùng để nhắm upsell hoặc tăng giá; disclaimer không thay thế gate và moderation.
- R23. Mỗi output phải qua evidence/provenance, anti-influence, editorial/meaning và privacy gates phù hợp với Tarot trước khi hiển thị.
- R24. Product analytics chỉ đo event và quality signal tối thiểu; không gửi nguyên câu hỏi, reading prose, card history gắn định danh, birth data hoặc third-party context vào analytics.

### Key Flows

#### Flow 1 — Từ Daily Note sang self-draw

- **Trigger:** User đọc xong Daily Note và chọn `Hỏi thêm một góc`.
- **Steps:** App đưa ba câu gợi ý → user chọn/sửa câu và context → chọn spread → tự shuffle/chọn lá → reveal theo position → đọc interpretation → lưu hoặc bỏ.
- **Outcome:** User có một góc reflection mới, còn Daily Note và chart evidence giữ nguyên.
- **Covers:** R7–R14, R20–R24.

#### Flow 2 — Từ Radar sang self-draw

- **Trigger:** User chọn một chapter hoặc điểm cấn trong Radar.
- **Steps:** App chỉ mang sang excerpt đã chọn → gợi ba câu tập trung vào phần user có thể quan sát/hỏi → user bốc → output không suy ý định người kia → user có thể tạo conversation prompt.
- **Outcome:** Tarot giúp user soi phần mình và câu cần hỏi, không biến thành compatibility verdict.
- **Covers:** R8, R11, R13, R19–R24.

#### Flow 3 — Rút lá làm rõ

- **Trigger:** User chọn `Chỗ này vẫn chưa rõ` trong reading hiện tại.
- **Steps:** User chọn câu/position → chọn mục đích làm rõ → rút một lá → app đặt clarifier cạnh phần gốc → khóa draw bổ sung trong session.
- **Outcome:** Reading sâu hơn nhưng lịch sử và ambiguity không bị xóa.
- **Covers:** R15–R17, R20–R23.

#### Flow 4 — Editor phát hành knowledge

- **Trigger:** Editor tạo hoặc sửa card meaning, position rule, question prompt hoặc safety copy.
- **Steps:** Hoàn thiện metadata → specialist review → safety/privacy review → fixture preview và gates → publisher tạo release → staged activation → monitor hoặc rollback.
- **Outcome:** Nội dung mới có provenance, có thể audit và không sửa ngầm revision cũ.
- **Covers:** R1–R6, R23.

#### Flow 5 — Save và share

- **Trigger:** User chọn lưu đồng bộ hoặc tạo share card.
- **Steps:** App xin auth đúng lúc nếu cần → user preview dữ liệu sẽ xuất hiện → tạo immutable artifact/link có revoke/expiry → recipient chỉ thấy public projection.
- **Outcome:** Insight có thể mang đi mà không lộ birth data hoặc người thứ ba.
- **Covers:** R14, R19, R24.

### Acceptance Examples

- AE1. **Given** user mở Lá Hỏi từ Daily Note, **when** user chọn một câu gợi ý và bốc một lá, **then** kết quả nói rõ đây là Tarot draw và không đổi nội dung hoặc evidence của Daily Note. Covers R8–R11, R13.
- AE2. **Given** Radar chứa thông tin về một người khác, **when** user mở Lá Hỏi, **then** context mặc định chỉ là excerpt user vừa chọn và output không khẳng định người kia nghĩ hoặc sẽ làm gì. Covers R13, R20, R24.
- AE3. **Given** user đã có reading, **when** user yêu cầu làm rõ, **then** họ phải chọn phần chưa rõ và chỉ nhận một clarifier gắn với phần đó. Covers R15–R17.
- AE4. **Given** user muốn bốc lại cùng câu hỏi vì không thích kết quả, **when** họ chọn draw again, **then** app mở lại reading hoặc giúp viết câu hỏi cụ thể hơn thay vì cấp vô hạn lá mới. Covers R17, R22.
- AE5. **Given** một content block thiếu source rights hoặc bị safety gate chặn, **when** publisher mở release, **then** release không thể activate và báo đúng lý do cho editor. Covers R2–R5, R23.
- AE6. **Given** user chưa đăng nhập, **when** họ hoàn tất self-draw và không chọn sync/share, **then** họ vẫn xem được reading mà không bị chặn bởi auth. Covers R14.
- AE7. **Given** user tạo share card từ Radar-linked Tarot, **when** recipient mở link, **then** không có tên người thứ ba, birth data, chart evidence hoặc compatibility claim. Covers R19, R24.

### Success Measures

- Tỷ lệ hoàn tất phiên sau khi đã chọn câu hỏi, không dùng tổng số draw làm north-star.
- Tỷ lệ user đánh dấu reading `rõ hơn` hoặc lưu một micro-action.
- Tỷ lệ clarifier trên first reading nằm trong ngưỡng lành mạnh và không tăng theo cơ chế monetization.
- Tỷ lệ output qua automated gates và human sample review theo từng release.
- Tỷ lệ share bị revoke/report, privacy incident và safety escalation.
- Tỷ lệ quay lại recap hoặc reading đã lưu thay vì bốc lại cùng câu.

### Feature Expansion Priority

1. **Content Studio foundation:** workflow, corpus, preview, gates, release và rollback.
2. **Lá Hỏi self-draw:** entry từ Daily/Radar, question bank, one-card/three-card reading.
3. **Rút lá làm rõ:** anchored clarifier và anti-redraw controls.
4. **Vòng đối chiếu:** micro-action outcome và weekly private recap.
5. **Lá mang đi:** privacy-safe share artifact và acquisition landing.
6. **Lá Dẫn Live:** chỉ bắt đầu sau khi verification, booking, payment, moderation, block/report và support runbook được duyệt.

### Scope Boundaries

**Trong self-draw MVP**

- Content Studio tối thiểu để quản lý Tarot knowledge và question prompts.
- Self-draw từ Daily, Radar và Khám phá.
- Một clarifier, save, delete và share projection.
- Quality, privacy và anti-influence gates.

**Deferred for later**

- Reader discovery, live booking, payment, availability, refund, payout và trust console.
- Asynchronous written/audio/video reader delivery.
- Creator deck marketplace, paid interpretation packs và community annotations.
- Pair pulse, monthly pattern map và adaptive personalization từ feedback.

**Outside this product's identity**

- Tarot như bằng chứng cho chart hoặc compatibility score.
- Unlimited redraw, streak/FOMO, curse removal, certainty claims và emotionally targeted upsell.
- Public feed cho câu hỏi nhạy cảm hoặc reader contact ngoài nền tảng.

<!-- ce-section: work-relationships -->
### How This Work Fits Together

Plan này bao phủ self-draw Tarot và Content Studio tối thiểu cần để phát hành nó an toàn. Các phần sau là hướng mở rộng, chưa phải cam kết implementation trong cùng release:

- **Content Studio** enables self-draw quality, Daily/Radar corpus growth và future reader-authored content.
- **Rút lá làm rõ** depends on first-reading provenance và immutable session history.
- **Vòng đối chiếu** shares mood, save và experiment patterns nhưng cần privacy purpose riêng.
- **Lá Dẫn Live** depends on identity verification, marketplace operations, payments, moderation và store-policy review.
- **Async reader delivery** can proceed only after digital-content payment, transcript retention và dispute rules được quyết định.

### Outstanding Questions

**Deferred to planning**

- Chọn bộ bài public-domain/licensed nào và policy quyền sử dụng artwork ra sao.
- Reversal tắt ở MVP hay là lựa chọn rõ ràng của user; không được bật ngầm.
- Exact retention cho guest Tarot session và near-identical-question cooldown.
- Content Studio MVP dùng UI nội bộ hoàn chỉnh hay import/export có review UI tối thiểu trước.

**Deferred to a separate reader-marketplace plan**

- Live text, voice hay video là launch format đầu tiên.
- Merchant/payment route cho web, iOS và Android; recording/transcript có được phép hay không.
- Reader verification standard, age gate, pricing, refund/no-show, payout, report và appeals.

### Sources and Research

- Product grounding: `docs/foundation/la-lanh-reading-knowledge-spec.md`, `docs/operations/content-matrix-release-gate.md`, `docs/foundation/la-lanh-radar-hop-gu-spec.md`, `docs/foundation/la-lanh-product-plan-v2.md`, `docs/ideation/2026-09-08-short-game-reveal-onboarding-ideation.html`.
- Current implementation grounding: `apps/api/app/domains/readings/`, `apps/api/app/domains/astro/`, `apps/api/app/domains/radar/`, `apps/api/app/domains/relationships/`, `apps/api/app/domains/share/`.
- External patterns: [Labyrinthos app](https://labyrinthos.co/pages/app), [Labyrinthos clarification guidance](https://labyrinthos.co/blogs/learn-tarot-with-labyrinthos-academy/when-a-tarot-reading-makes-no-sense-how-to-interpret-a-confusing-tarot-reading?page=2), [Keen advisor screening](https://help.keen.com/hc/en-us/articles/4413390476307-How-do-I-apply-to-be-an-Advisor), [Purple Garden verification](https://www.purplegarden.co/how-we-verify-advisors), [Biddy Tarot ethics](https://biddytarot.com/blog/the-ethics-of-tarot-reading/), [Apple App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/), [Google Play 1:1 online services](https://support.google.com/googleplay/android-developer/answer/10281818).

