#!/usr/bin/env bash
# Resume bench_qwen3_4b_v3.sh from an interrupted run: reuse completed
# _base/_v1 legs already on disk, only re-run the missing legs, then merge.
set -uo pipefail

EXPORT_DIR="${EXPORT_DIR:-data/exports/2026-08-06T21-46-44Z}"
SNAPSHOT="${SNAPSHOT:-data/snapshots/2026-08-06T21-44-52Z}"
TAXONOMY="${TAXONOMY:-/home/ivy/Work/guru/concepts/taxonomy.toml}"
V2_GGUF="${V2_GGUF:-out/qwen3-4b-guru-v2/gguf/qwen-3-4b-guru-v2-Q4_K_M.gguf}"
V3_GGUF="${V3_GGUF:-out/qwen3-4b-guru-v3-r32/qwen-3-4b-guru-v3-Q4_K_M.gguf}"
LLAMA_SERVER="${LLAMA_SERVER:-$HOME/programs/llama.cpp/build/bin/llama-server}"
OUT_DIR="${1:?Usage: $0 <existing OUT_DIR with _base and _v1 already done>}"

[[ -f "$OUT_DIR/_base/cells.csv" && -f "$OUT_DIR/_v1/cells.csv" ]] || { echo "expected _base and _v1 already complete in $OUT_DIR" >&2; exit 1; }

PORT=18098
bench_one() {
    local name="$1" model="$2"
    # A killed run can leave cells.csv empty OR partially populated (bench.py
    # writes incrementally) — neither is "done". Require every one of the
    # 181 test chunks to actually appear in column 2 before treating a leg
    # as complete; anything short is deleted and redone from scratch.
    local n_chunks=0
    [[ -f "$OUT_DIR/_$name/cells.csv" ]] && n_chunks=$(tail -n +2 "$OUT_DIR/_$name/cells.csv" | cut -d',' -f2 | sort -u | wc -l)
    if [[ "$n_chunks" -ge 181 ]]; then
        echo "→ ($name) already done ($n_chunks/181 chunks), skipping"
        return
    fi
    echo "→ ($name) incomplete ($n_chunks/181 chunks) or missing, redoing from scratch"
    rm -rf "$OUT_DIR/_$name"
    echo "→ ($name) starting llama-server ($(basename "$model"))"
    local retries=3
    while (( retries-- > 0 )); do
        "$LLAMA_SERVER" --model "$model" --host 127.0.0.1 --port "$PORT" \
            --ctx-size 20480 --n-gpu-layers 999 --parallel 1 --device CUDA1 --flash-attn on --jinja --no-webui \
            > "$OUT_DIR/server-logs/$name.log" 2>&1 &
        local pid=$!
        local tries=180 up=0
        until curl -sf "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; do
            (( tries-- > 0 )) || break
            kill -0 "$pid" 2>/dev/null || break
            sleep 1
        done
        curl -sf "http://127.0.0.1:$PORT/health" >/dev/null 2>&1 && { up=1; }
        if [[ "$up" == "1" ]]; then
            mkdir -p "$OUT_DIR/_$name"
            PYTHONUNBUFFERED=1 .venv/bin/python eval/bench.py \
                --export-dir "$EXPORT_DIR" --snapshot "$SNAPSHOT" --split test \
                --taxonomy "$TAXONOMY" --max-tokens 6144 \
                --endpoint "$name=http://127.0.0.1:$PORT" --out-dir "$OUT_DIR/_$name"
            kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true
            sleep 3
            return
        fi
        echo "  ($name) attempt failed, retrying ($retries left)" >&2
        kill -9 "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true
        sleep 3
    done
    echo "$name: all retries exhausted" >&2
    exit 1
}

bench_one v2 "$V2_GGUF"
bench_one v3 "$V3_GGUF"

{ head -1 "$OUT_DIR/_base/cells.csv"; for n in base v1 v2 v3; do tail -n +2 "$OUT_DIR/_$n/cells.csv"; done; } > "$OUT_DIR/cells.csv"
{ head -1 "$OUT_DIR/_base/runs.csv";  for n in base v1 v2 v3; do tail -n +2 "$OUT_DIR/_$n/runs.csv";  done; } > "$OUT_DIR/runs.csv"

echo ""; echo "=== HUMAN-GRADED ==="
.venv/bin/python eval/report_human.py "$OUT_DIR" | tee "$OUT_DIR/report_human.txt"
echo ""; echo "=== TEACHER-LABEL ==="
.venv/bin/python eval/report.py "$OUT_DIR" | tee "$OUT_DIR/report.txt"
