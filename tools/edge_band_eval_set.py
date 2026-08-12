#!/usr/bin/env python3
"""edge_band_eval_set.py — build the frozen rank 6–50 eval set (Phase 1, step 1).

The reranker's ship gate is precision@top-20% within neighbour rank 6–50, but
labels exist almost exclusively where the incumbent looked (rank ≤5, sim
≥0.75). This tool samples the gated band so it can be graded fresh.

Leakage, and why the partition is over *works* rather than pairs
----------------------------------------------------------------
A cross-encoder that has seen a passage in training can score it by memorised
prior rather than by pair compatibility, so a passage must not appear on both
sides. Pair-level grouping does not deliver that: hold out the group (A, B)
and work A still reaches training through (A, C). The partition therefore
assigns whole *works* to train or eval, and a pair is usable only if both of
its works land on the same side. Pairs straddling the split are discarded.

Work is the right unit rather than text: sources/works.toml declares works
spanning many text ids (agrippa-natural-magic is 74, dhammapada 26), so
text-level splitting puts chapters of one treatise on both sides.

That rigour is expensive here — 62 works, densely interconnected — so the
report mode prints the cost before anything is frozen. The holdout is chosen
by *stratified random* selection across traditions with a fixed seed,
deliberately NOT by searching for the split that preserves the most training
data: that search selects peripheral, low-degree works and games the eval.

Usage:
    python3 tools/edge_band_eval_set.py --report
    python3 tools/edge_band_eval_set.py --report --holdout-works 16
    python3 tools/edge_band_eval_set.py --emit --target 400
    python3 tools/edge_band_eval_set.py --show 7 --run runs/edges/band-eval/<ts>
"""
from __future__ import annotations

import argparse
import collections
import json
import random
import sqlite3
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from rellm.config import load as load_config          # noqa: E402
from rellm.corpus import chunk_body, chunk_citation   # noqa: E402
from rellm.edges import (                             # noqa: E402
    EDGE_SYSTEM_PROMPT, POSITIVE_TYPES, REVIEWED_STATUS,
    _text_id, build_edge_prompt,
)

def review_rubric(cfg) -> str:
    """guru's node-14 review rubric, read from the repo rather than copied.

    The stored labels were produced by this rubric, not by the proposal prompt
    in rellm.edges — the two set opposite thresholds. The proposal prompt is
    written to stop the proposer under-calling structural mythemes; the review
    rubric exists to catch pairs that merely share a topic ("the bar is a
    shared conceptual move"). Grading the band with the proposal prompt made
    the eval incommensurable with the labels the model trains on, which is
    what the calibration arm caught.

    The rubric's own task template interpolates a proposing model's verdict,
    confidence and justification. Band pairs were never proposed, so those
    fields are dropped and the bar is applied to the pair directly.
    """
    raw = (cfg.guru.repo / "prompts" / "ingest" / "edge-review.md").read_text()
    body = raw.split("---", 2)[-1]                    # drop TOML frontmatter
    body = body.split("## Task", 1)
    system = body[0].replace("## System", "").strip()
    tells = body[1] if len(body) > 1 else ""
    tells = tells.split("```")[-1].strip()            # drop the fill-in template
    return f"{system}\n\n{tells}"


BAND_LO, BAND_HI = 6, 50
SUB_BANDS = ((6, 10), (11, 25), (26, 50))
SEED = 20260812


# ── snapshot state ───────────────────────────────────────────────────────────

def latest_snapshot(snapshots_dir: Path) -> Path:
    cands = sorted(d for d in snapshots_dir.iterdir() if d.is_dir())
    if not cands:
        raise SystemExit(f"no snapshots in {snapshots_dir} — run `rellm snapshot`")
    return cands[-1]


def load_state(conn: sqlite3.Connection):
    rows = conn.execute(
        "SELECT ce.chunk_id, ce.vector, n.tradition_id t "
        "FROM chunk_embeddings ce JOIN nodes n ON n.id = ce.chunk_id "
        "WHERE n.type='chunk' ORDER BY ce.chunk_id"
    ).fetchall()
    ids = [r[0] for r in rows]
    trads = np.array([r[2] or r[0].split(".")[0] for r in rows])
    M = np.stack([np.frombuffer(r[1], dtype=np.float32) for r in rows])
    M = M / np.linalg.norm(M, axis=1, keepdims=True)

    labelled: dict[tuple[str, str], bool] = {}
    ph = ",".join("?" for _ in REVIEWED_STATUS)
    for src, tgt, et in conn.execute(
        f"SELECT source_chunk, target_chunk, edge_type FROM staged_edges "
        f"WHERE status IN ({ph})", list(REVIEWED_STATUS)
    ):
        labelled[(src, tgt) if src <= tgt else (tgt, src)] = et in POSITIVE_TYPES
    return ids, trads, M, labelled


