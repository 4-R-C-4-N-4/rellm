#!/usr/bin/env python3
"""edge_retrieval_sim.py — replay candidate-generation strategies offline.

Replays candidate generation against the snapshot's embeddings, read-only.
Every strategy is evaluated at a matched budget so the comparison is spend-
for-spend.

Strategies
----------
current   : the incumbent — global top-N cross-tradition neighbours gated by
            an absolute similarity floor (propose_edges.py --top-n 5
            --min-similarity 0.75).
budget    : a fixed candidate budget allocated across tradition pairs by
            measured yield (Wilson lower bound), taken top-down inside each
            pair block under a per-chunk cap.
hybrid    : budget, plus an unconditional per-chunk coverage floor.
worklevel : work-pair granularity — a relative per-block similarity
            percentile instead of a global constant, with yields shrunk
            work -> tradition -> grand mean. No coverage floor.

Scoring
-------
Coverage and balance are computed over all candidates. Yield is computed only
on the subset each strategy selects that already carries a post-review label —
new candidates have no ground truth, and that gap is reported, not hidden.

IMPORTANT: simulation cannot settle yield. Both `hybrid` and `worklevel`
simulated at or above the incumbent here and then lost decisively when their
novel candidates were actually judged (0.32 and 0.30 against 0.74 and 0.68).
Use tools/edge_candidate_probe.py before believing any of these numbers.
See docs/edges/edge-process-audit.md.

Usage:
    python3 tools/edge_retrieval_sim.py
    python3 tools/edge_retrieval_sim.py --budget 25000 --pctile 85
"""
from __future__ import annotations

import argparse
import math
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from rellm.config import load as load_config  # noqa: E402
from rellm.edges import POSITIVE_TYPES, REVIEWED_STATUS  # noqa: E402


def latest_snapshot(snapshots_dir: Path) -> Path:
    cands = sorted(d for d in snapshots_dir.iterdir() if d.is_dir())
    if not cands:
        raise SystemExit(f"no snapshots in {snapshots_dir}")
    return cands[-1] / "guru.db"


def wilson_lower(k: int, n: int, z: float = 1.96) -> float:
    if n == 0:
        return 0.0
    p = k / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    return max(0.0, (centre - margin) / denom)


def load_state(conn: sqlite3.Connection):
    rows = conn.execute(
        "SELECT ce.chunk_id, ce.vector, n.tradition_id t "
        "FROM chunk_embeddings ce JOIN nodes n ON n.id = ce.chunk_id "
        "WHERE n.type='chunk' ORDER BY ce.chunk_id"
    ).fetchall()
    ids = [r["chunk_id"] for r in rows]
    trads = np.array([r["t"] or r["chunk_id"].split(".")[0] for r in rows])
    M = np.stack([np.frombuffer(r["vector"], dtype=np.float32) for r in rows])
    M = M / np.linalg.norm(M, axis=1, keepdims=True)

    # Post-review labels, keyed by unordered chunk pair.
    labels: dict[tuple[str, str], bool] = {}
    ph = ",".join("?" for _ in REVIEWED_STATUS)
    for src, tgt, et in conn.execute(
        f"SELECT source_chunk, target_chunk, edge_type FROM staged_edges "
        f"WHERE status IN ({ph})", list(REVIEWED_STATUS)
    ):
        labels[(src, tgt) if src <= tgt else (tgt, src)] = et in POSITIVE_TYPES

    return ids, trads, M, labels


def tradition_yield(labels, idx_of, trads) -> dict[tuple[str, str], tuple[int, int]]:
    """(accepted, total) per unordered tradition pair, from labelled pairs."""
    agg: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0, 0])
    for (a, b), pos in labels.items():
        ia, ib = idx_of.get(a), idx_of.get(b)
        if ia is None or ib is None:
            continue
        ta, tb = trads[ia], trads[ib]
        key = (ta, tb) if ta <= tb else (tb, ta)
        agg[key][1] += 1
        agg[key][0] += int(pos)
    return {k: tuple(v) for k, v in agg.items()}


