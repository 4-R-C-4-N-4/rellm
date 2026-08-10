"""Edge-proposal prompt contract + post-review label extraction.

The prompt mirrors guru/scripts/propose_edges.py exactly (PROMPT_VERSION v2)
so anything trained or benchmarked here sees the same input its production
caller sends.

Post-review truth: guru's review_edges.py rewrites `edge_type` on reclassify
(review_edges.py:177,184), and every rejection in the store went through the
reclassify path with an explicit reclassify_to. So on any reviewed row,
`edge_type` IS the corrected label — no join to review_actions needed.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from rellm.corpus import chunk_body, chunk_citation

EDGE_PROMPT_VERSION = "v2"

EDGE_TYPES = ("PARALLELS", "CONTRASTS", "surface_only", "unrelated")
POSITIVE_TYPES = ("PARALLELS", "CONTRASTS")
REVIEWED_STATUS = ("accepted", "rejected", "reclassified")

# Verbatim from guru/scripts/propose_edges.py SYSTEM_PROMPT.
EDGE_SYSTEM_PROMPT = """\
You are a comparative religion scholar. Given two passages from different mystical
traditions, classify their relationship. Respond ONLY with valid JSON.

A genuine PARALLEL can be conceptual (the same insight in different words) OR
structural — a shared narrative structure / mytheme carried by different
characters, names, and wording. Recurring cross-tradition mythemes count as
PARALLELS, not surface_only: the flood / deluge survivor, katabasis (descent to
and return from the underworld), the quest for immortality or the plant/food of
life, the dying-and-rising figure, theomachy (combat with a chaos-monster at
creation), judgment of the dead in the afterlife, the world-tree / axis mundi,
and the psychopomp who guides souls. Different tradition, different proper nouns,
and different surface vocabulary do NOT by themselves make a pair surface_only;
reserve surface_only for pairs whose only link is an incidental shared word or
image with no shared conceptual OR structural content.
"""


def build_edge_prompt(citation_a: str, body_a: str,
                      citation_b: str, body_b: str) -> str:
    """Verbatim from guru/scripts/propose_edges.py build_pair_prompt."""
    return f"""\
Passage A ({citation_a}):
\"\"\"
{body_a}
\"\"\"

Passage B ({citation_b}):
\"\"\"
{body_b}
\"\"\"

Classify the relationship between these two passages:
  PARALLELS    — genuine conceptual parallel (same insight, different tradition)
  CONTRASTS    — genuine conceptual opposition (same theme, opposite position)
  surface_only — superficially similar wording but no deep connection
  unrelated    — no meaningful connection

Respond with:
{{
  "edge_type": "<PARALLELS|CONTRASTS|surface_only|unrelated>",
  "confidence": <0.0-1.0>,
  "justification": "<one to two sentences explaining the relationship>"
}}
"""


def parse_edge_response(raw: str) -> dict | None:
    """Extract the verdict object from a model response.

    Tolerates markdown fences and a thinking-model preamble by scanning for
    the first balanced top-level object containing an edge_type.
    """
    if not raw:
        return None
    depth = 0
    start: int | None = None
    in_str = False
    esc = False
    for i, ch in enumerate(raw):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                try:
                    obj = json.loads(raw[start:i + 1])
                except json.JSONDecodeError:
                    start = None
                    continue
                if isinstance(obj, dict) and "edge_type" in obj:
                    return obj
                start = None
    return None


def normalize_verdict(obj: dict | None) -> tuple[str | None, float | None, str]:
    """(edge_type, confidence, justification) with the edge_type validated."""
    if not obj:
        return None, None, ""
    et = obj.get("edge_type")
    et = et if et in EDGE_TYPES else None
    try:
        conf = float(obj.get("confidence"))
    except (TypeError, ValueError):
        conf = None
    return et, conf, str(obj.get("justification") or "")


@dataclass
class EdgePair:
    """One reviewed staged_edge with both passages resolved."""

    edge_id: int
    source_chunk: str
    target_chunk: str
    label: str            # post-review edge_type — the gold label
    status: str
    confidence: float | None
    similarity: float | None
    model: str | None
    source_body: str
    target_body: str
    source_citation: str
    target_citation: str
    source_tradition: str
    target_tradition: str

    @property
    def is_positive(self) -> bool:
        return self.label in POSITIVE_TYPES

    @property
    def tradition_pair(self) -> tuple[str, str]:
        a, b = self.source_tradition, self.target_tradition
        return (a, b) if a <= b else (b, a)


def _text_id(chunk_id: str) -> str:
    parts = chunk_id.split(".", 2)
    return parts[1] if len(parts) >= 3 else chunk_id


def iter_reviewed_edges(
    conn: sqlite3.Connection,
    corpus_dir: Path,
    *,
    status: tuple[str, ...] = REVIEWED_STATUS,
    limit: int | None = None,
) -> Iterator[EdgePair]:
    """Yield reviewed staged_edges with both bodies resolvable on disk.

    Skips pairs whose chunk files are missing from the corpus (144 chunks are
    absent, costing ~277 pairs).
    """
    has_sim = "similarity" in {
        r[1] for r in conn.execute("PRAGMA table_info(staged_edges)")
    }
    sim_col = "se.similarity" if has_sim else "NULL"

    placeholders = ",".join("?" for _ in status)
    sql = f"""
        SELECT se.id, se.source_chunk, se.target_chunk, se.edge_type,
               se.status, se.confidence, {sim_col} AS similarity, se.model,
               ns.tradition_id AS src_trad, nt.tradition_id AS tgt_trad
        FROM staged_edges se
        LEFT JOIN nodes ns ON ns.id = se.source_chunk
        LEFT JOIN nodes nt ON nt.id = se.target_chunk
        WHERE se.status IN ({placeholders})
        ORDER BY se.id
    """
    emitted = 0
    for r in conn.execute(sql, list(status)):
        body_a = chunk_body(r["source_chunk"], corpus_dir)
        body_b = chunk_body(r["target_chunk"], corpus_dir)
        if body_a is None or body_b is None:
            continue
        yield EdgePair(
            edge_id=r["id"],
            source_chunk=r["source_chunk"],
            target_chunk=r["target_chunk"],
            label=r["edge_type"],
            status=r["status"],
            confidence=r["confidence"],
            similarity=r["similarity"],
            model=r["model"],
            source_body=body_a,
            target_body=body_b,
            source_citation=chunk_citation(r["source_chunk"], corpus_dir),
            target_citation=chunk_citation(r["target_chunk"], corpus_dir),
            source_tradition=r["src_trad"] or r["source_chunk"].split(".")[0],
            target_tradition=r["tgt_trad"] or r["target_chunk"].split(".")[0],
        )
        emitted += 1
        if limit and emitted >= limit:
            return


def group_key(pair: EdgePair) -> str:
    """Leakage-safe grouping key for train/test splits.

    19,338 pairs are drawn from only 4,720 distinct chunks (~8 pairs per
    chunk), so a random pair-level split puts the same passage on both sides
    of the boundary. Splitting on the text-pair keeps a whole
    (text_a, text_b) cluster together.
    """
    a = f"{pair.source_tradition}/{_text_id(pair.source_chunk)}"
    b = f"{pair.target_tradition}/{_text_id(pair.target_chunk)}"
    return "|".join(sorted((a, b)))
