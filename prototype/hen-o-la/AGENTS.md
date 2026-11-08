# Hẹn ở Lá boundaries

- Standalone, unshipped prototype for feeling the rhythm of one matchmaking evening. Do not wire it into apps/web, apps/api, auth, storage, networking or production without new owner approval and the legal/privacy review in `docs/research/2026-11-07-the-gioi-pixel-ghep-doi.md` (KS-26 stays BLOCK).
- Owner decisions (07/11/2026): an event, not an open world; people register and only some are invited; each evening has a setting (this one: a rainy café); it runs like a real matchmaking session; speech shows as bubbles over heads; private chat is undecided and not built.
- All guests are fictional adults with Lá nicknames. No real names, photos, birth data, charts, location, analytics or persistent storage. The player only picks a Lá nickname, a look, an item and a lantern colour.
- Matching stays mutual: a pair is announced only when both chose each other. Nobody learns who chose them otherwise. No public rejection (no lights switched off in front of others).
- Leaves and letters are anonymous and must never raise anyone's feeling toward the sender. Letters may only mention an act the writer actually saw.
- No compatibility score, astrology match or "who is watching you". Tarot halves only give a conversation topic.
- Speech bubbles are plain text (textContent), single line, ≤ 40 characters for the player.
- Motion: honour prefers-reduced-motion and the Full/Reduced/Off setting. No flashing, shake or autoplay sound. Touch targets ≥ 44 px where they are the main control.
- No XP, coins, streaks, paid features or return pressure.
- Keep `event.test.cjs`, `world.test.cjs` and `cafe.test.cjs` green. Report browser-pane checks and real-device checks separately.
- The everyday café (`quan.html`) has no free text (preset greetings only), no points, streaks, visit counters, time-spent displays or return rewards. Take-aways are a drink, the card of the day (same for everyone, suggests a small action, never predicts) and a kind sentence. Belongings (bag, umbrella, laptop, book…) are looks only: never sold, ranked, unlocked or rewarded.
- Duo challenge (`doi.html`): each teammate holds half of the facts and half of the answer; both must lock. A wrong answer gets one shared sentence that never says which blank or who. The extra line is always a fictional record, never a person in the evening. Horror stays mild: no gore, no flashing, slow dimming to a cap, a team-wide "Mình sợ quá" light switch, team plays at the gentler courage level, and each level ends on a funny reveal. "Đi tiếp cùng nhau?" never reveals who said no.
- Mezzanine guests (`khach.html`): only shared moments (free time, lanterns, retelling). Never private ones, never who chose whom, no names on daters, nothing to click on them, cheers have no target, no viewer counter. Cô Lá's notes never identify anyone.
