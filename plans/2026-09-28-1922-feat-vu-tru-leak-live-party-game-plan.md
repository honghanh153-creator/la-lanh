---
title: Vũ Trụ Leak Live Party Game - Plan
type: feat
date: 2026-09-28
topic: vu-tru-leak-live-party-game
artifact_contract: ce-unified-plan/v1
product_contract_source: ce-brainstorm
execution: code
---

# Vũ Trụ Leak Live Party Game - Plan

## Goal Capsule

- **Objective:** Một nhóm 3–6 sinh viên 18+ có thể vào cùng một room bằng link hoặc QR, chơi hết một phiên Astro party game trong tối đa 8 phút và nhận một recap đáng chia sẻ mà không phải công khai dữ liệu sinh.
- **Means:** Xây `Vũ Trụ Leak`, nơi nhóm đoán phản ứng của từng người, lật đáp án thật, xem chart receipt khi người đó đồng ý và kết thúc bằng một Tarot plot twist tùy chọn.
- **Product authority:** Product Contract này quyết định hành vi người chơi, phạm vi launch, safety line, nội dung và tín hiệu thành công. Kế hoạch triển khai sau đó quyết định kiến trúc realtime và cách tái dùng capability, chart, Tarot và share renderer hiện có.
- **Open blockers:** Không có câu hỏi chặn planning. Các ngưỡng pilot bên dưới là mục tiêu kiểm chứng, không phải benchmark thị trường.

---

## Product Contract

### Summary

`Vũ Trụ Leak` là live party game mobile-first cho nhóm bạn đang ở cùng nhau hoặc đang gọi nhóm.
Mỗi vòng tạo một reveal ba lớp: nhóm đoán gì, người trên ghế nóng tự chọn gì và chart gợi ý pattern nào.
Link referral là vé vào room đang chạy; người nhận không phải đăng ký hoặc nhập dữ liệu sinh để chơi.

### Problem Frame

Các tính năng Lá Lành hiện tại chủ yếu tạo giá trị trong phiên đọc riêng tư.
Referral hiện có thể đưa một người vào flow, nhưng chưa tạo khoảnh khắc cả nhóm phải tham gia cùng lúc hoặc một câu chuyện đủ riêng để chia sẻ sau đó.
Quiz async, daily puzzle và card horoscope đều dễ sao chép và thiếu phản ứng tập thể.

Cửa sổ 2026 ưu tiên nội dung có chuyện thật, reaction, co-creation và các buổi tụ tập có concept rõ.
Lá Lành có lợi thế mà game party phổ thông không có: chart có thể giải thích khoảng lệch giữa cách bạn bè nhìn một người và cách người đó tự nhận mình, miễn là chart chỉ đóng vai nhân chứng chứ không phán quyết.

### Key Decisions

- **Live room là sản phẩm chính, không phải quiz async.** Governs R1–R9.
- **Chart receipt là lớp thứ ba sau vote và đáp án thật.** Governs R10–R14.
- **Referral là quyền tham gia room, không phải điều kiện mở khóa reading.** Governs R2, R5, R20.
- **MVP chỉ dành cho người từ 18 tuổi.** Governs R3, R18, R19.
- **Không có free-text ẩn danh.** Governs R7, R15–R19.
- **Tarot chỉ là plot twist cuối room và có thể bỏ qua.** Governs R13–R14.
- **Campus là kênh pilot, không có school dashboard.** Governs R23–R24.

### Actors

- A1. **Host:** Người tạo room, chia sẻ link/QR, bắt đầu hoặc kết thúc phiên và xử lý người phá game.
- A2. **Player:** Người vào room bằng nickname, vote, lên ghế nóng nếu đồng ý, react và nhận recap.
- A3. **Profile owner:** Player đã có chart trong Lá Lành và chủ động bật chart receipt cho vòng của mình.
- A4. **Campus partner:** Câu lạc bộ hoặc đại sứ sinh viên phát QR cho pilot nhưng không nhận dữ liệu cá nhân trong room.
- A5. **Safety operator:** Người xử lý report và theo dõi các chỉ số abuse ở mức cần thiết cho beta.

