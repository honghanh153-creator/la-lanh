# Market research: "Tháng này có gì mới" (monthly feature) — 2026-10-11

Read-only web research. No source code changed. No sign-in, purchase or installer download.
Not legal advice. Companion doc (repo feasibility, data model, retention, engine gaps):
`docs/research/2026-10-11-monthly-feature-feasibility.md`.

Revision 2026-10-12: addresses review of PR #9 (guest storage and recap window, legal sources,
Rule 3 dates, source critique). The v1/v2 direction below is still an **unconfirmed
recommendation**. The owner must pick a direction and create a user story with AC and DoD before
anything is built.

Revision 2026-10-22: retention re-checked against the current target `collab/integration` @
`c3fab3311d65` (includes `5f3eded`, automatic Daily notes kept at most 24 hours). Daily notes and
their moods are no longer a 29-day recap input; the recap section below is updated. The 2026-10-12
corrections stand. No TTL is extended and nothing monthly is built in this PR.

---

## Tóm tắt tiếng Việt

**Thị trường làm gì với "tháng"** (mẫu khoảng 11 app đã tra, không phải toàn thị trường):
- Trong mẫu này, phần lớn app chiêm tinh lớn **không có màn "tháng này" riêng**. Co–Star chỉ có note ngày và bán "Your Year Ahead". CHANI có bài đọc theo tuần, và bản 2026 có "month-by-month" cùng lịch "key dates" (trăng mới/tròn, nghịch hành, nhật/nguyệt thực). The Pattern dùng **timeline chu kỳ cá nhân**. TimePassages và Astro Future có **danh sách mốc quan trọng**. Moonly, Stardust và Labyrinthos xoay quanh **chu kỳ trăng**. Sanctuary và Nebula bán tử vi ngày/tuần/tháng/năm **theo 12 cung**.
- Ở Việt Nam, khung "tháng" mặc định là **Lịch Vạn Niên**: lưới tháng âm/dương, rằm/mùng một, **ngày tốt/xấu, giờ hoàng đạo**. Lá Lành phải tránh đúng mô thức này.

**Bằng chứng:** Không có số liệu công khai đáng tin nào so sánh nội dung tháng với nội dung ngày.
- "Fresh start effect" (Dai, Milkman & Riis 2014) đo các mốc thời gian như đầu tuần/tháng/năm, học kỳ, sinh nhật, ngày lễ. Bài **không** nghiên cứu trăng mới. "Trăng mới là một mốc làm mới" chỉ là **giả thuyết cần thử**.
- Spotify Wrapped 2025 là case về **chia sẻ**: hơn 200 triệu người xem ít nhất một story trong 24 giờ; hơn 500 triệu lượt chia sẻ, tính cả ảnh chụp màn hình và tải về. Lượt chia sẻ không phải số người riêng biệt, và nguồn không có số liệu giữ chân hay ROI.
- Recap kiểu "fun facts" khó duy trì (Gentler Streak đã bỏ).

**Dữ liệu và recap (đã đối chiếu code):** Máy chủ giữ note ngày, mood, thí nghiệm hành động và tarot theo từng hồ sơ (`guest_id`, kể cả khách). Theo target hiện tại (`c3fab3311d65`), **note ngày tự động bị ẩn sau 24 giờ và đủ điều kiện xóa từ 18 giờ** (trừ note hôm nay, note đã lưu và note còn việc nhỏ/phản hồi/link chia sẻ chưa hết hạn); **mood mất theo note cha**. Note đã lưu (và mood của chúng), thí nghiệm và tarot bị xóa vật lý khi đủ 29 ngày 18 giờ, ở lần dọn đầu tiên sau đó (job chạy mỗi 6 giờ). Lời hứa là "tối đa", **không phải "giữ đủ"**. Thiết bị chỉ giữ cache trong bộ nhớ 36 giờ và vài marker đồng bộ, **không có kho lịch sử**. Vì vậy "tính trên thiết bị" chưa phải khả năng sẵn có. Có hai lựa chọn thật: (1) endpoint tổng hợp theo hồ sơ, đọc từ dữ liệu còn được phép giữ; (2) xây kho local mới, có thời hạn, xóa, đăng xuất và tách theo hồ sơ. Recap phải ghi rõ khoảng ngày thật có dữ liệu, ngày thiếu và ngày bắt đầu opt-in. Không coi ngày thiếu là "không hoạt động" hay mood bằng 0. Không âm thầm kéo dài thời hạn lưu.

**Pháp lý** (đã đọc trang scan của PDF ký chính thức và toàn văn trên CSDL quốc gia; tách rõ điều luật và suy luận):
- Luật 91/2025/QH15 Điều 9: đồng ý phải tự nguyện, biết rõ, thể hiện rõ ràng, kiểm chứng được, **theo từng mục đích**, không ép đồng ý mục đích khác; im lặng không phải đồng ý. Điều này không cấm một màn hình hỏi nhiều mục đích nếu từng lựa chọn độc lập. Điều 10: quyền rút lại đồng ý.
- Nghị định 356/2025 Điều 4 khoản 1: dữ liệu nhạy cảm gồm đời sống riêng tư (điểm c), tình trạng sức khỏe (điểm d) và **dữ liệu theo dõi hành vi, hoạt động sử dụng dịch vụ trên không gian mạng (điểm l)**. Recap về việc dùng app nhiều khả năng thuộc nhóm (l), dù mood có được coi là sức khỏe hay không. Tổng hợp còn gắn với hồ sơ thì **không phải dữ liệu ẩn danh**.
- Luật Quảng cáo (VBHN 88/VBHN-VPQH, đã gồm Luật 75/2025) Điều 8: khoản 3 nay là "trái với truyền thống lịch sử, văn hóa, đạo đức xã hội"; khoản 9 cấm quảng cáo sai hoặc gây nhầm lẫn về công dụng; khoản 11 cấm "nhất/duy nhất" khi không có chứng minh. Nghị định 87/2026/NĐ-CP (hiệu lực 15/05/2026) **thay Nghị định 38/2021** về xử phạt văn hóa và quảng cáo.
- "Miễn phí" hay "tự soi" **không** làm sản phẩm an toàn về pháp lý. Bộ luật Hình sự Điều 320 là vấn đề riêng. Các điểm cần luật sư được đánh dấu ở mục 4.