def work_map(cfg) -> dict[str, str]:
    """text_id → work_id, for texts belonging to a declared multi-text work."""
    path = cfg.guru.repo / "sources" / "works.toml"
    d = tomllib.loads(path.read_text())
    return {t: w["id"]
            for w in (d.get("work") or d.get("works") or [])
            for t in w.get("texts", w.get("members", []))}


def work_of(chunk_id: str, t2w: dict[str, str]) -> str:
    """`tradition/work` — falls back to the text id for unaffiliated texts."""
    tid = _text_id(chunk_id)
    return f"{chunk_id.split('.')[0]}/{t2w.get(tid, tid)}"


# ── partition ────────────────────────────────────────────────────────────────
#
# The unit is per tradition, because a uniform one does not survive contact
# with the corpus:
#
#   - 16 traditions own two or more works, so the unit is the **work** and
#     train/eval share no treatise.
#   - 7 own exactly one (celtic, finnic, hermeticism, mandaean, shinto,
#     sufism, upanishads). A work-level split there is all-or-nothing, and
#     holding the work out erases the tradition from training entirely —
#     which for hermeticism, the hub that lands in everyone's top-5, would
#     distort both the model and the gate. So the unit falls back to the
#     **text**, and those eval pairs are flagged `text-disjoint`: train and
#     eval can share a treatise but never a passage.
#
# Every tradition therefore keeps material on both sides, and the milder
# leak is confined to pairs the artifact marks, so band precision can be
# reported with and without them.

def unit_of(chunk_id: str, t2w: dict[str, str], text_level: set[str]) -> str:
    w = work_of(chunk_id, t2w)
    if w.split("/")[0] in text_level:
        return f"{w}#{_text_id(chunk_id)}"
    return w


def partition_units(units_by_trad: dict[str, list[str]], frac: float,
                    seed: int, n_trads: int | None = None) -> set[str]:
    """Stratified random holdout, fixed seed, every tradition represented.

    Not optimised for training-set retention: searching for the cheapest
    holdout selects peripheral low-degree works and games the eval toward
    exactly the thin material the gate is supposed to judge fairly.
    """
    rng = random.Random(seed)
    splittable = sorted(t for t, us in units_by_trad.items() if len(us) >= 2)
    if n_trads is not None and n_trads < len(splittable):
        # Every pair is cross-tradition, so a pair survives into training only
        # if BOTH endpoints dodge the holdout. Drawing from every tradition
        # therefore straddles ~half the corpus. Narrowing the holdout to a
        # random subset of traditions buys training mass back, at the cost of
        # eval breadth — the knob this exposes.
        rng.shuffle(splittable)
        splittable = splittable[:n_trads]
    out: set[str] = set()
    for t in sorted(splittable):
        us = sorted(units_by_trad[t])
        rng.shuffle(us)
        k = min(len(us) - 1, max(1, round(len(us) * frac)))
        out |= set(us[:k])
    return out


# ── band candidates ──────────────────────────────────────────────────────────

def band_pairs(M, trads, ids, top: int = BAND_HI):
    """Unordered cross-tradition pairs with their best-direction rank.

    Rank is taken as the better of the two directions, matching how the audit
    pooled the probe results.
    """
    n = len(ids)
    best: dict[tuple[int, int], int] = {}
    for i in range(n):
        sims = M @ M[i]
        sims[trads == trads[i]] = -np.inf      # cross-tradition only
        sims[i] = -np.inf
        idx = np.argpartition(-sims, top)[:top]
        idx = idx[np.argsort(-sims[idx])]
        for rank, j in enumerate(idx, start=1):
            if not np.isfinite(sims[j]):
                continue
            key = (i, int(j)) if i < j else (int(j), i)
            if rank < best.get(key, 10**9):
                best[key] = rank
    return best


def sub_band(rank: int) -> tuple[int, int] | None:
    for lo, hi in SUB_BANDS:
        if lo <= rank <= hi:
            return (lo, hi)
    return None


