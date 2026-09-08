"""Benchmark candidate models against teacher labels on a held-out split.

Each --endpoint is queried against every chunk in the chosen split (default
"test"). Outputs two CSVs in --out-dir:
  cells.csv  — per (model, chunk, concept) row, union of teacher/model positives
  runs.csv   — per (model, chunk) inference outcome (parse ok, latency, etc.)

The cell rows are the union of {teacher positives} ∪ {model positives} for each
chunk; cells where both said 0 are not written (they'd dominate the file with
no signal). The True-Negative count is recoverable as
   (n_test_chunks × n_concepts) − TP − FP − FN
and report.py computes F1 from the explicit row counts.

Usage:
    python eval/bench.py \\
        --export-dir data/exports/<ts> \\
        --endpoint student=http://127.0.0.1:8080 \\
        --endpoint base=http://127.0.0.1:8081 \\
        --out-dir runs/bench/<ts>

Each endpoint must be a running llama-server with --jinja so the model's chat
template is applied. Inference is greedy (temperature 0) and serial.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from rellm.config import load as load_config
from rellm.db import open_db
from rellm.extract import iter_teacher_chunks
from rellm.formats import SYSTEM_PROMPT, build_user_prompt, parse_model_tags
from rellm.grammar import build_grammar
from rellm.taxonomy import load_taxonomy


def _endpoint(s: str) -> tuple[str, str]:
    if "=" not in s:
        raise argparse.ArgumentTypeError(f"expected name=url, got {s!r}")
    name, url = s.split("=", 1)
    return name.strip(), url.rstrip("/")


def _call(url: str, system: str, user: str, max_tokens: int, timeout: float,
          grammar: str | None = None) -> tuple[str, float]:
    payload: dict = {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.0,
        "max_tokens": max_tokens,
    }
    if grammar:
        payload["grammar"] = grammar  # llama.cpp GBNF — constrains output structure
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{url}/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"], time.monotonic() - t0


def _resolve_db(cfg, snap: Path | None) -> Path:
    if snap is not None:
        return snap / "guru.db" if snap.is_dir() else snap
    if cfg.rellm.snapshots.exists():
        cands = sorted(d for d in cfg.rellm.snapshots.iterdir() if d.is_dir())
        if cands:
            return cands[-1] / "guru.db"
    fallback = cfg.rellm.data_dir / "guru.db"
    if fallback.exists():
        return fallback
    raise SystemExit("no snapshot or fallback guru.db; run `rellm snapshot` first")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--export-dir", type=Path, required=True,
                    help="export dir containing splits.json")
    ap.add_argument("--snapshot", type=Path, default=None,
                    help="DB snapshot dir/file; else latest")
    ap.add_argument("--endpoint", action="append", type=_endpoint, required=True,
                    help="name=URL (repeat for multiple models)")
    ap.add_argument("--split", default="test", choices=["train", "val", "test"])
    ap.add_argument("--all-curated", action="store_true",
                    help="ignore --split; bench all chunks that have any "
                         "human-curated tag (accepted or rejected)")
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--limit", type=int, default=0, help="cap chunks for smoke test")
    ap.add_argument("--max-tokens", type=int, default=4096)
    ap.add_argument("--timeout", type=float, default=180.0)
    ap.add_argument("--taxonomy", type=Path, default=None,
                    help="taxonomy.toml to score against; else cfg.guru.taxonomy. "
                         "Use the snapshot a model was trained on if the live "
                         "taxonomy has since changed.")
    ap.add_argument("--grammar", choices=["off", "open", "strict"], default="off",
                    help="GBNF-constrain output. open=any snake_case id (keeps "
                         "new-concept discovery); strict=only taxonomy ids; "
                         "off=unconstrained (default).")
    args = ap.parse_args()

    cfg = load_config()
    concepts = load_taxonomy(args.taxonomy or cfg.guru.taxonomy)
    taxonomy_ids = {c.id for c in concepts}
    grammar = None
    if args.grammar != "off":
        grammar = build_grammar(concepts, allow_new=(args.grammar == "open"))
        print(f"grammar: {args.grammar} ({len(grammar)} chars)", file=sys.stderr)

    splits = json.loads((args.export_dir / "splits.json").read_text())["splits"]

    db = _resolve_db(cfg, args.snapshot)
    with open_db(db) as conn:
        # Grade against the owner-applied (accepted) labels — the vetted positives,
        # consistent with v5's accepted-only training target. Denylist matches the
        # export (cfg.model.teacher was removed in the v4 config cleanup).
        all_chunks = list(iter_teacher_chunks(
            conn, cfg.guru.corpus_dir,
            exclude_prefixes=cfg.model.exclude_model_prefixes,
            exclude_models=cfg.model.exclude_models,
            prompt_version=cfg.prompt.version,
            status=("accepted",),
        ))

    if args.all_curated:
        chunks = [c for c in all_chunks
                  if any(t.status in ("accepted", "rejected") for t in c.tags)]
    else:
        target_ids = {cid for cid, b in splits.items() if b == args.split}
        chunks = [c for c in all_chunks if c.chunk_id in target_ids]

    if args.limit:
        chunks = chunks[: args.limit]

    n_endpoints = len(args.endpoint)
    print(f"benchmarking {len(chunks)} chunks × {n_endpoints} endpoints "
          f"({len(taxonomy_ids)} concepts)", file=sys.stderr)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    cells_path = args.out_dir / "cells.csv"
    runs_path = args.out_dir / "runs.csv"

    with cells_path.open("w", newline="") as cf, runs_path.open("w", newline="") as rf:
        cw = csv.writer(cf)
        rw = csv.writer(rf)
        cw.writerow(["model", "chunk_id", "concept_id",
                     "teacher_score", "model_score", "in_taxonomy",
                     "human_status", "split"])
        rw.writerow(["model", "chunk_id", "parse_ok",
                     "n_emitted", "n_out_of_taxonomy", "latency_s"])

        for i, ch in enumerate(chunks, 1):
            teacher = {t.concept_id: t.score for t in ch.tags}
            status_by_cid = {t.concept_id: t.status for t in ch.tags}
            split_bucket = splits.get(ch.chunk_id, "")
            user_prompt = build_user_prompt(ch.body, ch.citation, concepts)

            for name, url in args.endpoint:
                try:
                    raw, dt = _call(url, SYSTEM_PROMPT, user_prompt,
                                    max_tokens=args.max_tokens, timeout=args.timeout,
                                    grammar=grammar)
                except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError) as e:
                    print(f"  [{i}/{len(chunks)}] {name} {ch.chunk_id}: ERROR {e}",
                          file=sys.stderr)
                    rw.writerow([name, ch.chunk_id, 0, 0, 0, ""])
                    continue

                parse_ok, pred = parse_model_tags(raw)
                n_oot = sum(1 for cid in pred if cid not in taxonomy_ids)
                rw.writerow([name, ch.chunk_id, int(parse_ok),
                             len(pred), n_oot, f"{dt:.2f}"])

                union = {cid for cid, s in teacher.items() if s >= 1} | \
                        {cid for cid, s in pred.items() if s >= 1}
                for cid in union:
                    cw.writerow([
                        name, ch.chunk_id, cid,
                        teacher.get(cid, 0), pred.get(cid, 0),
                        int(cid in taxonomy_ids),
                        status_by_cid.get(cid, ""),
                        split_bucket,
                    ])

            print(f"  [{i}/{len(chunks)}] {ch.chunk_id}", file=sys.stderr)

    print(f"\nwrote {cells_path}", file=sys.stderr)
    print(f"wrote {runs_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
