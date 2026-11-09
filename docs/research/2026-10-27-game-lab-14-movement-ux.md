# Game lab 14: nghiên cứu chuyển động, game feel và UI/UX

Ngày 27/10/2026. Người làm: Claude. Prototype: [`prototype/game-lab-14/`](../../prototype/game-lab-14/README.md). Nối tiếp review game lab 13 ở PR #104.

Owner chọn (27/10/2026): nghiên cứu rồi dựng lại; người chơi điều khiển nhân vật đi lại; đồ họa pixel (hướng B).

## Cách nghiên cứu

Chạy quy trình deep research: 5 hướng tìm, 23 nguồn, 94 nhận định. 25 nhận định quan trọng nhất được kiểm chéo 3 phiếu, 20 giữ lại và 5 bị bác. Nguồn được ghi rõ là primary (MDN, W3C, Microsoft XAG, bài báo bình duyệt), secondary (báo ngành) hay ý kiến nhà làm game. Phần về Obra Dinn và Golden Idol đã kiểm trực tiếp ở review PR #104.

## Điều có bằng chứng và đã áp dụng

| Chủ đề | Nguồn | Áp dụng trong lab 14 |
|---|---|---|
| Pixel sắc nét: canvas nhỏ, CSS `image-rendering: pixelated`, chỉ phóng theo bội số nguyên | [MDN Crisp pixel art](https://developer.mozilla.org/en-US/docs/Games/Techniques/Crisp_pixel_art_look) (primary) | Canvas 240×160, phóng theo bội số nguyên của pixel thiết bị; vẽ ở toạ độ làm tròn |
| `imageSmoothingEnabled` mặc định là true và bị đặt lại khi đổi kích thước canvas | [MDN imageSmoothingEnabled](https://developer.mozilla.org/en/docs/Web/API/CanvasRenderingContext2D/imageSmoothingEnabled) (primary) | Tắt lại sau mỗi lần `fit()` |
| Vùng chạm: 24×24 là sàn AA, 44×44 cho điều khiển quan trọng | [WCAG 2.2 SC 2.5.8](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum) và SC 2.5.5 (primary) | Mọi nút ≥ 44 px; nút hành động 56 px; D-pad 48 px mỗi ô |
| D-pad/joystick ảo kém hơn nút vật lý, dễ trôi khi mắt rời khỏi nút | [Baldauf và cộng sự 2015](https://publications.ait.ac.at/en/publications/investigating-on-screen-gamepad-designs-for-smartphone-controlled/), [Teather, Roth & MacKenzie 2017](https://yorku.ca/mack/ec2017.html) (bình duyệt) | Chạm-để-đi là điều khiển chính; D-pad chỉ là tuỳ chọn. **Chưa có nghiên cứu nào so trực tiếp chạm-để-đi**, đây là suy luận |
| Nhấp nháy chỉ vi phạm khi > 3 lần/giây **và** đủ lớn; đỏ bão hoà có ngưỡng chặt hơn | [WCAG 2.3.1](https://w3c.github.io/wcag21/understanding/three-flashes-or-below-threshold), [Xbox XAG 118](https://learn.microsoft.com/en-us/gaming/accessibility/xbox-accessibility-guidelines/118) (primary) | Không có hiệu ứng nhấp nháy; báo sai dùng chữ hồng nhạt, rung nhỏ một lần, tắt khi giảm chuyển động |
| Cần nút tắt/giảm chuyển động trong game, không chỉ dựa vào `prefers-reduced-motion` | [Xbox XAG 117](https://learn.microsoft.com/en-us/gaming/accessibility/xbox-accessibility-guidelines/117) (primary, hướng dẫn) | Cài đặt Đầy đủ / Giảm / Tắt; mặc định Giảm nếu hệ điều hành yêu cầu |
| Camera cố định hợp với phòng vừa một màn hình | Itay Keren, *Scroll Back*, GDC 2015 ([bản ghi lại](https://icewyrmgames.github.io/research/scroll-back-the-theory-and-practice-of-cameras-in-side-scrollers), secondary) | Không cuộn camera |
| Phản hồi tức thì cho mỗi lần đoán khiến người chơi thử hết tổ hợp | Lucas Pope, [devlog #734](https://dukope.com/devlogs/obra-dinn/tig-30/); Color Gray Games, [Game Developer 1/11/2022](https://www.gamedeveloper.com/design/case-of-the-golden-idol) (ý kiến nhà làm game) | Nộp phải đúng cả hồ sơ lẫn lý do; sai thì một câu chung |

## Ý kiến, chưa có bằng chứng (ghi rõ là quy ước)

- Tốc độ đi khoảng 60–90 px/s ở độ phân giải gốc; lab 14 dùng 72 px/s, đạt tốc độ tối đa trong khoảng 0,08 giây, dừng trong khoảng 0,06 giây.
- Chu kỳ bước 4 khung, mỗi khung 120–150 ms; lab 14 dùng 130 ms. Chớp mắt mỗi 3–5 giây, dài 130 ms.
- "Juice" là nhiều lớp phản hồi nhỏ (Jan Willem Nijman, *The Art of Screenshake*, theo tường thuật của [Game Developer](https://gamedeveloper.com/design/vlambeer-co-founder-shares-advice-on-building-better-action-games)). Đây là trình diễn cho game bắn súng, nên lab 14 chỉ lấy các lớp êm: bụi bước chân, lấp lánh, nhân vật nhảy nhẹ, hồ sơ tan thành lá. Bỏ rung màn hình để giữ tinh thần "bình yên".

## Nhận định bị bác, không dùng

- "9,2 mm tương đương 44–48 CSS px".
- Số liệu UXmatters 2013 về tỉ lệ cầm máy một tay và ngón cái trái/phải.
- "Mọi hiệu ứng phải ≤ 3 lần nhấp nháy/giây" mà bỏ qua ngoại lệ về diện tích.
- Định nghĩa camera lerp theo nguồn đã dẫn.

## Câu hỏi mở cho chơi thử

1. Trên điện thoại 360–390 px, chạm-để-đi có ít lỗi và nhanh tới đồ vật hơn D-pad không? Đo bằng số lần chạm hụt và thời gian tới nguồn đầu tiên.
2. Người mới có hiểu phải làm gì trong 30 giây đầu nhờ mũi tên mục tiêu và ba bước dưới khung game không?
3. Bỏ máy chấm có làm người chơi bỏ cuộc ở P2/R2 không? Có cần thang gợi ý không làm lộ đáp án không?
4. Bội số pixel không đều khi giãn ở 360 px/2x có gây khó chịu không?
