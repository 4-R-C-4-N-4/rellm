---
base_model: unsloth/Qwen2.5-7B-Instruct-bnb-4bit
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

# qwen2.5-7b-rellm

A distilled chunk→concept tagger for the [guru](https://github.com/4-R-C-4-N-4) comparative-religion pipeline. Fine-tuned from [Qwen2.5-7B-Instruct](https://huggingface.co/unsloth/Qwen2.5-7B-Instruct-bnb-4bit) on 2,598 (passage, tag-set) pairs labeled by a larger 27B teacher, this model scores passages from mystical texts against a curated taxonomy of comparative-religion concepts.

**Current version: v2** — see [Versions](#versions) for v1.

Training pipeline: [github.com/4-R-C-4-N-4/rellm](https://github.com/4-R-C-4-N-4/rellm)

## What it does

Given a passage of mystical text and a list of candidate concepts (each with an ID and a one-sentence definition), the model returns a JSON array rating every present concept on a 0–3 scale:

- **0** — not present
- **1** — peripherally present
- **2** — clearly present
- **3** — central theme

Concepts scoring 0 are omitted. The output is strict JSON — no markdown, no prose. The prompt contract matches the production caller in guru exactly, so this model is a drop-in replacement for the teacher in the tagging step.

## Why it exists

The guru pipeline indexes a multi-tradition corpus of mystical texts by tagging each passage against a working taxonomy of ~88 (and growing) comparative-religion concepts (e.g. `theosis`, `paradox_as_teaching`, `divine_marriage`, `archons`). Two upstream options had problems:

- **The 27B teacher** produces high-quality labels but is too slow to re-tag the full corpus on every taxonomy revision.
- **The off-the-shelf 7B base model** is fast enough but is unreliable: it under-tags (recall 0.16 on v2 eval), invents out-of-taxonomy IDs (9 in 130 chunks), and misjudges severity.

This model closes most of that gap at the 7B compute budget.

## Evaluation (v2)

Held-out test split from the same data distribution. `base` = Qwen2.5-7B-Instruct (no fine-tuning), `v2` = this model. Both queried at temperature 0 with identical system + user prompts via llama-server.

### vs teacher labels (130 chunks, 88 concepts)

| Model | Precision | Recall |   F1  | Macro-F1 |  MAE | Parse rate | OOT-IDs | Lat (s) |
|-------|----------:|-------:|------:|---------:|-----:|-----------:|--------:|--------:|
| base  |     0.328 |  0.162 | 0.217 |    0.182 | 0.53 |      96.2% |       9 |    4.00 |
| v2    | **0.597** | **0.602** | **0.599** | **0.525** | 0.42 | 99.2% |  2 | 4.72 |

### vs human-graded labels (held-out test chunks, 92 chunks)

Strongest signal — humans labels are an independent ground truth.

| Model | Precision | Recall |   F1  | Specificity |
|-------|----------:|-------:|------:|------------:|
| base  |     0.750 |  0.158 | 0.261 |       0.963 |
| v2    | **0.600** | **0.474** | **0.529** | **0.778** |
| 27B teacher (reference) | 0.378 | 1.000 | 0.549 | 0.000 |

v2 at F1=0.529 on test chunks vs human ground truth essentially matches the 27B teacher's own F1 of 0.549 at 7B compute cost — the distillation goal.

### Where v2 moves the needle vs v1

v2's biggest gain over v1 is *uniformity* across the 88-concept taxonomy: macro-F1 0.398 → 0.525 (+0.127), driven by previously-blind concepts (`prayer`, `theurgy`, `detachment_gelassenheit`, `wu_wei`, `evil_as_privation`, etc.) and previously-underrepresented traditions (mesopotamian +0.32, jewish_mysticism +0.20, buddhism +0.19, sufism +0.14). Trade: small regressions on traditions v1 over-specialized in (egyptian −0.06, hermeticism −0.08, western_esoteric −0.03) and on a handful of high-frequency concepts that lose data share under the broader distribution (`living_god` −0.21, `body_as_obstacle` −0.17).

Full v1↔v2 comparison: [`docs/v1-vs-v2-comparison.md`](https://github.com/4-R-C-4-N-4/rellm/blob/main/docs/v1-vs-v2-comparison.md).

## Training (v2)

- **Base:** `unsloth/Qwen2.5-7B-Instruct-bnb-4bit`
- **Method:** Supervised fine-tuning (TRL `SFTTrainer`) with QLoRA via [Unsloth](https://github.com/unslothai/unsloth)
- **LoRA:** r=32, α=64, dropout=0, applied to all attention + MLP projections (`q,k,v,o,gate,up,down`)
- **Schedule:** 3 epochs, batch 1 × grad-accum 16 (effective 16), paged AdamW-8bit, lr 1.5e-4, cosine, warmup 0.03
- **Sequence length:** 5632 (88-concept prompts run median 5137 tokens; 5632 is the largest context that fits backward on a 24 GB 3090)
- **Chat template:** `qwen-2.5`
- **Checkpoint:** best-by-val-loss
- **Hardware:** single 24 GB GPU (NVIDIA RTX 3090)
- **Wall-clock:** 15h 51m
- **Seed:** 42

### Training data (v2)

Source: `staged_tags` table of a guru.db snapshot, filtered to rows produced by teacher `Qwen3.5-27B-UD-Q4_K_XL.gguf` with prompt version `v1`, status ∈ {pending, accepted}.

- **2,598 chunks** across **88 concepts** (in-export)
- Splits: **2,339 train / 129 val / 130 test** (90/5/5, stratified by chunk_id)
- 160 train chunks dropped during training because their tokenized length exceeded `max_seq_length=5632` (right-truncation would cut the assistant JSON response; better to drop)
- Tradition mix (largest → smallest): neoplatonism, egyptian, taoism, greek_mystery, western_esoteric, zoroastrianism, jewish_mysticism, gnosticism, christian_mysticism, renaissance_hermeticism, hermeticism, buddhism, sufism, mesopotamian, platonism (plus a handful of single-chunk traditions). Compared to v1, **buddhism, sufism, and several Hindu lineages now have nonzero training signal.**

## Files in this repo

- `adapter/` — LoRA adapter (~310 MB). Load on top of the base model; this is the canonical, reproducible artifact.
- `merged/` — adapter merged into base weights, FP16 (~15 GB). For direct `from_pretrained`.
- `gguf/` — quantized for `llama.cpp` / Ollama / llama-server.
  - `qwen2.5-7b-rellm-F16.gguf` — full-precision conversion
  - `qwen2.5-7b-rellm-Q4_K_M.gguf` — 4-bit, ~4.4 GB, recommended for local inference

## Usage

### llama.cpp / llama-server (recommended for the guru pipeline)

```bash
llama-server -m qwen2.5-7b-rellm-Q4_K_M.gguf --jinja --port 8080
```

The `--jinja` flag is required so the model's chat template is applied. The guru tagging caller hits the OpenAI-compatible `/v1/chat/completions` endpoint.

### transformers (merged weights)

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

tok = AutoTokenizer.from_pretrained("4rc4n4/qwen2.5-7b-rellm", subfolder="merged")
model = AutoModelForCausalLM.from_pretrained(
    "4rc4n4/qwen2.5-7b-rellm", subfolder="merged", device_map="auto"
)

messages = [
    {"role": "system", "content": "You are a comparative religion scholar..."},  # see prompt below
    {"role": "user", "content": "<passage + concept list>"},
]
prompt = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
out = model.generate(**tok(prompt, return_tensors="pt").to(model.device), max_new_tokens=1024)
print(tok.decode(out[0], skip_special_tokens=True))
```

### LoRA adapter (on top of the base)

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM

base = AutoModelForCausalLM.from_pretrained("unsloth/Qwen2.5-7B-Instruct-bnb-4bit", device_map="auto")
model = PeftModel.from_pretrained(base, "4rc4n4/qwen2.5-7b-rellm", subfolder="adapter")
```

### Prompt contract

The model expects the exact prompt structure used at training time. See `src/rellm/formats.py` in the training repo for the canonical builder; the short version is:

- **System:** `"You are a comparative religion scholar helping to build a concept index of mystical texts. For each passage given, score it against every concept definition provided. Respond ONLY with a valid JSON array (no markdown, no commentary)."`
- **User:** a passage block, the 0–3 scoring rubric, and a JSON list of `{id, definition}` candidate concepts, ending with the output schema and `Return [] if nothing scores >= 1.`

Deviating from this format will degrade quality — the model was trained on a single prompt template.

## Versions

| Tag | Date | F1 (vs teacher, full test) | Macro-F1 | Training data |
|-----|------|---------------------------:|---------:|---------------|
| v1  | 2026-05-13 | 0.577 (re-scored on v2-test) / 0.629 (v1-era) | 0.398 / 0.548 | 2,188 chunks, 61 concepts |
| v2  | 2026-05-22 | **0.599** | **0.525** | 2,598 chunks, 88 concepts |

Pin a specific version with `revision="v1"` or `revision="v2"` when downloading.

### v1 (historical)

The v1 release was trained on the 61-concept taxonomy snapshot from 2026-05-11 (2,188 SFT examples). Its model card reported F1=0.629 / Macro-F1=0.548 against the v1-era teacher labels on 103 test chunks, and F1=0.638 / Macro-F1=0.508 against 360 human-graded chunks. A v2-era sanity rerun against the original v1 snapshot reproduces F1=0.615 (drift due to running against the current 88-concept taxonomy file rather than the v1-era 61-concept one).

v1 is preserved at the `v1` git tag on both the HF repo and the rellm GitHub repo. Use it if you need to reproduce earlier results exactly; otherwise prefer v2.

## Limitations

- **Domain-locked, but broader than v1.** v2 added training signal for buddhism, sufism, jewish_mysticism, and mesopotamian, but the corpus is still heavily Mediterranean / Greek-philosophical at the long tail. Calibration on East-Asian, South-Asian, and indigenous traditions remains weak.
- **Taxonomy-bound.** Scoring is conditioned on the concept list passed in the prompt. The model will faithfully ignore concepts not given to it; if you change the taxonomy meaningfully, retrain.
- **Imbalanced concepts.** A handful of low-frequency concepts (`archons`, `pleroma`, `divine_intoxication`, `demiurge`) still have F1 ≈ 0 — too few teacher positives to learn a reliable boundary. Filter or boost these in downstream review.
- **High-frequency concept drift.** v2 traded some precision on a handful of high-frequency concepts that dominated v1's training mass (`living_god` −0.21, `body_as_obstacle` −0.17, `apophatic_theology` −0.09) for broader coverage. If your downstream use is dominated by those concepts, v1 may still be competitive.
- **Latency.** Greedy decoding at ~4.7 s/chunk on a single 24 GB GPU is fine for batch corpus tagging but not for interactive use. Use the Q4_K_M GGUF for faster local inference.
- **Not a chat model anymore.** This is a tagging specialist. Don't expect general assistant behavior — it was tuned on a single task and prompt format.

## License

Apache 2.0

## Citation

```bibtex
@software{rellm_qwen25_7b,
  author = {4rc4n4},
  title  = {qwen2.5-7b-rellm: a distilled chunk→concept tagger for comparative-religion corpora},
  year   = {2026},
  url    = {https://huggingface.co/4rc4n4/qwen2.5-7b-rellm}
}
```
