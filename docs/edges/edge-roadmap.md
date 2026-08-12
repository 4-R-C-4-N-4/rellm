# Edge pipeline — execution roadmap

**Status:** Phase 0 shipped (guru #58, #59) · **Phase 1 HELD — see the
2026-08-12 addendum at the end of this document.** Two findings from Phase 1
step 1 undercut the plan as written: the training labels are not reproducible,
and the model's deployment target was measured and found structurally inert.
The addendum records both and the decision they force. Phases 1–3 below are
kept as the record of the plan they amend.
**Scope:** the whole path to a fixed edge pipeline, across both repos.
**Inputs:** `edge-process-audit.md` (findings), `edge-reranker-build-spec.md`
(the model)
**Working snapshot:** `data/snapshots/2026-08-12T00-05-42Z-edges-phase1`

Sequenced by dependency rather than by importance. Measurements are dated
where they have been re-checked: the audit's figures were true of the
2026-08-09 snapshot, and two of them have since moved.

---

## The export boundary — read this before touching anything

sqlite is the workbench. **The deliverable is the Postgres staging DB**, loaded
from `export/guru-corpus.sql.gz` by `scripts/export.py`. Every change below is
graded against that boundary first.

What actually crosses it:

| sqlite | crosses? | how |
|---|---|---|
| `edges` (live) | **yes** | `load_edges()` — `SELECT source_id, target_id, type, tier, justification FROM edges`, unfiltered |
| `staged_edges` | **no** | never read by `export.py` |
| `staged_tags`, `review_actions`, `tagging_progress` | **no** | never read |
| chunks | yes, but **from corpus TOMLs on disk** (`CORPUS_DIR.rglob("chunks/*.toml")`), not from `nodes` |

**This is the load-bearing fact for the whole plan: `staged_edges` is a
workbench table that never leaves sqlite.** The review gate — `promote_to_live`
in `review_edges.py` — is the only path into `edges`, and `edges` is the only
edge source the export sees. So Phase 0 and Phase 1 cannot affect staging at
all, and only Phase 2 (indirectly) and Phase 3.1 (directly) touch it.

### Constraints the plan must respect

1. **No Postgres schema changes.** `SCHEMA_VERSION = 4` is pinned, and
   `export.py` states guru-web's `EXPECTED_SCHEMA_VERSION` must advance in the
   same deploy. Nothing in this roadmap needs a DDL change — keep it that way,
   because the moment it does, this stops being a guru-only change.
2. **The load is atomic** — `corpus_new` built, validated inline, then
   `ALTER SCHEMA … RENAME` swapped. A validation failure rolls the whole thing
   back, so a bad export is a total outage of the corpus refresh, not a partial
   one.
3. **`edges` PK is `(source, target, edge_type)`.** Duplicate emission fails the
   load.

### Pre-existing bug this plan would have made worse

`load_chunks()` emits chunks from corpus TOMLs, but `load_edges()` emits *all*
of `edges` with no endpoint check, and `emit_validation()` checks
`summary_nodes` child ids against chunks — **but never edge endpoints**.

Measured on the 2026-08-09 snapshot:

- **929 live edges reference a chunk endpoint with no corpus file** (63 of them
  cross-tradition PARALLELS/CONTRASTS).
- They export as dangling references, the load succeeds, and guru-web fails to
  resolve them at render time.

> **Re-measured 2026-08-12: zero.** All 5,559 chunk nodes resolve to exactly
> 5,559 corpus TOMLs. The subsplit label separator fix (guru #56) and the
> mabinogion re-chunk sync closed the gap. The missing endpoint check in
> `emit_validation()` is still real, but it now guards against regression
> rather than fixing a live fault — see 0.4.

## The consumer: what guru-web actually does with edges

This is what the whole plan is betting on improving, so it decides whether the
bet pays. `src/lib/reader.ts:getRelatedPassages` is the query:

```sql
SELECT e.edge_type, e.tier, e.annotation, p.id AS partner_id, ...
  FROM edges e
  JOIN chunks p ON p.id = CASE WHEN e.source = $1 THEN e.target ELSE e.source END
 WHERE (e.source = $1 OR e.target = $1)
   AND e.edge_type = ANY(ARRAY['PARALLELS','CONTRASTS'])
 ORDER BY e.edge_type = 'CONTRASTS',
          CASE e.tier WHEN 'verified' THEN 0 WHEN 'proposed' THEN 1 ELSE 2 END,
          p.id
```

Three facts that change the plan:

1. **There is no quality signal in the ordering.** It sorts PARALLELS before
   CONTRASTS, then by tier — but **11,000 of 11,102 cross-tradition edges are
   `verified` PARALLELS**, so both keys are constant for nearly every chunk.
   The effective sort is the final tiebreak: `p.id`, **alphabetical partner
   chunk id**.
2. **There is no `LIMIT`.** Every edge for the chunk is fetched. The UI slices
   at `RELATED_VISIBLE = 10` and hides the rest behind a "N more" disclosure.
3. **`weight` is never referenced anywhere in guru-web.** Zero occurrences.

### Why this caps the bet

**467 chunks — 13.2% of those with any edges — already have more than 10
partners**, so what a reader sees is the alphabetically-first 10 of up to 177.
For those chunks the ranking is not merely weak, it is arbitrary.

That splits the payoff of the plan in two:

- Improving edge **precision** (fewer bad edges) helps immediately, because bad
  edges stop occupying the list at all.
- Improving edge **coverage** — which is the entire point of Phase 2 — makes
  the visible top-10 *worse* without a ranking signal, because more edges
  compete for the same 10 alphabetical slots.

**So the guru-web change is a prerequisite for Phase 2, not a follow-on.**
Shipping wider retrieval into an unranked, unlimited query degrades the reading
experience for exactly the hub chunks that matter most.

### A free win, no schema change

`corpus-schema.sql` already has `weight REAL` on `edges`, documented as "an
optional similarity / relevance score attached by the pipeline for downstream
ranking." `load_edges()` hardcodes `"weight": None` — it has always been NULL.

The reranker score is exactly that value. Populating it needs **no DDL change
and no `SCHEMA_VERSION` bump**. But it is inert until guru-web sorts by it, so
"free win" understates the coupling: Phase 2.4 (populate) and Phase 2W (sort by
it) only pay off together.

---

## The shape of it

```
  PHASE 0 ✓ ────────────► PHASE 2 ──────► PHASE 3
  guru: stop data loss    guru: rerank    guru: consolidate
        (shipped)               ▲
                                │
  PHASE 1 ──────────────────────┘
  rellm: build the reranker      ▲
        (HELD — see addendum)    │
                            DECISION GATE
```

Phase 0 was guru-side schema and write-path work and is done. Phase 1 started,
and its first deliverable invalidated its own gate — see the addendum. Phase 2
needs a working Phase 1 through the gate, in whatever form Phase 1 resumes.

---

## Phase 0 — stop the data loss (guru, ~4h, no model required) — SHIPPED

> 0.1, 0.2 and 0.3 landed in guru #58 and #59. 0.4 re-measured to a
> no-op; see below. Kept in full because the reasoning is the record of
> why each column exists.

**Done before the next sweep ran**, which was the point: every one of these
was losing information irrecoverably while it went unfixed.

### 0.1 Persist negatives — `propose_edges.py:256`

The single highest-value line-change in the whole plan. Currently only
PARALLELS/CONTRASTS are written, so:

- Re-runs re-pay for every pair Mistral already rejected. `get_existing_pairs()`
  cannot see a "no."
- **The training set has no easy negatives**, which is a live problem for
  Phase 1 (see the spec's §4 mitigation).

Write negatives with `status='rejected'`, `tier='proposed'`, and a
`reviewed_by` sentinel like `model-negative` so they are distinguishable from
curated rejections and never enter the review queue.

> Care needed: `idx_staged_edges_provenance_unique` is `WHERE status='pending'`,
> so the existing ON CONFLICT clause will not fire for rows written straight to
> `rejected`. Either widen the index or upsert on a different predicate — this
> is the one place in Phase 0 that can silently duplicate rows, and the
> corruption mode is quiet and cumulative: duplicated negatives pollute the
> exact training set this plan exists to build. **Test it on a DB copy with a
> deliberate double-run and assert the row count** before the first real sweep
> writes through it.

### 0.2 Schema — one migration, `v3_009_edge_provenance.sql`

```sql
ALTER TABLE staged_edges ADD COLUMN similarity REAL;
ALTER TABLE staged_edges ADD COLUMN presentation_order TEXT;  -- 'ab' | 'ba'
CREATE TABLE IF NOT EXISTS edge_progress (
    chunk_id     TEXT PRIMARY KEY REFERENCES nodes(id),
    model        TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    completed_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
```

- `similarity` — the retrieval score, never persisted, which is why
  `--min-similarity` was never tunable against outcomes. Backfillable for
  existing rows — but **not with `tools/edge_similarity_backfill.py` as it
  stands**: that tool refuses any path resolving to the live guru.db, by
  design. Port the backfill logic into a guru-side script and leave the rellm
  guard intact; do not add an override flag, because the guard's entire value
  is that rellm tooling *categorically* cannot write to the live DB. Risk
  class of the backfill itself is low: it fills an all-NULL column with values
  recomputable from on-disk embeddings, so recovery from any mistake is
  re-NULL and re-run. Copy-test, then apply with before/after checks (row
  count unchanged, zero non-NULL values overwritten, no inserts/deletes) —
  proportionate ceremony, no more.
- `presentation_order` — `pair_key()` canonicalises at `propose_edges.py:164`
  *before* insert, destroying the order the model saw. Record which passage was
  A, or AB/BA stays permanently unauditable in the store.
- `edge_progress` — mirrors `tagging_progress`. **836 chunks (15%) have never
  been evaluated** and nothing records what has been swept, so coverage is a
  function of which ad-hoc `--tradition`/`--text` runs someone remembered.
  **Seed it empty; do not backfill from history.** Nothing recorded which
  chunks were actually swept, so any backfill is inference ("appeared as a
  source at some point"), and it would mark chunks done under the
  top-5-with-floor regime that Phase 2 retires — suppressing exactly the
  re-coverage the wider sweep is for. Populate going forward only.

### 0.3 `serve-llama.sh` context bug

`CTX_SIZE="32768"` is hardcoded, not `${CTX_SIZE:-32768}`. Raising `--parallel`
via a wrapper silently shrinks each slot's context — at `PARALLEL=8` that is
4096/slot, which truncates a thinking model mid-JSON. One word, and it will
bite the Phase 1 probe runs otherwise.

### 0.4 Stop exporting dangling edges — `export.py:load_edges`

> **Re-measured 2026-08-12: the dangling edges are gone.** All 5,559 chunk
> nodes resolve to exactly 5,559 corpus TOMLs; zero dangling endpoints in live
> `edges`, zero in `staged_edges`. The 929 figure was real on 2026-08-09, and
> the corpus work since — the subsplit label separator fix (guru #56) and the
> mabinogion re-chunk sync — closed it. **The filter half of this item is now
> a no-op and the Phase 2 sequencing constraint is void.**

What remains is the cheap half, and it is worth keeping: `emit_validation()`
still never checks edge endpoints, so if this regresses the export succeeds
and guru-web fails to resolve at render time. Add the endpoint check as a
regression guard — roughly twenty minutes, no longer an hour, and no longer
blocking anything.

**Phase 0 exit:** a sweep can run without losing negatives, provenance, or
progress. **0.1, 0.2 and 0.3 shipped** (guru #58, #59); 0.4 reduced to a
validation guard.

**Export impact of Phase 0: none.** Every change is confined to `staged_edges`
and the new `edge_progress` table. `edges` is untouched, so staging sees no
behavioural change at all.

---

## Phase 1 — build the reranker (rellm, ~2 days) — NEXT

Full detail in `edge-reranker-build-spec.md`. Sequence:

Working snapshot: `data/snapshots/2026-08-12T00-05-42Z-edges-phase1`, taken
after Phase 0 landed, so `similarity` is populated natively and no rellm-side
backfill is needed. **20,379 reviewed pairs**, none dropped for missing bodies.

1. **Partition first, then build the band eval set.** Split the 824 work-pair
   groups into train / held-out, stratified by tradition pair. Then sample
   300–500 rank 6–50 pairs **from held-out groups only**, stratified by
   tradition pair and rank sub-band, Claude-grade them, and freeze. Doing it
   in this order costs no training data; sampling first and excluding groups
   afterwards would drop ~4,000 labelled pairs. The decision gate below is
   measured on this set — without it the only band labels are ~130 probe pairs
   carrying Qwen-27B judge labels (+0.10–0.15 bias), which cannot distinguish
   the 0.65 ship bar from the 0.50 kill bar.
2. Export the 20,379 labelled pairs via `rellm.edges.iter_reviewed_edges`.
   **Group by work pair, not text pair** — `group_key` needs a work-aware
   variant reading `sources/works.toml`. 178 of 229 texts belong to a
   multi-text work, and 39.8% of pairs sit in a text-pair group finer than
   their work-pair group, so text-level splits put chapters of one treatise on
   both sides. 824 work-pair groups at ~25 pairs each. See the spec's §4.
3. Mine easy negatives from random cross-tradition pairs — target ~1:1 against
   the 9,036 existing hard negatives. Spot-check the assumed ~0 base rate by
   judging ~100 random pairs first (rank 76+ yielded 0.232 in the probes;
   uniform random should be far lower, but measure it). Mine part of the
   negative budget from the rank 6–50 band itself so the deployment band is
   not out-of-distribution relative to both training clusters.
4. Train ModernBERT-large as a binary cross-encoder. Collapse CONTRASTS into
   positive; 108 examples is not learnable.
5. Offline eval: AUC, calibration, and **precision within rank 6–50 on the
   frozen band set** — overall AUC can look healthy while the band that
   matters does not move. Report the residual author-level leakage that
   work-pair grouping still permits rather than engineering around it.
6. Live probe via `tools/edge_candidate_probe.py --strategy reranker`.

### DECISION GATE

Measured on the frozen Claude-graded band set (step 1), with the live probe as
confirmation — not on the pooled probe labels alone.

| outcome | next |
|---|---|
| rank 6–50 precision@top-20% **≥ 0.65** | proceed to Phase 2 as written |
| **0.50–0.65** | proceed, but keep the similarity floor as a backstop and widen retrieval to top-20 rather than top-50 |
| **< 0.50** | **stop.** The embedding space is the binding constraint. Phase 2 becomes "evaluate a domain-adapted embedder" and the reranker is shelved. |

That third row is a real possibility, not a formality. Two retrieval redesigns
already failed here, and the reason both failed — the rank-5 cliff — is a
property of the embedding space that a cross-encoder is being asked to see
past. If it cannot, that is a finding worth having cheaply.

---

## Phase 2 — rerank in retrieval (guru, ~3h, needs Phase 1 + the gate)

This is the change that actually fixes coverage, and it is small once the
reranker exists.

In `propose_edges.py`:

1. Retrieve **top-50 by rank per chunk**, cross-tradition, with **no absolute
   similarity floor**. The floor is what locks out native_american (1.1
   proposals/chunk vs hermeticism's 28.8) and it filters on a dimension that
   does not predict quality within the band (AUC 0.509).
2. Score all 50 with the reranker, both directions, mean them — symmetry 1.0 by
   construction rather than Mistral's 0.790.
3. Pass the top-N survivors to the LLM for a verdict + justification.

The reranker replaces the floor as the filter. Retiring the floor without
putting something in its place is precisely what sank `hybrid` and `worklevel`
(0.32 and 0.30 against ~0.70).

**4. Populate `edges.weight` with the reranker score** on promotion. The column
exists, is already exported, and has always been NULL. No DDL change, no
`SCHEMA_VERSION` bump, no guru-web deploy required — it just starts carrying a
ranking signal.

**Before the first wide sweep:** clear or triage the 2,058 pending rows. Adding
a large candidate batch on top of an unreviewed backlog makes both harder to
reason about.

### Export impact of Phase 2: indirect, and volume is the thing to watch

Nothing here writes to `edges` directly — the review gate still does. But
top-50 retrieval means more proposals, more accepted proposals, and therefore a
larger live `edges` table, which is exported in full on every refresh.

Before the first wide sweep, decide the volume ceiling deliberately: 11,147
cross-tradition edges today, and a 10x proposal increase at current accept
rates is a materially larger artifact and a denser graph in the web app.
`--top-n` on the LLM stage is the throttle — the reranker widens what is
*considered*, not necessarily what is *proposed*.

---

## Phase 2W — rank the reader query (guru-web, ~3h, ships WITH Phase 2)

Without this, Phase 2 is a regression for hub chunks. Ship them together.

**2W.1 Order by `weight`.** Add `e.weight` to the SELECT and slot it into the
ORDER BY after tier and before `p.id`:

```sql
 ORDER BY e.edge_type = 'CONTRASTS',
          CASE e.tier WHEN 'verified' THEN 0 WHEN 'proposed' THEN 1 ELSE 2 END,
          e.weight DESC NULLS LAST,
          p.id
```

`NULLS LAST` matters: `weight` is NULL for all 11,147 existing edges and will
stay NULL for any edge promoted before the reranker exists. Without it, the
transition period sorts scored edges *below* unscored ones on Postgres's
default `NULLS FIRST` for DESC.

**2W.2 Add a SQL `LIMIT`.** The query fetches every edge — up to 177 rows with
bodies — to render 10. Once ordering is meaningful, cap the fetch (~50) and
keep the "N more" disclosure over that.

**2W.3 Decide what the count means.** The header renders
`{parallels.length} parallels`. If Phase 2 triples edge volume, that number
triples and stops being a quality signal. Either count only above a weight
threshold, or state it as "showing 10 of N."

### Interim option, before the reranker exists

`weight` could be populated now with cosine similarity via
`tools/edge_similarity_backfill.py`, giving 2W.1 something to sort by
immediately and fixing the alphabetical ordering for the 467 already-truncated
chunks.

Caveat, stated honestly: similarity has **AUC 0.509 for predicting accept
within the retrieved band**, so this is not a validated relevance ranking. The
argument for it is only that alphabetical ordering is definitionally
meaningless and similarity is at worst arbitrary. Treat it as a stopgap, not a
result, and do not report it as an improvement without measuring it.

---

## Phase 3 — consolidate (guru, ~4h, needs Phase 2 in production)

Only worth doing once the reranker is live and producing calibrated scores.

> **Phase 3.1 is the only step in this plan that changes the export source
> directly.** `auto_promote_edges.py` writes into live `edges`, which is what
> `load_edges()` reads. Everything before this point is either sqlite-only or
> mediated by human review. Treat it accordingly.

**3.1 Replace the promotion gate.** `auto_promote_edges.py:46` filters
`confidence >= 0.85` on a field where 93.4% of values are exactly 0.85 — it
reads as a quality threshold and functions as a pass-through. Swap in the
reranker's calibrated probability and pick the threshold from a precision
target. Latent rather than damaging today only because the live graph is
review-backed (45 of 11,147 at `tier='proposed'`); it is a footgun for any
future bulk promotion.

> Do not wire auto-promotion to the reranker without a human-graded set. The
> labels are `agent-claude`'s — `reviewed_by` is `ivy-desktop` for exactly one
> row out of 19,615 — so the model inherits Claude's judgment and no eval here
> can detect a bias they share.

**3.2 Route disagreement to review.** Score both orders; where the reranker and
the LLM judge disagree, queue for human review instead of silently taking one.
Converts an invisible error rate into an explicit queue.

**3.3 Recall probe.** Exhaustively judge all cross-tradition pairs for ~30
chunks spanning central and peripheral traditions. It is the only way to get a
denominator — recall is currently not merely unmeasured but unmeasurable, and
`--top-n 5` is a hard ceiling that bound before the judge did on at least 134
chunks.

---

## Sequencing summary

| phase | repo | effort | blocks on | status |
|---|---|---|---|---|
| 0.1–0.3 | guru | ~4h | nothing | **shipped** — guru #58, #59 |
| 0.4 | guru | ~20m | nothing | reduced to a validation guard; nothing dangling today |
| 1 | rellm | ~2d | nothing | **next** — settles the embedding-ceiling question either way |
| 2 | guru | ~3h | 1 + gate | this is the coverage fix; watch export volume |
| 2W | guru-web | ~3h | ships **with** 2 | without it Phase 2 regresses hub chunks |
| 3 | guru | ~4h | 2 in prod | makes promotion trustworthy |

Phase 0 was the urgent half and is done: every sweep that ran before it
permanently discarded the negatives Phase 1 wanted, and that bleeding has
stopped. Phase 1 no longer blocks on anything.

---

## Explicitly not planned

- **Replacing Mistral as the judge.** It flips 21% under order reversal and
  cannot clean its own backlog, but it produces the `justification` that
  `auto_promote_edges.py:168` writes into live `edges`. Revisit once the
  reranker has removed most of its volume.
- **Re-reviewing the existing 11,102 accepted edges.** They are review-backed
  and there is no evidence they are wrong. Order-flip does *not* predict label
  disagreement (lift 0.98), so there is no cheap filter to prioritise a
  re-review — out-of-fold reranker disagreement is the tool once Phase 1 exists.
- **A human-graded gauge set.** Deferred by choice, but it is the hard ceiling
  on everything above and blocks Phase 3.1 specifically.
- **Reranking `EXPRESSES` (chunk→concept) edges.** The same "no quality signal
  in the ORDER BY" pattern appears at `reader.ts:326` and `:411`, which sort by
  tier then id. Same fix, different pipeline, out of scope here — but worth a
  ticket, because the tagger already produces a score that is being discarded
  the same way.

---

## Addendum, 2026-08-12 — what Phase 1 step 1 found, and where that leaves the plan

Phase 1's first deliverable (the frozen band eval set) was built —
`runs/edges/band-eval/2026-08-12T00-28-04Z/`, 399 rank 6–50 pairs graded,
work-level partition, 79 tradition pairs — and its calibration arm invalidated
the gate it was built for. Full write-ups: that run's `FINDINGS.md`,
`runs/edges/label-repro/2026-08-12T01-36-17Z/FINDINGS.md`, and
`runs/edges/retrieval-novelty/FINDINGS.md`.

### Finding 1 — the labels are not a stable quantity

Fresh Claude grading, under the project's own review rubric
(`guru/prompts/ingest/edge-review.md`), recovers the archived `agent-claude`
verdicts at chance on boundary pairs: **kappa +0.040** (n=60). Both candidate
confounds were tested and refuted:

- *Restricted range* is real (full-range kappa +0.266) but mislocates nothing:
  random pairs reproduce at 95%, stored negatives at 83%, **stored positives
  at 33%**. Fresh review rejects two thirds of the edges the archive accepted.
- *Anchoring* (showing the proposer's verdict + justification, the reviewer's
  actual view) moved kappa only to +0.129 and made the bias *more* negative.

No cheap filter separates reproducible positives from the rest (similarity
0.790 vs 0.770; stored confidence is the inert 0.85 on every rejected row).

Consequences: §2's ship gate cannot distinguish 0.65 from 0.50 against ground
truth this soft, the kill branch would fire on label noise while presenting as
a verdict on the embedding space, and the same labels back the 11,102 verified
live edges. "Are these chunks parallel?" appears to be underdetermined absent
a task — the positives are where the subjectivity lives.

Two side results, both actionable:

- **Random-pair base rate is 0.050, not ~0** (n=40), and both hits are
  substantive parallels (one is Boehme↔Plotinus, on the review rubric's own
  proven-real list). §4's unjudged easy-negative mining would train the model
  to suppress its own objective. Mine with a judging pass or not at all.
- ~12% of band pairs are editorial apparatus (prefaces, catalogues, front
  matter), grading 0.24 positive vs 0.56 for the rest.
  `staged_cleanups.status='apparatus'` exists and has never been populated.

### Finding 2 — the deployment target was measured, and edges-as-a-leg is inert

The owner's framing: the human-in-the-loop step is retrieval in guru-web —
chunk-pair parallelism is not independently judgeable, relevance to a query
is. That reframe was tested, which first required bringing the sqlite pilot
retriever to guru-web parity (**guru PR #60**: three-tier concept resolution,
lexical FTS5 leg, summary leg, production scoring; chunk↔chunk traversal moved
behind `EDGE_LEG=on` — guru-web never had it).

Against the parity baseline, over guru-web's golden queries
(`runs/edges/retrieval-novelty/FINDINGS.md`):

- **Reach is real**: median edge partner sits at vector rank 2,056 of 5,559;
  only 5.8% within vector top-200. The graph reaches material no similarity
  widening finds. Twice confirmed.
- **The motivating examples are gone**: both documented `knownGaps` failures
  are fixed by the baseline's lexical leg; edge partners contain the expected
  tradition in neither.
- **Under production scoring the leg is inert**: edge chunks enter the final
  top-15 in 4 of 240 slots. A scoreless candidate cannot compete in an
  additive scorer.
- **The oversupply stands**: 721 undifferentiated candidates per query for 15
  slots.

The chain is reach → selection → relevance. Reach exists, selection does not,
relevance is unmeasured — and there is no longer a demonstrated retrieval
failure that edges would cure.

### Where this leaves Phases 1–3

- **Phase 1 as specced (chunk-pair cross-encoder against review labels) is
  held.** Its training target is unstable (Finding 1) and its deployment
  rationale unproven (Finding 2). Do not resume without a decision on what
  the model predicts.
- **The surviving model concept is a (query, chunk) relevance scorer** — the
  selection layer for whatever leg or panel consumes edges — evaluated on
  query relevance, where stability is testable (and must be tested first, the
  same way the pair labels were).
- **Phase 2's retrieval rewire is moot until selection exists.** Phase 2W (the
  reader panel ordering fix) is untouched by all of this and remains the one
  consumer edges demonstrably have today.
- **Cheapest next probe** if edges-in-retrieval stays live: judge sampled
  partners for 2–3 golden queries for relevance *to the query*. Closes the
  question or funds it.

### Addendum update, later 2026-08-12 — the anchored-inheritance experiment

The (query, chunk) direction was built and measured the same day (guru branch
`edge-score-inheritance` stacked on #60; rellm `tools/edge_inherit_ab.py`,
`tools/edge_relevance_judge.py`; findings in
`runs/edges/relevance-judge/2026-08-12T12-49-14Z/FINDINGS.md`).

- **The (query, chunk) judgment frame is valid: inter-grader kappa +0.800**
  (vs +0.04 for pair labels), with clean ceiling/floor separation (baseline
  66.7% strict-relevant, random 0.0%). Label generation for a relevance
  scorer is methodologically safe.
- **Anchored score inheritance works mechanically** — dose-responsive,
  surfaces nothing on anchor-less queries — and lifts edge material to 15.9%
  strict relevance vs a 0% floor. But it displaces ~67%-relevant baseline
  chunks, ~4:1 against. **EDGE_INHERIT stays off.**
- **The trained scorer's bar is now a measured number**: raise surfaced-slot
  strict relevance from 15.9% toward 66.7%. The deployment slot is the
  `pair_sim` multiplier in `retrieval_legs.inherited_partners` — no
  architectural change when the model lands.
- Transfer strength varies by anchor specificity (family-level "cosmology"
  4/8 strict; concept-level "wu wei" 0/11): a parallel shares the *move*, not
  the *topic*, so specific-topic queries transfer worst. A scorer sees the
  query text and can learn this; a static edge weight cannot.
- Rarity-bump ablation: removing it moves 26/240 slots. It stays until its
  replacement beats it on this harness.
