"""Unsloth QLoRA SFT for distilling the guru tagger.

Prereqs:
    rellm export                       # writes data/exports/<ts>/sft.jsonl
    rellm splits data/exports/<ts>     # writes splits.json next to it

Install (separate venv, follow Unsloth's installer for your CUDA):
    pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
    pip install pyyaml

Run:
    python train/train_distill.py \\
        --export-dir data/exports/<ts> \\
        --config configs/qwen25-7b-distill.yml \\
        --output-dir out/qwen25-7b-r32
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _train(args: argparse.Namespace) -> None:
    import yaml
    import torch
    from datasets import Dataset
    from unsloth import FastLanguageModel
    from unsloth.chat_templates import get_chat_template
    from trl import SFTTrainer, SFTConfig

    cfg = yaml.safe_load(Path(args.config).read_text())
    export_dir = Path(args.export_dir)
    splits = json.loads((export_dir / "splits.json").read_text())["splits"]

    train_rows: list[dict] = []
    val_rows: list[dict] = []
    with (export_dir / "sft.jsonl").open() as f:
        for line in f:
            ex = json.loads(line)
            bucket = splits.get(ex["chunk_id"], "train")
            (val_rows if bucket == "val" else train_rows if bucket == "train" else []).append(ex)
    print(f"loaded {len(train_rows)} train / {len(val_rows)} val")

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=cfg["base_model"],
        max_seq_length=cfg["max_seq_length"],
        dtype=None,
        load_in_4bit=True,
    )
    tokenizer = get_chat_template(tokenizer, chat_template=cfg.get("chat_template", "qwen-2.5"))

    model = FastLanguageModel.get_peft_model(
        model,
        r=cfg["lora_r"],
        lora_alpha=cfg["lora_alpha"],
        lora_dropout=cfg.get("lora_dropout", 0.0),
        target_modules=cfg["lora_target_modules"],
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=cfg.get("seed", 42),
    )

    def _format(ex: dict) -> dict:
        return {
            "text": tokenizer.apply_chat_template(
                ex["messages"], tokenize=False, add_generation_prompt=False
            )
        }

    train_ds = Dataset.from_list(train_rows).map(
        _format, remove_columns=["chunk_id", "tradition_id", "messages"]
    )
    val_ds = Dataset.from_list(val_rows).map(
        _format, remove_columns=["chunk_id", "tradition_id", "messages"]
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        dataset_text_field="text",
        max_seq_length=cfg["max_seq_length"],
        args=SFTConfig(
            output_dir=str(output_dir),
            per_device_train_batch_size=cfg["batch_size"],
            gradient_accumulation_steps=cfg["grad_accum"],
            num_train_epochs=cfg["epochs"],
            learning_rate=cfg["learning_rate"],
            warmup_ratio=cfg.get("warmup_ratio", 0.03),
            lr_scheduler_type=cfg.get("lr_scheduler", "cosine"),
            optim=cfg.get("optim", "adamw_8bit"),
            logging_steps=cfg.get("logging_steps", 10),
            eval_strategy="steps",
            eval_steps=cfg.get("eval_steps", 100),
            save_steps=cfg.get("save_steps", 200),
            save_total_limit=cfg.get("save_total_limit", 3),
            bf16=torch.cuda.is_bf16_supported(),
            fp16=not torch.cuda.is_bf16_supported(),
            seed=cfg.get("seed", 42),
            report_to=cfg.get("report_to", "none"),
        ),
    )
    trainer.train()

    adapter_dir = output_dir / "adapter"
    model.save_pretrained(adapter_dir)
    tokenizer.save_pretrained(adapter_dir)
    print(f"saved adapter to {adapter_dir}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--export-dir", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--output-dir", required=True)
    _train(ap.parse_args())


if __name__ == "__main__":
    main()
