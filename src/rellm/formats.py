"""Build SFT chat-format examples from extracted teacher data.

The prompt mirrors guru/scripts/tag_concepts.py exactly so the student learns
the same input contract its production caller will send.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from rellm.extract import TaggedChunk, TeacherTag
from rellm.taxonomy import Concept


SYSTEM_PROMPT = (
    "You are a comparative religion scholar helping to build a concept index "
    "of mystical texts. For each passage given, score it against every concept "
    "definition provided. Respond ONLY with a valid JSON array (no markdown, "
    "no commentary)."
)


def build_user_prompt(chunk_body: str, citation: str, concepts: list[Concept]) -> str:
    concepts_block = "\n".join(
        f'  {{"id": "{c.id}", "definition": "{c.definition}"}}' for c in concepts
    )
    return f"""Passage ({citation}):
\"\"\"
{chunk_body}
\"\"\"

Rate each concept 0-3 for how strongly this passage expresses it:
  0 = not present
  1 = peripherally present
  2 = clearly present
  3 = central theme

Concepts:
[
{concepts_block}
]

Return a JSON array of objects for every concept with score >= 1:
[
  {{
    "concept_id": "<id from list above OR a new snake_case id>",
    "score": <0-3>,
    "justification": "<one sentence>",
    "is_new_concept": <true if not in list>,
    "new_concept_def": "<definition if is_new_concept else null>"
  }}
]

Return [] if nothing scores >= 1. Output only the JSON array. No preamble, no explanation, no markdown fences. Start your response with [ and end with ]. Return [] if nothing scores >= 1."""


def parse_model_tags(raw: str) -> tuple[bool, dict[str, int]]:
    """Parse a model's JSON-array response into (parse_ok, {concept_id: score}).

    Tolerates markdown fences and a few common wrapper shapes ({"tags": [...]}).
    Returns (False, {}) when the body fails to parse as JSON at all. An empty
    list parses as (True, {}).
    """
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:].strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return False, {}
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
    return True, out


def serialize_teacher_tags(tags: list[TeacherTag]) -> str:
    out = [
        {
            "concept_id": t.concept_id,
            "score": t.score,
            "justification": t.justification or "",
            "is_new_concept": t.is_new_concept,
            "new_concept_def": t.new_concept_def,
        }
        for t in tags
    ]
    return json.dumps(out, ensure_ascii=False)


def sft_example(chunk: TaggedChunk, concepts: list[Concept]) -> dict:
    return {
        "chunk_id": chunk.chunk_id,
        "tradition_id": chunk.tradition_id,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(chunk.body, chunk.citation, concepts)},
            {"role": "assistant", "content": serialize_teacher_tags(chunk.tags)},
        ],
    }


def write_sft_jsonl(
    chunks: Iterable[TaggedChunk],
    concepts: list[Concept],
    out_path: Path,
) -> int:
    n = 0
    with out_path.open("w") as f:
        for ch in chunks:
            f.write(json.dumps(sft_example(ch, concepts), ensure_ascii=False) + "\n")
            n += 1
    return n
