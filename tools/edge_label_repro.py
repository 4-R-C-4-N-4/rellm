#!/usr/bin/env python3
"""edge_label_repro.py — is the stored edge label reproducible?

The band eval's calibration arm found that fresh Claude, applying guru's own
review rubric, recovers archived `agent-claude` verdicts at chance
(kappa +0.040, n=60). Two confounds could explain that without the labels
actually being bad, and this tool tests both.

**1. Restricted range.** Every labelled pair is a Mistral proposal, and every
negative is one Claude overturned, so the calibration sample sits entirely on
the decision boundary — exactly where agreement is hardest and kappa is most
attenuated. `--emit` builds a full-range set instead: stored positives, stored
negatives, and random cross-tradition pairs whose gold is presumed negative.
If kappa recovers there, only the boundary is unstable, which is tolerable and
documentable. If it stays near zero, the label set is unreliable in general.

The random stratum doubles as the base-rate spot check the build spec wants
before mining easy negatives: it measures how often a random cross-tradition
pair is actually a parallel, an assumption currently taken on faith.

**2. Anchoring.** guru's review contract shows the reviewer the proposing
model's verdict, confidence and justification, and states outright that "the
justification alone predicts the verdict well enough to prioritise". The
archived labels were produced with Mistral's reasoning on screen; the
calibration graders saw only the passages. `--show-calib --anchored`
reproduces the reviewer's actual view. If agreement jumps, the labels are
reproducible only under anchoring — which band pairs can never match, since
they were never proposed.

Usage:
    python3 tools/edge_label_repro.py --emit --n-random 40 --n-pos 30 --n-neg 30
    python3 tools/edge_label_repro.py --show 7
    python3 tools/edge_label_repro.py --show-calib 7 --anchored --band-run <dir>
    python3 tools/edge_label_repro.py --report
"""
from __future__ import annotations

import argparse
import json
import random
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

from rellm.config import load as load_config          # noqa: E402
from rellm.corpus import chunk_body, chunk_citation   # noqa: E402
from rellm.edges import POSITIVE_TYPES, REVIEWED_STATUS  # noqa: E402
from edge_band_eval_set import latest_snapshot, review_rubric  # noqa: E402

RUN_ROOT = PROJECT_ROOT / "runs" / "edges" / "label-repro"
SEED = 20260812


def render(cfg, cit_a, body_a, cit_b, body_b, proposal: dict | None = None) -> str:
    """The review rubric applied to one pair, optionally anchored.

    `proposal` mirrors what guru's review UI puts in front of a reviewer:
    the proposing model's verdict, confidence and stated reason.
    """
    out = [review_rubric(cfg), "\n---\n"]
    if proposal:
        out.append(
            f"{proposal['source_id']}  ──{proposal['edge_type']} "
            f"@ {proposal['confidence']}──  {proposal['target_id']}\n"
            f"model's justification: {proposal['justification']}\n")
    out.append(f'A ({cit_a}):\n"""\n{body_a}\n"""\n')
    out.append(f'B ({cit_b}):\n"""\n{body_b}\n"""\n')
    out.append("Respond with a single JSON object and no prose outside it:\n"
               '{"edge_type": "<PARALLELS|CONTRASTS|surface_only|unrelated>", '
               '"confidence": <0.0-1.0>, "justification": "<one to two sentences>"}')
    return "\n".join(out)


