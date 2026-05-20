# FurEver Match — Matching Schema

## Overview

Every adoption request is scored against every available dog in three tiers:

```
Hard Rules → Soft Scoring → Personality Matching → Final Score
```

Dogs that fail any hard rule are eliminated immediately. Remaining dogs receive a
soft score (rule-based) and a personality score (LLM-assisted), which are blended
into a final score used for ranking.

---

## Final Score Formula

```
final_score = soft_score × 0.60 + personality_score × 0.40
```

---

## Tier 1 — Hard Rules (pass / fail)

A single failure eliminates the dog. All three rules can be toggled in `matching_rules.yaml`.

| Rule | Condition | Notes |
|---|---|---|
| **Gender** | Dog gender must match `requested_gender` | Skipped when no preference set |
| **Pets compatibility** | Dog must get along with dogs/cats if adopter has them | Triggered by `which_pets` field |
| **Kids compatibility** | Dog must get along with kids if adopter has children ≤ 16 | Children older than 16 are not counted |

**Filter dominance warning**: if any single hard rule eliminates > 95% of available dogs, a warning is returned so the user can reconsider that preference.

---

## Tier 2 — Soft Rules (scored 0–100, weighted average)

Applied to dogs that pass all hard rules. Each rule produces a score between 0 and 1, then weights are applied.

| Rule | Weight | How it scores |
|---|---|---|
| **Kids compatibility** | 2.0 | 1.0 friendly · 0.5 unknown · 1.0 not relevant |
| **Pets compatibility** | 2.0 | 1.0 compatible · 0.5 unknown · 1.0 not relevant |
| **Size** | 1.5 | 1.0 exact · −0.3 per step · min 0.0 |
| **Home requirements** | 1.5 | Matrix of dog size × energy level × home type (see below) |
| **Energy level** | 1.0 | 1.0 exact · −0.3 per step · min 0.0 |
| **Age compatibility** | 1.0 | 1.0 exact · −0.4 per step · min 0.1 |
| **Training level** | 1.0 | 1.0 exact · −0.25 per step · min 0.0 |

### Home requirements matrix (sample)

| Dog | Energy | House + Yard | House only | Apartment |
|---|---|---|---|---|
| Large | High | 1.00 | 0.50 | 0.10 |
| Large | Medium | 1.00 | 0.65 | 0.20 |
| Medium | High | 1.00 | 0.75 | 0.40 |
| Medium | Low | 1.00 | 0.90 | 0.75 |
| Small | Any | 1.00 | 0.85–0.95 | 0.65–0.88 |

### Valid enum values

| Field | Values |
|---|---|
| `size` | `small` · `medium` · `large` |
| `energy_level` | `low` · `medium` · `high` · `very_high` |
| `age` bucket | `puppy` (0–1 yr) · `young` (1–4 yr) · `adult` (4–7 yr) · `senior` (7+ yr) |
| `training_level` | `basic` · `intermediate` · `advanced` |
| `gender` | `male` · `female` · null (no preference) |

---

## Tier 3 — Personality Matching (LLM-assisted, no extra LLM call at match time)

### Dog features (pre-computed once per dog, stored in `dog_llm_features`)

Extracted by LLM from the dog's Hebrew description + profile fields:

| Feature | Type | Description |
|---|---|---|
| `personality_traits` | list | 3–5 key personality descriptors |
| `activity_level` | `low`/`medium`/`high` | How active the dog is |
| `care_requirements` | `low`/`medium`/`high` | Time/effort needed daily |
| `ideal_owner_profile` | text | Free-text description of ideal owner |
| `needs` | list | e.g. exercise, training, space, attention |
| `fears_sensitivities` | list | Known fears or triggers |
| `social_traits` | text | How the dog relates to people / other animals |

Run `py migrate_dog_llm_features.py` to populate or refresh this table.

### Person features (1 LLM call per match request)

Extracted by LLM from the adoption request answers:

| Feature | Type | Description |
|---|---|---|
| `activity_level` | `low`/`medium`/`high` | Adopter's daily activity level |
| `time_availability` | `low`/`medium`/`high` | How much time they can give a dog |
| `experience_level` | `beginner`/`intermediate`/`experienced` | Prior dog ownership experience |
| `lifestyle` | text | Short description of daily life / routine |
| `home_environment` | text | Living situation description |
| `motivations` | list | Why they want a dog |
| `expectations` | list | What they expect from the dog |

### Local comparison (no LLM, instant)

Person and dog features are compared locally using three checks:

| Check | Logic | Weight |
|---|---|---|
| **Activity alignment** | dog `activity_level` vs person `activity_level` | 1.0 exact · 0.5 one step · 0.0 two steps |
| **Care vs time** | dog `care_requirements` (inverted) vs person `time_availability` | High-care dog + low-time person = low score |
| **Experience vs complexity** | Beginner + dog with 4+ needs = penalty; experienced = bonus | Flat adjustment |

Average of checks → `personality_score` (0–100)

---

## Database Tables

| Table | Purpose |
|---|---|
| `dogs` | Dog profiles including `energy_level`, `size`, `gender`, `level_of_training` |
| `adoption_requests` | Adopter quiz answers |
| `dog_images` | Photos per dog |
| `dog_llm_features` | Pre-computed LLM personality features per dog |

---

## Key Files

| File | Purpose |
|---|---|
| `furever_match/matching_rules.yaml` | All rule parameters, weights, thresholds — edit here to tune matching |
| `furever_match/matching_v2.py` | Hard filters, soft scoring functions, LLM extraction prompts |
| `furever_match/matching_integration_v2.py` | Full pipeline orchestration, personality comparison logic |
| `furever_match/llm.py` | Ollama and Gemini client wrappers |
| `migrate_dog_llm_features.py` | One-time / refresh script to pre-compute dog features |
| `migrate_energy_level.py` | Populates `energy_level` for dogs that are missing it |

---

## Adding / Updating Dogs

When new dogs are added to the DB:

1. Run `py migrate_energy_level.py` — sets `energy_level` for new records
2. Run `py migrate_dog_llm_features.py` — pre-computes LLM features for new records

Both scripts skip dogs that already have values unless `--overwrite` is passed.

---

## Score Thresholds (display only)

| Score | Label |
|---|---|
| 90–100 | Highly recommended |
| 75–89 | Recommended |
| 60–74 | Consider |
| 40–59 | Requires discussion |
| 0–39 | Not recommended |
