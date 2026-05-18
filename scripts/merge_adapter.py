"""Merge a QLoRA adapter into the base model and save a full fp16/bf16 HF checkpoint.

Run after train/train_distill.py finishes. Output is the input to scripts/to_gguf.sh.

Usage:
    python scripts/merge_adapter.py \
        --adapter-dir out/qwen25-7b-r32/adapter \
        --out-dir     out/qwen25-7b-r32/merged
"""
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter-dir", required=True, help="dir containing adapter_config.json + tokenizer")
    ap.add_argument("--out-dir", required=True, help="destination for the merged HF checkpoint")
    ap.add_argument("--max-seq-length", type=int, default=4096)
    args = ap.parse_args()

    from unsloth import FastLanguageModel

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=args.adapter_dir,
        max_seq_length=args.max_seq_length,
        dtype=None,
        load_in_4bit=False,
    )

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    model.save_pretrained_merged(str(out), tokenizer, save_method="merged_16bit")
    print(f"merged checkpoint written to {out}")


if __name__ == "__main__":
    main()
