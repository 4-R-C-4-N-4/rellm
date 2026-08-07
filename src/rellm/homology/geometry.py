"""Scoring over a direction set: cosine + per-tradition-pair null calibration.

Raw residual-stream cosines are anisotropy-inflated (amendment A4); every
reported score is the percentile of the pair's cosine within the null
distribution of ALL cross-tradition concept pairings for the same tradition
pair. Cosine is evidence, not definition — the percentile is the honest unit.
"""
from __future__ import annotations

from collections import defaultdict

import numpy as np


class Scorer:
    def __init__(self, directions: dict):
        self.dirs = directions
        self.by_trad = defaultdict(list)
        for (t, c) in directions:
            self.by_trad[t].append(c)
        self._null = {}

    def cosine(self, a: tuple[str, str], b: tuple[str, str]) -> float | None:
        if a not in self.dirs or b not in self.dirs:
            return None
        return float(self.dirs[a] @ self.dirs[b])

    def _null_dist(self, t1: str, t2: str) -> np.ndarray:
        key = (t1, t2)
        if key not in self._null:
            A = np.vstack([self.dirs[(t1, c)] for c in self.by_trad[t1]])
            B = np.vstack([self.dirs[(t2, c)] for c in self.by_trad[t2]])
            self._null[key] = (A @ B.T).ravel()
        return self._null[key]

    def percentile(self, a: tuple[str, str], b: tuple[str, str]) -> float | None:
        cos = self.cosine(a, b)
        if cos is None:
            return None
        null = self._null_dist(a[0], b[0])
        return float((null < cos).mean() * 100)
