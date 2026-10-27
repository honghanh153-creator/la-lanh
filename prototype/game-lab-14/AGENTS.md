# Game lab 14 boundaries

- Standalone, unshipped research prototype. Do not wire it into apps/web, apps/api, auth, storage or production without new approval.
- Owner decisions (27/10/2026): research + rebuild; player-controlled character walking the room; pixel art (direction B). Keep movement, in-scene animation and game feel; do not regress to a static scene with forms.
- Fictional adults only. No real names, photos, birth data, charts, analytics, network APIs or persistent storage. Zodiac and tarot are author-assigned and change tone or suggest a method; they are never evidence and never name a record.
- No answer oracle: the notebook must not compute match/no-match or shortest paths. A correct submission needs the right record and the right reason; wrong answers get one identical message.
- Every case must have exactly one candidate from its sources (keep `cases.test.cjs` green). Never mutate earlier fixtures to change an answer.
- Motion: honour prefers-reduced-motion and the in-game Full/Reduced/Off setting. No flashing (> 3/s), no screen shake, no autoplay sound. Touch targets at least 44×44 CSS px.
- No XP, coins, streaks, paid hints or return pressure.
- Report DOM/script checks and real-device checks separately; do not claim device QA that was not done.
