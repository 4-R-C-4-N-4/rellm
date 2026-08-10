# Edge process audit — 2026-08-09

Measured against snapshot `data/snapshots/2026-08-09T19-34-58Z-edges/`.
The live guru DB was not modified.

The original question was "which model should replace Mistral for edges."
The answer turns out to matter less than the pipeline around it: the judge is
one of six defects, and it is not the one costing the most coverage.

---

## 1. What works

Worth stating first, because the integrity layer is sound and shouldn't be
touched:

- **Zero orphaned live edges.** Every `edges` row of type PARALLELS/CONTRASTS
  has staged provenance.
- **Zero live-but-rejected edges.** `review_edges.py`'s `delete_live_edge`
  retraction path is working — rejects really do get pulled from the graph.
- **Post-review labels are recoverable.** `edge_type` is rewritten on
  reclassify, and every rejection went through the reclassify path with an
  explicit `reclassify_to`. `WHERE status IN (...)` gives clean gold labels
  with no join to `review_actions`.
- **The live graph is review-backed, not auto-promoted.** Only 45 of 11,147
  cross-tradition edges sit at `tier='proposed'`; 11,102 are `verified`.

---

## 2. The similarity floor is the largest single defect

`propose_edges.py` applies `--min-similarity 0.75` as a global absolute
threshold. Achievable cross-tradition similarity is not comparable across
traditions, so a global floor does not mean the same thing for each one.

Best-available cross-tradition neighbour similarity, by tradition:

| tradition | chunks | top-5 band mean | % of chunks with **no** neighbour ≥0.75 | proposals/chunk |
|---|---|---|---|---|
| hermeticism | 60 | 0.798 | 0.0% | **28.8** |
| christian_mysticism | 443 | 0.798 | 2.7% | 17.5 |
| western_esoteric | 974 | 0.787 | 4.3% | 5.3 |
| celtic | 191 | 0.765 | 12.6% | 3.5 |
| finnic | 275 | 0.759 | 17.5% | 3.3 |
| greek_mystery | 260 | 0.729 | **38.1%** | 11.1 |
| native_american | 249 | **0.753** | **28.1%** | **1.1** |

Read the native_american row against the floor: its top-5 band averages 0.753,
barely above 0.75, so roughly one of five candidates survives — which is
exactly the 1.1 proposals/chunk observed. Hermeticism's band sits at 0.798, so
all five survive *and* it lands in everyone else's top-5.

This is a rich-get-richer mechanism, and it is not driven by corpus size:
hermeticism has 60 chunks and 26x the per-chunk proposal rate of
native_american's 249.

**The floor is filtering on a dimension that carries no quality signal.**
Backfilling similarity onto all 21,673 edges and correlating against the
post-review verdict gives `AUC = 0.509` — chance. Accept rate is flat across
every similarity bucket (61.6% at [0.70,0.75), 54.9% at [0.75,0.80), 58.4% at
[0.80,0.85)).

So the gate excludes nothing harmful and systematically excludes exactly the
traditions a comparative-religion index most wants compared.

Resulting coverage — fraction of a tradition's chunks with any cross-tradition
edge:

```
hinduism        15.4%      neoplatonism         91.4%
native_american 20.9%      hermeticism          86.7%
celtic          28.3%      christian_mysticism  83.5%
finnic          38.9%      jewish_mysticism     82.0%
```

The graph is a Neoplatonic–Christian–Hermetic core with most other traditions
loosely attached.

---

## 3. There is no notion of "done"

**836 chunks (15% of the corpus) have never been evaluated at all** — never
appearing as source or target of any staged_edge. All 836 have embeddings, so
every one was eligible.

`propose_edges.py` is driven by ad-hoc `--tradition` / `--text` filters and
records nothing about what it has swept. A `tagging_progress` table exists for
the tag pipeline; there is no edge equivalent. Coverage is therefore a
function of which sweeps someone happened to run.

Worst affected: native_american (125 of 249 chunks, 50%), western_esoteric
(99), gnosticism (89), greek_mystery (88).

---

## 4. Negatives are discarded, which costs twice