def proposal_for(conn, a: str, b: str) -> dict | None:
    r = conn.execute(
        "SELECT source_chunk, target_chunk, edge_type, confidence, justification "
        "FROM staged_edges WHERE (source_chunk=? AND target_chunk=?) "
        "OR (source_chunk=? AND target_chunk=?) LIMIT 1", (a, b, b, a)).fetchone()
    if not r or not r[4]:
        return None
    return {"source_id": r[0], "target_id": r[1], "edge_type": r[2],
            "confidence": r[3], "justification": r[4]}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--emit", action="store_true")
    ap.add_argument("--show", type=int)
    ap.add_argument("--show-calib", type=int)
    ap.add_argument("--anchored", action="store_true",
                    help="show the proposing model's verdict and justification")
    ap.add_argument("--run", type=Path, help="label-repro run dir")
    ap.add_argument("--band-run", type=Path, help="band-eval run dir (for --show-calib)")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--n-random", type=int, default=40)
    ap.add_argument("--n-pos", type=int, default=30)
    ap.add_argument("--n-neg", type=int, default=30)
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()

    cfg = load_config()
    corpus = cfg.guru.repo / "corpus"
    snap = latest_snapshot(cfg.rellm.snapshots)
    conn = sqlite3.connect(f"file:{snap/'guru.db'}?mode=ro", uri=True)

    if args.show_calib is not None:
        run = args.band_run
        rows = [json.loads(l) for l in (run / "calib.jsonl").read_text().splitlines()]
        p = rows[args.show_calib]
        prop = proposal_for(conn, p["a"], p["b"]) if args.anchored else None
        print(f"### calibration pair {args.show_calib}  [{p['a']} | {p['b']}]\n")
        print(render(cfg, p["citation_a"], chunk_body(p["a"], corpus) or "",
                     p["citation_b"], chunk_body(p["b"], corpus) or "", prop))
        return

    if args.show is not None:
        run = args.run or sorted(d for d in RUN_ROOT.iterdir() if d.is_dir())[-1]
        rows = [json.loads(l) for l in (run / "pairs.jsonl").read_text().splitlines()]
        p = rows[args.show]
        prop = proposal_for(conn, p["a"], p["b"]) if args.anchored else None
        print(f"### pair {args.show}  [{p['a']} | {p['b']}]\n")
        print(render(cfg, p["citation_a"], chunk_body(p["a"], corpus) or "",
                     p["citation_b"], chunk_body(p["b"], corpus) or "", prop))
        return

    if args.report:
        run = args.run or sorted(d for d in RUN_ROOT.iterdir() if d.is_dir())[-1]
        report(run)
        return

    # ── emit ────────────────────────────────────────────────────────────────
    rng = random.Random(args.seed)
    ph = ",".join("?" for _ in REVIEWED_STATUS)
    labelled = [(r[0], r[1], r[2] in POSITIVE_TYPES) for r in conn.execute(
        f"SELECT source_chunk, target_chunk, edge_type FROM staged_edges "
        f"WHERE status IN ({ph})", list(REVIEWED_STATUS))]
    have = {(a, b) if a <= b else (b, a) for a, b, _ in labelled}

    chunks = [(r[0], r[1] or r[0].split(".")[0]) for r in conn.execute(
        "SELECT id, tradition_id FROM nodes WHERE type='chunk'")]
    chunks = [(c, t) for c, t in chunks if chunk_body(c, corpus) is not None]

    def ok(a, b):
        return chunk_body(a, corpus) is not None and chunk_body(b, corpus) is not None

    pos = [(a, b) for a, b, p in labelled if p and ok(a, b)]
    neg = [(a, b) for a, b, p in labelled if not p and ok(a, b)]
    rng.shuffle(pos); rng.shuffle(neg)

    rand: list[tuple[str, str]] = []
    while len(rand) < args.n_random:
        (a, ta), (b, tb) = rng.sample(chunks, 2)
        if ta == tb:
            continue
        key = (a, b) if a <= b else (b, a)
        if key in have or key in {(x, y) if x <= y else (y, x) for x, y in rand}:
            continue
        rand.append((a, b))

    rows = []
    for a, b in pos[:args.n_pos]:
        rows.append({"a": a, "b": b, "stratum": "stored-positive", "gold": True})
    for a, b in neg[:args.n_neg]:
        rows.append({"a": a, "b": b, "stratum": "stored-negative", "gold": False})
    for a, b in rand:
        # Gold is an assumption here, not a record — that is the point.
        rows.append({"a": a, "b": b, "stratum": "random", "gold": False})
    rng.shuffle(rows)                     # stratum must not be inferable from idx

    for n, r in enumerate(rows):
        r["idx"] = n
        r["citation_a"] = chunk_citation(r["a"], corpus)
        r["citation_b"] = chunk_citation(r["b"], corpus)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    run = RUN_ROOT / ts
    (run / "grades").mkdir(parents=True, exist_ok=True)
    (run / "pairs.jsonl").write_text("".join(
        json.dumps({k: v for k, v in r.items() if k not in ("gold", "stratum")}) + "\n"
        for r in rows))
    (run / "gold.json").write_text(json.dumps(
        {str(r["idx"]): {"gold": r["gold"], "stratum": r["stratum"]} for r in rows},
        indent=2))
    print(f"wrote {run}  ({len(rows)} pairs: {args.n_pos} stored-positive, "
          f"{args.n_neg} stored-negative, {len(rand)} random)")
    print("gold + stratum withheld from pairs.jsonl")


