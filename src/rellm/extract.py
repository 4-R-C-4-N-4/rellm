"""Pull (chunk, teacher_tags) join rows from a guru.db snapshot."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Sequence

from rellm.corpus import chunk_body, chunk_citation


@dataclass
class TeacherTag:
    concept_id: str
    score: int
    justification: str | None
    is_new_concept: bool
    new_concept_def: str | None
    status: str = "pending"


@dataclass
class TaggedChunk:
    chunk_id: str
    body: str
    citation: str
    tradition_id: str | None
    tags: list[TeacherTag]


def iter_teacher_chunks(
    conn: sqlite3.Connection,
    corpus_dir: Path,
    *,
    exclude_prefixes: Sequence[str] = (),
    exclude_models: Sequence[str] = (),
    prompt_version: str,
    status: tuple[str, ...] = ("pending", "accepted"),
    limit: int | None = None,
) -> Iterator[TaggedChunk]:
    """Yield one TaggedChunk per chunk with usable teacher staged_tags.

    Takes every tag (any model) matching (prompt_version, status) EXCEPT models
    whose signature starts with an `exclude_prefixes` entry or exactly matches an
    `exclude_models` entry. This denylist shape is deliberate: staged_tags.model
    is unreliable free-text (tag_concepts.py --model default, not the loaded
    gguf), so an allowlist would silently drop a mislabeled teacher. The one
    invariant is excluding the student's own lineage (self-distillation). Rows are
    aggregated into one record per chunk_id; chunks whose body isn't resolvable on
    disk are skipped.
    """
    placeholders = ",".join("?" for _ in status)
    where = ["s.prompt_version = ?", f"s.status IN ({placeholders})"]
    params: list = [prompt_version, *status]
    for pref in exclude_prefixes:
        where.append("s.model NOT LIKE ?")
        params.append(pref + "%")
    if exclude_models:
        ph = ",".join("?" for _ in exclude_models)
        where.append(f"s.model NOT IN ({ph})")
        params.extend(exclude_models)
    sql = f"""
        SELECT s.chunk_id, s.concept_id, s.score, s.justification,
               s.is_new_concept, s.new_concept_def, s.status, n.tradition_id
        FROM staged_tags s
        JOIN nodes n ON n.id = s.chunk_id
        WHERE {" AND ".join(where)}
        ORDER BY s.chunk_id, s.concept_id
    """
    rows = conn.execute(sql, params)

    current_id: str | None = None
    current_tradition: str | None = None
    tags: list[TeacherTag] = []
    emitted = 0

    def finalize() -> TaggedChunk | None:
        if current_id is None:
            return None
        body = chunk_body(current_id, corpus_dir)
        if body is None:
            return None
        return TaggedChunk(
            chunk_id=current_id,
            body=body,
            citation=chunk_citation(current_id, corpus_dir),
            tradition_id=current_tradition,
            tags=tags.copy(),
        )

    for r in rows:
        if r["chunk_id"] != current_id:
            done = finalize()
            if done is not None:
                yield done
                emitted += 1
                if limit is not None and emitted >= limit:
                    return
            current_id = r["chunk_id"]
            current_tradition = r["tradition_id"]
            tags = []
        tags.append(TeacherTag(
            concept_id=r["concept_id"],
            score=r["score"],
            justification=r["justification"],
            is_new_concept=bool(r["is_new_concept"]),
            new_concept_def=r["new_concept_def"],
            status=r["status"],
        ))

    done = finalize()
    if done is not None:
        yield done
