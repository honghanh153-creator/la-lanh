# Variety baseline: generated tables

Fixtures: {"profiles": {"version": "variety-profiles-v1", "seed": "la-lanh-variety-fixtures-v1", "synthetic": true, "sha256": "be5f447263b49f0d41a18154e526d6a46da14847884ef6759501199fa63b1782", "note": "Focus is null for everyone: the focus feature (F) does not exist yet."}, "radar_pairs": {"version": "variety-radar-pairs-v1", "seed": "la-lanh-variety-fixtures-v1", "synthetic": true, "sha256": "0c11130f909254541ef5903f1f35812651f5d9dc8ff3b1bc7f3a2a5cc05e829a"}, "tarot_bank": "tarot-question-bank-v1"}

## Daily M1 (pass rate: shortest repeat gap >= 90 days) and M2 (identical to the previous day)

| Stratum | Profiles | headline | scene | advice | why_today | companion |
|---|---|---|---|---|---|---|
| date_only|pool=1|focus=none | 300 (ok) | 0.0 (gap 6.0; M2 0.0) | 0.0 (gap 1.0; M2 0.8342) | 0.0 (gap 1.0; M2 0.9799) | n/a | 0.0 (gap 1.0; M2 1.0) |
| date_only|pool=2-3|focus=none | 0 (insufficient) | — | — | — | — | — |
| date_only|pool=>=4|focus=none | 0 (insufficient) | — | — | — | — | — |
| time_known|pool=1|focus=none | 0 (insufficient) | — | — | — | — | — |
| time_known|pool=2-3|focus=none | 0 (insufficient) | — | — | — | — | — |
| time_known|pool=>=4|focus=none | 900 (ok) | 0.0 (gap 6.0; M2 0.0) | 0.0 (gap 1.0; M2 0.2032) | 0.0 (gap 1.0; M2 0.3039) | 0.0 (gap 1.0; M2 0.5636) | 0.0 (gap 1.0; M2 0.3094) |

## Daily M4 / M5 / M7

- M4: {"time_known": {"identical_pairs": 404517, "pairs": 6722000, "rate": 0.0602}, "date_only": {"identical_pairs": 656600, "pairs": 656600, "rate": 1.0}, "same_birthdate_date_only_pairs": {"identical_days": 4000, "days": 4000, "rate": 1.0}}
- M5: {"date_only|pool=1|focus=none": {"mean": 0.0, "p10": 0, "distribution": {"0": 60000}}, "date_only|pool=2-3|focus=none": {}, "date_only|pool=>=4|focus=none": {}, "time_known|pool=1|focus=none": {}, "time_known|pool=2-3|focus=none": {}, "time_known|pool=>=4|focus=none": {"mean": 0.432, "p10": 0, "distribution": {"1": 77695, "0": 102305}}}
- M7: {"remove_birth_time_changes_note": 0.8799, "next_day_changes_note": 1.0, "note": "salt does not exist yet; ablation compares real signals only"}

## Tarot

```json
{
 "questions": 247,
 "readings": 988,
 "content_rejections": 0,
 "T1_form_accuracy": "not applicable yet (the engine has no question form; US-20 adds it)",
 "T2_headline_duplicates": {
  "playful_grounded|one_focus": {
   "readings": 247,
   "distinct": 5,
   "duplicate_rate": 0.9798
  },
  "playful_grounded|three_unblock": {
   "readings": 247,
   "distinct": 5,
   "duplicate_rate": 0.9798
  },
  "roast|one_focus": {
   "readings": 247,
   "distinct": 9,
   "duplicate_rate": 0.9636
  },
  "roast|three_unblock": {
   "readings": 247,
   "distinct": 9,
   "duplicate_rate": 0.9636
  }
 },
 "T3_generic_markers_positions": {
  "meaning:Ý chính của lá": 988,
  "action:Thử nhé:": 872,
  "scene:Ví dụ:": 1976
 },
 "T4_same_card_role_different_text": {
  "pairs": 21060,
  "different": 0,
  "rate": 0.0
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
 "R1_unique_sentences_per_reading": {
  "mean": 3.16,
  "p10": 1,
  "note": "baseline proxy: sentences not shared with any other pair (contact sentences are tagged only after R2)"
 },
 "R2_context_change_fit_friction": 0.0,
 "R2_voice_change_all_sections": 0.0877,
 "R3_cross_pair_overlap": 0.9077,
 "low_signal_pairs": 0,
 "unknown_time_method": "partner at local noon, Moon/houses/angles removed (current BirthService behaviour)",
 "versions": {
  "knowledge_version": "relationship-corpus-v2-2026-09-17",
  "renderer_version": "radar-living-dossier-v1",
  "gate_version": "conditional-reflection-v3"
 }
}
```
