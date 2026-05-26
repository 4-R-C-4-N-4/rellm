#!/usr/bin/env bash
# Bench v3 alone on the SAME held-out test split + SAME snapshot the base/v1/v2
# gauge used, then fold v3 into a combined dir so all four are scored against
# identical human labels. Avoids re-running base/v1/v2 (saves ~30 min) and
# guarantees label parity.

set -euo pipefail

GAUGE_DIR="${GAUGE_DIR:-runs/bench/gauge-human-2026-05-25T13-00-46Z}"   # has base/v1/v2
EXPORT_DIR="${EXPORT_DIR:-data/exports/2026-05-21T16-49-07Z}"            # 130-chunk test split
SNAPSHOT="${SNAPSHOT:-data/snapshots/2026-05-25T13-00-46Z}"             # identical human labels
V3_GGUF="${V3_GGUF:-out/qwen25-7b-r32-v3/gguf/qwen2.5-7b-rellm-Q4_K_M.gguf}"
LLAMA_SERVER="${LLAMA_SERVER:-$HOME/programs/llama.cpp/build/bin/llama-server}"
TS="$(date -u +%Y-%m-%dT%H-%M-%SZ)"
OUT_DIR="${OUT_DIR:-runs/bench/gauge-v3-$TS}"

for f in "$V3_GGUF" "$LLAMA_SERVER" "$GAUGE_DIR/cells.csv"; do
    [[ -e "$f" ]] || { echo "missing: $f" >&2; exit 1; }
done

mkdir -p "$OUT_DIR/server-logs" "$OUT_DIR/_v3"
PORT=18080

echo "→ (v3) starting llama-server on :$PORT"
"$LLAMA_SERVER" --model "$V3_GGUF" --host 127.0.0.1 --port "$PORT" \
    --ctx-size 8192 --n-gpu-layers 999 --parallel 1 --jinja --no-webui \
    > "$OUT_DIR/server-logs/v3.log" 2>&1 &
pid=$!
trap 'kill "$pid" 2>/dev/null || true' EXIT INT TERM

tries=120
until curl -sf "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; do
    (( tries-- > 0 )) || { echo "v3 server never came up" >&2; exit 1; }
    sleep 1
done
echo "→ (v3) server ready, benching"

uv run python eval/bench.py \
    --export-dir "$EXPORT_DIR" \
    --snapshot "$SNAPSHOT" \
    --split test \
    --endpoint "v3=http://127.0.0.1:$PORT" \
    --out-dir "$OUT_DIR/_v3"

kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true; trap - EXIT INT TERM

# combine: base/v1/v2 (from gauge) + v3
{ cat "$GAUGE_DIR/cells.csv"; tail -n +2 "$OUT_DIR/_v3/cells.csv"; } > "$OUT_DIR/cells.csv"
{ cat "$GAUGE_DIR/runs.csv";  tail -n +2 "$OUT_DIR/_v3/runs.csv";  } > "$OUT_DIR/runs.csv"

echo ""; echo "→ combined: $OUT_DIR"
echo "=== HUMAN-GRADED (base/v1/v2/v3) ==="
uv run python eval/report_human.py "$OUT_DIR" | tee "$OUT_DIR/report_human.txt"
echo ""; echo "=== teacher-label view ==="
uv run python eval/report.py "$OUT_DIR" | tee "$OUT_DIR/report.txt"