**Mốc thời gian (Quy tắc 3):** Giữ **ngày xảy ra hiện tượng bầu trời** (có nguồn tính, múi giờ, độ chính xác). Không gọi đó là ngày tốt/xấu, hạn chót cho việc đời thường, hay dự báo cảm xúc lên/xuống. Chủ sản phẩm phải sửa Quy tắc 3 và ví dụ trong product plan trước khi triển khai.

**Khuyến nghị (chưa chốt):** v1 bắt đầu từ **mốc bầu trời chung, không cần ngày sinh**: tối đa 4 mốc, chỉ mô tả, theo quy tắc chọn cố định. Thêm **nhịp trăng** (ý định nhỏ lúc trăng mới, nhìn lại lúc trăng tròn). Lớp cá nhân chỉ dựng từ dữ liệu thật; chỉ giờ sinh EXACT mới có nhà. v2 là **recap "Tháng của bạn"**: đồng ý recap riêng, đồng ý chia sẻ riêng, xem trước và sửa trước khi chia sẻ, mặc định không chia sẻ. Đo "có ích, dễ hiểu, không bị hiểu là dự báo" trước, rồi mới đo tỷ lệ quay lại.

---

## 1. What competitors show for monthly content

Legend: ✅ confirmed by the source cited · ◐ partial or adjacent · — not found in the sources checked.

| App | Monthly horoscope text | Lunations (new/full) | Retrogrades / ingresses | Personal transit timeline | Eclipse season | Month recap of own data | New-moon intention | Monthly / moon tarot |
|---|---|---|---|---|---|---|---|---|
| Co–Star | — (daily only; paid "Your Year Ahead") | — | — | ◐ | — | — | — | — |
| The Pattern | — | — | ◐ "Cosmic Climate" | ✅ cycles with peak dates | — | — | — | — |
| CHANI | ✅ month-by-month (2026) | ✅ | ✅ | ✅ Transits tab | ✅ | — | ◐ rituals + journal prompts | ◐ tarot in weekly rituals |
| Sanctuary | ✅ by sign | — | — | — | — | — | — | ◐ daily draw |
| Nebula | ✅ by sign | ◐ | — | — | — | — | — | — |
| Moonly | — | ✅ lunar calendar | ✅ retrograde guidance | ◐ "green-light windows" | ◐ | — | ✅ | ◐ |
| TimePassages | — | ✅ (free) | ✅ Mercury Rx, VOC Moon; printed AstroCal | ✅ transit bi-wheels | ◐ | — | — | — |
| Astro Future | — | ◐ | ✅ key-date list | ✅ time scrubber | ✅ | — | — | — |
| Labyrinthos | — | ◐ | — | — | — | ◐ "mirror" report over a period | — | ✅ 8 moon-phase spreads |
| Stardust | — | ✅ moon ring | — | — | — | ◐ cycle-vs-moon "synchronicity" | — | — |
| Lịch Vạn Niên (VN) | — | ✅ rằm / mùng một | — | — | — | — | — | — |

### Concrete UI patterns observed

1. **Key-dates list / calendar.**
   - CHANI's 2026 release added "updated key date calendars" and "month-by-month breakdowns". Its site groups key dates into Big Moments, Major Transits & retrogrades, New & Full Moons, Eclipses and Mercury Retrogrades.
   - Astro Future flags eclipses, solstices, retrogrades and "planetary birthdays". One reviewer called it the most concise list of significant dates for the year.
   - TimePassages sells a printable monthly "Astro Calendar" with moon phases, ingresses and aspect patterns.
2. **Personal timeline with start / peak / end.** The Pattern's Timing tab (now "Your Transits") lists personal cycles, such as a six-month "identity transformation", each with forecasts and peak dates. It also hosts a place to "share your experience" with other users.
3. **Moon ring / phase strip.** Stardust's home screen is a ring of lunar phases. Moonly is built around a lunar calendar with Full Moon rituals and New Moon intentions.
4. **Phase-specific spread.** Labyrinthos offers eight Moon Phase Tarot Spreads, plus a journal and a "mirror" report that aggregates readings over a period.
5. **Weekly cadence rather than monthly.** CHANI's anchor is the weekly reading and podcast. Reviewers describe a Sunday listening routine. New and full moons, retrogrades and eclipses are delivered as weekly rituals, tarot, journal prompts and audio.
6. **By-sign periodic text.** Sanctuary and Nebula offer daily, weekly, monthly and annual horoscopes per sign, shareable to social media.
7. **Vietnamese month grid.** Lịch Vạn Niên shows a month grid of lunar and solar dates with rằm and mùng một markers. Its day detail covers hoàng đạo / hắc đạo days, giờ hoàng đạo, good and bad stars, and suitable days for weddings, openings and moving. Lịch Như Ý adds 12 con giáp, 12 cung hoàng đạo and numerology. This **good/bad-day grid is the default Vietnamese mental model for "this month"**, and it is precisely the deterministic pattern Lá Lành must not reproduce.
8. **Deterministic timing language in Western apps too.** Moonly advertises "personal green-light windows" for big decisions. Its personal astrologer answers whether to cut your hair or go on a date on a given day. The Lá Lành product plan v2 contains the same anti-pattern ("thời điểm tốt để nộp đơn", Rule 3 "deadline"). The feasibility doc flags it for rewrite.

