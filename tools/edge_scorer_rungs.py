#!/usr/bin/env python3
"""edge_scorer_rungs.py — can an existing scorer find the relevant partners?

The relevance judgment left 100 doubly-graded (query, chunk) items (kappa
+0.800): 69 edge-surfaced partners (11 strict-relevant), 15 baseline chunks,
16 random. Before training anything, test whether scorers we can have today
separate relevant from not:

  rung 1   query↔chunk embedding cosine (nomic, already computed for chunks)
  rung 2   BAAI/bge-reranker-v2-m3 zero-shot, CPU

Metrics per rung, on the surfaced stratum (the operational set):
  - AUC against the strict label (both graders relevant) and lenient label
  - precision@3 per query, averaged — the deployment question is "keep the
    top few partners per query", not global ranking
  - kept-slot relevance at a 1-in-6 keep rate, vs the 15.9% unranked rate
    and the 66.7% baseline bar
Sanity: baseline-vs-random separation on the same scorer — a scorer that
cannot tell the retriever's own results from noise is disqualified.

CPU-only by construction (CUDA_VISIBLE_DEVICES emptied before torch import).
Query embeddings come from ollama's resident nomic model — 9 short strings.

Usage:
    tools/venv python tools/edge_scorer_rungs.py --rung 1 [--run DIR]
    tools/venv python tools/edge_scorer_rungs.py --rung 2
    python3 tools/edge_scorer_rungs.py --report
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sqlite3
import sys
import urllib.request
from pathlib import Path

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

import numpy as np

RELLM_ROOT = Path(__file__).parent.parent
GURU_ROOT = RELLM_ROOT.parent / "guru"
JUDGE_ROOT = RELLM_ROOT / "runs" / "edges" / "relevance-judge"
VERDICTS = ("relevant", "marginal", "not_relevant")


def latest(root: Path) -> Path:
    return sorted(d for d in root.iterdir() if d.is_dir())[-1]


def load_run(run: Path):
    items = {json.loads(l)["idx"]: json.loads(l)
             for l in (run / "judge.jsonl").read_text().splitlines()}
    key = {int(k): v for k, v in json.loads((run / "key.json").read_text()).items()}

    def load(d):
        out = {}
        for f in sorted(d.glob("*.jsonl")):
            for line in f.read_text().splitlines():
                if line.strip():
                    g = json.loads(line)
                    if g.get("verdict") in VERDICTS:
                        out[g["idx"]] = g["verdict"]
        return out

    g1, g2 = load(run / "grades-1"), load(run / "grades-2")
    labels = {}
    for i in items:
        if i in g1 and i in g2:
            labels[i] = {
                "strict": g1[i] == g2[i] == "relevant",
                "lenient": g1[i] != "not_relevant" and g2[i] != "not_relevant",
            }
    return items, key, labels


def auc(scores: list[float], y: list[bool]) -> float:
    order = np.argsort(scores)
    ranks = np.empty(len(scores)); ranks[order] = np.arange(1, len(scores) + 1)
    pos = np.array(y); n1, n0 = int(pos.sum()), int((~pos).sum())
    if not n1 or not n0:
        return float("nan")
    return float((ranks[pos].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def metrics(items, key, labels, scores: dict[int, float], name: str) -> dict:
    surf = [i for i in labels if key[i] == "surfaced" and i in scores]
    out = {"rung": name, "n_surfaced": len(surf)}
    for lab in ("strict", "lenient"):
        out[f"auc_{lab}"] = round(auc([scores[i] for i in surf],
                                      [labels[i][lab] for i in surf]), 3)
    # per-query precision@3 and kept-slot rate at ~1-in-6
    by_q = collections.defaultdict(list)
    for i in surf:
        by_q[items[i]["query"]].append(i)
    p3, kept_hits, kept_n = [], 0, 0
    for q, idxs in by_q.items():
        idxs.sort(key=lambda i: -scores[i])
        top3 = idxs[:3]
        p3.append(sum(labels[i]["strict"] for i in top3) / len(top3))
        k = max(1, round(len(idxs) / 6))
        kept_n += k
        kept_hits += sum(labels[i]["strict"] for i in idxs[:k])
    out["precision_at_3"] = round(sum(p3) / len(p3), 3) if p3 else None
    out["kept_slot_strict"] = round(kept_hits / kept_n, 3) if kept_n else None
    out["kept_n"] = kept_n

    # sanity: does the scorer separate baseline from random?
    bs = [i for i in scores if key.get(i) == "baseline"]
    rd = [i for i in scores if key.get(i) == "random"]
    if bs and rd:
        out["sanity_auc_baseline_vs_random"] = round(auc(
            [scores[i] for i in bs + rd],
            [True] * len(bs) + [False] * len(rd)), 3)
    return out


def embed_query(text: str) -> np.ndarray:
    payload = json.dumps({"model": "nomic-embed-text:v1.5", "input": text}).encode()
    req = urllib.request.Request("http://localhost:11434/api/embed", data=payload,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        v = np.array(json.loads(r.read())["embeddings"][0], dtype=np.float32)
    return v / np.linalg.norm(v)


def rung1(items, key, labels, run: Path) -> dict:
    conn = sqlite3.connect(f"file:{GURU_ROOT/'data'/'guru.db'}?mode=ro", uri=True)
    vecs = {}
    for cid, blob in conn.execute("SELECT chunk_id, vector FROM chunk_embeddings"):
        v = np.frombuffer(blob, dtype=np.float32)
        vecs[cid] = v / np.linalg.norm(v)
    qembs = {q: embed_query(q) for q in {it["query"] for it in items.values()}}
    scores = {i: float(qembs[it["query"]] @ vecs[it["citation"]])
              for i, it in items.items() if it["citation"] in vecs}
    m = metrics(items, key, labels, scores, "1: query-chunk embedding cosine")
    (run / "rung1_scores.json").write_text(json.dumps(scores, indent=2))
    return m


def rung2(items, key, labels, run: Path) -> dict:
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    name = "BAAI/bge-reranker-v2-m3"
    tok = AutoTokenizer.from_pretrained(name)
    model = AutoModelForSequenceClassification.from_pretrained(
        name, dtype=torch.float32)
    model.eval()
    scores = {}
    order = sorted(items)
    with torch.no_grad():
        for i in range(0, len(order), 8):
            batch = order[i:i + 8]
            enc = tok([[items[j]["query"], items[j]["body"]] for j in batch],
                      padding=True, truncation=True, max_length=1024,
                      return_tensors="pt")
            logits = model(**enc).logits.view(-1)
            for j, s in zip(batch, logits.tolist()):
                scores[j] = s
            print(f"  scored {min(i + 8, len(order))}/{len(order)}", flush=True)
    m = metrics(items, key, labels, scores, "2: bge-reranker-v2-m3 zero-shot (CPU)")
    (run / "rung2_scores.json").write_text(json.dumps(scores, indent=2))
    return m


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rung", type=int, choices=(1, 2))
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--run", type=Path)
    args = ap.parse_args()

    run = args.run or latest(JUDGE_ROOT)
    items, key, labels = load_run(run)
    print(f"run {run.name}: {len(items)} items, {len(labels)} doubly-graded")

    if args.report:
        for f in sorted(run.glob("rung*_metrics.json")):
            print(json.dumps(json.loads(f.read_text()), indent=2))
        return

    m = rung1(items, key, labels, run) if args.rung == 1 else rung2(items, key, labels, run)
    (run / f"rung{args.rung}_metrics.json").write_text(json.dumps(m, indent=2))
    print(json.dumps(m, indent=2))


if __name__ == "__main__":
    main()
