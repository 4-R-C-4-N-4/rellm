# edge-reranker — Build Spec

**Status:** ready for execution
**Owner:** Ivy
**Target executor:** local coding agent
**Type:** production build
**Depends on:** `docs/edges/edge-process-audit.md` (every bar below is set from a
measured number in that audit, not a guess)

---

## 1. Objective

Train a cross-encoder that scores a chunk pair for cross-tradition parallelism,
and deploy it **inside retrieval as a reranker** — not as a replacement for
Mistral in the judge seat.

That placement is the single most important finding of the audit, and it
inverts the original plan. The reasoning:

- A bi-encoder cannot rank within its own retrieved band (`AUC = 0.509`), and
  yield falls off a cliff after neighbour rank 5 (0.709 → 0.395 → 0.250).
- Every attempt to fix coverage by reallocating that same embedding signal
  failed under test — two independent mechanisms, both ~0.30 against ~0.70.
- But the rank 6–25 band still yields **0.395–0.442**. That is not noise. It
  is roughly two of every five pairs being genuine, with no way to tell which.

A cross-encoder attends across both passages jointly, so it sees what the
bi-encoder structurally cannot. Its job is to find the good ~40% in a band the
incumbent currently discards wholesale.

Model name: **`edge-reranker-v1`**
HF repo: `4rc4n4/edge-reranker` (not published until the ship gate passes)

### The falsifiable claim

> Within the rank 6–50 band, a cross-encoder can select a subset whose accept
> rate is ≥ 0.65 — comparable to what rank 1–5 already delivers.

If true, guru recovers real coverage in exactly the traditions the absolute
similarity floor locks out, at high precision. If false, the ceiling is the
embedding space itself and the next move is a better embedder, not more
retrieval policy. **Either outcome is a decision**, which is why this is worth
building before anything else on the list.

---

## 2. Quality bars

All measured on a held-out set split by text-pair group (see §4).

### Primary (ship gate)

| metric | bar | baseline it must beat |
|---|---|---|
| precision@top-20% within rank 6–50 | **≥ 0.65** | 0.40 (unranked band average) |
| AUC on held-out labelled pairs | ≥ 0.80 | 0.509 (bi-encoder similarity) |
| AB/BA symmetry | **1.000** | 0.790 (Mistral) |

Symmetry is exactly 1.0 *by construction* — score both directions and mean
them. This is a structural advantage over any generative judge and should be
asserted in a test, not measured hopefully.

### Secondary (report, do not gate)

- Calibration error (ECE) ≤ 0.10. The point is to replace
  `auto_promote_edges.py`'s inert 0.85 floor with a probability that means
  something; 93.4% of current `confidence` values are literally the same
  number.
- Inference throughput ≥ 5,000 pairs/sec batched on the 3090. A full
  5,556-chunk × top-50 rerank is ~140k pairs and must be minutes, not hours.

### Explicit non-goal

Beating Mistral as a *judge*. The reranker emits no justification, and
`auto_promote_edges.py:168` writes `justification` into live `edges`. The
generative judge stays where it is for now.

---

## 3. Model class

**`answerdotai/ModernBERT-large`** (395M), fine-tuned as a binary
cross-encoder.

- 8192 native context. Pair length is p99 1,907 / max 2,046 tokens, so pairs
  fit whole with no truncation policy needed.
- 19,338 labelled examples is squarely the right scale for this architecture —
  too small to fine-tune a 4B decoder well, ample for a 400M encoder.
- Trains in well under an hour on the 3090; the 4B tagger took ~18h.

Fallback if ModernBERT underperforms: `BAAI/bge-reranker-v2-m3` (568M), which
is already pretrained for exactly this pair-scoring objective and may need less
data to converge.

**Why not a generative model:** the output is one number. The tagger needed a
decoder because it emitted a variable-length list over a 110-concept
vocabulary. Spending a 4B decoder on a scalar is the wrong tool, and it cannot
give the calibrated probability that makes the promotion gate work.

---

## 4. Data

**Source:** `rellm snapshot`, then `rellm.edges.iter_reviewed_edges`. Already
implemented and tested.

**Volume:** 19,338 reviewed pairs with both bodies resolvable.

**Label:** post-review `edge_type`. `review_edges.py` rewrites it on
reclassify, and every rejection went through that path, so it is the corrected
label with no join to `review_actions`.

