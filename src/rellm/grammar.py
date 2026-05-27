"""Generate a GBNF grammar from the concept taxonomy.

Constrains a model's output to the exact tagging JSON schema that
`rellm.formats.build_user_prompt` asks for. llama.cpp masks illegal tokens at
every decoding step, so the model *cannot* emit invalid JSON, malformed concept
ids, or out-of-range scores — structural validity is guaranteed, not hoped for.

Two vocabulary modes:

  - open  (allow_new=True, default): concept_id is any well-formed snake_case
    string. Preserves guru's new-concept discovery (`is_new_concept` proposals)
    while still guaranteeing valid JSON and killing garbage/prose ids. Novel ids
    become review-queue signal, not errors. Use for tagging / discovery passes.

  - strict (allow_new=False): concept_id must be one of the taxonomy's ids, so
    out-of-taxonomy ids are impossible. Use for sweeps against a frozen concept
    set where new proposals are unwanted.

The grammar is *derived from the taxonomy*, so it regenerates for free when the
taxonomy changes — no retraining. Note: the grammar guarantees structure for
*completed* generations; a response truncated by `max_tokens` mid-array is still
incomplete, so pair it with an adequate token budget.
"""
from __future__ import annotations

from rellm.taxonomy import Concept

# Fixed part of the schema (matches formats.serialize_teacher_tags). The `cid`
# rule is appended by build_grammar() per mode. Raw string so GBNF's \" and \\
# pass through untouched.
# Each rule MUST be on a single line — the llama.cpp GBNF parser treats a
# newline as a rule terminator, so a wrapped rule body fails to parse.
_SCHEMA = r'''root ::= ws "[" ws ( tag ( ws "," ws tag )* ws )? "]" ws
tag ::= "{" ws "\"concept_id\"" ws ":" ws cid ws "," ws "\"score\"" ws ":" ws score ws "," ws "\"justification\"" ws ":" ws string ws "," ws "\"is_new_concept\"" ws ":" ws boolean ws "," ws "\"new_concept_def\"" ws ":" ws ( string | "null" ) ws "}"
score ::= "0" | "1" | "2" | "3"
boolean ::= "true" | "false"
string ::= "\"" ( [^"\\] | "\\" ["\\/bfnrt] )* "\""
ws ::= [ \t\n]*
'''


def build_grammar(concepts: list[Concept], *, allow_new: bool = True) -> str:
    """GBNF for the tagging output schema. allow_new toggles open vs strict ids."""
    if allow_new:
        # any well-formed snake_case id (known or novel) — discovery preserved
        cid_rule = 'cid       ::= "\\"" [a-z] [a-z0-9_]* "\\""'
    else:
        # closed vocabulary: exactly the taxonomy's ids
        ids = sorted({c.id for c in concepts})
        if not ids:
            raise ValueError("strict grammar needs a non-empty taxonomy")
        alts = " | ".join(f'"\\"{cid}\\""' for cid in ids)
        cid_rule = f"cid       ::= {alts}"
    return _SCHEMA + cid_rule + "\n"
