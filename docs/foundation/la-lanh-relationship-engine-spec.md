# Lá Lành relationship engine v2

## Product contract

Vòng Lá does not answer “hai người hợp bao nhiêu phần trăm?”. It surfaces a small set of inspectable relationship energies and a useful next conversation. Astrology is one reflective lens; intent, boundaries, consent, safety and lived interaction stay separate and outrank it.

## Source corpus v1

The engine stores concepts and provenance, not copyrighted excerpts. Ten reference works seed the editorial matrix:

| Source | Class | Safe contribution |
|---|---|---|
| *Attached* — Amir Levine & Rachel Heller | relationship psychology | needs for closeness and reassurance; never assign an attachment label |
| *Hold Me Tight* — Sue Johnson | relationship psychology | recurring connection/disconnection cycles and repair questions |
| *The Seven Principles for Making Marriage Work* — John Gottman & Nan Silver | relationship psychology | knowing the other person, turning toward, repair and shared meaning |
| *Eight Dates* — John & Julie Gottman et al. | dating/conversation | consented prompts about trust, conflict, intimacy, money, family, play and growth |
| *How to Not Die Alone* — Logan Ury | dating/decision science | reduce spark-only bias and encourage observable, revisable choices |
| *Nonviolent Communication* — Marshall B. Rosenberg | communication | observation–feeling–need–request scaffolding; not therapy |
| *Person-to-Person Astrology* — Stephen Arroyo | relationship astrology | elements and Sun/Moon/Mercury/Venus/Mars needs and motivations |
| *Synastry* — Ronald Davison | relationship astrology | cross-aspects, house interchanges and relationship chart method |
| *Planets in Composite* — Robert Hand | relationship astrology | midpoint Composite as the relationship’s symbolic third chart |
| *Light on Relationships* — Hart de Fouw & Robert Svoboda | Jyotish relationship astrology | strengths/challenges and free-will framing; factual layer only until expert review |

The canonical machine-readable registry is `apps/api/app/domains/relationships/knowledge.py` and includes allowed/prohibited uses per source. Coverage tests require every concept id named by a source to resolve to a traceable editorial rule; a book title in the registry without an executable concept is not counted as knowledge coverage.

## Voice bank

Chart facts choose **what** may be discussed; the user explicitly chooses **how** it is said. The engine must never infer tone preference from sign, gender, mood, clicks or chat.

| Voice | Product promise |
|---|---|
| `straight_warm` | direct, concrete and kind; no mystical filler |
| `gentle_specific` | softer delivery without hiding the fact, limit or next action |
| `playful_grounded` | at most one natural Gen Z/slang beat; evidence comes before the joke |
| `deep_dive` | method, evidence and uncertainty explained in layers |

All voices keep the same safety boundaries and disclaimer semantics. Voice changes must not change candidate ranking, confidence, consent or chart facts.

## Chart set

| Method | Runtime status | Minimum input | Product use |
|---|---|---|---|
| Natal relationship profile | available through Natal facts | one exact chart for houses | each person’s needs/context; no personality verdict |
| Western Synastry v2 | available | two compatible Western charts | strict cross-aspects, strength, dimensions and A↔B house overlays |
| Midpoint Composite v2 | available | two compatible Western charts | shared relationship pattern through midpoint points + aspects; houses withheld |
| Davison uncorrected midpoint | available | both exact times and places | a real midpoint moment/place chart with explicit method caveat |
| Transits to Davison/Composite points | derivable, not product-wired | relationship chart + observed instant | shared timing after product/UX review; never used for candidate ranking |
| Jyotish D1 + nakshatra/drishti | factual engine available | compatible Jyotish charts | research/inspectable facts only |
| D9/Navāṁśa points | available behind expert/content gate | exact Jyotish chart | factual divisional positions; no generated relationship copy |
| Ashtakoota/Kuṭa score | gated | expert-reviewed rules and bias review | not implemented; no 36-point ranking |
| Corrected Davison, progressions | roadmap | documented reference algorithm + golden fixtures | no launch claim |

## Relationship dimensions

