#!/usr/bin/env python3
"""scorer_teacher.py — bge-reranker-v2-m3 teacher logits over sampled pairs.

Mirrors the judged scoring config exactly (fp32 weights, max_length 1024,
body already truncated to 2400 chars by scorer_pairs.py) so teacher logits
live on the same scale as every judged run. Cache keyed
(sha256(query)[:16], chunk_id) makes reruns incremental.

GPU: owner-authorized for this plan (todo:519f3554). Pins the 3090 via
CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=0 (set by the caller);
falls back to CPU transparently.

Usage:
    python tools/scorer_teacher.py --pairs <pairs.jsonl> --out <teacher.jsonl>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path


def qh(query: str) -> str:
    return hashlib.sha256(query.encode()).hexdigest()[:16]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pairs", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--batch", type=int, default=64)
    args = ap.parse_args()

    import torch
    from transformers import (AutoModelForSequenceClassification,
                              AutoTokenizer)

    rows = [json.loads(l) for l in args.pairs.read_text().splitlines()
            if l.strip()]
    cache: dict[tuple[str, str], float] = {}
    if args.out.exists():
        for l in args.out.read_text().splitlines():
            r = json.loads(l)
            cache[(r["qh"], r["chunk_id"])] = r["teacher_logit"]
    todo = [r for r in rows if (qh(r["query"]), r["chunk_id"]) not in cache]
    print(f"{len(rows)} pairs, {len(cache)} cached, {len(todo)} to score")

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    name = "BAAI/bge-reranker-v2-m3"
    tok = AutoTokenizer.from_pretrained(name)
    model = AutoModelForSequenceClassification.from_pretrained(
        name, dtype=torch.float32).to(dev)
    model.eval()
    print(f"teacher on {dev}"
          + (f" ({torch.cuda.get_device_name(0)})" if dev == "cuda" else ""))

    t0 = time.monotonic()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "a") as out, torch.no_grad():
        for i in range(0, len(todo), args.batch):
            batch = todo[i:i + args.batch]
            enc = tok([[r["query"], r["body"]] for r in batch],
                      padding=True, truncation=True, max_length=1024,
                      return_tensors="pt").to(dev)
            logits = model(**enc).logits.view(-1)
            for r, s in zip(batch, logits.tolist()):
                out.write(json.dumps({"qh": qh(r["query"]),
                                      "chunk_id": r["chunk_id"],
                                      "teacher_logit": round(s, 5)}) + "\n")
            if (i // args.batch) % 20 == 0:
                done = min(i + args.batch, len(todo))
                rate = done / max(time.monotonic() - t0, 1e-9)
                print(f"  {done}/{len(todo)}  ({rate:.0f} pairs/s)",
                      flush=True)
    dt = time.monotonic() - t0
    print(f"scored {len(todo)} pairs in {dt:.0f}s"
          f"  ({len(todo) / max(dt, 1e-9):.0f} pairs/s on {dev})")


if __name__ == "__main__":
    main()