def select_current(S, trads, top_n: int, min_sim: float) -> set[tuple[int, int]]:
    """Incumbent: global top-N cross-tradition, absolute similarity floor."""
    out: set[tuple[int, int]] = set()
    n = S.shape[0]
    for i in range(n):
        row = S[i].copy()
        row[trads == trads[i]] = -1.0        # exclude same tradition
        row[i] = -1.0
        k = min(top_n, n - 1)
        cand = np.argpartition(-row, k)[:k]
        for j in cand:
            if row[j] >= min_sim:
                out.add((i, j) if i < j else (j, i))
    return out


def allocate(weights: dict, tw: float, total_budget: int, floor: int,
             label: str) -> dict:
    """Split `total_budget` across pairs: a floor for every pair, the rest by
    weight.

    The floor is spent *inside* the budget, not added on top of it. Doing
    `max(floor, share)` only ever adds, so with 253 tradition pairs and a
    floor of 25 at least 6,325 candidates were forced regardless of the
    requested budget — `--budget` was inert below that and the strategies were
    never actually compared at matched spend.
    """
    n = len(weights) or 1
    floor_total = floor * n
    if floor_total > total_budget:
        floor = total_budget // n
        floor_total = floor * n
        print(f"  note: {label} floor exceeded the budget; lowered to {floor}/pair")
    remaining = max(0, total_budget - floor_total)
    return {k: floor + int(round(remaining * w / tw)) for k, w in weights.items()}


