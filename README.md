# rellm

Distillation pipeline for the chunk→concept tagger used in the [guru](https://github.com/4-R-C-4-N-4) comparative-religion indexing project. Takes teacher labels (currently `Qwen3.5-27B`) from a `guru.db` snapshot, builds an SFT dataset, fine-tunes a smaller student with QLoRA, and exports adapter + merged + GGUF artifacts for production tagging.

**rellm is the pipeline, not a model.** It produces distilled tagger models, each published to its own 🤗 repo with its own release tags:

- **`qwen2.5-7b-rellm`** — current release **v3** — [huggingface.co/4rc4n4/qwen2.5-7b-rellm](https://huggingface.co/4rc4n4/qwen2.5-7b-rellm)
- **`qwen-3-4b-guru`** — a faster 4B production tagger (in progress; see [`docs/qwen-3-4b-guru-build-spec.md`](docs/qwen-3-4b-guru-build-spec.md))

If you just want a model, go to its repo. This repo is for retraining them — each model's HF target lives in its config's `publish:` block, so adding a model is config, not code.

## Why distill?

The guru pipeline tags every passage in a multi-tradition corpus of mystical texts against a working taxonomy of ~80 comparative-religion concepts. The 27B teacher produces high-quality labels but is too slow to re-tag the full corpus on every taxonomy revision. The 7B base model is fast enough but under-tags badly (recall ~0.21) and invents out-of-taxonomy IDs.

The v1 student lifts F1 from 0.28 → 0.64 against human-graded labels at the same 7B compute budget. See the [model card](https://huggingface.co/4rc4n4/qwen2.5-7b-rellm) for full eval numbers.

## Pipeline

```
guru.db ──► rellm snapshot ──► rellm export ──► rellm splits
                                                    │
                                                    ▼
                                          train/train_distill.py
                                                    │
                                            ┌───────┴───────┐
                                            ▼               ▼
                                  scripts/merge_adapter.py  (adapter/ is shippable)
                                            │
                                            ▼
                                    scripts/to_gguf.sh
                                            │
                                  eval/bench.py + eval/report.py
```

## Quickstart

### Install

```bash
# Core CLI (snapshot/export/splits/eval orchestration)
pip install -e .

# Training stack — installed separately because Unsloth ships CUDA-matched wheels.
# See train/train_distill.py for the exact command for your CUDA version.
pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git" pyyaml

# llama.cpp (for GGUF conversion + serving). Build llama.cpp yourself; the
# scripts/to_gguf.sh helper expects it at $HOME/programs/llama.cpp by default
# — override with LLAMA_CPP=/your/path.
```

Requirements: Python ≥3.11 <3.13, CUDA GPU with ≥24 GB VRAM for the default 7B QLoRA config, and a built [llama.cpp](https://github.com/ggerganov/llama.cpp) if you want GGUFs.

### End-to-end recipe (reproduces v1)

```bash
# 1. Configure paths to the upstream guru repo in rellm.toml (already set for
#    /home/ivy/Work/guru — edit for your machine).

# 2. Snapshot the current guru state into data/snapshots/<ts>/
rellm snapshot

# 3. Sanity-check what teacher labels are available
rellm stats
# Look for the row matching the teacher + prompt version set in rellm.toml.

# 4. Build the SFT dataset (one chat-format example per tagged chunk)
rellm export
# → data/exports/<ts>/sft.jsonl  + export-manifest.json

# 5. Split 90/5/5 train/val/test, deterministic by chunk_id
rellm splits data/exports/<ts>
# → data/exports/<ts>/splits.json

# 6. Train (QLoRA, r=32 all-linear, 3 epochs)
python train/train_distill.py \
    --export-dir data/exports/<ts> \
    --config configs/qwen25-7b-distill.yml \
    --output-dir out/qwen25-7b-r32

# 7. Merge adapter → FP16 HF checkpoint (for transformers users)
python scripts/merge_adapter.py \
    --adapter-dir out/qwen25-7b-r32/adapter \
    --out-dir     out/qwen25-7b-r32/merged

# 8. Convert merged → F16 GGUF → quantized (for llama.cpp / Ollama)
scripts/to_gguf.sh out/qwen25-7b-r32/merged qwen2.5-7b-rellm Q4_K_M
```

### Evaluate

Bench two endpoints against the held-out test split (e.g. fine-tuned vs base):

```bash
# Run student + base behind llama-server (--jinja so chat template is applied)
llama-server -m out/qwen25-7b-r32/qwen2.5-7b-rellm-Q4_K_M.gguf --jinja --port 8080 &
llama-server -m qwen2.5-7b-instruct-Q4_K_M.gguf                 --jinja --port 8081 &

# Inference + scoring
python eval/bench.py \
    --export-dir data/exports/<ts> \
    --endpoint student=http://127.0.0.1:8080 \
    --endpoint base=http://127.0.0.1:8081 \
    --out-dir runs/bench/<ts>

# Aggregate metrics
python eval/report.py runs/bench/<ts>
```

Output: precision / recall / F1 (score ≥ 1 as positive), macro-F1 over concepts, score-level confusion matrix, parse rate, latency, out-of-taxonomy IDs, and a worst-F1 concepts table.

### Publish (if you've retrained)

```bash
# Keep MODEL_CARD.md (source of truth) in sync with the HF README
cp MODEL_CARD.md out/qwen25-7b-r32/README.md

# Push artifacts (replace `vN` with the next version)
hf upload 4rc4n4/qwen2.5-7b-rellm out/qwen25-7b-r32/adapter adapter
hf upload 4rc4n4/qwen2.5-7b-rellm out/qwen25-7b-r32/merged  merged
hf upload 4rc4n4/qwen2.5-7b-rellm out/qwen25-7b-r32/qwen2.5-7b-rellm-Q4_K_M.gguf gguf/qwen2.5-7b-rellm-Q4_K_M.gguf
hf upload 4rc4n4/qwen2.5-7b-rellm out/qwen25-7b-r32/qwen2.5-7b-rellm-F16.gguf    gguf/qwen2.5-7b-rellm-F16.gguf
hf upload 4rc4n4/qwen2.5-7b-rellm out/qwen25-7b-r32/README.md                    README.md

# Tag both sides
git tag -a vN -m "vN — <summary>" && git push --tags
python -c "from huggingface_hub import HfApi; HfApi().create_tag('4rc4n4/qwen2.5-7b-rellm', tag='vN')"
```

## Repo layout

```
configs/                 training hyperparameter YAML
src/rellm/               CLI + data layer
  cli.py                 typer commands: snapshot, stats, export, splits, tag
  extract.py             pull (chunk, teacher_tags) joins from guru.db
  formats.py             SFT chat-format builder — prompt mirrors guru's tag_concepts.py
  splits.py              deterministic 90/5/5 train/val/test split
  taxonomy.py            load concepts from guru's taxonomy.toml
  corpus.py              resolve chunk body + citation from corpus/ on disk
  db.py, config.py
train/train_distill.py   Unsloth QLoRA SFT entry point
scripts/
  merge_adapter.py       adapter → FP16 HF checkpoint
  to_gguf.sh             merged → F16 GGUF → quantized
eval/
  bench.py               run candidates against the test split, write cells.csv + runs.csv
  report.py              F1 / macro-F1 / confusion / worst concepts
  report_human.py        same shape, against human-graded labels
  report_score.py        score-level breakdown
  zero_shot.py           probe a model with no teacher reference (sanity)
MODEL_CARD.md            source of truth for the HF README — keep them in sync
rellm.toml               paths to upstream guru repo, teacher signature, prompt version
configs/qwen25-7b-distill.yml   the v1 recipe
```

## Configuration

`rellm.toml` at the repo root controls everything that's stable across runs:

```toml
[guru]
repo       = "/home/ivy/Work/guru"
db         = "/home/ivy/Work/guru/data/guru.db"
corpus_dir = "/home/ivy/Work/guru/corpus"
taxonomy   = "/home/ivy/Work/guru/concepts/taxonomy.toml"

[model]
base    = "unsloth/Qwen2.5-7B-Instruct-bnb-4bit"
teacher = "Qwen3.5-27B-UD-Q4_K_XL.gguf"

[prompt]
version = "v1"   # bump when guru's tag prompt changes meaningfully
```

`configs/<name>.yml` controls per-run training hyperparameters.

## Prompt contract

The training-time prompt in `src/rellm/formats.py` **must match** the production caller in `guru/scripts/tag_concepts.py` byte-for-byte. If the upstream prompt changes meaningfully, bump `[prompt].version` in `rellm.toml` so old + new teacher outputs aren't mixed in a single training run.

## License

Apache 2.0 — see [LICENSE](LICENSE).
