#!/usr/bin/env python3
"""derived_parallels.py — PROTOTYPE: parallels as a derived table, no Pass C.

Replaces LLM pair-classification with: EXPRESSES (human-gated) x thin-student
(concept, chunk) scores. A chunk's partners = top-K cross-tradition
co-expressors of its concepts, pair grade = min leg score, thresholded.

Usage:
    EDGE_GURU_ROOT=<worktree> python tools/derived_parallels.py \
        --model <student> --out runs/edges/derived/<ts> [--top-k 5]
"""
from __future__ import annotations
import argparse, collections, json, os, sqlite3, sys
from pathlib import Path

RELLM_ROOT = Path(__file__).parent.parent
GURU_ROOT = Path(os.environ.get("EDGE_GURU_ROOT", RELLM_ROOT.parent / "guru"))
sys.path.insert(0, str(GURU_ROOT))

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--top-k", type=int, default=5)
    ap.add_argument("--min-grade", type=float, default=-4.415,
                    help="min-leg grade floor (default: the student's "
                         "calibrated EDGE_RERANK threshold)")
    args = ap.parse_args()
    args.model = args.model.resolve(); args.out = args.out.resolve()

    os.chdir(GURU_ROOT)
    from guru.corpus import resolve_chunk_path
    import tomllib
    conn = sqlite3.connect(f"file:{GURU_ROOT/'data'/'guru.db'}?mode=ro", uri=True)

    defs = {}
    with open(GURU_ROOT/"concepts"/"taxonomy.toml","rb") as f:
        tax = tomllib.load(f)
    def collect(n):
        for k,v in n.items():
            if isinstance(v,dict): collect(v)
            elif isinstance(v,str): defs[f"concept.{k}"] = v
    collect(tax.get("concepts", {}))

    trad = {c:t for c,t in conn.execute("SELECT id,tradition_id FROM nodes WHERE type='chunk'")}
    bycon = collections.defaultdict(set); bychunk = collections.defaultdict(set)
    for s,t in conn.execute("SELECT source_id,target_id FROM edges WHERE type='EXPRESSES'"):
        if t in defs:
            bycon[t].add(s); bychunk[s].add(t)

    need = sorted({(c,ch) for c,chs in bycon.items() for ch in chs})
    print(f"(concept, chunk) pairs to score: {len(need)}")
    bodies = {}
    for _,ch in need:
        if ch not in bodies:
            p = resolve_chunk_path(ch)
            if p: bodies[ch] = tomllib.load(open(p,"rb"))["content"]["body"][:2400]

    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForSequenceClassification.from_pretrained(args.model, dtype=torch.float32).to(dev)
    model.eval()
    score = {}
    pairs = [(c,ch) for c,ch in need if ch in bodies]
    with torch.no_grad():
        for i in range(0, len(pairs), 64):
            b = pairs[i:i+64]
            enc = tok([[defs[c], bodies[ch]] for c,ch in b], padding=True,
                      truncation=True, max_length=512, return_tensors="pt").to(dev)
            for (c,ch),s in zip(b, model(**enc).logits.view(-1).tolist()):
                score[(c,ch)] = s
            if (i//64)%100==0: print(f"  {min(i+64,len(pairs))}/{len(pairs)}", flush=True)

    # per concept: chunks ranked by score, for partner lookup
    ranked = {c: sorted(chs, key=lambda ch: -score.get((c,ch), -99)) for c,chs in bycon.items()}
    args.out.mkdir(parents=True, exist_ok=True)
    n_rows = 0
    partners_of = {}
    with open(args.out/"derived_parallels.jsonl","w") as out:
        for ch, concepts in bychunk.items():
            # anchor gate: chunk must itself clear the floor on a concept for
            # that concept to contribute partners
            vias = [c for c in concepts
                    if (score.get((c,ch)) or -99) >= args.min_grade]
            # round-robin across via concepts, partners ranked by the
            # PARTNER's own concept score (the anchor's score is a gate, not
            # a rank — min-leg clamping made panels monochrome)
            iters = {c: iter(ranked[c]) for c in vias}
            best = {}
            picked_n = 0
            while iters and picked_n < args.top_k * 2:
                for c in list(iters):
                    other = next(iters[c], None)
                    if other is None:
                        del iters[c]; continue
                    if other == ch or trad.get(other) == trad.get(ch):
                        continue
                    b = score.get((c,other))
                    if b is None or b < args.min_grade:
                        del iters[c]; continue
                    if other not in best:
                        best[other] = (c, b)
                        picked_n += 1
            for other,(c,g) in sorted(best.items(), key=lambda kv:-kv[1][1]):
                out.write(json.dumps({"chunk":ch,"partner":other,"via":c,
                                      "grade":round(g,3)})+"\n")
                n_rows += 1
            partners_of[ch] = len(best)
    json.dump({(f"score_pairs"): len(pairs), "rows": n_rows,
               "chunks_with_partners": sum(1 for v in partners_of.values() if v),
               "chunks_total": len(bychunk)},
              open(args.out/"summary.json","w"), indent=2)
    # postgres-shaped TSV for the reader-panel snapshot trial:
    # edges(source, target, edge_type, tier, weight, annotation), one
    # direction per unique pair, annotation = the via explanation.
    seen_pairs = set()
    label = {c: c.split(".",1)[1].replace("_"," ") for c in defs}
    with open(args.out/"edges_derived.tsv","w") as tsv:
        for line in open(args.out/"derived_parallels.jsonl"):
            r = json.loads(line)
            k = (min(r["chunk"],r["partner"]), max(r["chunk"],r["partner"]))
            if k in seen_pairs: continue
            seen_pairs.add(k)
            ann = (f"Shared concept: {label[r['via']]} — "
                   f"{defs[r['via']].split('.')[0]}. (derived)")
            tsv.write("\t".join([k[0], k[1], "PARALLELS", "inferred",
                                 str(r["grade"]), ann]) + "\n")
    print(f"wrote {args.out}: {n_rows} partner rows "
          f"({len(seen_pairs)} unique pairs in edges_derived.tsv), "
          f"{sum(1 for v in partners_of.values() if v)}/{len(bychunk)} chunks have partners")

if __name__ == "__main__":
    main()