`propose_edges.py:256` writes a row only when the verdict is PARALLELS or
CONTRASTS. Negative verdicts are dropped entirely.

1. **Re-runs re-pay.** `get_existing_pairs()` is built from stored rows, so a
   pair Mistral rejected is invisible to dedup and gets re-judged on every
   subsequent sweep. The pipeline is structurally incapable of remembering a
   "no."
2. **The training set has no easy negatives.** All 8,513 negatives are pairs
   Mistral called positive and Claude overturned — hard negatives at the
   decision boundary, with no obvious non-matches anywhere in the set.

---

## 5. Recall is capped and unmeasured

`--top-n 5` is a hard ceiling on how many parallels any chunk can have. 134
chunks had **every** proposal accepted at n≥5 — provably truncated, since the
cap bound before the judge did.

The live degree distribution is extremely skewed: mean 6.3, max 177
(`life-and-doctrines-boehme.116`), 680 chunks at degree 1, 168 at degree ≥20.

Nothing in the pipeline estimates what fraction of true parallels it finds.
Recall is not merely unmeasured, it is unmeasurable as built.

---

## 6. The judge is order-unstable

400-pair stratified audit, both presentation orders, temperature 0
(`runs/edges/symmetry/2026-08-09T19-39-50Z/`):

```
exact symmetry (4-way)    0.780
binary symmetry           0.790
FLIP RATE                 0.210    (84/400)
```

**Mistral reverses its verdict on 21% of pairs when A and B are swapped.**
PARALLELS is symmetric; nothing but presentation order changed. Flips
concentrate where discrimination matters: 25.7% on gold-negative pairs vs
15.8% on gold-positive.

This cannot be measured from the existing store — `pair_key()` canonicalises
the pair at `propose_edges.py:164` *before* insert, destroying the order the
model actually saw and leaving 0 reciprocal rows.

Mistral also emits `surface_only` only 6 times in 400, preferring `unrelated`
(77), while Claude's negatives are 8,338 surface_only vs 175 unrelated. The
two judges use inverted negative vocabularies, which is why exact and binary
symmetry are nearly identical — the 4-way distinction is barely in use.

**A negative result worth recording:** order-flip does *not* predict
disagreement with the Claude label (lift 0.98). I proposed it as a
grading-free filter for weak labels; it does not work. Mistral answers
PARALLELS on 79% of a 47.5%-positive sample, so its disagreement is dominated
by systematic positive bias rather than borderline-ness. Use out-of-fold model
disagreement for label cleaning instead.

Caveat on the accuracy figures: every reviewed row is a pair Mistral already
endorsed once, so re-judging measures self-consistency, not fresh accuracy.
What it validly establishes is that **Mistral cannot clean its own backlog.**

---

## 7. The confidence gate is inert

20,253 of 21,673 rows carry `confidence` exactly 0.85 (93.4%).
`auto_promote_edges.py:46` sets `DEFAULT_CONFIDENCE = 0.85` and filters `>=`.
The gate admits essentially everything. It reads as a quality threshold and
functions as a pass-through. Currently latent rather than damaging, since the
live graph is review-backed — but it is a live footgun for any future bulk
promotion.

---

## Recommended process changes

Ordered by coverage recovered per unit of work. None requires a new model.

**1. Replace the global floor with per-tradition-pair rank retrieval.**
Take top-k neighbours *within each target tradition* rather than top-5
globally. Every chunk then gets candidates from every tradition, and candidate
sets become comparable across pairs. Allocate k from the matrix's measured
accept rate — more for high-yield pairs, a non-zero floor for the rest so
distant traditions aren't frozen out. This is the single change that unblocks
hinduism/native_american/celtic.

**2. Add an `edge_progress` table** keyed by `(chunk_id, model, prompt_version)`,
mirroring `tagging_progress`. Makes "done" a fact rather than a memory, and
makes the 836-chunk gap visible instead of invisible.

**3. Persist negatives** with `status='rejected'`. Completes dedup, stops
re-paying for known negatives, and accumulates the easy negatives the training
set lacks.

