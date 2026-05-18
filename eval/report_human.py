"""Score student vs base against human-curated ground truth.

Filters the cells.csv from `bench.py --all-curated` down to rows where a human
verdict exists (accepted or rejected), then computes:

  - Per-model precision / recall / F1 / specificity on humans-as-truth.
  - Same metrics broken out by split (train / val / test), so contamination
    is visible: train chunks were seen by the student during fine-tuning;
    val and test were not.
  - Teacher baseline: by construction teacher always scored >= 1 on these
    cells, so its specificity is 0 and its recall is 1 — F1 is determined
    purely by the accepted/total ratio.

Usage:
    python eval/report_human.py runs/bench/<ts>
"""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


def _f1(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f


def _spec(tn: int, fp: int) -> float:
    return tn / (tn + fp) if tn + fp else 0.0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("bench_dir", type=Path)
    args = ap.parse_args()

    cells_path = args.bench_dir / "cells.csv"

    # counters[(model, split)] = {"tp", "fp", "fn", "tn"}
    counters: dict[tuple[str, str], dict[str, int]] = defaultdict(
        lambda: {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    )
    total_curated_rows = 0

    with cells_path.open() as f:
        for row in csv.DictReader(f):
            status = row.get("human_status", "")
            if status not in ("accepted", "rejected"):
                continue
            total_curated_rows += 1

            m = row["model"]
            split = row.get("split") or "unknown"
            ms = int(row["model_score"])
            mpos = ms >= 1
            human_pos = status == "accepted"

            for key in [(m, split), (m, "ALL")]:
                c = counters[key]
                if human_pos and mpos:
                    c["tp"] += 1
                elif human_pos and not mpos:
                    c["fn"] += 1
                elif not human_pos and mpos:
                    c["fp"] += 1
                else:
                    c["tn"] += 1

    if not counters:
        print("no human-curated rows found in cells.csv")
        print("hint: re-run bench.py with --all-curated and the new snapshot")
        return

    print(f"\nhuman-curated cells found: {total_curated_rows // 2} per model "
          f"(× {len({m for m, _ in counters})} models)")

    models = sorted({m for m, _ in counters})
    splits = ["ALL", "train", "val", "test", "unknown"]
    splits = [s for s in splits if any((m, s) in counters for m in models)]

    print("\n=== Per-model × split, humans-as-truth ===")
    print(f"{'model':<12} {'split':<8} {'TP':>5} {'FP':>5} {'FN':>5} {'TN':>5} "
          f"{'prec':>7} {'rec':>7} {'F1':>7} {'spec':>7}  {'n':>5}")
    for m in models:
        for s in splits:
            if (m, s) not in counters:
                continue
            c = counters[(m, s)]
            p, r, f = _f1(c["tp"], c["fp"], c["fn"])
            sp = _spec(c["tn"], c["fp"])
            n = c["tp"] + c["fp"] + c["fn"] + c["tn"]
            print(f"{m:<12} {s:<8} {c['tp']:>5} {c['fp']:>5} {c['fn']:>5} "
                  f"{c['tn']:>5} {p:>7.3f} {r:>7.3f} {f:>7.3f} {sp:>7.3f}  "
                  f"{n:>5}")

    # Teacher baseline: it scored >=1 on every cell humans reviewed, so
    # TP = n_accepted, FP = n_rejected, FN=TN=0.
    if ("ALL" in splits) and counters:
        first_model = models[0]
        c = counters[(first_model, "ALL")]
        n_acc = c["tp"] + c["fn"]
        n_rej = c["fp"] + c["tn"]
        p, r, f = _f1(n_acc, n_rej, 0)
        print(f"\nTeacher baseline (all curated): precision={p:.3f}  "
              f"recall=1.000  F1={f:.3f}  specificity=0.000  "
              f"(n_accepted={n_acc}, n_rejected={n_rej})")
        print("This is what humans would score the teacher itself — beating "
              "this F1 means the model has learned to reject teacher mistakes.")


if __name__ == "__main__":
    main()
