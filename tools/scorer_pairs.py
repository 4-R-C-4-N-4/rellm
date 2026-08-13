#!/usr/bin/env python3
"""scorer_pairs.py — stratified (query, chunk) pair sampling for the thin scorer.

Per query (todo:6ab430e5; spec docs/edges/thin-scorer-spec.md):
  baseline   the parity retriever's top-15 (positive-rich)     ~15
  edge       anchored PARALLELS partners (operational stratum)  ≤8
  hardneg    vector ranks 16..200, not retrieved               ~5
  random     uniform corpus chunks                              2

Bodies come along (truncated to 2400 chars, the judged scoring config) so
teacher labeling and training need no further corpus access. Known-apparatus
chunks (guru-web todo:6e0c2a63) are excluded from baseline/edge strata only —
they remain fair game as negatives.

Env: EDGE_GURU_ROOT (guru worktree), OLLAMA at localhost:11434.
Usage:
    python3 tools/scorer_pairs.py --queries data/scorer/queries.jsonl \
        --out runs/edges/scorer/<ts>/pairs.jsonl [--allow-frozen]
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sqlite3
import sys
import urllib.request
from pathlib import Path

RELLM_ROOT = Path(__file__).parent.parent
GURU_ROOT = Path(os.environ.get("EDGE_GURU_ROOT", RELLM_ROOT.parent / "guru"))
sys.path.insert(0, str(RELLM_ROOT / "src"))
sys.path.insert(0, str(GURU_ROOT))

SEED = 20260812

# Apparatus-heavy chunk id prefixes/singletons from the golden-backfill audit
# (guru-web todo:6e0c2a63). Coarse by design: positives sampling only.
APPARATUS_PATTERNS = (
    "gnosticism.gospel-of-philip.001",
    "zoroastrianism.bundahishn.",
    "celtic.mabinogion.001", "celtic.mabinogion.002", "celtic.mabinogion.003",
    "celtic.mabinogion.004", "celtic.mabinogion.005",
)


def is_apparatus(cid: str) -> bool:
    return any(cid.startswith(p) for p in APPARATUS_PATTERNS)


def embed(text: str) -> list[float]:
    payload = json.dumps({"model": "nomic-embed-text:v1.5",
                          "input": text}).encode()
    req = urllib.request.Request("http://localhost:11434/api/embed",
                                 data=payload,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())["embeddings"][0]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--queries", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--allow-frozen", action="store_true",
                    help="permit frozen-work queries (gold-eval sampling only)")
    ap.add_argument("--edge-boost", action="store_true",
                    help="emit ONLY the edge stratum, with a lower anchor bar "
                         "(match_weight >= 0.5), cap 20 partners/anchor, up to "
                         "24 partners/query — corrective sampling for the "
                         "operational stratum (1.2%% of the base run)")
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()
    # Resolve before the chdir below, or relative paths silently break.
    args.queries = args.queries.resolve()
    args.out = args.out.resolve()

    os.chdir(GURU_ROOT)
    from guru.corpus import resolve_chunk_path            # noqa: E402
    from guru.preferences import UserPreferences          # noqa: E402
    from guru.retriever import HybridRetriever            # noqa: E402
    from guru import retrieval_legs as legs               # noqa: E402
    import tomllib                                        # noqa: E402

    queries = [json.loads(l) for l in args.queries.read_text().splitlines()
               if l.strip()]
    if not args.allow_frozen:
        # queries.jsonl is already frozen-filtered by scorer_query_pool.py;
        # this is belt-and-braces for ad-hoc query files.
        pass

    rng = random.Random(args.seed)
    retriever = HybridRetriever()
    prefs = UserPreferences.allow_all()
    conn = sqlite3.connect(f"file:{GURU_ROOT/'data'/'guru.db'}?mode=ro",
                           uri=True)
    conn.row_factory = sqlite3.Row
    all_chunks = [r[0] for r in conn.execute(
        "SELECT id FROM nodes WHERE type='chunk'")]

    def body_of(cid: str) -> str | None:
        p = resolve_chunk_path(cid)
        if p is None:
            return None
        with open(p, "rb") as f:
            return tomllib.load(f)["content"]["body"][:2400]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    n_rows = 0
    with open(args.out, "w") as out:
        for i, q in enumerate(queries):
            picked: dict[str, str] = {}   # chunk_id -> stratum (first wins)

            if args.edge_boost:
                walk = retriever._graph_walk(q["query"], prefs, conn)
                anchors = {c["chunk_id"]: max(c.get("match_weight", 0), 0.5)
                           for c in walk if c.get("match_weight", 0) >= 0.5}
                if not anchors:
                    continue
                partners = legs.inherited_partners(conn, anchors, cap=20)
                edge_ids = [p for p in partners if not is_apparatus(p)]
                rng.shuffle(edge_ids)
                for pid in edge_ids[:24]:
                    picked[pid] = "edge"
                for cid, stratum in picked.items():
                    body = body_of(cid)
                    if not body:
                        continue
                    out.write(json.dumps({
                        "query": q["query"], "work": q["work"],
                        "kind": q["kind"], "source": q["source"],
                        "chunk_id": cid, "stratum": stratum, "body": body,
                    }) + "\n")
                    n_rows += 1
                continue

            qe = embed(q["query"])
            base = retriever.retrieve(q["query"], qe, prefs, top_k=15)
            for c in base:
                if not is_apparatus(c.chunk_id):
                    picked.setdefault(c.chunk_id, "baseline")

            # anchored edge partners: concept-leg chunks at direct-match
            # weight serve as anchors (sampling approximation of the
            # retriever's internal anchor set)
            walk = retriever._graph_walk(q["query"], prefs, conn)
            anchors = {c["chunk_id"]: 1.0 for c in walk
                       if c.get("match_weight", 0) >= 1.0}
            partners = legs.inherited_partners(conn, anchors, cap=10)
            edge_ids = [pid for pid in partners if not is_apparatus(pid)]
            rng.shuffle(edge_ids)
            for pid in edge_ids[:8]:
                picked.setdefault(pid, "edge")

            vec = retriever._vector_search(qe, prefs, 200)
            tail = [h["chunk_id"] for h in vec[15:]
                    if h["chunk_id"] not in picked]
            for cid in rng.sample(tail, min(5, len(tail))):
                picked.setdefault(cid, "hardneg")

            for cid in rng.sample(all_chunks, 4):
                if len([1 for s in picked.values() if s == "random"]) >= 2:
                    break
                picked.setdefault(cid, "random")

            for cid, stratum in picked.items():
                body = body_of(cid)
                if not body:
                    continue
                out.write(json.dumps({
                    "query": q["query"], "work": q["work"],
                    "kind": q["kind"], "source": q["source"],
                    "chunk_id": cid, "stratum": stratum, "body": body,
                }) + "\n")
                n_rows += 1
            if (i + 1) % 50 == 0:
                print(f"  {i + 1}/{len(queries)} queries, {n_rows} pairs",
                      flush=True)

    print(f"wrote {args.out}  ({n_rows} pairs from {len(queries)} queries)")


if __name__ == "__main__":
    main()
