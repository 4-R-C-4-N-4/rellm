# Homology phase 1–2 findings (2026-08-05)

Status: **method gate not passed** — the geometry does not beat the cheap
baseline out of sample. Per the proposal's own decision point, the homology
scoring layer should not be wired into guru on current evidence. The gold
set, the extraction infrastructure, and the secondary uses all survive.

## What was measured

Gold set: 56 cross-tradition concept pairs, human-adjudicated on a 0–4
depth-of-correspondence scale (amendment A9; `data/homology/gold/ratified.jsonl`).
Split 29 tune / 27 test, stratified by rating (A5). All scores are
null-calibrated percentiles per tradition pair (A4).

| method | selection (tune) | held-out test | notes |
|---|---|---|---|
| nomic embedding centroids (phase 1.5) | — | ρ **+0.147**, AUC **0.606** (full set) | the number to beat |
| Qwen2.5-7B-**Instruct** residual sweep, 29 layers × {mean,last} × {dom,cen} | ρ +0.247 (L27 cen/last) | ρ **+0.001**, AUC **0.516** | tune peak was pure selection noise — the split caught it |
| Qwen2.5-7B **base** residual sweep, same grid | ρ +0.262 (L26 cen/mean) | ρ **+0.138**, AUC **0.626** | real but ≈ baseline, not above it |

The difference-of-means method with register-matched negatives (`dom`) never
outperformed the plain centered centroid (`cen`) on tune — negative matching,
the proposal's central engineering bet, did not unlock a depth signal at
whole-chunk pooling granularity.

## Two findings worth keeping

**1. The baseline fails *informatively*.** Embedding centroids track surface/
topic overlap: five human-rated-1 false friends score above the 89th
percentile (theurgy↔Great Work 99.5, Wakan Tanka↔Julian 94.2), while the
human-rated-4 fanā↔Eckhart pair lands at 18.6 with negative cosine. The gold
set defeats lexical methods — it has real discriminating power, and the
false-friend problem is real at the representation level.

**2. Base > Instruct out of sample** (AUC 0.626 vs 0.516, ρ 0.138 vs 0.001).
Directionally consistent with the A7 suppression hypothesis — instruction
tuning damaging exactly the mind-attribution/supernatural directions this
corpus lives in — but from a single split at n=27, treat as a lead, not a
result.

## Why the method likely fails here

The adjudicator's depth ratings encode information that is not in the
passages: documented transmission history (Arabic Plotinus → Sufi metaphysics
behind the fanā 4), scholarly consensus about telos and frame, and
discipline-level debates (Idel vs Scholem behind the sefirot 0). A pooled
representation of what the corpus *says* cannot recover judgments grounded in
what scholarship *knows about* the corpus. Secondarily: whole-chunk mean/last
pooling dilutes any concept-specific component, and cells bottom out at n=10
teacher-tagged chunks.

## Recommendation

- **Do not wire homology edges into guru.** The human stays the depth oracle;
  cross-tradition equivalence claims keep the existing review-gate flow.
- **Keep the secondary uses** — they never depended on the gold gate:
  - *Taxonomy hygiene*: within-tradition cosine over the extracted directions
    is a redundancy/collision map; both direction sets are already on disk.
  - *Entanglement audit*: base-vs-finetuned tagger geometry comparison, now
    cheap (extraction is ~3 min/model on the 3090).
- **If the homology layer is ever revisited**, the leads in order: token-level
  pooling over concept-relevant spans (not whole chunks); cross-validated
  selection instead of split-half (n=56 is small for a 116-config sweep); a
  bigger gold set; and running the base-vs-instruct comparison properly as
  the suppression probe.

## Artifacts

- `data/homology/gold/` — candidates, ratified set, verdicts (phone app: `tools/adjudicate_gold.py`)
- `data/homology/directions/<model-slug>/` — states.npy + manifest, one per model, never mix
- `data/homology/baseline/` — `centroid-nomic.json`, `sweep-*.json` (full per-pair scores)
- `src/rellm/homology/` — extract / directions / geometry / goldset
- `tools/homology_extract.py`, `tools/homology_sweep.py`, `tools/homology_baseline.py`