**Takeaway (sample only):** None of the 11 apps checked combines (a) the collective sky of the month, (b) where it touches *your* chart, and (c) your own month, in one non-predictive surface. CHANI comes closest but is paywalled ($11.99/mo) and leans on "manifestation" and ritual language. This is a sample of well-known apps from store listings and reviews, not a market-wide survey. It suggests a possible opening for a plain-language, agency-first month view; it does not prove a market gap.

### Sources (Q1)
- CHANI App Store listing (features, 2026 update, reviews): https://apps.apple.com/us/app/-/id1532791252
- CHANI blog, "6 ways the CHANI app can help you make sense of this month's astro mess": https://www.chani.com/blogs/6-ways-the-chani-app-can-help-you-make-sense-of-this-months-astro-mess
- CHANI New Moon practice interview: https://www.mashupamericans.com/?p=15752
- Co–Star App Store listing (daily-only description; IAPs including "Your Year Ahead"): https://apps.apple.com/app/id1264782561
- The Pattern review (Timing tab, cycles, peak dates): https://www.bustle.com/life/pattern-app-review-features-price
- The Pattern listing text mirror ("Your Transits", "Cosmic Climate"): https://www.apkmirror.com/apk/pattern-home-inc/the-pattern/
- TimePassages App Store: https://apps.apple.com/us/app/timepassages-astrology/id488946918
- Astro Future App Store: https://apps.apple.com/us/app/-/id1119123378
- Astro Future key-dates review: https://www.yogajournal.com/lifestyle/astrology/best-astrology-app/
- Moonly App Store (lunar calendar, rituals, "green-light windows", paywall reviews): https://apps.apple.com/US/app/id1489889871
- Moonly review: https://www.bustle.com/life/moonly-astrology-app-review
- Labyrinthos App Store (journal, mirror report, spreads): https://apps.apple.com/us/app/-/id1155180220
- Labyrinthos review: https://www.bustle.com/life/labyrinthos-tarot-reading-app-review
- Labyrinthos feature-request board (moon widget requested, so not built in): https://feedback.labyrinthos.co/b/kvj5dqme/feature-ideas
- Stardust review: https://www.bustle.com/wellness/stardust-app-review-period-tracking-astrology
- Sanctuary App Store: https://apps.apple.com/app/id1417411962
- Nebula App Store: https://apps.apple.com/app/id1459969523
- Nebula periodic horoscopes (roundup): https://www.igeeksblog.com/best-horoscope-apps-for-iphone-ipad/
- Lịch Vạn Niên (Âm Lịch) App Store: https://apps.apple.com/us/app/id877914778
- Lịch Như Ý App Store: https://apps.apple.com/us/app/-/id797395252
- Lịch Việt App Store: https://apps.apple.com/app/id980481486
- VN app roundups (secondary): https://fptshop.com.vn/tin-tuc/for-gamers/app-xem-tu-vi-206364 and https://voh.com.vn/apps/5-ung-dung-lich-am-tien-dung-cho-dien-thoai-android-va-ios-392032.html

---

## 2. Engagement / retention evidence, and what users complain about

### Evidence quality warning
No primary, public retention data compares monthly with daily content for astrology apps. The circulating figures cannot be traced to a source and should not be used in planning:
- Co–Star "45% retention", "1M DAU": Analytics Insight, no source given. https://www.analyticsinsight.net/artificial-intelligence/best-ai-powered-horoscope-apps
- "30–40% DAU" for astrology apps: Apptunix, a vendor blog. https://www.apptunix.com/blog/how-to-develop-an-astrology-app-like-co-star/

### What is defensible
- **Temporal landmarks motivate fresh starts.** Dai, Milkman & Riis (2014, *Management Science* 60(10), doi:10.1287/mnsc.2014.1901) ran three archival field studies. Google searches for "diet", gym visits and goal commitments all rose after temporal landmarks: the start of a new week, month, year or semester, a birthday, or a holiday. The paper does not study lunar phases. The full text has no mention of the Moon (checked by text search of the author-hosted PDF). It supports a **beginning-of-month** moment. That a **new moon** works as a fresh-start landmark, or raises retention in an astrology app, is a hypothesis to test, not a finding. https://faculty.wharton.upenn.edu/wp-content/uploads/2014/06/Dai_Fresh_Start_2014_Mgmt_Sci.pdf
- **Weekly cadence anchors habit in a paid astrology app.** CHANI reviewers describe a Sunday routine around the weekly reading (App Store reviews, above). That is anecdotal but consistent.
- **Monthly self-data reports are an established journaling pattern.**
  - Daylio sends a monthly report notification with charts and "Most Influential Activities".
  - Its "Year in Pixels" can be exported as an image to share.
  - Sources: https://www.apkmirror.com/apk/habitics/daylio-diary-journal-mood-tracker/daylio-diary-journal-mood-tracker-1-37-0-release/ and https://daylio.net/
