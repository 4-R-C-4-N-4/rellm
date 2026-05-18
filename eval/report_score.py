"""Score-level diagnostic across human verdicts.

Drills into where student / base / teacher differ at each score level, with
the load-bearing question: when the teacher said score=X and humans rejected,
did the student dial it down (good) or stay close to the teacher (bad)?

Usage:
    python eval/report_score.py runs/bench/<ts>
"""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


def _pct(n: int, d: int) -> str:
    return f"{n/d*100:>5.1f}%" if d else "   -- "


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("bench_dir", type=Path)
    args = ap.parse_args()

    cells = list(csv.DictReader((args.bench_dir / "cells.csv").open()))
    models = sorted({r["model"] for r in cells})
    print(f"\nloaded {len(cells)} rows × {len(models)} models from {args.bench_dir}")

    # --- 1. Emission distribution by score ----------------------------------
    print("\n=== Score emission distribution (cells where actor emitted >= 1) ===")
    print(f"{'actor':<10}  {'score=1':>14} {'score=2':>14} {'score=3':>14}  {'total':>7}")
    # teacher row (dedupe by chunk_id × concept_id)
    teach: dict[int, int] = {1: 0, 2: 0, 3: 0}
    seen: set[tuple[str, str]] = set()
    for r in cells:
        key = (r["chunk_id"], r["concept_id"])
        if key in seen:
            continue
        seen.add(key)
        s = int(r["teacher_score"])
        if s >= 1:
            teach[s] += 1
    tt = sum(teach.values())
    print(f"{'teacher':<10}  " + " ".join(f"{teach[i]:>6d} ({_pct(teach[i], tt)})" for i in (1, 2, 3)) + f"  {tt:>7d}")
    for m in models:
        dist = {1: 0, 2: 0, 3: 0}
        for r in cells:
            if r["model"] != m:
                continue
            s = int(r["model_score"])
            if s >= 1:
                dist[s] = dist.get(s, 0) + 1
        tot = sum(dist.values())
        print(f"{m:<10}  " + " ".join(f"{dist[i]:>6d} ({_pct(dist[i], tot)})" for i in (1, 2, 3)) + f"  {tot:>7d}")

    # --- 2. Per-teacher-score binary F1 against humans -----------------------
    print("\n=== Per-teacher-score F1 against humans ===")
    print(f"{'model':<10} {'t.score':>7} {'n':>5} {'acc':>5} {'rej':>5}  "
          f"{'prec':>6} {'rec':>6} {'F1':>6} {'spec':>6}")
    for m in models:
        for tscore in (1, 2, 3):
            tp = fp = fn = tn = 0
            for r in cells:
                if r["model"] != m:
                    continue
                if int(r["teacher_score"]) != tscore:
                    continue
                if r["human_status"] not in ("accepted", "rejected"):
                    continue
                mpos = int(r["model_score"]) >= 1
                hpos = r["human_status"] == "accepted"
                if hpos and mpos:
                    tp += 1
                elif hpos and not mpos:
                    fn += 1
                elif not hpos and mpos:
                    fp += 1
                else:
                    tn += 1
            n = tp + fp + fn + tn
            if n == 0:
                continue
            acc, rej = tp + fn, fp + tn
            p = tp / (tp + fp) if tp + fp else 0
            r_ = tp / (tp + fn) if tp + fn else 0
            f = 2 * p * r_ / (p + r_) if p + r_ else 0
            sp = tn / (tn + fp) if tn + fp else 0
            print(f"{m:<10} {tscore:>7} {n:>5} {acc:>5} {rej:>5}  "
                  f"{p:>6.3f} {r_:>6.3f} {f:>6.3f} {sp:>6.3f}")

    # --- 3. Conditional score distribution -----------------------------------
    print("\n=== Score the model emits, conditional on (teacher_score, human_verdict) ===")
    print("  Expected behavior: on 'rejected' rows, model should dial DOWN (toward 0).")
    print("  On 'accepted' rows, model should match teacher's score.")
    for m in models:
        print(f"\n  {m}:")
        print(f"  {'t':<3} {'verdict':<10} {'n':>5}  "
              f"{'m=0':>11} {'m=1':>11} {'m=2':>11} {'m=3':>11}  "
              f"{'mean':>5} {'Δ':>6}")
        for tscore in (1, 2, 3):
            for verdict in ("accepted", "rejected"):
                rows = [r for r in cells
                        if r["model"] == m
                        and int(r["teacher_score"]) == tscore
                        and r["human_status"] == verdict]
                if not rows:
                    continue
                dist = {0: 0, 1: 0, 2: 0, 3: 0}
                for r in rows:
                    dist[int(r["model_score"])] += 1
                n = len(rows)
                mean_s = sum(int(r["model_score"]) for r in rows) / n
                delta = mean_s - tscore
                cells_str = " ".join(f"{dist[i]:>4d}({_pct(dist[i], n)})" for i in (0, 1, 2, 3))
                print(f"  {tscore:<3} {verdict:<10} {n:>5}  {cells_str}  "
                      f"{mean_s:>5.2f} {delta:>+6.2f}")

    # --- 4. Score delta histogram --------------------------------------------
    print("\n=== Score delta (model − teacher) on cells where teacher >= 1 ===")
    for m in models:
        print(f"\n  {m}:")
        print(f"  {'verdict':<10} {'n':>5}  {'mean Δ':>7}   delta histogram")
        for verdict in ("accepted", "rejected", "pending"):
            deltas: dict[int, int] = defaultdict(int)
            for r in cells:
                if r["model"] != m:
                    continue
                if int(r["teacher_score"]) < 1:
                    continue
                if (r["human_status"] or "pending") != verdict:
                    continue
                d = int(r["model_score"]) - int(r["teacher_score"])
                deltas[d] += 1
            n = sum(deltas.values())
            if n == 0:
                continue
            mean_d = sum(d * c for d, c in deltas.items()) / n
            hist = "  ".join(f"{d:+d}:{deltas[d]:>4d}" for d in range(-3, 4) if deltas[d] > 0)
            print(f"  {verdict:<10} {n:>5}  {mean_d:>+7.2f}   {hist}")


if __name__ == "__main__":
    main()
