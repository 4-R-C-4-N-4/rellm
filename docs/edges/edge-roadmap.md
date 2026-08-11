# Edge pipeline — execution roadmap

**Status:** ready to execute on merge
**Scope:** the whole path from this PR to a fixed edge pipeline, across both
repos.
**Inputs:** `edge-process-audit.md` (findings), `edge-reranker-build-spec.md`
(the model)

This PR is measurement only — it changes nothing in guru. What follows is the
work it unblocks, sequenced by dependency rather than by importance.

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

Measured on the snapshot:

- **929 live edges reference a chunk endpoint with no corpus file** (63 of them
  cross-tradition PARALLELS/CONTRASTS).
- They export as dangling references, the load succeeds, and guru-web fails to
  resolve them at render time.

This is broken today, independent of anything here. But Phase 2 retires the
similarity floor and widens retrieval, which reaches more of the 273 file-less
chunk ids — so it would grow the dangling set. **Fixing it is now Phase 0.4,
ahead of any retrieval change.**

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

## Phase 0 — stop the data loss (guru, ~5h, no model required)

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

### 0.4 Stop exporting dangling edges — `export.py:load_edges`

929 live edges point at a chunk with no corpus file and are exported as
dangling references today, because `load_edges()` filters nothing and the
inline validation never checks edge endpoints.

Filter endpoints against the emitted chunk set, and add an edge-endpoint check
to `emit_validation()` so a regression fails the load loudly instead of
degrading the web app silently.

> Sequence this **before** Phase 2. Retiring the similarity floor reaches more
> of the 273 file-less chunk ids, so fixing the filter afterwards means
> shipping a known-worse export in between.

**Phase 0 exit:** a sweep can run without losing negatives, provenance, or
progress, and the export stops emitting dangling edges.

**Export impact of Phase 0: none.** Every change is confined to `staged_edges`,
a new `edge_progress` table, and the export's own endpoint filter. `edges` is
untouched, so staging sees no behavioural change other than 929 broken
references disappearing.

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

| phase | repo | effort | blocks on | value if later phases never happen |
|---|---|---|---|---|
| 0 | guru | ~5h | nothing | high — stops data loss *and* fixes 929 dangling exported edges |
| 1 | rellm | ~1d | nothing | high — settles the embedding-ceiling question either way |
| 2 | guru | ~3h | 0 + 1 + gate | this is the coverage fix; watch export volume |
| 2W | guru-web | ~3h | ships **with** 2 | without it Phase 2 regresses hub chunks |
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
- **Reranking `EXPRESSES` (chunk→concept) edges.** The same "no quality signal
  in the ORDER BY" pattern appears at `reader.ts:326` and `:411`, which sort by
  tier then id. Same fix, different pipeline, out of scope here — but worth a
  ticket, because the tagger already produces a score that is being discarded
  the same way.
