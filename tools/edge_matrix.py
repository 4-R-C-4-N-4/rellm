#!/usr/bin/env python3
"""edge_matrix.py — cross-tradition edge outcome matrix from guru.db.

Aggregates staged_edges by tradition-pair and text-pair, reporting the
post-review outcome distribution and an accept rate with a Wilson lower
bound (the "confidence" on the rate — small-n cells are not trustworthy
and the bound makes that explicit rather than letting 1/1 = 100% read as
signal).

Post-review truth: review_edges.py rewrites edge_type on reclassify, and
every rejection in the store went through the reclassify path, so
edge_type on a reviewed row IS the corrected label.

Usage:
    python3 tools/edge_matrix.py                        # summary to stdout
    python3 tools/edge_matrix.py --out runs/edges/      # + TSV exports
    python3 tools/edge_matrix.py --min-n 20             # hide thin cells
"""
from __future__ import annotations

import argparse
import math
import sqlite3
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from rellm.config import load as load_config  # noqa: E402

REVIEWED = ("accepted", "rejected", "reclassified")
POSITIVE = ("PARALLELS", "CONTRASTS")
NEGATIVE = ("surface_only", "unrelated")


def latest_snapshot(snapshots_dir: Path) -> Path:
    """Default to the newest snapshot — the live guru.db is a prod artifact and
    these tools should not depend on its current state."""
    cands = sorted(d for d in snapshots_dir.iterdir() if d.is_dir())
    if not cands:
        raise SystemExit(f"no snapshots in {snapshots_dir} — run `rellm snapshot` first")
    return cands[-1] / "guru.db"


def wilson_lower(k: int, n: int, z: float = 1.96) -> float:
    """Lower bound of the Wilson score interval for k successes in n trials.

    Used as a rank key so a 1/1 cell doesn't outrank a 900/1000 cell.
    """
    if n == 0:
        return 0.0
    p = k / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    return max(0.0, (centre - margin) / denom)


@dataclass
class Cell:
    """Outcome tallies for one unordered pair (traditions or texts)."""

    parallels: int = 0
    contrasts: int = 0
    surface_only: int = 0
    unrelated: int = 0
    pending: int = 0
    confidences: list[float] = field(default_factory=list)

    @property
    def accepted(self) -> int:
        return self.parallels + self.contrasts

    @property
    def rejected(self) -> int:
        return self.surface_only + self.unrelated

    @property
    def reviewed(self) -> int:
        return self.accepted + self.rejected

    @property
    def accept_rate(self) -> float:
        return self.accepted / self.reviewed if self.reviewed else 0.0

    @property
    def rate_lower(self) -> float:
        return wilson_lower(self.accepted, self.reviewed)

    @property
    def mean_conf(self) -> float:
        return sum(self.confidences) / len(self.confidences) if self.confidences else 0.0


def split_chunk_id(chunk_id: str) -> tuple[str, str]:
    """'<tradition>.<text_id>.<seq>' -> (tradition, text_id)."""
    parts = chunk_id.split(".", 2)
    if len(parts) < 3:
        return (chunk_id, chunk_id)
    return (parts[0], parts[1])


def unordered(a: str, b: str) -> tuple[str, str]:
    return (a, b) if a <= b else (b, a)


def build(conn: sqlite3.Connection) -> tuple[dict, dict, dict]:
    """Return (tradition_cells, text_cells, totals)."""
    rows = conn.execute(
        """
        SELECT se.source_chunk, se.target_chunk, se.edge_type,
               se.status, se.confidence,
               ns.tradition_id AS src_trad, nt.tradition_id AS tgt_trad
        FROM staged_edges se
        LEFT JOIN nodes ns ON ns.id = se.source_chunk
        LEFT JOIN nodes nt ON nt.id = se.target_chunk
        """
    ).fetchall()

    trad: dict[tuple[str, str], Cell] = defaultdict(Cell)
    text: dict[tuple[str, str], Cell] = defaultdict(Cell)
    totals = Cell()

    for r in rows:
        src_trad = r["src_trad"] or split_chunk_id(r["source_chunk"])[0]
        tgt_trad = r["tgt_trad"] or split_chunk_id(r["target_chunk"])[0]
        src_text = f"{src_trad}/{split_chunk_id(r['source_chunk'])[1]}"
        tgt_text = f"{tgt_trad}/{split_chunk_id(r['target_chunk'])[1]}"

        tkey = unordered(src_trad, tgt_trad)
        xkey = unordered(src_text, tgt_text)

        for cell in (trad[tkey], text[xkey], totals):
            if r["status"] == "pending":
                cell.pending += 1
            elif r["status"] in REVIEWED:
                attr = {
                    "PARALLELS": "parallels",
                    "CONTRASTS": "contrasts",
                    "surface_only": "surface_only",
                    "unrelated": "unrelated",
                }.get(r["edge_type"])
                if attr:
                    setattr(cell, attr, getattr(cell, attr) + 1)
                # reviewed rows only — every other column in the table excludes
                # pending, so folding 2,058 unjudged proposals into the mean
                # would make this column mean something different from its
                # neighbours.
                if r["confidence"] is not None:
                    cell.confidences.append(r["confidence"])


    return trad, text, totals


