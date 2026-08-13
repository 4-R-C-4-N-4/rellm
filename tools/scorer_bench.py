#!/usr/bin/env python3
"""scorer_bench.py — CPU latency bench for a (query, chunk) cross-encoder.

Spec targets (docs/edges/thin-scorer-spec.md): ≥100 pairs/s on ONE cpu
thread fp32; int8 (dynamic quantization) reported alongside; load ≤2s.

CPU-only by construction. Usage:
    python tools/scorer_bench.py --model <dir-or-name> [--pairs <pairs.jsonl>]
"""
from __future__ import annotations

import argparse
import json
import os
import random
import time
from pathlib import Path

os.environ["CUDA_VISIBLE_DEVICES"] = ""

N_PAIRS = 240
MAX_LENGTH = 512


def bench(model, tok, pairs, threads: int, label: str) -> float:
    import torch
    torch.set_num_threads(threads)
    with torch.no_grad():   # warmup
        enc = tok(pairs[:8], padding=True, truncation=True,
                  max_length=MAX_LENGTH, return_tensors="pt")
        model(**enc)
    t0 = time.monotonic()
    with torch.no_grad():
        for i in range(0, len(pairs), 32):
            enc = tok(pairs[i:i + 32], padding=True, truncation=True,
                      max_length=MAX_LENGTH, return_tensors="pt")
            model(**enc)
    dt = time.monotonic() - t0
    rate = len(pairs) / dt
    print(f"  {label:<28}{threads} thread(s): "
          f"{rate:7.1f} pairs/s  ({dt:5.1f}s / {len(pairs)} pairs)")
    return rate


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", required=True)
    ap.add_argument("--pairs", type=Path,
                    help="pairs.jsonl for realistic bodies; synthetic if absent")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    t0 = time.monotonic()
    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model, dtype=torch.float32)
    model.eval()
    load_s = time.monotonic() - t0
    n_params = sum(p.numel() for p in model.parameters())
    print(f"model {args.model}: {n_params/1e6:.1f}M params, "
          f"load {load_s:.2f}s")

    if args.pairs and args.pairs.exists():
        rows = [json.loads(l) for l in args.pairs.read_text().splitlines()
                if l.strip()]
        random.Random(0).shuffle(rows)
        pairs = [[r["query"], r["body"]] for r in rows[:N_PAIRS]]
    else:
        pairs = [["what happens to the soul after death",
                  "lorem " * 400]] * N_PAIRS

    results = {"params_m": round(n_params / 1e6, 2),
               "load_seconds": round(load_s, 2), "max_length": MAX_LENGTH}
    results["fp32_1t"] = round(bench(model, tok, pairs, 1, "fp32"), 1)
    results["fp32_8t"] = round(bench(model, tok, pairs, 8, "fp32"), 1)

    qmodel = torch.ao.quantization.quantize_dynamic(
        model, {torch.nn.Linear}, dtype=torch.qint8)
    results["int8_1t"] = round(bench(qmodel, tok, pairs, 1, "int8 dynamic"), 1)
    results["int8_8t"] = round(bench(qmodel, tok, pairs, 8, "int8 dynamic"), 1)

    if args.out:
        args.out.write_text(json.dumps(results, indent=2))
        print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
