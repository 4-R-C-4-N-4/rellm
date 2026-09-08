# qwen-3-4b-guru-v5 — training plan

**Goal.** Ship the finetune the v4 findings deferred: a cheap 4B that can
**backfill the 12 cross-tradition drift concepts** onto older traditions, which
v4 could not (0/44 cross-tradition training rows → it learned each new concept in
its Blavatsky/Hermetic/Gnostic flavour only). The guru-side fix is landed and
verified; v5 is the retrain that consumes it.

Same recipe as v4 (`configs/qwen-3-4b-guru-v4.yml`). The only deltas are **data**
(the applied backfill positives) and **one export bug fix** (dedup) forced by a
new data condition v4 never faced.

## Upstream state — verified, not assumed (2026-09-06)

Guru PR #127 ran a 27B sample pass over older-tradition chunks and applied the
reviewed net-new tags. Checked directly against the live `guru/data/guru.db`
(source that `rellm snapshot` mirrors — the `export/guru-corpus.sql.gz` is guru's
downstream sync artifact, not what rellm ingests):

- **Taxonomy unchanged:** 154 leaf concepts, `prompt_version=v1`, 0 added/renamed.
  v5 is a *data* refresh, not a taxonomy bump. (168 `concept` **nodes** in the DB
  ≠ 154 taxonomy leaves; the export keys off the taxonomy, which is stable.)
- **Node-4 gate holds live.** All 12 backfill concepts now carry non-zero
  older-tradition `EXPRESSES` rows (older = not theosophy/western_esoteric/
  gnosticism), matching the findings table exactly:

  | concept | older | concept | older | concept | older |
  |---|--:|---|--:|---|--:|
  | divine_immanence | 109 | trinity | 24 | talisman_magic | 12 |
  | divination | 38 | incarnation | 19 | qliphoth | 8 |
  | stellar_determinism | 31 | esoteric_lineage | 13 | initiation | 7 |
  | gender | 29 | | | exorcism | 5 |
  | | | | | spirit_conjuration | 3 |

  The v4 bellwether **incarnation** (27B=3 / base=0 / v4=0 on the Gita avatāra
  chunk) now has 19 older-tradition rows incl. hinduism — real training signal
  where v4 had none.
- **Snapshot pulled:** `data/snapshots/2026-09-06T12-15-36Z-v5/` (36,626 accepted
  / 13,743 pending staged_tags; 47,267 EXPRESSES).

## Recipe change — applied tags only, deduped (DONE)

Two decisions, both landed:

