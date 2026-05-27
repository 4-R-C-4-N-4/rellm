#!/usr/bin/env bash
# Exploratory bench for qwen-3-4b-guru: zero-shot base Qwen3-4B vs the fine-tuned
# student, on the 4B's OWN held-out test split (contamination-free for the 4B),
# scored against teacher labels and human verdicts from the same snapshot.
#
# No rellm/7B comparison here (per the build-spec §9: some of these test chunks
# were in the 7B's training set, so a cross-model comparison would be misleading).
#
# Larger ctx (12288) than the 7B gauge so the longest prompts (~7.1k tok) plus a
# full response fit without context truncation confounding the parse rate.

set -euo pipefail

EXPORT_DIR="${EXPORT_DIR:-data/exports/2026-05-26T13-03-07Z}"     # 293-chunk test split
SNAPSHOT="${SNAPSHOT:-data/snapshots/2026-05-26T13-02-19Z}"        # teacher + human labels
# The model trained on the 88 flat concepts; guru's live taxonomy.toml has since
# migrated to three-tier (6 domains), so score against the reconstructed snapshot.
TAXONOMY="${TAXONOMY:-data/exports/2026-05-26T13-03-07Z/taxonomy.toml}"
BASE_GGUF="${BASE_GGUF:-$HOME/programs/qwen/Qwen3-4B-Instruct-2507-Q4_K_M.gguf}"
GURU_GGUF="${GURU_GGUF:-out/qwen3-4b-guru/gguf/qwen-3-4b-guru-Q4_K_M.gguf}"
LLAMA_SERVER="${LLAMA_SERVER:-$HOME/programs/llama.cpp/build/bin/llama-server}"
TS="$(date -u +%Y-%m-%dT%H-%M-%SZ)"
OUT_DIR="${OUT_DIR:-runs/bench/qwen3-4b-$TS}"

for f in "$BASE_GGUF" "$GURU_GGUF" "$LLAMA_SERVER"; do
    [[ -e "$f" ]] || { echo "missing: $f" >&2; exit 1; }
done

mkdir -p "$OUT_DIR/server-logs"
PORT=18092

bench_one() {
    local name="$1" model="$2"
    echo "→ ($name) starting llama-server on :$PORT ($(basename "$model"))"
    "$LLAMA_SERVER" --model "$model" --host 127.0.0.1 --port "$PORT" \
        --ctx-size 12288 --n-gpu-layers 999 --parallel 1 --jinja --no-webui \
        > "$OUT_DIR/server-logs/$name.log" 2>&1 &
    local pid=$!
    cleanup() { kill "$pid" 2>/dev/null || true; }
    trap cleanup EXIT INT TERM
    local tries=180
    until curl -sf "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; do
        (( tries-- > 0 )) || { echo "server $name never came up" >&2; exit 1; }
        sleep 1
    done
    echo "→ ($name) server ready, benching"
    mkdir -p "$OUT_DIR/_$name"
    uv run python eval/bench.py \
        --export-dir "$EXPORT_DIR" --snapshot "$SNAPSHOT" --split test \
        --taxonomy "$TAXONOMY" \
        --endpoint "$name=http://127.0.0.1:$PORT" --out-dir "$OUT_DIR/_$name"
    kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true; trap - EXIT INT TERM
    sleep 3
}

bench_one base "$BASE_GGUF"
bench_one guru "$GURU_GGUF"

{ head -1 "$OUT_DIR/_base/cells.csv"; for n in base guru; do tail -n +2 "$OUT_DIR/_$n/cells.csv"; done; } > "$OUT_DIR/cells.csv"
{ head -1 "$OUT_DIR/_base/runs.csv";  for n in base guru; do tail -n +2 "$OUT_DIR/_$n/runs.csv";  done; } > "$OUT_DIR/runs.csv"

echo ""; echo "→ combined: $OUT_DIR"
echo "=== HUMAN-GRADED (base vs guru) ==="
uv run python eval/report_human.py "$OUT_DIR" | tee "$OUT_DIR/report_human.txt"
echo ""; echo "=== teacher-label view ==="
uv run python eval/report.py "$OUT_DIR" | tee "$OUT_DIR/report.txt"