HEADERS = [
    "pair", "reviewed", "accepted", "rejected",
    "accept_rate", "rate_lower95", "pending", "mean_conf",
]


def rows_for(cells: dict, min_n: int) -> list[list]:
    out = []
    for (a, b), c in cells.items():
        if c.reviewed < min_n:
            continue
        out.append([
            f"{a} <-> {b}", c.reviewed, c.accepted, c.rejected,
            round(c.accept_rate, 4), round(c.rate_lower, 4),
            c.pending, round(c.mean_conf, 4),
        ])
    out.sort(key=lambda r: -r[1])
    return out


def print_table(title: str, rows: list[list], limit: int) -> None:
    print(f"\n{'=' * 100}\n{title}\n{'=' * 100}")
    print(f"{'pair':<58}{'n':>7}{'acc':>7}{'rej':>7}{'rate':>8}{'lo95':>8}{'pend':>7}")
    print("-" * 100)
    for r in rows[:limit]:
        print(f"{r[0]:<58}{r[1]:>7}{r[2]:>7}{r[3]:>7}"
              f"{r[4]:>8.3f}{r[5]:>8.3f}{r[6]:>7}")
    if len(rows) > limit:
        print(f"... {len(rows) - limit} more rows (see TSV export)")


def write_tsv(path: Path, rows: list[list]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        f.write("\t".join(HEADERS) + "\n")
        for r in rows:
            f.write("\t".join(str(x) for x in r) + "\n")
    print(f"wrote {path}  ({len(rows)} rows)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", help="guru.db path; default is the latest snapshot")
    ap.add_argument("--out", type=Path, help="directory for TSV exports")
    ap.add_argument("--min-n", type=int, default=1,
                    help="hide pairs with fewer than N reviewed edges")
    ap.add_argument("--limit", type=int, default=40, help="rows printed per table")
    args = ap.parse_args()

    cfg = load_config()
    db = args.db or latest_snapshot(cfg.rellm.snapshots)
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    trad, text, totals = build(conn)

    print(f"db: {db}")
    print(f"\nreviewed: {totals.reviewed:,}   "
          f"accepted: {totals.accepted:,} ({totals.accept_rate:.1%})   "
          f"rejected: {totals.rejected:,}   pending: {totals.pending:,}")
    print(f"  PARALLELS {totals.parallels:,}  CONTRASTS {totals.contrasts:,}  "
          f"surface_only {totals.surface_only:,}  unrelated {totals.unrelated:,}")
    print(f"tradition pairs: {len(trad):,}    text pairs: {len(text):,}")

    trad_rows = rows_for(trad, args.min_n)
    text_rows = rows_for(text, args.min_n)

    print_table("TRADITION x TRADITION", trad_rows, args.limit)
    print_table("TEXT x TEXT", text_rows, args.limit)

    # Worst cells by accept rate, among those with enough volume to trust.
    noisy = [r for r in trad_rows if r[1] >= 30]
    noisy.sort(key=lambda r: r[4])
    print_table("NOISIEST TRADITION PAIRS (n>=30, lowest accept rate)", noisy, 20)

    if args.out:
        write_tsv(args.out / "edge_matrix_tradition.tsv", trad_rows)
        write_tsv(args.out / "edge_matrix_text.tsv", text_rows)

    conn.close()


if __name__ == "__main__":
    main()
