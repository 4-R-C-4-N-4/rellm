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

A fast chunk→concept tagger for the [guru](https://github.com/4-R-C-4-N-4) comparative-religion indexing pipeline. Fine-tuned from [Qwen3-4B-Instruct-2507](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507) on 2,808 (passage, tag-set) pairs — teacher labels from a 27B model, refined by human review — this model scores passages from mystical texts against a curated 88-concept taxonomy.

**Exploratory v1.** This release was built to test Qwen3-4B as a faster replacement for the bulk-tagging step. It met no formal ship gates (none were set); see [Evaluation](#evaluation) and [Limitations](#limitations) for exactly what was and wasn't measured.

## What it does

Given a passage and a list of candidate concepts (each `{id, definition}`), the model returns a JSON array rating every present concept 0–3 (0=absent … 3=central theme); concepts scoring 0 are omitted. Output is strict JSON, no prose. The prompt contract matches the guru tagging caller exactly.

## Evaluation

Held-out test split (293 chunks the model never trained on), scored against both the 27B teacher's labels and independent human accept/reject verdicts. `base` = Qwen3-4B-Instruct-2507 with no fine-tuning. Both at temperature 0 via llama-server, identical prompts.

### vs human-graded labels (1,990 graded cells)

Strongest signal — human verdicts are an independent ground truth.

| Model | Precision | Recall | F1 | Specificity |
|-------|----------:|-------:|------:|------------:|
| base  | 0.682 | 0.550 | 0.609 | 0.590 |
| **qwen-3-4b-guru** | **0.710** | **0.571** | **0.633** | **0.626** |
| 27B teacher (reference) | 0.616 | 1.000\* | 0.762\* | 0.000 |

\* The teacher's recall is 1.0 by construction — humans only reviewed tags the teacher emitted — so its **precision (0.616)** is the comparable number. This model's precision (0.710) clears it.

### vs teacher labels

| Model | Precision | Recall | F1 | Macro-F1 | Parse rate | OOT-IDs | tags/chunk | Lat (s) |
|-------|----------:|-------:|------:|---------:|-----------:|--------:|-----------:|--------:|
| base  | 0.345 | 0.561 | 0.427 | 0.293 | 94.9% | 18 | 27.6 | 13.9 |
| **qwen-3-4b-guru** | 0.557 | 0.614 | **0.584** | **0.432** | **99.7%** | **1** | 12.5 | **5.3** |

The fine-tune's main effect is **calibration, reliability, and speed**: the base model massively over-tags (27.6 concepts/chunk, 18 invented IDs, 94.9% parse, 13.9 s) while this model is disciplined (12.5 concepts/chunk, 1 invented ID, **99.7% parse, 5.3 s** — ~2.6× faster). It modestly improves on the base against human truth too (F1 0.609 → 0.633).

## Training

- **Base:** `unsloth/Qwen3-4B-Instruct-2507-bnb-4bit`
- **Method:** QLoRA (TRL `SFTTrainer` via [Unsloth](https://github.com/unslothai/unsloth))
- **LoRA:** r=32, α=64, dropout 0, all attention + MLP projections
- **Schedule:** 3 epochs, batch 1 × grad-accum 16, paged AdamW-8bit, lr 1.5e-4 cosine, warmup 0.03
- **Sequence length:** 6144 (8192 OOM'd on a 24 GB 3090 — the loss logits are `seq_len × 151,936 vocab`; 6144 fits and drops only ~5% of examples)
- **Chat template:** Qwen3 ChatML (`qwen3-instruct`)
- **Checkpoint:** best-by-val-loss (eval_loss 0.3421)
- **Hardware / wall-clock:** single RTX 3090 / ~18 h
- **Seed:** 42

### Training data

Source: `staged_tags` from a guru.db snapshot, teacher `Qwen3.5-27B-UD-Q4_K_XL.gguf`, prompt version `v1`, status ∈ {pending, accepted} (human-**rejected** tags dropped).

- **2,808 chunks**, **88 concepts**, 25,893 target tags (**47% human-accepted**, rest unreviewed teacher labels, 0 rejected)
- Splits 80/10/10 by chunk_id (2,245 / 270 / 293); 111 train chunks (4.9%) dropped for exceeding 6144 tokens

The 88-concept taxonomy this model expects is pinned in `taxonomy.toml` in this repo. (The upstream guru taxonomy has since migrated to a three-tier hierarchy; this model's contract is the flat 88-concept version it trained on.)

## Files

- `adapter/` — LoRA adapter (~260 MB); the canonical artifact
- `merged/` — adapter merged into base, FP16 (~8 GB)
- `gguf/qwen-3-4b-guru-Q4_K_M.gguf` — 4-bit, ~2.5 GB, recommended for serving
- `gguf/qwen-3-4b-guru-F16.gguf` — full-precision conversion
- `taxonomy.toml` — the 88-concept taxonomy (prompt contract)

## Usage

```bash
llama-server -m qwen-3-4b-guru-Q4_K_M.gguf --jinja --port 8080
```

The guru tagging caller hits the OpenAI-compatible `/v1/chat/completions` endpoint. The model expects the exact prompt structure used at training time (system role + passage + 0–3 rubric + JSON concept list); deviating degrades quality.

## Limitations

- **Exploratory release.** No formal throughput benchmark and no quantization sweep were run; only Q4_K_M is provided and serving throughput at concurrency is unmeasured. Treat the eval as a sound point estimate, not a gated guarantee.
- **Domain-locked.** The corpus is heavily Mediterranean / Greek-philosophical; calibration on East-Asian, South-Asian, and indigenous traditions is weaker.
- **Taxonomy-bound.** Scoring is conditioned on the 88-concept list in the prompt. Use the pinned `taxonomy.toml`; if you change the taxonomy meaningfully, retrain.
- **Label noise.** ~53% of training targets are unreviewed teacher labels, so the model inherits some of the teacher's tagging tendencies on un-reviewed concepts.
- **Not a chat model.** Tuned on a single task and prompt format.

## License

Apache 2.0
