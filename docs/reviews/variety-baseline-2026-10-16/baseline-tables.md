# Variety baseline: generated tables

Fixtures: {"profiles": {"version": "variety-profiles-v1", "seed": "la-lanh-variety-fixtures-v1", "synthetic": true, "sha256": "be5f447263b49f0d41a18154e526d6a46da14847884ef6759501199fa63b1782", "note": "Focus is null for everyone: the focus feature (F) does not exist yet."}, "radar_pairs": {"version": "variety-radar-pairs-v1", "seed": "la-lanh-variety-fixtures-v1", "synthetic": true, "sha256": "0c11130f909254541ef5903f1f35812651f5d9dc8ff3b1bc7f3a2a5cc05e829a"}, "tarot_bank": "tarot-question-bank-v1"}

## Daily M1 (pass rate: shortest repeat gap >= 90 days) and M2 (identical to the previous day)

| Stratum | Profiles | headline | scene | advice | why_today | companion |
|---|---|---|---|---|---|---|
| date_only|pool=1|focus=none | 300 (ok) | 0.0 (gap 6.0; M2 0.0) | 0.0 (gap 1.0; M2 0.8342) | 0.0 (gap 1.0; M2 0.9799) | n/a | 0.0 (gap 1.0; M2 1.0) |
| date_only|pool=2-3|focus=none | 0 (insufficient) | — | — | — | — | — |
| date_only|pool=>=4|focus=none | 0 (insufficient) | — | — | — | — | — |
| time_known|pool=1|focus=none | 865 (ok) | 0.0 (gap 6; M2 0.0) | 0.0 (gap 1; M2 0.2065) | 0.0 (gap 1; M2 0.3083) | 0.0 (gap 1; M2 0.5656) | 0.0 (gap 1; M2 0.314) |
| time_known|pool=2-3|focus=none | 35 (insufficient) | 0.0 (gap 6; M2 0.0) | 0.0 (gap 1; M2 0.122) | 0.0 (gap 1; M2 0.1945) | 0.0 (gap 1; M2 0.4963) | 0.0 (gap 1; M2 0.1976) |
| time_known|pool=>=4|focus=none | 0 (insufficient) | — | — | — | — | — |

## Daily M4 / M5 / M7

- M4: {"time_known": {"identical_pairs": 404517, "pairs": 6722000, "rate": 0.0602}, "date_only": {"identical_pairs": 656600, "pairs": 656600, "rate": 1.0}, "same_birthdate_date_only_pairs": {"identical_days": 4000, "days": 4000, "rate": 1.0}}
- M5: {"date_only|pool=1|focus=none": {"mean": 0.0, "p10": 0, "distribution": {"0": 60000}}, "date_only|pool=2-3|focus=none": {}, "date_only|pool=>=4|focus=none": {}, "time_known|pool=1|focus=none": {"mean": 0.957, "p10": 1, "distribution": {"2": 9045, "1": 147456, "0": 16499}}, "time_known|pool=2-3|focus=none": {"mean": 0.754, "p10": 0, "distribution": {"1": 4715, "0": 2005, "2": 280}}, "time_known|pool=>=4|focus=none": {}}
- M7: {"remove_birth_time_changes_note": 0.8799, "next_day_changes_note": 1.0, "note": "salt does not exist yet; ablation compares real signals only"}

## Tarot

```json
{
 "questions": 247,
 "matrix": {
  "maps": [
   "one_focus",
   "three_unblock",
   "five_clarity",
   "five_loop",
   "five_choice",
   "five_conversation"
  ],
  "voices": [
   "straight_warm",
   "gentle_specific",
   "playful_grounded",
   "roast"
  ],
  "readings": 5928,
  "content_rejections": 0
 },
 "T1_form_accuracy": "not applicable yet (the engine has no question form; US-20 adds it)",
 "T2_headline_duplicates_by_voice": {
  "gentle_specific": {
   "readings": 1482,
   "distinct": 5,
   "duplicate_rate": 0.9966
  },
  "playful_grounded": {
   "readings": 1482,
   "distinct": 5,
   "duplicate_rate": 0.9966
  },
  "roast": {
   "readings": 1482,
   "distinct": 9,
   "duplicate_rate": 0.9939
  },
  "straight_warm": {
   "readings": 1482,
   "distinct": 5,
   "duplicate_rate": 0.9966
  }
 },
 "T3_generic_markers": {
  "positions": 23712,
  "meaning:Ý chính của lá": 1976,
  "action:Thử nhé:": 5232,
  "scene:Ví dụ:": 23712
 },
 "T4_same_card_role_topic_different_text": {
  "roles": 24,
  "cards": 78,
  "topics": 6,
  "question_pairs": 9292608,
  "different": 0,
  "rate": 0.0,
  "voice": "playful_grounded (default)"
 },
 "knowledge_versions": [
  "tarot-knowledge-v4"
 ]
}
```

## Radar

```json
{
 "pairs": 50,
 "readings": 800,
 "sentence_source": "visible prose per RadarContinuePage: headline, summary, pair signature, compatibility meanings; section title/body and highlights, scene, perspectives, observation title/body",
 "R1_unique_sentences_per_reading": {
  "mean": 5.16,
  "p10": 2,
  "note": "baseline proxy: sentences not shared with any other pair (contact sentences are tagged only after R2)"
 },
 "R2_context_change_fit_friction": {
  "comparisons": 1200,
  "mean_changed_share": 0.0
 },
 "R2_voice_change_fit_friction": {
  "comparisons": 1200,
  "mean_changed_share": 0.0
 },
 "diagnostic_voice_change_full_reading": {
  "comparisons": 1200,
  "mean_changed_share": 0.0513
 },
 "R3_cross_pair_overlap": 0.9127,
 "low_signal_pairs": 0,
 "unknown_time_method": "partner at local noon, Moon/houses/angles removed (current BirthService behaviour)",
 "versions": {
  "knowledge_version": "relationship-corpus-v2-2026-09-17",
  "renderer_version": "radar-living-dossier-v1",
  "gate_version": "conditional-reflection-v3"
 }
}
```
