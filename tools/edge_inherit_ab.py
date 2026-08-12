#!/usr/bin/env python3
"""edge_inherit_ab.py — A/B the anchored edge-inheritance term.

Arms, per golden query, all through guru's parity retriever:

  A     baseline (rarity diversity on, no edges)
  B     rarity diversity OFF — is the "lazy tradition log fn" doing anything?
  C@w   EDGE_INHERIT at several weights (rarity on)
  D     EDGE_INHERIT at the middle weight, rarity OFF — the proposed end
        state: conceptual novelty via edges instead of tradition rarity

Reports how much edge material enters the final top-K, from which anchors,
what it displaces, and how the arms differ. Writes every surfaced partner to
surfaced.jsonl with its query, anchor and body — the judgment set for the
relevance grading that decides whether the mechanism stays.

Usage:
    python3 tools/edge_inherit_ab.py
    python3 tools/edge_inherit_ab.py --top-k 15 --weights 0.5,0.8,1.2
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RELLM_ROOT = Path(__file__).parent.parent
GURU_ROOT = RELLM_ROOT.parent / "guru"
sys.path.insert(0, str(RELLM_ROOT / "src"))
sys.path.insert(0, str(GURU_ROOT))

OLLAMA = "http://localhost:11434/api/embed"
EMBED_MODEL = "nomic-embed-text:v1.5"


def embed(text: str) -> list[float]:
    payload = json.dumps({"model": EMBED_MODEL, "input": text}).encode()
    req = urllib.request.Request(OLLAMA, data=payload,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())["embeddings"][0]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--top-k", type=int, default=15)
    ap.add_argument("--weights", default="0.5,0.8,1.2")
    args = ap.parse_args()
    weights = [float(w) for w in args.weights.split(",")]
    mid = weights[len(weights) // 2]

    os.chdir(GURU_ROOT)
    from guru.preferences import UserPreferences        # noqa: E402
    from guru.retriever import HybridRetriever          # noqa: E402

    gold = json.loads((GURU_ROOT.parent / "guru-web" / "src" / "__tests__"
                       / "fixtures" / "golden-retrieval.json").read_text())
    queries = [q["query"] for q in gold["queries"]]
    queries += [g["query"] for g in gold.get("knownGaps", {}).get("cases", [])]

    conn = sqlite3.connect(f"file:{GURU_ROOT/'data'/'guru.db'}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    retriever = HybridRetriever()
    prefs = UserPreferences.allow_all()

    def run(q, qe, inherit=None, rarity=True):
        for var in ("EDGE_INHERIT", "EDGE_LEG"):
            os.environ.pop(var, None)
        if inherit:
            os.environ["EDGE_INHERIT"] = str(inherit)
        saved = retriever._diversity_boost
        if not rarity:
            retriever._diversity_boost = 0.0
        try:
            return retriever.retrieve(q, qe, prefs, top_k=args.top_k)
        finally:
            retriever._diversity_boost = saved
            os.environ.pop("EDGE_INHERIT", None)

    arms = [("A  base", dict(inherit=None, rarity=True)),
            ("B  base, no rarity", dict(inherit=None, rarity=False))]
    arms += [(f"C  inherit {w}", dict(inherit=w, rarity=True)) for w in weights]
    arms += [(f"D  inherit {mid}, no rarity", dict(inherit=mid, rarity=False))]

    print(f"top-k {args.top_k}   queries {len(queries)}   arms {len(arms)}\n")

    results: dict[str, dict[str, list]] = {}
    for q in queries:
        qe = embed(q)
        results[q] = {}
        for name, kw in arms:
            results[q][name] = run(q, qe, **kw)

    base_name = arms[0][0]
    surfaced = []
    print(f"{'arm':<26}{'Δ vs A':>8}{'edge-in':>9}{'trads':>7}")
    for name, _ in arms:
        delta = entered = 0
        trads = set()
        for q in queries:
            a_ids = [c.chunk_id for c in results[q][base_name]]
            ids = [c.chunk_id for c in results[q][name]]
            new = [c for c in results[q][name] if c.chunk_id not in a_ids]
            delta += len(new)
            trads.update(c.tradition for c in results[q][name])
            if name.startswith(("C", "D")):
                # verify entrants are actually edge material: they entered only
                # once EDGE_INHERIT was on and are absent from both baselines
                b_ids = [c.chunk_id for c in results[q]["B  base, no rarity"]]
                for c in new:
                    if c.chunk_id not in b_ids:
                        entered += 1
                        surfaced.append({
                            "arm": name, "query": q, "chunk_id": c.chunk_id,
                            "tradition": c.tradition,
                            "displaced": [x for x in a_ids
                                          if x not in ids][:3],
                            "body": c.body[:1200],
                        })
        print(f"{name:<26}{delta:>8}{entered if name[0] in 'CD' else '':>9}"
              f"{len(trads):>7}")

    mid_arm = f"C  inherit {mid}"
    print(f"\nper query, {mid_arm}:")
    print(f"  {'query':<48}{'edge-in':>9}  entrant traditions")
    for q in queries:
        a_ids = {c.chunk_id for c in results[q][base_name]}
        b_ids = {c.chunk_id for c in results[q]['B  base, no rarity']}
        new = [c for c in results[q][mid_arm]
               if c.chunk_id not in a_ids and c.chunk_id not in b_ids]
        print(f"  {q[:46]:<48}{len(new):>9}  "
              f"{sorted({c.tradition for c in new}) if new else ''}")

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    out = RELLM_ROOT / "runs" / "edges" / "inherit-ab" / ts
    out.mkdir(parents=True, exist_ok=True)
    dedup: dict[tuple, dict] = {}
    for s in surfaced:
        dedup[(s["query"], s["chunk_id"])] = s
    (out / "surfaced.jsonl").write_text(
        "".join(json.dumps(s) + "\n" for s in dedup.values()))
    (out / "summary.json").write_text(json.dumps({
        "created_at": ts, "top_k": args.top_k, "weights": weights,
        "queries": len(queries), "surfaced_unique": len(dedup),
    }, indent=2))
    print(f"\nwrote {out}  ({len(dedup)} unique surfaced partners for judgment)")


if __name__ == "__main__":
    main()