- `communication`: Mercury and information-processing contacts.
- `emotional`: Moon and felt-safety contacts.
- `relating`: Venus and reciprocal affection/values.
- `drive`: Mars, desire, action and boundary friction.
- `growth`: Jupiter/Saturn and long-horizon learning/commitment themes.
- `friction`: dynamic square/opposition evidence; never treated as “bad”.

One contact may support multiple dimensions. `tone` describes geometry (`flow`, `activation`, `mixed`) rather than goodness. `strength` is a transparent exactness curve inside the versioned orb; it is not a compatibility probability.

## Radar Living Dossier projection

The relationship engine returns inspectable facts; Radar turns those facts into a private, evidence-bound reading through `radar-living-dossier-v1`:

1. eligible Synastry contacts are normalized into everyday themes such as communication, emotional rhythm, attraction, pace/boundaries, clarity and autonomy;
   contacts made only between outer/generational points are withheld from the public thesis because they cannot personalize this pair well enough; they may remain inspectable engine facts but do not compete with personal-planet evidence;
2. contacts within a theme are ordered deterministically by channel contribution, exactness and evidence ID, then kept together as a cluster rather than reduced to one winning aspect;
3. the strongest coordination cluster and strongest friction cluster form a Pair Signature that names both the easy entry point and the negotiation point;
4. directional house overlays stay directional (`you`, `them`) and Midpoint Composite evidence is labeled as the shared rhythm; none of these layers claims to know another person's intent;
5. each report chapter may expose highlights, an everyday scene, directional perspectives or one observable check, but every statement remains conditional and traceable to the receipts shown under `Vì sao Lá đọc vậy?`.

Ba chỉ báo giữ đúng receipts của tối đa sáu contact đã tham gia công thức; metadata là hợp của chapter receipts và indicator receipts. Highlight không được trỏ tới evidence ID vắng mặt trong disclosure của chính chapter.

Directional copy luôn được project theo viewer: private check là A→B; consented invite lưu A→B cho owner và trả B→A cho recipient. Synastry receipts và house overlay cards phải giữ đúng chiều tương ứng.

The projector may be shorter when evidence is sparse. Khi chỉ có một cluster không đủ friction hoặc không còn contact cá nhân hóa sau filter, projector chuyển sang sparse/low-signal branch, nói rõ giới hạn và không dùng cùng một góc để đồng thời khẳng định điểm hợp lẫn điểm cấn. It must not invent a second side, repeat the same sentence through synonyms, pad every report to the same length or send chart/personal data to a generative provider. The public contract remains `radar-result-v2`; Dossier fields are additive so stored v2 results continue to render.

## Content gate

Generated copy must:

1. cite at least one chart evidence id and one editorial concept id;
2. use conditional language (“có thể”, “thử kiểm chứng”) and a concrete two-person prompt;
3. avoid attachment diagnosis, mental-health labels, coercion, certainty, breakup/stay advice and moral judgments;
4. never infer intent, sexual orientation, abuse, trauma or willingness from birth data or app behavior;
5. withhold house/D9 claims when input precision is not eligible.
6. resolve every editorial concept to a registered source id and every chart statement to a fact/evidence id;
7. use only the voice profile explicitly selected by the user; default to `straight_warm` when no preference exists.

## Privacy and security

- Birth time, place, coordinates, relationship intent and pair-derived facts are sensitive personal data.
- This engine slice is pure calculation and static knowledge: no new database table, external model call, log field or public endpoint.
- Later integration requires separate matching consent, pair-purpose limitation, authorization for both profiles, retention/deletion propagation, redacted telemetry and re-check immediately before mutual creation.
- Candidate ranking must run hard safety/preference filters before any optional astrology diversity logic. Book-derived psychology is never a hidden ranking signal.

## Current sources

- [Astrodienst relationship charts](https://www.astro.com/prod/pr_relation_p.htm)
- [Astrodienst partner chart FAQ](https://www.astro.com/faq/fq_fh_partner_e.htm)
- Official publisher/author pages referenced by the machine-readable registry.
