#!/usr/bin/env python3
"""edge_candidate_probe.py — is a challenger strategy's extra reach worth anything?

The retrieval sim can measure coverage, balance and cost. It cannot measure
the yield of candidates a challenger reaches and the incumbent never did:
those pairs have never been judged, so no label exists. This probe judges
them.

Judge bias is controlled by sampling three arms and scoring them with one
judge in one pass:

  shared          selected by BOTH strategies, already carries a Claude label.
                  Calibration arm — measures the judge against known truth.
  current_only    selected by the incumbent but NOT the challenger, labelled.
                  Measures what the challenger gives up.
  challenger_only selected by the challenger, never proposed by the incumbent,
                  no label. The unknown being measured.

Absolute accept rates from any single judge are biased (Mistral answers
PARALLELS on 79% of pairs). Scoring every arm with the same judge and prompt
makes that bias common-mode so it cancels in the differences, and the
labelled `shared` arm quantifies what remains.

Pairs whose corpus files are missing are dropped from all arms equally.

Serve a judge first, e.g.:
    llama-server --model Qwen3.5-27B-UD-Q4_K_XL.gguf --parallel 8 \
        --ctx-size 49152 --reasoning off --reasoning-budget 0 --jinja

Thinking must be disabled: at --reasoning auto the model spends its whole
token budget reasoning and never emits the JSON verdict (parse rate 4/8).

Read-only against the snapshot.

Usage:
    python3 tools/edge_candidate_probe.py --n 120 --concurrency 8 \
        --max-tokens 1024 --strategy worklevel
"""
from __future__ import annotations

import argparse
import json
import random
import sqlite3
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

from rellm.config import load as load_config  # noqa: E402
from rellm.corpus import chunk_body, chunk_citation, resolve_chunk_path  # noqa: E402
from rellm.edges import (  # noqa: E402
    POSITIVE_TYPES, build_edge_prompt, normalize_verdict, parse_edge_response,
)
from edge_retrieval_sim import (  # noqa: E402
    latest_snapshot, load_state, select_current, select_hybrid,
    select_worklevel, tradition_yield,
)
from edge_symmetry import call_judge  # noqa: E402


def build_arms(cur, hyb, ids, labels, rng, n, corpus_dir):
    """Partition the two selections into the three comparison arms.

    Pairs whose corpus files are missing are dropped from ALL arms equally —
    a pair nobody can read is not evidence about any strategy. The previous
    round lost 21/120 challenger calls this way while current_only lost 0,
    because a coverage-driven strategy reaches the 144 absent chunks.
    """
    ok: dict[int, bool] = {}

    def readable(i):
        if i not in ok:
            ok[i] = resolve_chunk_path(ids[i], corpus_dir) is not None
        return ok[i]

    def key(i, j):
        a, b = ids[i], ids[j]
        return (a, b) if a <= b else (b, a)

    shared, cur_only, hyb_only = [], [], []
    for pair in cur & hyb:
        if key(*pair) in labels and readable(pair[0]) and readable(pair[1]):
            shared.append(pair)
    for pair in cur - hyb:
        if key(*pair) in labels and readable(pair[0]) and readable(pair[1]):
            cur_only.append(pair)
    for pair in hyb - cur:
        if key(*pair) not in labels and readable(pair[0]) and readable(pair[1]):
            hyb_only.append(pair)

    for lst in (shared, cur_only, hyb_only):
        rng.shuffle(lst)
    return {
        "shared": shared[:n],
        "current_only": cur_only[:n],
        "challenger_only": hyb_only[:n],
    }, {"shared": len(shared), "current_only": len(cur_only), "challenger_only": len(hyb_only)}


def judge_pair(arm, i, j, ids, trads, labels, corpus_dir, base, model,
               max_tokens, timeout):
    a, b = ids[i], ids[j]
    lkey = (a, b) if a <= b else (b, a)
    body_a, body_b = chunk_body(a, corpus_dir), chunk_body(b, corpus_dir)
    out = {
        "arm": arm, "source_chunk": a, "target_chunk": b,
        "tradition_pair": "|".join(sorted((str(trads[i]), str(trads[j])))),
        "gold": labels.get(lkey), "error": None, "edge_type": None,
    }
    if body_a is None or body_b is None:
        out["error"] = "body missing"
        return out
    try:
        raw = call_judge(base, model,
                         build_edge_prompt(chunk_citation(a, corpus_dir), body_a,
                                           chunk_citation(b, corpus_dir), body_b),
                         max_tokens, timeout)
        et, conf, just = normalize_verdict(parse_edge_response(raw))
        out.update(edge_type=et, confidence=conf, justification=just[:400])
    except Exception as e:  # noqa: BLE001
        out["error"] = str(e)
    return out


