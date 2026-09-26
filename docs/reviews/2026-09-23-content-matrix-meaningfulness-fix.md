# Content matrix meaningfulness fix — 2026-09-23

## Symptom

QA produced a thesis with two identical needs and internal shorthand:

> Hai nhu cầu bật lên cùng lúc và khuếch đại nhau. Một nhịp cần độ an toàn, kết nối và thời gian để cảm nhận; nhịp kia cần độ an toàn, kết nối và thời gian để cảm nhận. Khi căng: khó biết nhu cầu nào đang cầm lái. Góc rộng: chỉ là sắc độ nền.

## Root cause

The relationship lens compared both placements through element rhythm. Two placements in the same element therefore emitted the same clause twice. The synthesis grammar then appended generic aspect and orb atoms without naming each planetary need. Editorial gate v2 compared whole sections only, so near-duplicate clauses inside one section passed.

## Corrected contract

1. Name both planets or points.
2. State the distinct need represented by each one.
3. Explain how the aspect makes those functions cooperate, compete or require adjustment.
4. Use orb only to tell the reader how much weight to give the idea.
5. Keep degree and house-mode detail in evidence unless it improves the everyday explanation.
6. Reject near-duplicate clauses and internal shorthand before persistence.

Runtime versions:

- knowledge: `western-interpretation-matrix-v4`
- renderer: `deterministic-vi-v4`
- editorial gate: `editorial-gate-vi-v3`

## Verification matrix

- Same-element combinations cover fire, earth, air and water.
- Every combination runs through 6 aspect types and 3 orb bands.
- The reported bad sentence is a red/green regression fixture.
- The 365-day publishability suite and complete reading module suite must pass.
- Vietnamese label matching preserves accents so `Hải Vương` cannot be mistaken for aspect `vuông`.

## Security and privacy review

This correction changes static knowledge atoms, deterministic composition and local publication gates only. It adds no field, identifier, account requirement, analytics event, storage, external provider call or new processing purpose. Existing evidence, anti-influence and privacy gates remain mandatory. Data minimization is therefore unchanged.

References checked:

- [Astrodienst — Aspect](https://www.astro.com/astrowiki/en/Aspect): interpretation starts with the two planets involved; harmonious aspects also have blind spots.
- [Astrodienst — Orb](https://www.astro.com/astrowiki/en/Orb): orb expresses allowed distance from exactness and varies by method, so product copy should treat it as weighting rather than certainty.
- [Astrodienst — Transit](https://www.astro.com/astrowiki/en/Transit): transit interpretation depends on the natal role and orb, with tighter initial orbs recommended.
- [OWASP MASVS-PRIVACY-1](https://mas.owasp.org/MASVS/controls/MASVS-PRIVACY-1/): continue minimizing access to sensitive data and resources.
- [Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15](https://vanban.chinhphu.vn/?classid=1&docid=214590&pageid=27160&typegroup=): current Vietnamese privacy-law baseline, effective 2026-01-01.
