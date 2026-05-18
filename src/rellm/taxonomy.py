"""Load the guru concept taxonomy."""
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Concept:
    id: str
    category: str
    definition: str


def load_taxonomy(path: Path) -> list[Concept]:
    with path.open("rb") as f:
        raw = tomllib.load(f)
    out: list[Concept] = []
    for category, items in raw.get("concepts", {}).items():
        for cid, definition in items.items():
            out.append(Concept(id=cid, category=category, definition=definition))
    return out
