#!/usr/bin/env python3
"""edge_curation_probe.py — grade the live PARALLELS graph with the thin scorer.

The organized-better probe (todo:10857362). For every live PARALLELS edge:

  via    = the EXPRESSES-concept intersection of its two chunks — what the
           pair is actually parallel ABOUT. Empty via is suspect by
           construction: nothing recorded is shared.
  grade  = min over the two legs of student(concept-definition query, body).
           Per-CONCEPT static grading is legitimate (the per-arbitrary-query
           static weight is the proven dead end); an edge whose weaker leg
           does not even answer its own shared concept is not a curated
           parallel. Best via concept wins for the edge.

Outputs (run dir): edge_grades.jsonl, report.json, suspect_queue.json — a
PROPOSAL only. No guru.db writes; the owner keeps the apply gate.

Usage:
    EDGE_GURU_ROOT=<worktree> python tools/edge_curation_probe.py \
        --model runs/edges/scorer/<ts>/student-3a2 --out runs/edges/curation/<ts>
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sqlite3
import sys
from pathlib import Path

RELLM_ROOT = Path(__file__).parent.parent
GURU_ROOT = Path(os.environ.get("EDGE_GURU_ROOT", RELLM_ROOT.parent / "guru"))
sys.path.insert(0, str(GURU_ROOT))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--suspect-percentile", type=float, default=10.0,
                    help="graded edges below this percentile join the "
                         "suspect queue proposal")
    args = ap.parse_args()
    args.model = args.model.resolve()
    args.out = args.out.resolve()

    os.chdir(GURU_ROOT)
    from guru.corpus import resolve_chunk_path            # noqa: E402
    import tomllib                                        # noqa: E402

    conn = sqlite3.connect(f"file:{GURU_ROOT/'data'/'guru.db'}?mode=ro",
                           uri=True)

    # concept definitions (canonical queries)
    defs: dict[str, str] = {}
    with open(GURU_ROOT / "concepts" / "taxonomy.toml", "rb") as f:
        tax = tomllib.load(f)

    def collect(node: dict) -> None:
        for k, v in node.items():
            if isinstance(v, dict):
                collect(v)
            elif isinstance(v, str):
                # graph nodes are namespaced ("concept.<id>"); taxonomy keys
                # are bare — store under the graph's namespace
                defs[f"concept.{k}"] = v
    collect(tax.get("concepts", {}))

    # chunk -> expressed concepts
    expresses: dict[str, set[str]] = collections.defaultdict(set)
    for src, tgt in conn.execute(
            "SELECT source_id, target_id FROM edges WHERE type='EXPRESSES'"):
        expresses[src].add(tgt)

    edges = [(s, t) for s, t in conn.execute(
        "SELECT source_id, target_id FROM edges WHERE type='PARALLELS'")]
    print(f"{len(edges)} PARALLELS edges, {len(defs)} concept definitions")

    via_of: dict[tuple[str, str], list[str]] = {}
    need: set[tuple[str, str]] = set()   # (concept, chunk) pairs to score
    empty_via = []
    for s, t in edges:
        via = sorted(c for c in (expresses[s] & expresses[t]) if c in defs)
        via_of[(s, t)] = via
        if not via:
            empty_via.append((s, t))
            continue
        for c in via:
            need.add((c, s))
            need.add((c, t))
    print(f"empty-via edges: {len(empty_via)} "
          f"({len(empty_via)/len(edges):.1%}); "
          f"unique (concept, chunk) pairs to score: {len(need)}")

    bodies: dict[str, str] = {}
    for _, cid in need:
        if cid not in bodies:
            p = resolve_chunk_path(cid)
            if p is not None:
                with open(p, "rb") as f:
                    bodies[cid] = tomllib.load(f)["content"]["body"][:2400]

    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model, dtype=torch.float32).to(dev)
    model.eval()

    pairs = [(c, cid) for c, cid in sorted(need) if cid in bodies]
    scores: dict[tuple[str, str], float] = {}
    with torch.no_grad():
        for i in range(0, len(pairs), 64):
            batch = pairs[i:i + 64]
            enc = tok([[defs[c], bodies[cid]] for c, cid in batch],
                      padding=True, truncation=True, max_length=512,
                      return_tensors="pt").to(dev)
            for (c, cid), s in zip(batch,
                                   model(**enc).logits.view(-1).tolist()):
                scores[(c, cid)] = s
            if (i // 64) % 50 == 0:
                print(f"  scored {min(i+64, len(pairs))}/{len(pairs)}",
                      flush=True)

    graded = []
    for (s, t), via in via_of.items():
        if not via:
            continue
        best = None
        for c in via:
            a, b = scores.get((c, s)), scores.get((c, t))
            if a is None or b is None:
                continue
            g = min(a, b)
            if best is None or g > best[1]:
                best = (c, g)
        if best:
            graded.append({"source": s, "target": t, "via": best[0],
                           "grade": round(best[1], 4),
                           "n_via": len(via)})

    graded.sort(key=lambda e: e["grade"])
    import numpy as np
    gvals = np.array([e["grade"] for e in graded])
    if len(gvals) == 0:
        raise SystemExit("nothing graded — check concept id namespace vs "
                         "taxonomy keys before trusting empty-via counts")
    cut = float(np.percentile(gvals, args.suspect_percentile))
    suspects = [e for e in graded if e["grade"] <= cut]

    deg = collections.Counter()
    for s, t in edges:
        deg[s] += 1
        deg[t] += 1
    hubs = deg.most_common(10)

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "edge_grades.jsonl").write_text(
        "".join(json.dumps(e) + "\n" for e in graded))
    (args.out / "suspect_queue.json").write_text(json.dumps({
        "note": "PROPOSAL only — no db writes. Suspect = empty-via, or "
                "graded at/below the given percentile of min-leg "
                "via-concept relevance.",
        "model": str(args.model), "suspect_percentile": args.suspect_percentile,
        "grade_cutoff": round(cut, 4),
        "empty_via": [{"source": s, "target": t} for s, t in empty_via],
        "low_grade": suspects,
    }, indent=1))
    report = {
        "edges": len(edges), "graded": len(graded),
        "empty_via": len(empty_via),
        "grade_percentiles": {p: round(float(np.percentile(gvals, p)), 3)
                              for p in (5, 10, 25, 50, 75, 90, 95)},
        "suspects_low_grade": len(suspects),
        "top_hubs": [{"chunk": c, "degree": d} for c, d in hubs],
        "via_count_hist": dict(collections.Counter(
            min(e["n_via"], 5) for e in graded)),
    }
    (args.out / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
