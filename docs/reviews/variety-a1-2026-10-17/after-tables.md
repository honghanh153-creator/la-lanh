# B3-1a after-report: tables

Fixtures: {"profiles": {"version": "variety-profiles-v1", "seed": "la-lanh-variety-fixtures-v1", "synthetic": true, "sha256": "be5f447263b49f0d41a18154e526d6a46da14847884ef6759501199fa63b1782", "note": "Focus is null for everyone: the focus feature (F) does not exist yet."}}

## Daily M1 (pass rate: shortest repeat gap >= 90 days) and M2 (identical to the previous day)

| Stratum | Profiles | headline | scene | advice | why_today | companion |
|---|---|---|---|---|---|---|
| date_only|pool=1|focus=none | 300 (ok) | 0.0 (gap 2.0; M2 0.0) | 0.0 (gap 2.0; M2 0.0) | 0.0 (gap 2.0; M2 0.0) | n/a | 0.0 (gap 1.0; M2 1.0) |
| date_only|pool=2-3|focus=none | 0 (insufficient) | — | — | — | — | — |
| date_only|pool=>=4|focus=none | 0 (insufficient) | — | — | — | — | — |
| time_known|pool=1|focus=none | 20 (insufficient) | 0.0 (gap 2.0; M2 0.0) | 0.0 (gap 2.5; M2 0.0) | 0.0 (gap 2.0; M2 0.0) | 0.0 (gap 1.0; M2 0.1206) | 0.0 (gap 1.0; M2 0.3013) |
| time_known|pool=2-3|focus=none | 880 (ok) | 0.0 (gap 2.0; M2 0.0) | 0.0 (gap 3.0; M2 0.0) | 0.0 (gap 2.0; M2 0.0) | 0.0136 (gap 1; M2 0.1653) | 0.0 (gap 1.0; M2 0.1443) |
| time_known|pool=>=4|focus=none | 0 (insufficient) | — | — | — | — | — |

## Daily M4 / M5 / M7

- M4: {"time_known": {"identical_pairs": 1187, "pairs": 6722000, "rate": 0.0002}, "date_only": {"identical_pairs": 1654, "pairs": 656600, "rate": 0.0025}, "same_birthdate_date_only_pairs": {"identical_days": 9, "days": 4000, "rate": 0.0022}}
- M5: {"date_only|pool=1|focus=none": {"mean": 0.0, "p10": 0, "distribution": {"0": 60000}}, "date_only|pool=2-3|focus=none": {}, "date_only|pool=>=4|focus=none": {}, "time_known|pool=1|focus=none": {"mean": 0.81, "p10": 0, "distribution": {"0": 846, "1": 3068, "2": 86}}, "time_known|pool=2-3|focus=none": {"mean": 0.685, "p10": 0, "distribution": {"2": 4468, "0": 59843, "1": 111689}}, "time_known|pool=>=4|focus=none": {}}
- M7: {"remove_birth_time_changes_note": 0.908, "next_day_changes_note": 1.0, "note": "salt on; ablation keeps the owner's salt and changes one real signal"}

## A1 rotation

```json
{
 "consecutive_pairs": 238800,
 "same_situation_consecutive_pairs": 86167,
 "same_situation_axis_repeats": {
  "headline": 0,
  "scene": 0,
  "advice": 0
 },
 "three_day_same_situation_runs_with_pool_ge_2": 0,
 "full_combo_seen_in_previous_30d_rate": 0.0253,
 "full_combo_seen_in_previous_60d_rate": 0.0494,
 "pool_rule": "pool = top-K (K=3) distinct issues of the day after ranking"
}
```
