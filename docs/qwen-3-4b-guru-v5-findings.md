# qwen-3-4b-guru-v5 — findings

Trained + evaluated 2026-09-07 (plan: `qwen-3-4b-guru-v5-plan.md`). Goal: ship the
backfill v4 deferred — a disciplined 4B that surfaces the 12 cross-tradition drift
concepts on older traditions where v4 (0 cross-tradition training rows) was blind.
**Result: achieved.** v5 beats v4 on the held-out bench across the board and
recovers the backfill without regressing the guards.

## Training

Recipe = v4 verbatim, data = accepted-only + deduped export (4,440 ex / 25,402
tags / 0 dup keys). 753 steps / 3 epochs, ~29.4 h on the 3090, peak VRAM 12.8 GB
(no fallback). **Best eval_loss 0.1788 @ step 753** (= final; monotonic
0.1926→0.1788, no overfit); `load_best` restored it. Adapter/merged/Q4_K_M gguf in
`out/qwen3-4b-guru-v5-r32/`.

## Bench — held-out test split (223 chunks, teacher = accepted labels, full 154-concept prompt)

| model | precision | recall | F1 | MAE | tags/chunk | OOT ids |
|---|--:|--:|--:|--:|--:|--:|
| base | 0.120 | 0.503 | 0.194 | 0.51 | 44.7 | 31 |
| v4 | 0.236 | 0.480 | 0.316 | 0.40 | 11.3 | 5 |
| **v5** | **0.279** | **0.537** | **0.367** | **0.31** | 10.7 | 4 |

**v5 > v4 on every axis:** precision +0.043, recall +0.057, **F1 0.316→0.367
(+16% rel)**, lower MAE (0.40→0.31), fewer invented ids (5→4). Macro-F1
0.243→0.274. v5's recall (0.537) even exceeds base's (0.503) while staying ~4×
more precise and staying disciplined (10.7 vs base's 44.7 tags/chunk — the v2
shotgun failure mode is absent). No regression; a clean improvement.

(The test split is v5's accepted-only split; some chunks may have been in v4's
train — a leak that would *favour* v4. v5 wins anyway.)

## Probe — the backfill test (32 held-out val/test older-tradition cells, 9 concepts)

Cells where a backfill concept is a vetted-accepted positive on an older-tradition
chunk **v5 never trained on**. (Only 9 of 12 concepts had held-out cells;
initiation/exorcism/qliphoth had all their older rows in train.) Score ≥2 fired:

| | fired ≥2 / n |
|---|--:|
| base | 19 / 32 (shotgun — 44 tags/chunk, no discrimination) |
| **v4** | **3 / 32** ← the v4 blindness |
| **v5** | **19 / 32** |

**v5 recovers 19/32 where v4 managed 3/32** — and does it with discipline (base
matches the recall only by spraying 44 tags/chunk at P=0.12). Per concept, v5 vs
v4 (fired ≥2 / n): divine_immanence 7/10 vs 1, gender 4/4 vs 0, divination 3/4 vs
0, stellar_determinism 3/4 vs 1, esoteric_lineage 1/3 vs 0, **incarnation 1/2 vs
0** (the bellwether fires — score 3 on `christian_mysticism.life-and-doctrines-boehme.106`;
the hinduism Gita cell was in train so isn't a held-out probe).

**Weak spots (all small-n, thinnest concepts):** trinity 0/2 (both abstract
apophatic Dionysius/Julian passages; base fires, v5 misses), talisman_magic 0/2
(nobody fires — likely marginal in those specific chunks), spirit_conjuration 0/1
(v5 misses the one iamblichus cell v4 got; thinnest concept, 2 train older rows).
Matches the plan's risk note: lean candidate recall on the thin trio, not a review
error. A small 27B top-up on trinity/talisman_magic/spirit_conjuration older cells
would close these if wanted.

## Guards — no v2-style contamination

- **psychic_attack SILENT on all 6 kalevala chunks** (0/6, all models) and v5
  correctly routes the runo-magic to `word_power_incantation` (fires 2–3). No
  false-friend leak.
- **occult_police CLEAN (0)** everywhere for all models — hallucination guard holds.

## Bottom line

v5 is the intended model: disciplined like v4, more accurate than v4 on held-out
tagging (F1 +16% rel, fewer hallucinations), and — the point of the whole campaign
— it **backfills the cross-tradition concepts v4 could not** (19/32 vs 3/32 on
held-out cells), with the guards intact. Ready to serve for the cheap full-corpus
backfill (parallel 4B tagging → `/guru-review-tags` queue, owner apply gate). The
27B only ever touched the sample.

Artifacts: `out/qwen3-4b-guru-v5-r32/` (adapter/merged/gguf); eval
`runs/bench/qwen3-4b-v5-2026-09-07T19-40-59Z/` (report.txt, probe_report.txt,
cells.csv, per-model probe jsonl).
