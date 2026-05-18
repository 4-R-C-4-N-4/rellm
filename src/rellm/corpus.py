"""Resolve chunk_id → chunk body by reading the guru corpus TOMLs.

Mirror of guru.corpus.resolve_chunk_path — duplicated here to keep rellm
free of an import-time dependency on the guru repo.
"""
from __future__ import annotations

import tomllib
from functools import lru_cache
from pathlib import Path


def resolve_chunk_path(chunk_id: str, corpus_dir: Path) -> Path | None:
    """Map chunk_id "<trad>.<text_id>.<seq>" → <corpus>/<trad>/<text_id>/chunks/<seq>.toml."""
    parts = chunk_id.split(".", 2)
    if len(parts) < 3:
        return None
    trad, text_id, seq = parts
    p = corpus_dir / trad / text_id / "chunks" / f"{seq}.toml"
    return p if p.exists() else None


@lru_cache(maxsize=4096)
def _read_toml(path: Path) -> dict:
    with path.open("rb") as f:
        return tomllib.load(f)


def chunk_body(chunk_id: str, corpus_dir: Path) -> str | None:
    p = resolve_chunk_path(chunk_id, corpus_dir)
    if p is None:
        return None
    data = _read_toml(p)
    return data.get("content", {}).get("body")


def chunk_citation(chunk_id: str, corpus_dir: Path) -> str:
    p = resolve_chunk_path(chunk_id, corpus_dir)
    if p is None:
        return chunk_id
    ch = _read_toml(p).get("chunk", {})
    name = ch.get("text_name", chunk_id)
    section = ch.get("section")
    return f"{name} — {section}" if section else name
