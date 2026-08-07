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

**v3 (current).** Trains natively on the full, live 110-concept taxonomy at 9,472 context (v1/v2 were stuck on a pinned 88-concept fallback by a taxonomy-loader bug and an unset flash-attn dependency, both fixed for this release). The training corpus also went through four rounds of quarantine review that corrected ~2,600 cross-tradition "false friend" tags a prior root-cause investigation traced from v2's regression. v1 was published under the `qwen-3-4b-guru-v1` tag; v2 was an internal-only retrain that regressed and was never published (see [Evaluation](#evaluation) and the [regression autopsy](https://github.com/4-R-C-4-N-4/rellm/blob/main/docs/qwen-3-4b-v2-regression-autopsy.md) for why). This release met no formal ship gates (none were set); see [Limitations](#limitations) for exactly what was and wasn't measured.

## What it does

Given a passage and a list of candidate concepts (each `{id, definition}`), the model returns a JSON array rating every present concept 0–3 (0=absent … 3=central theme); concepts scoring 0 are omitted. Output is strict JSON, no prose. The prompt contract matches the guru tagging caller exactly.

## Evaluation

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
- **Sequence length:** 9,472 (v1/v2 were capped at 6,144 by an OOM ceiling later root-caused to flash-attn silently never being installed — the fallback Xformers path is far less memory-efficient at long context. With flash-attn 2.8.3.post1 compiled from source, 9,472 trains cleanly on a single 24 GB 3090. The richer 110-concept definitions block alone runs ~5,939 tokens; 9,472 covers the full observed example-length range, 6,273–9,294 tokens, with zero examples dropped)
- **Chat template:** Qwen3 ChatML (`qwen3-instruct`)
- **Checkpoint:** best-by-val-loss, final step 594 (eval_loss 0.2701, improved monotonically through training)
- **Hardware:** single RTX 3090 (24 GB); resumed once from checkpoint-300 after an external interruption at step 370
- **Seed:** 42

### Training data

Source: `staged_tags` from a guru.db snapshot, post-quarantine (four review batches correcting ~2,600 cross-tradition false-friend / blanket-tagged / lexically-keyed tags — see the [regression autopsy](https://github.com/4-R-C-4-N-4/rellm/blob/main/docs/qwen-3-4b-v2-regression-autopsy.md)), teacher `Qwen3.5-27B-UD-Q4_K_XL.gguf`.

- **3,504 examples**, **110 concepts** (the full live guru taxonomy — domain → family → concept, three tiers)
- Splits by chunk_id: 3,161 train / 162 val / 181 test

The taxonomy this model expects is pinned in `taxonomy.toml` in this repo, matching guru's live taxonomy at training time.

## Files

- `adapter/` — LoRA adapter (~260 MB); the canonical artifact
- `merged/` — adapter merged into base, FP16 (~8 GB)
- `gguf/qwen-3-4b-guru-v3-Q4_K_M.gguf` — 4-bit, recommended for serving
- `gguf/qwen-3-4b-guru-v3-F16.gguf` — full-precision conversion
- `taxonomy.toml` — the 110-concept taxonomy (prompt contract)

## Usage

```bash
llama-server -m qwen-3-4b-guru-v3-Q4_K_M.gguf --jinja --port 8080
```

The guru tagging caller hits the OpenAI-compatible `/v1/chat/completions` endpoint. The model expects the exact prompt structure used at training time (system role + passage + 0–3 rubric + JSON concept list); deviating degrades quality.

## Limitations

- **Exploratory release.** No formal throughput benchmark and no quantization sweep were run; only Q4_K_M is provided and serving throughput at concurrency is unmeasured. Treat the eval as a sound point estimate, not a gated guarantee.
- **Domain-locked.** The corpus is heavily Mediterranean / Greek-philosophical; calibration on East-Asian, South-Asian, and indigenous traditions is weaker.
- **Taxonomy-bound.** Scoring is conditioned on the concept list in the prompt. Use the pinned `taxonomy.toml`; if guru's live taxonomy drifts meaningfully from this snapshot, retrain.
- **Label noise.** A portion of training targets are unreviewed teacher labels, so the model inherits some of the teacher's tagging tendencies on un-reviewed concepts. Quarantine review corrected the worst systematic contamination (cross-tradition false friends) but was not an exhaustive per-tag re-review.
- **Not a chat model.** Tuned on a single task and prompt format.

## License

Apache 2.0
