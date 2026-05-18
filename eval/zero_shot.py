"""Zero-shot capability probe.

Runs each base-model candidate (via ollama) against a sample of human-accepted
chunks and writes a per-(model, chunk, concept) row CSV. Use the result to
pick which base model to actually finetune.

Run:
    pip install -e .[eval]
    python eval/zero_shot.py \\
        --models qwen2.5:7b qwen2.5:14b llama3.1:8b \\
        --sample 40 \\
        --out runs/zero_shot/<ts>.csv

Agreement metric is "recall on human-positives": did the model also score
this concept >= 1? That's the load-bearing question for the base-model pick.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from rellm.config import load as load_config
from rellm.db import open_db
from rellm.extract import iter_teacher_chunks
from rellm.formats import SYSTEM_PROMPT, build_user_prompt
from rellm.taxonomy import load_taxonomy


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", type=Path, default=None,
                    help="Snapshot path; else latest, else data/guru.db")
    ap.add_argument("--models", nargs="+", required=True,
                    help="Ollama model tags, e.g. qwen2.5:7b qwen2.5:14b")
    ap.add_argument("--sample", type=int, default=40)
    ap.add_argument("--out", type=Path, required=True)
    return ap.parse_args()


def _resolve_snapshot(cfg, snap: Path | None) -> Path:
    if snap is not None:
        return snap / "guru.db" if snap.is_dir() else snap
    if cfg.rellm.snapshots.exists():
        cands = sorted(d for d in cfg.rellm.snapshots.iterdir() if d.is_dir())
        if cands:
            return cands[-1] / "guru.db"
    fallback = cfg.rellm.data_dir / "guru.db"
    if fallback.exists():
        return fallback
    raise SystemExit("no snapshot found; run `rellm snapshot` first")


def _call_ollama(model: str, system: str, user: str) -> str:
    import ollama
    resp = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        options={"temperature": 0},
    )
    return resp["message"]["content"]


def _parse_scores(raw: str) -> dict[str, int]:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:].strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if isinstance(data, dict):
        for k in ("tags", "results", "concepts", "items"):
            if k in data:
                data = data[k]
                break
    out: dict[str, int] = {}
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and "concept_id" in item:
                try:
                    out[str(item["concept_id"])] = int(item.get("score", 0))
                except (TypeError, ValueError):
                    pass
    return out


def main() -> None:
    args = _parse_args()
    cfg = load_config()
    concepts = load_taxonomy(cfg.guru.taxonomy)
    db = _resolve_snapshot(cfg, args.snapshot)

    with open_db(db) as conn:
        chunks = list(iter_teacher_chunks(
            conn, cfg.guru.corpus_dir,
            teacher_model=cfg.model.teacher,
            prompt_version=cfg.prompt.version,
            status=("accepted",),
            limit=args.sample,
        ))
    print(f"probing {len(chunks)} chunks × {len(args.models)} models", file=sys.stderr)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["model", "chunk_id", "concept_id", "human_score", "model_score", "found"])
        for ch in chunks:
            human = {t.concept_id: t.score for t in ch.tags}
            prompt = build_user_prompt(ch.body, ch.citation, concepts)
            for m in args.models:
                try:
                    raw = _call_ollama(m, SYSTEM_PROMPT, prompt)
                except Exception as e:
                    print(f"  {m} {ch.chunk_id}: {e}", file=sys.stderr)
                    continue
                pred = _parse_scores(raw)
                for cid, hs in human.items():
                    ps = pred.get(cid, 0)
                    w.writerow([m, ch.chunk_id, cid, hs, ps, int(ps >= 1)])
    print(f"wrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
