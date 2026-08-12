#!/usr/bin/env python3
"""edge_band_eval_collect.py — merge, validate and freeze the band eval grades.

Reads the sampled pairs and every grades/*.jsonl written by the graders,
checks that each pair was graded exactly once, and writes `graded.jsonl` —
the frozen artifact the ship gate is measured on.

The band's positive rate is the number that matters most here: it is the
baseline the gate's ≥0.65 has to beat. The audit's pooled probes put the
unranked band at ~0.40, and that estimate carried Qwen-27B judge labels with
a +0.10–0.15 positive bias, so a Claude-graded rate is worth having on its
own.

Usage:
    python3 tools/edge_band_eval_collect.py
    python3 tools/edge_band_eval_collect.py --run runs/edges/band-eval/<ts>
    python3 tools/edge_band_eval_collect.py --freeze
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from rellm.edges import EDGE_TYPES, POSITIVE_TYPES   # noqa: E402

# Editorial apparatus the graders repeatedly ran into: prefaces, footnotes,
# bookseller catalogues, text-critical front matter. Matched against grader
# prose, so this is a floor on the real rate, not a measurement.
APPARATUS_RE = re.compile(
    r"apparatus|front matter|back matter|preface|footnote|catalogue|transcriber|"
    r"translator's note|editorial|bibliograph|title page|\bindex\b", re.I)

BAND_ROOT = PROJECT_ROOT / "runs" / "edges" / "band-eval"


def latest_run() -> Path:
    return sorted(d for d in BAND_ROOT.iterdir() if d.is_dir())[-1]


def rate(rows) -> float:
    return sum(r["edge_type"] in POSITIVE_TYPES for r in rows) / len(rows) if rows else 0.0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", type=Path)
    ap.add_argument("--freeze", action="store_true",
                    help="write graded.jsonl (refuses while grades are missing)")
    args = ap.parse_args()

    run = args.run or latest_run()
    pairs = {json.loads(l)["idx"]: json.loads(l)
             for l in (run / "pairs.jsonl").read_text().splitlines()}
    print(f"run: {run.name}   sampled pairs: {len(pairs)}")

    grades: dict[int, dict] = {}
    dupes: list[int] = []
    bad: list[tuple] = []
    for f in sorted((run / "grades").glob("*.jsonl")):
        n = 0
        for line in f.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                g = json.loads(line)
            except json.JSONDecodeError:
                bad.append((f.name, line[:60]))
                continue
            if g.get("edge_type") not in EDGE_TYPES:
                bad.append((f.name, f"bad edge_type {g.get('edge_type')!r}"))
                continue
            i = g["idx"]
            if i in grades:
                dupes.append(i)
            grades[i] = g
            n += 1
        print(f"  {f.name:16} {n:>4} verdicts")

    missing = sorted(set(pairs) - set(grades))
    extra = sorted(set(grades) - set(pairs))
    print(f"\ngraded {len(grades)}/{len(pairs)}   missing {len(missing)}   "
          f"duplicates {len(dupes)}   malformed {len(bad)}   out-of-range {len(extra)}")
    if missing:
        print(f"  missing idx: {missing[:20]}{' …' if len(missing) > 20 else ''}")
    for f, why in bad[:5]:
        print(f"  malformed in {f}: {why}")

    rows = [dict(pairs[i], **grades[i]) for i in sorted(grades) if i in pairs]
    if not rows:
        return

    counts = collections.Counter(r["edge_type"] for r in rows)
    print("\nverdicts:")
    for t in EDGE_TYPES:
        print(f"  {t:<14}{counts[t]:>5}  {counts[t]/len(rows):>6.1%}")
    print(f"\nBAND POSITIVE RATE: {rate(rows):.3f}   "
          f"(n={len(rows)}) — the baseline the ship gate's 0.65 must beat")

    print("\nby rank sub-band:")
    for lo, hi in ((6, 10), (11, 25), (26, 50)):
        sub = [r for r in rows if r["sub_band"] == [lo, hi]]
        print(f"  rank {lo:>2}–{hi:<2}  n={len(sub):>4}  positive {rate(sub):.3f}")

    print("\nby leakage class:")
    for k in ("work-disjoint", "text-disjoint"):
        sub = [r for r in rows if r["leak"] == k]
        if sub:
            print(f"  {k:<15} n={len(sub):>4}  positive {rate(sub):.3f}")

    print("\nby grading batch (a check on grader drift, not a result):")
    for f in sorted((run / "grades").glob("*.jsonl")):
        idxs = {json.loads(l)["idx"] for l in f.read_text().splitlines() if l.strip()}
        sub = [r for r in rows if r["idx"] in idxs]
        if sub:
            print(f"  {f.stem:<10} n={len(sub):>4}  positive {rate(sub):.3f}")

    conf = [r.get("confidence", 0) for r in rows]
    print(f"\nmean grader confidence: {sum(conf)/len(conf):.2f}   "
          f"below 0.6: {sum(c < 0.6 for c in conf)}")

    # How soft is the positive class? The gate is precision@top-20%, so if
    # most positives are marginal calls the bar is being measured against a
    # soft ground truth and a reranker can clear it on weak agreement.
    pos = [r for r in rows if r["edge_type"] in POSITIVE_TYPES]
    marg = [r for r in pos if r.get("confidence", 0) < 0.6]
    print(f"positives: {len(pos)}   marginal (<0.6): {len(marg)} "
          f"({len(marg)/len(pos):.0%} of positives)" if pos else "")
    strict = [r for r in rows
              if not (r["edge_type"] in POSITIVE_TYPES and r.get("confidence", 0) < 0.6)]
    print(f"positive rate, marginal positives demoted to negative: "
          f"{rate([r for r in strict]):.3f}")

    # Editorial apparatus — prefaces, footnotes, catalogues, front matter.
    # guru has an `apparatus` status on staged_cleanups but nothing is flagged
    # with it, so the graders' own prose is the only signal available.
    flagged = [r for r in rows if APPARATUS_RE.search(r.get("justification", ""))]
    if flagged:
        clean = [r for r in rows if r not in flagged]
        print(f"\napparatus mentioned in {len(flagged)} justifications "
              f"({len(flagged)/len(rows):.0%})")
        print(f"  positive rate, apparatus-flagged: {rate(flagged):.3f}")
        print(f"  positive rate, rest:              {rate(clean):.3f}")

    # Calibration arm: the same graders, same rubric, on pairs that already
    # carry a stored verdict. Divergence here means the band numbers are not
    # comparable to the labels the model trains on.
    gold_path = run / "calib_gold.json"
    if gold_path.exists():
        gold = {int(k): v for k, v in json.loads(gold_path.read_text()).items()}
        print(f"\ncalibration arm ({len(gold)} pairs with stored verdicts):")
        for label, cdir in (("propose rubric", run / "grades-calib"),
                            ("review rubric ", run / "grades-calib-review")):
            if not cdir.exists():
                continue
            got = {}
            for f in sorted(cdir.glob("*.jsonl")):
                for line in f.read_text().splitlines():
                    if line.strip():
                        try:
                            g = json.loads(line)
                            got[g["idx"]] = g["edge_type"] in POSITIVE_TYPES
                        except (json.JSONDecodeError, KeyError):
                            pass
            both = sorted(set(gold) & set(got))
            if not both:
                continue
            agree = sum(gold[i] == got[i] for i in both)
            fp = sum(got[i] for i in both) / len(both)
            gp = sum(gold[i] for i in both) / len(both)
            # False positives against stored labels are the failure that
            # matters: a grader that calls everything positive agrees with
            # every stored positive and learns nothing.
            fp_n = sum(1 for i in both if got[i] and not gold[i])
            fn_n = sum(1 for i in both if not got[i] and gold[i])
            # Raw agreement is worthless on an unbalanced set — calling
            # everything positive scores the base rate for free. Cohen's
            # kappa is agreement above what the two marginals alone predict.
            pe = gp * fp + (1 - gp) * (1 - fp)
            po = agree / len(both)
            kappa = (po - pe) / (1 - pe) if pe < 1 else float("nan")
            print(f"  {label}  n={len(both):<3} agreement {po:>5.1%} "
                  f"(chance {pe:.1%}, kappa {kappa:+.3f})   "
                  f"stored {gp:.3f} -> fresh {fp:.3f} (bias {fp-gp:+.3f})   "
                  f"false-pos {fp_n}  false-neg {fn_n}")
            # Does the grader know when it is right?
            confs = {}
            for f in sorted(cdir.glob("*.jsonl")):
                for line in f.read_text().splitlines():
                    if line.strip():
                        try:
                            g = json.loads(line)
                            confs[g["idx"]] = g.get("confidence", 0)
                        except (json.JSONDecodeError, KeyError):
                            pass
            hi = [i for i in both if confs.get(i, 0) >= 0.7]
            if hi:
                ha = sum(gold[i] == got[i] for i in hi) / len(hi)
                print(f"{'':<17} confident subset (>=0.7): n={len(hi)}  "
                      f"agreement {ha:.1%}")
        print("  The stored labels came from prompts/ingest/edge-review.md, not from"
              "\n  the proposal prompt in rellm.edges. Grading the band against the"
              "\n  proposal prompt measures a different threshold than the one the"
              "\n  model trains on, which is what this arm exists to detect.")

    if not args.freeze:
        print("\nnot frozen — pass --freeze to write graded.jsonl")
        return
    if missing or dupes or bad:
        sys.exit("\nREFUSING to freeze: grades incomplete or malformed")

    (run / "graded.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in rows))
    summary = {
        "n": len(rows),
        "band_positive_rate": round(rate(rows), 4),
        "counts": dict(counts),
        "by_sub_band": {f"{lo}-{hi}": round(rate([r for r in rows
                                                  if r["sub_band"] == [lo, hi]]), 4)
                        for lo, hi in ((6, 10), (11, 25), (26, 50))},
        "by_leak": {k: round(rate([r for r in rows if r["leak"] == k]), 4)
                    for k in ("work-disjoint", "text-disjoint")},
    }
    (run / "graded_summary.json").write_text(json.dumps(summary, indent=2))
    print(f"\nfroze {run/'graded.jsonl'}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
