# qwen-3-4b-guru-v4 — training plan

**Goal.** Teach the 4B tagger the 44 concepts added since v3 so it can **backfill
the older corpus** — works tagged before those concepts existed. Success = older
works fire on the new concepts *where there is a genuine reference* (the
taxonomy-drift payoff, cf. cosmogony×Enuma Elish), while NOT false-firing modern
Western-esoteric concepts onto lexically-similar ancient passages (the v2
contamination failure mode; see `qwen-3-4b-v2-regression-autopsy.md`).

Same recipe as v3. Deltas: data (two teachers, current corpus) + context length.

## Confirmation: latest export ↔ last finetune

The most recent rellm export `data/exports/2026-08-06T21-46-44Z/` IS v3's basis
(manifest: teacher Qwen3.5-27B, prompt v1, 3,504 examples, 110 concepts — matches
`out/qwen3-4b-guru-v3-r32`). It is now stale: since Aug-6 the taxonomy grew +44,
new corpus was added, and a second teacher appeared. **A fresh snapshot + export
is required for v4.**

## What is new since v3

- **Taxonomy 110 → 154** leaf concepts. 0 removed/renamed (clean superset), still
  `prompt_version=v1`. The +44:
  - Sethian/Gnostic: `barbelo` `luminaries` `self_begotten`
    `incorruptible_generation` `stellar_determinism` `rejection_of_sacrifice`
    `qliphoth`
  - Kybalion Hermetic principles: `mentalism` `vibration` `polarity` `rhythm`
    `gender`
  - Western-esoteric psychism: `psychic_attack` `psychic_vampirism`
    `artificial_elemental` `thought_form` `etheric_projection` `astral_vision`
    `aura` `higher_self` `inner_voice` `invisible_world` `haunting` `possession`
    `exorcism` `spirit_conjuration` `elemental_beings` `occult_police`
    `talisman_magic` `divination` `secret_societies` `esoteric_lineage`
    `initiation` `left_hand_path` `right_hand_path` `telepathy`
    `magical_absorption` `collective_psychic_field` `christ_force` `involution`
    `divine_immanence` `incarnation` `trinity` `relative_truth`
- **New corpus:** `theosophy/blavatsky-sd`, `western_esoteric/*` (kybalion,
  psychic-self-defence, book-of-ceremonial-magic, secret-teachings,
  transcendental-magic ×2, tarot-of-the-bohemians, tertium-organum),
  `gnosticism/gospel-of-judas`.
- **Teacher upgrade — and an unreliable label.** v3 distilled from a teacher
  recorded as `Qwen3.5-27B-UD-Q4_K_XL.gguf`. The new corpus carries two 27B
  signatures — `Qwen3.5…` and `Qwen3.8…` — but that `model` field is a FREE-TEXT
  operator label written by `tag_concepts.py --model` (default
  `Qwen3.5-27B-UD-Q4_K_XL.gguf`, NOT read from the loaded gguf). So the signature
  is not a reliable record of the physical model: the theosophy batch was
  explicitly labeled 3.8; the Aug-17/18 western_esoteric batch (kybalion,
  book-of-ceremonial-magic, tarot, psychic-self-defence — ids 80009–84817, run
  immediately before the 3.8 theosophy block at id 85038+) took the DEFAULT 3.5
  label but was plausibly the same physical 3.8 model. Older western_esoteric
  (tertium-organum May, transcendental-magic July) genuinely predate any 3.8.
  **Bottom line for v4: irrelevant to the export** — the union `s.model IN
  ('Qwen3.5…','Qwen3.8…')` captures every 27B-labeled row regardless. The two
  labels tag disjoint chunk sets (0 overlap), so the union is clean with no
  dedup. Treat "3.5 vs 3.8" as label bookkeeping, not a true teacher split.

## Data recipe

| | v3 | v4 |
|---|---|---|
| teacher filter | single `Qwen3.5-27B` | **denylist: all tags minus student lineage + Carnice-9b** (contributors: 3.5 + 3.8 labels) |
| status filter | pending,accepted | same |
| chunk-examples | 3,504 | **4,554** |
| teacher rows | ~30k | **35,040** |
| concepts | 110 | **154** |
| body resolution | — | 4,554/4,554 (0 drops, post blavatsky-chunk fix) |

## The code change — export by denylist, not teacher allowlist

