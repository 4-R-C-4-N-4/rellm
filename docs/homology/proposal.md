# rellm-homology

A concept-direction model for measuring cross-tradition conceptual homology.

**Status:** design / pre-build
**Scope:** new module in the rellm repo, sitting alongside the fine-tuned tagger — not a fine-tune itself.

## What this is

A derived model, not a trained one. It consists of:

- A set of extracted concept directions `v_{C,T}` — one per (concept C, tradition T) — living in the residual stream of a chosen base model.
- A geometry engine over those directions (cosine matrices, homology scoring, false-friend detection).
- Exporters that turn the geometry into graph edges and review flags for guru.

No gradient updates. The "model" is the direction set plus the geometry defined over it. It is cheap to rebuild and fully inspectable.

## The goal (single sentence)

Turn guru's cross-tradition equivalence claims from assertions into measurements — specifically, give the system the ability to **withhold and flag** equivalences that are surface/translation artifacts rather than genuine conceptual correspondences.

The point is the second capability. It is easy to make a synthesis engine assert more equivalences; the value here is a falsifiable signal that can say "these two concepts look alike but the model represents them as unrelated." That is a defense against perennialist over-reach / the false-friend problem, which is the central discipline-level risk for a comparative-synthesis product.

This is instrumentation, not an oracle. Cosine between concept directions is evidence of homology, model-dependent and reproducible — not a definition of it. The output is a signal for a human scholar or the study-mode layer to adjudicate, never a mechanical verdict on whether two concepts "are the same."

## Method

### Concept directions via difference-of-means

For concept C in tradition T:

```
# [reconstructed — original code block lost in paste]
pos = { h_L(x) : x a chunk in T tagged C }        # pooled hidden state, layer L
neg = { h_L(x) : x a matched negative from T }     # same tradition, same register, not-C
v_{C,T} = mean(pos) - mean(neg)                    # then unit-normalize
```

The crucial property: because positives and negatives are drawn from the same tradition, the tradition-common component (its prose style, register, characteristic vocabulary) largely cancels in the difference. What remains is, ideally, the concept component with the tradition baseline subtracted out.

This is what makes cross-tradition comparison defensible. Two directions extracted this way — each already centered against its own tradition's baseline — can be compared by cosine without the score being dominated by "how tradition A writes vs. how tradition B writes."

### Negative matching is make-or-break

If negatives are not matched to positives on length, register, and source, `v_{C,T}` captures style rather than concept, and the whole edifice measures nothing. Treat negative construction as the primary engineering effort, not an afterthought. Options, roughly in order of rigor:

1. Same-source, adjacent-passage negatives (best register match).
2. Concept-swapped negatives: passages about a different concept from the same tradition/text.
3. Synthesized hard negatives (see steering below), used sparingly and always mixed with real ones.

### Homology score

