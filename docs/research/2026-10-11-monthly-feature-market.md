# Market research: "Tháng này có gì mới" (monthly feature) — 2026-10-11

Read-only web research. No source code changed. No sign-in, purchase or installer download.
Companion doc (repo feasibility, data retention, engine gaps):
`docs/research/2026-10-11-monthly-feature-feasibility.md`.

---

## Tóm tắt tiếng Việt

**Thị trường làm gì với "tháng":**
- Hầu hết app chiêm tinh lớn **không có màn "tháng này" riêng**. Co–Star chỉ có note ngày và bán "Your Year Ahead". CHANI có bài đọc theo tuần, và bản 2026 có "month-by-month" cùng lịch "key dates" (trăng mới/tròn, nghịch hành, nhật/nguyệt thực). The Pattern dùng **timeline chu kỳ cá nhân** (bắt đầu, đỉnh, kết thúc). TimePassages và Astro Future có **danh sách mốc quan trọng** và thanh kéo thời gian. Moonly, Stardust và Labyrinthos xoay quanh **chu kỳ trăng**: nghi thức trăng mới/tròn, spread theo pha trăng, vòng pha trăng. Sanctuary và Nebula bán tử vi ngày/tuần/tháng/năm **theo 12 cung**, dạng chung chung.
- Ở Việt Nam, khung "tháng" mặc định là **Lịch Vạn Niên**: lưới tháng âm/dương, rằm/mùng một, **ngày tốt/xấu, giờ hoàng đạo**. Lá Lành phải tránh đúng mô thức này, vì nó là dự đoán định mệnh.

**Bằng chứng giữ chân người dùng:** Không có số liệu công khai đáng tin nào so sánh nội dung tháng với nội dung ngày. Ba điều có bằng chứng:
- "Fresh start effect" (Dai, Milkman & Riis 2014): đầu tuần và đầu tháng làm tăng hành vi hướng mục tiêu.
- Recap cá nhân có thể chia sẻ được (Spotify Wrapped 2025: hơn 200 triệu người dùng trong 24 giờ, hơn 500 triệu lượt chia sẻ).
- Recap kiểu "fun facts" khó duy trì (Gentler Streak đã bỏ).

Người dùng phàn nàn nhiều nhất về **paywall, push dày và upsell, nội dung lặp hoặc chung chung**. Có phàn nàn về giọng tiêu cực (Co–Star) và nỗi sợ "Mercury nghịch hành", nhưng chủ yếu xuất hiện trong báo chí văn hoá.

**Pháp lý (nguồn chính thức):**
- Luật BVDLCN 91/2025/QH15 và Nghị định 356/2025/NĐ-CP có hiệu lực từ 01/01/2026. **Nghị định 13/2023 đã bị thay thế.**
- Recap dùng mood hoặc nhật ký có thể chạm danh mục **dữ liệu nhạy cảm** ("đời sống riêng tư", "tình trạng sức khỏe"). Vì vậy cần đồng ý **riêng theo từng mục đích**, và im lặng không được tính là đồng ý (Điều 9).
- Luật Quảng cáo Điều 8 cấm quảng cáo gây nhầm lẫn về công dụng (khoản 9) và trái thuần phong mỹ tục (khoản 3).
- Apple 4.3(b) coi "fortune telling" là danh mục bão hoà, nên app phải khác biệt thật.

**Khuyến nghị:** Làm **C (nhịp trăng: đặt 1 ý định nhỏ lúc trăng mới, nhìn lại lúc trăng tròn)** làm xương sống v1. Kèm theo đó là **A-lite**: một dải "mốc trời tháng này" tối đa 4 mốc, chỉ mô tả "bầu trời đang ra sao" và nối vào lá số, không có "ngày tốt/xấu", không có "nên làm X". **B (recap tháng của chính bạn)** để sang v2, bật bằng đồng ý riêng và ưu tiên tính trên thiết bị.

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

