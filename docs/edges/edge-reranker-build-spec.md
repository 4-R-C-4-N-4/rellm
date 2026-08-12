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

All measured on a held-out set split by **work-pair** group (see §4).

### Primary (ship gate)

| metric | bar | baseline it must beat |
|---|---|---|
| precision@top-20% within rank 6–50 | **≥ 0.65** | 0.40 (unranked band average) |
| AUC on held-out labelled pairs | ≥ 0.80 | 0.509 (bi-encoder similarity) |
| AB/BA symmetry | **1.000** | 0.790 (Mistral) |

Symmetry is exactly 1.0 *by construction* — score both directions and mean
them. This is a structural advantage over any generative judge and should be
asserted in a test, not measured hopefully.

### Where the band labels come from — resolve before training

The primary gate is measured within rank 6–50, but labels exist almost
exclusively where the incumbent looked — rank ≤5, sim ≥0.75 — so the held-out
grouped split contains almost no pairs in the gated band. The only labelled
data there today is ~130 pairs pooled from the two probes, and those carry
Qwen-27B judge labels with a measured +0.10–0.15 positive bias, not the Claude
labels everything else is built on. Measured on that, the gate cannot
distinguish 0.65 from 0.50 — which are the ship and kill thresholds.

**First deliverable of the build: a frozen band eval set.**

Order of operations matters here, and the obvious order is wrong. Partition
the work-pair groups (§4) into train and held-out *first*, stratified by
tradition pair. Then sample 300–500 rank 6–50 pairs **from held-out groups
only**, stratified by tradition pair and by rank sub-band (6–10, 11–25,
26–50). Grade them with Claude — the same label source as the training set, so
no new inconsistency — and freeze the artifact.

Sampling the eval set first and excluding its groups afterwards would pull
roughly 4,000 labelled pairs out of training for nothing. Partitioning first
makes the band eval set free.

The ship gate and the kill criterion are both measured on this set; the pooled
probe pairs are corroborative only.

### Secondary (report, do not gate)

- Calibration error (ECE) ≤ 0.10. The point is to replace
  `auto_promote_edges.py`'s inert 0.85 floor with a probability that means
  something; 93.4% of current `confidence` values are literally the same
  number.
- Inference throughput: report it, and expect **tens of pair-directions per
  second, not thousands**. A 395M cross-encoder over ~1.5–2k-token pairs costs
  ~1.5 TFLOPs per forward pass; at realistic 3090 fp16 utilisation that is
  ~20–40 pairs/sec, and direction-averaging doubles the work. The full
  5,559-chunk × top-50 rerank (~140k pairs, ~280k directions) is a **2–4 hour
  batch job**. That is fine for a sweep that runs occasionally; an earlier
  draft's 5,000 pairs/sec bar was short-sequence-reranker territory and is
  unachievable at this pair length.

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
- 20,379 labelled examples is squarely the right scale for this architecture —
  too small to fine-tune a 4B decoder well, ample for a 400M encoder.
- Trains in a few hours on the 3090 — ~30k examples × ~1.5k tokens × a few
  epochs is roughly 2–6h depending on epochs and packing; the 4B tagger took
  ~18h.

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

**Volume:** 20,379 reviewed pairs, every one with both bodies resolvable.

> Measured on snapshot `2026-08-12T00-05-42Z-edges-phase1`, which supersedes
> the audit's 19,338. Two things changed: the audit dropped ~277 pairs whose
> chunk files were missing from the corpus, and **that gap is now closed** —
> all 5,559 chunk ids resolve to exactly 5,559 corpus TOMLs, so
> `iter_reviewed_edges` discards nothing. The remainder is review carried out
> since 2026-08-09.

**Label:** post-review `edge_type`. `review_edges.py` rewrites it on
reclassify, and every rejection went through that path, so it is the corrected
label with no join to `review_actions`.

**Target:** binary. PARALLELS/CONTRASTS = 1, surface_only/unrelated = 0.
Balance is 11,343 / 9,036 — 55.7 / 44.3.

> **CONTRASTS is not learnable and must not be modelled.** 108 examples out of
> 20,379. Collapse it into the positive class and leave the
> PARALLELS-vs-CONTRASTS distinction to human review.

### Splits: group by work pair, stratify by tradition pair

These are two different jobs and the units differ.

**Group by work pair.** A random pair-level split leaks badly — 20,379 pairs
are drawn from only 4,674 chunks, ~9 pairs each, so the same passage lands on
both sides. But grouping by *text* pair, which is what `rellm.edges.group_key`
currently does, is not enough either: `sources/works.toml` declares 11 works
spanning many text ids each (`agrippa-natural-magic` is 74, `dhammapada` 26,
`corpus-hermeticum` 17), and **178 of the 229 texts in the labelled set belong
to a multi-text work**.

| grouping unit | groups | mean pairs/group |
|---|---|---|
| tradition pair | 195 | 104.5 |
| **work pair — use this** | **824** | **24.7** |
| text pair (`group_key` today) | 2,070 | 9.8 |

**39.8% of pairs (8,110 of 20,379) sit in a text-pair group finer than their
work-pair group.** A text-level split can therefore put Agrippa chapter 3 in
train and chapter 47 in test, or two tractates of the *Corpus Hermeticum* on
opposite sides — same author, same treatise, same vocabulary and doctrine.
That inflates held-out AUC, and both the 0.80 ship bar and the 0.70 kill bar
are read off that number. 824 groups at ~25 pairs each is ample, so the
correction is free.

