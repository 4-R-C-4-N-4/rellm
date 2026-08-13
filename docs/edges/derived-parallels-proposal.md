# Proposal: retire Pass C — parallels as a derived table

**Date:** 2026-08-13 · **Status:** proposal, owner decision
**Prototype:** `tools/derived_parallels.py` → `runs/edges/derived/2026-08-13-run1/`
**Context:** the owner's assessment that the PARALLELS leg is expensive GPU
work for net-null benefit. The measurement record agrees.

## The case against Pass C, in its own numbers

- 20,412 large-LLM pair classifications paid for to date, plus agent/human
  review of 21,712 staged rows, netting 11,300 live edges — of which the
  curation probe just flagged 25% suspect.
- The pair-level judgment Pass C asks the LLM to make is the one judgment
  this project has *proven* unstable (review-label kappa +0.04), and its
  per-pair similarity signal is noise (AUC 0.509).
- Production consumers: the reader panel. Retrieval terms remain off.
- Meanwhile the two components that measured well — human-gated EXPRESSES
  tags and the thin (query, chunk) scorer — can generate the same product.

## The replacement

`parallels` becomes a **derived, versioned table**, not reviewed content:

1. Source of truth: EXPRESSES (already behind the owner's tag apply gate).
2. Score every (concept, chunk) pair with the thin student —
   **38,433 scores, ~8 minutes on the 3090**, cached incrementally
   (a corpus update re-scores only new/changed chunks).
3. A chunk's partners: cross-tradition co-expressors of its concepts,
   partner-score-ranked per concept, thresholded at the calibrated grade,
   apparatus-flagged chunks excluded, capped per panel.
4. Reader panel and atlas consume the derived table and gain the via label
   ("parallel about *the demiurge*") and a grade for free.
5. `staged_edges` review flow retires. CONTRASTS (112 live rows) becomes a
   small curated list or is dropped.
6. EDGE_INHERIT/EDGE_RERANK, if ever enabled, consume the same table.

## Prototype evidence (run 2026-08-13)

- 18,632 partner rows over 2,363 chunks from the 38k scores.
- **21 of 24 independently judged strict-relevant edge partners are
  reachable** in the derived table — the proven-good material survives.
- Only 3.2% of live edges are reproduced *as identical pairs* — expected and
  not a defect: Pass C sampled pairs by vector adjacency; the derived table
  selects the best-graded co-expressors from the full 5.1M-pair candidate
  space. The comparison that matters is panel quality, which is the owner's
  ratification call; sample side-by-side panels are in the session record
  and reproducible from the run dir.
- Known prototype flaws to fix before adoption (both localized to ranking):
  rank partners by the partner's own concept score (min-leg clamps every
  partner to the anchor's score today), and round-robin panels across via
  concepts (single-via monocultures otherwise).

## What is lost, honestly

- **Taxonomy-blind parallels** — pairs whose shared move has no concept
  (the Plotinus-dialectic kind). Recoverable only through taxonomy growth
  or a hand-curated list. Pass C could in principle find these; in practice
  they are concentrated in the empty-via set review couldn't defend.
- **LLM pair nuance** (PARALLELS vs CONTRASTS vs surface-only). The grade
  threshold replaces "surface-only"; CONTRASTS dies as a pipeline.
- Panel churn: derived panels differ from today's edges; readers see a
  different (better-labeled) set after cutover.

## Cost comparison

| | Pass C (status quo) | derived table |
|---|---|---|
| per corpus version | ~20k+ LLM pair calls on a large local model (GPU hours) | ~8 GPU-min (student), incremental |
| review burden | 21k staged rows to date; queue continues growing | none (tags already gated) |
| output | unlabeled pairs, 25% suspect | via-labeled, graded, thresholded panels |
| judgment stability | kappa +0.04 (pair frame) | built on kappa +0.85–0.88 frames |

## Migration sketch (guru-side, future PR)

1. Fix the two prototype ranking flaws; re-emit; owner eyeballs ~10 panels.
2. Port the generator into guru as a pipeline stage (replacing Pass C in the
   ingest workbook), writing `derived_parallels` beside — not over — `edges`.
3. Reader panel reads the new table behind a flag; owner compares live.
4. On acceptance: Pass C node retired in the workbook, staged_edges frozen
   as historical record, suspect-queue cleanup of the legacy edges proceeds
   independently.

The stopping point of this proposal is deliberate: changing the ingest
pipeline is the owner's call; everything above is evidence and a reversible
prototype.
