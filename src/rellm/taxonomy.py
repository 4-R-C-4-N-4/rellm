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
    """Parse [concepts.DOMAIN.FAMILY] tables — three tiers, concepts are the leaves.

    Pre-hierarchy taxonomy.toml had a flat [concepts.CATEGORY] shape (one dict
    of id->definition per category); the v2 domain/family restructuring added
    a tier, so this now descends domain -> family -> concept to reach the
    leaf definitions instead of treating each family as a single concept.
    """
    with path.open("rb") as f:
        raw = tomllib.load(f)
    out: list[Concept] = []
    for domain, families in raw.get("concepts", {}).items():
        for family, items in families.items():
            for cid, definition in items.items():
                out.append(Concept(id=cid, category=family, definition=definition))
    return out
