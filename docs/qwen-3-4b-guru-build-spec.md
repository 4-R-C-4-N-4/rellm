# qwen-3-4b-guru — Build Spec

**Status:** ready for execution
**Owner:** Ivy
**Target executor:** local coding agent (Hermes / Claude Code)
**Type:** production build, not experiment

---

## 1. Objective

Ship a fast, human-aligned chunk→concept tagger for the guru pipeline. Replace the 27B teacher in the bulk-tagging step so corpus iteration cycles drop from days to hours. Quality bar is "good enough to surface candidates for human review in guru-review," not "perfect labels."

Model name: **`qwen-3-4b-guru`**
HF repo: `4rc4n4/qwen-3-4b-guru`
Git tag: `qwen-3-4b-guru-v1` on both rellm GitHub and HF repos

---

## 2. Quality and speed bars

Both must be met for ship.

### Quality (on stratified held-out human test set, ~300 chunks)

- Recall ≥ 0.65
- Precision ≥ 0.50
- Macro-F1 ≥ 0.50
- OOT (out-of-taxonomy IDs) rate < 1%
- Parse rate ≥ 99%

Recall is floored above precision because reviewers can reject false positives in one click but cannot see omissions. Asymmetric error cost → recall-leaning model.

### Speed (on llama-server, RTX 3090, Q4_K_M GGUF unless quant sweep selects otherwise)

- Per-chunk latency: report, no hard cap
- **Throughput at concurrency 4: ≥ 600 chunks/hour** (the actual production constraint — full 10k chunk re-tag in under 24h with headroom)

### Hard gates (any failure blocks ship)

- OOT rate < 1%
- Parse rate ≥ 99%
- No tradition with ≥20 train chunks has F1 < 0.30 (no blind spots)

---

## 3. Base model

`Qwen/Qwen3-4B-Instruct-2507`

Training-time variant: `unsloth/Qwen3-4B-Instruct-2507-bnb-4bit` if available, else load full-precision with `load_in_4bit=True` via Unsloth `FastLanguageModel.from_pretrained`.

**Why not Qwen3.5-4B (March 2026):** multimodal-by-design (5B params including vision encoder we never use), hybrid Gated DeltaNet + MoE architecture with immature QLoRA tooling on consumer GPUs, thinking-by-default. Wrong tradeoffs for a text-only structured-output fast tagger. Revisit for v2.

**Why not Qwen3-4B-Thinking-2507:** SFT on JSON-only targets trains the thinking out of the model unless training data includes reasoning traces, which we don't have. Deferred to a separate experiment.

---

## 4. Data

### Source

Re-export from current `guru.db`, table `staged_tags`, teacher
`Qwen3.5-27B-UD-Q4_K_XL.gguf` + `prompt_version='v1'` (same filter rellm uses;
the 783 `Carnice-9b` rows are a different model, excluded). Same 88-concept
taxonomy as production — do NOT migrate to the three-tier hierarchy in this build.

**The live data is NOT fully reviewed.** As of 2026-05-26 the teacher's rows are:

| status | tags | chunks |
|---|---:|---:|
| pending (unreviewed) | 13,372 | 2,559 |
| accepted (human-verified) | 12,521 | 2,372 |
| rejected (human-verified negative) | 7,517 | 2,021 |
| reassigned | 10 | 10 |

So the original "every row is a human-verified positive, no filtering needed" is
wrong. **Filter policy: `status IN ('pending','accepted')` — drop rejected and
reassigned.** This is rellm's default and was validated in the rellm v2→v3 cycle:
dropping the human-rejected tags improved both precision *and* recall against human
truth. Training on rejected rows as positives would teach the model to emit tags
humans explicitly threw out — the opposite of the goal.

Including `pending` (unreviewed teacher positives) is deliberate for a
recall-leaning model: it maximizes positive coverage. The tradeoff is noise — by
the reviewed accept/reject ratio, roughly a third of pending rows would likely be
rejected if reviewed. If a cleaner, precision-leaning run is wanted instead, the
alternative is **accepted-only** (12,521 tags / 2,372 chunks), at the cost of ~15%
fewer chunks and weaker coverage on under-reviewed traditions.

**Expected scale (pending+accepted):** ~25,900 tag rows across **2,808 chunks**,
48% human-accepted. Tags span 94 distinct `concept_id`s — the 88 taxonomy concepts
plus ~6 reviewer-proposed new ids; the prompt still presents only the 88.

