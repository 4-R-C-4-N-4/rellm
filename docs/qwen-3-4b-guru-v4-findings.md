# qwen-3-4b-guru-v4 — findings

Trained 2026-09-02/03 (see `qwen-3-4b-guru-v4-plan.md`). Goal: teach the 44
concepts added since v3 so the 4B can **backfill older works** tagged before
those concepts existed. Below is what the training + probe actually showed.

## Training: clean success

- 771 steps / 3 epochs, ~30.7h, best eval_loss ≈0.182 (monotonic decline, no
  overfit). Adapter → `out/qwen3-4b-guru-v4-r32/`; merged + Q4_K_M gguf built.
- 16384 window: **0 examples truncated** (max seq 15,399 < window). Peak 18.2GB
  on the 3090, FA2 active.
- v4 is a **disciplined tagger**: ~15 tags/chunk vs the base model's ~85/chunk
  shotgun (the v2-autopsy over-tagging failure mode is absent). It tags
  old-concept content richly and sensibly.

## Backfill: does NOT work as hoped — and the reason is subtle

**Structural fact (data):** all 44 new concepts have **2,157 training rows, 100%
on the new corpus (theosophy/western_esoteric/gnosticism), 0 on any older
tradition.** Taxonomy drift: the older works were tagged before these concepts
existed, so the teacher never applied them there. v4 learned each new concept in
its Blavatsky/Hermetic/Gnostic flavor only.

**Probe (232 older-tradition chunks, full 154-concept prompt):**
- 10/44 new concepts fired on ≥1 older chunk (score≥2); the rest did not fire in
  the sample. But this is a **loose lower bound** — the probe sampled whole works,
  not concept-bearing passages, so many "misses" are just the concept being
  absent from the sampled chunks (confirmed: the 27B agrees several sampled
  cells, e.g. qliphoth×greater-holy-assembly.001, divination×adapa, carry no
  such concept). Do not read "34/44 never fired" as 34 real failures.
- Negative guards held: `occult_police` fired **0/232** (hallucination guard
  clean); Kalevala runo-magic routed to `word_power_incantation` 36/40 (correct),
  with one stray `psychic_attack` (1/40 — minor leak, not a v2-style explosion).

**The one clean case — a genuine capacity gap, NOT a fine-tune artifact.**
The Gita ch4 chunk is the textbook avatāra passage ("I am born age after age…"),
which the `incarnation` definition explicitly names ("the Hindu avatara"). Result
on that exact chunk, full taxonomy in prompt:

| model | incarnation score |
|---|---|
| **27B teacher** (Qwen3.8) | **3 (central)** |
| base Qwen3-4B | 0 |
| v4 (fine-tuned 4B) | 0 |

So the concept **is** present and detectable — the 27B nails it — but **neither
4B** surfaces it, fine-tuned or not. This corrects an earlier wrong call of mine
("fine-tuning overrode the definition"): base misses it too. It's a model-capacity
gap (a 4B can't discriminate this subtle cross-tradition concept from the
definition alone, and it gets crowded out of the 4B's ~15-tag budget by stronger
matches like detachment/gnosis/mystical_union), compounded by zero cross-tradition
training signal.

## Bottom line

- v4 is a good, disciplined tagger for **new-corpus-style** text (what it trained
  on). It did not regress into base's shotgun behavior.
- v4 **cannot reliably backfill the new concepts onto older traditions** — partly
  a capacity gap (incarnation×Gita), partly that the training set had no
  cross-tradition examples of these concepts to learn from.
- The cheap-4B-backfill premise is undercut: the only model that reliably surfaces
  these concepts on old traditions is the 27B — which is exactly the slow model
  the 4B was meant to replace (~110s/chunk with thinking).

## Recommended path (not yet done — owner's call)

To actually get backfill, close the training gap rather than expect zero-shot
generalization:
1. **27B sample pass:** run the 27B on a stratified SAMPLE of older-tradition
   chunks (the traditions each new concept plausibly lives in) with the full
   taxonomy, post-filter to the 44 new concepts. The 27B fires them (incarnation=3),
   so this yields real cross-tradition positives.
2. **Retrain v5** with those examples folded in → v5 has seen incarnation-on-Hindu,
   trinity-on-Egyptian, etc., and should generalize where v4 can't.
3. v5 (cheap) then backfills the full corpus; the 27B only ever touched a sample.

Alternative if a v5 is not worth it: use the 27B directly for the new-concept
backfill (accept the cost), and keep v4 for new-corpus tagging.

Artifacts: adapter/merged/gguf in `out/qwen3-4b-guru-v4-r32/`; probe outputs were
in scratch (not committed). Bench vs v3 on held-out test was not run — the backfill
question dominated and is answered.

## v5 backfill — DONE through verification (2026-09-06)

Steps 1 and the review/apply of the "Recommended path" above are complete; only
the retrain (step 2) remains, and it is rellm's to run.

- **Scope narrowed to 12 concepts, not 44.** The psychism concepts (psychic_attack,
  etheric_projection, aura, thought_form, occult_police, …) have no ancient home to
  backfill onto and were dropped. The 12 genuinely cross-tradition drift concepts:
  trinity, stellar_determinism, divine_immanence, initiation, divination,
  esoteric_lineage, exorcism, gender, spirit_conjuration, incarnation, qliphoth,
  talisman_magic.
- **27B sample pass** (guru `scripts/assemble_v5_candidates.py` → 531 older-tradition
  candidate chunks, `data/backfill-v5/union-chunk-ids.txt`) tagged by Qwen3.8-27B,
  net-new tags reviewed to exhaustion via `/guru-review-tags` (queue-only,
  reviewer=agent-claude), owner applied.
- **Node 4 gate PASS** — every one of the 12 now carries non-zero older-tradition
  live `EXPRESSES` rows (was 0/44 cross-tradition for v4):

  | concept | rows | concept | rows | concept | rows |
  |---|--:|---|--:|---|--:|
  | divine_immanence | 109 | divination | 38 | stellar_determinism | 31 |
  | gender | 29 | trinity | 24 | incarnation | 19 |
  | esoteric_lineage | 13 | talisman_magic | 12 | qliphoth | 8 |
  | initiation | 7 | exorcism | 5 | spirit_conjuration | 3 |

  The v4 bellwether `incarnation` (27B=3 / v4=0 on the Gita) is now 19 older-tradition
  rows incl. hinduism. Thin trio (spirit_conjuration 3 / exorcism 5 / initiation 7)
  clears non-zero but is lean — if v5 eval under-tags there, suspect candidate recall
  (too few older chunks surfaced), not the review.

**Remaining (rellm, owner's GPU call):** fresh SFT export via the landed denylist
(these accepted tags now flow in as positives) → retrain v5 on the v4 recipe/config
→ v5 backfills the full corpus cheaply. No edges pass is needed (guru node 14 edge
review is retired with Pass C; cross-tradition PARALLELS derive at node 16 from
applied tags, outside tagger training).