**1. Export status = `accepted` only (not v4's `pending,accepted`).** Train on the
*applied* tags — the owner-gated truth — not any label a model threw at a chunk.
This is viable now in a way it wasn't at v4 time: the corpus has since been heavily
reviewed, so accepted is the bulk (36,626 vs 13,743 pending). All 12 backfill
concepts keep their full older-tradition rows under accepted-only (they were
applied) — nothing is lost.

**2. Dedup to one tag per `(chunk, concept)`.** v4's export was clean only by luck:
its two teacher labels (3.5 / 3.8) tagged *disjoint* chunks, so no chunk had two
rows for one concept. The backfill breaks that — the 27B sample pass re-scored
*whole* older chunks against the full taxonomy, re-emitting concepts they already
carried. `serialize_teacher_tags` had **no dedup**, so those become **duplicate
`concept_id` keys** in the target (contradictory when scores diverge).

The two decisions compose: switching to accepted-only *already* removes every
observed collision (all 1,758 duplicate pairs came from **pending** 3.8 re-tags
hitting **accepted** 3.5 rows; the apply gate keeps one accepted row per tag, so
accepted-only has **0** duplicate pairs today). The dedup is the **defensive
guarantee** so a future double-accept can never leak duplicate keys.

Landed in `extract.iter_teacher_chunks`: tags now accumulate into a per-concept
dict, keeping the row that `_supersedes` prefers — **accepted > pending, then max
score** (recall-favouring; keeps that row's justification). Not by model label
(3.5/3.8 are unreliable free-text, not a real teacher split). Regression test:
`tests/test_extract_dedup.py` (pure python, no pytest). Guarded invariant: no
target contains a repeated `concept_id`.

## Export shape — actual (accepted-only, deduped, verified)

`data/exports/2026-09-06T12-21-28Z/` on snapshot `2026-09-06T12-15-36Z-v5`:

| | v4 (pending+accepted) | v5 (accepted-only) |
|---|--:|--:|
| examples (chunks) | 4,554 | **4,440** |
| teacher tags | 35,040 | **25,402** |
| concepts | 154 | 154 |
| contributing signatures | 3.5 (30,354) + 3.8 (4,686) | 3.5 (19,211) + 3.8 (6,191) |
| targets with a repeated concept | n/a | **0 / 4,440** ✓ |

Splits: train 4,008 / val 209 / test 223. Fewer rows than v4 but all owner-applied,
and the 12 backfill concepts are present on older-tradition chunks in the export
(incarnation confirmed on `hinduism.bhagavad-gita-chapter-09.001`; older-tradition
counts match the DB: divine_immanence 109 … spirit_conjuration 3).

## Hyperparameters — v4-identical

Reuse `configs/qwen-3-4b-guru-v4.yml` verbatim as `qwen-3-4b-guru-v5.yml` (base
`Qwen3-4B-Instruct-2507`, LoRA r32/α64, 3 epochs, lr 1.5e-4 cosine, bs1×ga16, FA2,
seed 42, load-best/eval_loss, `max_seq_length: 16384`). The 154-concept
definitions block (11,439 tok) is the dominant, unchanged term; the backfill only
lengthens completions on the 385 touched chunks. v4's measured max seq was 15,399
< 16384, so headroom likely holds — but **re-run the VRAM + length smoke test at
16384** on the v5 export before the full run (a handful of newly tag-rich chunks
could nudge the max; fallbacks unchanged: 15,360 / 14,336 / r16).

## Pipeline

Done (this session):
1. ✓ Snapshot `data/snapshots/2026-09-06T12-15-36Z-v5`.
2. ✓ Dedup landed in `extract.iter_teacher_chunks` + `tests/test_extract_dedup.py` (passing).
3. ✓ Export `data/exports/2026-09-06T12-21-28Z` (accepted-only): 4,440 ex / 25,402 tags,
   0 duplicate concept keys, contributing 3.5 + 3.8.
4. ✓ Splits: train 4,008 / val 209 / test 223.

Remaining (owner's GPU call):
5. Copy `configs/qwen-3-4b-guru-v4.yml` → `qwen-3-4b-guru-v5.yml` (recipe verbatim).
6. VRAM smoke-test at 16384 across the length range on the v5 export.
7. Full train `qwen-3-4b-guru-v5` — announce start, `llm stop` first for the 3090,
   pin `CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=0`, via `agent-run`.
8. **Bench vs v4-r32** on the gauge set — v4 never ran the held-out bench; v5 should
   confirm no regression on new-corpus tagging.
9. **Backfill probe** — reuse the v4 plan's probe set. Bellwether: **incarnation ×
   bhagavad-gita ch.4** must now FIRE (v4=0; 19 training rows now, confirmed in the
   export). Thin trio (spirit_conjuration 3 / exorcism 5 / initiation 7) — if v5
   under-tags there, suspect candidate recall in the sample pass, not the review.
   Guards must stay silent (psychic_attack on Kalevala → word_power_incantation;
   occult_police fires nowhere old).
10. If it passes → cheap full-corpus backfill via parallel 4B tagging → `/guru-review-tags`
   queue, owner apply gate. The 27B only ever touched the sample.

## Risks

- **Fewer rows than v4 (25.4k vs 35k)** — the accepted-only cut trades quantity for
  vetted quality; still 4,440 chunks (v3 trained on 3,504). Watch eval_loss/bench.
- **Thin trio (3/5/7 rows)** — leanest signal; the probe is the tell.
- **No edges pass needed** — cross-tradition PARALLELS derive at guru node 16 from
  applied tags, outside tagger training (Pass C retirement).
