# Thin scorer spec (rung 3): frozen targets

**Date:** 2026-08-12 · **Ticket:** todo:085e47c3 (parent e2f907cf)
**Role:** the numbers every later child of this plan is measured against.
Change them only by editing this doc in its own commit, with a reason.

## What is being built

A (query, chunk) relevance cross-encoder small and fast enough for the lean
box, distilled from bge-reranker-v2-m3 zero-shot — the scorer that passed the
EDGE_RERANK quality gate (72.7% strict vs 62.5% baseline, kappa +1.000) but
failed synchronous latency by two orders of magnitude (0.48 s/pair CPU).

Two consumers, in priority order:
1. **Offline edge curation** — grading the live PARALLELS graph (child 9).
2. **The EDGE_RERANK slot** — drop-in via `EDGE_RERANK_MODEL`, still
   default-off; synchronous enable is an owner decision at ship gate.

## Frozen targets

| dimension | target | rationale |
|---|---|---|
| params | **≤ 25M** | ~23× thinner than bge (568M); MiniLM-class |
| latency | **≥ 100 pairs/s on 1 CPU thread** (fp32) | 120-pair query ≤ 1.2s; int8 reported alongside |
| model load | ≤ 2s cold | lean box, no resident daemon assumed |
| quality: AUC | **≥ 0.74 strict** on the 2026-08-12T18-14-23Z surfaced stratum | match zero-shot bge (0.742) |
| quality: gate | **kept-slot strict ≥ baseline strict** on gold-eval (frozen works) | the standing ship bar |
| teacher agreement | **Pearson r ≥ 0.85** vs bge logits on held-out pairs | distillation sanity |
| sanity | baseline-vs-random AUC ≥ 0.85 | disqualifier if failed, as ever |

## Architecture candidates (cheapest first, stop at first pass)

1. **3a: cross-encoder/ms-marco-MiniLM-L6-v2 warm start** (~22.7M) —
   already a (query, passage) cross-encoder; fine-tune head+top layers on
   teacher logits.
2. **3b: MiniLM-L4/L2 or distilled-from-scratch** — only if 3a misses the
   latency bar with int8.

Bi-encoders are **disqualified** (four confirmations of the selection
ceiling; cosine's re-run AUC 0.686 collapses on specific-concept queries).

## Data budget

- Queries: ~500–1000. Golden trainable-work queries (frozenEval:false, both
  kinds) + ritual-style synthetic queries per trainable work. Provenance
  manifest mandatory; **no frozenEval:true work's queries in training, ever**
  — those works form gold-eval.
- Pairs: ~30/query stratified — baseline top-15, anchored edge partners,
  hard negatives (vector ranks 16–200, not retrieved), random floor
  (≈ 15/8/5/2). Known-apparatus chunks excluded from positive strata only.
- Teacher: bge fp32 logits, mirrored scoring config (max_length 1024,
  body[:2400]); cached by (sha256(query), chunk_id).
- Gold: ~300 blind double-graded items under the established protocol
  (independent passes, key withheld). gold-cal from trainable-work queries
  (calibration/early-stop only); **gold-eval from frozen-work queries only**
  (the deciding number). Abort bar: inter-grader kappa < +0.6 → regrade,
  don't use.

## Eval protocol

1. Rung-3 row in `edge_scorer_rungs.py` on the 18-14-23Z judged set — direct
   ladder comparability.
2. gold-eval metrics (AUC, kept-slot at the gate threshold).
3. Latency bench: pairs/s at 1 and 8 CPU threads, fp32 and dynamic-int8,
   plus load time.
4. Ship gate: student in the EDGE_RERANK slot (threshold recalibrated on
   student logits, same top-decile procedure), `--wide --rerank` A/B, blind
   double-graded re-judge, lean-settings latency.

## Compute

Teacher batches, training, and the curation probe run on the 3090
(`CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=0`), released when done —
owner authorized 2026-08-12 for this plan. Serving-side measurements are
CPU-only, matching the lean-box constraint.
