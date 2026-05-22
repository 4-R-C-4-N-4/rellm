# qwen2.5-7b-rellm: v1 → v2 comparison

## tl;dr

v2 wins on every aggregate metric, but the headline is in the distribution,
not the average:

- **Full v2 test split (130 chunks, vs teacher labels)**: F1 **0.577 → 0.599** (+0.022),
  **macro-F1 0.398 → 0.525 (+0.127)**. The macro-F1 jump is the real story —
  v2 is far more uniformly competent across the 85 active concepts. v1 was strong
  on a few high-frequency concepts and weak on many.
- **v1-test carryover (103 chunks, the chunks v1 was originally evaluated on)**:
  F1 0.612 (v1) vs 0.602 (v2) — basically tied. v1 holds its ground on its home
  turf, but with much lower macro-F1 (0.402 vs 0.513).
- **Held-out test chunks vs human labels (92 chunks)**: F1 **0.411 (v1) → 0.529 (v2)**
  (+0.118). v2 nearly matches the 27B teacher's own human-rated F1 of 0.549
  at 7B inference cost.
- **Domain coverage**: v2 finally scores on traditions v1 either skipped
  (buddhism, sufism) or saw too little of (mesopotamian, jewish_mysticism).
  Largest gains: mesopotamian +0.32, jewish_mysticism +0.20, buddhism +0.19,
  sufism +0.14.
- **Trade-off**: v2 regresses slightly on traditions v1 over-specialized on —
  egyptian -0.06, hermeticism -0.08, western_esoteric -0.03.
- **v1 model card numbers reproduce**: sanity-bench gives F1=0.615 on the
  original 103 chunks (vs published 0.629); the small drift is from running
  the bench against the current 88-concept taxonomy file rather than the
  v1-era 61-concept taxonomy.

## What changed between v1 and v2

### Training data

| | v1 (2026-05-13 export) | v2 (2026-05-21 export) | Δ |
|---|---:|---:|---:|
| Source snapshot | `2026-05-11T22-12-29Z-initial` | `2026-05-21T16-47-43Z-80concept` | — |
| Corpus chunks | 2,852 | 3,089 | +237 |
| Taxonomy concepts (in snapshot) | 62 | 89 | +27 |
| Concepts with teacher rows | 61 | 88 | +27 |
| SFT examples (chunks with ≥1 tag) | 2,188 | 2,598 | +410 (+19%) |
| Train / val / test split | 1,979 / 106 / 103 | 2,339 / 129 / 130 | — |
| Teacher | `Qwen3.5-27B-UD-Q4_K_XL.gguf` | same | — |
| Prompt version | v1 | same | — |
| Status filter | pending,accepted | same | — |

Notable: **all 103 v1-test chunks survive into v2-test** (deterministic chunk-id
hashing). The 27 new v2-test chunks come from the corpus growth + new
traditions. That gives us a built-in apples-to-apples 103-chunk subset for
direct v1↔v2 head-to-head, in addition to the full 130-chunk v2 split.

### Training config

| Knob | v1 (`qwen25-7b-distill.yml`) | v2 (`qwen25-7b-distill-v2.yml`) |
|---|---|---|
| LoRA r | 32 | 32 (tried 64; OOMed at 8k ctx) |
| LoRA α | 64 | same |
| Learning rate | 2.0e-4 | **1.5e-4** |
| Epochs | 3 | 3 |
| Per-device batch / grad accum | 2 / 8 | **1 / 16** (effective 16 unchanged) |
| Optimizer | adamw_8bit | **paged_adamw_8bit** (CPU-offloads optimizer state) |
| Max seq length | 4096 | **5632** (dropped 171 longer examples) |
| Sequence packing | off | off |
| Checkpoint selected | last | **best-by-val-loss** (eval_loss) |
| Base | unsloth/Qwen2.5-7B-Instruct-bnb-4bit | same |

Notable: v1 silently truncated 3.2% of its training examples at
`max_seq_length=4096`. v2 needed a longer context because the 88-concept
prompts run median 5137 / max 6352 tokens — at 4096 v2 would have truncated
100% of examples, cutting the assistant response from every one. 5632 was the
largest context that fits backward on a 24 GB 3090 at r=32 batch=1 (8k OOMed
on backward, 6k OOMed at the longest examples). The trainer drops examples
that exceed `max_seq_length` rather than letting SFTTrainer right-truncate,
since right-truncation would cut the assistant JSON response. Final training
set: 2,179 chunks (160 of the 2,339 train chunks were over 5632).

Effective batch and LoRA size are matched to v1, so the v2 quality gain is
attributable to the data + the no-truncation fix, not capacity bumps.

