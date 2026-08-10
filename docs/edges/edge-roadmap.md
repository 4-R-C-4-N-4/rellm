# Edge pipeline — execution roadmap

**Status:** ready to execute on merge
**Scope:** the whole path from this PR to a fixed edge pipeline, across both
repos.
**Inputs:** `edge-process-audit.md` (findings), `edge-reranker-build-spec.md`
(the model)

This PR is measurement only — it changes nothing in guru. What follows is the
work it unblocks, sequenced by dependency rather than by importance.

---

## The shape of it

```
  PHASE 0 ──────────────► PHASE 2 ──────► PHASE 3
  guru: stop data loss    guru: rerank    guru: consolidate
        (no model)              ▲
                                │
  PHASE 1 ──────────────────────┘
  rellm: build the reranker      ▲
                                 │
                            DECISION GATE
```

Phase 0 and Phase 1 are **independent and should run concurrently** — Phase 0
is guru-side schema and write-path work, Phase 1 is rellm-side model work, and
neither blocks the other. Phase 2 needs both.

---

## Phase 0 — stop the data loss (guru, ~4h, no model required)

**Do this first, and do it before the next sweep runs.** Every one of these is
losing information right now, and the loss is not recoverable after the fact.

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
> is the one place in Phase 0 that can silently duplicate rows.

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
  existing rows with `tools/edge_similarity_backfill.py`.
- `presentation_order` — `pair_key()` canonicalises at `propose_edges.py:164`
  *before* insert, destroying the order the model saw. Record which passage was
  A, or AB/BA stays permanently unauditable in the store.
- `edge_progress` — mirrors `tagging_progress`. **836 chunks (15%) have never
  been evaluated** and nothing records what has been swept, so coverage is a
  function of which ad-hoc `--tradition`/`--text` runs someone remembered.

### 0.3 `serve-llama.sh` context bug

`CTX_SIZE="32768"` is hardcoded, not `${CTX_SIZE:-32768}`. Raising `--parallel`
via a wrapper silently shrinks each slot's context — at `PARALLEL=8` that is
4096/slot, which truncates a thinking model mid-JSON. One word, and it will
bite the Phase 1 probe runs otherwise.

**Phase 0 exit:** a sweep can run without losing negatives, provenance, or
progress. Nothing about retrieval has changed yet.

---

## Phase 1 — build the reranker (rellm, ~1 day, concurrent with Phase 0)

Full detail in `edge-reranker-build-spec.md`. Sequence:

1. Export 19,338 labelled pairs via `rellm.edges.iter_reviewed_edges`, grouped
   splits via `group_key` (1,877 groups).
2. Mine easy negatives from random cross-tradition pairs — base rate ~0, so no
   judging needed. Target ~1:1 against the existing hard negatives.
3. Train ModernBERT-large as a binary cross-encoder. Collapse CONTRASTS into
   positive; 102 examples is not learnable.
4. Offline eval: AUC, calibration, and **precision within rank 6–50
   specifically** — overall AUC can look healthy while the band that matters
   does not move.
5. Live probe via `tools/edge_candidate_probe.py --strategy reranker`.

### DECISION GATE

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

## Phase 2 — rerank in retrieval (guru, ~3h, needs Phase 0 + Phase 1)

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

**Before the first wide sweep:** clear or triage the 2,058 pending rows. Adding
a large candidate batch on top of an unreviewed backlog makes both harder to
reason about.

---

## Phase 3 — consolidate (guru, ~4h, needs Phase 2 in production)

Only worth doing once the reranker is live and producing calibrated scores.

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

| phase | repo | effort | blocks on | value if later phases never happen |
|---|---|---|---|---|
| 0 | guru | ~4h | nothing | high — stops ongoing, unrecoverable data loss |
| 1 | rellm | ~1d | nothing | high — settles the embedding-ceiling question either way |
| 2 | guru | ~3h | 0 + 1 + gate | this is the coverage fix |
| 3 | guru | ~4h | 2 in prod | makes promotion trustworthy |

**Start Phase 0 and Phase 1 on the same day.** Phase 0 is the higher-urgency
half despite being the less interesting one: it needs no model, it is a few
hours, and every sweep that runs before it permanently discards negatives the
Phase 1 retrain wants.

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
