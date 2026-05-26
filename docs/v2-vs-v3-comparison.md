# v2 → v3 comparison

**tl;dr.** v3 is the best tagger we've trained, on every headline metric. Against
human ground truth on the held-out test split it lifts **recall 0.415 → 0.524
(+0.109)** with **precision holding at 0.769** (up from 0.759) — F1 **0.537 →
0.623 (+0.086)**. The gain came from data, not capacity: identical hyperparameters
to v2, but trained on labels that are now 48% human-verified with ~6,000 more
human-accepted positives. The cost is small: parse rate dips to 96.9% and latency
rises to 5.8 s/chunk, both because v3 emits more tags.

This is the cycle where the distilled 7B student clearly **surpasses its 27B
teacher on precision** (0.769 vs 0.666) while closing most of the recall gap.

## How v3 was built

Same recipe as v2 (Unsloth QLoRA, r=32/α=64 all-linear, 3 epochs, batch 1 ×
grad-accum 16, lr 1.5e-4 cosine, paged AdamW-8bit, max_seq_length 5632, seed 42)
— **only the data changed**, so the v2→v3 delta isolates the data effect.

| | v2 | v3 |
|---|---|---|
| Snapshot | 2026-05-21 (pre-review) | 2026-05-25 (post human-review push) |
| Export | `data/exports/2026-05-21T16-49-07Z` | `data/exports/2026-05-25T13-52-51Z` |
| Chunks | 2,598 | 2,808 (+210 newly tagged) |
| Target tags | 19,936 | 25,559 |
| — human-accepted | ~2,265 (≈11%) | **12,187 (48%)** |
| — pending (unreviewed) | bulk | 13,372 |
| — human-rejected (dropped) | included as positives | **0** (789 v2 positives now removed) |
| Trained examples (post-5632 filter) | ~2,180 (171 dropped, 6.6%) | **2,102** (457 dropped, 17%) |

Two things to note:

- **The lever was recall/label-quality, not precision-cleaning.** Only 789 of v2's
  target tags were later rejected by humans — v2 wasn't badly polluted. The real
  change is **+~6,000 human-accepted positives** (3,621 added to existing chunks,
  2,412 from new chunks). Those are endorsed labels v2 never saw, and they're what
  moved recall.
- **v3 trains on *fewer* examples than v2** (2,102 vs ~2,180). Its denser labels
  push 17% of examples past the 3090's 5632-token ceiling, where they're dropped
  (right-truncation would cut the assistant JSON). v3 wins anyway because the
  examples it keeps carry much richer, cleaner labels — but fully exploiting the
  new signal wants a larger GPU at >5632 ctx.

Held-out integrity: `assign_split()` is a deterministic chunk_id hash, so all 129
surviving v2-test chunks land in v3's test bucket again (0 leak). All four models
below are evaluated on the identical held-out chunks and the identical human labels.

## Headline: humans as ground truth

Held-out test split, scored against human accept/reject verdicts (763 graded
cells/model, 118 chunks). This is the strongest signal — independent of the teacher.

| Model | Precision | Recall | F1 | Specificity |
|-------|----------:|-------:|------:|------------:|
| base  | 0.833 | 0.118 | 0.207 | 0.953 |
| v1    | 0.673 | 0.356 | 0.466 | 0.655 |
| v2    | 0.759 | 0.415 | 0.537 | 0.737 |
| **v3** | **0.769** | **0.524** | **0.623** | 0.686 |
| 27B teacher\* | 0.666 | 1.000 | 0.799 | 0.000 |

\* The teacher's recall is 1.0 *by construction* — humans only reviewed tags the
teacher emitted, so its misses can't be counted. Its **precision (0.666)** is the
honest, comparable number; both v2 and v3 beat it.

- **Recall +0.109** (0.415 → 0.524): v3 recovers 266 of 508 human-accepted concepts
  vs v2's 211 — 55 more hits, 55 fewer misses. This is the weakness v3 targeted.
- **Precision held** (0.759 → 0.769): no trade-off; v3 is both more eager *and*
  slightly more correct.
- **Specificity −0.051** (0.737 → 0.686): the lone cost — emitting more produces 13
  more false positives. The +55 true positives dwarf it.

## Teacher-label view (continuity with the v1/v2 docs)

| Model | Precision | Recall | F1 | Macro-F1 | MAE | Parse | Lat (s) | n_emit |
|-------|----------:|-------:|------:|---------:|----:|------:|--------:|-------:|
| base  | 0.398 | 0.152 | 0.220 | 0.176 | 0.53 | 96.2% | 3.97 | 4.1 |
| v1    | 0.621 | 0.509 | 0.560 | 0.386 | 0.37 | 100.0% | 4.94 | 8.8 |
| v2    | 0.669 | 0.518 | 0.584 | 0.502 | 0.42 | 99.2% | 4.75 | 8.3 |
| **v3** | 0.636 | **0.585** | **0.609** | **0.522** | 0.42 | 96.9% | 5.83 | 9.8 |

v3 leads on F1, recall, and macro-F1. Its teacher-*precision* dips (0.669 → 0.636)
**because** it now emits human-correct tags the teacher missed — which is exactly
why its *human* precision rose. The student is no longer just mimicking the teacher.

