#!/usr/bin/env bash
# Bench base / v1 / v2 against the v2 test split, one llama-server at a time.
# More robust than running three servers concurrently (which had connection
# failures around chunk 30 — likely a memory-pressure issue).
#
# Output dir contains the combined cells.csv / runs.csv suitable for
# eval/report.py and eval/report_v2_compare.py.

set -euo pipefail

EXPORT_DIR="${EXPORT_DIR:-data/exports/2026-05-21T16-49-07Z}"
BASE_GGUF="${BASE_GGUF:-$HOME/programs/qwen/qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf}"
V1_GGUF="${V1_GGUF:-out/qwen25-7b-r32/qwen2.5-7b-rellm-Q4_K_M.gguf}"
V2_GGUF="${V2_GGUF:-out/qwen25-7b-r32-v2/qwen2.5-7b-rellm-Q4_K_M.gguf}"
LLAMA_SERVER="${LLAMA_SERVER:-$HOME/programs/llama.cpp/build/bin/llama-server}"
TS="$(date -u +%Y-%m-%dT%H-%M-%SZ)"
OUT_DIR="${OUT_DIR:-runs/bench/v2-vs-v1-vs-base-serial-$TS}"
EXTRA_ARGS="${EXTRA_ARGS:-}"   # forwarded to eval/bench.py (e.g. --all-curated)

for f in "$BASE_GGUF" "$V1_GGUF" "$V2_GGUF" "$LLAMA_SERVER"; do
    [[ -e "$f" ]] || { echo "missing: $f" >&2; exit 1; }
done
[[ -f "$EXPORT_DIR/sft.jsonl" && -f "$EXPORT_DIR/splits.json" ]] || {
    echo "export dir incomplete: $EXPORT_DIR" >&2; exit 1
}

mkdir -p "$OUT_DIR/server-logs"

PORT=18080

bench_one() {
    local name="$1" model="$2"
    echo "→ ($name) starting llama-server on :$PORT ($(basename "$model"))"
    "$LLAMA_SERVER" \
        --model "$model" \
        --host 127.0.0.1 --port "$PORT" \
        --ctx-size 8192 --n-gpu-layers 999 --parallel 1 \
        --jinja --no-webui \
        > "$OUT_DIR/server-logs/$name.log" 2>&1 &
    local pid=$!
    cleanup() { kill "$pid" 2>/dev/null || true; }
    trap cleanup EXIT INT TERM

    local tries=120
    until curl -sf "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; do
        (( tries-- > 0 )) || { echo "server $name on :$PORT never came up" >&2; exit 1; }
        sleep 1
    done
    echo "→ ($name) server ready, running bench"

    local tmp_dir="$OUT_DIR/_$name"
    mkdir -p "$tmp_dir"
    uv run python eval/bench.py \
        --export-dir "$EXPORT_DIR" \
        --endpoint "$name=http://127.0.0.1:$PORT" \
        --out-dir "$tmp_dir" \
        $EXTRA_ARGS

    kill "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
    trap - EXIT INT TERM
    sleep 3  # let GPU memory release
}

bench_one base "$BASE_GGUF"
bench_one v1   "$V1_GGUF"
bench_one v2   "$V2_GGUF"

# concat per-model outputs into the combined dir
{
    head -1 "$OUT_DIR/_base/cells.csv"
    for n in base v1 v2; do tail -n +2 "$OUT_DIR/_$n/cells.csv"; done
} > "$OUT_DIR/cells.csv"
{
    head -1 "$OUT_DIR/_base/runs.csv"
    for n in base v1 v2; do tail -n +2 "$OUT_DIR/_$n/runs.csv"; done
} > "$OUT_DIR/runs.csv"

echo ""
echo "→ bench done: $OUT_DIR"
echo "→ aggregating: uv run python eval/report.py $OUT_DIR"
uv run python eval/report.py "$OUT_DIR" | tee "$OUT_DIR/report.txt"
