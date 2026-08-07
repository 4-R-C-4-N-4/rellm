# qwen-3-4b-guru v1 → v2 regression autopsy (2026-08-05)

**tl;dr.** The v2 regression is real but it is not a training problem — it is
**tag-corpus contamination from the new-tradition review push**, plus collateral
interference. The dominant mechanism: Greco-philosophical concept labels
(`theurgy`, `numerical_mysticism`, `divine_marriage`, …) were accepted onto
finnic/celtic/norse folk-magic chunks during review; v2 trained on them and
learned diluted concepts. This is the false-friend problem from the homology
work (docs/homology/), surfacing inside the *training corpus* instead of the
edge graph. Separately: the "base beats the fine-tunes" reading of the June
bench is a measurement artifact — v1 is genuinely the best tagger of the
three; the real anomaly is only v2 < v1.

## 1. The bench blind spot (base does NOT beat the fine-tunes)

`runs/bench/qwen3-4b-v1-v2-2026-06-10T00-49-04Z`, humans-as-truth showed base
0.608 > v1 0.598 > v2 0.579. But the human bench grades only curated cells,
and **77–83% of every model's emissions land on ungraded cells** where they
cost nothing:

| model | emissions | graded | ungraded (invisible) | graded precision |
|---|---:|---:|---:|---:|
| base | 6,118 | 1,045 | 5,073 (82.9%) | 0.711 |
| v1 | 4,247 | 1,004 | 3,243 (76.4%) | 0.716 |
| v2 | 4,451 | 990 | 3,461 (77.8%) | 0.699 |

Base emits 29.4 tags/chunk (vs ~13), invents 37 out-of-taxonomy IDs, runs
2.3× slower, and its recall edge is +24 accepted hits bought with ~1,900
extra emissions (~1% marginal precision). The shotgun exploits the grading
blind spot. **v1 vs v2 is the fair comparison (matched emission rates), and
v2 loses on precision and recall simultaneously.** Corollary for future
benches: report emissions-outside-curated-cells per model, or the metric
rewards over-emission.

## 2. Root cause A: cross-tradition label contamination (regressed concepts whose targets GREW)

Per-concept target counts, v1 export (`2026-05-26T13-03-07Z`) vs v2 export
(`2026-06-09T03-24-50Z`), joined with per-concept human-graded F1 deltas:

| concept | F1 v1→v2 | own targets | growth from new traditions |
|---|---:|---:|---|
| theurgy | 0.842 → 0.320 | 255 → 360 | **+109 (finnic 85, celtic 21, norse 3)** |
| numerical_mysticism | 0.483 → 0.240 | 351 → 412 | **+67 (finnic 52)** |
| divine_marriage | 0.556 → 0.235 | 122 → 147 | **+25 (finnic 23)** |
| renunciation_of_wealth | 0.600 → 0.400 | 158 → 190 | **+32** |
| heroic_furor | 0.667 → 0.400 | 124 → 134 | **+10** |

For every regressed concept whose targets grew, **~100% of the growth came
from finnic/celtic/norse**. All 85 finnic `theurgy` tags carry status
`accepted` — they came through the review gate, not raw from the teacher.
The new-tradition review pass accepted 2,903 / rejected 194 (93.7% accept).

The error class is exactly the homology gold set's false-friend axis: the
adjudication rated Iamblichean theurgy ↔ operative magic as *surface only*
(A-10, rating 1) and Kalevala word-magic as its own concept
(`word_power_incantation`, which already exists with 177 finnic chunks).
Väinämöinen's magic singing tagged `theurgy`/`numerical_mysticism` is a
reviewer merging on lexical/functional resemblance — the similarity bias the
homology docs describe, applied at the tag layer. v2 faithfully learned
"theurgy ≈ any operative magic" and collapsed on the Greco test cells.

## 3. Root cause B: interference (regressed concepts whose targets were FLAT)

`birth_of_word_in_soul` (−0.42), `angra_mainyu_principle` (−0.40),
`opposites_transcended` (−0.37), `apophatic_theology` (−0.32),
`inner_light` (−0.22), `evil_as_privation` (−0.20) all regressed with **±2%
target change**. Their own data didn't move; the corpus around them did
(+2,576 total targets, animism alone 0 → 377). Rebalancing shared features
under a shifted label distribution is classic SFT interference; the
base-vs-v1-vs-v2 entanglement audit (homology direction sets; merged models
exist under `out/qwen3-4b-guru*/merged`) can localize which concept pairs
collapsed, but the corpus-level cause is already established.

Rejection-signal warp (the 10× rejected-drop delta) was tested and is at
most minor: corr(F1 delta, rejection share) = −0.23, and the worst
regressions had ~5% rejection shares.

## 4. Remediation (proposed order)

1. **Quarantine + re-review the new-tradition tag layer.** Build a review
   queue of accepted (concept, tradition) tags where the concept's
   pre-existing distribution is overwhelmingly Greco-philosophical and the
   chunk is finnic/celtic/norse/native_american. Rank by incongruity. Queue
   only — apply stays with the human, per the standing review-gate flow.
   Likely outcome for the theurgy-class tags: **reassign** to the right
   concept (`word_power_incantation`, `sacred_names`, …), not delete.
2. **Add a tradition-affinity guard to future review passes**: a reviewer
   accepting a concept onto a tradition where it has never appeared should
   be a flagged, deliberate act, not a bulk accept.
3. **Taxonomy hygiene before v3**: within-tradition redundancy matrix from
   the existing direction sets; merge/split the near-duplicates the gold-set
   adjudication already flagged (`sunyata_emptiness` on taoism,
   `fana_annihilation` on Eckhart, `detachment_gelassenheit` span).
4. **Retrain v3 only after 1–3.** Same recipe as v2 — the recipe was never
   the problem. Expect the v2 blind-spot gains (animism, maat) to survive,
   since those were genuine new coverage.
5. Optional mechanism check: run the entanglement audit (base/v1/v2
   directions) to see which concept pairs v2 collapsed — useful as a
   regression test for the v3 retrain.

## Provenance

Benches: `runs/bench/qwen3-4b-v1-v2-2026-06-10T00-49-04Z` (323 chunks,
humans-as-truth + teacher view). Exports compared:
`2026-05-26T13-03-07Z` (v1) vs `2026-06-09T03-24-50Z` (v2). Snapshot for
statuses: `2026-06-09T03-24-41Z`. Analysis run 2026-08-05 in-session; scripts
inline (see session transcript), all counts reproducible from the artifacts
above.
