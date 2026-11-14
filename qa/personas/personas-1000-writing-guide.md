# Hướng dẫn viết phần đời sống cho người giả P101–P1000

Mỗi người viết nhận một tệp khung (`skeleton-NN.json`, khoảng 30 người). Khung đã cố định: nhóm, hoàn cảnh chính (`segment_label`), tuổi, vùng, nơi đang sống (`attributes.lives_in`, `living_area`), quê (`hometown`), ngành (nếu là sinh viên), thu nhập hoặc mức chi (`attributes.income`), mạng xã hội (`attributes.platforms`, `main_app`), có xem video "chọn tụ" Tarot trên TikTok không (`pick_a_pile_watcher`), LGBTQ+ (`lgbtq`), dùng chung điện thoại (`shared_phone`), không có ai an toàn để tâm sự (`no_safe_person`), mức quen điện thoại (`digital_literacy`), hay thức sau 0 giờ (`sleeps_after_midnight`), mức căng thẳng (`stress`), mức hứng thú chiêm tinh (`traits.interest`), các mức chịu lặp, chịu việc, tỉ lệ giữ việc (`traits`), và mood 29 ngày (`mood_29`).

**Không đổi bất kỳ trường nào của khung.** Chỉ viết thêm các trường dưới đây, khớp với khung.

## Nguyên tắc

- Mọi người là **hư cấu**. Không lấy người thật, người nổi tiếng, KOL, tài khoản mạng xã hội có thật, tên trường hay công ty cụ thể có thể nhận ra một người. Có thể nói tên thành phố, ngành, loại công việc.
- Không viết ngày, giờ, nơi sinh vào phần chữ.
- Tiếng Việt đời thường, câu ngắn, cụ thể. Không thơ, không sáo.
- Không định kiến, không giễu nhại. Người LGBTQ+ được viết như người bình thường có chuyện đời riêng; chỉ nhắc chuyện công khai hay chưa nếu hợp hoàn cảnh.
- Thu nhập và mức chi phải khớp: người chi dưới 1 triệu thì đời sống thắt chặt; người chi từ 5 triệu thì có thể thoải mái hơn.
- `shared_phone` = true: nói rõ ai hay cầm máy (em, mẹ, bạn cùng phòng, vợ/chồng…).
- `no_safe_person` = true: nói rõ vì sao không có ai an toàn để kể (nhà căng, bạn mới quen, ngại…).
- `pick_a_pile_watcher` = true: họ hay xem video "chọn tụ" Tarot trên TikTok.
- `digital_literacy` = "low": dùng điện thoại hạn chế (gọi, Zalo, xem video), ngại bấm nhiều.
- Phần chữ không được nhắc tới khủng hoảng, tự làm hại, hay ý muốn không sống. Phần kiểm an toàn đã nằm ở `tests` của khung, đừng viết thêm.

## Các trường cần viết

