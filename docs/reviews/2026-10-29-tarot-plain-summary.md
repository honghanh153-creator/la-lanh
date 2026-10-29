# Tarot: plain summary and headlines (29/10/2026)

**Status: implemented on branch `feat/tarot-plain-summary` for exact-SHA review; not merged, not released.**
The owner's reading of the samples below is still needed before release (fallback approval rule).

## Why

Owner feedback in chat, 29/10/2026, on a framed work reading: "chỗ content tarot vẫn kỳ lắm, đưa và sửa thêm
đi". The quoted reading showed these problems:

| Problem | Source |
|---|---|
| The headline named two of five cards ("Năm Cốc và Át Kiếm soi một điều…") and said nothing. | `stance.HEADLINES` / `ROAST_HEADLINES` with `{pair}` / `{focal}` |
| Every sentence had a card as its subject ("Ngôi Sao cho thấy…", "Át Kiếm nhắc rằng…"). | `stance._role_sentence` |
| Linking words implied causes that do not exist ("Từ đó mà, Ba Gậy gợi ý…", "Thế nên, Năm Cốc…"). | `stance.CONJUNCTIONS` / `ROAST_CONJUNCTIONS`, gate `summary_links_cards` (N−1 links) |
| The summary repeated every position block below it, about 110–130 words. | one sentence per role |
| Two different "gợi ý bạn có thể…" steps, and the summary's step could differ from the step actually shown. | the summary used the card's resource; the step position may show the T02/T03 step |
| The Roast opener ("Tóm gọn cho người đang ôm việc tới cổ, không vòng vo nha.") came before a long summary. | `voice.SUMMARY_OPENERS` |

## What changed (renderer v9, gates v6; readings stored under v8 keep their text)

- **Summary** (`stance.plain_summary`):
  - **What it covers:**
    - the first core role ("Điểm chính: …");
    - both options of a choice ("Hướng A: …. Đổi lại, dễ …."), otherwise the first pitfall ("Có điều, bạn dễ …");
    - then the step the reader sees at the step position ("Trước hết, …").
  - **Rules:**
    - no card names and no linking words between unrelated cards;
    - the goal lead and the timing readiness line stay;
    - other roles stay only in their own blocks.
- **Gate `summary_plain`** (replaces `summary_links_cards`): the summary carries each summarized role's text and
  the shown step, and names no card. Luna's synthesis is held to the same gate. Its instruction now says the
  synthesis names no card and ends on the same step.
- **Headlines** carry the form and the lean (or topic), without card names. Stance markers, "sẵn sàng" for timing,
  no advice words, three frames per key per register: all kept.
- **Roast opener**: only legacy (unframed) readings still get it.
- **Measurement (US-20 AC11, spec T2)**: the 10% duplicate ceiling now applies to the opening (headline +
  summary). Headlines alone repeat by design, at about 88%, and that rate is still reported.
- **Bank results (tarot:audit):**
  - opening duplicates 0.23–0.89%;
  - every direct-voice provider payload traced (5,340);
  - the psychology checklist passes on all 7,104 framed readings;
  - T4 0.99.

## Samples: before (integration `e0d62fa`, renderer v8)

```
### Mình cần nhìn rõ điều gì trong công việc lúc này? · five_clarity · work · roast
HEADLINE: Năm Cốc và Át Kiếm: điều đáng soi kỹ trong công việc, khỏi vòng vo.
SUMMARY (124 chữ): Tóm gọn cho người đang ôm việc tới cổ, không vòng vo nha. Ngôi Sao cho thấy một tiến bộ nhỏ có thể giúp bạn tin lại vào hướng làm đang sửa. Có điều nè, Át Kiếm nhắc rằng bạn dễ nói lỗi quá chung khiến người thực hiện không biết sửa đâu. Thêm nữa nè, Bốn Tiền cho thấy giữ nguồn lực ổn định cần phân biệt khoản dự phòng với việc giữ quá chặt. Từ đó mà, Ba Gậy gợi ý bạn có thể kiểm tra phản hồi cho đề xuất đã gửi trước khi mở thêm phạm vi. Thế nên, Năm Cốc gợi ý bạn có thể tách phần không đạt khỏi tài liệu hoặc kỹ năng có thể giữ lại.

### Mình cần nhìn rõ điều gì trong công việc lúc này? · five_clarity · work · straight_warm
HEADLINE: Năm Cốc và Át Kiếm: điều đáng nhìn rõ trong công việc.
SUMMARY (109 chữ): Ngôi Sao cho thấy một tiến bộ nhỏ có thể giúp bạn tin lại vào hướng làm đang sửa. Có điều, Át Kiếm nhắc rằng bạn dễ nói lỗi quá chung khiến người thực hiện không biết sửa đâu. Bên cạnh đó, Bốn Tiền cho thấy giữ nguồn lực ổn định cần phân biệt khoản dự phòng với việc giữ quá chặt. Từ đó, Ba Gậy gợi ý bạn có thể kiểm tra phản hồi cho đề xuất đã gửi trước khi mở thêm phạm vi. Vì vậy, Năm Cốc gợi ý bạn có thể tách phần không đạt khỏi tài liệu hoặc kỹ năng có thể giữ lại.

### Mình có nên nhắn lại cho bạn ấy không? · three_unblock · relationships · playful_grounded
HEADLINE: Tiết Chế: chuyện nhắn lại còn kéo về hai phía.
SUMMARY (57 chữ): Hai Cốc cho thấy muốn việc lắng nghe và đáp lại đến từ cả hai phía. Có điều, Bảy Kiếm nhắc rằng bạn dễ giữ thông tin để kiểm soát câu trả lời của người kia. Vì vậy, Tiết Chế gợi ý bạn có thể thống nhất một cách liên lạc mà cả hai thấy thoải mái.

### Mình có nên nghỉ ngơi sớm hơn tối nay không? · one_focus · self_care · roast
HEADLINE: Ẩn Sĩ: chuyện nghỉ ngơi còn kéo về hai phía.
SUMMARY (47 chữ): Tóm gọn nhẹ nhàng, không ai bắt bạn phải gồng đâu. Khi cần nghỉ, chọn một khoảng có thể dừng việc thay vì chờ mọi thứ xong hết. Ẩn Sĩ cho thấy khoảng riêng giúp bạn nghe được mong muốn không bị ý kiến khác lấn át.

### Mình nên nhận lời hay từ chối dự án mới? · five_choice · work · straight_warm
HEADLINE: Công Lý: các lá nghiêng về thử từ chối.
SUMMARY (130 chữ): Tám Tiền cho thấy luyện kỹ năng qua từng lần sửa giúp chất lượng công việc chắc hơn. Thêm nữa, Mười Gậy: hướng này được khối lượng đang ôm cần được giảm hoặc chia lại. Đổi lại, hướng này dễ làm thay mọi người để giữ tiến độ rồi không ai thấy bạn quá tải. Bên cạnh đó, Sáu Cốc: hướng này được kinh nghiệm cũ có thể hữu ích khi được xét trong điều kiện hiện tại. Đổi lại, hướng này dễ lặp cách từng thành công mà không xem yêu cầu mới. Có điều, Hai Kiếm nhắc rằng bạn dễ đợi mọi rủi ro biến mất rồi mới chọn. Vì vậy, Công Lý gợi ý bạn có thể kiểm tra kết quả theo yêu cầu đã thống nhất.
```