def summarize(results):
    def pos(v):
        return v in POSITIVE_TYPES

    by_arm = defaultdict(list)
    for r in results:
        if not r["error"] and r["edge_type"]:
            by_arm[r["arm"]].append(r)

    print(f"\n{'=' * 78}\nCANDIDATE PROBE\n{'=' * 78}")
    print(f"{'arm':<16}{'n':>6}{'judge_pos':>12}{'claude_pos':>12}{'agreement':>12}")
    print("-" * 78)
    out = {}
    for arm in ("shared", "current_only", "challenger_only"):
        rs = by_arm.get(arm, [])
        if not rs:
            continue
        jp = sum(pos(r["edge_type"]) for r in rs) / len(rs)
        lab = [r for r in rs if r["gold"] is not None]
        # None, not NaN: the challenger arm has no labels by construction,
        # and bare NaN is not valid JSON.
        cp = sum(r["gold"] for r in lab) / len(lab) if lab else None
        ag = sum(pos(r["edge_type"]) == r["gold"] for r in lab) / len(lab) if lab else None
        out[arm] = {"n": len(rs), "judge_pos": jp, "claude_pos": cp, "agreement": ag}
        cps = f"{cp:.3f}" if cp is not None else "   —"
        ags = f"{ag:.3f}" if ag is not None else "   —"
        print(f"{arm:<16}{len(rs):>6}{jp:>12.3f}{cps:>12}{ags:>12}")

    if "shared" in out and "challenger_only" in out:
        s, h = out["shared"], out["challenger_only"]
        print(f"\ncalibration (from `shared`, which has Claude labels):")
        print(f"  judge says positive   {s['judge_pos']:.3f}")
        print(f"  Claude says positive  {s['claude_pos']:.3f}")
        bias = s["judge_pos"] - s["claude_pos"]
        print(f"  judge bias            {bias:+.3f}")
        print(f"\nchallenger raw judge positive rate     {h['judge_pos']:.3f}")
        print(f"bias-corrected estimate               {max(0.0, h['judge_pos'] - bias):.3f}")
        if "current_only" in out:
            c = out["current_only"]
            print(f"\ncurrent_only judge positive rate       {c['judge_pos']:.3f}")
            print(f"challenger   judge positive rate       {h['judge_pos']:.3f}")
            print(f"  -> same judge, same prompt: the DIFFERENCE is the signal")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--snapshot", type=Path)
    ap.add_argument("--n", type=int, default=120, help="pairs per arm")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--base-url", default="http://127.0.0.1:8080")
    ap.add_argument("--model", default="Qwen3.5-27B-UD-Q4_K_XL.gguf")
    ap.add_argument("--max-tokens", type=int, default=2048)
    ap.add_argument("--timeout", type=float, default=600.0)
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--strategy", default="worklevel", choices=["worklevel", "hybrid"])
    ap.add_argument("--pctile", type=float, default=90.0)
    ap.add_argument("--k-shrink", type=float, default=20.0)
    ap.add_argument("--work-floor", type=int, default=0)
    ap.add_argument("--per-chunk-min", type=int, default=2)
    ap.add_argument("--pair-floor", type=int, default=25)
    ap.add_argument("--per-chunk-cap", type=int, default=3)
    ap.add_argument("--explore", type=float, default=0.15)
    ap.add_argument("--min-obs", type=int, default=20)
    ap.add_argument("--out", type=Path, default=PROJECT_ROOT / "runs" / "edges" / "probe")
    args = ap.parse_args()

    cfg = load_config()
    db = (args.snapshot / "guru.db" if args.snapshot and args.snapshot.is_dir()
          else args.snapshot or latest_snapshot(cfg.rellm.snapshots))
    if db.resolve() == cfg.guru.db.resolve():
        raise SystemExit("refusing to read the live guru db — use a snapshot")
    print(f"snapshot: {db}  (read-only)")

    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    ids, trads, M, labels = load_state(conn)
    conn.close()

    idx_of = {c: i for i, c in enumerate(ids)}
    uniq = sorted(set(trads.tolist()))
    S = (M @ M.T).astype(np.float32)
    np.fill_diagonal(S, -1.0)
    yields = tradition_yield(labels, idx_of, trads)

    cur = select_current(S, trads, 5, 0.75)
    if args.strategy == "worklevel":
        chal = select_worklevel(S, ids, trads, labels, idx_of, len(cur),
                                args.pctile, args.k_shrink, args.per_chunk_cap,
                                args.work_floor)
    else:
        chal, _ = select_hybrid(S, trads, uniq, yields, len(cur),
                                args.per_chunk_min, args.pair_floor,
                                args.min_obs, args.explore, args.per_chunk_cap)
    print(f"current {len(cur):,}   {args.strategy} {len(chal):,}")

    rng = random.Random(args.seed)
    arms, pools = build_arms(cur, chal, ids, labels, rng, args.n, cfg.guru.corpus_dir)
    print("arm pool sizes: " + "  ".join(f"{k}={v:,}" for k, v in pools.items()))
    print("sampled:        " + "  ".join(f"{k}={len(v)}" for k, v in arms.items()))

    tasks = [(arm, i, j) for arm, pairs in arms.items() for i, j in pairs]
    run_dir = args.out / datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    run_dir.mkdir(parents=True, exist_ok=True)
    res_path = run_dir / "results.jsonl"
    print(f"judge: {args.model}  {len(tasks)} calls\nwriting {res_path}\n")

    results = []
    t0 = time.time()
    with res_path.open("w") as fh, ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futs = [ex.submit(judge_pair, arm, i, j, ids, trads, labels,
                          cfg.guru.corpus_dir, args.base_url, args.model,
                          args.max_tokens, args.timeout)
                for arm, i, j in tasks]
        for n, fut in enumerate(futs, 1):
            r = fut.result()
            results.append(r)
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            fh.flush()
            if n % 20 == 0 or n == len(futs):
                el = time.time() - t0
                print(f"  {n}/{len(futs)}  {el:.0f}s  "
                      f"eta {(len(futs) - n) * el / n / 60:.1f}m")

    s = summarize(results)
    (run_dir / "summary.json").write_text(json.dumps(s, indent=2))
    print(f"\nwrote {run_dir}")


if __name__ == "__main__":
    main()
