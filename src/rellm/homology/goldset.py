"""Ratified gold set: loading, metrics, and the tune/test split.

The gold verdict is an ordinal 0-4 depth rating (amendment A9). Metrics:
  spearman   — rank correlation of score vs rating (primary)
  tail_auc   — P(score of a 3-4 pair > score of a 0-1 pair)  (go/no-go)
  band means — where the 2s land relative to the tails (held prediction)

Layer/pooling/method selection tunes on the TUNE half only (amendment A5);
the chosen config is then reported on TEST. Split is deterministic and
stratified by rating.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np


def load_gold(path: Path) -> list[dict]:
    gold = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    return [g for g in gold if g["verdict"] != "rejected"]


def split(gold: list[dict]) -> tuple[list[dict], list[dict]]:
    """Deterministic stratified halves: within each rating, alternate by id order."""
    tune, test = [], []
    for rating in sorted({g["verdict"] for g in gold}):
        group = sorted((g for g in gold if g["verdict"] == rating),
                       key=lambda g: g["id"])
        for i, g in enumerate(group):
            (tune if i % 2 == 0 else test).append(g)
    return tune, test


def pair_key(g: dict) -> tuple[tuple[str, str], tuple[str, str]]:
    return ((g["a"]["tradition"], g["a"]["concept"]),
            (g["b"]["tradition"], g["b"]["concept"]))


def spearman(x, y) -> float:
    def rank(v):
        v = np.asarray(v, dtype=float)
        order = np.argsort(v)
        ranks = np.empty(len(v))
        sv = v[order]
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
    denom = np.sqrt((rx @ rx) * (ry @ ry))
    return float((rx @ ry) / denom) if denom else 0.0


def metrics(scored: list[tuple[int, float]]) -> dict:
    """scored: [(rating, score)] with None-scored pairs already dropped."""
    ratings = [r for r, _ in scored]
    scores = [s for _, s in scored]
    lo = [s for r, s in scored if r <= 1]
    hi = [s for r, s in scored if r >= 3]
    mid = [s for r, s in scored if r == 2]
    auc = float(np.mean([[h > l for l in lo] for h in hi])) if lo and hi else None
    return {
        "n": len(scored),
        "spearman": round(spearman(ratings, scores), 3),
        "tail_auc": round(auc, 3) if auc is not None else None,
        "mean_score": {
            "0-1": round(float(np.mean(lo)), 1) if lo else None,
            "2": round(float(np.mean(mid)), 1) if mid else None,
            "3-4": round(float(np.mean(hi)), 1) if hi else None,
        },
    }