### Requirements

**Room entry and presence**

- R1. Host có thể tạo một room riêng tư cho 3–6 người và nhận link cùng QR để mời bạn tham gia.
- R2. Player mở link phải xem được premise, tuổi tối thiểu và dữ liệu cần dùng trước khi nhập nickname và vào room mà không cần tài khoản.
- R3. Host và player phải xác nhận từ 18 tuổi trước khi tạo hoặc tham gia room; người không xác nhận không được vào game.
- R4. Room phải hiển thị rõ ai đang online, ai đã sẵn sàng và điều kiện tối thiểu để host bắt đầu.
- R5. Invite chỉ cấp quyền vào đúng room, tự hết hạn và có thể bị host thu hồi; URL không chứa nickname, birth data, chart evidence hoặc câu trả lời.
- R6. Nếu room chưa đủ ba người, app cho phép host chờ, chia sẻ lại hoặc đóng room mà không tạo cảm giác người chơi đã thất bại.

**Round loop**

- R7. Mỗi round dùng một prompt đóng có 2–3 lựa chọn từ content bank; MVP không nhận free-text từ host hoặc player.
- R8. Mỗi player được mời lên ghế nóng tối đa một lần trong phiên và có thể bỏ qua mà không cần giải thích.
- R9. Một round phải lần lượt khóa đáp án bí mật của người trên ghế nóng, nhận vote của nhóm, lật vote, lật đáp án thật và mở reaction trong một nhịp không quá 60 giây.

**Chart receipt and Tarot**

- R10. Chart receipt chỉ xuất hiện khi người trên ghế nóng có chart thuộc chính họ và bật consent cho round đó.
- R11. Receipt phải dùng tối thiểu hai tín hiệu chart có liên quan trực tiếp tới prompt; nếu evidence không đạt ngưỡng nội dung, app bỏ receipt thay vì tạo lời giải thích chung chung.
- R12. Receipt phải giải thích khoảng lệch giữa vote và đáp án bằng ngôn ngữ đời thường; placement, độ số, ngày sinh, giờ sinh và nơi sinh không xuất hiện trong room hoặc recap.
- R13. Sau round cuối, nhóm có thể bỏ qua hoặc cùng chọn một lá úp để nhận Tarot plot twist về nhịp của phiên chơi.
- R14. Tarot plot twist không được dự đoán tương lai, đọc ý định người vắng mặt hoặc thay đổi kết quả các round trước.

**Content and tone**

- R15. Prompt bank chỉ dùng tình huống low-stakes quen thuộc với sinh viên: group project, deadline, đi chơi, nhắn tin, chia lịch, làm quen và ranh giới giao tiếp.
- R16. Prompt, receipt, reaction và recap không được gắn nhãn toxic, red flag, thông minh, bất ổn, chung thủy, hấp dẫn hoặc chẩn đoán sức khỏe tâm thần.
- R17. Giọng game được phép cợt nhẹ ở hành vi cụ thể nhưng không chế giễu ngoại hình, hoàn cảnh, danh tính hoặc phần chart của người chơi.

**Safety, privacy and control**

- R18. MVP không có public room discovery, contact upload, auto-invite, direct message, voice chat hoặc anonymous text.
- R19. Host có thể kick và end room; mọi player có thể leave, mute reaction và report room hoặc prompt.
- R20. Core natal, Daily, Radar và Tarot reading không được khóa sau số lượt mời, số người tham gia hoặc share.
- R21. Room state và player inputs phải tự xóa trong vòng 24 giờ; recap chỉ được giữ lâu hơn khi host chủ động lưu trong phạm vi retention đã công bố.
- R22. Analytics chỉ ghi sự kiện sản phẩm và safety; không ghi nickname, birth data, chart evidence, vote choice hoặc nội dung receipt.

**Recap and campus pilot**

