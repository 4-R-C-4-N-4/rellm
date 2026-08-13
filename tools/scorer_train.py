#!/usr/bin/env python3
"""scorer_train.py — distill the thin (query, chunk) cross-encoder (rung 3a).

Student: cross-encoder/ms-marco-MiniLM-L6-v2 (22.7M params) warm start —
already a (query, passage) single-logit cross-encoder — fine-tuned end to end
with MSE against bge-reranker-v2-m3 teacher logits (scorer_teacher.py), so
the student inherits the teacher's judged scale and the calibrated-threshold
procedure transfers.

Split is BY QUERY (never by pair): 90/10 train/val on query hash. Early stop
on val Pearson r. max_length 512 for the student (speed target); truncation
loss is the student's problem to absorb and Pearson-vs-teacher reports it.

GPU owner-authorized for this plan (todo:82f6dbb7). Writes checkpoint +
training card under runs/edges/scorer/<ts>/.

Usage:
    python tools/scorer_train.py --pairs <pairs.jsonl> --teacher <teacher.jsonl> \
        --out runs/edges/scorer/<ts>/student-3a
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import time
from pathlib import Path

SEED = 20260812
STUDENT = "cross-encoder/ms-marco-MiniLM-L6-v2"


def qh(query: str) -> str:
    return hashlib.sha256(query.encode()).hexdigest()[:16]


def pearson(a, b) -> float:
    import numpy as np
    a, b = np.asarray(a), np.asarray(b)
    if a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pairs", type=Path, required=True)
    ap.add_argument("--teacher", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--epochs", type=int, default=4)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--max-length", type=int, default=512)
    args = ap.parse_args()

    import numpy as np                                     # noqa: F401
    import torch
    from torch.utils.data import DataLoader, Dataset
    from transformers import (AutoModelForSequenceClassification,
                              AutoTokenizer)

    torch.manual_seed(SEED)
    random.seed(SEED)

    teacher = {}
    for l in args.teacher.read_text().splitlines():
        r = json.loads(l)
        teacher[(r["qh"], r["chunk_id"])] = r["teacher_logit"]
    rows = []
    for l in args.pairs.read_text().splitlines():
        r = json.loads(l)
        t = teacher.get((qh(r["query"]), r["chunk_id"]))
        if t is not None:
            rows.append((r["query"], r["body"], t, r["stratum"]))
    print(f"{len(rows)} labeled pairs")

    queries = sorted({qh(q) for q, *_ in rows})
    rng = random.Random(SEED)
    rng.shuffle(queries)
    val_q = set(queries[:max(1, len(queries) // 10)])
    train = [r for r in rows if qh(r[0]) not in val_q]
    val = [r for r in rows if qh(r[0]) in val_q]
    print(f"train {len(train)} pairs / val {len(val)} pairs "
          f"({len(val_q)} val queries, split by query)")

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(STUDENT)
    model = AutoModelForSequenceClassification.from_pretrained(
        STUDENT, num_labels=1).to(dev)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"student {STUDENT} ({n_params/1e6:.1f}M params) on {dev}")

    class DS(Dataset):
        def __init__(self, data): self.data = data
        def __len__(self): return len(self.data)
        def __getitem__(self, i): return self.data[i]

    def collate(batch):
        enc = tok([[q, b] for q, b, *_ in batch], padding=True,
                  truncation=True, max_length=args.max_length,
                  return_tensors="pt")
        y = torch.tensor([t for _, _, t, _ in batch], dtype=torch.float32)
        return enc, y

    dl = DataLoader(DS(train), batch_size=args.batch, shuffle=True,
                    collate_fn=collate)
    vdl = DataLoader(DS(val), batch_size=64, collate_fn=collate)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr)

    def evaluate() -> float:
        model.eval()
        preds, ys = [], []
        with torch.no_grad():
            for enc, y in vdl:
                enc = {k: v.to(dev) for k, v in enc.items()}
                preds += model(**enc).logits.view(-1).cpu().tolist()
                ys += y.tolist()
        model.train()
        return pearson(preds, ys)

    best_r, card_epochs = -2.0, []
    args.out.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    for epoch in range(1, args.epochs + 1):
        losses = []
        for enc, y in dl:
            enc = {k: v.to(dev) for k, v in enc.items()}
            loss = torch.nn.functional.mse_loss(
                model(**enc).logits.view(-1), y.to(dev))
            loss.backward()
            opt.step()
            opt.zero_grad()
            losses.append(float(loss))
        r = evaluate()
        card_epochs.append({"epoch": epoch,
                            "train_mse": round(sum(losses) / len(losses), 4),
                            "val_pearson": round(r, 4)})
        print(f"epoch {epoch}: train MSE {card_epochs[-1]['train_mse']:.4f}"
              f"  val Pearson {r:+.4f}", flush=True)
        if r > best_r:
            best_r = r
            model.save_pretrained(args.out)
            tok.save_pretrained(args.out)

    card = {
        "student": STUDENT, "params_m": round(n_params / 1e6, 2),
        "pairs": {"train": len(train), "val": len(val)},
        "val_queries": len(val_q), "split": "by-query",
        "config": {"epochs": args.epochs, "batch": args.batch,
                   "lr": args.lr, "max_length": args.max_length,
                   "loss": "mse-vs-teacher-logit", "seed": SEED},
        "pairs_sha": hashlib.sha256(
            args.pairs.read_bytes()).hexdigest()[:16],
        "epochs": card_epochs, "best_val_pearson": round(best_r, 4),
        "train_seconds": round(time.monotonic() - t0, 1), "device": dev,
    }
    (args.out / "training-card.json").write_text(json.dumps(card, indent=2))
    print(f"best val Pearson {best_r:+.4f}; saved {args.out}")


if __name__ == "__main__":
    main()
