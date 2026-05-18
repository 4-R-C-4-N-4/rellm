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

A distilled chunk→concept tagger for the [guru](https://github.com/4-R-C-4-N-4) comparative-religion pipeline. Fine-tuned from [Qwen2.5-7B-Instruct](https://huggingface.co/unsloth/Qwen2.5-7B-Instruct-bnb-4bit) on 2,188 (passage, tag-set) pairs labeled by a larger 27B teacher, this model scores passages from mystical texts against a curated taxonomy of comparative-religion concepts.

Training pipeline: [github.com/4-R-C-4-N-4/rellm](https://github.com/4-R-C-4-N-4/rellm)

## What it does

Given a passage of mystical text and a list of candidate concepts (each with an ID and a one-sentence definition), the model returns a JSON array rating every present concept on a 0–3 scale:

- **0** — not present
- **1** — peripherally present
- **2** — clearly present
- **3** — central theme

Concepts scoring 0 are omitted. The output is strict JSON — no markdown, no prose. The prompt contract matches the production caller in guru exactly, so this model is a drop-in replacement for the teacher in the tagging step.

## Why it exists

The guru pipeline indexes a multi-tradition corpus of mystical texts by tagging each passage against a working taxonomy of ~80 (and growing) comparative-religion concepts (e.g. `theosis`, `paradox_as_teaching`, `divine_marriage`, `archons`). Two upstream options had problems:

- **The 27B teacher** produces high-quality labels but is too slow to re-tag the full corpus on every taxonomy revision.
- **The off-the-shelf 7B base model** is fast enough but is unreliable: it under-tags (recall 0.21), invents out-of-taxonomy IDs, and misjudges severity.

This model closes most of that gap at the 7B compute budget.

## Evaluation

Held-out test split from the same data distribution. `base` = Qwen2.5-7B-Instruct (no fine-tuning), `student` = this model. Both queried at temperature 0 with identical system + user prompts via llama-server.

### vs teacher labels (103 chunks, 61 concepts)

| Model   | Precision | Recall |    F1 | Macro-F1 |  MAE | Out-of-tax IDs |
|---------|----------:|-------:|------:|---------:|-----:|---------------:|
| base    |     0.353 |  0.230 | 0.279 |    0.253 | 0.49 |              2 |
| student |     0.607 |  0.651 | **0.629** | **0.548** | 0.40 |              0 |

### vs human-graded labels (360 chunks)

| Model   | Precision | Recall |    F1 | Macro-F1 |  MAE | Out-of-tax IDs |
|---------|----------:|-------:|------:|---------:|-----:|---------------:|
| base    |     0.414 |  0.213 | 0.281 |    0.234 | 0.52 |             14 |
| student |     0.667 |  0.611 | **0.638** | **0.508** | 0.37 |              3 |

Both evals show the same shape: the student more than doubles F1 over the base, with the biggest gains in recall. Notably, F1 against human-graded labels (0.638) is slightly *higher* than against the teacher (0.629), suggesting the student isn't just memorizing teacher idiosyncrasies — it generalizes to the underlying judgment task.

Parse rate is 100% for both models on these splits (strict JSON). Latency at greedy decoding on a single 24GB GPU: base ≈ 3.0 s/chunk, student ≈ 4.2 s/chunk (the student emits more tags per chunk, so per-token cost is similar).

## Training

- **Base:** `unsloth/Qwen2.5-7B-Instruct-bnb-4bit`
- **Method:** Supervised fine-tuning (TRL `SFTTrainer`) with QLoRA via [Unsloth](https://github.com/unslothai/unsloth)
- **LoRA:** r=32, α=64, dropout=0, applied to all attention + MLP projections (`q,k,v,o,gate,up,down`)
- **Schedule:** 3 epochs, batch 2 × grad-accum 8 (effective 16), AdamW-8bit, lr 2e-4, cosine, warmup 0.03
- **Sequence length:** 4096, chat template `qwen-2.5`
- **Hardware:** single 24 GB GPU
- **Seed:** 42

### Training data

Source: `staged_tags` table of a guru.db snapshot, filtered to rows produced by teacher `Qwen3.5-27B-UD-Q4_K_XL.gguf` with prompt version `v1`, status ∈ {pending, accepted}.

- **2,188 chunks** across **61 concepts**
- Splits: **1,979 train / 106 val / 103 test** (90/5/5, stratified by chunk)
- Tradition mix (largest → smallest): neoplatonism (648), egyptian (384), taoism (272), greek_mystery (195), western_esoteric (145), zoroastrianism (129), gnosticism (108), christian_mysticism (104), renaissance_hermeticism (93), hermeticism (55), jewish_mysticism (40), mesopotamian (15)

## Files in this repo

- `adapter/` — LoRA adapter (~100 MB). Load on top of the base model; this is the canonical, reproducible artifact.
- `merged/` — adapter merged into base weights, FP16 (~15 GB). For direct `from_pretrained`.
- `gguf/` — quantized for `llama.cpp` / Ollama / llama-server.
  - `qwen2.5-7b-rellm-F16.gguf` — full-precision conversion
  - `qwen2.5-7b-rellm-Q4_K_M.gguf` — 4-bit, ~4.5 GB, recommended for local inference

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

## Limitations

- **Domain-locked.** Trained on mystical traditions such as Neoplatonism, Hermeticism, Gnosticism, Christian mysticism, Egyptian, Mesopotamian, Zoroastrian, and Taoist sources. The Buddhist and Hindu corpora were excluded from this training run; expect weaker calibration there.
- **Taxonomy-bound.** Scoring is conditioned on the concept list passed in the prompt. The model will faithfully ignore concepts not given to it; if you change the taxonomy meaningfully, retrain.
- **Imbalanced concepts.** A handful of low-frequency concepts (`archons`, `kenoma`, `pleroma`, `self_examination`) have F1 ≈ 0 against human labels — too few teacher positives to learn a reliable boundary. Filter or boost these in downstream review.
- **Latency.** Greedy decoding at ~4 s/chunk on a single 24 GB GPU is fine for batch corpus tagging but not for interactive use. Use the Q4_K_M GGUF for faster local inference.
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