- **Novelty recaps decay.** Gentler Streak, a fitness app that markets itself as anti-streak, dropped its fun-facts monthly recap because it "was no longer that fun nor sustainable from a production standpoint". It replaced it with a data recap users can compare month to month. https://9to5mac.com/2024/04/05/gentler-streak-monthly-activity-recap/
- **Vietnam takes horoscopes unusually seriously.** YouGov APAC found that 75% of Vietnamese respondents take horoscopes seriously, the highest in the region. It also found that 33% of all respondents have changed behaviour because of a horoscope. Fieldwork was in August 2017, so the data is old. This raises the duty of care against predictive framing. https://business.yougov.com/content/19426-horoscope-and-behaviour-change
- **Qualitative research.** A 2026 interpretative phenomenological study of young adults (20–28) using astrology and tarot apps found self-care use. Participants also noted the "risk of encountering negative predictions". https://researchdiscovery.drexel.edu/esploro/outputs/journalArticle/Young-adults-using-apps-for-alternative/991022152825004721

### Complaint themes (review sentiment)
1. **Paywalls and upsell creep.** This is the top theme.
   - Co–Star reviewers call it "essentially 'bricked'" behind its subscription (App Store).
   - Unstar's May 2026 qualitative pull of 1–2-star reviews says Co–Star push cadence rose to 2–3 a day, with upsells disguised as horoscope previews.
   - The same pull found Nebula trial-to-weekly billing and The Pattern cancellation friction.
   - Moonly reviewers say "more than half the meditations are locked".
   - Unstar is a competitor-ranking site, so treat it as directional. https://unstar.app/blog/co-star-sanctuary-pattern-nebula-stellium-astrology-apps-ranked-2026
2. **Generic or recycled content.**
   - Co–Star: "a couple of repeats" in a year.
   - The Pattern: "the same five descriptors recycle across friends".
   - Nebula: weekly predictions repeat with small wording changes (Unstar).
   - CHANI: content "became too general" compared with chart-based forecasts (App Store review).
3. **Negative or fear tone.**
   - Co–Star's daily alerts are widely described as cryptic and negative. https://ixd.prattsi.org/tag/astrology and https://reneemillette.substack.com/p/what-the-heck-is-going-on-with-my
   - Culture pieces document retrograde blame and the anxiety of "waiting for" Mercury retrograde.
   - CHANI's own monthly marketing leads with "pretty messy" before reassuring readers.
   - Sources: https://www.reaction.life/p/sign-of-the-times-astrologys-millennial-revival, https://www.aol.com/life-feels-mess-yes-mercury-050000829.html and the CHANI blog above.
4. **Deterministic or unverifiable predictions.**
   - Users praise accuracy ("so spot on accurate", CHANI review). The same users then complain when generalisation breaks the illusion.
   - The Pattern compatibility scores reportedly change for the same pair on different days (Unstar).

**Implication for Lá Lành:** The monthly surface must not become (a) another paywall teaser, (b) 12-sign generic text, (c) a retrograde warning, or (d) a push-volume lever. These are the four most-complained-about patterns.

---

## 3. Gen Z shareability: monthly / periodic recap formats

What the evidence supports:
- **Spotify Wrapped is a sharing case, not retention evidence.**
  - Wrapped 2025 had more than 200M "engaged users" in its first 24 hours (it took 62 hours in 2024). An engaged user is someone who viewed at least one Wrapped story.
  - It had more than 500M shares, up 41%. That count includes native in-app shares plus screenshots and downloads. It counts share events, not distinct people who shared, and there is no breakdown by channel.
  - The source reports no retention, churn, subscription or revenue effect. Nothing here estimates the return or ROI of a recap for a small beta.
  - 2025 formats leaned on **comparison and identity labels**: "listening age", listener category and a multiplayer "Wrapped Party".
  - Source: https://techcrunch.com/2025/12/04/spotify-says-wrapped-2025-is-its-biggest-yet-with-200m-users-in-its-first-day
- **Why recaps get shared** (marketing analysis, not peer-reviewed):
  - Each slide is pre-formatted for Stories.
  - The content is about the user, not the brand, so sharing feels like self-expression.
  - It balances belonging with uniqueness.
  - Sources: https://nogood.io/2025/01/20/spotify-wrapped-marketing-strategy/ and https://www.psychologs.com/the-psychology-behind-your-spotify-wrapped/
- **Caveat.** The same analyses report "Wrapped anxiety", where users curate behaviour for the recap. That is a direct conflict with Lá Lành's no-guilt rule.
- **Co–Star's viral loop was the screenshot of one blunt line** in a recognisable boxed frame, such as "drink water". https://dailydot.com/co-star-astrology-app-push-notifications-memes
- **Monthly recaps are spreading to platforms.** Instagram is testing a Story-style monthly Insights recap. https://www.socialmediatoday.com/news/instagram-monthly-stats-performance-recap/744691/
- **Vendor case studies** report lifts from personality-label recaps. Dreams reported +200% engagement and HomeExchange a 66.9% open rate. These come without control groups, so treat them as directional. https://storyly.io/personalized-wrapped and https://inappstory.com/case-studies/case-study-stories-homeexchange

Design principles for Lá Lành month cards (synthesis):
1. **One identity-ish line, not a score.** For example, "Tháng 10 của bạn: tháng chọn ít mà chắc". Avoid counts that shame, such as "bạn mở app 3/31 ngày".
2. **Screenshot-native 9:16 card**, with one sentence that still makes sense to someone without the app.
3. **Sky content is the safest share; self content shares only by explicit choice.** Nothing is shared by default. The user previews and can edit the card before sharing. A card should never include mood, notes, intention text or birth data. A "theme only" line can still reveal private life, so it also needs preview. Copy must say that screenshots and downloaded images cannot be revoked. US-18 (DEFERRED since 2026-09-20, pool recap) is a reference for tone and privacy principles only. Its AC are not AC for a monthly feature.
4. **Comparison as play, not ranking.** "Bạn và bạn thân cùng tháng trăng mới ở nhà 5" is fine. "Ai may mắn hơn" is not.
5. **Low production cost per month.** This is the Gentler Streak lesson: the template must be generated from data and a reviewed content matrix, not hand-written monthly.
6. **Public share links follow AGENTS.md**: no-index, no cache, tokens out of logs and referrers, and revocable.