**4. Record `presentation_order` and `similarity`** on each staged row so
symmetry stays auditable and retrieval stays tunable.

**5. Symmetrise at the process level.** Since the judge flips 21%, score both
orders and promote only on agreement; route disagreements to review. This
converts a silent 21% error rate into an explicit queue.

**6. Retire the confidence floor** until a calibrated score exists to replace
it.

**7. Build a recall probe.** Exhaustively evaluate all cross-tradition pairs
for ~30 chunks spanning central and peripheral traditions. That gives a
denominator, and it is the only way to know whether top-k is leaving parallels
on the table.

Once 1–4 are in, the judge swap becomes worth doing — and a cross-encoder is
the right class, because §2 proved bi-encoder similarity has no residual
discrimination and §6 showed a generative judge cannot hold a symmetric
relation stable. A cross-encoder scored in both directions and averaged is
symmetric by construction.

---

## Prototype: retrieval replay (`tools/edge_retrieval_sim.py`)

Offline replay against the snapshot's embeddings, read-only. Three strategies
at matched budget:

| metric | current | budget-only | **hybrid** |
|---|---|---|---|
| candidate pairs | 19,891 | 19,506 | **17,838** |
| chunk coverage | 89.5% | 72.4% | **100.0%** |
| tradition pairs (of 253) | 204 | 253 | **253** |
| balance entropy | 0.831 | 0.922 | 0.911 |
| yield on labelled subset | 0.549 | 0.569 | 0.562 |

Two intermediate failures worth keeping, because they define the design:

1. **Per-chunk top-k across all traditions is unaffordable.** With 23
   traditions even k=1 forces ~61k candidates; the first attempt produced
   253,710 pairs (12.8x budget).
2. **A pure tradition-pair budget starves chunks.** Allocating per pair and
   taking top-M inside each collapses onto hub chunks — coverage fell to
   72.4%, *worse* than the incumbent, even with a per-chunk cap.

The working design needs both halves: an unconditional per-chunk coverage
floor (every chunk gets its top-2 cross-tradition neighbours with **no**
similarity threshold — this is what lets distant traditions in at all), then
yield-weighted allocation of the remaining budget across tradition pairs.

Redistribution, candidates per chunk:

| gains | current → hybrid | | loses | current → hybrid |
|---|---|---|---|---|
| norse | 4.7 → 16.7 | | renaissance_hermeticism | 12.9 → 8.6 |
| sufism | 11.1 → 18.0 | | christian_mysticism | 11.7 → 7.8 |
| zoroastrianism | 7.0 → 13.6 | | western_esoteric | 7.8 → 4.8 |
| buddhism | 5.8 → 9.6 | | jewish_mysticism | 11.2 → 9.4 |
| taoism | 4.0 → 8.3 | | egyptian | 7.1 → 5.6 |
| gnosticism | 4.3 → 6.0 | | neoplatonism | 5.6 → 4.6 |

Every tradition reaches 100% chunk coverage, at ~10% *less* spend than the
incumbent.

### What this does not establish

**The yield of newly-explored candidates is unknown.** 10,722 of hybrid's
17,838 candidates carry no label, because nobody has ever judged a pair
outside the incumbent's reach.

The "known accepted edges re-selected" figures (current 57.0%, hybrid 36.0%)
must not be read as recall. Labels exist only where the incumbent looked, so
that metric scores the incumbent against its own output and penalises any
strategy that explores. It measures agreement with the existing graph, not
correctness.

**Decisive next experiment:** sample ~200 hybrid-only candidates — pairs the
incumbent never proposed — and judge them. Their accept rate is the number
that decides whether the coverage gain is real value or noise. Until that
runs, hybrid is established as cheaper, better-balanced and fully covering,
but *not* yet as higher-yield.

Tuning note: `shinto` (1 chunk) and `upanishads` (2 chunks) draw 65 and 64
candidates per chunk under the pair floor. Those are corpus stubs; either
raise the minimum tradition size or drop the pair floor for them.

## Probe result — hybrid's extra reach is NOT worth it as designed

