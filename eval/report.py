"""Aggregate eval/bench.py outputs into a metrics report.

Reads cells.csv + runs.csv from a bench output dir and prints:
  - per-model summary (precision/recall/F1 on score>=1, MAE, parse rate, latency)
  - macro-F1 averaged over concepts
  - score confusion matrix (teacher × model, 0..3)
  - worst-F1 concepts (where the model struggles most)

Usage:
    python eval/report.py runs/bench/<ts>
"""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean


def _f1(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("bench_dir", type=Path)
    ap.add_argument("--min-positives", type=int, default=2,
                    help="ignore concepts with fewer teacher positives in worst-F1 table")
    args = ap.parse_args()

    cells_path = args.bench_dir / "cells.csv"
    runs_path = args.bench_dir / "runs.csv"

    tp: dict[str, int] = defaultdict(int)
    fp: dict[str, int] = defaultdict(int)
    fn: dict[str, int] = defaultdict(int)
    c_tp: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    c_fp: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    c_fn: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    score_err: dict[str, list[int]] = defaultdict(list)
    confusion: dict[str, dict[tuple[int, int], int]] = defaultdict(lambda: defaultdict(int))
    oot: dict[str, int] = defaultdict(int)

    with cells_path.open() as f:
        for row in csv.DictReader(f):
            m = row["model"]
            cid = row["concept_id"]
            ts = int(row["teacher_score"])
            ms = int(row["model_score"])
            in_tax = int(row["in_taxonomy"])

            tpos, mpos = ts >= 1, ms >= 1
            if tpos and mpos:
                tp[m] += 1
                c_tp[m][cid] += 1
                score_err[m].append(abs(ts - ms))
            elif tpos and not mpos:
                fn[m] += 1
                c_fn[m][cid] += 1
            elif not tpos and mpos:
                fp[m] += 1
                c_fp[m][cid] += 1
                if not in_tax:
                    oot[m] += 1
            confusion[m][(ts, ms)] += 1

    runs: dict[str, dict] = defaultdict(lambda: {"n": 0, "ok": 0, "lat": [], "emit": []})
    with runs_path.open() as f:
        for row in csv.DictReader(f):
            m = row["model"]
            s = runs[m]
            s["n"] += 1
            s["ok"] += int(row["parse_ok"])
            try:
                s["lat"].append(float(row["latency_s"]))
                s["emit"].append(int(row["n_emitted"]))
            except ValueError:
                pass

    models = sorted(set(tp) | set(fp) | set(fn) | set(runs))

    print("\n=== Per-model summary ===")
    print(f"{'model':<14} {'precision':>10} {'recall':>10} {'F1':>8} "
          f"{'MAE':>6} {'parse%':>8} {'lat(s)':>8} {'n_emit':>8} {'runs':>6}")
    for m in models:
        p, r, f = _f1(tp[m], fp[m], fn[m])
        mae = mean(score_err[m]) if score_err[m] else 0.0
        rs = runs[m]
        parse_pct = rs["ok"] / rs["n"] * 100 if rs["n"] else 0.0
        lat = mean(rs["lat"]) if rs["lat"] else 0.0
        n_emit = mean(rs["emit"]) if rs["emit"] else 0.0
        print(f"{m:<14} {p:>10.3f} {r:>10.3f} {f:>8.3f} "
              f"{mae:>6.2f} {parse_pct:>7.1f}% {lat:>8.2f} {n_emit:>8.1f} {rs['n']:>6}")

    print("\n=== Macro-F1 (averaged over concepts that appear in either teacher or model) ===")
    for m in models:
        all_c = set(c_tp[m]) | set(c_fp[m]) | set(c_fn[m])
        f1s = [_f1(c_tp[m][c], c_fp[m][c], c_fn[m][c])[2] for c in all_c]
        macro = mean(f1s) if f1s else 0.0
        print(f"  {m:<14} macro-F1 = {macro:.3f}   (over {len(f1s)} concepts)")

    print("\n=== Score confusion (rows=teacher, cols=model) ===")
    for m in models:
        print(f"  {m}:")
        print(f"          m=0     m=1     m=2     m=3")
        for ts in range(4):
            cells = "  ".join(f"{confusion[m].get((ts, ms), 0):>5}" for ms in range(4))
            print(f"  t={ts}    {cells}")

    print("\n=== Out-of-taxonomy concept IDs emitted (model invented IDs) ===")
    for m in models:
        print(f"  {m:<14} {oot[m]}")

    print(f"\n=== Worst-F1 concepts (n_teacher_positives >= {args.min_positives}) ===")
    for m in models:
        all_c = set(c_tp[m]) | set(c_fp[m]) | set(c_fn[m])
        ranked = []
        for cid in all_c:
            n_pos = c_tp[m][cid] + c_fn[m][cid]
            if n_pos < args.min_positives:
                continue
            _, _, fc = _f1(c_tp[m][cid], c_fp[m][cid], c_fn[m][cid])
            ranked.append((fc, cid, n_pos))
        ranked.sort()
        print(f"  {m}:")
        for fc, cid, n in ranked[:5]:
            print(f"    {cid:<42} F1={fc:.3f}  (n={n})")


if __name__ == "__main__":
    main()
