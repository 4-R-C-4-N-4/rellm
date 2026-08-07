#!/usr/bin/env python3
"""Run hidden-state extraction for the homology module.

    .venv/bin/python tools/homology_extract.py --model unsloth/Qwen2.5-7B-Instruct

Needs the 3090 to itself (`llm stop` first). Output lands under
data/homology/directions/<model-slug>/ and is the artifact every sweep
downstream reads; re-extraction against a different model is a different
artifact and must never be mixed (proposal: provenance is identity).
"""
import argparse
from pathlib import Path

from rellm.config import load
from rellm.homology.extract import extract


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--max-tokens", type=int, default=1024)
    ap.add_argument("--batch-tokens", type=int, default=8192)
    args = ap.parse_args()

    cfg = load()
    slug = args.model.replace("/", "--")
    out = cfg.rellm.root / "data" / "homology" / "directions" / slug
    extract(cfg, args.model, out, args.max_tokens, args.batch_tokens)


if __name__ == "__main__":
    main()