def kappa(gold: dict, got: dict, keys) -> tuple[float, float, float]:
    if not keys:
        return float("nan"), float("nan"), 0.0
    po = sum(gold[i] == got[i] for i in keys) / len(keys)
    gp = sum(gold[i] for i in keys) / len(keys)
    fp = sum(got[i] for i in keys) / len(keys)
    pe = gp * fp + (1 - gp) * (1 - fp)
    return po, pe, ((po - pe) / (1 - pe) if pe < 1 else float("nan"))


def report(run: Path) -> None:
    meta = {int(k): v for k, v in json.loads((run / "gold.json").read_text()).items()}
    gold = {i: m["gold"] for i, m in meta.items()}
    got, conf = {}, {}
    for f in sorted((run / "grades").glob("*.jsonl")):
        for line in f.read_text().splitlines():
            if line.strip():
                try:
                    g = json.loads(line)
                    got[g["idx"]] = g["edge_type"] in POSITIVE_TYPES
                    conf[g["idx"]] = g.get("confidence", 0)
                except (json.JSONDecodeError, KeyError):
                    pass
    both = sorted(set(gold) & set(got))
    print(f"run: {run.name}   graded {len(got)}/{len(gold)}")
    if not both:
        return

    po, pe, k = kappa(gold, got, both)
    print(f"\nFULL RANGE  n={len(both)}  agreement {po:.1%} "
          f"(chance {pe:.1%})  kappa {k:+.3f}")
    print("  compare: boundary-only calibration arm scored kappa +0.040")

    print("\nby stratum:")
    for s in ("stored-positive", "stored-negative", "random"):
        ks = [i for i in both if meta[i]["stratum"] == s]
        if not ks:
            continue
        agree = sum(gold[i] == got[i] for i in ks) / len(ks)
        posr = sum(got[i] for i in ks) / len(ks)
        print(f"  {s:<16} n={len(ks):>3}  fresh-positive {posr:.3f}  "
              f"agrees with gold {agree:.1%}")

    rnd = [i for i in both if meta[i]["stratum"] == "random"]
    if rnd:
        r = sum(got[i] for i in rnd) / len(rnd)
        print(f"\nRANDOM-PAIR BASE RATE: {r:.3f} (n={len(rnd)})")
        print("  the build spec assumes ~0 and mines easy negatives unjudged;")
        print("  above ~0.05 a 1:1 mix injects real label noise")

    # Boundary-only kappa from the same graders, for a like-for-like contrast.
    bnd = [i for i in both if meta[i]["stratum"] != "random"]
    if bnd:
        po2, pe2, k2 = kappa(gold, got, bnd)
        print(f"\nboundary subset (stored pairs only)  n={len(bnd)}  "
              f"agreement {po2:.1%} (chance {pe2:.1%})  kappa {k2:+.3f}")
        print("  if full-range kappa is high while this stays ~0, the labels are"
              "\n  fine away from the boundary and unstable on it")


if __name__ == "__main__":
    main()