(The original "~3k chunks, ~10k tag rows" under-counted rows ~2.5×.)

### Splits

80 / 10 / 10, stratified by tradition (not just `chunk_id`), seed 42.

Expected from 2,808 chunks: **~2,246 train / ~281 val / ~281 test**.

**Why stratify by tradition, not just chunk_id:** per-tradition F1 is a hard gate (§2). A purely chunk_id-stratified split could leave small traditions with <5 test chunks, making per-tradition F1 unmeasurable. Tradition-stratified guarantees signal on every tradition with ≥20 train examples.

### Tradition histogram check (pre-flight)

Before splitting, run the tradition histogram. For any tradition with <20 chunks total, exclude it from the per-tradition F1 gate (note in model card as "insufficient signal"). For traditions with 20–50 chunks, expect noisy per-tradition F1 and treat the 0.30 floor as approximate.

**Actuals (2026-05-26, pending+accepted universe, 15 traditions / 2,808 chunks):**

| tradition | chunks | | tradition | chunks |
|---|---:|---|---|---:|
| neoplatonism | 694 | | renaissance_hermeticism | 110 |
| egyptian | 408 | | hermeticism | 63 |
| taoism | 327 | | sufism | 37 |
| greek_mystery | 253 | | platonism | 35 |
| western_esoteric | 215 | | buddhism | 20 |
| christian_mysticism | 181 | | mesopotamian | 15 |
| jewish_mysticism | 173 | | | |
| zoroastrianism | 151 | | | |
| gnosticism | 126 | | | |

- **14 traditions ≥20 chunks** → per-tradition F1 gate applies.
- **mesopotamian (15)** is under 20 → excluded from the gate as "insufficient signal."
- **buddhism (20), platonism (35), sufism (37)** are in the noisy 20–50 band; with an 80% train split buddhism yields only ~16 train chunks, so treat its 0.30 floor as approximate (or fold it into the insufficient-signal note).

### Drop policy

Chunks exceeding `max_seq_length=8192` after tokenization: drop from training, log the count. Do NOT right-truncate (cuts the assistant JSON target). Expected drop count: **near 0** — the same export tokenized with the Qwen2.5 tokenizer at 88 concepts maxed at ~7,150 tokens (median ~5,170), so 8192 clears nearly everything. Confirm with the Qwen3 tokenizer in Phase 2 (its tokenization differs slightly), but the 17% drop that bit rellm at the 3090's 5632 ceiling does not recur at 8192.

For production inference, over-length chunks get sliding-window fallback (separate pipeline concern, not a training-time issue).

### Prompt builder

`src/rellm/formats.py` unchanged. The prompt contract is the production contract:

- **System:** `"You are a comparative religion scholar helping to build a concept index of mystical texts. For each passage given, score it against every concept definition provided. Respond ONLY with a valid JSON array (no markdown, no commentary)."`
- **User:** passage block, 0–3 rubric, JSON list of `{id, definition}` candidate concepts, output schema, `Return [] if nothing scores >= 1.`
- **Assistant target:** JSON array of `{id, score}` objects, scores 1–3, concepts scoring 0 omitted.

---

## 5. Training recipe

| Param                | Value                                | Notes                                                                    |
| -------------------- | ------------------------------------ | ------------------------------------------------------------------------ |
| Method               | QLoRA via Unsloth + TRL `SFTTrainer` |                                                                          |
| LoRA r               | 32                                   |                                                                          |
| LoRA α               | 64                                   |                                                                          |
| LoRA dropout         | 0                                    |                                                                          |
| Target modules       | `q,k,v,o,gate,up,down`               |                                                                          |
| Epochs               | 3                                    |                                                                          |
| Per-device batch     | 1                                    |                                                                          |
| Grad accumulation    | 16                                   | Effective batch 16                                                       |
| Optimizer            | paged AdamW-8bit                     |                                                                          |
| Learning rate        | 1.5e-4                               |                                                                          |
| LR schedule          | cosine                               |                                                                          |
| Warmup ratio         | 0.03                                 |                                                                          |
| Sequence length      | **8192**                             | 4B has the headroom; recovers chunks rellm dropped                       |
| Chat template        | Qwen3 (from tokenizer)               | Do NOT override; verify in pre-flight                                    |
| Checkpoint selection | best-by-val-loss                     |                                                                          |
| Seed                 | 42                                   |                                                                          |
| Hardware             | single 24 GB RTX 3090                |                                                                          |
| Expected wall-clock  | 6–9h                                 |                                                                          |

