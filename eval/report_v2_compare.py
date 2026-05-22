"""Aggregate v1↔v2 comparison metrics from a three-endpoint bench dir.

Reads cells.csv + runs.csv from a `bench_v2.sh` run (endpoints: base, v1, v2)
and prints, for each {full v2-test split (130 chunks), v1-test carryover
(103 chunks), per-tradition slices, per-concept deltas}:

  - precision / recall / F1 / macro-F1 / MAE / parse rate / OOT-IDs
  - tables formatted for pasting into docs/v1-vs-v2-comparison.md

Usage:
    python eval/report_v2_compare.py runs/bench/v2-vs-v1-vs-base-<ts> \\
        --v1-export data/exports/2026-05-13T16-31-48Z

If --v1-export is omitted, the v1-test carryover table is skipped.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean


def _f1(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f


def _load_cells(bench_dir: Path) -> list[dict]:
    with (bench_dir / "cells.csv").open() as f:
        return list(csv.DictReader(f))


def _load_runs(bench_dir: Path) -> dict[str, dict]:
    runs: dict[str, dict] = defaultdict(lambda: {"n": 0, "ok": 0, "lat": [], "emit": [], "oot_chunks": 0})
    with (bench_dir / "runs.csv").open() as f:
        for row in csv.DictReader(f):
            m = row["model"]
            s = runs[m]
            s["n"] += 1
            s["ok"] += int(row["parse_ok"])
            try:
                s["lat"].append(float(row["latency_s"]))
                s["emit"].append(int(row["n_emitted"]))
                s["oot_chunks"] += int(int(row["n_out_of_taxonomy"]) > 0)
            except (ValueError, KeyError):
                pass
    return runs


def _metrics(rows: list[dict], runs: dict[str, dict] | None = None) -> dict[str, dict]:
    tp: dict[str, int] = defaultdict(int)
    fp: dict[str, int] = defaultdict(int)
    fn: dict[str, int] = defaultdict(int)
    c_tp: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    c_fp: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    c_fn: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    score_err: dict[str, list[int]] = defaultdict(list)
    oot: dict[str, int] = defaultdict(int)
    chunks: dict[str, set] = defaultdict(set)

    for row in rows:
        m = row["model"]
        cid = row["concept_id"]
        ts = int(row["teacher_score"])
        ms = int(row["model_score"])
        in_tax = int(row["in_taxonomy"])
        chunks[m].add(row["chunk_id"])
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

    out: dict[str, dict] = {}
    models = sorted(set(tp) | set(fp) | set(fn))
    for m in models:
        p, r, f = _f1(tp[m], fp[m], fn[m])
        all_c = set(c_tp[m]) | set(c_fp[m]) | set(c_fn[m])
        f1s = [_f1(c_tp[m][c], c_fp[m][c], c_fn[m][c])[2] for c in all_c]
        macro = mean(f1s) if f1s else 0.0
        mae = mean(score_err[m]) if score_err[m] else 0.0
        out[m] = {
            "P": p, "R": r, "F1": f, "macro_F1": macro,
            "MAE": mae, "OOT": oot[m],
            "n_chunks": len(chunks[m]),
            "tp": tp[m], "fp": fp[m], "fn": fn[m],
        }
        if runs and m in runs:
            rs = runs[m]
            out[m]["parse"] = rs["ok"] / rs["n"] if rs["n"] else 0.0
            out[m]["lat"] = mean(rs["lat"]) if rs["lat"] else 0.0
            out[m]["emit"] = mean(rs["emit"]) if rs["emit"] else 0.0
    return out


def _print_table(title: str, m: dict[str, dict], note: str = "") -> None:
    print(f"\n### {title}")
    if note:
        print(f"{note}")
    print()
    header = ["model", "P", "R", "F1", "macro-F1", "MAE", "parse", "lat(s)", "n_emit", "OOT", "n_chunks"]
    print("| " + " | ".join(header) + " |")
    print("|" + "|".join(["---"] * len(header)) + "|")
    for name in ["base", "v1", "v2"]:
        if name not in m:
            continue
        d = m[name]
        cells = [
            name,
            f"{d['P']:.3f}",
            f"{d['R']:.3f}",
            f"{d['F1']:.3f}",
            f"{d['macro_F1']:.3f}",
            f"{d['MAE']:.2f}",
            f"{d.get('parse', 0)*100:.1f}%" if "parse" in d else "—",
            f"{d.get('lat', 0):.2f}" if "lat" in d else "—",
            f"{d.get('emit', 0):.1f}" if "emit" in d else "—",
            str(d["OOT"]),
            str(d["n_chunks"]),
        ]
        print("| " + " | ".join(cells) + " |")


def _concept_deltas(rows: list[dict], a: str, b: str, min_n: int = 3) -> tuple[list[tuple], list[tuple]]:
    """Per-concept F1 for model a vs b, sorted by Δ. Returns (gains, regressions)."""
    tp: dict[tuple[str, str], int] = defaultdict(int)
    fp: dict[tuple[str, str], int] = defaultdict(int)
    fn: dict[tuple[str, str], int] = defaultdict(int)
    for row in rows:
        m = row["model"]
        if m not in (a, b):
            continue
        cid = row["concept_id"]
        ts = int(row["teacher_score"])
        ms = int(row["model_score"])
        tpos, mpos = ts >= 1, ms >= 1
        if tpos and mpos:
            tp[(m, cid)] += 1
        elif tpos and not mpos:
            fn[(m, cid)] += 1
        elif not tpos and mpos:
            fp[(m, cid)] += 1
    concepts = set(c for (_, c) in tp) | set(c for (_, c) in fp) | set(c for (_, c) in fn)
    rows_out = []
    for c in concepts:
        n_pos = tp[(a, c)] + fn[(a, c)]
        if n_pos < min_n:
            continue
        _, _, fa = _f1(tp[(a, c)], fp[(a, c)], fn[(a, c)])
        _, _, fb = _f1(tp[(b, c)], fp[(b, c)], fn[(b, c)])
        rows_out.append((c, n_pos, fa, fb, fb - fa))
    rows_out.sort(key=lambda r: r[-1])
    return rows_out[-10:][::-1], rows_out[:10]  # top gains (b-a positive), top regressions


def _by_tradition(rows: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        tradition = row["chunk_id"].split(".")[0]
        out[tradition].append(row)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("bench_dir", type=Path)
    ap.add_argument("--v1-export", type=Path, default=None,
                    help="path to v1 export dir so we can filter to the v1-test carryover subset")
    ap.add_argument("--min-positives", type=int, default=3,
                    help="ignore concepts with fewer teacher positives in delta tables")
    args = ap.parse_args()

    cells = _load_cells(args.bench_dir)
    runs = _load_runs(args.bench_dir)

    # ---- v2-test full ----
    print("# v1 ↔ v2 comparison")
    print(f"\nBench dir: `{args.bench_dir}`")
    print(f"Models in bench: {sorted({r['model'] for r in cells})}")
    print(f"Chunks in bench: {len(set(r['chunk_id'] for r in cells))}")

    full = _metrics(cells, runs)
    _print_table("Full v2-test split (130 chunks)", full)

    # ---- v1-test carryover subset ----
    if args.v1_export:
        v1_splits = json.loads((args.v1_export / "splits.json").read_text())["splits"]
        v1_test_ids = {cid for cid, b in v1_splits.items() if b == "test"}
        sub_cells = [r for r in cells if r["chunk_id"] in v1_test_ids]
        n_sub = len(set(r["chunk_id"] for r in sub_cells))
        sub = _metrics(sub_cells)
        _print_table(
            f"v1-test carryover ({n_sub} chunks — same chunks v1 was originally evaluated on)",
            sub,
            "Re-scored against the v2-era teacher labels. v1 model card reported "
            "F1=0.629 against v1-era labels; the new taxonomy means absolute numbers "
            "are not directly comparable, but the model-to-model delta is."
        )

    # ---- per-tradition ----
    print("\n### Per-tradition F1 (v2 model only, on v2-test)")
    print()
    print("| Tradition | n chunks | base F1 | v1 F1 | v2 F1 |")
    print("|---|---:|---:|---:|---:|")
    for tradition, sub in sorted(_by_tradition(cells).items(), key=lambda kv: -len({r['chunk_id'] for r in kv[1]})):
        n_chunks = len({r["chunk_id"] for r in sub})
        m = _metrics(sub)
        row = [tradition, str(n_chunks)]
        for name in ["base", "v1", "v2"]:
            row.append(f"{m[name]['F1']:.3f}" if name in m else "—")
        print("| " + " | ".join(row) + " |")

    # ---- per-concept deltas v1→v2 ----
    gains, regressions = _concept_deltas(cells, "v1", "v2", min_n=args.min_positives)
    print(f"\n### Top 10 v2 gains over v1 (concepts with ≥{args.min_positives} teacher positives)")
    print()
    print("| Concept | n | v1 F1 | v2 F1 | Δ |")
    print("|---|---:|---:|---:|---:|")
    for cid, n, fa, fb, delta in gains:
        print(f"| {cid} | {n} | {fa:.3f} | {fb:.3f} | {delta:+.3f} |")
    print(f"\n### Top 10 v2 regressions vs v1 (concepts with ≥{args.min_positives} teacher positives)")
    print()
    print("| Concept | n | v1 F1 | v2 F1 | Δ |")
    print("|---|---:|---:|---:|---:|")
    for cid, n, fa, fb, delta in regressions:
        print(f"| {cid} | {n} | {fa:.3f} | {fb:.3f} | {delta:+.3f} |")


if __name__ == "__main__":
    main()
