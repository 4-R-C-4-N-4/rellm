"""Train/val/test splits with leakage protection.

Splits by chunk_id (not row) so concept-level phrasing for a given passage
stays in one bucket. The hash is stable across runs given the same seed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def _bucket(chunk_id: str, seed: str = "rellm-v1") -> float:
    h = hashlib.sha256(f"{seed}:{chunk_id}".encode()).digest()
    return int.from_bytes(h[:8], "big") / 2**64


def assign_split(chunk_id: str, val: float = 0.05, test: float = 0.05) -> str:
    b = _bucket(chunk_id)
    if b < val:
        return "val"
    if b < val + test:
        return "test"
    return "train"


def write_split_manifest(
    chunk_ids: list[str],
    path: Path,
    val: float = 0.05,
    test: float = 0.05,
) -> dict:
    splits: dict[str, str] = {}
    counts = {"train": 0, "val": 0, "test": 0}
    for cid in chunk_ids:
        s = assign_split(cid, val=val, test=test)
        splits[cid] = s
        counts[s] += 1
    manifest = {"val": val, "test": test, "counts": counts, "splits": splits}
    path.write_text(json.dumps(manifest, indent=2))
    return manifest