`extract.iter_teacher_chunks` filtered `s.model = ?` (single teacher). Because
`staged_tags.model` is unreliable free-text (tag_concepts.py `--model` default,
not the loaded gguf), an allowlist would silently drop a mislabeled teacher run.
Reworked to a **denylist**: take every tag EXCEPT `exclude_model_prefixes`
(`qwen-3-4b-guru` — the student lineage, never self-distill) and `exclude_models`
(`Carnice-9b` — 86 chunks, all already 27B-covered, 0 unique). The export
manifest records `contributing_models` (signatures that actually survived, with
row counts) as real provenance read from the data. Landed + smoke-tested: 4,554
chunk-examples, contributors `Qwen3.5-27B` (30,354 rows) + `Qwen3.8-27B` (4,686),
no finetune/Carnice leakage.

## Hyperparameters — v3-identical except max_seq_length

Base `Qwen3-4B-Instruct-2507`, LoRA r32/α64, 3 epochs, lr 1.5e-4 cosine,
bs1×ga16, FA2, seed 42, load-best/eval_loss. See `configs/qwen-3-4b-guru-v4.yml`.

Measured total sequence (real Qwen tokenizer, input+completion): p50 12,618,
p90 13,367, p99 14,534, **max 15,399**. Definitions block alone = 11,439 tokens
(v3: 6,128).

- **`max_seq_length: 16384`** → 0 truncation. Fallbacks if the 3090 won't hold
  16K: 15,360 (0.2% trunc), 14,336 (1.4%), or r16.
- **Risk:** 16K is ~1.7× v3's window. Smoke-test at 16384 on the 3090 before the
  full run (v3 smoke-tested 8192/9472).

## Pipeline

1. Patch multi-teacher export.
2. `rellm snapshot --label v4` → frozen guru.db.
3. `rellm export` (both teachers, pending+accepted, pinned 154-concept
   taxonomy.toml) → `rellm splits`.
4. VRAM smoke-test at 16K → full train `qwen-3-4b-guru-v4`.
5. Bench vs v3-r32 on the existing gauge set.
6. Run the probe set below.
7. If it passes → full backfill via parallel 4B tagging (full taxonomy in prompt,
   post-filter to the 44-concept delta) → `/guru-review-tags` queue, owner apply
   gate.

## Probe set — the test at the end

All verified: real chunks, **zero existing tags** for the target concept, tagged
before the concept existed. A fire is genuine backfill, not re-detection.

| # | concept | older work (tradition) | chunks | expect | proves |
|---|---|---|---|---|---|
| 1 | `incarnation` | bhagavad-gita ch.4 (hinduism) | 237 | FIRE | anchor — Krishna's avatāra declaration; near-certain |
| 2 | `qliphoth` | greater/lesser-holy-assembly, book-of-concealed-mystery (jewish_mysticism) | 178 | FIRE | thin concept (3 rows) recovers its native home — Zohar shells / kings of Edom |
| 3 | `mentalism`+`vibration` | corpus-hermeticum (hermeticism) | 60 | FIRE | Kybalion principles land on their source text |
| 4 | `trinity` | bhagavad-gita (hinduism) & book-of-the-dead (egyptian) | 237 / 453 | FIRE | cross-tradition structural transfer (Trimurti; Amen/Ptah/Osiris) |
| 5 | `divine_immanence` | tao-te-ching, zhuangzi (taoism) | 138 | FIRE | immanence recognized outside its Western-esoteric framing |
| 6 | `divination` | omen/extispicy texts (mesopotamian) | 56 | FIRE | central ancient practice under the new label |
| 7 | `psychic_attack` | kalevala (finnic) | 275 | SILENT | v2-guard — curse/spell bait must route to `word_power_incantation` |
| 8 | `occult_police` | entire old corpus | — | SILENT | hallucination guard — a 4-row concept must fire nowhere old |

**Read.** 1–6 firing (score ≥2, justification citing the real passage) = the
backfill goal works. 7–8 silent = no regression to v2 false-friend contamination.
The bellwether is **#2**: if a 3-example concept correctly lights up the Zohar,
the thin-concept worry is largely answered; if dark, do a small 27B top-up on the
thin set before backfilling.

## Risks carried forward

- **10 thin new concepts (<5 rows):** qliphoth, barbelo, luminaries,
  collective_psychic_field, occult_police, self_begotten, magical_absorption,
  inner_voice, aura, telepathy. Probe #2 is the bellwether; top-up only if it
  underperforms.
- **Teacher mix (3.5 ∪ 3.8):** low risk (disjoint, same prompt v1); watch bench
  for style seams.
- **16K VRAM fit:** smoke-test gated.
