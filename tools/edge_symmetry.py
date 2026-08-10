#!/usr/bin/env python3
"""edge_symmetry.py — AB vs BA consistency audit for edge judges.

PARALLELS and CONTRASTS are symmetric relations, so f(A,B) must equal f(B,A).
Generative judges are notoriously order-sensitive, and guru's store cannot
answer this retroactively: propose_edges.py canonicalises the pair with
pair_key() at line 164 *before* insert, so the presentation order the model
actually saw is destroyed and there are 0 reciprocal rows. The metric has to
be generated fresh.

Why it matters here: symmetry is a LABEL-FREE quality signal. A pair whose
verdict flips under order reversal is inherently borderline, which flags
shaky rows in the existing agent-claude labels without anyone grading.

Reads a snapshot read-only; writes results to runs/edges/symmetry/.

Usage:
    # start a judge first, e.g. guru/scripts/run-mistral.sh
    python3 tools/edge_symmetry.py --n 400 --model Mistral-...gguf
    python3 tools/edge_symmetry.py --resume runs/edges/symmetry/<run>/results.jsonl
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from rellm.config import load as load_config  # noqa: E402
from rellm.edges import (  # noqa: E402
    EDGE_SYSTEM_PROMPT,
    POSITIVE_TYPES,
    build_edge_prompt,
    iter_reviewed_edges,
    normalize_verdict,
    parse_edge_response,
)


def latest_snapshot(snapshots_dir: Path) -> Path:
    cands = sorted(d for d in snapshots_dir.iterdir() if d.is_dir())
    if not cands:
        raise SystemExit(f"no snapshots in {snapshots_dir} — run `rellm snapshot`")
    return cands[-1] / "guru.db"


def call_judge(base: str, model: str, prompt: str,
               max_tokens: int, timeout: float, retries: int = 2) -> str:
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": EDGE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.0,
    }).encode()
    last: Exception | None = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(
                f"{base}/v1/chat/completions", data=payload,
                headers={"Content-Type": "application/json"}, method="POST",
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read())
            msg = data["choices"][0]["message"]
            return (msg.get("content") or "").strip() or (msg.get("reasoning_content") or "")
        except Exception as e:  # noqa: BLE001 — retry any transport/decode failure
            last = e
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"judge call failed after {retries + 1} tries: {last}")


def judge_both_orders(pair, base: str, model: str,
                      max_tokens: int, timeout: float) -> dict:
    """Score a pair in both presentation orders."""
    ab_prompt = build_edge_prompt(
        pair.source_citation, pair.source_body,
        pair.target_citation, pair.target_body,
    )
    ba_prompt = build_edge_prompt(
        pair.target_citation, pair.target_body,
        pair.source_citation, pair.source_body,
    )

    out = {
        "edge_id": pair.edge_id,
        "source_chunk": pair.source_chunk,
        "target_chunk": pair.target_chunk,
        "gold": pair.label,
        "gold_positive": pair.is_positive,
        "stored_confidence": pair.confidence,
        "similarity": pair.similarity,
        "tradition_pair": "|".join(pair.tradition_pair),
        "error": None,
    }
    try:
        for tag, prompt in (("ab", ab_prompt), ("ba", ba_prompt)):
            raw = call_judge(base, model, prompt, max_tokens, timeout)
            et, conf, just = normalize_verdict(parse_edge_response(raw))
            out[f"{tag}_edge_type"] = et
            out[f"{tag}_confidence"] = conf
            out[f"{tag}_justification"] = just
            out[f"{tag}_parsed"] = et is not None
    except Exception as e:  # noqa: BLE001
        out["error"] = str(e)
    return out


def stratified_sample(pairs: list, n: int, seed: int) -> list:
    """Sample across tradition-pairs so the audit isn't swallowed by the
    Boehme/Plotinus cluster, and balance positive vs negative gold."""
    rng = random.Random(seed)
    by_bucket: dict[tuple, list] = defaultdict(list)
    for p in pairs:
        by_bucket[(p.tradition_pair, p.is_positive)].append(p)

    buckets = sorted(by_bucket)
    for b in buckets:
        rng.shuffle(by_bucket[b])

    picked: list = []
    i = 0
    while len(picked) < n and any(by_bucket[b] for b in buckets):
        b = buckets[i % len(buckets)]
        if by_bucket[b]:
            picked.append(by_bucket[b].pop())
        i += 1
    rng.shuffle(picked)
    return picked[:n]


def summarize(results: list[dict]) -> dict:
    ok = [r for r in results if not r["error"] and r.get("ab_parsed") and r.get("ba_parsed")]
    parse_fail = len(results) - len(ok)

    def pos(v: str | None) -> bool:
        return v in POSITIVE_TYPES

    exact = [r for r in ok if r["ab_edge_type"] == r["ba_edge_type"]]
    binary = [r for r in ok if pos(r["ab_edge_type"]) == pos(r["ba_edge_type"])]

    ab_gold = [r for r in ok if pos(r["ab_edge_type"]) == r["gold_positive"]]
    ba_gold = [r for r in ok if pos(r["ba_edge_type"]) == r["gold_positive"]]

    consistent = binary
    incons = [r for r in ok if pos(r["ab_edge_type"]) != pos(r["ba_edge_type"])]
    cons_agree = [r for r in consistent if pos(r["ab_edge_type"]) == r["gold_positive"]]

    s = {
        "n_requested": len(results),
        "n_usable": len(ok),
        "n_parse_or_error_fail": parse_fail,
        "exact_symmetry": len(exact) / len(ok) if ok else 0.0,
        "binary_symmetry": len(binary) / len(ok) if ok else 0.0,
        "flip_rate": len(incons) / len(ok) if ok else 0.0,
        "ab_agrees_gold": len(ab_gold) / len(ok) if ok else 0.0,
        "ba_agrees_gold": len(ba_gold) / len(ok) if ok else 0.0,
        "consistent_and_agrees_gold": len(cons_agree) / len(consistent) if consistent else 0.0,
        "n_flipped": len(incons),
    }

    # Does an order flip predict disagreement with the Claude label? If yes,
    # symmetry is a usable label-quality filter.
    if incons and consistent:
        f_dis = sum(1 for r in incons if pos(r["ab_edge_type"]) != r["gold_positive"]) / len(incons)
        c_dis = sum(1 for r in consistent if pos(r["ab_edge_type"]) != r["gold_positive"]) / len(consistent)
        s["gold_disagree_when_flipped"] = f_dis
        s["gold_disagree_when_consistent"] = c_dis
        s["flip_lift"] = f_dis / c_dis if c_dis else float("inf")
    return s


def print_summary(s: dict, by_trad: dict) -> None:
    print(f"\n{'=' * 78}\nAB / BA SYMMETRY\n{'=' * 78}")
    print(f"sampled {s['n_requested']}  usable {s['n_usable']}  "
          f"failed {s['n_parse_or_error_fail']}")
    print(f"\n  exact symmetry (all 4 labels)   {s['exact_symmetry']:.3f}")
    print(f"  binary symmetry (pos vs neg)    {s['binary_symmetry']:.3f}")
    print(f"  FLIP RATE                       {s['flip_rate']:.3f}  ({s['n_flipped']} pairs)")
    print(f"\n  AB agrees with claude label     {s['ab_agrees_gold']:.3f}")
    print(f"  BA agrees with claude label     {s['ba_agrees_gold']:.3f}")
    print(f"  agreement | consistent          {s['consistent_and_agrees_gold']:.3f}")
    if "flip_lift" in s:
        print(f"\n  claude-disagreement | flipped     {s['gold_disagree_when_flipped']:.3f}")
        print(f"  claude-disagreement | consistent  {s['gold_disagree_when_consistent']:.3f}")
        print(f"  LIFT                              {s['flip_lift']:.2f}x")
        print("  (>1 means an order flip predicts a shaky label — usable as a "
              "grading-free\n   filter over the existing review set)")

    if by_trad:
        print(f"\n{'tradition pair':<50}{'n':>6}{'flip':>8}{'agree':>8}")
        print("-" * 78)
        for k, v in sorted(by_trad.items(), key=lambda kv: -kv[1]["n"])[:20]:
            if v["n"] < 3:
                continue
            print(f"{k:<50}{v['n']:>6}{v['flip'] / v['n']:>8.3f}{v['agree'] / v['n']:>8.3f}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--snapshot", type=Path)
    ap.add_argument("--n", type=int, default=400, help="pairs to audit")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--base-url", default=os.environ.get("LLAMACPP_BASE_URL",
                                                         "http://127.0.0.1:8080"))
    ap.add_argument("--model", default="Mistral-Small-3.2-24B-Instruct-2506-UD-Q5_K_XL.gguf",
                    help="provenance label; llama.cpp serves whatever is loaded")
    ap.add_argument("--max-tokens", type=int, default=512)
    ap.add_argument("--timeout", type=float, default=300.0)
    ap.add_argument("--concurrency", type=int, default=4,
                    help="match llama-server --parallel")
    ap.add_argument("--out", type=Path, default=PROJECT_ROOT / "runs" / "edges" / "symmetry")
    ap.add_argument("--report-only", type=Path,
                    help="re-summarize an existing results.jsonl without calling a judge")
    args = ap.parse_args()

    if args.report_only:
        results = [json.loads(l) for l in args.report_only.read_text().splitlines() if l.strip()]
        s = summarize(results)
        print_summary(s, by_tradition(results))
        return

    cfg = load_config()
    db = (args.snapshot / "guru.db" if args.snapshot and args.snapshot.is_dir()
          else args.snapshot or latest_snapshot(cfg.rellm.snapshots))
    if db.resolve() == cfg.guru.db.resolve():
        raise SystemExit("refusing to read the live guru db — use a snapshot")

    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    print(f"snapshot: {db}")

    pairs = list(iter_reviewed_edges(conn, cfg.guru.corpus_dir))
    print(f"reviewed pairs with both bodies: {len(pairs):,}")
    sample = stratified_sample(pairs, args.n, args.seed)
    print(f"stratified sample: {len(sample)} across "
          f"{len({p.tradition_pair for p in sample})} tradition pairs")

    run_dir = args.out / datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    run_dir.mkdir(parents=True, exist_ok=True)
    results_path = run_dir / "results.jsonl"
    print(f"judge: {args.model} @ {args.base_url}  (2 calls/pair, "
          f"{len(sample) * 2} total)\nwriting {results_path}\n")

    results: list[dict] = []
    t0 = time.time()
    with results_path.open("w") as fh, ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futs = [ex.submit(judge_both_orders, p, args.base_url, args.model,
                          args.max_tokens, args.timeout) for p in sample]
        for i, fut in enumerate(futs, 1):
            r = fut.result()
            results.append(r)
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            fh.flush()
            if i % 20 == 0 or i == len(futs):
                el = time.time() - t0
                print(f"  {i}/{len(futs)}  {el:.0f}s  "
                      f"({el / i:.1f}s/pair, eta {(len(futs) - i) * el / i / 60:.1f}m)")

    s = summarize(results)
    (run_dir / "summary.json").write_text(json.dumps(s, indent=2))
    print_summary(s, by_tradition(results))
    print(f"\nwrote {run_dir}")
    conn.close()


def by_tradition(results: list[dict]) -> dict:
    def pos(v):
        return v in POSITIVE_TYPES
    agg: dict[str, dict] = defaultdict(lambda: {"n": 0, "flip": 0, "agree": 0})
    for r in results:
        if r.get("error") or not r.get("ab_parsed") or not r.get("ba_parsed"):
            continue
        a = agg[r["tradition_pair"]]
        a["n"] += 1
        a["flip"] += int(pos(r["ab_edge_type"]) != pos(r["ba_edge_type"]))
        a["agree"] += int(pos(r["ab_edge_type"]) == r["gold_positive"])
    return agg


if __name__ == "__main__":
    main()