def select_budget(S, trads, uniq, yields, total_budget: int,
                  floor: int, min_obs: int, explore: float,
                  per_chunk_cap: int = 3):
    """Allocate a fixed candidate budget across tradition pairs, then take the
    top-scoring chunk pairs inside each.

    Per-chunk top-k is the wrong unit: with 23 traditions even k=1 forces
    ~61k candidates. Allocating per tradition *pair* decouples spend from
    (chunks x traditions) and still guarantees every pair a non-zero share,
    which is what breaks the absolute-floor bias.

    Weight = (measured yield + explore) * sqrt(block size). The yield term
    exploits the matrix; the explore constant keeps unmeasured pairs alive;
    sqrt(size) stops the two largest traditions from eating the budget.
    """
    cols = {t: np.where(trads == t)[0] for t in uniq}

    weights: dict[tuple[str, str], float] = {}
    for a in range(len(uniq)):
        for b in range(a + 1, len(uniq)):
            t1, t2 = uniq[a], uniq[b]
            n1, n2 = cols[t1].size, cols[t2].size
            if n1 == 0 or n2 == 0:
                continue
            acc, n = yields.get((t1, t2), (0, 0))
            y = wilson_lower(acc, n) if n >= min_obs else None
            score = (y if y is not None else explore) + explore
            weights[(t1, t2)] = score * math.sqrt(n1 * n2)

    tw = sum(weights.values()) or 1.0
    alloc = allocate(weights, tw, total_budget, floor, "tradition")

    out: set[tuple[int, int]] = set()
    for (t1, t2), m in alloc.items():
        i_idx, j_idx = cols[t1], cols[t2]
        block = S[np.ix_(i_idx, j_idx)]
        m = min(m, block.size)
        if m <= 0:
            continue

        # Take a margin over the allocation, then fill greedily by descending
        # similarity subject to a per-chunk cap. Without the cap, top-M inside
        # a block collapses onto a few hub chunks and coverage drops.
        pool = min(block.size, max(m * 8, m + 64))
        flat = np.argpartition(block.ravel(), -pool)[-pool:]
        flat = flat[np.argsort(-block.ravel()[flat])]

        deg: dict[int, int] = defaultdict(int)
        taken = 0
        for f in flat:
            if taken >= m:
                break
            i = i_idx[f // j_idx.size]
            j = j_idx[f % j_idx.size]
            if i == j:
                continue
            if deg[i] >= per_chunk_cap or deg[j] >= per_chunk_cap:
                continue
            key = (i, j) if i < j else (j, i)
            if key in out:
                continue
            out.add(key)
            deg[i] += 1
            deg[j] += 1
            taken += 1
    return out, alloc


def select_hybrid(S, trads, uniq, yields, total_budget: int,
                  per_chunk_min: int, floor: int, min_obs: int,
                  explore: float, per_chunk_cap: int):
    """Coverage floor first, then yield-weighted spend on the remainder.

    Two failure modes need fixing at once. An absolute similarity floor
    starves semantically distant traditions (they never clear it); a pure
    tradition-pair budget starves individual chunks (the greedy fills by
    similarity and low-similarity chunks are never reached).

    So: give every chunk its top-`per_chunk_min` cross-tradition neighbours
    unconditionally — no similarity threshold, which is what guarantees
    native_american and hinduism chunks enter the graph at all — then spend
    what's left where the matrix says yield is highest.
    """
    out: set[tuple[int, int]] = set()

    # Pass 1 — unconditional per-chunk coverage floor.
    for i in range(S.shape[0]):
        row = S[i].copy()
        row[trads == trads[i]] = -1.0
        row[i] = -1.0
        k = min(per_chunk_min, row.size - 1)
        if k <= 0:
            continue
        for j in np.argpartition(-row, k)[:k]:
            out.add((i, j) if i < j else (j, i))

    # Pass 2 — yield-weighted allocation over whatever budget remains.
    if len(out) > total_budget:
        print(f"  note: hybrid's {per_chunk_min}/chunk coverage floor costs "
              f"{len(out):,}, over the {total_budget:,} budget — this strategy "
              f"cannot be compared at matched spend below that.")
    remaining = max(0, total_budget - len(out))
    if remaining:
        extra, alloc = select_budget(S, trads, uniq, yields, remaining,
                                     floor, min_obs, explore, per_chunk_cap)
        out |= extra
    else:
        alloc = {}
    return out, alloc


def work_of(chunk_id: str) -> str:
    p = chunk_id.split(".", 2)
    return f"{p[0]}/{p[1]}" if len(p) >= 3 else chunk_id


def pair_yields(labels, idx_of, keyfn):
    """(accepted, total) per unordered key pair, from labelled chunk pairs."""
    agg = defaultdict(lambda: [0, 0])
    for (a, b), pos in labels.items():
        if a not in idx_of or b not in idx_of:
            continue
        ka, kb = keyfn(a), keyfn(b)
        key = (ka, kb) if ka <= kb else (kb, ka)
        agg[key][1] += 1
        agg[key][0] += int(pos)
    return {k: tuple(v) for k, v in agg.items()}


def select_worklevel(S, ids, trads, labels, idx_of, total_budget: int,
                     pctile: float, k_shrink: float, per_chunk_cap: int,
                     pair_floor: int):
    """Work-pair granularity, with a relative threshold and shrunk yields.

    Two corrections over `hybrid`:

    1. The threshold is a percentile of each *work pair's own* similarity
       block, not a global constant. 35% of accept-rate variance lives
       between works inside a tradition pair (Iamblichus<->Agrippa 0.059 vs
       Iamblichus<->Heroic-Enthusiasts 0.946), so a tradition-level constant
       averages over pairs that behave nothing alike. The percentile needs no
       labels — it is pure embedding arithmetic, available for every block.

    2. No unconditional per-chunk coverage floor. That is what sank `hybrid`:
       forcing every chunk in dragged candidates down to 0.595 similarity and
       yield collapsed to 0.32. Some chunks have no cross-tradition partner
       and buying them one buys noise.

    Budget uses a hierarchical shrink work -> tradition -> grand mean, so thin
    work cells fall back rather than overfitting their handful of labels.
    """
    works = np.array([work_of(c) for c in ids])
    w_of_t = {w: t for w, t in zip(works, trads)}

    y_work = pair_yields(labels, idx_of, work_of)
    y_trad = pair_yields(labels, idx_of, lambda c: c.split(".")[0])
    tot_a = sum(a for a, _ in y_trad.values())
    tot_n = sum(n for _, n in y_trad.values())
    grand = tot_a / tot_n if tot_n else 0.5

    def shrunk_rate(wpair):
        w1, w2 = wpair
        t1, t2 = w_of_t[w1], w_of_t[w2]
        tk = (t1, t2) if t1 <= t2 else (t2, t1)
        ta, tn = y_trad.get(tk, (0, 0))
        r_trad = (ta + k_shrink * grand) / (tn + k_shrink)
        wa, wn = y_work.get(wpair, (0, 0))
        return (wa + k_shrink * r_trad) / (wn + k_shrink)

    wcols = defaultdict(list)
    for i, w in enumerate(works):
        wcols[w].append(i)
    wcols = {w: np.array(v) for w, v in wcols.items()}
    wnames = sorted(wcols)

    # Weight each cross-tradition work pair by shrunk yield * sqrt(block size).
    weights = {}
    for a in range(len(wnames)):
        for b in range(a + 1, len(wnames)):
            w1, w2 = wnames[a], wnames[b]
            if w_of_t[w1] == w_of_t[w2]:
                continue
            n1, n2 = wcols[w1].size, wcols[w2].size
            if n1 == 0 or n2 == 0:
                continue
            weights[(w1, w2)] = shrunk_rate((w1, w2)) * math.sqrt(n1 * n2)

    tw = sum(weights.values()) or 1.0
    alloc = allocate(weights, tw, total_budget, pair_floor, "work-pair")
    out: set[tuple[int, int]] = set()

    for (w1, w2), wgt in weights.items():
        m = alloc[(w1, w2)]
        i_idx, j_idx = wcols[w1], wcols[w2]
        block = S[np.ix_(i_idx, j_idx)]
        if block.size == 0:
            continue
        m = min(m, block.size)

        # Relative floor: only this block's own top (100-pctile)% is eligible.
        thresh = float(np.percentile(block, pctile))

        pool = min(block.size, max(m * 8, m + 64))
        flat = np.argpartition(block.ravel(), -pool)[-pool:]
        flat = flat[np.argsort(-block.ravel()[flat])]

        deg = defaultdict(int)
        taken = 0
        for f in flat:
            if taken >= m:
                break
            if block.ravel()[f] < thresh:
                break                      # sorted desc: nothing below qualifies
            i = i_idx[f // j_idx.size]
            j = j_idx[f % j_idx.size]
            if i == j or deg[i] >= per_chunk_cap or deg[j] >= per_chunk_cap:
                continue
            key = (i, j) if i < j else (j, i)
            if key in out:
                continue
            out.add(key)
            deg[i] += 1
            deg[j] += 1
            taken += 1
    return out


def evaluate(name, sel, ids, trads, labels, uniq):
    n_chunks = len(ids)
    covered = set()
    per_trad_pair: dict[tuple[str, str], int] = defaultdict(int)
    per_trad: dict[str, int] = defaultdict(int)
    for i, j in sel:
        covered.add(i); covered.add(j)
        ta, tb = trads[i], trads[j]
        per_trad_pair[(ta, tb) if ta <= tb else (tb, ta)] += 1
        per_trad[ta] += 1
        per_trad[tb] += 1

    lab_hit = 0
    lab_pos = 0
    for i, j in sel:
        a, b = ids[i], ids[j]
        key = (a, b) if a <= b else (b, a)
        if key in labels:
            lab_hit += 1
            lab_pos += int(labels[key])

    # Balance: normalised entropy of per-tradition candidate mass, and the
    # per-chunk rate for the most- and least-served traditions.
    counts = np.array([per_trad[t] for t in uniq], dtype=float)
    p = counts / counts.sum() if counts.sum() else counts
    nz = p[p > 0]
    entropy = float(-(nz * np.log(nz)).sum() / math.log(len(uniq))) if len(uniq) > 1 else 0.0

    trad_sizes = {t: int((trads == t).sum()) for t in uniq}
    per_chunk = {t: per_trad[t] / trad_sizes[t] for t in uniq if trad_sizes[t]}
    starved = sorted(per_chunk.items(), key=lambda kv: kv[1])[:4]

    return {
        "name": name,
        "pairs": len(sel),
        "chunk_coverage": len(covered) / n_chunks,
        "chunks_uncovered": n_chunks - len(covered),
        "tradition_pairs_touched": len(per_trad_pair),
        "max_tradition_pairs": len(uniq) * (len(uniq) - 1) // 2,
        "labelled_overlap": lab_hit,
        "yield_on_labelled": lab_pos / lab_hit if lab_hit else float("nan"),
        "unlabelled": len(sel) - lab_hit,
        "balance_entropy": entropy,
        "starved": starved,
    }


def print_eval(e):
    print(f"\n--- {e['name']} ---")
    print(f"  candidate pairs          {e['pairs']:,}")
    print(f"  chunk coverage           {e['chunk_coverage']:.1%}  "
          f"({e['chunks_uncovered']:,} chunks with no candidate)")
    print(f"  tradition pairs touched  {e['tradition_pairs_touched']} / {e['max_tradition_pairs']} possible")
    print(f"  balance entropy          {e['balance_entropy']:.3f}  (1.0 = uniform)")
    print(f"  overlap with labels      {e['labelled_overlap']:,}")
    print(f"  yield on labelled subset {e['yield_on_labelled']:.3f}")
    print(f"  unlabelled (no truth)    {e['unlabelled']:,}")
    print(f"  least-served traditions  " +
          ", ".join(f"{t} {v:.1f}/chunk" for t, v in e["starved"]))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--snapshot", type=Path)
    ap.add_argument("--top-n", type=int, default=5, help="incumbent top-N")
    ap.add_argument("--min-sim", type=float, default=0.75, help="incumbent floor")
    ap.add_argument("--min-obs", type=int, default=20,
                    help="labelled pairs needed before a yield is trusted")
    ap.add_argument("--budget", type=int, default=0,
                    help="budget strategy: total candidates (0 = match incumbent)")
    ap.add_argument("--pair-floor", type=int, default=25,
                    help="budget strategy: minimum candidates per tradition pair")
    ap.add_argument("--explore", type=float, default=0.15,
                    help="budget strategy: weight given to unmeasured pairs")
    ap.add_argument("--pctile", type=float, default=90.0,
                    help="worklevel: per-block similarity percentile floor")
    ap.add_argument("--k-shrink", type=float, default=20.0,
                    help="worklevel: hierarchical shrinkage constant")
    ap.add_argument("--work-floor", type=int, default=0,
                    help="worklevel: minimum candidates per work pair. Default 0 "
                         "because there are 24,299 cross-tradition work pairs — "
                         "a floor of 1 alone exceeds the whole budget. Must match "
                         "edge_candidate_probe.py's default or the sim and the "
                         "probe describe different selections.")
    ap.add_argument("--per-chunk-min", type=int, default=2,
                    help="hybrid: guaranteed candidates per chunk (coverage floor)")
    ap.add_argument("--per-chunk-cap", type=int, default=3,
                    help="budget strategy: max candidates per chunk per tradition pair")
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
    print(f"chunks {len(ids):,}   traditions {len(uniq)}   labelled pairs {len(labels):,}")

    print("computing similarity matrix...")
    S = (M @ M.T).astype(np.float32)
    np.fill_diagonal(S, -1.0)

    yields = tradition_yield(labels, idx_of, trads)
    rates = {k: wilson_lower(a, n) for k, (a, n) in yields.items() if n >= args.min_obs}
    if rates:
        print(f"trusted tradition-pair yields: {len(rates)} cells "
              f"(Wilson lower {min(rates.values()):.3f}–{max(rates.values()):.3f}, "
              f"min_obs={args.min_obs})")

    print("selecting: current...")
    cur = select_current(S, trads, args.top_n, args.min_sim)

    budget = args.budget or len(cur)      # match the incumbent's spend by default
    print(f"selecting: budget (target {budget:,} candidates)...")
    bdg, alloc = select_budget(S, trads, uniq, yields, budget,
                               args.pair_floor, args.min_obs, args.explore,
                               args.per_chunk_cap)

    e_cur = evaluate(f"current  (top-{args.top_n}, sim>={args.min_sim})",
                     cur, ids, trads, labels, uniq)
    print(f"selecting: hybrid (coverage floor {args.per_chunk_min}/chunk + yield)...")
    hyb, _ = select_hybrid(S, trads, uniq, yields, budget, args.per_chunk_min,
                           args.pair_floor, args.min_obs, args.explore,
                           args.per_chunk_cap)

    print(f"selecting: worklevel (p{args.pctile:.0f} per-block floor, shrink k={args.k_shrink})...")
    wlv = select_worklevel(S, ids, trads, labels, idx_of, budget, args.pctile,
                           args.k_shrink, args.per_chunk_cap, args.work_floor)

    e_bdg = evaluate(f"budget   (yield-allocated, floor {args.pair_floor}/pair)",
                     bdg, ids, trads, labels, uniq)
    e_hyb = evaluate(f"hybrid   ({args.per_chunk_min}/chunk floor + yield)",
                     hyb, ids, trads, labels, uniq)
    e_wlv = evaluate(f"worklevel (p{args.pctile:.0f} block floor, shrunk yield)",
                     wlv, ids, trads, labels, uniq)
    print_eval(e_cur)
    print_eval(e_bdg)
    print_eval(e_hyb)
    print_eval(e_wlv)

    print(f"\n{'=' * 74}\nCOMPARISON (budget matched)\n{'=' * 74}")
    max_tp = e_cur["max_tradition_pairs"]
    hdr = f"{'metric':<24}{'current':>11}{'budget':>11}{'hybrid':>11}{'worklevel':>11}"
    print(hdr); print("-" * 74)
    def row(lbl, f, fmt="{:.3f}"):
        print(f"{lbl:<24}" + "".join(fmt.format(f(e)).rjust(11)
                                     for e in (e_cur, e_bdg, e_hyb, e_wlv)))
    row("candidate pairs", lambda e: e["pairs"], "{:,.0f}")
    row("chunk coverage", lambda e: e["chunk_coverage"] * 100, "{:.1f}%")
    row(f"tradition pairs /{max_tp}", lambda e: e["tradition_pairs_touched"], "{:,.0f}")
    row("balance entropy", lambda e: e["balance_entropy"])
    row("yield on labelled", lambda e: e["yield_on_labelled"])
    row("labelled overlap", lambda e: e["labelled_overlap"], "{:,.0f}")

    # How much of the incumbent's accepted mass would rank retrieval keep?
    def acc_kept(sel):
        keep = 0
        for i, j in sel:
            a, b = ids[i], ids[j]
            key = (a, b) if a <= b else (b, a)
            if labels.get(key):
                keep += 1
        return keep
    total_acc = sum(1 for v in labels.values() if v)
    print(f"\n  known accepted edges re-selected (REFERENCE-BIASED — see note):")
    for lbl, sel in (("current", cur), ("budget", bdg), ("hybrid", hyb), ("worklevel", wlv)):
        print(f"    {lbl:<9}{acc_kept(sel):>7,} / {total_acc:,} "
              f"({acc_kept(sel) / total_acc:5.1%})")
    print("""
  NOTE: labels exist only for pairs the incumbent proposed, so this metric
  scores 'current' against its own historical output. It measures agreement
  with the existing graph, NOT recall of true parallels. A new strategy that
  explores elsewhere is penalised for looking where nobody has labelled.
  Yield-on-labelled is the fairer comparison; coverage and balance are
  measured over all candidates and are not reference-biased.""")


if __name__ == "__main__":
    main()
