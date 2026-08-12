#!/usr/bin/env python3
"""edge_relevance_judge.py — is the surfaced edge material relevant to the query?

The judgment that decides whether the anchored inheritance term stays. Three
strata, blind and shuffled together:

  surfaced   partners the EDGE_INHERIT term put into the final top-K
  baseline   chunks the parity baseline itself returned (expected ceiling)
  random     random corpus chunks paired with the same queries (expected floor)

If graders cannot separate baseline from random, the judgment is unstable and
decides nothing — that is the built-in stability check, learned the hard way
from the pair-label kappa result. Every item is graded twice by independent
graders; report gives inter-grader agreement alongside the rates.

Usage:
    python3 tools/edge_relevance_judge.py --emit --ab-run runs/edges/inherit-ab/<ts>
    python3 tools/edge_relevance_judge.py --show 7 [--run DIR]
    python3 tools/edge_relevance_judge.py --report [--run DIR]
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import random
import sqlite3
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RELLM_ROOT = Path(__file__).parent.parent
# EDGE_GURU_ROOT lets a run target a guru worktree; see edge_inherit_ab.py.
GURU_ROOT = Path(os.environ.get("EDGE_GURU_ROOT", RELLM_ROOT.parent / "guru"))
sys.path.insert(0, str(RELLM_ROOT / "src"))
sys.path.insert(0, str(GURU_ROOT))

RUN_ROOT = RELLM_ROOT / "runs" / "edges" / "relevance-judge"
SEED = 20260812
VERDICTS = ("relevant", "marginal", "not_relevant")

RUBRIC = """\
You are evaluating one retrieval result for a comparative-religion index. A
reader typed the query; the system returned the passage as part of its answer
set. Judge whether the passage belongs there.

  relevant      — on-topic for the query: a reader asking this would consider
                  the passage a useful part of the answer. Cross-tradition
                  material counts fully; the index exists to surface the same
                  question answered in other traditions. It does not need to
                  be the best possible passage, just a defensible member of a
                  15-result answer set.
  marginal      — touches the query's topic, but weakly: tangential, generic,
                  or mostly about something else.
  not_relevant  — a reader asking this query would be puzzled to receive it.