For a candidate cross-tradition pair (C in T1, C' in T2):

```
# [reconstructed — original code block lost in paste]
homology(C, T1; C', T2) = cos( v_{C,T1}, v_{C',T2} )
```

- High cosine → candidate homology → weighted graph edge.
- Low cosine on a lexically/translationally paired (C, C') → flagged false friend.

### Pooling and layer selection

- **Pooling:** mean-pool over content tokens vs. last-token — decide empirically on the validation set; don't assume.
- **Layer:** concepts surface at different depths. Sweep layers and select the layer (or a small ensemble of layers) that maximizes separation on the validation set below. Budget for this; it is real work, not a constant.

## Outputs into guru

- **Weighted graph edges** between concept nodes across traditions, cosine as edge weight → feeds the graph-RAG legs. Edges below a floor are omitted; edges flagged as false friends are recorded as negative evidence, not silently dropped.
- **Homology matrix / report artifact** for study-mode — the inspectable "shows its work" surface. For a paid research tool, auditability is a stronger sell than confident synthesis.
- **Disagreement flag** for the QA layer: when the synthesis LLM asserts an equivalence the geometry does not support (or vice versa), route to review. This is the direct tie-in to the existing dossier/study-mode QA pattern.

## Secondary functions (maintenance, not the point)

These fall out of the same primitive for free, but do not by themselves justify the module:

- **Taxonomy hygiene.** Within-tradition pairwise cosine over `{v_C}` is a redundancy/collision map. Above-threshold pairs are merge-or-split decisions to make before they poison training.
- **Entanglement audit.** Extract directions from the base vs. the fine-tuned tagger and compare geometry. Where the fine-tune collapsed a previously separate pair toward collinear, you have a spurious co-tagging artifact — a lead on the error floor.
- **Hard-negative synthesis.** For an entangled pair, steer a generator along `+v_C − v_{C'}` to produce C-but-emphatically-not-C' passages, label, fold in. Constructive use of steering to de-correlate the tagger.

## Module layout (proposed)

```
# [reconstructed — original code block lost in paste]
src/rellm/homology/
  extract.py      # hidden-state extraction, pooling, layer sweep
  directions.py   # direction store + provenance metadata
  geometry.py     # cosine matrices, null calibration, scoring
  goldset.py      # gold-set loading, separation metrics
  export.py       # guru edge/flag exporters
data/homology/
  gold/           # candidates.jsonl, ratified.jsonl
  directions/     # per-base-model direction sets
docs/homology/
  proposal.md     # this file
```

Every stored direction carries provenance metadata. Because the directions are base-model-dependent, the base-model id and extraction date are part of the artifact identity — a re-extraction against a different base is a different model and must not be silently compared against old directions.

## Evaluation (do this first — it is also the go/no-go)

Build a small human-adjudicated validation set before anything else. Construct it in two steps: an agent proposes candidates with evidence, then a human adjudicates.

### Step 1 — agent proposes gold candidates with evidence

Task an agent to surface candidate pairs of both kinds, each as a structured record:

```
# [reconstructed — original code block lost in paste; live schema in data/homology/gold/README.md]
{ id, kind_proposed: homology|false_friend, difficulty, a: {concept, tradition, term},
  b: {...}, claim, rationale, primary_evidence: [{source, quote}], secondary_citations, cell_n }
```

The point of Step 1 is speed: proposing candidates and pulling the supporting passages is the tedious part, and it's exactly what an agent is good at. The human then ratifies rather than starts from a blank page.

Two constraints that make this safe rather than circular:

1. **Evidence must be external, not the agent's confidence.** A candidate is only useful if it comes with primary passages and secondary citations a human can check. "The model thinks these correspond" is not evidence — it's the thing under test. The human adjudicates the evidence, not the assertion.
2. **The proposer must be independent of the base being scored.** If the same model class that will later be measured by the geometry also proposes the gold set, you validate the directions against the model's own priors and learn nothing. Use a different model (or at minimum a different base) for proposing, and lean on the external citations as the real ground truth. The human is the circularity-breaker.

### Step 2 — human adjudicates

The human accepts / rejects / reclassifies each candidate. Only human-ratified records enter the gold set, tagged with the human's verdict and the evidence that justified it — never the agent's proposed verdict on its own.

**Deliberately oversample false friends.** Agents are much better at proposing plausible homologies than plausible false friends — the bias runs toward finding similarity — so the harder and more valuable half of the set is the half the agent under-generates. Prompt for it explicitly (terms that translate alike but that scholarship distinguishes) and keep the borderline cases; a gold set of only easy homologies won't test the geometry's discriminating power.

### Then: measure separation

Measure whether cosine separates the two ratified sets. If it doesn't separate on cases a human already knows the answer to, the method doesn't work on your corpus and nothing downstream is trustworthy.

This set does double duty:

- It is the eval harness (layer/pooling selection tune against it).
- It is the honesty check on the whole proposal. This design was method-led — a paper's technique mapped onto the stack — so the standing risk is that it solves a problem guru doesn't actually have. The test is simple: do you feel the false-friend problem biting in current output? The validation set is where that question gets answered empirically. If the geometry can't separate known cases, or if you can't point to real bad equivalences in production, drop the homology layer and keep only the taxonomy-hygiene use.

## Build phases

1. **Validation set.** Agent proposes candidates with evidence (independent of the scored base); human adjudicates into a small ratified set of homologies + false friends. Go/no-go gate.
2. **Extraction + store** on a handful of concepts across 2–3 traditions. Negative construction. Layer/pooling sweep.
3. **Geometry + scoring.** Check separation against the validation set. Decision point: continue only if it separates.
4. **Scale + wire.** Full taxonomy; export graph edges; wire the disagreement flag into QA.
5. **Secondary audits.** Redundancy matrix; base-vs-fine-tuned entanglement; hard-negative synthesis.

## Caveats (carry these into the repo)

- **Cosine is evidence, not definition.** Model-dependent → the signal is reproducible and inspectable, not "true." Adjudication stays human.
- **Linear separability is assumed.** Difference-of-means is crude; fine theological distinctions may not be cleanly linear. This complements the tagger head, it does not replace it.
- **Negative matching is the failure mode.** Unmatched negatives silently convert the whole thing into a style detector. Guard this hardest.
- **Base-model selection matters specifically here.** The domain is mind-attribution and supernatural content — the exact directions that instruction/safety tuning tends to rotate and suppress. A generic instruction-tuned base may be systematically miscalibrated on precisely this domain. Measure that suppression on the candidate base (difference-of-means on a mind/supernatural probe) as a selection criterion before committing. "Represents supernatural claims weakly" is a mild defect elsewhere and a critical flaw for this corpus.

---

# Review amendments (2026-08-03)

Findings from a grounding pass against guru.db and the edge-review retro
(`docs/edges/edge-review-pass.md`). Original proposal above is unmodified;
strike or fold in as adjudicated.

## A1. Production evidence: partial

Of 4,457 reviewed 0.85-tier PARALLELS, 3.5% flipped to surface_only. Of the
four failure modes, only deity-name-without-shared-move is the conceptual
false-friend problem; the other three (hymn invocations vs philosophy,
title-page chunks, scholarly apparatus read as primary text) are chunk-genre
hygiene, which concept-level geometry will not fix. The stronger justification
is independence: the current edge layer is LLMs checking LLMs (Mistral
proposes, LLM reviews) with a shared bias toward similarity. The geometry is
the first non-LLM-opinion signal in the stack. Two measurements the review
flow structurally could not make:

- **Precision on the accepted 96.5%** — nobody has audited the accepts with an
  orthogonal instrument.
- **Recall** — high-cosine pairs with no existing edge are candidate missed
  parallels; the review flow can only re-judge what was proposed.

## A2. Data sparsity is the binding constraint (measured 2026-08-03)

5,340 chunks, 115 concepts, 23 traditions. Of 1,332 populated
(concept, tradition) cells: **331 have n≥30, 685 have n≥10, 647 have n<10**.
"Phase 4: full taxonomy" is not achievable on this corpus; expect defensible
directions for roughly a quarter of populated cells, concentrated in
western_esoteric / christian_mysticism / gnosticism / neoplatonism /
hermeticism. Consequences:

- Set an explicit min-n floor per cell; report coverage with every direction
  set. A cell below the floor yields **no measurement**, which must never be
  conflated with "no homology" downstream.
- Gold-set candidates are constrained to cells with n≥10 (else the gold pairs
  themselves are unmeasurable in phase 2/3).

## A3. New phase 1.5: embedding-centroid baseline

guru.db already has `chunk_embeddings`. Before any residual-stream work,
compute tradition-centered concept centroids from the existing embeddings
(mean of C-tagged chunks minus tradition mean) and run the gold set on that.
~A day of work. If centered centroids already separate, the residual-stream
machinery isn't earning its keep; if they don't, that validates the gold set's
difficulty and sets the baseline the directions must beat.

## A4. Null-calibrate cosines

Residual streams are anisotropic; raw cosines between arbitrary difference
vectors sit well above zero on shared dominant components. Do not threshold
absolute cosine. Score each pair as a percentile against a null distribution
of mismatched concept pairs drawn from the same tradition pair. Applies to the
embedding baseline too.

## A5. Gold-set circularity guard

The set is both the tuning target (layer/pooling sweep) and the go/no-go gate.
Split it (tune/test) or use leave-one-out across the sweep; do not tune and
judge on the same pairs.

## A6. Negatives from teacher labels only

"Not tagged with C" is contaminated by tagger recall misses (the base 7B
under-tags at recall ~0.21 — the reason rellm exists). Prefer concept-swapped
negatives (positively tagged with a different concept, same source); use
absence-based negatives only against 27B teacher labels, never student labels.

## A7. The base-model tension is internal

The entanglement audit requires extracting from the tagger's own base
(Qwen2.5-7B-Instruct) for comparability with the fine-tune. The homology
measurement wants a base that instruction/safety tuning has not rotated on
mind-attribution content. These are two different direction sets under the
provenance rule — extract both explicitly (e.g. Qwen2.5-7B base for homology,
-Instruct for the audit); never compare across them. Practical: extraction
needs HF weights with hidden-state hooks (not the served GGUFs); 7B bf16 fits
the 3090; one forward pass yields all layers, so the layer sweep is nearly
free. `llm stop` first — extraction and llama.cpp can't share the card.

## A8. Translation-layer caveat

The corpus is English translations, much of it Victorian (Budge, Taylor,
Mead). Tradition-centering mostly absorbs translator style (translator ≈
tradition here), but any source-language distinction the translation flattened
is unrecoverable by any method on this corpus. The measurement is homology of
translated presentations.

## A9. Graded verdicts, not binary (2026-08-03, from the first adjudication session)

The binary homology/false_friend gold label failed in practice: the
adjudicator found that nearly every pair is alike at one level of description
and divergent at another (the meditation pair is the clean example — "sit and
do nothing" is genuinely shared; telos and frame genuinely diverge). Forcing a
binary both pressures the judge and destroys exactly the structure the
instrument is supposed to detect. This is the Katz/perennialist level-
dependence problem showing up as an annotation-schema bug.

Resolution: the gold verdict is an ordinal 0–4 depth-of-correspondence rating
(anchors in `data/homology/gold/README.md`), plus "rejected" for unusable test
cases. Consequences for the eval design (supersedes the binary-separation
framing in the Evaluation section above):

- Primary metric: **Spearman rank correlation** between cosine and rating.
  The human signal needed is a stable ordering, not a fact of sameness —
  absolute-placement subjectivity washes out of rank statistics.
- Go/no-go: **tail separation** between ratings 0–1 and 3–4 (the derived
  binary). The 2s are excluded from the gate but kept as a prediction: a good
  instrument scores them between the tails.
- Downstream fit is better, not worse: guru edges want a graded weight
  anyway, and the false-friend flag becomes "high lexical/surface pull, low
  measured depth" rather than a hard class.

## Amended phase order

1. Gold set (as proposed; candidates constrained to measurable cells).
1.5. Embedding-centroid baseline from `chunk_embeddings` — first separation number.
2–5. As proposed, gated on the baseline result, with A4/A5 folded into the
     geometry and eval design.

## Gold-set provenance (phase 1 run, 2026-08-03)

Proposer: Claude (Fable 5) agents — independent of the scored base (Qwen).
Candidates constrained to cells with n≥10 from the 2026-08-03 guru.db state.
Four proposer lanes: Hellenic-esoteric cluster, East-West pairs,
ancient/mythic cluster (seeded with the production deity-name failure mode),
and a false-friend-only specialist lane targeting translation-vocabulary
collisions. False friends oversampled by construction (~50% of quota).
Candidates: `data/homology/gold/candidates.jsonl`; adjudication sheet:
`data/homology/gold/adjudication.md`. Only human-ratified records enter
`ratified.jsonl`.