Abort condition: if val loss at end of epoch 1 is worse than 1.5× the starting loss, kill the run — indicates recipe failure on the new base.

---

## 6. Pre-flight checks (mandatory, before launching full training)

### Check 1: Chat template sanity

Tokenize one training example end-to-end. Visually inspect for:

- `<|im_start|>` and `<|im_end|>` markers (Qwen3 ChatML)
- System message in system role, not concatenated into user
- Assistant target = JSON array only, no leading whitespace or markdown fences
- `add_generation_prompt=False` during training (target is in the data, not to be generated)

**This is the #1 silent failure mode for Qwen3 fine-tunes.** Qwen2.5 and Qwen3 use different templates; Unsloth auto-detection can pick wrong. Block on this check.

### Check 2: Overfit-a-batch sanity

Train on 8 fixed examples for 200 steps, eval disabled. Confirm:

- Loss decreases monotonically toward ~0
- Sampled generations produce valid JSON arrays matching the training targets
- No NaN losses, no gradient explosions

If loss stalls or generations are garbage, the recipe is broken. Block.

### Check 3: Zero-shot baseline on held-out human test set

Run `Qwen3-4B-Instruct-2507` zero-shot (no fine-tune) against the 300-chunk test set. Record full eval (precision, recall, F1, macro-F1, OOT rate, parse rate, per-tradition F1).

This serves three purposes:
1. **Skip-training gate:** if zero-shot already meets all §2 quality gates, ship the zero-shot model. No training needed.
2. **Prompt-contract compatibility check:** confirms the prompt format works on the new base before burning training compute.
3. **Floor:** the fine-tune must beat zero-shot convincingly to justify the training cost.

---

## 7. Execution plan

### Phase 1: Setup

- Branch `feat/qwen-3-4b-guru` off rellm main
- Copy `configs/rellm.yaml` → `configs/qwen-3-4b-guru.yaml`, edit per §5
- Add `qwen-3-4b-guru` to adapter registry schema with rollback metadata pointing to rellm

### Phase 2: Data prep

- Export current `staged_tags` to `data/exports/qwen-3-4b-guru/`
- Generate tradition histogram, write to `data/exports/qwen-3-4b-guru/tradition_histogram.json`
- Generate 80/10/10 tradition-stratified split with seed 42, write split manifest
- Tokenize a stratified 50-chunk sample, log sequence length distribution against 8192 cap

### Phase 3: Pre-flight

Run all three checks in §6. Block on any failure.

**Decision point after Check 3:** if zero-shot meets all §2 gates, skip to Phase 6 with the zero-shot model. Document the decision in `docs/qwen-3-4b-guru-zero-shot-decision.md`.

### Phase 4: Train

- Launch full SFT run with W&B logging under `qwen-3-4b-guru-v1`
- Monitor val loss; apply abort condition (§5)
- On completion, save best-by-val-loss checkpoint

### Phase 5: Merge, quantize, sweep

- Merge LoRA adapter into base FP16 weights → `merged/`
- Convert to GGUF F16 via `llama.cpp/convert_hf_to_gguf.py`
- Quantize to Q4_K_M, Q5_K_M, Q6_K, Q8_0 via `llama-quantize`
- **Quantization sweep:** run full eval (§2 metrics) against held-out test set on each quant level
- Select the smallest quant that loses ≤2 F1 points vs FP16 merged. Default selection: Q4_K_M unless it regresses meaningfully.

### Phase 6: Throughput benchmark

- Spin up llama-server with selected GGUF, `--jinja`, port 8080
- Benchmark chunks/hour at concurrency 1, 2, 4, 8 on a representative 100-chunk sample (real prompts, real concept lists)
- Record throughput curve in model card. Hard gate: ≥600 chunks/hour at concurrency 4.

### Phase 7: Decision

Apply §2 gates. Document outcome in `docs/qwen-3-4b-guru-decision.md` with full metrics table.

Three possible outcomes:

- **All gates pass:** proceed to Phase 8 (ship)
- **Quality gates pass, throughput gate fails:** ship anyway, note throughput regression as a known limitation, file follow-up for quant or inference-stack optimization
- **Any quality gate fails:** write postmortem to `docs/qwen-3-4b-guru-postmortem.md`, tag adapter on HF as `v1-failed` for reproducibility, do not promote