360 judge calls, Qwen3.5-27B (thinking disabled), three arms scored in one
pass (`runs/edges/probe/2026-08-09T23-13-56Z/`):

| arm | n | judge positive | Claude positive | agreement |
|---|---|---|---|---|
| shared (calibration) | 114 | 0.719 | 0.570 | 0.623 |
| current_only | 120 | 0.742 | 0.575 | 0.650 |
| **hybrid_only** | 99 | **0.323** | — | — |

Judge bias from the calibration arm is +0.149, putting hybrid_only's
bias-corrected yield at **~0.17 against current_only's 0.74** — a 2.3x gap on
the raw rates, far larger than the judge noise it sits on. Verdict mix tells
the same story: hybrid_only came back `unrelated` 65 times out of 99, where
current_only returned `PARALLELS` 84 of 120.

**The mechanism is similarity, not territory.** Yield inside hybrid_only,
bucketed:

| similarity | n | yield |
|---|---|---|
| [0.70, 0.75) | 28 | 0.214 |
| [0.75, 0.80) | 61 | 0.361 |
| [0.80, 1.00) | 7 | 0.571 |

Whereas splitting the same pairs by whether their tradition pair had ever been
proposed before gives 0.330 (old territory) vs 0.273 (new territory) — nearly
identical, and the new-territory cell is only n=11.

So the newly reached traditions are **not** shown to be barren. Hybrid's
problem is that its unconditional per-chunk floor takes each chunk's top-2
neighbours *with no similarity threshold at all*, dragging in pairs down to
0.595 similarity. Hybrid's median candidate sits at 0.764 against
current_only's 0.782, and the tail is what kills it.

### Correction to §2

§2 concluded from `AUC = 0.509` that similarity carries no quality signal and
that tuning `min_similarity` was pointless. **That was overstated.** The AUC
was computed only on pairs that had already cleared the 0.75 floor — a
restricted range, which attenuates correlation by construction. This probe
samples below the floor and finds a clear monotone gradient (0.214 → 0.361 →
0.571).

The correct statement is narrower: similarity does not discriminate *within*
the retrieved band, but it does discriminate *at and below the boundary*. The
floor is doing real work. What's wrong with it is that it is a single global
constant applied to a space where each tradition pair has its own achievable
range — not that thresholding is wrong in principle.

### Revised design hypothesis (untested)

- **Drop the unconditional per-chunk floor.** 100% chunk coverage was the
  wrong target; optimising for it is what produced the thin tail. Some chunks
  genuinely have no cross-tradition partner and forcing them in buys noise.
- **Replace the global floor with a per-tradition-pair relative threshold** —
  e.g. a percentile within that pair's own similarity distribution. Distant
  traditions stop being excluded wholesale without the bottom being scraped.
- **Keep** the yield-weighted budget allocation and the tradition-pair
  exploration floor; nothing in this probe implicates them.

This hypothesis needs its own probe before it goes anywhere near guru. The
lesson from this round is that coverage and balance metrics are cheap and
simulable, and yield is neither — so no retrieval change should be adopted on
simulation alone.

### Operational finding

21 of 120 hybrid_only pairs failed with **body missing**, against 0 of 120 for
current_only. Hybrid's coverage floor forces in chunks whose corpus files are
absent (the 144 known missing). Any coverage-driven design needs a corpus
existence check before it spends judge calls.

## Probe 2 — work-level retrieval also fails, and the common cause is rank

Work-level retrieval (per-block p90 threshold, hierarchically shrunk yields,
no coverage floor) simulated *better* than every alternative — yield on the
labelled overlap 0.613 vs the incumbent's 0.549, at 12% less spend. It failed
the probe the same way hybrid did
(`runs/edges/probe/2026-08-10T01-02-10Z/`):

| arm | n | judge positive | Claude positive |
|---|---|---|---|
| shared (calibration) | 120 | 0.725 | 0.625 |
| current_only | 120 | 0.675 | 0.475 |
| **challenger_only** | 120 | **0.300** | — |

