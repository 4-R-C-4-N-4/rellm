#!/usr/bin/env bash
# Head-to-head: base / qwen-3-4b-guru-v1 / qwen-3-4b-guru-v2 on the v2-export test
# split (323 held-out chunks neither model saw at training), graded against the
# fresh snapshot's current human verdicts.
#
# Same 88-concept v1 taxonomy as both models trained on — pure data-delta test:
# does v2's 10x rejection signal + extra accepted data actually beat v1?

set -uo pipefail

EXPORT_DIR="${EXPORT_DIR:-data/exports/2026-06-09T03-24-50Z}"
SNAPSHOT="${SNAPSHOT:-data/snapshots/2026-06-09T03-24-41Z}"
TAXONOMY="${TAXONOMY:-$EXPORT_DIR/taxonomy.toml}"
BASE_GGUF="${BASE_GGUF:-$HOME/programs/qwen/Qwen3-4B-Instruct-2507-Q4_K_M.gguf}"
V1_GGUF="${V1_GGUF:-out/qwen3-4b-guru/gguf/qwen-3-4b-guru-Q4_K_M.gguf}"
V2_GGUF="${V2_GGUF:-out/qwen3-4b-guru-v2/gguf/qwen-3-4b-guru-v2-Q4_K_M.gguf}"
LLAMA_SERVER="${LLAMA_SERVER:-$HOME/programs/llama.cpp/build/bin/llama-server}"
TS="$(date -u +%Y-%m-%dT%H-%M-%SZ)"
OUT_DIR="${OUT_DIR:-runs/bench/qwen3-4b-v1-v2-$TS}"

for f in "$BASE_GGUF" "$V1_GGUF" "$V2_GGUF" "$LLAMA_SERVER" "$TAXONOMY"; do
    [[ -e "$f" ]] || { echo "missing: $f" >&2; exit 1; }
done
mkdir -p "$OUT_DIR/server-logs"

PORT=18097
bench_one() {
    local name="$1" model="$2"
    echo "→ ($name) starting llama-server ($(basename "$model"))"
    "$LLAMA_SERVER" --model "$model" --host 127.0.0.1 --port "$PORT" \
        --ctx-size 12288 --n-gpu-layers 999 --parallel 1 --jinja --no-webui \
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
    PYTHONUNBUFFERED=1 uv run python eval/bench.py \
        --export-dir "$EXPORT_DIR" --snapshot "$SNAPSHOT" --split test \
        --taxonomy "$TAXONOMY" --max-tokens 6144 \
        --endpoint "$name=http://127.0.0.1:$PORT" --out-dir "$OUT_DIR/_$name"
    kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true; trap - EXIT INT TERM
    sleep 3
}

bench_one base "$BASE_GGUF"
bench_one v1   "$V1_GGUF"
bench_one v2   "$V2_GGUF"

{ head -1 "$OUT_DIR/_base/cells.csv"; for n in base v1 v2; do tail -n +2 "$OUT_DIR/_$n/cells.csv"; done; } > "$OUT_DIR/cells.csv"
{ head -1 "$OUT_DIR/_base/runs.csv";  for n in base v1 v2; do tail -n +2 "$OUT_DIR/_$n/runs.csv";  done; } > "$OUT_DIR/runs.csv"

echo ""; echo "=== HUMAN-GRADED ==="
uv run python eval/report_human.py "$OUT_DIR" | tee "$OUT_DIR/report_human.txt"
echo ""; echo "=== TEACHER-LABEL ==="
uv run python eval/report.py "$OUT_DIR" | tee "$OUT_DIR/report.txt"
