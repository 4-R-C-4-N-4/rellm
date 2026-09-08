#!/usr/bin/env bash
# v5 evaluation: base / v4 / v5 on
#   (1) BENCH — v5's held-out test split (223 chunks), teacher-label graded, full
#       154-concept taxonomy in every prompt → no-regression check vs v4.
#   (2) PROBE — the 31 held-out (val/test) older-tradition cells where one of the
#       12 backfill concepts is a vetted-accepted positive (v5 never trained on
#       these chunks), plus kalevala psychic_attack guards. This is the fair
#       backfill generalization test: v5 should FIRE the target where v4 (0
#       cross-tradition training rows) misses, and stay SILENT on the guards.
set -uo pipefail

EXPORT_DIR="${EXPORT_DIR:-data/exports/2026-09-06T12-21-28Z}"
SNAPSHOT="${SNAPSHOT:-data/snapshots/2026-09-06T12-15-36Z-v5}"
TAXONOMY="${TAXONOMY:-/home/ivy/Work/guru/concepts/taxonomy.toml}"
BASE_GGUF="${BASE_GGUF:-$HOME/programs/qwen/Qwen3-4B-Instruct-2507-Q4_K_M.gguf}"
V4_GGUF="${V4_GGUF:-out/qwen3-4b-guru-v4-r32/qwen-3-4b-guru-v4-Q4_K_M.gguf}"
V5_GGUF="${V5_GGUF:-out/qwen3-4b-guru-v5-r32/qwen-3-4b-guru-v5-Q4_K_M.gguf}"
LLAMA_SERVER="${LLAMA_SERVER:-$HOME/programs/llama.cpp/build/bin/llama-server}"
PROBE_IDS="${PROBE_IDS:-runs/probe-v5/chunk-ids.txt}"
TS="$(date -u +%Y-%m-%dT%H-%M-%SZ)"
OUT_DIR="${OUT_DIR:-runs/bench/qwen3-4b-v5-$TS}"

for f in "$BASE_GGUF" "$V4_GGUF" "$V5_GGUF" "$LLAMA_SERVER" "$TAXONOMY" "$PROBE_IDS"; do
    [[ -e "$f" ]] || { echo "missing: $f" >&2; exit 1; }
done
mkdir -p "$OUT_DIR/server-logs" "$OUT_DIR/probe"

PORT=18099
eval_one() {
    local name="$1" model="$2"
    echo "→ ($name) starting llama-server ($(basename "$model"))"
    # llama.cpp device numbering is INVERTED vs nvidia-smi (CUDA0=4070, CUDA1=3090)
    # and ignores CUDA_DEVICE_ORDER — must pin the 3090 with --device CUDA1.
    "$LLAMA_SERVER" --model "$model" --host 127.0.0.1 --port "$PORT" \
        --ctx-size 20480 --n-gpu-layers 999 --parallel 1 --device CUDA1 \
        --flash-attn on --jinja --no-webui \
        > "$OUT_DIR/server-logs/$name.log" 2>&1 &
    local pid=$!
    cleanup() { kill "$pid" 2>/dev/null || true; }
    trap cleanup EXIT INT TERM
    local tries=180
    until curl -sf "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; do
        (( tries-- > 0 )) || { echo "$name never came up" >&2; kill "$pid" 2>/dev/null; exit 1; }
        sleep 1
    done

    echo "  ($name) bench test split…"
    mkdir -p "$OUT_DIR/_$name"
    PYTHONUNBUFFERED=1 .venv/bin/python eval/bench.py \
        --export-dir "$EXPORT_DIR" --snapshot "$SNAPSHOT" --split test \
        --taxonomy "$TAXONOMY" --max-tokens 6144 \
        --endpoint "$name=http://127.0.0.1:$PORT" --out-dir "$OUT_DIR/_$name"

    echo "  ($name) probe held-out backfill cells…"
    .venv/bin/python -m rellm tag --endpoint "http://127.0.0.1:$PORT" \
        --snapshot "$SNAPSHOT" --taxonomy "$TAXONOMY" --max-tokens 6144 \
        --out "$OUT_DIR/probe/$name.jsonl" < "$PROBE_IDS" 2>/dev/null \
      || .venv/bin/rellm tag --endpoint "http://127.0.0.1:$PORT" \
        --snapshot "$SNAPSHOT" --taxonomy "$TAXONOMY" --max-tokens 6144 \
        --out "$OUT_DIR/probe/$name.jsonl" < "$PROBE_IDS"

    kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true; trap - EXIT INT TERM
    sleep 3
}

eval_one base "$BASE_GGUF"
eval_one v4   "$V4_GGUF"
eval_one v5   "$V5_GGUF"

# merge bench CSVs
{ head -1 "$OUT_DIR/_base/cells.csv"; for n in base v4 v5; do tail -n +2 "$OUT_DIR/_$n/cells.csv"; done; } > "$OUT_DIR/cells.csv"
{ head -1 "$OUT_DIR/_base/runs.csv";  for n in base v4 v5; do tail -n +2 "$OUT_DIR/_$n/runs.csv";  done; } > "$OUT_DIR/runs.csv"

echo ""; echo "=== BENCH (teacher-label, held-out test split) ==="
.venv/bin/python eval/report.py "$OUT_DIR" | tee "$OUT_DIR/report.txt"

echo ""; echo "=== PROBE (held-out backfill generalization) ==="
.venv/bin/python scripts/probe_report_v5.py "$OUT_DIR/probe" runs/probe-v5/manifest.json | tee "$OUT_DIR/probe_report.txt"

echo ""; echo "done: $OUT_DIR"
