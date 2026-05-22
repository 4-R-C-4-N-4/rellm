# Zero-Tag Diagnostic — Debug Re-Run Findings

Follow-up to `80-concept-teacher-run-retro.md`. Re-ran the same prompt + same teacher model (`Qwen3.5-27B-UD-Q4_K_XL.gguf` via llamacpp) against a 20-chunk sample of production zero-tag results, capturing raw responses to `data/retag-debug/<chunk_id>.json`.

## Headline

**The failure mode is thinking-budget overflow, not vocabulary mismatch or taxonomy coverage.**

The model engages deeply with these chunks and identifies the right concepts; it just runs out of `max_tokens=6000` before emitting the JSON array. The pre-JSON reasoning is preserved and discarded by the production pipeline.

Sample: 20 zero-tag chunks (10 each from `tertium-organum` and `life-and-doctrines-boehme`), spread across the chunk range, body-only (no `.001` title pages).

## Bimodal model behavior

The response distribution is sharply bimodal:

| Classification | Count | Raw length (chars) | What happened |
|---|---:|---|---|
| `tags_emitted` | 8 | 400 – 2,297 | Model went straight to JSON, ~700 token total. Parsed cleanly. |
| `empty_array` | 12 | 20,035 – 23,039 | Model wrote ~6000 tokens of "Thinking Process" prose, exhausted budget, never emitted `[...]`. `parse_json_response` found nothing and returned `[]`. |

There is no in-between. The model either answers directly in <2.5k chars or goes into long-form reasoning and runs out of tokens.

Important: this is **stochastic, not deterministic per chunk**. `tertium-organum.120` was zero-tag in production and emitted 8 tags on re-run with identical inputs — the sampling just happened to land it in direct-answer mode the second time.

## What the lost reasoning contains

For most empty_array chunks, the reasoning text ends with the model's explicit final list of concepts and scores, formatted like:

```
Final list:
1. mechanical_humanity (3)
2. self_knowledge (3)
3. pneumatic_elect (2)
4. hidden_sayings (2)
5. spiritual_ascent (2)
6. fragmentation_of_knowledge (New, 2)
7. cosmic_dualism (1)
8. eschatological_judgment (1)
```

That's `tertium-organum.200` — the "wheat and tares" / two-classes-of-humanity chunk where I predicted in the retro that `pneumatic_elect` should fire. It did fire; the model just never got to write the JSON.

Concepts the model identified (across the 12 thinking responses) include both existing taxonomy entries — `pneumatic_elect`, `self_knowledge`, `hidden_sayings`, `spiritual_ascent`, `theosis_deification`, `microcosm_macrocosm`, `correspondence`, `gnosis_direct_knowledge`, `separation_from_source`, `return_to_source`, `sephirot`, `infinite_cosmos`, `cosmic_sympathy`, `paradox_as_teaching`, `divine_madness` — and **new concepts the model proposed** like `mechanical_humanity`, `kingdom_within`, `inner_silence`, `divine_intoxication`, `alchemical_work`, `detachment_gelassenheit`, `inner_light`, `opposites_transcended`, `body_as_obstacle`, `numerical_mysticism`, `unity_of_being`, `living_god`, `evil_as_privation`, `cosmic_dualism`, `fragmentation_of_knowledge`, `self_examination`, `tripartite_soul`, `ritual_fire`. Several of those are strong candidates for a taxonomy v2.

## Why the production pipeline misses this

`scripts/llm.py:call_llamacpp` has a thinking-model branch:

```python
content = msg.get("content") or ""
reasoning = msg.get("reasoning_content") or ""
if content.strip():
    return content
return reasoning  # so parse_json_response can scan for JSON
```

But the Qwen3.5-27B teacher doesn't separate reasoning into the `reasoning_content` field — it emits its analysis as plain `content` (literally starting "Thinking Process:\n\n1. Analyze the Request:"). So:

1. `call_llamacpp` returns the prose as if it were a normal response.
2. `parse_json_response` scans for `[` or `{`, finds nothing parseable (the model never got to JSON), returns `[]`.
3. `parse_tags` returns `[]`.
4. `tag_concepts.py` logs `: 0 tags` and moves on.
5. The reasoning — which contains the actual concept-scoring answer — is discarded.

`<think>` and `</think>` delimiter counts in these responses are zero, so the existing thinking-model branch doesn't help.

## Impact estimate

In-sample: 12/20 zero-tag chunks (60%) were budget-overflow misses with recoverable signal; 8/20 were correctly handled on retry (the same prompt happened to land in direct-answer mode).

Production-wide extrapolation is more nuanced because the 1294 zero-tag total is dominated by apparatus:

- ~664 zeros are concentrated in `-index` texts (`plotinus-select-works-index` 373, `egyptian-book-of-the-dead-index` 156, `zhuangzi-inner-chapters-index` 135). These are correct rejections.
- The remaining ~630 zero-tag chunks are scattered across body-text content. If the 60% budget-overflow rate from this sample generalizes to that population, **roughly ~380 chunks production-wide have recoverable concept signal in lost reasoning**.

## Recommendations

In rough order of cost vs. payoff:

1. **Raise `max_tokens` in `tag_concepts.py`** from 6000 to 16,000 or 24,000. The teacher's `n_ctx_train` is 262,144 so context is not the limit. This is a one-line change and would have prevented the majority of these misses on the first run.
2. **Prompt-side: instruct the model to emit JSON first, then optionally reason after.** Current system prompt says "Respond ONLY with a valid JSON array" but the model still produces a thinking-process preamble. Adding "Begin your response with `[`. Do not write any analysis or reasoning before the JSON." may push it into direct-answer mode more reliably.
3. **Salvage existing zero-tag rows.** Write a one-off that, for every body-text zero-tag chunk in production (~630), re-runs with raised max_tokens. Compare new tag count vs. zero; populate `staged_tags` with the recovered results under a new `prompt_version` so the review tool can show old/new side by side.
4. **Capture raw responses in production going forward.** Add a `--save-raw <dir>` flag to `tag_concepts.py` that writes the raw response per chunk on every run. Cheap insurance; we lose ~5MB per 1000 chunks worth of artifacts but gain forensic data for future surprises.
5. **Pull the model's proposed new concepts** from the 12 thinking responses into a candidate list for taxonomy v2 discussion.

## Methodology note

Two slips in the retro this addendum follows up:

1. The retro originally cited `tertium-organum.050` and `boehme.050` as zero-tag examples; both actually got tags (8 and 7 respectively). I read those chunks for content during the retro but didn't verify zero-tag membership. The retro has been corrected to use verified zero-tag chunks (`.030/.100/.200` for Tertium, `.060/.100` for Boehme).
2. The "vocabulary mismatch" and "taxonomy gap" hypotheses in the retro were both wrong. The teacher's vocabulary handles modern paraphrase fine (it picked up Ouspensky's "wheat and tares" → `pneumatic_elect`) and the taxonomy covers most of the substantive content (it just also wanted to propose new entries). The actual problem is much more mundane: token-budget exhaustion in a thinking model.

The lesson for next time: when surfacing model behavior from a long run, the first thing to verify is whether the artifacts capture the model's actual response or just a downstream parse outcome. If only the parse outcome is preserved, the explanation surface is much thinner than it looks.