**Target:** binary. PARALLELS/CONTRASTS = 1, surface_only/unrelated = 0.
Balance is 56.9 / 43.1.

> **CONTRASTS is not learnable and must not be modelled.** 102 examples out of
> 19,338. Collapse it into the positive class and leave the
> PARALLELS-vs-CONTRASTS distinction to human review.

**Splits:** grouped by text-pair via `rellm.edges.group_key`, which yields
1,877 groups. A random pair-level split leaks — 19,338 pairs are drawn from
only 4,720 chunks, ~8 pairs each, so the same passage would appear on both
sides. Hold out whole groups, stratified by tradition pair.

### The hard-negative problem, and the fix

Every one of the 8,513 negatives is a pair Mistral proposed as positive and
Claude overturned — near-boundary hard negatives. There is **not one easy
negative in the set**, because `propose_edges.py:256` never wrote Mistral's own
negatives.

A model trained only on these will be sharp at the boundary and badly
calibrated on obvious non-matches, which is fatal for a reranker that will see
the whole rank 6–50 band.

**Fix, and it is nearly free:** mine easy negatives by sampling random
cross-tradition pairs. Their base rate of being a genuine parallel is
essentially zero, so they need no judging. Target roughly a 1:1 mix of
hard:easy negatives and verify on held-out data that adding them does not
degrade boundary precision.

---

## 5. Evaluation

The harness already exists and is the reason this build is measurable at all.

1. **Offline** — AUC, precision@k, calibration on the held-out groups.
2. **Rank-stratified** — precision within rank 6–50 specifically. This is the
   ship gate; overall AUC can look fine while the band that matters does not
   improve.
3. **Symmetry** — assert `f(A,B) == f(B,A)` exactly after direction-averaging.
4. **Live probe** — `tools/edge_candidate_probe.py` with `--strategy reranker`
   (needs adding). Three arms, judge calibration control. **A reranker that
   simulates well and loses the probe is rejected**, on precedent: hybrid and
   worklevel both simulated at or above the incumbent and lost 0.32/0.30 to
   0.74/0.68.

### Ceiling to state plainly

The labels are `agent-claude`'s review verdicts, not human ones — `reviewed_by`
is `ivy-desktop` for exactly one row out of 19,615. The model's ceiling is
Claude's curation, and no eval here can detect a systematic bias Claude shares.
That is acceptable for a reranker whose output is reviewed anyway; it would not
be acceptable for an auto-promotion gate. Do not wire this to
`auto_promote_edges.py` without a human-graded set first.

---

## 6. Deployment

Two changes in guru, in order, each independently useful:

1. **Widen retrieval, add a rerank stage.** `propose_edges.py` takes top-50 by
   rank instead of top-5-with-floor, scores them with the reranker, and passes
   the top-N to the LLM. The absolute similarity floor is retired — the
   reranker is the filter now, and it is the mechanism that lets distant
   traditions in without the yield collapse that sank `hybrid`.
2. **Persist negatives** (`propose_edges.py:256`). Needed regardless, and it
   feeds the next training round with the easy negatives currently thrown away.

Deliberately **not** in scope here, though all are in the audit's process list:
`edge_progress` tracking, recording presentation order, the recall probe.
Independent of the model and separately valuable.

---

## 7. Kill criteria

Stop and re-plan if:

- Held-out AUC < 0.70 after both base models are tried → the labels are noisier
  than assumed; go get a human-graded set before spending more.
- Rank 6–50 precision@top-20% < 0.50 → the cross-encoder is not seeing past the
  bi-encoder's ceiling. **The conclusion is then that the embedding space is
  the binding constraint**, and the next build is a domain-adapted embedder,
  not more reranking.

The second is a real possibility and the audit gives it genuine odds. It is
written here so that outcome counts as a finding rather than a failure.

---

## 8. Estimated effort

| step | effort |
|---|---|
| export + easy-negative mining | ~2h |
| train ModernBERT-large, grouped splits | ~1h GPU |
| offline eval + rank-stratified eval | ~2h |
| live probe (360 judge calls) | ~30m GPU |
| guru-side rerank integration | ~3h |

About a day. The tooling that would normally dominate this estimate —
extraction, splits, probe harness, judge setup — is already built and tested in
this PR.
