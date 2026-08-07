# Homology gold set

Human-adjudicated validation set for the rellm-homology module
(see `docs/homology/proposal.md`). Files:

- `candidates.jsonl` — agent-proposed candidates with evidence. NOT ground truth.
- `adjudication.md` — human-readable sheet for the accept/reject/reclassify pass.
- `ratified.jsonl` — human-ratified records only. This is the gold set; nothing
  reads `candidates.jsonl` downstream.

## Candidate record schema (candidates.jsonl)

```json
{
  "id": "A-01",
  "kind_proposed": "homology | false_friend",
  "difficulty": "easy | borderline",
  "a": {"concept": "<taxonomy concept id>", "tradition": "<tradition id>", "term": "<surface term>"},
  "b": {"concept": "...", "tradition": "...", "term": "..."},
  "claim": "one sentence: the correspondence, or the surface trap",
  "rationale": "2-4 sentences comparing the actual conceptual moves",
  "primary_evidence": [{"source": "<guru corpus file path>", "quote": "<verbatim excerpt>"}],
  "secondary_citations": ["Author, Work, locus — claim"],
  "cell_n": {"a": 42, "b": 17}
}
```

Constraints enforced at proposal time: both (concept, tradition) cells have
n≥10 teacher-tagged chunks (else unmeasurable in phase 2/3); primary evidence
is quoted verbatim from the guru corpus; citations are checkable scholarship,
flagged "(citation uncertain)" where the proposer wasn't sure.

## Ratified record schema (ratified.jsonl)

Candidate record plus:

```json
{
  "verdict": 0,
  "verdict_note": "optional: why, especially where the rating surprises the proposer's lean",
  "adjudicated_by": "ivy",
  "adjudicated_at": "YYYY-MM-DD"
}
```

`verdict` is a **graded depth-of-correspondence rating**, not a binary class —
adopted 2026-08-03 after the first adjudication session showed the binary
smudges the level-dependence of correspondence (nearly every pair is alike at
one level of description and divergent at another; forcing homology/false_friend
loses exactly that structure). Anchors:

| rating | anchor |
|---|---|
| 0 | unrelated — even the surface link is spurious |
| 1 | surface only — shared word/image; the moves diverge (textbook false friend) |
| 2 | family resemblance — same genus ("they're all meditation"), different function/frame |
| 3 | strong correspondence — same conceptual move; frame differences secondary |
| 4 | same move — functionally identical or lineage-connected |
| "rejected" | not a usable test case (bad evidence, incoherent pairing) — excluded from eval |

The human signal the eval needs is a stable *ordering*, not a metaphysical
fact of sameness — subjectivity in absolute placement washes out of rank
statistics as long as the ordering is consistent.

**Eval use:** (1) Spearman rank correlation between cosine and rating over all
non-rejected pairs; (2) tail separation between 0–1 and 3–4 (the derived
binary, for the go/no-go); (3) the 2s are a held prediction — a good
instrument scores them between the tails, and systematic failure there is
informative. Legacy note: binary verdicts from the first session were migrated
homology→4, false_friend→1 (only A-01..A-03 were affected, all easy lineage
homologies).

Working file: `verdicts.json` (written live by `tools/adjudicate_gold.py`,
shape `{id: {verdict, note, synced}}`; `synced: true` marks a rating
auto-copied from a duplicate-pair twin). `ratified.jsonl` is assembled from it
when adjudication is called done.

## Provenance

Proposer must be independent of the base model the geometry is extracted from
(proposal §Step 1). Phase-1 run 2026-08-03: Claude agents proposing, Qwen the
candidate scored base. Cell counts from guru.db as of 2026-08-03.