def stratified_sample(cands, target, seed):
    """Even thirds across sub-bands; within each, round-robin over tradition
    pairs so no single pair dominates and coverage is as wide as the pool
    allows."""
    rng = random.Random(seed)
    per_band = max(1, target // len(SUB_BANDS))
    chosen = []
    for band in SUB_BANDS:
        pool: dict[tuple[str, str], list] = collections.defaultdict(list)
        for c in cands:
            if c["sub_band"] == list(band):
                pool[tuple(c["tradition_pair"])].append(c)
        for v in pool.values():
            rng.shuffle(v)
        keys = sorted(pool)
        rng.shuffle(keys)
        picked, exhausted = [], False
        while len(picked) < per_band and not exhausted:
            exhausted = True
            for k in keys:
                if pool[k]:
                    picked.append(pool[k].pop())
                    exhausted = False
                    if len(picked) >= per_band:
                        break
        chosen.extend(picked)
    return chosen


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--report", action="store_true", help="print the split cost, write nothing")
    ap.add_argument("--emit", action="store_true", help="freeze the eval set")
    ap.add_argument("--show", type=int, help="print the grading prompt for pair N")
    ap.add_argument("--rubric", choices=("propose", "review"), default="propose",
                    help="which threshold to grade against; 'review' matches "
                         "the rubric that produced the stored labels")
    ap.add_argument("--show-calib", type=int, help="print the prompt for calibration pair N")
    ap.add_argument("--emit-calibration", type=int, default=0,
                    help="also sample N already-labelled pairs as a grader control")
    ap.add_argument("--run", type=Path, help="run dir (with --show)")
    ap.add_argument("--holdout-traditions", type=int, default=None,
                    help="how many traditions contribute units to the holdout")
    ap.add_argument("--holdout-frac", type=float, default=0.25,
                    help="fraction of each tradition's units held out")
    ap.add_argument("--target", type=int, default=400)
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()

    cfg = load_config()
    corpus = cfg.guru.repo / "corpus"

    if args.emit_calibration and args.run:
        # Add a calibration arm to an EXISTING run, reusing its frozen
        # partition — re-running --emit would resample the band and orphan
        # grading already in flight.
        part = json.loads((args.run / "partition.json").read_text())
        eval_works = set(part["holdout_units"])
        text_level = set(part["text_level_traditions"])
        snap = latest_snapshot(cfg.rellm.snapshots)
        conn = sqlite3.connect(f"file:{snap/'guru.db'}?mode=ro", uri=True)
        ids, trads, M, labelled = load_state(conn)
        t2w = work_map(cfg)
        wof = {c: unit_of(c, t2w, text_level) for c in ids}
        rng = random.Random(args.seed + 1)
        pool = [(a, b, g) for (a, b), g in labelled.items()
                if a in wof and b in wof
                and wof[a] in eval_works and wof[b] in eval_works
                and chunk_body(a, corpus) is not None
                and chunk_body(b, corpus) is not None]
        rng.shuffle(pool)
        rows = [{"idx": n, "a": a, "b": b,
                 "citation_a": chunk_citation(a, corpus),
                 "citation_b": chunk_citation(b, corpus), "gold_positive": g}
                for n, (a, b, g) in enumerate(pool[:args.emit_calibration])]
        (args.run / "calib.jsonl").write_text(
            "".join(json.dumps({k: v for k, v in r.items() if k != "gold_positive"}) + "\n"
                    for r in rows))
        (args.run / "calib_gold.json").write_text(json.dumps(
            {str(r["idx"]): r["gold_positive"] for r in rows}, indent=2))
        gp = sum(r["gold_positive"] for r in rows)
        print(f"calibration arm: {len(rows)} already-labelled pairs "
              f"({gp} positive / {len(rows)-gp} negative by stored label) -> {args.run}")
        print("gold withheld from calib.jsonl; graders see the same blind prompt")
        return

    if args.show_calib is not None:
        run = args.run or sorted(d for d in (PROJECT_ROOT / "runs/edges/band-eval").iterdir()
                                 if d.is_dir())[-1]
        rows = [json.loads(l) for l in (run / "calib.jsonl").read_text().splitlines()]
        p = rows[args.show_calib]
        print(f"### calibration pair {args.show_calib}  [{p['a']} | {p['b']}]\n")
        if args.rubric == "review":
            print(review_rubric(cfg))
            print(f"\n---\n\nA ({p['citation_a']}):\n\"\"\"\n"
                  f"{chunk_body(p['a'], corpus) or ''}\n\"\"\"\n")
            print(f"B ({p['citation_b']}):\n\"\"\"\n"
                  f"{chunk_body(p['b'], corpus) or ''}\n\"\"\"\n")
            print("Respond with a single JSON object and no prose outside it:\n"
                  '{"edge_type": "<PARALLELS|CONTRASTS|surface_only|unrelated>", '
                  '"confidence": <0.0-1.0>, "justification": "<one to two sentences>"}')
        else:
            print(EDGE_SYSTEM_PROMPT)
            print(build_edge_prompt(p["citation_a"], chunk_body(p["a"], corpus) or "",
                                    p["citation_b"], chunk_body(p["b"], corpus) or ""))
        return

    if args.show is not None:
        run = args.run or sorted(d for d in (PROJECT_ROOT / "runs/edges/band-eval").iterdir() if d.is_dir())[-1]
        rows = [json.loads(l) for l in (run / "pairs.jsonl").read_text().splitlines()]
        p = rows[args.show]
        # Rank and similarity are deliberately withheld: they are the
        # retrieval signal the gate exists to test independently, and a
        # grader who sees them cannot be blind to it.
        print(f"### pair {args.show}  [{p['a']} | {p['b']}]\n")
        if args.rubric == "review":
            print(review_rubric(cfg))
            print(f"\n---\n\nA ({p['citation_a']}):\n\"\"\"\n"
                  f"{chunk_body(p['a'], corpus) or ''}\n\"\"\"\n")
            print(f"B ({p['citation_b']}):\n\"\"\"\n"
                  f"{chunk_body(p['b'], corpus) or ''}\n\"\"\"\n")
            print("Respond with a single JSON object and no prose outside it:\n"
                  '{"edge_type": "<PARALLELS|CONTRASTS|surface_only|unrelated>", '
                  '"confidence": <0.0-1.0>, "justification": "<one to two sentences>"}')
        else:
            print(EDGE_SYSTEM_PROMPT)
            print(build_edge_prompt(p["citation_a"], chunk_body(p["a"], corpus) or "",
                                    p["citation_b"], chunk_body(p["b"], corpus) or ""))
        return

    snap = latest_snapshot(cfg.rellm.snapshots)
    conn = sqlite3.connect(f"file:{snap/'guru.db'}?mode=ro", uri=True)
    ids, trads, M, labelled = load_state(conn)
    t2w = work_map(cfg)
    print(f"snapshot: {snap.name}   chunks {len(ids):,}   labelled pairs {len(labelled):,}")

    # Traditions owning a single work split at text level instead (see above).
    works_by_trad = collections.defaultdict(set)
    for c in ids:
        w = work_of(c, t2w)
        works_by_trad[w.split("/")[0]].add(w)
    text_level = {t for t, ws in works_by_trad.items() if len(ws) == 1}

    wof = {c: unit_of(c, t2w, text_level) for c in ids}
    units_by_trad = collections.defaultdict(list)
    for u in sorted(set(wof.values())):
        units_by_trad[u.split("/")[0]].append(u)

    eval_works = partition_units(units_by_trad, args.holdout_frac, args.seed,
                                 args.holdout_traditions)
    print(f"units: {len(set(wof.values()))} "
          f"({len(works_by_trad) - len(text_level)} traditions split by work, "
          f"{len(text_level)} by text)")
    print(f"holdout: {len(eval_works)} units across "
          f"{len({w.split('/')[0] for w in eval_works})} traditions (seed {args.seed}, "
          f"frac {args.holdout_frac})")
    orphan = [t for t, us in units_by_trad.items() if set(us) <= eval_works]
    print(f"traditions with nothing left in training: {len(orphan)} {orphan}")

    train = ee = straddle = 0
    for (a, b) in labelled:
        ia, ib = wof.get(a), wof.get(b)
        if ia is None or ib is None:
            continue
        if ia in eval_works and ib in eval_works:
            ee += 1
        elif ia not in eval_works and ib not in eval_works:
            train += 1
        else:
            straddle += 1
    tot = train + ee + straddle
    print(f"\nlabelled pairs: train {train:,} ({train/tot:.0%})   "
          f"eval {ee:,} ({ee/tot:.0%})   straddling, discarded {straddle:,} ({straddle/tot:.0%})")

    # Ranks depend only on the embeddings, not the partition — cache them so
    # tuning the holdout does not re-walk 5,559 chunks each time.
    cache = PROJECT_ROOT / "runs" / "edges" / "band-eval" / f".ranks-{snap.name}.json"
    if cache.exists():
        best = {tuple(map(int, k.split(","))): v
                for k, v in json.loads(cache.read_text()).items()}
        print(f"\nneighbour ranks: cached ({len(best):,} pairs)")
    else:
        print("\ncomputing neighbour ranks…", flush=True)
        best = band_pairs(M, trads, ids)
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps({f"{i},{j}": r for (i, j), r in best.items()}))
        print(f"neighbour ranks: computed and cached ({len(best):,} pairs)")
    idx_trad = {i: trads[i] for i in range(len(ids))}

    cands = []
    for (i, j), rank in best.items():
        sb = sub_band(rank)
        if sb is None:
            continue
        a, b = ids[i], ids[j]
        key = (a, b) if a <= b else (b, a)
        if key in labelled:                        # already graded
            continue
        if wof[a] not in eval_works or wof[b] not in eval_works:
            continue                               # must be inside the holdout
        if chunk_body(a, corpus) is None or chunk_body(b, corpus) is None:
            continue
        ta, tb = idx_trad[i], idx_trad[j]
        cands.append({
            "a": a, "b": b, "rank": rank, "sub_band": list(sb),
            "similarity": float(M[i] @ M[j]),
            "tradition_pair": sorted((str(ta), str(tb))),
            "work_pair": sorted((wof[a], wof[b])),
            "leak": ("text-disjoint"
                     if {str(ta), str(tb)} & text_level else "work-disjoint"),
        })

    print(f"band candidates inside the holdout: {len(cands):,}")
    for lo, hi in SUB_BANDS:
        n = sum(1 for c in cands if c["sub_band"] == [lo, hi])
        print(f"  rank {lo:>2}–{hi:<2} {n:>7,}")
    tp = collections.Counter(tuple(c["tradition_pair"]) for c in cands)
    print(f"  distinct tradition pairs: {len(tp)}")
    lk = collections.Counter(c["leak"] for c in cands)
    print(f"  work-disjoint {lk['work-disjoint']:,}   "
          f"text-disjoint (single-work tradition) {lk['text-disjoint']:,}")

    if args.report or not args.emit:
        print("\nreport only — nothing written (use --emit to freeze)")
        return

    sample = stratified_sample(cands, args.target, args.seed)
    for n, c in enumerate(sample):
        c["idx"] = n
        c["citation_a"] = chunk_citation(c["a"], corpus)
        c["citation_b"] = chunk_citation(c["b"], corpus)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    run = PROJECT_ROOT / "runs" / "edges" / "band-eval" / ts
    run.mkdir(parents=True, exist_ok=True)
    (run / "pairs.jsonl").write_text(
        "".join(json.dumps(c) + "\n" for c in sample))
    (run / "partition.json").write_text(json.dumps({
        "seed": args.seed, "snapshot": snap.name,
        "holdout_units": sorted(eval_works),
        "text_level_traditions": sorted(text_level),
        "labelled_train": train, "labelled_eval": ee, "labelled_straddling": straddle,
    }, indent=2))
    (run / "manifest.json").write_text(json.dumps({
        "created_at": ts, "snapshot": snap.name, "seed": args.seed,
        "band": [BAND_LO, BAND_HI], "target": args.target, "sampled": len(sample),
        "by_sub_band": {f"{lo}-{hi}": sum(1 for c in sample if c["sub_band"] == [lo, hi])
                        for lo, hi in SUB_BANDS},
        "distinct_tradition_pairs": len({tuple(c["tradition_pair"]) for c in sample}),
        "by_leak": {k: sum(1 for c in sample if c["leak"] == k)
                    for k in ("work-disjoint", "text-disjoint")},
        "candidate_pool": len(cands),
    }, indent=2))
    if args.emit_calibration:
        # Grader control, mirroring the probes' shared calibration arm: pairs
        # that ALREADY carry a stored Claude verdict, re-graded blind. If the
        # fresh grades diverge from the stored ones, the band numbers are not
        # comparable to the training labels and the gate is measuring drift.
        rng = random.Random(args.seed + 1)
        pool = []
        for (a, b), gold in labelled.items():
            if a not in wof or b not in wof:
                continue
            if wof[a] in eval_works and wof[b] in eval_works:
                pool.append((a, b, gold))
        rng.shuffle(pool)
        calib = []
        for n, (a, b, gold) in enumerate(pool[:args.emit_calibration]):
            calib.append({"idx": n, "a": a, "b": b,
                          "citation_a": chunk_citation(a, corpus),
                          "citation_b": chunk_citation(b, corpus), "gold_positive": gold})
        (run / "calib.jsonl").write_text(
            "".join(json.dumps({k: v for k, v in c.items() if k != "gold_positive"}) + "\n"
                    for c in calib))
        (run / "calib_gold.json").write_text(json.dumps(
            {str(c["idx"]): c["gold_positive"] for c in calib}, indent=2))
        print(f"calibration arm: {len(calib)} already-labelled pairs "
              f"(gold withheld in calib_gold.json)")

    print(f"\nwrote {run}  ({len(sample)} pairs)")
    print(json.dumps(json.loads((run / "manifest.json").read_text()), indent=2))


if __name__ == "__main__":
    main()