## Samples: after (renderer v9)

```
### Mình cần nhìn rõ điều gì trong công việc lúc này? · five_clarity · work · roast
HEADLINE: Chuyện công việc, nói gọn nè.
SUMMARY (49 chữ): Điểm chính: một tiến bộ nhỏ có thể giúp bạn tin lại vào hướng làm đang sửa. Có điều, bạn dễ nói lỗi quá chung khiến người thực hiện không biết sửa đâu. Trước hết, tách phần không đạt khỏi tài liệu hoặc kỹ năng có thể giữ lại.

### Mình cần nhìn rõ điều gì trong công việc lúc này? · five_clarity · work · straight_warm
HEADLINE: Điều đáng nhìn rõ trong công việc lúc này.
SUMMARY (49 chữ): Điểm chính: một tiến bộ nhỏ có thể giúp bạn tin lại vào hướng làm đang sửa. Có điều, bạn dễ nói lỗi quá chung khiến người thực hiện không biết sửa đâu. Trước hết, tách phần không đạt khỏi tài liệu hoặc kỹ năng có thể giữ lại.

### Mình có nên nhắn lại cho bạn ấy không? · three_unblock · relationships · playful_grounded
HEADLINE: Chuyện nhắn lại còn kéo về hai phía.
SUMMARY (52 chữ): Điểm chính: muốn việc lắng nghe và đáp lại đến từ cả hai phía. Có điều, bạn dễ giữ thông tin để kiểm soát câu trả lời của người kia. Trước hết, gõ tin bạn định gửi vào ghi chú, ba mươi phút sau đọc lại rồi mới chọn gửi hay sửa.

### Mình có nên nghỉ ngơi sớm hơn tối nay không? · one_focus · self_care · roast
HEADLINE: Chuyện nghỉ ngơi còn kéo về hai phía.
SUMMARY (49 chữ): Khi cần nghỉ, chọn một khoảng có thể dừng việc thay vì chờ mọi thứ xong hết. Điểm chính: khoảng riêng giúp bạn nghe được mong muốn không bị ý kiến khác lấn át. Trước hết, khi mắt bắt đầu cay, gập máy lại và nằm xuống mười phút.

### Mình nên nhận lời hay từ chối dự án mới? · five_choice · work · straight_warm
HEADLINE: Các lá nghiêng về thử từ chối.
SUMMARY (101 chữ): Điểm chính: luyện kỹ năng qua từng lần sửa giúp chất lượng công việc chắc hơn. Hướng A: khối lượng đang ôm cần được giảm hoặc chia lại. Đổi lại, dễ làm thay mọi người để giữ tiến độ rồi không ai thấy bạn quá tải. Hướng B: kinh nghiệm cũ có thể hữu ích khi được xét trong điều kiện hiện tại. Đổi lại, dễ lặp cách từng thành công mà không xem yêu cầu mới. Trước hết, ghi một dòng: buổi tối nay dành cho việc gì của bạn; lời nhờ nào chạm vào đó thì trả lời không.
```

## Not changed here (next pass, with the owner)

- **Position blocks** still use "lead + label: card text" ("Nhìn chung, bằng chứng thật: …"), with the label
  repeating the position header.
- **Some card × topic lines read badly**, for example Bốn Tiền · work: "giữ nguồn lực ổn định cần phân biệt khoản
  dự phòng với việc giữ quá chặt".
- Fixing both means reworking 78 cards × 6 topics × 3 fields with the owner, as content.
- The T02/T03 context limit (recipient binding) and T05 stay open.
