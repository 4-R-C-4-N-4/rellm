# 80-Concept Teacher Run — Retro

**Command:** `python3 scripts/tag_concepts.py --respect-reviewed --supersede-pending --batch-size 100`
**Model:** `llamacpp/Qwen3.5-27B-UD-Q4_K_XL.gguf` (the teacher)
**Taxonomy:** `concepts/taxonomy.toml` v1 — 88 concepts across 6 categories (cosmology, soteriology, theology, praxis, anthropology, ethics). Called the "80-concept" set; live count is 88.
**Window:** 2026-05-15 16:08 → 2026-05-21 10:40 (5d 18h 33m wall clock)
**Raw log:** `80-concept-teacher-run.txt`

## Headline

- 3089 chunks tagged, **0 errors**, 31 batches of 100 with steady ~4.5h/batch cadence.
- ~161s/chunk on average — no degradation across the 138-hour run.
- 11,473 tags proposed by the model.
- DB outcome: 6665 inserted + 3806 superseded + 1002 skipped_reviewed = 11473 (matches log proposals exactly; 0 conflicts).
- Mean **3.71 tags/chunk**, max 21, **41.9% of chunks (1294) got 0 tags**.

## Per-tradition rates

| tradition | chunks | mean tags | zero-tag % |
|---|---:|---:|---:|
| mesopotamian | 15 | 5.73 | 13% |
| buddhism | 20 | 5.15 | 20% |
| gnosticism | 127 | 5.01 | 22% |
| zoroastrianism | 154 | 4.70 | 31% |
| egyptian | 456 | 4.26 | 38% |
| jewish_mysticism | 184 | 4.12 | 38% |
| taoism | 376 | 3.86 | 37% |
| sufism | 37 | 3.84 | 49% |
| greek_mystery | 261 | 3.72 | 42% |
| **neoplatonism** | **841** | 3.66 | 42% |
| platonism | 36 | 3.31 | 47% |
| hermeticism | 63 | 2.65 | 59% |
| western_esoteric | 225 | 2.59 | 53% |
| christian_mysticism | 182 | 2.52 | 59% |
| renaissance_hermeticism | 112 | 2.25 | 62% |

Antiquity traditions tag densely; later/discursive ones tag thinly. Two clusters separated by roughly the dividing line: pre-Hellenistic ritual/scripture vs. Renaissance/early-modern prose treatise.

## The zero-tag question

The 1294 zero-tag chunks split into two very different populations.

### Population 1 — apparatus (working as designed)

Concentrated in a few text_ids and dominated by the `-index` suffix:

| text_id | zero-tag chunks |
|---|---:|
| neoplatonism.plotinus-select-works-index | 373 |
| egyptian.egyptian-book-of-the-dead-index | 156 |
| taoism.zhuangzi-inner-chapters-index | 135 |
| jewish_mysticism.enoch-charles-1917 | 58 |
| egyptian.egyptian-heaven-and-hell | 36 |

Spot-checked first chunks of `tertium-organum`, `pythagorean-golden-verses`, `orphic-hymns`, `heroic-enthusiasts-pt1`: title pages, errata, scan attribution. Zero is correct here — matches [[feedback_tag_reject_preface_chunks]] (the apparatus case, not the false-positive case the memory warns against).

### Population 2 — real misses (the interesting finding)

Two non-`-index` texts have zero-tag rates >50% and zero-tag chunks scattered throughout, not just at the front:

- **`western_esoteric.tertium-organum`**: 124 / 225 chunks (55%) zero. Verified zero-tag chunks contain unambiguously conceptual material:
  - `.030` (Ch IV pt 2): Ouspensky on the non-existence of past/future/present as conventionally conceived — direct metaphysics of time.
  - `.100` (Ch XIII pt 7): phenomena vs noumena, infinite meanings, "thing-in-itself," knowledge as relative, citation of "Light on the Path."
  - `.200` (Ch XXIII pt 2): the two-classes-of-humanity / "wheat and tares" / esoteric pedagogy reading — *pneumatic_elect* is literally a taxonomy concept and this is a near-perfect prose paraphrase of it. Got nothing.