> **Work to do in step 2:** `rellm.edges.group_key` needs a work-aware variant
> that reads `sources/works.toml` and falls back to the text id for texts
> belonging to no declared work. Its docstring currently calls text-pair
> grouping "leakage-safe", which this supersedes.

**Stratify by tradition pair.** That is where the variation the reranker exists
to address actually lives — hermeticism at 28.8 proposals/chunk against
native_american's 1.1 — so it is what makes the held-out set representative of
the coverage question. Tradition pair is the wrong *split* unit: holding out
whole tradition pairs would measure generalisation to unseen tradition
combinations, a harder and different question than the one deployment asks.

> **Residual leakage, to report rather than engineer around:** work-level
> grouping still permits leakage between different works by the same author —
> Boehme has more than one treatise in the corpus. Author-level grouping would
> be coarser again for diminishing return. State it in the eval's limitations.

### The hard-negative problem, and the fix

Every one of the 9,036 negatives is a pair Mistral proposed as positive and
Claude overturned — near-boundary hard negatives. There is **not one easy
negative in the set**, because `propose_edges.py` never wrote Mistral's own
negatives.

> Phase 0.1 has since fixed that: negatives now persist as
> `status='rejected'`, `reviewed_by='model-negative'`. They accumulate from
> the next sweep onward, so this mitigation is for *this* training round. A
> later round gets real judge negatives for free.

A model trained only on these will be sharp at the boundary and badly
calibrated on obvious non-matches, which is fatal for a reranker that will see
the whole rank 6–50 band.

**Fix, and it is nearly free:** mine easy negatives by sampling random
cross-tradition pairs. Their base rate of being a genuine parallel should be
near zero, so they need no judging. Target roughly a 1:1 mix of hard:easy
negatives and verify on held-out data that adding them does not degrade
boundary precision.

Two checks on that mitigation, both cheap:

- **Spot-check the "no judging needed" assumption before minting thousands of
  negatives.** Rank 76+ pairs yielded 0.232 in the probes. Those were
  strategy-selected rather than uniform-random, so truly random pairs should
  sit far lower — but this corpus is curated for cross-tradition resonance,
  and "essentially zero" is an assumption where the measurement costs ~15
  minutes: judge ~100 random pairs. If the real base rate is ≥5%, a 1:1 mix
  injects meaningful label noise into the negative class.
- **Cover the deployment band.** Positives and hard negatives all sit at rank
  ≤5 / sim ≥0.75; random easy negatives sit at very low similarity. Rank 6–50
  — the band the model is deployed on — is out-of-distribution relative to
  *both* clusters, and a model can separate easy negatives on a
  topical-similarity shortcut without learning anything in the band that
  matters. Mine part of the negative budget from the rank 6–50 band itself
  (~60% negative per the probes). Band negatives need labels — judge-labelled
  with the known bias, or extend the Claude grading pass from §2 beyond the
  frozen eval set — and the band eval is what verifies the shortcut didn't
  happen.

---

## 5. Evaluation

The harness already exists and is the reason this build is measurable at all.

1. **Offline** — AUC, precision@k, calibration on the held-out groups.
2. **Rank-stratified** — precision within rank 6–50 specifically, measured on
   the frozen Claude-graded band set from §2. This is the ship gate; overall
   AUC can look fine while the band that matters does not improve, and the
   grouped held-out split contains almost no band pairs of its own.
3. **Symmetry** — assert `f(A,B) == f(B,A)` exactly after direction-averaging.
4. **Live probe** — `tools/edge_candidate_probe.py` with `--strategy reranker`
   (needs adding). Three arms, judge calibration control. **A reranker that
   simulates well and loses the probe is rejected**, on precedent: hybrid and
   worklevel both simulated at or above the incumbent and lost 0.32/0.30 to
   0.74/0.68.

### Ceiling to state plainly

The labels are `agent-claude`'s review verdicts, not human ones — `reviewed_by`
is `ivy-desktop` for exactly one row in the whole reviewed set. The model's
ceiling is Claude's curation, and no eval here can detect a bias Claude shares.
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
   traditions in without the yield collapse that sank `hybrid`. Keep an
   existence check on chunk bodies before reranking: a cross-encoder needs
   bodies, and the audit's 273 unresolvable chunk ids — since closed, all
   5,559 now resolve — came from a re-chunk, so a future one can reopen it.
   `edge_candidate_probe.py` already applies this check to every arm.
2. ~~**Persist negatives.**~~ **Done in Phase 0.1**, along with
   `edge_progress`, `similarity` and `presentation_order`. The next training
   round inherits real judge negatives rather than mined ones.

Deliberately **not** in scope here: the recall probe, and the calibrated
promotion gate. Independent of the model and separately valuable.

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
| Claude-graded band eval set (300–500 pairs, frozen) | ~2h |
| export + easy-negative mining + base-rate spot check | ~2–3h |
| train ModernBERT-large, grouped splits | ~2–6h GPU |
| offline eval + rank-stratified + text-disjoint sanity check | ~2h |
| live probe (360 judge calls) | ~30m GPU |
| guru-side rerank integration | ~3h |

Realistically two days rather than one — the band eval set and the honest
training time push it past a single day. The tooling that would normally
dominate this estimate — extraction, splits, probe harness, judge setup — is
already built and tested in this PR.