Bias +0.100, so ~0.20 corrected against current_only's 0.675. Hybrid scored
0.323 vs 0.742. **Two mechanisms with nothing in common structurally, near-
identical failure.** That is a property of the problem, not of either design.

### The cause: yield collapses past neighbour rank 5

Pooling both probes — 693 judged pairs — and computing each pair's
cross-tradition neighbour rank (the better of the two directions):

| rank | n | yield |
|---|---|---|
| 1–2 | 230 | 0.691 |
| 3–5 | 261 | **0.709** |
| 6–10 | 38 | 0.395 |
| 11–25 | 43 | 0.442 |
| 26–75 | 52 | 0.250 |
| 76+ | 69 | 0.232 |

There is a cliff immediately after rank 5. And the arms sit exactly where
their yields predict:

| arm | median rank |
|---|---|
| shared | 2 |
| current_only | 4 |
| hybrid_only | 16 |
| worklevel challenger | 65 |

Any strategy that adds coverage at fixed budget must reach past rank 5,
because ranks 1–5 are already taken. Past rank 5 the embedding signal is
spent. Both redesigns were elaborate ways of buying rank-20+ pairs.

### `--top-n 5` is very well chosen

Crossing rank against the similarity floor:

| | sim ≥ 0.75 | sim < 0.75 |
|---|---|---|
| **rank ≤ 5** | **0.715** (n=474) | 0.294 (n=17) |
| **rank > 5** | 0.377 (n=130) | 0.194 (n=72) |

Both dimensions carry independent signal, and the incumbent's conjunction
selects precisely the high-yield cell. `--top-n 5 --min-similarity 0.75` is
close to optimal for yield. Its cost is coverage, and the coverage it forgoes
is genuinely thin material.

This also kills the obvious simple fix — "keep top-5 by rank, drop the
absolute floor," which would add 565 native_american and 561 greek_mystery
candidate slots. Those pairs are the rank≤5/sim<0.75 cell, and it yields
0.294. **Caveat: n=17, 95% CI roughly 0.13–0.53** — suggestive, not settled,
though even the upper bound sits below 0.715. Worth a dedicated probe before
anyone acts on it.

### Revised conclusion

The Western centroid is a growth artifact of the corpus *and* a real property
of the current embedding space. Those are not in tension, and the second one
means **no reallocation of that embedding signal fixes the first.** Distant
traditions' nearest neighbours are genuinely far, and far pairs yield poorly
however they are selected.

The lever is therefore not retrieval policy. It is one of:

1. **Better embeddings.** `nomic-embed-text` is general-purpose. A
   domain-adapted embedder might place Kalevala↔Mabinogion or
   Hindu↔Neoplatonic material where a general model cannot.
2. **A cross-encoder reranker over a wider net** — retrieve top-50 by rank
   (cheap), rerank with a cross-encoder (cheap), spend judge calls only on
   survivors. The rank 6–25 band yields 0.395–0.442, which is *not nothing*:
   if a reranker can separate the good ~40% there, that is real recovered
   coverage at acceptable precision.
3. **Accept the ceiling** and state plainly that the graph covers what the
   embedding space can reach.

Option 2 relocates the model work. The cross-encoder's value is not as a
Mistral replacement in the judge seat — it is as a *retrieval* component that
sees what a bi-encoder structurally cannot, trained on exactly the 19,338
labelled pairs already in hand.

## Artifacts

| path | what |
|---|---|
| `tools/edge_matrix.py` | tradition/text outcome matrix, Wilson-bounded rates |
| `tools/edge_similarity_backfill.py` | adds `staged_edges.similarity`; similarity-vs-outcome AUC |
| `tools/edge_symmetry.py` | AB/BA consistency audit |
| `src/rellm/edges.py` | guru v2 prompt contract, `iter_reviewed_edges`, leakage-safe `group_key` |
| `runs/edges/edge_matrix_{tradition,text}.tsv` | 194 tradition pairs, 1,926 text pairs |
| `runs/edges/symmetry/2026-08-09T19-39-50Z/` | 400-pair audit, results + summary |

Both write-capable tools refuse any path resolving to `cfg.guru.db` or inside
the guru repo.