**Takeaway:** No leading app combines (a) the collective sky of the month, (b) where it touches *your* chart, and (c) your own month, in one non-predictive surface. CHANI comes closest but is paywalled ($11.99/mo) and leans on "manifestation" and ritual language. There is white space for a plain-language, agency-first month view.

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
- **Temporal landmarks motivate fresh starts.** Dai, Milkman & Riis (2014, *Management Science* 60(10)) found that searches for "diet", gym visits and goal commitments rise after temporal landmarks, including the start of a week or month. This is the strongest evidence for a beginning-of-month or new-moon intention moment. https://faculty.wharton.upenn.edu/wp-content/uploads/2014/06/Dai_Fresh_Start_2014_Mgmt_Sci.pdf
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
- **Spotify Wrapped scale.**
  - Wrapped 2025 had more than 200M engaged users in its first 24 hours (it took 62 hours in 2024).
  - It had more than 500M shares, up 41%, counting in-app shares, screenshots and downloads.
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
3. **Sky content shares safely; self content shares only by explicit choice.** The default share card should contain only the month's sky line and the user's chosen theme. It should never include mood, notes or birth data. This matches the existing US-18 AC06 rule ("default ẩn danh … không lộ số liệu nhạy cảm").
4. **Comparison as play, not ranking.** "Bạn và bạn thân cùng tháng trăng mới ở nhà 5" is fine. "Ai may mắn hơn" is not.
5. **Low production cost per month.** This is the Gentler Streak lesson: the template must be generated from data and a reviewed content matrix, not hand-written monthly.
6. **Public share links follow AGENTS.md**: no-index, no cache, tokens out of logs and referrers, and revocable.

---

## 4. Ethical and regulatory angles (official sources first)

