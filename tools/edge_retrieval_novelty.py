#!/usr/bin/env python3
"""edge_retrieval_novelty.py — do chunk↔chunk edges earn a place in retrieval?

v2. The first version of this measurement ran against a baseline that was
missing two of production's four legs (lexical, summary) and whose concept
matcher silently resolved family-level queries ("cosmology", "soteriology")
to nothing. Every number it produced overstated the edge leg's contribution —
the queries where edges appeared to add traditions were exactly the queries
where the concept leg was dead. guru PR #60 brought the sqlite retriever to
guru-web parity; this measures against that.

Three questions, per golden query:

  reach        Edge partners' position in the vector ranking — is this
               material a wider top-k would find anyway?
  redundancy   How many partners the full four-leg pipeline already surfaces,
               in its final top-K and in its candidate pool.
  displacement Run the retriever with EDGE_LEG=on vs off: under production's
               additive scoring, do edge chunks actually enter the final
               top-K, and what do they push out? An edge chunk arrives with
               similarity 0 and no lexical hit, so its whole score is the
               graph term + diversity — this is the leg's realistic ceiling
               inside the current scorer, as opposed to its candidate count.

Baseline is guru's parity retriever (vector + concept + lexical + summary,
EDGE_LEG=off) over the live workbench DB. Read-only apart from the FTS
sidecar the retriever itself maintains.

Usage:
    python3 tools/edge_retrieval_novelty.py
    python3 tools/edge_retrieval_novelty.py --top-k 15 --json out.json
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import urllib.request
from pathlib import Path

import numpy as np

RELLM_ROOT = Path(__file__).parent.parent
GURU_ROOT = RELLM_ROOT.parent / "guru"
sys.path.insert(0, str(RELLM_ROOT / "src"))
sys.path.insert(0, str(GURU_ROOT))

from rellm.config import load as load_config          # noqa: E402

OLLAMA = "http://localhost:11434/api/embed"
EMBED_MODEL = "nomic-embed-text:v1.5"


def embed(text: str) -> list[float]:
    payload = json.dumps({"model": EMBED_MODEL, "input": text}).encode()
    req = urllib.request.Request(OLLAMA, data=payload,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())["embeddings"][0]


def load_vectors(conn):
    rows = conn.execute(
        "SELECT ce.chunk_id, ce.vector, n.tradition_id "
        "FROM chunk_embeddings ce JOIN nodes n ON n.id = ce.chunk_id "
        "WHERE n.type='chunk' ORDER BY ce.chunk_id").fetchall()
    ids = [r[0] for r in rows]
    trad = {r[0]: (r[2] or r[0].split(".")[0]) for r in rows}
    M = np.stack([np.frombuffer(r[1], dtype=np.float32) for r in rows])
    M = M / np.linalg.norm(M, axis=1, keepdims=True)
    return ids, trad, M


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--top-k", type=int, default=15)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()

    os.chdir(GURU_ROOT)   # guru paths resolve relative to its repo root
    from guru.preferences import UserPreferences        # noqa: E402
    from guru.retriever import HybridRetriever          # noqa: E402
    from guru import retrieval_legs as legs             # noqa: E402

    cfg = load_config(RELLM_ROOT / "rellm.toml")
    conn = sqlite3.connect(f"file:{GURU_ROOT/'data'/'guru.db'}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    ids, trad, M = load_vectors(conn)
    vrank_cache: dict[str, dict[str, int]] = {}

    gold = json.loads((GURU_ROOT.parent / "guru-web" / "src" / "__tests__"
                       / "fixtures" / "golden-retrieval.json").read_text())
    queries = [dict(q) for q in gold["queries"]]
    for g in gold.get("knownGaps", {}).get("cases", []):
        queries.append({"query": g["query"], "gap": g["expectedTradition"]})

    retriever = HybridRetriever()
    prefs = UserPreferences.allow_all()
    print(f"baseline: guru parity retriever (PR #60), four legs, EDGE_LEG=off")
    print(f"chunks {len(ids):,}   queries {len(queries)}   top-k {args.top_k}\n")

    rows = []
    for q in queries:
        qe = embed(q["query"])
        sims = M @ (np.asarray(qe, dtype=np.float32)
                    / np.linalg.norm(qe))
        order = np.argsort(-sims)
        vrank = {ids[j]: r for r, j in enumerate(order, start=1)}

        os.environ.pop("EDGE_LEG", None)
        base = retriever.retrieve(q["query"], qe, prefs, top_k=args.top_k)
        base_ids = [c.chunk_id for c in base]
        base_trads = {c.tradition for c in base}

        # candidate pool the baseline already considers (vector 2k + concept +
        # lexical + summary) — partners inside it are redundant even when they
        # miss the final top-K.
        pool = {ids[j] for j in order[:args.top_k * 2]}
        pool |= {h["chunk_id"] for h in retriever._graph_walk(q["query"], prefs, conn)}
        pool |= set(legs.lexical_search(conn, q["query"], args.top_k * 2))

        anchors = pool | set(base_ids)
        os.environ["EDGE_LEG"] = "on"
        partners = {h["chunk_id"] for h in legs.edge_partners(conn, anchors)}
        edge_on = retriever.retrieve(q["query"], qe, prefs, top_k=args.top_k)
        os.environ.pop("EDGE_LEG", None)
        on_ids = [c.chunk_id for c in edge_on]

        displaced = [c for c in base_ids if c not in on_ids]
        entered = [c for c in on_ids if c not in base_ids and c in partners]

        # NOTE: partners are disjoint from the anchor pool BY CONSTRUCTION
        # (edge_partners never emits a chunk already in anchors), so
        # "partners already in the pool" is definitionally zero and not a
        # metric. Redundancy is answered by the rank distribution instead.
        ranks = sorted(vrank[c] for c in partners if c in vrank)
        rows.append({
            "query": q["query"], "gap": q.get("gap"),
            "partners": len(partners),
            "rank_median": ranks[len(ranks) // 2] if ranks else 0,
            "within_top200": sum(r <= 200 for r in ranks),
            "new_traditions": sorted({trad[c] for c in partners if c in trad}
                                     - base_trads),
            "edge_entered_topk": entered,
            "edge_displaced": displaced,
            "gap_in_baseline": (q.get("gap") in base_trads if q.get("gap") else None),
            "gap_in_partners": (q.get("gap") in {trad[c] for c in partners if c in trad}
                                if q.get("gap") else None),
        })

    # ── report ──────────────────────────────────────────────────────────────
    tp = sum(r["partners"] for r in rows)
    print(f"edge candidates: {tp:,} total, {tp/len(rows):.0f}/query "
          f"(disjoint from the candidate pool by construction)")
    med = sorted(r["rank_median"] for r in rows)[len(rows) // 2]
    t200 = sum(r["within_top200"] for r in rows)
    print(f"  median partner vector rank {med:,} of {len(ids):,}   "
          f"within vector top-200: {t200:,} ({t200/tp:.1%})")
    ent = sum(len(r["edge_entered_topk"]) for r in rows)
    print(f"\ndisplacement under production scoring (EDGE_LEG on vs off):")
    print(f"  edge chunks entering final top-{args.top_k}, all queries: {ent}")

    print(f"\n  {'query':<48}{'cands':>7}{'t200':>7}{'med-rk':>8}{'+trad':>7}{'enter':>7}")
    for r in rows:
        print(f"  {r['query'][:46]:<48}{r['partners']:>7}{r['within_top200']:>7}"
              f"{r['rank_median']:>8}{len(r['new_traditions']):>7}"
              f"{len(r['edge_entered_topk']):>7}")

    print("\nknownGaps — expected tradition present?")
    for r in rows:
        if r["gap"]:
            print(f"  {r['query'][:44]:<46} {r['gap']:<16} "
                  f"baseline: {'YES' if r['gap_in_baseline'] else 'no ':<4} "
                  f"edge partners: {'YES' if r['gap_in_partners'] else 'no'}")

    if args.json:
        args.json.write_text(json.dumps(rows, indent=2))
        print(f"\nwrote {args.json}")


if __name__ == "__main__":
    main()