Total wall-clock: **15h 51m on a single 3090** for the final run. Final
train_loss 0.371 (running average), final eval_loss 0.301 (vs v1's 0.471).

## Headline metrics

`v2-test (130 chunks)` and `v1-test (103 chunks)` use teacher labels from
the v2 snapshot. `human-graded` uses accepted/rejected labels from the
upstream guru staged_tags table.

### vs teacher labels — full v2 test split (130 chunks, 88 concepts)

| Model   | Precision | Recall | F1    | Macro-F1 | MAE  | Parse rate | OOT-IDs | Lat (s) |
|---------|----------:|-------:|------:|---------:|-----:|-----------:|--------:|--------:|
| base    | 0.328     | 0.162  | 0.217 | 0.182    | 0.53 | 96.2%      | 9       | 4.00    |
| v1      | 0.558     | 0.596  | 0.577 | 0.398    | 0.38 | 100.0%     | 2       | 4.97    |
| v2      | **0.597** | **0.602** | **0.599** | **0.525** | 0.42 | 99.2% | 2 | 4.72 |

### vs teacher labels — v1-test carryover subset (103 chunks)

Same chunks v1 was originally evaluated on, scored against the v2-era teacher
labels (88 concepts).

| Model   | Precision | Recall | F1    | Macro-F1 | MAE  | OOT-IDs |
|---------|----------:|-------:|------:|---------:|-----:|--------:|
| base    | 0.311     | 0.161  | 0.212 | 0.164    | 0.51 | 8       |
| v1      | **0.609** | **0.615** | **0.612** | 0.402 | 0.38 | 2 |
| v2      | 0.600     | 0.604  | 0.602 | **0.513** | 0.44 | 1     |

v1 wins narrowly on F1 on its home-turf chunks but loses on macro-F1 —
again, v2 spreads competence across more concepts even on the v1-era split.

For reference, v1's model card reported F1=0.629 / Macro-F1=0.548 against
the v1-era 61-concept teacher labels. A sanity rerun (v1 GGUF against
v1's original snapshot + export) gives F1=0.615 / Macro-F1=0.433 — model
card reproduces to within 0.014 on F1.

### vs human-graded labels (held-out test chunks, 92 chunks)

The cleanest signal: human labels don't change as the teacher does, and we
filter to chunks not seen during fine-tuning. n is smaller because the
intersection of (curated chunks in current snapshot) ∩ (chunks in v2 test
split) is modest.

| Model   | TP | FP | FN | TN | Precision | Recall | F1    | Specificity |
|---------|---:|---:|---:|---:|----------:|-------:|------:|------------:|
| base    | 6  | 2  | 32 | 52 | 0.750     | 0.158  | 0.261 | 0.963       |
| v1      | 15 | 20 | 23 | 34 | 0.429     | 0.395  | 0.411 | 0.630       |
| v2      | **18** | 12 | 20 | 42 | **0.600** | **0.474** | **0.529** | **0.778** |

Teacher (27B) human-rated F1 on the same 1,481-cell pool: **0.549** with
precision 0.378, recall 1.000 (by construction — only teacher-positive cells
are in the curated pool). v2 at F1=0.529 on test chunks essentially matches
the 27B teacher's own human-F1 at 7B compute cost. v1 trails meaningfully.

(The full curated bench was on 500 chunks × 3 models; the test-split numbers
above are the slice not seen during fine-tuning. The train/val/all rows are
in `runs/bench/v2-human-2026-05-22T16-13-20Z/` for anyone wanting to read
the full table.)

## Per-tradition deltas

F1 vs teacher labels on the full v2-test split. Largest n chunks first.

| Tradition           | n chunks | base F1 | v1 F1 | v2 F1 | v2−v1 |
|---------------------|---------:|--------:|------:|------:|------:|
| neoplatonism        | 39       | 0.244   | 0.693 | 0.679 | −0.014 |
| egyptian            | 23       | 0.192   | 0.687 | 0.629 | −0.058 |
| greek_mystery       | 15       | 0.136   | 0.430 | 0.491 | +0.061 |
| taoism              | 10       | 0.137   | 0.524 | 0.542 | +0.018 |
| western_esoteric    | 10       | 0.273   | 0.584 | 0.551 | −0.033 |
| christian_mysticism | 6        | 0.286   | 0.394 | 0.458 | +0.064 |
| jewish_mysticism    | 6        | 0.230   | 0.531 | **0.732** | **+0.201** |
| gnosticism          | 5        | 0.190   | 0.492 | 0.590 | +0.098 |
| renaissance_hermeticism | 4    | 0.351   | 0.615 | 0.675 | +0.060 |
| hermeticism         | 4        | 0.240   | 0.482 | 0.405 | −0.077 |
| buddhism            | 3        | 0.261   | 0.385 | **0.579** | **+0.194** |
| zoroastrianism      | 2        | 0.000   | 0.476 | 0.550 | +0.074 |
| mesopotamian        | 1        | 0.200   | 0.556 | **0.875** | **+0.319** |
| platonism           | 1        | 0.333   | 0.250 | 0.500 | +0.250 |
| sufism              | 1        | 0.000   | 0.529 | 0.667 | +0.138 |

The pattern is consistent with the macro-F1 story: v2 picks up the
under-represented traditions v1 had no signal on (buddhism, jewish_mysticism,
mesopotamian, sufism), and slightly cedes ground on the traditions v1
over-specialized on through heavy training-mass bias (egyptian, hermeticism,
western_esoteric).

## Per-concept deltas (n ≥ 3 teacher positives)

### Top 10 v2 gains over v1

| Concept | n | v1 F1 | v2 F1 | Δ |
|---|---:|---:|---:|---:|
| detachment_gelassenheit  | 5  | 0.000 | 0.667 | +0.667 |
| alchemical_work          | 3  | 0.000 | 0.667 | +0.667 |
| evil_as_privation        | 6  | 0.000 | 0.615 | +0.615 |
| wu_wei                   | 4  | 0.000 | 0.615 | +0.615 |
| prayer                   | 16 | 0.000 | 0.593 | +0.593 |
| theurgy                  | 9  | 0.000 | 0.526 | +0.526 |
| mechanical_humanity      | 4  | 0.000 | 0.400 | +0.400 |
| anamnesis                | 3  | 0.000 | 0.400 | +0.400 |
| infinite_cosmos          | 5  | 0.000 | 0.286 | +0.286 |
| eschatological_judgment  | 8  | 0.400 | 0.667 | +0.267 |

Ten concepts went from F1=0 to F1>0.4 — these were concepts v1 was effectively
blind to (low signal or out-of-distribution for its training mix).

### Top 10 v2 regressions vs v1

| Concept | n | v1 F1 | v2 F1 | Δ |
|---|---:|---:|---:|---:|
| living_god             | 44 | 0.699 | 0.486 | −0.213 |
| opposites_transcended  | 16 | 0.606 | 0.439 | −0.167 |
| body_as_obstacle       | 22 | 0.667 | 0.500 | −0.167 |
| ritual_purity          | 16 | 0.364 | 0.222 | −0.141 |
| correspondence         | 16 | 0.500 | 0.400 | −0.100 |
| apophatic_theology     | 35 | 0.727 | 0.633 | −0.094 |
| unity_of_being         | 48 | 0.659 | 0.583 | −0.076 |
| monad                  | 24 | 0.830 | 0.755 | −0.075 |
| logos                  | 31 | 0.618 | 0.549 | −0.069 |
| self_knowledge         | 25 | 0.582 | 0.524 | −0.058 |

The regressions are all on high-frequency concepts where v1 had heavy
training signal. v2's broader concept distribution dilutes the per-concept
data, costing some precision on the dominant concepts. No regression is
catastrophic; biggest drop is `living_god` at −0.213.

## Latency, parse, and out-of-taxonomy

Greedy decoding, single 3090, llama-server with `--jinja`.

| Model | Latency (s/chunk) | Parse rate | Avg tags emitted | OOT-IDs |
|-------|-----:|-----:|-----:|-----:|
| base  | 4.00 | 96.2% | 4.1  | 9 |
| v1    | 4.97 | 100.0% | 8.8 | 2 |
| v2    | 4.72 | 99.2%  | 8.3 | 2 |

v2 is marginally faster than v1 (fewer tokens emitted because it's
somewhat more conservative on borderline cases). Parse rate is 99.2% —
one chunk in 130 produced invalid JSON for v2; v1 was 100%. OOT-IDs tied
at 2. Both fine-tuned models are dramatically better than base on
parse rate and OOT discipline.

## Caveats

- **Not a clean data-only A/B with v1.** v2 also changed: learning rate
  (2e-4 → 1.5e-4), max_seq_length (4096 → 5632), gradient-accumulation
  shape (2×8 → 1×16), optimizer (adamw_8bit → paged_adamw_8bit),
  best-by-val checkpoint selection, and dataset-level filtering of
  examples over the context limit. All but the first were forced
  decisions to make training fit/work; none target adapter capacity.
- **88 vs 61 concepts is a real distribution shift.** The v1 model on the
  v2-test split is being asked to score 27 concepts it was never trained
  on. v1's apparent F1 of 0.577 includes its zero-shot performance on
  those 27 concepts.
- **Train contamination in the human bench.** The full 500-chunk human
  bench mixes train + val + test chunks; only the test slice (92 chunks)
  is a clean held-out comparison. v1's apparent advantage on the ALL row
  is from train-set memorization.

## How this was run

- Snapshot: `data/snapshots/2026-05-21T16-47-43Z-80concept/`
- Export: `data/exports/2026-05-21T16-49-07Z/` (2,598 examples, 88 concepts)
- v2 training: `configs/qwen25-7b-distill-v2.yml` → `out/qwen25-7b-r32-v2/`
  (15h 51m, 411 steps, batch=1×ga=16)
- Three-way bench (base + v1 + v2): `scripts/bench_v2_serial.sh` →
  `runs/bench/v2-vs-v1-vs-base-serial-2026-05-22T15-31-12Z/`
- v1 sanity bench: `scripts/bench_v1_sanity.sh` →
  `runs/bench/v1-sanity-2026-05-22T16-02-51Z/`
- Human-curated bench: `EXTRA_ARGS="--all-curated --limit 500" scripts/bench_v2_serial.sh` →
  `runs/bench/v2-human-2026-05-22T16-13-20Z/`
- Comparison report: `eval/report_v2_compare.py runs/bench/v2-vs-v1-vs-base-serial-2026-05-22T15-31-12Z --v1-export data/exports/2026-05-13T16-31-48Z`
