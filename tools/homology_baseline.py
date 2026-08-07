#!/usr/bin/env python3
"""Embedding-centroid baseline for the homology gold set (proposal amendment A3).

For each (concept, tradition) cell with n >= MIN_N teacher-tagged chunks,
computes a tradition-centered concept centroid from guru's existing
chunk_embeddings (nomic-embed-text, 768d):

    centroid(C, T) = mean(vec(chunk) for chunk in T tagged C) - mean(vec(chunk) for chunk in T)

then scores every ratified gold pair by cosine between its two centroids,
null-calibrated per tradition pair (amendment A4): the reported percentile is
the gold cosine's rank among cosines of ALL cross-tradition concept pairings
for that same tradition pair.

Metrics against the human 0-4 depth ratings (amendment A9):
  - Spearman rank correlation (cosine and percentile vs rating)
  - tail separation: ratings 0-1 vs 3-4 (rank-sum AUC)
  - band-2 prediction: where the 2s land relative to the tails

Usage: python3 tools/homology_baseline.py
Writes data/homology/baseline/centroid-nomic.json and prints a report.
"""
import json
import sqlite3
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "data" / "homology" / "gold"
OUT = ROOT / "data" / "homology" / "baseline"
DB = "/home/ivy/Work/guru/data/guru.db"
MIN_N = 10


def load_vectors(db):
    rows = db.execute("SELECT chunk_id, vector FROM chunk_embeddings")
    ids, mats = [], []
    for cid, blob in rows:
        ids.append(cid)
        mats.append(np.frombuffer(blob, dtype=np.float32))
    return ids, np.vstack(mats).astype(np.float64)


def main():
    db = sqlite3.connect(DB)
    ids, X = load_vectors(db)
    idx = {c: i for i, c in enumerate(ids)}

    trad_of = dict(db.execute(
        "SELECT id, tradition_id FROM nodes WHERE type='chunk'"))
    tags = db.execute(
        "SELECT e.source_id, e.target_id FROM edges e "
        "JOIN nodes n ON n.id = e.source_id "
        "WHERE e.type='EXPRESSES' AND n.type='chunk'").fetchall()

    # tradition means
    trad_rows = {}
    for cid in ids:
        trad_rows.setdefault(trad_of.get(cid), []).append(idx[cid])
    trad_mean = {t: X[r].mean(axis=0) for t, r in trad_rows.items() if t}

    # cell -> chunk rows
    cell_rows = {}
    for chunk, concept in tags:
        if chunk in idx:
            cell_rows.setdefault((trad_of[chunk], concept), []).append(idx[chunk])

    # centered, normalized centroids for measurable cells
    cent = {}
    for (t, c), rows in cell_rows.items():
        if len(rows) < MIN_N:
            continue
        v = X[rows].mean(axis=0) - trad_mean[t]
        norm = np.linalg.norm(v)
        if norm > 0:
            cent[(t, c)] = v / norm

    gold = [json.loads(l) for l in (GOLD / "ratified.jsonl").read_text().splitlines()]
    gold = [g for g in gold if g["verdict"] != "rejected"]

    # null distributions per tradition pair: cosines of ALL cross concept pairings
    by_trad = {}
    for (t, c) in cent:
        by_trad.setdefault(t, []).append(c)

    def null_cosines(t1, t2):
        A = np.vstack([cent[(t1, c)] for c in by_trad[t1]])
        B = np.vstack([cent[(t2, c)] for c in by_trad[t2]])
        return A @ B.T  # matrix of cosines (unit vectors)

    null_cache = {}
    results = []
    for g in gold:
        a, b = (g["a"]["tradition"], g["a"]["concept"]), (g["b"]["tradition"], g["b"]["concept"])
        if a not in cent or b not in cent:
            results.append({"id": g["id"], "rating": g["verdict"], "cosine": None,
                            "percentile": None, "reason": "cell below floor"})
            continue
        cos = float(cent[a] @ cent[b])
        tp = (a[0], b[0])
        if tp not in null_cache:
            null_cache[tp] = null_cosines(*tp).ravel()
        null = null_cache[tp]
        pct = float((null < cos).mean() * 100)
        results.append({"id": g["id"], "rating": g["verdict"], "cosine": round(cos, 4),
                        "percentile": round(pct, 1)})

    scored = [r for r in results if r["cosine"] is not None]

    def spearman(x, y):
        def rank(v):
            order = np.argsort(v)
            ranks = np.empty(len(v))
            sv = np.array(v)[order]
            i = 0
            while i < len(v):
                j = i
                while j + 1 < len(v) and sv[j + 1] == sv[i]:
                    j += 1
                ranks[order[i:j + 1]] = (i + j) / 2 + 1
                i = j + 1
            return ranks
        rx, ry = rank(x), rank(y)
        rx -= rx.mean(); ry -= ry.mean()
        return float((rx @ ry) / np.sqrt((rx @ rx) * (ry @ ry)))

    ratings = [r["rating"] for r in scored]
    rho_cos = spearman(ratings, [r["cosine"] for r in scored])
    rho_pct = spearman(ratings, [r["percentile"] for r in scored])

    lo = [r["percentile"] for r in scored if r["rating"] <= 1]
    hi = [r["percentile"] for r in scored if r["rating"] >= 3]
    mid = [r["percentile"] for r in scored if r["rating"] == 2]
    # rank-sum AUC: P(random hi > random lo)
    auc = float(np.mean([[h > l for l in lo] for h in hi])) if lo and hi else None

    report = {
        "method": "tradition-centered concept centroids, nomic-embed-text 768d",
        "min_n": MIN_N, "cells": len(cent), "gold_scored": len(scored),
        "gold_skipped": len(results) - len(scored),
        "spearman_rating_vs_cosine": round(rho_cos, 3),
        "spearman_rating_vs_percentile": round(rho_pct, 3),
        "tail_auc_lo01_vs_hi34": round(auc, 3) if auc is not None else None,
        "mean_percentile": {
            "ratings_0_1": round(float(np.mean(lo)), 1) if lo else None,
            "ratings_2": round(float(np.mean(mid)), 1) if mid else None,
            "ratings_3_4": round(float(np.mean(hi)), 1) if hi else None,
        },
        "pairs": sorted(results, key=lambda r: (r["percentile"] is None, -(r["percentile"] or 0))),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "centroid-nomic.json").write_text(json.dumps(report, indent=1))

    print(f"cells with centroids (n>={MIN_N}): {len(cent)}   gold pairs scored: {len(scored)}")
    print(f"Spearman rating~cosine     : {rho_cos:+.3f}")
    print(f"Spearman rating~percentile : {rho_pct:+.3f}")
    print(f"tail AUC (0-1 vs 3-4)      : {auc:.3f}")
    print(f"mean null-percentile  0-1: {np.mean(lo):5.1f}   2: {np.mean(mid):5.1f}   3-4: {np.mean(hi):5.1f}")
    print()
    print(f"{'id':6} {'rating':>6} {'cosine':>8} {'pctile':>7}")
    for r in report["pairs"]:
        if r["cosine"] is None:
            print(f"{r['id']:6} {str(r['rating']):>6} {'--':>8} {'--':>7}  ({r['reason']})")
        else:
            print(f"{r['id']:6} {str(r['rating']):>6} {r['cosine']:8.4f} {r['percentile']:7.1f}")


if __name__ == "__main__":
    main()
