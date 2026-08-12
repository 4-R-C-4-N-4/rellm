#!/usr/bin/env python3
"""edge_retrieval_novelty.py — do chunk↔chunk edges reach anything retrieval misses?

The cheapest decisive question about the edge graph, and it needs no relevance
judgments at all.

Chunk↔chunk PARALLELS edges are not query-addressable: unlike concepts, a query
cannot match them directly. They can only be traversed *from a chunk another leg
already retrieved*, so their entire value proposition is second-order — given
the other legs found X, does X's partner add something they missed? If most
partners were already retrieved, the edge leg is redundant and no amount of edge
quality changes that.

This measures exactly that, against guru-web's golden query set.

Deliberately generous to edges:
  - the baseline is guru's vector + concept legs only. guru-web's production
    retriever also runs lexical and summary legs, so the real baseline is wider
    and the real novelty lower than reported here.
  - novelty is reported against several baseline widths, since a narrow
    baseline flatters the edge leg.
  - concept matching mirrors guru/retriever.py's substring matcher, which is
    cruder than guru-web's alias/family expansion — again widening the gap the
    edge leg gets to fill.

Read-only: snapshot + corpus + ollama for query embeddings. Writes nothing to
guru.

Usage:
    python3 tools/edge_retrieval_novelty.py
    python3 tools/edge_retrieval_novelty.py --top-k 15 --json out.json
"""
from __future__ import annotations

import argparse
import collections
import json
import sqlite3
import sys
import tomllib
import urllib.request
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

from rellm.config import load as load_config              # noqa: E402
from edge_band_eval_set import latest_snapshot            # noqa: E402

OLLAMA = "http://localhost:11434/api/embed"
EMBED_MODEL = "nomic-embed-text:v1.5"
CONCEPT_MIN_WORD_LEN = 5          # mirrors guru's _concept_min_word_len default