### Vietnam
- **Personal data.** Law 91/2025/QH15 on Personal Data Protection is effective 2026-01-01.
  - Official metadata: https://congbao.chinhphu.vn/van-ban/luat-so-91-2025-qh15-45578.htm
  - Implementing Decree 356/2025/NĐ-CP was issued 2025-12-31 and is effective 2026-01-01: https://vanban.chinhphu.vn/?docid=216387&pageid=27160 (signed PDF: https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/01/356-nd.signed.pdf)
  - **Decree 13/2023/NĐ-CP, named in the brief, has been replaced by Decree 356/2025** (per PwC Vietnam and EY legal alerts: https://www.pwc.com/vn/vn/publications/2026/20260128-new-rules-personal-data-protection.pdf and https://www.ey.com/vi_vn/technical/tax/tax-and-law-updates/nghi-dinh-so-356-2025-nd-cp-quy-dinh-chi-tiet-mot-so-dieu-va-bien-phap-thi-hanh-luat-bao-ve-du-lieu-ca-nhan). Do not design against Decree 13.
  - Law 91 Art. 2(3): sensitive personal data is data "gắn liền với quyền riêng tư của cá nhân", with the list set by the Government.
  - The Decree 356 Art. 4 list, per secondary summaries of the full text, includes "thông tin về đời sống riêng tư, bí mật cá nhân" and "tình trạng sức khỏe". Health is no longer limited to medical records. Mood logs, journal text and relationship notes in a monthly recap therefore plausibly fall into sensitive categories. **Counsel must confirm against the signed text.** The official PDF is a scanned image and could not be text-extracted in this pass.
  - Law 91 Art. 9 sets the consent conditions:
    - consent must be per purpose ("đối với từng mục đích");
    - it must not be bundled with other purposes;
    - it must be "rõ ràng, cụ thể" and recordable;
    - "Sự im lặng hoặc không phản hồi không được coi là sự đồng ý".
    - Withdrawal is covered in Art. 10. Article text was read via https://hethongphapluat.com/luat-bao-ve-du-lieu-ca-nhan-2025/dieu-9; verify against the official gazette text.
  - **Implication:** A recap that aggregates mood or notes needs its own opt-in, separate from the daily note. It needs a stated retention period, deletion that also removes the aggregate, and no default-on share. The repo's 29 d 18 h raw-input purge (see the feasibility doc) means a calendar-month recap needs either a consented derived aggregate or on-device computation.
- **Advertising.** Law on Advertising 16/2012/QH13 Art. 8 bans:
  - (3) content contrary to "thuần phong mỹ tục Việt Nam";
  - (6) content infringing freedom of belief;
  - (9) content that is untrue or "gây nhầm lẫn" about a product's or service's "công dụng";
  - (11) "nhất / duy nhất / tốt nhất" claims without proof.
  - Text read from an official provincial copy: https://tthc.hue.gov.vn/Upload/LEGALS/Luat%20Quang%20cao.doc
  - Law 75/2025/QH15 amends the advertising law from 2026-01-01; check the amended text before launch marketing. https://luatvietnam.vn/thuong-mai/luat-quang-cao-sua-doi-2025-so-75-2025-qh15-404208-d1.html (secondary)
  - **No clause found that names astrology or horoscopes.** The practical risk is marketing a monthly feature as predictive or accurate ("dự báo chính xác tháng của bạn"), which would be a misleading claim about the service's utility.
- **Superstition.** Criminal Code Art. 320 (practising superstition: "bói toán, đồng bóng") applies only after a prior administrative sanction or conviction. Decree 38/2021/NĐ-CP sanctions organising superstitious activity. Official full text was not retrieved in this pass; the sources are legal-press summaries such as https://lsvn.vn/hanh-nghe-me-tin-di-doan-va-cac-che-tai-xu-ly-a174659.html. A reflection product with no fees for "readings", no claims about events and no remedies or rituals sold to avert misfortune is far from this line. A "good/bad days" calendar or paid "giải hạn" content would move toward it. **Counsel review recommended. This is not legal advice.**

### Platforms
- **Apple App Review 4.3(b)** names "fortune telling" among saturated categories. New submissions must "offer a meaningfully different or improved experience". A non-predictive, self-reflection monthly feature supports that differentiation; a generic monthly horoscope weakens it.
- **Apple 5.1.1(ii) and 5.1.2(i)** require consent for collecting user or usage data and permission before using or sharing personal data. Source: https://developer.apple.com/app-store/review/guidelines/
- Any new persisted recap field must be reflected in Apple App Privacy, the Google Play Data Safety form and the in-app privacy copy (see `docs/legal/store-privacy-data-map.md`).

### Ethical design rules derived for the monthly surface
1. Describe the sky, not the user's fate. "Trăng tròn ngày X rơi vào vùng [nhà/cung] — vùng này nói về …" is acceptable. "Ngày X là ngày tốt để …" or "tránh ký hợp đồng" is not.
2. Retrograde and eclipse lines carry no warning, no "cẩn thận", and no blame attribution. This follows the repo reading-knowledge-spec rule that retrograde yields no psychological conclusion by itself.
3. No good/bad-day colouring on any calendar, which rules out the Lịch Vạn Niên pattern.
4. No "missed days" counts, streaks or "bạn đã bỏ lỡ"; an empty month is a neutral state.
5. Disclaimer and provenance on every sky claim, per the existing content gate.

---

## 5. Three concept options for "Tháng này có gì mới"

Shared constraints: guest-first; Sun-only users must get value; plain direct Vietnamese; one situation plus one small action; no predictions; no guilt or streaks; server-side Swiss Ephemeris.

### A. "Bầu trời tháng này": a sky calendar of 3–4 key dates, tied to the user's chart
- **UI:** A horizontal **calendar strip** for the month showing only the 3–4 key markers: new moon, full moon, at most one ingress or station, and an eclipse if there is one. Tapping a marker opens a **key-date card** with:
  - what is happening in the sky (one line);
  - where it touches you, as a house for users with a birth time and as the Sun-sign relationship for date-only users;
  - one situation plus one small action, phrased as an invitation.
- **Value:** Fresh, objectively true content every month. It differentiates from 12-sign generic text and uses the existing Swiss Ephemeris and astro spec. It works for guests at the collective level and gives a reason to add a birth time ("thêm giờ sinh để biết mốc này rơi vào vùng nào của bạn").
- **Risks:**
  - It is the closest of the three to predictive framing. The PRD Rule 3 "deadline" and "thời điểm tốt để nộp đơn" wording must be rewritten first.
  - Retrograde and eclipse content can drift into fear.
  - Vietnamese users may read any dated calendar as "ngày tốt/xấu".
  - Sun-only personalisation is thin (whole-sign-from-Sun or element only).
  - It needs an event solver plus a reviewed content matrix (events × houses/signs × direct/Roast).
- **Effort:** Medium–high. Needs an event solver with bracketed root finding, a content matrix, the review gate and fixtures. See the feasibility doc for the engine gaps.

### B. "Tháng của bạn": a recap of the user's own notes, experiments and moods, plus one theme
- **UI:** A month-end **story recap of 3–5 cards**:
  - notes saved;
  - small actions tried, with the user's own "có ích / không" taps;
  - a mood distribution, only if mood logging was consented;
  - one theme sentence, chosen from a reviewed bank by evidence and not generated freely;
  - a final shareable **month card** that by default shows only the theme line.
- **Value:** The highest personal relevance, with zero prediction risk because it is the user's own data. It is the Wrapped-style share format Gen Z already uses, and it closes the loop on the daily note's "one small action".
- **Risks:**
  - Mood, journal and relationship data are likely **sensitive** under Decree 356. That requires separate opt-in, retention and deletion design, and updates to store declarations.
  - The raw-input purge at about 30 days blocks the naive build.
  - Low-activity months produce thin or empty recaps that read as judgement ("bạn chỉ mở app 2 lần").
  - "Wrapped anxiety" works against the no-guilt rule.
  - Share cards risk leaking private content.
  - Guests on the web have only local data.
- **Effort:** Medium. Needs an aggregation job or on-device computation, a consent flow, a retention policy, share-card rendering and privacy review. It is lower if v1 computes everything **on device** from data the user still holds and stores nothing new server-side.

### C. "Nhịp trăng": a new-moon intention and a full-moon look-back
- **UI:**
  - At the **new moon**, a card offers "Tháng này bạn muốn để ý một điều nhỏ nào?" with 3 suggested small intentions, derived from the lunation's sign or house and the user's chart. The user can also write their own, kept local by default.
  - About two weeks later, at the **full moon**, a one-tap look-back asks "Điều đó thế nào rồi?": "có / chưa / đổi ý". It never says "thất bại". One reflection line follows.
  - An optional single tarot card can be drawn as a *prompt*, not a forecast.
  - A small moon-phase ring sits on Home.
- **Value:**
  - It maps directly onto the fresh-start effect at a natural landmark.
  - It gives two calm touchpoints a month without push volume.
  - It is intrinsically non-predictive because the user authors the intention, and it extends the daily "one small action" to a two-week horizon.
  - It works for every user (lunations are collective; personalisation is optional).
  - Its content matrix is small (2 lunations × 12 signs/houses).
- **Risks:**
  - "Ritual" or "manifest" vocabulary can read as magical thinking or superstition. Use "để ý / thử" language, never "thu hút / hiện thực hoá".
  - A missed look-back must not nag. Allow one reminder at most, and let it expire silently.
  - User-written intention text is personal content, so keep it local or apply explicit retention.
  - Lunations are only about 29.5 days apart, so some calendar months contain two new or two full moons. Copy should not depend on "the" new moon of the month.
- **Effort:** Low–medium. Needs lunation times (trivial with Swiss Ephemeris), a small reviewed matrix, two cards and a local store.

### Comparison

| | A Sky calendar | B Own-month recap | C Moon rhythm |
|---|---|---|---|
| Prediction risk | **High** (needs copy rewrite) | None | Low |
| Privacy risk | Low (birth data already held) | **High** (sensitive aggregates) | Low–medium (intention text) |
| Works for Sun-only / guests | Partially | Partially (local data) | **Yes** |
| Shareability | Medium (sky line) | **High** (Wrapped format) | Medium (intention card) |
| Monthly content cost | High | Low (template) | Low |
| Engineering effort | Medium–high | Medium | **Low–medium** |
| Guilt / streak risk | Low | **Medium–high** | Medium (look-back) |

### Recommendation
1. **v1: ship C as the spine, with an "A-lite" strip.** The monthly surface is the moon rhythm: new-moon intention and full-moon look-back. Add a 3–4-marker sky strip that only *describes* events and links each one to the chart at the level the user has data for.
   - No good/bad colouring, no "nên / tránh", no retrograde warnings.
   - Gate it on the no-prediction rewrite of PRD Rule 3 and the product plan's "thời điểm tốt" examples.
2. **v2: add B as an opt-in, on-device-first "Tháng của bạn".**
   - Default to a theme-only share card.
   - Ask for separate, purpose-specific consent before any mood or note aggregate is kept server-side.
   - Write a new user story with AC and DoD that mirror US-18 AC04–AC06 for privacy and tone.
3. **Do not ship** a 12-sign monthly horoscope, a good/bad-day calendar, push campaigns around retrogrades or eclipses, or any paywall teaser on this surface.

### Open items / AC-DoD status
- No user story, AC or DoD exists yet for any monthly feature; it needs a new US with AC.
- Decree 356 sensitive-data list: confirm from the signed text with counsel. The OCR-only PDF was not machine-readable here.
- Advertising Law as amended by Law 75/2025: re-check marketing copy before launch.
- Criminal Code Art. 320 and Decree 38/2021: official text not retrieved; secondary summaries only.
- Retention data: no primary data exists. Instrument `month_strip_opened`, `intention_set`, `lookback_answered` and `month_card_shared`, with no content in events, and measure against the daily note baseline.