| Trường | Viết gì |
|---|---|
| `name` | Tên gọi tiếng Việt hư cấu, 1–3 chữ. |
| `situation` | 2–4 câu: đang làm gì, ở đâu, với ai, tiền ra sao, chuyện gì đang chiếm đầu. Khớp mọi thuộc tính trên. |
| `stressors` | 3–5 áp lực cụ thể (mảng chuỗi ngắn). |
| `personality` | 1–2 câu, có nhắc thái độ với chiêm tinh/Tarot theo `traits.interest` (high: tin khá nhiều; mid: nửa tin nửa ngờ; low: không tin, dùng thử). |
| `daily_rhythm` | 1–2 câu: giờ dậy, giờ làm/học, giờ ngủ (khớp `sleeps_after_midnight`). |
| `phone_habits` | 1–2 câu: dùng app nào nhiều nhất (đúng `main_app`), các app khác trong `platforms`, mở Lá lúc nào, bao lâu. |
| `wants_from_app` | 2–4 điều họ muốn ở Lá. |
| `would_quit_if` | 2–3 điều làm họ bỏ app. |
| `quit_triggers` | 1–3 nhãn lấy từ: `repetition`, `generic`, `mood_ignored`, `task_pressure`, `no_memory`, `wrong_tone`. Khớp `would_quit_if`. |
| `repetition_tolerance_note` | 1 câu, khớp `traits.tolerance_repetition` (0,1 = rất ghét lặp; 0,8 = dễ chịu). |
| `task_tolerance_note` | 1 câu, khớp `traits.tolerance_tasks` (0,1 = rất ghét bị giao việc; 0,9 = thích có việc nhỏ). |
| `mood_pattern_note` | 1–2 câu giải thích vì sao mood 29 ngày đi như vậy. |
| `keeps_actions` | `{"likes": [...], "avoids": [...], "note": "..."}`. Nhãn lấy từ: `rest`, `body`, `solo_reflect`, `writing`, `social`, `planning`, `study_work`. `likes` không rỗng, không trùng `avoids`. |
| `tarot_questions` | 3–6 câu hỏi Tarot bằng giọng của họ: `{"day": 1–27, "context": "...", "text": "..."}`. `context` lấy từ: `general`, `relationships`, `work`, `communication`, `energy`, `self_care`. Mỗi câu 8–280 ký tự. **Không dùng** các chữ: "chết", "chet", "tự tử", "tu tu", "tự làm đau", "biến mất", "không muốn sống". |

## Đầu ra

Một tệp JSON là **mảng**, mỗi phần tử có `id` (đúng id trong khung) và đủ các trường trên. Ví dụ định dạng (một người giả có sẵn, đã rút gọn):

```json
{"id": "P004", "name": "Mai Hương",
 "situation": "Hương học năm ba ngành Điều dưỡng ở Hà Nội, ở ký túc xá trường. Quê ở Lào Cai, sau cấp ba đi làm công nhân hai năm rồi mới đi học lại nên lớn tuổi hơn bạn cùng lớp. Đang đi thực tập ở bệnh viện, có ca trực tối, tiền chủ yếu từ khoản dành dụm và mẹ gửi thêm.",
 "stressors": ["Ca thực tập tối về muộn, ngủ không đủ", "Lớn tuổi hơn bạn cùng lớp nên đôi khi thấy lạc lõng", "Khoản tiền dành dụm vơi dần"],
 "personality": "Chịu khó, kiên nhẫn, sống nội tâm. Không quan tâm nhiều đến tử vi, mở app chủ yếu để ghi lại tâm trạng.",
 "daily_rhythm": "Dậy 5 giờ rưỡi đi thực tập, chiều học trên lớp. Hôm có ca tối thì 22 giờ mới về, ngủ khoảng 23 giờ.",
 "phone_habits": "Dùng Zalo gọi về nhà, Facebook đọc tin nhóm lớp. Mở app này khoảng năm phút trước khi ngủ.",
 "wants_from_app": ["Một câu nhẹ nhàng, nói đúng hôm mình vừa trải qua", "Không bắt làm nhiều việc"],
 "would_quit_if": ["App không nhớ hôm qua mình vừa trực đêm", "Lời khuyên chung chung kiểu ai cũng nhận được"],
 "quit_triggers": ["no_memory", "generic"],
 "repetition_tolerance_note": "Không khó tính chuyện lặp, chỉ cần nội dung vẫn hợp với ngày hôm đó.",
 "task_tolerance_note": "Một hai việc nhỏ thì được, nhưng hôm trực về muộn sẽ bỏ qua.",
 "mood_pattern_note": "Cuối tuần thường lạc trôi vì nhớ nhà, có hôm căng khi bị nhắc ở khoa, còn lại chill.",
 "keeps_actions": {"likes": ["rest", "body"], "avoids": ["social"], "note": "Hay làm việc như duỗi chân, uống nước, đi ngủ sớm."},
 "tarot_questions": [{"day": 3, "context": "self_care", "text": "Tuần này trực nhiều, mình nên giữ sức thế nào"}]}
```

Trước khi trả lời, chạy `python3 check_batch.py <tệp khung> <tệp của bạn>` trong cùng thư mục và sửa tới khi báo `ok`.
