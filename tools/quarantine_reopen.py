#!/usr/bin/env python3
"""Re-open quarantined (concept x tradition) tag cells for guru-review.

Flips the matching *accepted* staged_tags rows back to 'pending' so they
surface in the guru-review queue, stamping the justification with the
quarantine batch and dossier reference. Touches NOTHING else: live edges
stay live until a reject/reassign is applied through the normal review flow
(scripts/review_tags.py retracts edges on apply — that path is unchanged).

    .venv/bin/python tools/quarantine_reopen.py            # dry run
    .venv/bin/python tools/quarantine_reopen.py --execute

A timestamped backup of guru.db is written next to the dossiers before any
mutation. Cells are defined in BATCH below; dossier evidence in
data/quarantine/dossiers.jsonl.
"""
import argparse
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from rellm.config import load

# batch-1 (ruled + applied 2026-08-05): theurgy/finnic, cosmic_dualism/finnic,
# kingdom_within/buddhism, living_god/celtic. Override scope per batch via
# --batch and --cells.
BATCH = "quarantine-batch-1"
CELLS = [
    ("theurgy", "finnic"),
    ("cosmic_dualism", "finnic"),
    ("kingdom_within", "buddhism"),
    ("living_god", "celtic"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true", help="mutate; default is dry run")
    ap.add_argument("--batch", default=BATCH, help="stamp name, e.g. quarantine-batch-2")
    ap.add_argument("--cells", default=None,
                    help="comma-separated concept:tradition pairs; default = batch-1 cells")
    args = ap.parse_args()
    global CELLS
    batch = args.batch
    cells = ([tuple(c.split(":")) for c in args.cells.split(",")]
             if args.cells else CELLS)

    cfg = load()
    qdir = cfg.rellm.root / "data" / "quarantine"
    conn = sqlite3.connect(cfg.guru.db)
    conn.row_factory = sqlite3.Row

    total = 0
    plans = []
    for concept, trad in cells:
        rows = conn.execute(
            """SELECT st.id, st.chunk_id, st.justification FROM staged_tags st
               JOIN nodes n ON n.id = st.chunk_id
               WHERE st.concept_id = ? AND n.tradition_id = ? AND st.status = 'accepted'""",
            (concept, trad)).fetchall()
        # pending-uniqueness collisions: a pending row already exists for the tuple
        collisions = conn.execute(
            """SELECT COUNT(*) FROM staged_tags st
               JOIN nodes n ON n.id = st.chunk_id
               WHERE st.concept_id = ? AND n.tradition_id = ? AND st.status = 'pending'""",
            (concept, trad)).fetchone()[0]
        plans.append((concept, trad, rows, collisions))
        total += len(rows)
        print(f"{concept} x {trad}: {len(rows)} accepted rows to re-open"
              + (f"  (WARNING: {collisions} pending rows already in cell)" if collisions else ""))

    print(f"total: {total} rows")
    if not args.execute:
        print("dry run — pass --execute to apply")
        return

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    backup_path = qdir / f"guru-pre-reopen-{ts}.db"
    bck = sqlite3.connect(backup_path)
    conn.backup(bck)
    bck.close()
    print(f"backup -> {backup_path}")

    stamped = 0
    for concept, trad, rows, _ in plans:
        ref = f"[{batch}: {concept} x {trad} — see rellm data/quarantine/dossiers.jsonl]"
        for r in rows:
            just = (r["justification"] or "").rstrip()
            conn.execute(
                """UPDATE staged_tags
                   SET status='pending', reviewed_by=NULL, reviewed_at=NULL,
                       justification=?
                   WHERE id=? AND status='accepted'""",
                (f"{just} {ref}".strip(), r["id"]))
            stamped += 1
    conn.commit()

    check = conn.execute(
        "SELECT COUNT(*) FROM staged_tags WHERE status='pending' AND justification LIKE ?",
        (f"%{batch}%",)).fetchone()[0]
    print(f"re-opened {stamped} rows; {check} pending rows now carry the {batch} stamp")


if __name__ == "__main__":
    main()
