---
base_model: unsloth/Qwen3-4B-Instruct-2507-bnb-4bit
library_name: transformers
license: apache-2.0
language:
- en
pipeline_tag: text-generation
tags:
- sft
- lora
- qlora
- unsloth
- trl
- comparative-religion
- text-classification
- concept-tagging
---

# qwen-3-4b-guru

A fast chunk→concept tagger for the [guru](https://github.com/4-R-C-4-N-4) comparative-religion indexing pipeline. Fine-tuned from [Qwen3-4B-Instruct-2507](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507) on (passage, tag-set) pairs — teacher labels from a 27B model, refined by human review — this model scores passages from mystical texts against guru's concept taxonomy.

**v5 (current).** Trains natively on the full, live **154-concept** taxonomy at **16,384** context. Its purpose is **cross-tradition backfill**: the taxonomy grew by 44 concepts after v3, and older works — tagged before those concepts existed — needed the new vocabulary applied where it genuinely fits (e.g. `incarnation` on a Hindu avatāra passage, `divine_immanence` on Neoplatonic and Taoist text). v4 (internal-only, never published — like v2) learned the new concepts only in their modern Western-esoteric flavour because it had **zero** cross-tradition training examples of them; v5 fixes this by folding in a reviewed 27B sample-pass over older traditions, so the applied cross-tradition tags become training positives. The v5 export is **applied-tags-only** (owner-accepted labels, deduped one tag per (chunk, concept)). Result: v5 beats v4 on held-out tagging **and** recovers the backfill v4 could not — see [Evaluation](#evaluation). v1/v3 were published under the `qwen-3-4b-guru-v1` / `-v3` tags; v2 and v4 were internal-only. This release met no formal ship gates (none were set); see [Limitations](#limitations) for exactly what was and wasn't measured.

## What it does

Given a passage and a list of candidate concepts (each `{id, definition}`), the model returns a JSON array rating every present concept 0–3 (0=absent … 3=central theme); concepts scoring 0 are omitted. Output is strict JSON, no prose. The prompt contract matches the guru tagging caller exactly.

## Evaluation

### v5 benchmark: base vs v4 vs v5

Head-to-head on v5's held-out test split (223 chunks), all models given the full live 154-concept taxonomy in every prompt, graded against the owner-accepted (vetted) labels. Temperature 0 via llama-server, identical prompts.

**vs accepted labels:**

| model | precision | recall | F1 | macro-F1 | MAE | tags/chunk | OOT-IDs |
|---|---:|---:|---:|---:|---:|---:|---:|
| base | 0.120 | 0.503 | 0.194 | 0.134 | 0.51 | 44.7 | 31 |
| v4 | 0.236 | 0.480 | 0.316 | 0.243 | 0.40 | 11.3 | 5 |
| **v5** | **0.279** | **0.537** | **0.367** | **0.274** | **0.31** | 10.7 | 4 |

v5 improves on v4 across every axis — precision, recall, F1 (+16% relative), lower error, fewer invented IDs — while staying disciplined (base's higher raw recall is a "shotgun" artifact: 44.7 tags/chunk at precision 0.12).

**Backfill probe (the point of v5).** On 32 held-out older-tradition cells where one of the 12 backfill concepts is a vetted positive on a chunk the model never trained on, v5 surfaces the target at score ≥2 on **19/32** cells versus v4's **3/32** — recovering the cross-tradition capability v4 lacked, with discipline intact. Guards held: `psychic_attack` stayed silent on Kalevala runo-magic (routed to `word_power_incantation`), `occult_police` fired nowhere. Weak spots are the thinnest concepts (trinity, talisman_magic, spirit_conjuration), where too few older chunks were surfaced in the sample-pass. Full detail: [v5 findings](https://github.com/4-R-C-4-N-4/rellm/blob/main/docs/qwen-3-4b-guru-v5-findings.md).

### v3 benchmark: base vs v1 vs v2 vs v3

Head-to-head on v3's own held-out test split (181 chunks), all four models given the full live 110-concept taxonomy in every prompt (this is the capability delta v3 is meant to fix, so v1/v2 see it here for the first time — v1/v2 trained on the pinned 88-concept fallback). Verified zero train/test leakage across all three fine-tunes under the chunk-hash split. All models at temperature 0 via llama-server, identical prompts.

**vs teacher labels:**

| model | precision | recall | F1 | macro-F1 | OOT-IDs | parse | latency |
|---|---:|---:|---:|---:|---:|---:|---:|
| base | 0.291 | 0.515 | 0.372 | 0.264 | 15 | 100% | 17.9s |
| v1 | 0.407 | 0.534 | 0.462 | 0.317 | 8 | 100% | 7.7s |
| v2 | 0.390 | 0.514 | 0.443 | 0.315 | 1 | 100% | 11.0s |
| **v3** | **0.439** | **0.545** | **0.486** | **0.331** | 2 | 100% | 9.3s |

**vs human-graded labels:** base 0.594 F1 (inflated — a "shotgun" over-emission artifact, base emits 36.3 tags/chunk vs v3's 14.2, landing extra hits on ungraded cells for free), v1 0.537, v2 0.577, **v3 0.589** — v3 wins among the models with comparable emission counts. v1's worst blind spot, `animism` (F1 0.000 at n=36), is fixed in v3.

v3 is a genuine, measured improvement over both predecessors on every capability-normalized metric — the taxonomy-loader fix, corpus quarantine, and full-context native training all paid off.

### v1 original evaluation (historical, not comparable to the table above — different test split, different corpus snapshot, 88-concept taxonomy)

Held-out test split (293 chunks the model never trained on), scored against both the 27B teacher's labels and independent human accept/reject verdicts.

| Model | Precision | Recall | F1 | Specificity |
|-------|----------:|-------:|------:|------------:|
| base  | 0.682 | 0.550 | 0.609 | 0.590 |
| qwen-3-4b-guru-v1 | 0.710 | 0.571 | 0.633 | 0.626 |
| 27B teacher (reference) | 0.616 | 1.000\* | 0.762\* | 0.000 |

\* The teacher's recall is 1.0 by construction — humans only reviewed tags the teacher emitted — so its precision (0.616) is the comparable number.

## Training

- **Base:** `unsloth/Qwen3-4B-Instruct-2507-bnb-4bit`
- **Method:** QLoRA (TRL `SFTTrainer` via [Unsloth](https://github.com/unslothai/unsloth))
- **LoRA:** r=32, α=64, dropout 0, all attention + MLP projections
- **Schedule:** 3 epochs, batch 1 × grad-accum 16, paged AdamW-8bit, lr 1.5e-4 cosine, warmup 0.03
- **Sequence length:** 16,384 (the 154-concept definitions block alone is ~11,439 tokens; 16,384 covers the full observed example-length range with zero examples dropped, and trains at 12.8 GB peak on a single 24 GB 3090 with flash-attn 2.8.3)
- **Chat template:** Qwen3 ChatML (`qwen3-instruct`)
- **Checkpoint:** best-by-val-loss, final step 753 (eval_loss 0.1788, improved monotonically through training — no overfit)
- **Hardware:** single RTX 3090 (24 GB), ~29.4 h
- **Seed:** 42

### Training data

Source: `staged_tags` from a guru.db snapshot, **applied-tags-only** — owner-accepted (vetted) labels, deduped to one tag per (chunk, concept). Teacher signatures are 27B (`Qwen3.5`/`Qwen3.8`, an unreliable free-text label — the export takes every non-student, non-Carnice teacher tag rather than allowlisting a signature).

- **4,440 examples / 25,402 tags**, **154 concepts** (the full live guru taxonomy — domain → family → concept, three tiers)
- Splits by chunk_id: 4,008 train / 209 val / 223 test
- Includes the reviewed cross-tradition backfill positives for the 12 drift concepts (trinity, stellar_determinism, divine_immanence, initiation, divination, esoteric_lineage, exorcism, gender, spirit_conjuration, incarnation, qliphoth, talisman_magic)

The taxonomy this model expects is pinned in `taxonomy.toml` in this repo, matching guru's live taxonomy at training time.

## Files

- `adapter/` — LoRA adapter (~260 MB); the canonical artifact
- `merged/` — adapter merged into base, FP16 (~8 GB)
- `gguf/qwen-3-4b-guru-v5-Q4_K_M.gguf` — 4-bit, recommended for serving (also aliased as `qwen-3-4b-guru-Q4_K_M.gguf`)
- `gguf/qwen-3-4b-guru-v5-F16.gguf` — full-precision conversion
- `taxonomy.toml` — the 154-concept taxonomy (prompt contract)
- Prior-version gguf (`-v3-`) are retained in `gguf/`.

## Usage

```bash
llama-server -m qwen-3-4b-guru-v5-Q4_K_M.gguf --jinja --port 8080
```

The guru tagging caller hits the OpenAI-compatible `/v1/chat/completions` endpoint. The model expects the exact prompt structure used at training time (system role + passage + 0–3 rubric + JSON concept list); deviating degrades quality.

## Limitations

- **Exploratory release.** No formal throughput benchmark and no quantization sweep were run; only Q4_K_M is provided and serving throughput at concurrency is unmeasured. Treat the eval as a sound point estimate, not a gated guarantee.
- **Domain-locked.** The corpus is heavily Mediterranean / Greek-philosophical; calibration on East-Asian, South-Asian, and indigenous traditions is weaker.
- **Taxonomy-bound.** Scoring is conditioned on the concept list in the prompt. Use the pinned `taxonomy.toml`; if guru's live taxonomy drifts meaningfully from this snapshot, retrain.
- **Thin cross-tradition concepts.** The backfill recovers most drift concepts on older traditions, but the thinnest (trinity, talisman_magic, spirit_conjuration) had too few older chunks surfaced in the 27B sample-pass and are under-tagged on held-out cells; a larger sample-pass would close them.
- **Label provenance.** v5 trains on owner-accepted labels only (a shift from prior versions, which included unreviewed teacher tags). Accepted labels are vetted but the teacher's tendencies still shape which tags were proposed for review in the first place.
- **Not a chat model.** Tuned on a single task and prompt format.

## License

Apache 2.0
