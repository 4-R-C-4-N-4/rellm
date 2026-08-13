#!/usr/bin/env python3
"""scorer_query_pool.py — assemble the thin-scorer training query pool.

Sources (todo:2cf94434; spec docs/edges/thin-scorer-spec.md):
  golden     guru-web fixtures/golden-queries/<work>.json where
             frozenEval:false — both kinds, owner-ratified wording
  synthetic  data/scorer/synthetic/<work>.jsonl — ritual-style queries
             drafted from chunks for training breadth

HARD RULE enforced here: no query whose work is frozenEval:true enters the
pool. Frozen works are the eval universe; this file is the enforcement point.

Usage:
    python3 tools/scorer_query_pool.py            # writes data/scorer/queries.jsonl
    python3 tools/scorer_query_pool.py --stats
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

RELLM_ROOT = Path(__file__).parent.parent
GOLDEN_DIR = (RELLM_ROOT.parent / "guru-web" / "src" / "__tests__"
              / "fixtures" / "golden-queries")
SYNTH_DIR = RELLM_ROOT / "data" / "scorer" / "synthetic"
OUT = RELLM_ROOT / "data" / "scorer" / "queries.jsonl"


def load_golden_meta() -> dict[str, dict]:
    meta = {}
    for f in sorted(GOLDEN_DIR.glob("*.json")):
        if f.name.startswith("_"):
            continue
        d = json.loads(f.read_text())
        meta[d["work"]] = d
    return meta


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stats", action="store_true")
    args = ap.parse_args()

    meta = load_golden_meta()
    frozen = {w for w, d in meta.items() if d["frozenEval"]}
    rows, seen, dropped_frozen, dropped_dup = [], set(), 0, 0

    def add(query: str, work: str, tradition: str, kind: str, source: str,
            prov: list[str]) -> None:
        nonlocal dropped_frozen, dropped_dup
        if work in frozen:
            dropped_frozen += 1
            return
        if work not in meta:
            raise SystemExit(f"unknown work {work!r} — not in golden fixtures")
        key = query.strip().lower()
        if key in seen:
            dropped_dup += 1
            return
        seen.add(key)
        rows.append({"query": query.strip(), "work": work,
                     "tradition": tradition, "kind": kind, "source": source,
                     "provenanceChunkIds": prov})

    for work, d in sorted(meta.items()):
        if d["frozenEval"]:
            continue
        for q in d["queries"]:
            kind = "probe" if q["kind"] == "recall-probe" else "relevance"
            add(q["query"], work, d["tradition"], kind, "golden",
                q["provenanceChunkIds"])

    for f in sorted(SYNTH_DIR.glob("*.jsonl")):
        for line in f.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            add(r["query"], r["work"], r["tradition"], r["kind"], "synthetic",
                r.get("provenanceChunkIds", []))

    if args.stats or True:
        by = Counter((r["source"], r["kind"]) for r in rows)
        print(f"pool: {len(rows)} queries over "
              f"{len({r['work'] for r in rows})} trainable works "
              f"({len(frozen)} frozen works excluded; "
              f"dropped {dropped_frozen} frozen-work rows, {dropped_dup} dups)")
        for (src, kind), n in sorted(by.items()):
            print(f"  {src:<10}{kind:<11}{n}")

    if not args.stats:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text("".join(json.dumps(r) + "\n" for r in rows))
        print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
