#!/usr/bin/env python3
"""edge_similarity_backfill.py — recover the retrieval score behind each staged_edge.

propose_edges.py never persisted the vector similarity that triggered a
proposal, so `--min-similarity` has never been tunable against outcomes.
Every chunk embedding is still present (nomic-embed-text, 768d, L2-normalised),
so the score is recoverable after the fact: cosine == dot product.

Writes a `similarity` column into a *snapshot* of guru.db. Refuses to touch
the live guru database — this is analysis scratch, not a source mutation.

Usage:
    python3 tools/edge_similarity_backfill.py                    # latest snapshot
    python3 tools/edge_similarity_backfill.py --snapshot PATH
    python3 tools/edge_similarity_backfill.py --report-only      # no writes
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from rellm.config import load as load_config  # noqa: E402

REVIEWED = ("accepted", "rejected", "reclassified")
POSITIVE = ("PARALLELS", "CONTRASTS")


def latest_snapshot(snapshots_dir: Path) -> Path:
    cands = sorted(d for d in snapshots_dir.iterdir() if d.is_dir())
    if not cands:
        raise SystemExit(f"no snapshots in {snapshots_dir} — run `rellm snapshot` first")
    return cands[-1] / "guru.db"


def guard_not_source(db: Path, cfg) -> None:
    """Hard stop if the target resolves to guru's live database."""
    if db.resolve() == cfg.guru.db.resolve():
        raise SystemExit(
            f"REFUSING to write to the live guru db ({db}).\n"
            f"Run `rellm snapshot` and target the copy."
        )
    try:
        if db.resolve().is_relative_to(cfg.guru.repo.resolve()):
            raise SystemExit(
                f"REFUSING to write inside the guru repo ({db}).\n"
                f"Target a snapshot under {cfg.rellm.snapshots}."
            )
    except AttributeError:  # py<3.9 fallback, not expected here
        pass


def load_embeddings(conn: sqlite3.Connection) -> dict[str, np.ndarray]:
    out: dict[str, np.ndarray] = {}
    for cid, dim, blob in conn.execute(
        "SELECT chunk_id, dim, vector FROM chunk_embeddings"
    ):
        v = np.frombuffer(blob, dtype=np.float32)
        if v.shape[0] != dim:
            continue
        n = np.linalg.norm(v)
        out[cid] = v / n if n > 0 else v
    return out


def ensure_column(conn: sqlite3.Connection) -> None:
    cols = {r[1] for r in conn.execute("PRAGMA table_info(staged_edges)")}
    if "similarity" not in cols:
        conn.execute("ALTER TABLE staged_edges ADD COLUMN similarity REAL")
        print("added staged_edges.similarity")
    else:
        print("staged_edges.similarity already present — recomputing")


def backfill(conn: sqlite3.Connection, emb: dict, write: bool) -> list[tuple]:
    rows = conn.execute(
        "SELECT id, source_chunk, target_chunk, edge_type, status FROM staged_edges"
    ).fetchall()

    updates: list[tuple[float, int]] = []
    scored: list[tuple] = []
    missing = 0

    for eid, src, tgt, etype, status in rows:
        va, vb = emb.get(src), emb.get(tgt)
        if va is None or vb is None:
            missing += 1
            continue
        sim = float(np.dot(va, vb))
        updates.append((sim, eid))
        scored.append((sim, etype, status))

    print(f"edges: {len(rows):,}   scored: {len(updates):,}   "
          f"missing embedding: {missing:,}")

    if write and updates:
        conn.executemany(
            "UPDATE staged_edges SET similarity=? WHERE id=?", updates
        )
        conn.commit()
        print(f"wrote similarity for {len(updates):,} rows")

    return scored


def report(scored: list[tuple]) -> None:
    """Does retrieval similarity predict the post-review verdict?"""
    rev = [(s, e) for s, e, st in scored if st in REVIEWED]
    if not rev:
        print("no reviewed rows to analyse")
        return

    sims = np.array([s for s, _ in rev])
    pos = np.array([e in POSITIVE for _, e in rev])

    print(f"\n{'=' * 78}\nSIMILARITY vs OUTCOME  (n={len(rev):,} reviewed)\n{'=' * 78}")
    print(f"accepted   mean sim {sims[pos].mean():.4f}  sd {sims[pos].std():.4f}  n {pos.sum():,}")
    print(f"rejected   mean sim {sims[~pos].mean():.4f}  sd {sims[~pos].std():.4f}  n {(~pos).sum():,}")
    print(f"separation {sims[pos].mean() - sims[~pos].mean():+.4f}")

    # Point-biserial correlation == Pearson r with a 0/1 variable.
    r = float(np.corrcoef(sims, pos.astype(float))[0, 1])
    print(f"point-biserial r = {r:+.4f}")

    # AUC via the Mann-Whitney U identity — the probability that a random
    # accepted pair scores above a random rejected one.
    order = sims.argsort()
    ranks = np.empty_like(order, dtype=float)
    ranks[order] = np.arange(1, len(sims) + 1)
    n1, n0 = int(pos.sum()), int((~pos).sum())
    auc = (ranks[pos].sum() - n1 * (n1 + 1) / 2) / (n1 * n0) if n1 and n0 else float("nan")
    print(f"AUC(similarity -> accept) = {auc:.4f}   "
          f"({'no better than chance' if abs(auc - 0.5) < 0.03 else 'some signal'})")

    print(f"\n{'bucket':<16}{'n':>8}{'accepted':>10}{'accept_rate':>13}")
    print("-" * 78)
    edges = [0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.01]
    for lo, hi in zip(edges, edges[1:]):
        m = (sims >= lo) & (sims < hi)
        if not m.any():
            continue
        print(f"{f'[{lo:.2f},{hi:.2f})':<16}{int(m.sum()):>8}"
              f"{int(pos[m].sum()):>10}{pos[m].mean():>13.3f}")
    below = sims < edges[0]
    if below.any():
        print(f"{f'< {edges[0]:.2f}':<16}{int(below.sum()):>8}"
              f"{int(pos[below].sum()):>10}{pos[below].mean():>13.3f}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--snapshot", type=Path, help="snapshot dir or guru.db path")
    ap.add_argument("--report-only", action="store_true", help="analyse without writing")
    args = ap.parse_args()

    cfg = load_config()
    if args.snapshot:
        db = args.snapshot / "guru.db" if args.snapshot.is_dir() else args.snapshot
    else:
        db = latest_snapshot(cfg.rellm.snapshots)

    guard_not_source(db, cfg)
    print(f"snapshot: {db}")

    conn = sqlite3.connect(str(db))
    if not args.report_only:
        ensure_column(conn)
    emb = load_embeddings(conn)
    print(f"embeddings loaded: {len(emb):,}")

    scored = backfill(conn, emb, write=not args.report_only)
    report(scored)
    conn.close()


if __name__ == "__main__":
    main()
