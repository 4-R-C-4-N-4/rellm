#!/usr/bin/env bash
# Head-to-head: base / qwen-3-4b-guru-v1 / v2 / v3 on v3's own held-out test
# split (181 chunks), graded against the current (post-quarantine) snapshot's
# human verdicts, using the live full ~110-concept taxonomy in every prompt.
#
# Verified zero leakage: every one of these 181 chunks that existed in v1/v2's
# corpus at export time landed in their VAL bucket (never train) under the
# split hash, so this is a fair held-out comparison for all four models —
# note v1/v2 see the full taxonomy for the first time here (they were trained
# on the pinned 88-concept fallback), which is exactly the capability delta
# v3 is meant to fix.

set -uo pipefail

EXPORT_DIR="${EXPORT_DIR:-data/exports/2026-08-06T21-46-44Z}"
SNAPSHOT="${SNAPSHOT:-data/snapshots/2026-08-06T21-44-52Z}"
TAXONOMY="${TAXONOMY:-/home/ivy/Work/guru/concepts/taxonomy.toml}"
BASE_GGUF="${BASE_GGUF:-$HOME/programs/qwen/Qwen3-4B-Instruct-2507-Q4_K_M.gguf}"
V1_GGUF="${V1_GGUF:-out/qwen3-4b-guru/gguf/qwen-3-4b-guru-Q4_K_M.gguf}"
V2_GGUF="${V2_GGUF:-out/qwen3-4b-guru-v2/gguf/qwen-3-4b-guru-v2-Q4_K_M.gguf}"
V3_GGUF="${V3_GGUF:-out/qwen3-4b-guru-v3-r32/qwen-3-4b-guru-v3-Q4_K_M.gguf}"
LLAMA_SERVER="${LLAMA_SERVER:-$HOME/programs/llama.cpp/build/bin/llama-server}"
TS="$(date -u +%Y-%m-%dT%H-%M-%SZ)"
OUT_DIR="${OUT_DIR:-runs/bench/qwen3-4b-v3-$TS}"

for f in "$BASE_GGUF" "$V1_GGUF" "$V2_GGUF" "$V3_GGUF" "$LLAMA_SERVER" "$TAXONOMY"; do
    [[ -e "$f" ]] || { echo "missing: $f" >&2; exit 1; }
done
mkdir -p "$OUT_DIR/server-logs"

PORT=18098
bench_one() {
    local name="$1" model="$2"
    echo "→ ($name) starting llama-server ($(basename "$model"))"
    # llama.cpp's own device numbering is inverted from nvidia-smi's PCI-bus
    # order (confirmed via --list-devices: CUDA0=4070, CUDA1=3090) and does
    # NOT respect CUDA_DEVICE_ORDER the way PyTorch does — must use --device
    # explicitly, else it silently layer-splits across both cards.
    "$LLAMA_SERVER" --model "$model" --host 127.0.0.1 --port "$PORT" \
        --ctx-size 20480 --n-gpu-layers 999 --parallel 1 --device CUDA1 --flash-attn on --jinja --no-webui \
        > "$OUT_DIR/server-logs/$name.log" 2>&1 &
    local pid=$!
    cleanup() { kill "$pid" 2>/dev/null || true; }
    trap cleanup EXIT INT TERM
    local tries=180
    until curl -sf "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; do
        (( tries-- > 0 )) || { echo "$name never came up" >&2; exit 1; }
        sleep 1
    done
    mkdir -p "$OUT_DIR/_$name"
    PYTHONUNBUFFERED=1 .venv/bin/python eval/bench.py \
        --export-dir "$EXPORT_DIR" --snapshot "$SNAPSHOT" --split test \
        --taxonomy "$TAXONOMY" --max-tokens 6144 \
        --endpoint "$name=http://127.0.0.1:$PORT" --out-dir "$OUT_DIR/_$name"
    kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true; trap - EXIT INT TERM
    sleep 3
}

bench_one base "$BASE_GGUF"
bench_one v1   "$V1_GGUF"
bench_one v2   "$V2_GGUF"
bench_one v3   "$V3_GGUF"

{ head -1 "$OUT_DIR/_base/cells.csv"; for n in base v1 v2 v3; do tail -n +2 "$OUT_DIR/_$n/cells.csv"; done; } > "$OUT_DIR/cells.csv"
{ head -1 "$OUT_DIR/_base/runs.csv";  for n in base v1 v2 v3; do tail -n +2 "$OUT_DIR/_$n/runs.csv";  done; } > "$OUT_DIR/runs.csv"

echo ""; echo "=== HUMAN-GRADED ==="
.venv/bin/python eval/report_human.py "$OUT_DIR" | tee "$OUT_DIR/report_human.txt"
echo ""; echo "=== TEACHER-LABEL ==="
.venv/bin/python eval/report.py "$OUT_DIR" | tee "$OUT_DIR/report.txt"
