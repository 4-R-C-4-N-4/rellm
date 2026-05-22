#!/usr/bin/env bash
# Stand up base / v1 / v2 llama-servers and bench all three against the v2
# test split in one shot.
#
# Prereqs:
#   - out/qwen25-7b-r32/qwen2.5-7b-rellm-Q4_K_M.gguf        (v1)
#   - out/qwen25-7b-r32-v2/qwen2.5-7b-rellm-Q4_K_M.gguf     (v2 — produced by scripts/to_gguf.sh)
#   - qwen2.5-7b-instruct-q4_k_m-*.gguf                     (base, in repo root)
#   - GPU free (~20 GB needed for three 7B Q4_K_M servers on one card)
#
# Output: runs/bench/v2-vs-v1-vs-base-<ts>/{cells,runs}.csv
#
# Override defaults via env: EXPORT_DIR, BASE_GGUF, V1_GGUF, V2_GGUF, OUT_DIR

set -euo pipefail

EXPORT_DIR="${EXPORT_DIR:-data/exports/2026-05-21T16-49-07Z}"
BASE_GGUF="${BASE_GGUF:-$HOME/programs/qwen/qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf}"
V1_GGUF="${V1_GGUF:-out/qwen25-7b-r32/qwen2.5-7b-rellm-Q4_K_M.gguf}"
V2_GGUF="${V2_GGUF:-out/qwen25-7b-r32-v2/qwen2.5-7b-rellm-Q4_K_M.gguf}"
LLAMA_SERVER="${LLAMA_SERVER:-$HOME/programs/llama.cpp/build/bin/llama-server}"
TS="$(date -u +%Y-%m-%dT%H-%M-%SZ)"
OUT_DIR="${OUT_DIR:-runs/bench/v2-vs-v1-vs-base-$TS}"

for f in "$BASE_GGUF" "$V1_GGUF" "$V2_GGUF" "$LLAMA_SERVER"; do
    [[ -e "$f" ]] || { echo "missing: $f" >&2; exit 1; }
done
[[ -f "$EXPORT_DIR/sft.jsonl" && -f "$EXPORT_DIR/splits.json" ]] || {
    echo "export dir incomplete: $EXPORT_DIR" >&2; exit 1
}

mkdir -p "$OUT_DIR"
LOG_DIR="$OUT_DIR/server-logs"
mkdir -p "$LOG_DIR"

start_server() {
    local name="$1" port="$2" model="$3"
    echo "→ starting $name on :$port ($(basename "$model"))"
    "$LLAMA_SERVER" \
        --model "$model" \
        --host 127.0.0.1 --port "$port" \
        --ctx-size 7168 --n-gpu-layers 999 --parallel 1 \
        --jinja --no-webui \
        > "$LOG_DIR/$name.log" 2>&1 &
    echo $! > "$LOG_DIR/$name.pid"
}

wait_ready() {
    local port="$1" tries=120
    until curl -sf "http://127.0.0.1:$port/health" >/dev/null 2>&1; do
        (( tries-- > 0 )) || { echo "server on :$port never came up" >&2; return 1; }
        sleep 1
    done
}

cleanup() {
    echo "→ stopping servers"
    for pidfile in "$LOG_DIR"/*.pid; do
        [[ -f "$pidfile" ]] || continue
        kill "$(cat "$pidfile")" 2>/dev/null || true
        rm -f "$pidfile"
    done
}
trap cleanup EXIT

start_server base 8080 "$BASE_GGUF"
start_server v1   8081 "$V1_GGUF"
start_server v2   8082 "$V2_GGUF"

for port in 8080 8081 8082; do wait_ready "$port"; done
echo "→ all three servers ready, running bench"

uv run python eval/bench.py \
    --export-dir "$EXPORT_DIR" \
    --endpoint base=http://127.0.0.1:8080 \
    --endpoint v1=http://127.0.0.1:8081 \
    --endpoint v2=http://127.0.0.1:8082 \
    --out-dir "$OUT_DIR"

echo ""
echo "→ bench done: $OUT_DIR"
echo "→ aggregating: uv run python eval/report.py $OUT_DIR"
uv run python eval/report.py "$OUT_DIR" | tee "$OUT_DIR/report.txt"