### Phase 8: Ship

Push to HF `4rc4n4/qwen-3-4b-guru`:

- `adapter/` — LoRA adapter (~150 MB)
- `merged/` — FP16 merged weights (~8 GB)
- `gguf/qwen-3-4b-guru-F16.gguf`
- `gguf/qwen-3-4b-guru-<selected-quant>.gguf` (production serving artifact)

Write model card with:
- Absolute eval numbers on human test set (no rellm comparison; see §9)
- Per-tradition F1 breakdown
- Per-concept F1 breakdown
- Quantization sweep results
- Throughput curve
- Prompt contract (production caller-compatible)
- Limitations section

Tag `qwen-3-4b-guru-v1` on git and HF.

### Phase 9: Production cutover

- Register adapter in guru's adapter registry with rollback metadata pointing to rellm
- Flag-gate routing in the guru tagging caller: `tagging.model = qwen-3-4b-guru | rellm`
- Run A/B for one week on incoming new corpus chunks: tag with both, store both, route to human review (review against either output is fine since both go through guru-review)
- After one week, evaluate human-review rejection rates per model. If qwen-3-4b-guru's rejection rate ≤ rellm's, flip the default. Keep rellm in the registry for rollback.

---

## 8. Artifacts and deliverables

- HF repo `4rc4n4/qwen-3-4b-guru` with all artifacts above
- `configs/qwen-3-4b-guru.yaml` in rellm repo
- `docs/qwen-3-4b-guru-decision.md` (gate outcome)
- `docs/qwen-3-4b-guru-zero-shot-decision.md` (Phase 3 decision)
- `docs/qwen-3-4b-guru-postmortem.md` (only if ship fails)
- Adapter registry entry with rollback metadata
- W&B run permalink in model card
- This spec, annotated with actuals, committed as `docs/qwen-3-4b-guru-build-spec.md`

---

## 9. Out of scope

Explicit non-goals to prevent scope creep:

- **Comparison to rellm in the model card.** Goal is "ship best fast tagger," not "beat rellm." Some held-out test chunks were almost certainly in rellm's training data; reported comparisons would be misleading. Model card reports absolute numbers on the new held-out test set only.
- **Three-tier taxonomy migration** (domain → family → concept). Same 88-concept flat taxonomy as production.
- **Thinking-mode variant.** Deferred to separate experiment with reasoning-augmented training data.
- **Qwen3.5-4B base.** Wrong architecture for this task, immature tooling. Revisit in 2–3 months for v2.
- **Larger held-out test set.** 300 chunks is sufficient given §2 gates; growing the test set is a separate workstream tracked in guru-review.

---

## 10. Risks and mitigations

| Risk                                                                  | Likelihood | Mitigation                                                                                  |
| --------------------------------------------------------------------- | ---------- | ------------------------------------------------------------------------------------------- |
| Qwen3 chat template applied incorrectly during training                | Medium     | Pre-flight check #1                                                                          |
| 4B underfits 88-concept taxonomy                                      | Low-medium | Per-tradition F1 breakdown surfaces this; rellm rollback available                          |
| Unsloth bnb-4bit variant unavailable                                  | Low        | Fallback to full-precision base with `load_in_4bit=True`                                    |
| Q4_K_M loses meaningful F1 vs FP16                                    | Medium     | Quant sweep in Phase 5 selects best size/quality tradeoff                                   |
| Throughput at concurrency 4 falls short                               | Low        | At 4B with Q4_K_M on 3090, expected throughput ~1000–1500 chunks/hr; if shortfall, try Q4_K_S or bump concurrency to 6 |
| Held-out test chunks overlap rellm training set, contaminating comparison | High       | §9: no rellm comparison in model card; report absolute numbers only                          |
| Zero-shot Qwen3-4B-Instruct-2507 meets gates, raising "should we even train" question | Medium     | Phase 3 decision point handles this explicitly — ship zero-shot if gates met, no training needed |

---

## 11. Definition of done

- All phases in §7 completed
- Either: model shipped to HF + adapter registered + git tagged + A/B routing live, OR postmortem written and adapter archived
- This spec annotated with actuals (final eval numbers, selected quant, throughput at each concurrency, wall-clock, dropped-chunk count) and committed
- Adapter registry has rollback path to rellm verified-functional via dry-run rollback
