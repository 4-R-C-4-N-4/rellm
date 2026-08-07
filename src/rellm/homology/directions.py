"""Concept directions per (tradition, concept) cell from cached hidden states.

Two construction methods, both computed against the same state slice:

  dom — difference of means with register-matched negatives (the proposal's
        method): positives are the cell's teacher-tagged chunks; negatives are
        same-tradition chunks NOT tagged with the concept, sampled to match
        the positives' distribution over source works (register/style match,
        amendment A6: concept-swapped, teacher labels only).
  cen — cell centroid minus tradition mean (the embedding-baseline analogue,
        kept as the in-model control).

Negative matching is the failure mode (proposal caveat 3) — guard hardest.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from ..config import Config
from ..db import open_db

MIN_N = 10


def load_states(states_dir: Path):
    manifest = json.loads((states_dir / "manifest.json").read_text())
    states = np.load(states_dir / "states.npy", mmap_mode="r")
    row = {cid: i for i, cid in enumerate(manifest["chunk_ids"])}
    return states, manifest, row


def cell_table(cfg: Config, row: dict[str, int]):
    """cells[(trad, concept)] = [row indices]; plus per-tradition rows and works."""
    with open_db(cfg.guru.db) as db:
        trad_of = {r["id"]: r["tradition_id"] for r in db.execute(
            "SELECT id, tradition_id FROM nodes WHERE type='chunk'")}
        tags = db.execute(
            "SELECT e.source_id AS chunk, e.target_id AS concept FROM edges e "
            "JOIN nodes n ON n.id = e.source_id "
            "WHERE e.type='EXPRESSES' AND n.type='chunk'").fetchall()

    work_of = {cid: cid.rsplit(".", 1)[0] for cid in row}  # <trad>.<text_id>
    trad_rows = defaultdict(list)
    for cid, i in row.items():
        t = trad_of.get(cid)
        if t:
            trad_rows[t].append(i)

    cells = defaultdict(list)
    tagged = defaultdict(set)  # (trad, concept) -> set of row idx
    for r in tags:
        cid = r["chunk"]
        if cid in row:
            key = (trad_of[cid], r["concept"])
            cells[key].append(row[cid])
            tagged[key].add(row[cid])

    cells = {k: v for k, v in cells.items() if len(v) >= MIN_N}
    row_work = {i: work_of[cid] for cid, i in row.items()}
    return cells, tagged, dict(trad_rows), row_work


def matched_negatives(pos: list[int], pool: list[int], row_work: dict[int, str],
                      rng: np.random.Generator, per_pos: int = 3) -> list[int]:
    """Sample negatives from `pool` matching the positives' work distribution.

    Works absent from the pool fall back to the tradition-wide remainder, so a
    single-work cell still gets negatives (from other works of that tradition).
    """
    want = Counter(row_work[i] for i in pos)
    by_work = defaultdict(list)
    for i in pool:
        by_work[row_work[i]].append(i)
    neg: list[int] = []
    fallback_quota = 0
    for work, k in want.items():
        avail = by_work.get(work, [])
        take = min(k * per_pos, len(avail))
        if take:
            neg.extend(rng.choice(avail, size=take, replace=False))
        fallback_quota += k * per_pos - take
    if fallback_quota:
        rest = [i for i in pool if i not in set(neg)]
        if rest:
            take = min(fallback_quota, len(rest))
            neg.extend(rng.choice(rest, size=take, replace=False))
    return neg


def build_directions(states_slice: np.ndarray, cells, tagged, trad_rows,
                     row_work, method: str, seed: int = 0) -> dict:
    """directions[(trad, concept)] = unit vector, for one (layer, pooling) slice.

    states_slice: float32 array (n_chunks, dim) — already layer/pooling-indexed.
    """
    rng = np.random.default_rng(seed)
    trad_mean = {t: states_slice[rows].mean(axis=0) for t, rows in trad_rows.items()}
    out = {}
    for (t, c), pos in cells.items():
        p = states_slice[pos].mean(axis=0)
        if method == "cen":
            v = p - trad_mean[t]
        elif method == "dom":
            pool = [i for i in trad_rows[t] if i not in tagged[(t, c)]]
            neg = matched_negatives(pos, pool, row_work, rng)
            if not neg:
                continue
            v = p - states_slice[neg].mean(axis=0)
        else:
            raise ValueError(method)
        n = np.linalg.norm(v)
        if n > 0:
            out[(t, c)] = (v / n).astype(np.float32)
    return out