- R23. Kết thúc phiên tạo `Leak Tape` 9:16 với số liệu vui từ chính phiên chơi, reaction được chọn và một CTA mở room mới; artifact không chứa dữ liệu sinh hoặc raw chart evidence.
- R24. Campus partner chỉ thấy số room, số người tham gia, completion và report rate ở dạng tổng hợp; không thấy danh sách người chơi, social graph, vote hoặc chart.
- R25. Pilot phải cho phép tắt campus label và chơi như một nhóm bạn bình thường để game không phụ thuộc vào quan hệ chính thức với trường.

### Key Flows

- F1. **Create and join room**
  - **Trigger:** A1 chọn `Mở Vũ Trụ Leak`.
  - **Actors:** A1, A2.
  - **Steps:** Host xác nhận 18+, nhận link/QR, bạn mở preview, xác nhận 18+, nhập nickname và vào lobby.
  - **Outcome:** Lobby có 3–6 player sẵn sàng hoặc host đóng room an toàn.
  - **Covers:** R1–R6.

- F2. **Play one round**
  - **Trigger:** Host bắt đầu và hệ thống chọn player đồng ý lên ghế nóng.
  - **Actors:** A1, A2, A3.
  - **Steps:** Player chọn đáp án bí mật; nhóm vote trong countdown; app reveal vote, đáp án thật, receipt đủ điều kiện và reaction.
  - **Outcome:** Cả nhóm hiểu một khoảng lệch cụ thể mà không bị gắn nhãn.
  - **Covers:** R7–R12, R15–R17.

- F3. **Finish with Tarot**
  - **Trigger:** Round cuối hoàn thành.
  - **Actors:** A1, A2.
  - **Steps:** Nhóm chọn bỏ qua hoặc chọn một lá úp; app hiển thị plot twist có giới hạn và chuyển sang recap.
  - **Outcome:** Tarot tạo một kết thúc chung nhưng không phán tương lai.
  - **Covers:** R13–R14.

- F4. **Share the lore**
  - **Trigger:** Recap hoàn tất.
  - **Actors:** A1, A2.
  - **Steps:** Người chơi xem Leak Tape, chọn share hoặc tạo room mới; người mở artifact công khai chỉ thấy nội dung đã làm sạch.
  - **Outcome:** Phiên chơi tạo acquisition loop mà không làm lộ chart.
  - **Covers:** R20, R23.

- F5. **Handle discomfort or abuse**
  - **Trigger:** Một player không muốn lên ghế nóng, rời room hoặc report.
  - **Actors:** A1, A2, A5.
  - **Steps:** Player skip/leave ngay; host có thể kick/end; report được ghi nhận mà không giữ nội dung riêng quá phạm vi cần thiết.
  - **Outcome:** Phiên tiếp tục hoặc dừng mà không ép người chơi tham gia.
  - **Covers:** R8, R18–R22.

### Acceptance Examples

- AE1. **Covers R2, R5.** Người nhận mở link trên trình duyệt mới, xem premise và age gate, nhập nickname rồi vào lobby; URL và trang preview không lộ dữ liệu của host.
- AE2. **Covers R6.** Chỉ có hai người trong lobby; host thấy `Cần thêm 1 người` cùng lựa chọn chia sẻ lại hoặc đóng room, không thấy CTA ép upload danh bạ.
- AE3. **Covers R8.** Player được chọn lên ghế nóng nhưng bấm `Bỏ qua lượt này`; game chuyển sang người khác và recap không gắn nhãn player đó.
- AE4. **Covers R10–R12.** Player có chart nhưng chưa bật consent; reveal vẫn có vote và đáp án thật, còn chart receipt được thay bằng `Bạn chưa bật receipt cho vòng này` chỉ trên màn hình của player đó.
- AE5. **Covers R11.** Chart engine không tìm được hai tín hiệu đủ liên quan; app không render một câu astrology chung chung và tiếp tục bằng insight từ vote so với đáp án.
- AE6. **Covers R13–R14.** Nhóm bỏ qua Tarot; recap vẫn đầy đủ và không coi phiên là chưa hoàn thành.
- AE7. **Covers R18–R19.** Player gửi reaction phá game liên tục; host kick player, token room của họ mất hiệu lực và họ vẫn có thể gửi report từ màn hình rời room.
- AE8. **Covers R21.** Sau 24 giờ, link room không mở lại được state hoặc vote; host chỉ còn recap nếu đã chủ động lưu.
- AE9. **Covers R23–R24.** Leak Tape được share ra ngoài campus; người xem thấy lore của phiên và CTA mở room, nhưng không thấy trường, ngày sinh, chart evidence hoặc danh sách vote cá nhân.

