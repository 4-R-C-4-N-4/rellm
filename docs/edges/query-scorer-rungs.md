# Can an existing scorer find the relevant edge partners?

**Date:** 2026-08-12 · **Status:** complete
**Data:** `runs/edges/relevance-judge/2026-08-12T12-49-14Z/` — 100 doubly-graded
(query, chunk) items, inter-grader kappa +0.800; 69 edge-surfaced partners of
which 11 strict-relevant, 15 baseline chunks (66.7% strict), 16 random (0%).
**Harness:** `tools/edge_scorer_rungs.py` · CPU-only by construction.

## The question

The anchored-inheritance experiment established that edge partners of
confident concept anchors reach the final top-K but judge only **15.9%**
strict-relevant against the **66.7%** material they displace. The missing
piece is a per-partner relevance signal. Before training a model, test the
scorers available today — cheapest first, stop at the first that works.

The bar, from the relevance findings: raise kept-slot strict relevance from
15.9% toward 66.7%.

## Metrics

All on the surfaced stratum (the operational set), strict label = both
independent graders said "relevant":

- **AUC** — does the scorer rank relevant above not-relevant at all?
- **precision@3 per query** — deployment keeps a few partners per query, not a
  global ranking.
- **kept-slot strict rate at a 1-in-6 keep** — directly comparable to the
  15.9% unranked rate and the 66.7% bar.
- **sanity: baseline-vs-random AUC** — a scorer that cannot separate the
  retriever's own results from noise is disqualified, whatever it does above.

Caveat on power: 69 surfaced items, 11 positives. Enough to read direction,
not to ship on. Extending the judgment set is cheap now that the frame is
proven (kappa +0.800).

## Rung 1 — query↔chunk embedding cosine (free)

nomic-embed vectors already computed for every chunk; queries embedded once.

| metric | value |
|---|---|
| AUC, strict | **0.522** (chance) |
| AUC, lenient | 0.486 |
| precision@3 | 0.25 |
| kept-slot strict (n=13) | 0.308 |
| sanity baseline-vs-random | **0.817** |

**Fails, informatively.** The sanity check passes — cosine cleanly separates
the retriever's own results from random noise — so the harness is sound and
the failure is specific: *within the surfaced band, embedding similarity
carries no relevance signal.* This is the third independent appearance of the
same ceiling (edge-band accept AUC 0.509; the rank-5 yield cliff; now query
space). Edge partners are, by construction, material that reaches the result
set through a path vector similarity cannot see — so vector similarity cannot
rank them either. No free scorer exists.

## Rung 2 — bge-reranker-v2-m3, zero-shot, CPU

568M cross-encoder pretrained for (query, passage) scoring — the task as
posed, unlike the (chunk, chunk) contortion of the original spec. ~2 min on
CPU for 100 pairs.

| metric | rung 1 (cosine) | rung 2 (bge zero-shot) |
|---|---|---|
| AUC, strict | 0.522 | **0.760** |
| AUC, lenient | 0.486 | 0.625 |
| sanity baseline-vs-random | 0.817 | **0.917** |
| precision@3 per query | 0.25 | 0.25 |
| global top-11 strict rate | — | **45.5%** (5/11) |

The identical precision@3 is a coincidence of aggregation, checked: the two
rungs pick different top-3 sets on all 8 queries (cosine +1 on Sephiroth, bge
+1 on cosmology, netting equal). The informative numbers are AUC and the
global selection row.

Two structural facts surfaced by the per-query breakdown:

1. **3 of 8 queries have zero relevant partners** — no scorer can fix those,
   and they cap per-query precision@3 at 0.417. The failure there belongs to
   the *graph* (nothing relevant is reachable), not the scorer.
2. **Relevance concentrates in few queries** (cosmology 4, Sephiroth 3), so
   the right deployment rule is a **global score threshold**, not a per-query
   quota. Under global top-11 selection, zero-shot bge lifts kept-slot strict
   relevance from 15.9% to **45.5%**.

## Verdict

The cross-encoder sees what the bi-encoder cannot — fourth confirmation of the
same ceiling, and the first time something has cleared it. Zero-shot, with no
training, the kept slots move from 15.9% to 45.5% strict relevance against the
66.7% bar. That is most of the distance on a scorer that has never seen this
corpus.

Standing decisions this supports:

- **Threshold, not quota**: gate inherited partners on reranker score, letting
  strong queries surface several and weak queries surface none. This also
  handles the zero-relevant-partner queries for free — they simply stay quiet.
- **Fine-tuning has a defensible case for the remaining gap** (45.5% → 66.7%),
  and its labels can be generated at scale under the proven kappa +0.800
  frame. It needs a real query distribution first — 14 golden queries are an
  eval set, not a training set.
- **Power caveat stands**: 11 positives. Before any ship decision, extend the
  judgment set and re-run this harness — one grading pass, ~an afternoon.

Deployment sketch, no architecture change: replace `pair_sim` in
`retrieval_legs.inherited_partners` with the reranker score over
(query, partner-body), thresholded. CPU latency is the open engineering
question for guru-web (batch of ~30 partner scores per query at ~1s/8 pairs
CPU — likely needs the score computed asynchronously or the model quantised;
measure before promising).

## Reproduce

```
python3 tools/edge_scorer_rungs.py --rung 1
<venv-with-transformers>/bin/python tools/edge_scorer_rungs.py --rung 2
python3 tools/edge_scorer_rungs.py --report
```

Scores and metrics land beside the judgment run
(`rung{1,2}_{scores,metrics}.json`). CPU-only by construction
(`CUDA_VISIBLE_DEVICES` emptied before torch import).