## Per-tradition (teacher-label F1, v2 → v3)

| Tradition | n | v2 | v3 | Δ |
|---|---:|---:|---:|---:|
| christian_mysticism | 6 | 0.457 | 0.586 | +0.129 |
| greek_mystery | 15 | 0.525 | 0.590 | +0.065 |
| taoism | 10 | 0.562 | 0.610 | +0.048 |
| hermeticism | 4 | 0.430 | 0.470 | +0.040 |
| gnosticism | 5 | 0.557 | 0.589 | +0.032 |
| neoplatonism | 39 | 0.679 | 0.690 | +0.011 |
| egyptian | 23 | 0.629 | 0.636 | +0.007 |
| western_esoteric | 10 | 0.548 | 0.544 | −0.003 |
| buddhism | 3 | 0.579 | 0.537 | −0.042 |
| zoroastrianism | 2 | 0.667 | 0.615 | −0.051 |
| jewish_mysticism | 6 | 0.732 | 0.667 | −0.065 |

Gains concentrate in the mid-frequency traditions that got the most new review;
the small regressions are all on tiny slices (2–6 chunks) where one chunk swings F1.

## Per-concept (teacher-label F1, v2 → v3, ≥4 teacher positives)

**Top gains**

| Concept | n | v2 | v3 | Δ |
|---|---:|---:|---:|---:|
| archons | 4 | 0.000 | 0.667 | +0.667 |
| separation_from_source | 18 | 0.182 | 0.412 | +0.230 |
| alchemical_work | 9 | 0.500 | 0.714 | +0.214 |
| infinite_cosmos | 6 | 0.250 | 0.444 | +0.194 |
| theurgy | 14 | 0.500 | 0.692 | +0.192 |
| correspondence | 30 | 0.308 | 0.500 | +0.192 |
| inner_silence | 11 | 0.476 | 0.667 | +0.190 |
| living_god | 49 | 0.453 | 0.619 | +0.166 |
| body_as_obstacle | 26 | 0.550 | 0.704 | +0.154 |

Notably `archons` (F1 0 in every prior version) and `living_god`/`body_as_obstacle`
(both *regressed* in v1→v2) recover strongly — the new accepted labels filled in
concepts that earlier versions were blind to or had lost.

**Top regressions**

| Concept | n | v2 | v3 | Δ |
|---|---:|---:|---:|---:|
| sunyata_emptiness | 4 | 0.857 | 0.667 | −0.190 |
| evil_as_privation | 12 | 0.421 | 0.240 | −0.181 |
| heroic_furor | 4 | 1.000 | 0.857 | −0.143 |
| eschatological_judgment | 12 | 0.727 | 0.615 | −0.112 |
| demiurge | 10 | 0.571 | 0.462 | −0.110 |
| hidden_sayings | 31 | 0.667 | 0.557 | −0.109 |

Mostly small-n concepts; `evil_as_privation` and `hidden_sayings` are the only
mid-frequency regressions worth watching downstream.

## Known v3 caveat: occasional over-generation (parse 96.9%)

On ~3% of chunks v3 slips into runaway over-generation — it keeps emitting tag
objects until it hits the token cap and truncates into invalid JSON. Diagnosis on
the 4 failing test chunks:

- It is **non-deterministic even at temperature 0** (llama.cpp greedy is not
  bit-exact): the same chunk parses fine one run and runs away the next.
- Raising `max_tokens` does **not** reliably fix it — sometimes it just gives the
  runaway more room (one chunk parsed at 4096 but truncated at 8192).
- This is the flip side of v3's eagerness — the same "emit more" behavior that
  bought +0.109 recall occasionally overshoots.

It is intrinsic and mild, not a retrain-worthy bug. Mitigations are downstream:
a truncation-salvage parser (recover complete objects before the cut) and/or a
retry on parse failure in the guru caller (works often, given the non-determinism).

## Reproduce

```bash
# data (drops human-rejected tags via the pending,accepted status filter)
uv run rellm snapshot
uv run rellm export   --snapshot data/snapshots/<ts>
uv run rellm splits   data/exports/<ts>           # deterministic; preserves held-out set

# train (~15h on a 24GB 3090)
uv run python train/train_distill.py \
  --config configs/qwen25-7b-distill-v3.yml \
  --export-dir data/exports/2026-05-25T13-52-51Z \
  --output-dir out/qwen25-7b-r32-v3

# gguf
uv run python scripts/merge_adapter.py --adapter-dir out/qwen25-7b-r32-v3/adapter \
  --out-dir out/qwen25-7b-r32-v3/merged --max-seq-length 5632
bash scripts/to_gguf.sh out/qwen25-7b-r32-v3/merged qwen2.5-7b-rellm Q4_K_M

# bench (human-graded, identical held-out chunks)
bash scripts/bench_gauge.sh        # base / v1 / v2
bash scripts/bench_v3_add.sh       # folds v3 into the same gauge
```

Bench dir for this report: `runs/bench/gauge-v3-2026-05-26T05-02-37Z`.