### Success Criteria

Các ngưỡng dưới đây là mục tiêu go/no-go cho pilot đầu tiên, không phải benchmark thị trường:

- Ít nhất 60% room có đủ ba người phải đi tới reveal đầu tiên.
- Median time từ tạo room tới reveal đầu tiên không quá 90 giây.
- Ít nhất 70% player đã vào round đầu phải ở lại tới recap.
- Ít nhất 20% player không phải host tạo room riêng trong 24 giờ sau phiên.
- Ít nhất 25% phiên hoàn tất tạo một hành động share hoặc save Leak Tape.
- Report rate dưới 1% player-session và không có P0 privacy incident trong pilot.
- Nghiên cứu định tính sau pilot phải xác nhận người chơi mô tả giá trị bằng “cả hội hiểu/đoán nhau” hoặc tương đương, không chỉ bằng “xem bói vui”.

### Scope Boundaries

**Deferred for later**

- `21:21 Cosmic Drop`, campus campaign có lịch hẹn và `12 Nhà After Dark`.
- `Toà Vũ Trụ`, Mercury Relay, public reaction remix và video animation nâng cao.
- Room lớn hơn sáu người, voice chat, spectator mode và nhiều deck Tarot.
- Reward collection, group lorebook dài hạn và account-based friend graph.

**Outside this product's identity**

- Anonymous confession, public roast, compatibility leaderboard hoặc xếp hạng người chơi theo chart.
- Teacher/school dashboard truy cập profile, vote hoặc derived insight của sinh viên.
- Game cho người dưới 18 tuổi trong phiên bản này.
- Prediction về điểm thi, sức khỏe, tình dục, sự chung thủy, hành vi phạm pháp hoặc ý định của người vắng mặt.
- Referral reward làm tăng độ “đúng”, mở khóa full natal hoặc tạo lợi thế trả phí trong game.

### Dependencies / Assumptions

- Guest session, capability link, natal chart, Tarot session, content gate và share artifact hiện có đủ gần để planning đánh giá khả năng tái sử dụng; realtime room vẫn là capability mới.
- Prompt bank cần editorial review riêng trước pilot; số lượng launch không quan trọng bằng khả năng tạo tranh luận mà không gây tổn thương.
- Pilot ban đầu dùng mobile web trên beta hiện có và nhắm tới nhóm sinh viên 18+ tại 2–3 câu lạc bộ trong hai tuần.
- Người chơi có thể ở cùng một địa điểm hoặc trong group call; game không phụ thuộc GPS, email trường hoặc danh bạ.

### Sources / Research

- `docs/ideation/2026-09-28-astro-tarot-campus-referral-games-ideation.html`
- `docs/foundation/la-lanh-tarot-engine-spec.md`
- `apps/web/src/app/router.tsx`
- `packages/contracts/src/v1.ts`
- [TikTok Next 2026](https://ads.tiktok.com/business/en-GB/next)
- [Discord social play, 2026](https://discord.com/press-releases/introducing-new-tools-to-power-game-discovery-and-social-play)
- [Vietnam student online–offline–online case](https://bsiawards.buzzmetrics.com/case-library/giai-the-thao-sinh-vien-toan-quoc-nam-2025---cup-tv360-2)
- [FTC action against NGL](https://www.ftc.gov/news-events/news/press-releases/2024/07/ftc-order-will-ban-ngl-labs-and-its-founders-offering-anonymous-messaging-apps-to-kids-under-18-and-halt)
- [Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15](https://vanban.chinhphu.vn/?classid=1&docid=214590&orggroupid=1&pageid=27160)