- **`christian_mysticism.life-and-doctrines-boehme`**: 99 / 159 chunks (62%) zero. Verified zero-tag chunks include:
  - `.060` (Ch 7 pt 2): Adam in paradise, inner/outer body, terrestrial substance "absorbed in the celestial essence," explicit parallel to the Bhagavad Gita's Atma. Should plausibly fire on *correspondence*, *microcosm_macrocosm*, *theosis_deification*.
  - `.100` (Ch 10 pt 7): Christ as second Adam, Jacob/Esau as nature/grace allegory, regeneration. Christian-mysticism soteriology, got nothing.

This pattern repeats more mildly across `heroic-enthusiasts-pt1/pt2`, `pythagorean-golden-verses` body chunks, and parts of `eckhart-sermons-field`. The model has a coverage gap for **discursive 16th–20th-century prose that paraphrases concepts in non-technical language**, even when the same concepts get tagged readily in primary scripture.

Two competing hypotheses worth disambiguating before the review pass:

1. **Vocabulary mismatch.** The taxonomy definitions lean on technical Greek/Hebrew/Sanskrit terms (sephirot, pleroma, tzimtzum, anamnesis). When Ouspensky talks about "dimensional ascent" in 1922 English without naming an antique school, the model doesn't fire the analogy. Fix: definitions could include modern paraphrases.
2. **Genuine taxonomy gap.** Western_esoteric/renaissance_hermeticism may lean on concepts the v1 taxonomy doesn't cover well (Bruno's heroic furore is in there as *divine_madness*, but four-dimensionalism, theosophical metaphysics, alchemical correspondence-as-method may not be). Fix: a v2 pass with these traditions as the audit case.

Recommend sampling ~30 zero-tag chunks from `tertium-organum` and `boehme` before the review-tool pass, classifying each as `apparatus` / `coverage_gap` / `vocabulary_miss` / `genuinely_concept_thin`. That ratio decides whether to spend cycles on taxonomy v2 or proceed straight to curation.

### Diagnostic addendum (2026-05-21)

The production `tag_concepts.py` does not persist the LLM's raw response — only the parsed-and-filtered tags (score ≥ 1) and a one-line `: N tags` log entry. A zero in the log is consistent with four very different failure modes: model returned `[]`, model returned objects all scored 0, model returned malformed JSON, or the request hit an empty-content / reasoning-only path.

`scripts/retag_sample_debug.py` (added in this branch) reissues the same prompt with the same model against a 20-chunk sample drawn from `tertium-organum` and `life-and-doctrines-boehme`, writing the full raw response, parsed JSON, parsed tags, prompt, and latency to `data/retag-debug/<chunk_id>.json`. It does not touch `staged_tags`. Results inform the four-way classification above. See follow-up doc once that sample completes.

## Throughput

- 161s/chunk is dominated by the 27B model at Q4_K_XL on llamacpp. Per-batch wall time was flat from batch 1 (~4h32m) to batch 30 (~4h26m) — no thermal throttling, no memory creep visible in cadence.
- 138-hour clean run with zero retries or crashes is the bigger win than any of the tag-rate numbers. The pipeline (chunk loader → llamacpp → DB writer with supersede policy) held up over a multi-day window with no babysitting.
- For a future run at this scale: add periodic batch summaries to log (already at 100-chunk granularity) and consider a rolling-mean tags/chunk in those summaries — would have surfaced the western_esoteric/christian_mysticism dropoff days earlier.

## Pipeline integrity check

11,473 proposed = 6665 inserted + 3806 superseded + 1002 skipped_reviewed. The supersede-pending policy did exactly what it should: 3806 prior pending tags were replaced, 1002 already-reviewed chunks kept their human-curated tags, and there were 0 row-level conflicts. Nothing to worry about here.

## What to do next

1. **Sample-classify zero-tag chunks** in Tertium-Organum and Boehme (~30 each) to choose between taxonomy-v2 and proceed-to-review.
2. **Review-tool curation pass** on the 6665 newly inserted rows. [[guru-review-tags]] handles the queue; this is the score-1 / score-2 backlog the skill is designed for.
3. **Consider a tag-rate-floor sanity check** before running again: if a text_id finishes with mean < 1.0 tags/chunk and isn't an `-index`, flag for human eyes before committing. Cheap insurance against a future run wasting 5 days on a text the taxonomy doesn't cover.

## Honorable mentions

- The 27B teacher held a stable inference rate for nearly six days straight on local hardware. That's the real headline.
- The `supersede_pending` semantics worked correctly under a real workload — 3806 supersedes, 0 conflicts. The schema-review hitlist work from the concept-hierarchy branch paid off here.