Judge the passage against the QUERY. Do not reward beautiful or famous
passages that miss the question, and do not penalise unfamiliar traditions."""


def latest(root: Path) -> Path:
    return sorted(d for d in root.iterdir() if d.is_dir())[-1]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--emit", action="store_true")
    ap.add_argument("--ab-run", type=Path, help="inherit-ab run to draw surfaced from")
    ap.add_argument("--show", type=int)
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--run", type=Path)
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()

    if args.show is not None:
        run = args.run or latest(RUN_ROOT)
        rows = [json.loads(l) for l in (run / "judge.jsonl").read_text().splitlines()]
        p = rows[args.show]
        print(f"### item {args.show}\n\n{RUBRIC}\n")
        print(f"QUERY: {p['query']}\n")
        print(f'PASSAGE ({p["citation"]}):\n"""\n{p["body"]}\n"""\n')
        print('Respond with a single JSON object and no prose outside it:\n'
              '{"verdict": "<relevant|marginal|not_relevant>", '
              '"confidence": <0.0-1.0>, "justification": "<one sentence>"}')
        return

    if args.report:
        run = args.run or latest(RUN_ROOT)
        report(run)
        return

    # ── emit ────────────────────────────────────────────────────────────────
    os.chdir(GURU_ROOT)
    from guru.corpus import resolve_chunk_path          # noqa: E402
    from guru.preferences import UserPreferences        # noqa: E402
    from guru.retriever import HybridRetriever          # noqa: E402
    import tomllib                                      # noqa: E402

    def body_of(cid: str) -> str | None:
        p = resolve_chunk_path(cid)
        if p is None:
            return None
        with open(p, "rb") as f:
            return tomllib.load(f)["content"]["body"]

    def embed(text: str) -> list[float]:
        payload = json.dumps({"model": "nomic-embed-text:v1.5",
                              "input": text}).encode()
        req = urllib.request.Request("http://localhost:11434/api/embed",
                                     data=payload,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())["embeddings"][0]

    ab = args.ab_run or latest(RELLM_ROOT / "runs" / "edges" / "inherit-ab")
    surfaced = [json.loads(l) for l in (ab / "surfaced.jsonl").read_text().splitlines()]
    queries = sorted({s["query"] for s in surfaced})
    rng = random.Random(args.seed)

    items = [{"query": s["query"], "chunk_id": s["chunk_id"],
              "stratum": "surfaced"} for s in surfaced]

    retriever = HybridRetriever()
    prefs = UserPreferences.allow_all()
    conn = sqlite3.connect(f"file:{GURU_ROOT/'data'/'guru.db'}?mode=ro", uri=True)
    all_chunks = [r[0] for r in conn.execute(
        "SELECT id FROM nodes WHERE type='chunk'")]

    for q in queries:
        base = retriever.retrieve(q, embed(q), prefs, top_k=15)
        picks = [base[0], base[len(base) // 2]] if len(base) > 1 else base
        for c in picks:
            items.append({"query": q, "chunk_id": c.chunk_id,
                          "stratum": "baseline"})
        for cid in rng.sample(all_chunks, 2):
            items.append({"query": q, "chunk_id": cid, "stratum": "random"})

    rng.shuffle(items)
    rows, key = [], {}
    for it in items:
        body = body_of(it["chunk_id"])
        if not body:
            continue
        key[str(len(rows))] = it["stratum"]
        rows.append({"idx": len(rows), "query": it["query"],
                     "citation": it["chunk_id"], "body": body[:2400]})

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    run = RUN_ROOT / ts
    (run / "grades-1").mkdir(parents=True, exist_ok=True)
    (run / "grades-2").mkdir(parents=True, exist_ok=True)
    (run / "judge.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    (run / "key.json").write_text(json.dumps(key, indent=2))
    counts = collections.Counter(key.values())
    print(f"wrote {run}  ({len(rows)} items: {dict(counts)})")
    print("stratum withheld from judge.jsonl; graders see query + passage only")


def report(run: Path) -> None:
    key = {int(k): v for k, v in json.loads((run / "key.json").read_text()).items()}

    def load(d: Path) -> dict[int, dict]:
        out = {}
        for f in sorted(d.glob("*.jsonl")):
            for line in f.read_text().splitlines():
                if line.strip():
                    try:
                        g = json.loads(line)
                        if g.get("verdict") in VERDICTS:
                            out[g["idx"]] = g
                    except (json.JSONDecodeError, KeyError):
                        pass
        return out

    g1, g2 = load(run / "grades-1"), load(run / "grades-2")
    both = sorted(set(g1) & set(g2) & set(key))
    print(f"run {run.name}   graded: g1 {len(g1)}  g2 {len(g2)}  overlap {len(both)}")
    if not both:
        return

    # Inter-grader stability, binary (relevant+marginal vs not).
    def pos(g):
        return g["verdict"] != "not_relevant"

    agree3 = sum(g1[i]["verdict"] == g2[i]["verdict"] for i in both) / len(both)
    a = sum(pos(g1[i]) == pos(g2[i]) for i in both) / len(both)
    p1 = sum(pos(g1[i]) for i in both) / len(both)
    p2 = sum(pos(g2[i]) for i in both) / len(both)
    pe = p1 * p2 + (1 - p1) * (1 - p2)
    kappa = (a - pe) / (1 - pe) if pe < 1 else float("nan")
    print(f"\ninter-grader: 3-way agreement {agree3:.1%}   "
          f"binary agreement {a:.1%} (chance {pe:.1%})  KAPPA {kappa:+.3f}")
    print("  the pair-label kappa that killed the last eval was +0.04; this "
          "number must be high for anything below to mean something\n")

    print(f"{'stratum':<11}{'n':>4}{'relevant':>10}{'marginal':>10}"
          f"{'not':>6}{'strict-rel%':>13}{'lenient%':>10}")
    for s in ("baseline", "surfaced", "random"):
        ks = [i for i in both if key[i] == s]
        if not ks:
            continue
        cnt = collections.Counter()
        strict = lenient = 0
        for i in ks:
            v1, v2 = g1[i]["verdict"], g2[i]["verdict"]
            cnt[v1] += 1
            cnt[v2] += 1
            if v1 == v2 == "relevant":
                strict += 1
            if pos(g1[i]) and pos(g2[i]):
                lenient += 1
        n2 = len(ks) * 2
        print(f"{s:<11}{len(ks):>4}{cnt['relevant']/n2:>10.1%}"
              f"{cnt['marginal']/n2:>10.1%}{cnt['not_relevant']/n2:>6.1%}"
              f"{strict/len(ks):>13.1%}{lenient/len(ks):>10.1%}")
    print("\nstrict-rel% = both graders said 'relevant'; lenient% = neither "
          "said 'not_relevant'.")


if __name__ == "__main__":
    main()
