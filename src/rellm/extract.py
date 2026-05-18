"""Pull (chunk, teacher_tags) join rows from a guru.db snapshot."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

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
    teacher_model: str,
    prompt_version: str,
    status: tuple[str, ...] = ("pending", "accepted"),
    limit: int | None = None,
) -> Iterator[TaggedChunk]:
    """Yield one TaggedChunk per chunk that has staged_tags from this teacher.

    Filters by (model, prompt_version, status). Aggregates rows into one
    record per chunk_id. Skips chunks whose body isn't resolvable on disk.
    """
    placeholders = ",".join("?" for _ in status)
    sql = f"""
        SELECT s.chunk_id, s.concept_id, s.score, s.justification,
               s.is_new_concept, s.new_concept_def, s.status, n.tradition_id
        FROM staged_tags s
        JOIN nodes n ON n.id = s.chunk_id
        WHERE s.model = ?
          AND s.prompt_version = ?
          AND s.status IN ({placeholders})
        ORDER BY s.chunk_id, s.concept_id
    """
    params = [teacher_model, prompt_version, *status]
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
