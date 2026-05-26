#!/usr/bin/env bash
# Human-graded gauge: re-bench base / v1 / v2 on the held-out v2 test split,
# scored against the *current* human review (accepted/rejected), not teacher
# labels. Answers "how do v1 and v2 actually compare on human ground truth?"
# on the 130 chunks neither was trained on (118 now carry human verdicts).
#
# Takes a fresh snapshot at run time so the newest review lands in the bench.
# One server at a time on :18080 (concurrent servers OOM'd a 24 GB card before).
#
# Outputs, in $OUT_DIR:
#   report_human.txt   — humans-as-truth P/R/F1 per model, broken out by split
#   report.txt         — teacher-label view (for continuity with the v2 doc)
#   report_compare.txt — v1 vs v2 per-tradition / per-concept deltas

set -euo pipefail

EXPORT_DIR="${EXPORT_DIR:-data/exports/2026-05-21T16-49-07Z}"   # holds the v2 test split
V1_EXPORT="${V1_EXPORT:-data/exports/2026-05-13T16-31-48Z}"     # for v1-test carryover table
BASE_GGUF="${BASE_GGUF:-$HOME/programs/qwen/qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf}"
V1_GGUF="${V1_GGUF:-out/qwen25-7b-r32/qwen2.5-7b-rellm-Q4_K_M.gguf}"
V2_GGUF="${V2_GGUF:-out/qwen25-7b-r32-v2/gguf/qwen2.5-7b-rellm-Q4_K_M.gguf}"
LLAMA_SERVER="${LLAMA_SERVER:-$HOME/programs/llama.cpp/build/bin/llama-server}"
TS="$(date -u +%Y-%m-%dT%H-%M-%SZ)"
OUT_DIR="${OUT_DIR:-runs/bench/gauge-human-$TS}"

for f in "$BASE_GGUF" "$V1_GGUF" "$V2_GGUF" "$LLAMA_SERVER"; do
    [[ -e "$f" ]] || { echo "missing: $f" >&2; exit 1; }
done
[[ -f "$EXPORT_DIR/splits.json" ]] || { echo "export dir incomplete: $EXPORT_DIR" >&2; exit 1; }

echo "→ snapshotting live guru.db so the newest review is in the gauge"
uv run rellm snapshot >/dev/null
SNAPSHOT="$(ls -d data/snapshots/*/ | sort | tail -1)"
SNAPSHOT="${SNAPSHOT%/}"
echo "→ using snapshot: $SNAPSHOT"

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
        --snapshot "$SNAPSHOT" \
        --split test \
        --endpoint "$name=http://127.0.0.1:$PORT" \
        --out-dir "$tmp_dir"

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
echo "=== HUMAN-GRADED (the gauge) ==="
uv run python eval/report_human.py "$OUT_DIR" | tee "$OUT_DIR/report_human.txt"
echo ""
echo "=== teacher-label view ==="
uv run python eval/report.py "$OUT_DIR" | tee "$OUT_DIR/report.txt"
echo ""
echo "=== v1 vs v2 deltas ==="
uv run python eval/report_v2_compare.py "$OUT_DIR" --v1-export "$V1_EXPORT" \
    | tee "$OUT_DIR/report_compare.txt"
