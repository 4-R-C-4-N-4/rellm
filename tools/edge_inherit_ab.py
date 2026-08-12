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
# EDGE_GURU_ROOT lets a run target a guru worktree (e.g. the
# retriever-parity-with-guru-web branch) without touching the main checkout.
GURU_ROOT = Path(os.environ.get("EDGE_GURU_ROOT", RELLM_ROOT.parent / "guru"))
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
    ap.add_argument("--wide", action="store_true",
                    help="add the per-work golden relevance queries "
                         "(guru-web fixtures/golden-queries/<work>.json, "
                         "kind=relevance) to the original golden set; "
                         "provenance recorded in queries.json")
    ap.add_argument("--rerank", action="store_true",
                    help="A/B the thresholded reranker term: arms A (base), "
                         "C@mid (pair_sim inheritance), R@mid (EDGE_RERANK). "
                         "surfaced.jsonl records R-arm entrants only (the "
                         "ship-gate judgment set); per-query latency logged "
                         "to latency.json. Needs torch (run under a venv "
                         "with transformers).")
    args = ap.parse_args()
    weights = [float(w) for w in args.weights.split(",")]
    mid = weights[len(weights) // 2]

    os.chdir(GURU_ROOT)
    from guru.preferences import UserPreferences        # noqa: E402
    from guru.retriever import HybridRetriever          # noqa: E402

    # guru-web lives beside the MAIN guru checkout even when EDGE_GURU_ROOT
    # points a run at a worktree.
    GURU_WEB = RELLM_ROOT.parent / "guru-web"
    gold = json.loads((GURU_WEB / "src" / "__tests__"
                       / "fixtures" / "golden-retrieval.json").read_text())
    queries = [q["query"] for q in gold["queries"]]
    queries += [g["query"] for g in gold.get("knownGaps", {}).get("cases", [])]
    # Query provenance manifest: lets the judged labels be partitioned later
    # (frozenEval=True work queries must never feed scorer training).
    provenance = {q: {"source": "golden-retrieval.json"} for q in queries}
    if args.wide:
        gq_dir = GURU_WEB / "src" / "__tests__" / "fixtures" / "golden-queries"
        for f in sorted(gq_dir.glob("*.json")):
            if f.name.startswith("_"):
                continue
            work = json.loads(f.read_text())
            for wq in work["queries"]:
                if wq["kind"] != "relevance" or wq["query"] in provenance:
                    continue
                queries.append(wq["query"])
                provenance[wq["query"]] = {
                    "source": f.name, "work": work["work"],
                    "tradition": work["tradition"],
                    "frozenEval": work["frozenEval"],
                }

    conn = sqlite3.connect(f"file:{GURU_ROOT/'data'/'guru.db'}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    retriever = HybridRetriever()
    prefs = UserPreferences.allow_all()

    def run(q, qe, inherit=None, rarity=True, rerank=None):
        for var in ("EDGE_INHERIT", "EDGE_LEG", "EDGE_RERANK"):
            os.environ.pop(var, None)
        if inherit:
            os.environ["EDGE_INHERIT"] = str(inherit)
        if rerank:
            os.environ["EDGE_RERANK"] = str(rerank)
        saved = retriever._diversity_boost
        if not rarity:
            retriever._diversity_boost = 0.0
        try:
            return retriever.retrieve(q, qe, prefs, top_k=args.top_k)
        finally:
            retriever._diversity_boost = saved
            for var in ("EDGE_INHERIT", "EDGE_RERANK"):
                os.environ.pop(var, None)

    if args.rerank:
        # Ship-gate A/B: same anchored envelope, pair_sim vs thresholded
        # reranker. B/D (rarity ablations) already measured; keep it lean.
        arms = [("A  base", dict(inherit=None, rarity=True)),
                (f"C  inherit {mid}", dict(inherit=mid, rarity=True)),
                (f"R  rerank {mid}", dict(rerank=mid, rarity=True))]
    else:
        arms = [("A  base", dict(inherit=None, rarity=True)),
                ("B  base, no rarity", dict(inherit=None, rarity=False))]
        arms += [(f"C  inherit {w}", dict(inherit=w, rarity=True))
                 for w in weights]
        arms += [(f"D  inherit {mid}, no rarity",
                  dict(inherit=mid, rarity=False))]

    print(f"top-k {args.top_k}   queries {len(queries)}   arms {len(arms)}\n")

    import time
    latency: dict[str, dict[str, dict]] = {}
    results: dict[str, dict[str, list]] = {}
    for qn, q in enumerate(queries):
        qe = embed(q)
        results[q] = {}
        latency[q] = {}
        for name, kw in arms:
            if kw.get("rerank"):
                from guru import rerank as _rr
                _rr.LAST.clear()
            t0 = time.monotonic()
            results[q][name] = run(q, qe, **kw)
            rec = {"seconds": round(time.monotonic() - t0, 3)}
            if kw.get("rerank"):
                rec.update({f"rerank_{k}": round(v, 3)
                            for k, v in _rr.LAST.items()})
            latency[q][name] = rec
        if args.rerank:
            print(f"  [{qn + 1}/{len(queries)}] {q[:56]:<58}"
                  f"{latency[q][arms[-1][0]]['seconds']:>8.1f}s", flush=True)

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
            if name.startswith(("C", "D", "R")):
                # verify entrants are actually edge material: they entered only
                # once the term was on and are absent from the baseline(s)
                b_ids = [c.chunk_id for c in
                         results[q].get("B  base, no rarity", [])]
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
        print(f"{name:<26}{delta:>8}{entered if name[0] in 'CDR' else '':>9}"
              f"{len(trads):>7}")

    mid_arm = f"C  inherit {mid}"
    print(f"\nper query, {mid_arm}:")
    print(f"  {'query':<48}{'edge-in':>9}  entrant traditions")
    for q in queries:
        a_ids = {c.chunk_id for c in results[q][base_name]}
        b_ids = {c.chunk_id for c in
                 results[q].get('B  base, no rarity', [])}
        new = [c for c in results[q][mid_arm]
               if c.chunk_id not in a_ids and c.chunk_id not in b_ids]
        print(f"  {q[:46]:<48}{len(new):>9}  "
              f"{sorted({c.tradition for c in new}) if new else ''}")

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    out = RELLM_ROOT / "runs" / "edges" / "inherit-ab" / ts
    out.mkdir(parents=True, exist_ok=True)
    dedup: dict[tuple, dict] = {}
    for s in surfaced:
        # In rerank mode surfaced.jsonl is the ship-gate judgment set for the
        # NEW term — R-arm entrants only; C entrants stay in the printed table.
        if args.rerank and not s["arm"].startswith("R"):
            continue
        dedup[(s["query"], s["chunk_id"])] = s
    (out / "surfaced.jsonl").write_text(
        "".join(json.dumps(s) + "\n" for s in dedup.values()))
    (out / "summary.json").write_text(json.dumps({
        "created_at": ts, "top_k": args.top_k, "weights": weights,
        "queries": len(queries), "wide": args.wide,
        "surfaced_unique": len(dedup),
    }, indent=2))
    (out / "queries.json").write_text(json.dumps(provenance, indent=2))
    (out / "latency.json").write_text(json.dumps(latency, indent=2))
    print(f"\nwrote {out}  ({len(dedup)} unique surfaced partners for judgment)")


if __name__ == "__main__":
    main()
