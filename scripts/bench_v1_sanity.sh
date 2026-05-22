#!/usr/bin/env bash
# Sanity-bench v1 against its own original snapshot + test split.
# Goal: verify the v1 model card's F1=0.629 (vs teacher) still reproduces.

set -euo pipefail

V1_GGUF="${V1_GGUF:-out/qwen25-7b-r32/qwen2.5-7b-rellm-Q4_K_M.gguf}"
V1_EXPORT="${V1_EXPORT:-data/exports/2026-05-13T16-31-48Z}"
V1_SNAPSHOT="${V1_SNAPSHOT:-data/snapshots/2026-05-11T22-12-29Z-initial}"
LLAMA_SERVER="${LLAMA_SERVER:-$HOME/programs/llama.cpp/build/bin/llama-server}"
TS="$(date -u +%Y-%m-%dT%H-%M-%SZ)"
OUT_DIR="${OUT_DIR:-runs/bench/v1-sanity-$TS}"

mkdir -p "$OUT_DIR/server-logs"

echo "→ starting v1 llama-server on :18080"
"$LLAMA_SERVER" \
    --model "$V1_GGUF" \
    --host 127.0.0.1 --port 18080 \
    --ctx-size 6144 --n-gpu-layers 999 --parallel 1 \
    --jinja --no-webui \
    > "$OUT_DIR/server-logs/v1.log" 2>&1 &
PID=$!
trap "kill $PID 2>/dev/null || true" EXIT INT TERM

tries=120
until curl -sf http://127.0.0.1:18080/health >/dev/null 2>&1; do
    (( tries-- > 0 )) || { echo "server never came up"; exit 1; }
    sleep 1
done
echo "→ server ready, running bench"

uv run python eval/bench.py \
    --export-dir "$V1_EXPORT" \
    --snapshot "$V1_SNAPSHOT" \
    --endpoint v1=http://127.0.0.1:18080 \
    --out-dir "$OUT_DIR"

kill $PID 2>/dev/null || true
wait $PID 2>/dev/null || true

echo ""
echo "→ bench done: $OUT_DIR"
uv run python eval/report.py "$OUT_DIR" | tee "$OUT_DIR/report.txt"