def embed(text: str) -> np.ndarray:
    payload = json.dumps({"model": EMBED_MODEL, "input": text}).encode()
    req = urllib.request.Request(OLLAMA, data=payload,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        v = np.array(json.loads(r.read())["embeddings"][0], dtype=np.float32)
    return v / np.linalg.norm(v)


def load_state(conn):
    rows = conn.execute(
        "SELECT ce.chunk_id, ce.vector, n.tradition_id "
        "FROM chunk_embeddings ce JOIN nodes n ON n.id = ce.chunk_id "
        "WHERE n.type='chunk' ORDER BY ce.chunk_id").fetchall()
    ids = [r[0] for r in rows]
    trad = {r[0]: (r[2] or r[0].split(".")[0]) for r in rows}
    M = np.stack([np.frombuffer(r[1], dtype=np.float32) for r in rows])
    M = M / np.linalg.norm(M, axis=1, keepdims=True)
    return ids, trad, M


def concept_ids(conn) -> list[str]:
    """Concept node ids straight from the snapshot — authoritative for what the
    retriever can actually walk, and immune to the taxonomy TOML's nesting."""
    return [r[0] for r in conn.execute(
        "SELECT id FROM nodes WHERE type='concept'")]


def concept_chunks(conn, query: str, concepts: list[str]) -> set[str]:
    """guru/retriever.py:_graph_walk, EXPRESSES half — concept → chunks.

    guru-web additionally expands through concept aliases and family/domain
    tiers, so this under-counts the real concept leg — which makes the edge
    leg look better here than it would in production.
    """
    q = query.lower()
    matched = [full for full in concepts
               for cid in [full.removeprefix("concept.")]
               if cid.replace("_", " ") in q
               or any(w in q for w in cid.split("_") if len(w) >= CONCEPT_MIN_WORD_LEN)]
    if not matched:
        return set()
    ph = ",".join("?" for _ in matched)
    return {r[0] for r in conn.execute(
        f"SELECT source_id FROM edges WHERE type='EXPRESSES' AND target_id IN ({ph})",
        matched)}


def edge_partners(conn, anchors: set[str], trad: dict) -> dict[str, set[str]]:
    """Cross-tradition partners reachable by one chunk↔chunk PARALLELS/CONTRASTS
    hop, mirroring guru/retriever.py's partner-emission rule."""
    if not anchors:
        return {}
    out: dict[str, set[str]] = collections.defaultdict(set)
    anchors = list(anchors)
    for i in range(0, len(anchors), 400):
        batch = anchors[i:i + 400]
        ph = ",".join("?" for _ in batch)
        for src, tgt in conn.execute(
            f"SELECT source_id, target_id FROM edges "
            f"WHERE type IN ('PARALLELS','CONTRASTS') "
            f"AND (source_id IN ({ph}) OR target_id IN ({ph}))", batch + batch):
            for anchor, partner in ((src, tgt), (tgt, src)):
                if anchor in anchors and partner not in anchors:
                    if trad.get(partner) and trad.get(partner) != trad.get(anchor):
                        out[partner].add(anchor)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--top-k", type=int, default=15)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()

    cfg = load_config()
    snap = latest_snapshot(cfg.rellm.snapshots)
    conn = sqlite3.connect(f"file:{snap/'guru.db'}?mode=ro", uri=True)
    ids, trad, M = load_state(conn)
    idx = {c: i for i, c in enumerate(ids)}

    concepts = concept_ids(conn)

    gold_path = (cfg.guru.repo.parent / "guru-web" / "src" / "__tests__"
                 / "fixtures" / "golden-retrieval.json")
    gold = json.loads(gold_path.read_text())
    queries = gold["queries"]
    gaps = gold.get("knownGaps", {}).get("cases", [])
    print(f"snapshot {snap.name}   chunks {len(ids):,}   "
          f"golden queries {len(queries)}   knownGaps {len(gaps)}")
    print(f"top-k {args.top_k}\n")

    rows = []
    for q in queries + [{"query": g["query"], "gap": g["expectedTradition"]} for g in gaps]:
        qe = embed(q["query"])
        sims = M @ qe
        order = np.argsort(-sims)
        vrank = {ids[j]: r for r, j in enumerate(order, start=1)}
        vec_2k = {ids[j] for j in order[:args.top_k * 2]}
        cc = concept_chunks(conn, q["query"], concepts)
        base = vec_2k | cc

        partners = edge_partners(conn, base, trad)
        ranks = sorted(vrank[c] for c in partners if c in vrank)
        base_tr = {trad[c] for c in base if c in trad}
        new_tr = {trad[c] for c in partners if c in trad} - base_tr

        def pct(p):
            return ranks[int(len(ranks) * p)] if ranks else 0
        rows.append({
            "query": q["query"], "concept_hits": len(cc), "baseline_n": len(base),
            "partners": len(partners),
            "rank_p25": pct(0.25), "rank_median": pct(0.50), "rank_p75": pct(0.75),
            "within_top50": sum(r <= 50 for r in ranks),
            "within_top200": sum(r <= 200 for r in ranks),
            "new_traditions": sorted(new_tr),
            "gap": q.get("gap"),
            "gap_reached": (q.get("gap") in {trad[c] for c in partners if c in trad}
                            if q.get("gap") else None),
        })

    # ── report ──────────────────────────────────────────────────────────────
    N = len(ids)
    tot_p = sum(r["partners"] for r in rows)
    t50 = sum(r["within_top50"] for r in rows)
    t200 = sum(r["within_top200"] for r in rows)
    print(f"edge-leg candidates across {len(rows)} queries: {tot_p:,} "
          f"({tot_p/len(rows):.0f} per query, for a top-{args.top_k} result set)")
    print(f"  already within vector top-50:  {t50:,} ({t50/tot_p:.1%})")
    print(f"  already within vector top-200: {t200:,} ({t200/tot_p:.1%})")
    med = sorted(r["rank_median"] for r in rows)[len(rows)//2]
    print(f"  median partner sits at vector rank {med:,} of {N:,}")
    print("\n  Partners deep in the vector ranking are material vector cannot reach —")
    print("  genuine novel reach. Partners near the top are material a wider top-k")
    print("  would have found anyway, without maintaining an edge graph.\n")

    print(f"  {'query':<46}{'conc':>5}{'cands':>7}{'p25':>7}{'med':>7}{'p75':>7}{'+trad':>7}")
    for r in rows:
        print(f"  {r['query'][:44]:<46}{r['concept_hits']:>5}{r['partners']:>7}"
              f"{r['rank_p25']:>7}{r['rank_median']:>7}{r['rank_p75']:>7}"
              f"{len(r['new_traditions']):>7}")

    gaprows = [r for r in rows if r["gap"]]
    if gaprows:
        print("\nknownGaps — can the edge leg reach the tradition retrieval misses?")
        for r in gaprows:
            print(f"  {r['query'][:44]:<46} expect {r['gap']:<16} "
                  f"reached: {'YES' if r['gap_reached'] else 'no'}")

    if args.json:
        args.json.write_text(json.dumps(rows, indent=2))
        print(f"\nwrote {args.json}")


if __name__ == "__main__":
    main()