---

## 4. Ethical and regulatory angles (official sources first)

### Vietnam

**How the sources were read.** The signed PDFs of Law 91/2025/QH15, Decree 356/2025/NĐ-CP and the
consolidated Advertising Law VBHN 88/VBHN-VPQH are image scans with no text layer. The relevant pages
were rendered to images and read visually. No OCR was run, so quotations below were transcribed by
hand and should be re-checked against the PDF before reuse in user-facing copy. Decree 87/2026/NĐ-CP
was read as full text on the national legal database (vbpl.vn). Each item separates **Text** (what the
article says) from **Inference** (what this research concludes for the product). Inferences are not
legal conclusions. Items marked **[counsel]** need legal review. Not legal advice.

**Personal data: Law 91/2025/QH15** (signed PDF:
https://datafiles.chinhphu.vn/cpp/files/vbpq/2025/7/91qh.signed.pdf; effective 2026-01-01; official
metadata: https://congbao.chinhphu.vn/van-ban/luat-so-91-2025-qh15-45578.htm).
- **Text, Art. 2(11) (p. 2):** de-identification (*khử nhận dạng*) means changing or deleting
  information to create new data that cannot identify, or help identify, a specific person.
- **Text, Art. 3(2)–(3) (p. 2):** collect and process only within a specific, clear scope and purpose.
  Keep data for a period appropriate to the processing purpose, unless the law says otherwise.
- **Text, Art. 9 (p. 6):**
  - (2) Consent is valid only if it is voluntary and the person knows the data type and purpose, the
    controller, and their rights and obligations.
  - (3) Consent is expressed clearly and specifically, in a form that can be printed or copied in
    writing, including electronic or verifiable formats.
  - (4)(a) Consent is given for each purpose (*"đối với từng mục đích"*).
  - (4)(b) It must not be conditioned on mandatory consent to purposes other than the agreed content.
  - (4)(c) It lasts until the person changes it or the law provides otherwise.
  - (4)(d) *"Sự im lặng hoặc không phản hồi không được coi là sự đồng ý."*
- **Text, Art. 10 (pp. 6–7):** the person may withdraw consent or ask to restrict processing. The
  request is made in writing, including electronic or verifiable form. The controller must act on it
  within the time set by law. Withdrawal does not apply to processing done before the request (10(4)).
- **Text, Art. 11 (p. 7):** consent comes before collection unless the law provides otherwise (11(1)).
  Non-state organisations may analyse and aggregate personal data only from sources they are permitted
  to process (11(3)).
- **Inference:**
  - A monthly recap is a new processing purpose (aggregating a person's use of the app into a
    summary). It needs its own opt-in, separate from the daily note, mood and share consents.
  - Art. 9(4) requires a separate choice per purpose. It does not forbid one screen that lists several
    purposes, as long as each has an independent control and refusing one does not block the others.
  - Withdrawal must stop new aggregation. Because Art. 3(3) ties retention to purpose, any stored
    recap or derived aggregate should be deleted when the recap consent is withdrawn, the source data's
    basis lapses, or the profile is deleted. **[counsel]** on whether Art. 10(4) permits keeping
    already-produced recaps.
  - A recap theme, mood distribution or count of experiments is **derived personal data** while it is
    linked to an owner ID. It is not de-identified under Art. 2(11), and it is not "anonymous".

**Personal data: Decree 356/2025/NĐ-CP** (signed PDF:
https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/01/356-nd.signed.pdf; listing:
https://vanban.chinhphu.vn/?docid=216387&pageid=27160). It replaces Decree 13/2023/NĐ-CP as the
implementing decree (per PwC Vietnam and EY alerts:
https://www.pwc.com/vn/vn/publications/2026/20260128-new-rules-personal-data-protection.pdf and
https://www.ey.com/vi_vn/technical/tax/tax-and-law-updates/nghi-dinh-so-356-2025-nd-cp-quy-dinh-chi-tiet-mot-so-dieu-va-bien-phap-thi-hanh-luat-bao-ve-du-lieu-ca-nhan).
The repeal clause itself was not read in this pass.
- **Text, Art. 3 (p. 2):** basic personal data includes date of birth (3(2)) and place of birth (3(4)).
- **Text, Art. 4(1) (pp. 2–3):** sensitive personal data includes, among others:
  - (c) information about private life, personal secrets and family secrets;
  - (d) health status;
  - (h) location determined through location services;
  - (l) *"Dữ liệu theo dõi hành vi, hoạt động sử dụng dịch vụ viễn thông, mạng xã hội, dịch vụ truyền
    thông trực tuyến và các dịch vụ khác trên không gian mạng"*.
- **Text, Art. 4(2) (p. 3):** when processing sensitive data, organisations must set access-permission
  rules, processing procedures and security measures.
- **Inference:**
  - A recap of opens, notes saved, experiments tried and tarot draws is plausibly **behaviour/service-use
    tracking data under point (l)**. This holds regardless of whether mood counts as health data. The
    repo already treats service-usage tracking as sensitive in the companion-growth module.
  - A five-value mood enum is not by itself diagnostic health data. Whether it falls under (c) or (d)
    depends on the actual content and purpose. **[counsel]**
  - Product analytics events for the monthly surface are also usage tracking. Keep them content-free
    and minimal, and declare them.
  - Art. 4(2) means owner-scoped access, a written processing procedure and security controls for any
    recap path, not only consent.

**Advertising: consolidated Advertising Law, VBHN 88/VBHN-VPQH** (PDF:
https://datafiles.chinhphu.vn/cpp/files/vbpq/2025/8/88-vbhn-vpqh.pdf). It reflects the amendments by
Law 75/2025/QH15, effective 2026-01-01.
- **Text, Art. 8 (p. 6):**
  - (3), amended by Law 75/2025 Art. 1(4)(a): advertising *"trái với truyền thống lịch sử, văn hóa,
    đạo đức xã hội"*. This replaces the older "thuần phong mỹ tục" wording.
  - (6): advertising that is discriminatory or infringes freedom of belief and religion.
  - (9): advertising that is untrue or misleading (*"không đúng hoặc gây nhầm lẫn"*) about, among
    other things, the quality, *công dụng* (utility) or manner of service of a product or service.
  - (10), amended by Law 75/2025 Art. 1(4)(b): comparison with others' products without lawful proof.
  - (11): "nhất", "duy nhất", "tốt nhất", "số một" or similar without lawful proof.
- **Inference:** No clause names astrology or horoscopes. The practical risk is marketing the monthly
  feature as predictive or accurate (for example "dự báo chính xác tháng của bạn"). That would be an
  untrue or misleading claim about the service's utility under (9), and a superlative under (11).
  Marketing copy needs evidence for every claim. **[counsel]** before launch marketing.

**Administrative sanctions: Decree 87/2026/NĐ-CP** on sanctions in culture and advertising (full text:
https://vbpl.vn/van-ban/chi-tiet/nghi-dinh-so-87-2026-nd-cp-quy-dinh-xu-phat-vi-pham-hanh-chinh-trong-linh-vuc-van-hoa-va-quang-cao--187899).
Issued 2026-03-27, effective 2026-05-15.
- **Text, Art. 93(2)(a):** it repeals Decree 38/2021/NĐ-CP. Planning must not rely on Decree 38/2021
  or on summaries of it.
- **Text, Art. 50 (advertising prohibited acts):**
  - (2)(a): fine of 10–20 million VND for unproven "nhất / duy nhất / tốt nhất / số một" claims;
  - (4)(d): fine of 40–60 million VND for advertising contrary to historical tradition, culture and
    social ethics;
  - (5)(c): fine of 80–100 million VND for untrue or misleading advertising about, among other things,
    a product's or service's *công dụng*.
- **Text, Art. 20 (festival organisation):** sanctions taking part in superstitious activity at a
  festival (20(4)(b)) and organising superstitious activity (20(8)(b)). These are in the festival
  context.
- **Not checked:** the article that sets fine levels for individuals versus organisations; other
  sanction decrees (for example on security and social order) that may cover superstitious practice
  outside festivals. **[counsel]**

**Criminal law: Criminal Code Art. 320** (practising superstition) is a separate criminal-law
question. It is not part of privacy or advertising compliance. Its official current text was not
retrieved in this pass. This research draws no safety conclusion from the product being free or
framed as "tự soi" (self-reflection). A free price or a disclaimer is not a licence for predictive
content. The controls that matter are product controls: no event prediction, no good/bad-day
calendars, and no paid remedies or "giải hạn". **[counsel]**

### Platforms
- **Apple App Review 4.3(b)** names "fortune telling" among saturated categories. New submissions must "offer a meaningfully different or improved experience". A non-predictive, self-reflection monthly feature supports that differentiation; a generic monthly horoscope weakens it.
- **Apple 5.1.1(ii) and 5.1.2(i)** require consent for collecting user or usage data and permission before using or sharing personal data. Source: https://developer.apple.com/app-store/review/guidelines/
- Any new persisted recap field must be reflected in Apple App Privacy, the Google Play Data Safety form and the in-app privacy copy (see `docs/legal/store-privacy-data-map.md`).

### Ethical design rules derived for the monthly surface
1. Describe the sky, not the user's fate. "Trăng tròn ngày X rơi vào vùng [nhà/cung] — vùng này nói về …" is acceptable. "Ngày X là ngày tốt để …" or "tránh ký hợp đồng" is not.
2. Retrograde and eclipse lines carry no warning, no "cẩn thận", and no blame attribution. This follows the repo reading-knowledge-spec rule that retrograde yields no psychological conclusion by itself. Do not infer good or bad times for communication or relationships from a station or retrograde.
3. No good/bad-day colouring on any calendar, which rules out the Lịch Vạn Niên pattern.
4. No "missed days" counts, streaks or "bạn đã bỏ lỡ"; an empty month is a neutral state.
5. Disclaimer and provenance on every sky claim, per the existing content gate.

### Proposed date contract (replaces the "Rule 3 deadline" framing)
An **astronomical event date** is different from an **action deadline**.
- **Keep:** the date (and, where precise enough, the time) a sky event happens. Examples: a lunation,
  a station, an ingress, or the computed start and end of a transit window. Each date carries its
  provenance (engine and version), timezone (ICT, stated) and precision (minute or day). See the
  feasibility doc for the receipt.
- **Never:** call a date good or bad; turn it into a deadline for life matters ("trước 13/11 hãy nộp
  đơn / tỏ tình"); say how long a life situation will last ("kéo dài đến tháng 8"); or predict that
  emotions will rise or fall around it. No urgency CTAs tied to sky dates.
- **Gate:** the owner must update Rule 3 (`docs/foundation/la-lanh-product-plan-v2.md:268-274`) and
  the "thời điểm tốt để nộp đơn" example (`:224`) before implementation. A UI disclaimer does not
  replace changing the rule.

---

## 5. Three concept options for "Tháng này có gì mới"

Shared constraints: guest-first; useful with no birth data at all; plain direct Vietnamese; one situation plus one small action; no predictions; no guilt or streaks; server-side Swiss Ephemeris.

### A. "Bầu trời tháng này": a sky strip of at most 4 key dates
- **UI:** A horizontal **strip** for the month showing at most 4 markers, chosen by a fixed rule (below). Tapping a marker opens a **key-date card** with:
  - what is happening in the sky (one line, with date and timezone);
  - optionally, where it touches the user, **only from data the user actually has** (see overlays);
  - one situation plus one small action, phrased as an invitation and never as timing advice.
- **Layer 1, no birth data (default):** the same sky events for everyone. This is the base of v1 and needs no personal data.
- **Overlays, only from real data:**
  - EXACT birth time: the lunation's natal house, as Sky Chapter does today (`TimePrecision.EXACT` only).
  - Date only: sign-level relations to natal bodies whose positions the date fixes. No houses. No "whole sign from the Sun" or other substitute houses.
  - No overlay is shown as more precise than its input.
- **Marker selection rule (deterministic, same for every user):**
  1. Every lunation whose ICT date falls in the month. Months with two new moons or two full moons show both. Copy is written per lunation, never for "the" new moon of the month.
  2. An eclipse is a lunation, so it replaces that marker instead of adding one. Eclipses are deferred from v1 until the solver is verified (feasibility doc).
  3. If slots remain: at most one station of Mercury, Venus or Mars, in that priority order, earliest first.
  4. If slots remain: the Sun's ingress.
  5. Outer-planet stations and other ingresses are not shown in v1.
  The personal overlay never changes which markers are chosen.
- **Caching:** only the non-personal monthly event list may go in a shared cache, keyed by month and engine version. Overlays are computed per owner on request, never shared-cached, and returned with `Cache-Control: no-store`.
- **Value:** Fresh, objectively true content every month that works for guests with no birth data. It differentiates from 12-sign generic text and gives an honest reason to add a birth time.
- **Risks:**
  - It is the closest of the three to predictive framing. The date contract above must be adopted first.
  - Retrograde and eclipse content can drift into fear.
  - Vietnamese users may read any dated calendar as "ngày tốt/xấu".
  - It needs an event solver plus a reviewed content matrix (events × signs, and × houses for EXACT, × direct/Roast).
- **Effort:** Medium. Needs an event solver with bracketed root finding and fixtures, a content matrix and the review gate. See the feasibility doc.

### B. "Tháng của bạn": a recap of the user's own notes, experiments and moods, plus one theme
- **UI:** A **story recap of 3–5 cards**:
  - the covered range and data kinds, stated first: for example "29 ngày, từ 14/10 đến 11/11; tính từ note đã lưu, việc nhỏ và tarot; có dữ liệu 9 ngày; bạn bật recap từ 20/10";
  - notes saved;
  - small actions tried, with the user's own "có ích / không" taps;
  - a mood distribution, only if mood logging and recap were both consented, labelled as covering saved notes only (automatic notes and their moods are deleted within about a day on the current target), or dropped;
  - one theme sentence, chosen from a reviewed bank by evidence and not generated freely;
  - an optional **month card** for sharing, off by default (see share rules).
- **Data model (verified in code; details in the feasibility doc):**
  - Server-side, per owner (`guest_id`, guests included), on the current target `c3fab3311d65`:
    - automatic Daily notes are hidden 24 h after creation and purge-eligible from 18 h, except today's note, saved notes and notes with an unexpired experiment, feedback or share; their moods cascade with them;
    - saved notes stay with the profile; their moods, action experiments and tarot sessions are purged once 29 d 18 h old, at the next 6-hourly cleanup, so within 30 days.
  - On the device (web and the Capacitor app, which share the web code): only a 36-hour in-memory note cache and small sync markers. There is **no device-side history**, so "on-device-first" is not an existing capability.
- **Two real options for v2:**
  1. **Owner-scoped aggregate endpoint.** It reads only rows that are still allowed to be kept and computes at request time. Nothing new is persisted, and the response is `no-store`. The window is bounded by retention: at most today plus the previous 28 local (ICT) dates (29 dates, inside the 29 d 18 h point) **for saved notes, their moods, experiments and tarot only**. Automatic Daily notes and their moods are not available across that window, so the recap must state which kinds it covers and must not present a mood distribution as the month's mood (it would cover saved notes only). Keeping an aggregate beyond that window is a separate, new derived dataset with its own consent, retention, deletion and export.
  2. **New local store.** It needs a retention limit, a delete control, clearing on logout and on profile or guest change, partitioning by profile on shared devices, exclusion from device backups, and its own privacy copy. "Local" does not mean "no privacy risk".
- **Rules for either option:**
  - Show the actual covered range, missing days and the opt-in start date.
  - Never treat missing data as zero activity or zero mood.
  - Never silently extend any retention window (TTL) to fill a calendar month. A calendar-month label ("Tháng 10") is not possible from current retention; use a rolling label with the real dates.
- **Consent and sharing:**
  - Recap consent is separate from share consent. The recap consent states which data the recap uses.
  - Withdrawing recap consent stops aggregation and deletes any stored recap artifact.
  - Sharing: default off, preview and edit before sharing, theme-only by default, never mood, notes or intention text. Copy says screenshots and downloads cannot be revoked. Share links follow AGENTS.md: no-index, no-store, tokens out of logs and referrers, revocable.
- **Value:** High personal relevance with no prediction risk, because it is the user's own data. It closes the loop on the daily note's "one small action".
- **Risks:**
  - Usage and mood aggregates are likely **sensitive** under Decree 356 Art. 4(1)(l), and possibly (c)/(d).
  - Low-activity months produce thin recaps that read as judgement ("bạn chỉ mở app 2 lần").
  - "Wrapped anxiety" works against the no-guilt rule.
  - Share cards risk leaking private content, even theme-only.
- **Effort:** Medium. Needs the aggregate endpoint or a new local store, a consent flow, coverage copy, share-card rendering and privacy review, plus store-declaration updates.

### C. "Nhịp trăng": a new-moon intention and a full-moon look-back
- **UI:**
  - At each **new moon**, a card offers "Bạn muốn để ý một điều nhỏ nào cho nửa tháng tới?" with 3 suggested small intentions from the lunation's sign (and house for EXACT charts). Picking a suggestion is the default; free text is optional.
  - At the next **full moon**, a one-tap look-back asks "Điều đó thế nào rồi?": "có / chưa / đổi ý". It never says "thất bại". One reflection line follows.
  - An optional single tarot card can be drawn as a *prompt*, not a forecast.
  - A small moon-phase ring sits on Home.
- **Value:**
  - It offers a calm, user-authored moment at a recurring landmark. Whether a new moon works as a fresh-start landmark is a **hypothesis to test**. Dai et al. (2014) studied calendar and personal landmarks, not lunar phases.
  - It gives two calm touchpoints a month without push volume.
  - It is non-predictive because the user authors the intention. It extends the daily "one small action" to a two-week horizon.
  - It works for every user (lunations are collective; personalisation is optional).
  - Its content matrix is small (2 lunation types × 12 signs, plus houses for EXACT).
- **Intention text rules:**
  - It is scoped to the profile that wrote it.
  - It has a stated retention: it expires after the look-back, or after one lunation cycle at most.
  - It has delete and withdraw controls.
  - It is cleared on logout or profile/guest change on a shared device.
  - It is never sent to the external rewrite provider, never used for matching or ranking, and never put in analytics.
  - Prompts do not invite writing about third parties by name.
- **Risks:**
  - "Ritual" or "manifest" vocabulary can read as magical thinking or superstition. Use "để ý / thử" language, never "thu hút / hiện thực hoá".
  - A missed look-back must not nag. Allow one reminder at most, and let it expire silently.
  - Some calendar months contain two new or two full moons. The cycle is per lunation, not per month.
- **Effort:** Low–medium. Needs lunation times (straightforward with Swiss Ephemeris), a small reviewed matrix, two cards and an intention store that follows the rules above.

### Comparison

| | A Sky strip | B Own-month recap | C Moon rhythm |
|---|---|---|---|
| Prediction risk | **High** without the date contract | None | Low |
| Privacy risk | None for layer 1; overlays use birth data already held | **High** (sensitive usage and mood aggregates) | Low–medium (intention text) |
| Works with no birth data / guests | **Yes** (layer 1) | Yes, from server-side owner data within retention | **Yes** |
| Shareability | Medium (sky line) | High, but sharing is opt-in only | Medium (intention card) |
| Monthly content cost | Medium | Low (template) | Low |
| Engineering effort | Medium | Medium | **Low–medium** |
| Guilt / streak risk | Low | **Medium–high** | Medium (look-back) |

### Recommendation (unconfirmed; owner decides)
1. **v1: shared sky events first, plus the moon rhythm.** Start with A's layer 1: at most 4 descriptive markers chosen by the fixed rule, with no birth data needed. Add C's new-moon intention and full-moon look-back. Add personal overlays only from real data (houses only for EXACT).
   - No good/bad colouring, no "nên / tránh", no retrograde warnings.
   - Gate it on the owner adopting the date contract (Rule 3 and the product-plan examples).
2. **v2: B as an opt-in "Tháng của bạn".** Prefer option 1 (owner-scoped, read-time aggregate within retention) unless the owner chooses to build and govern a new local store.
   - Recap consent and share consent are separate. Sharing is off by default, with preview and edit.
   - New user story with AC and DoD. US-18 is DEFERRED and is a reference for principles only.
3. **Do not ship** a 12-sign monthly horoscope, a good/bad-day calendar, push campaigns around retrogrades or eclipses, or any paywall teaser on this surface.

### How to measure (usefulness before return rate)
- **First, usefulness and understanding.** Ask an optional one-tap question on the card:
  - "Thẻ này có giúp bạn hiểu tháng này không?"
  - "Bạn có hiểu đây là mô tả bầu trời, không phải dự đoán không?"
  Also collect voluntary feedback, and review with a small group of users. Ship further only if users find it useful and do not read it as a forecast.
- **Only then, return behaviour.** Count `month_strip_opened`, `intention_set`, `lookback_answered` and `month_card_shared` against the daily-note baseline. Return rate is not a success criterion on its own.
- Events carry no content (no intention text, mood, notes or birth data). Usage events are themselves behaviour-tracking data under Decree 356 Art. 4(1)(l), so they need minimisation, a retention limit and declaration.

### Open items / AC-DoD status
- No user story, AC or DoD exists for any monthly feature. The owner must pick a direction and create the US with AC and DoD before build.
- The owner must update Rule 3 and the product-plan examples (date contract above).
- **[counsel]** Decree 356 classification of mood and usage aggregates; whether recaps may outlive withdrawal; Decree 87/2026 fine-level rules and other sanction decrees; Criminal Code Art. 320 (official text not retrieved).
- Quotations from the scanned PDFs were transcribed by hand from rendered page images (no OCR). Re-check them before reuse.
- Retention evidence: there is no primary data. Do not use Wrapped or the fresh-start paper as retention or ROI estimates.
