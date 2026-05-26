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

A distilled chunk→concept tagger for the [guru](https://github.com/4-R-C-4-N-4) comparative-religion pipeline. Fine-tuned from [Qwen2.5-7B-Instruct](https://huggingface.co/unsloth/Qwen2.5-7B-Instruct-bnb-4bit) on 2,808 (passage, tag-set) pairs — labels from a larger 27B teacher, refined by human review — this model scores passages from mystical texts against a curated taxonomy of comparative-religion concepts.

**Current version: v3** — see [Versions](#versions) for v1 and v2.

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
- **The off-the-shelf 7B base model** is fast enough but is unreliable: it under-tags (recall 0.12 vs human labels on the held-out test), invents out-of-taxonomy IDs (9 in 130 chunks), and misjudges severity.

This model closes most of that gap at the 7B compute budget.

## Evaluation (v3)

Held-out test split from the same data distribution, scored against both the 27B teacher's labels and independent human accept/reject verdicts. `base` = Qwen2.5-7B-Instruct (no fine-tuning). All models queried at temperature 0 with identical prompts via llama-server, on the identical held-out chunks.

### vs human-graded labels (held-out test, 118 chunks / 763 graded cells)

Strongest signal — human verdicts are an independent ground truth.

| Model | Precision | Recall |   F1  | Specificity |
|-------|----------:|-------:|------:|------------:|
| base  |     0.833 |  0.118 | 0.207 |       0.953 |
| v1    |     0.673 |  0.356 | 0.466 |       0.655 |
| v2    |     0.759 |  0.415 | 0.537 |       0.737 |
| **v3** | **0.769** | **0.524** | **0.623** | 0.686 |
| 27B teacher (reference) | 0.666 | 1.000 | 0.799 | 0.000 |

v3 beats every prior version on F1 and recall, and **its precision (0.769) clears the 27B teacher's (0.666)** — the student now rejects teacher mistakes rather than just mimicking. (The teacher's recall is 1.0 by construction — humans only reviewed tags it emitted — so its precision is the comparable number.)

### vs teacher labels (130 chunks, 88 concepts)

| Model | Precision | Recall |   F1  | Macro-F1 |  MAE | Parse rate | OOT-IDs | Lat (s) |
|-------|----------:|-------:|------:|---------:|-----:|-----------:|--------:|--------:|
| base  |     0.398 |  0.152 | 0.220 |    0.176 | 0.53 |      96.2% |       9 |    3.97 |
| v1    |     0.621 |  0.509 | 0.560 |    0.386 | 0.37 |     100.0% |       2 |    4.94 |
| v2    |     0.669 |  0.518 | 0.584 |    0.502 | 0.42 |      99.2% |       2 |    4.75 |
| **v3** | 0.636 | **0.585** | **0.609** | **0.522** | 0.42 | 96.9% | **0** | 5.83 |

### Where v3 moves the needle vs v2

v3's gain is **recall without a precision cost**: against human truth, recall 0.415 → 0.524 (+0.109) while precision held (0.759 → 0.769). It came purely from data — identical hyperparameters, but labels now 48% human-verified with ~6,000 more human-accepted positives. Concepts v2 was blind to or had lost recover (`archons` 0 → 0.667, `living_god` +0.166, `body_as_obstacle` +0.154), and v3 invents zero out-of-taxonomy IDs (v2: 2). The cost is small: parse rate dips to 96.9% and latency rises to ~5.8 s/chunk, both because v3 emits more tags.

Full v2↔v3 comparison: [`docs/v2-vs-v3-comparison.md`](https://github.com/4-R-C-4-N-4/rellm/blob/main/docs/v2-vs-v3-comparison.md). Earlier v1↔v2: [`docs/v1-vs-v2-comparison.md`](https://github.com/4-R-C-4-N-4/rellm/blob/main/docs/v1-vs-v2-comparison.md).

## Training (v3)

- **Base:** `unsloth/Qwen2.5-7B-Instruct-bnb-4bit`
- **Method:** Supervised fine-tuning (TRL `SFTTrainer`) with QLoRA via [Unsloth](https://github.com/unslothai/unsloth)
- **LoRA:** r=32, α=64, dropout=0, applied to all attention + MLP projections (`q,k,v,o,gate,up,down`)
- **Schedule:** 3 epochs, batch 1 × grad-accum 16 (effective 16), paged AdamW-8bit, lr 1.5e-4, cosine, warmup 0.03 — *identical to v2, so the v2→v3 gain isolates the data effect*
- **Sequence length:** 5632 (88-concept prompts run median ~5170 tokens; 5632 is the largest context that fits backward on a 24 GB 3090)
- **Chat template:** `qwen-2.5`
- **Checkpoint:** best-by-val-loss (eval_loss 0.2912)
- **Hardware:** single 24 GB GPU (NVIDIA RTX 3090)
- **Wall-clock:** 14h 50m
- **Seed:** 42

### Training data (v3)

Source: `staged_tags` table of a guru.db snapshot taken after a human-review push, filtered to rows produced by teacher `Qwen3.5-27B-UD-Q4_K_XL.gguf` with prompt version `v1`, status ∈ {pending, accepted} — so human-**rejected** tags are excluded.

- **2,808 chunks** across **88 concepts** (in-export)
- **25,559 target tags: 48% human-accepted** (12,187), the rest unreviewed teacher labels, zero human-rejected. This is the key change from v2, whose targets were almost entirely unreviewed.
- Splits: **2,538 train / 134 val / 136 test** (90/5/5, deterministic chunk_id hash — preserves the v2 held-out set for apples-to-apples eval)
- 457 train+val chunks (17%) dropped during training because their tokenized length exceeded `max_seq_length=5632`; net **2,102 training examples**. The denser human-accepted labels make more examples exceed the 3090's context ceiling — fully exploiting the new signal wants a larger GPU.
- The v2→v3 lever was **recall and label quality**, not precision cleanup: ~6,000 more human-accepted positives (added to existing chunks + 210 newly-tagged chunks) lifted held-out recall against human truth by +0.109 with no precision loss.

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

All three versions re-scored on the same held-out test split with the same harness, so the columns are directly comparable (numbers differ slightly from each version's original card, which used the taxonomy and labels current at its release).

| Tag | Date | F1 vs teacher | Macro-F1 | F1 vs human | Recall vs human | Training data |
|-----|------|--------------:|---------:|------------:|----------------:|---------------|
| v1  | 2026-05-13 | 0.560 | 0.386 | 0.466 | 0.356 | 2,188 chunks, 61 concepts |
| v2  | 2026-05-22 | 0.584 | 0.502 | 0.537 | 0.415 | 2,598 chunks, 88 concepts |
| **v3** | 2026-05-26 | **0.609** | **0.522** | **0.623** | **0.524** | 2,808 chunks, 88 concepts |

Pin a specific version with `revision="v1"`, `revision="v2"`, or `revision="v3"` when downloading.

### v1 / v2 (historical)

**v1** (2026-05-13) was trained on the 61-concept taxonomy snapshot (2,188 SFT examples). **v2** (2026-05-22) expanded to the 88-concept taxonomy and ~2,600 chunks, lifting macro-F1 from broader concept coverage; its targets were almost entirely *unreviewed* teacher labels. **v3** keeps v2's taxonomy and hyperparameters but trains on human-reviewed labels (48% accepted, rejected dropped), which is what lifted recall.

Both are preserved at the `v1` and `v2` git tags on the HF and GitHub repos. Use them to reproduce earlier results exactly; otherwise prefer v3.

## Limitations

- **Occasional over-generation (parse rate 96.9%).** On ~3% of chunks v3 keeps emitting tag objects until it hits the token cap and truncates into invalid JSON. It's the flip side of v3's higher recall (it emits more), is non-deterministic even at temperature 0, and is *not* fixed by raising `max_tokens`. Handle downstream with a truncation-salvage parser or a retry on parse failure. (v2 parsed at 99.2%.)
- **Domain-locked.** v3 broadened human-reviewed coverage across mid-frequency traditions (christian_mysticism, greek_mystery, taoism gained most), but the corpus is still heavily Mediterranean / Greek-philosophical at the long tail. Calibration on East-Asian, South-Asian, and indigenous traditions remains weak.
- **Taxonomy-bound.** Scoring is conditioned on the concept list passed in the prompt. The model will faithfully ignore concepts not given to it; if you change the taxonomy meaningfully, retrain.
- **Imbalanced concepts.** A few low-frequency concepts still have weak boundaries — too few teacher positives. v3 regressed slightly vs v2 on `evil_as_privation` (0.42 → 0.24) and `hidden_sayings` (0.67 → 0.56); filter or boost these in downstream review. (v3 *recovered* several that earlier versions missed, e.g. `archons` 0 → 0.67, `living_god` +0.17.)
- **Capacity-capped recall.** v3's denser labels push 17% of training examples past the 24 GB 3090's 5632-token ceiling, where they're dropped. Recall (0.524 vs human truth) is good but not teacher-level; closing the rest likely needs a larger GPU training at >5632 ctx, not more data.
- **Latency.** Greedy decoding at ~5.8 s/chunk on a single 24 GB GPU (up from v2's 4.7, since v3 emits more) is fine for batch corpus tagging but not interactive use. Use the Q4_K_M GGUF for faster local inference.
- **Not a chat model.** This is a tagging specialist. Don't expect general assistant behavior — it was tuned on a single task and prompt format.

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
