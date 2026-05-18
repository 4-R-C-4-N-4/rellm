#!/usr/bin/env bash
# Convert a merged HF checkpoint to a quantized GGUF for llama.cpp.
#
# Two-step: HF → f16 GGUF → quantized GGUF. The intermediate f16 is kept so
# you can re-quantize to a different size (Q5_K_M, Q8_0, etc.) without
# re-running the slow conversion.
#
# Usage:
#   scripts/to_gguf.sh <merged-dir> <output-basename> [quant]
#
# Example:
#   scripts/to_gguf.sh out/qwen25-7b-r32/merged qwen2.5-7b-rellm Q4_K_M
#
# Produces, next to the merged dir:
#   <basename>-F16.gguf      (intermediate, ~14GB for 7B)
#   <basename>-<quant>.gguf  (~4.7GB for Q4_K_M)

set -euo pipefail

MERGED_DIR="${1:?Usage: $0 <merged-dir> <output-basename> [quant=Q4_K_M]}"
OUT_NAME="${2:?Usage: $0 <merged-dir> <output-basename> [quant=Q4_K_M]}"
QUANT="${3:-Q4_K_M}"

LLAMA_CPP="${LLAMA_CPP:-$HOME/programs/llama.cpp}"
CONVERT="$LLAMA_CPP/convert_hf_to_gguf.py"
QUANTIZE_BIN="$LLAMA_CPP/build/bin/llama-quantize"
PYTHON="${PYTHON:-$HOME/Work/rellm/.venv/bin/python}"

if [[ ! -f "$CONVERT" ]]; then
    echo "convert_hf_to_gguf.py not found at $CONVERT" >&2
    exit 1
fi
if [[ ! -x "$QUANTIZE_BIN" ]]; then
    echo "llama-quantize not found at $QUANTIZE_BIN" >&2
    exit 1
fi
if [[ ! -d "$MERGED_DIR" ]]; then
    echo "merged dir not found: $MERGED_DIR" >&2
    exit 1
fi

OUT_PARENT="$(dirname "$MERGED_DIR")"
F16_GGUF="$OUT_PARENT/${OUT_NAME}-F16.gguf"
QUANT_GGUF="$OUT_PARENT/${OUT_NAME}-${QUANT}.gguf"

if [[ -f "$F16_GGUF" ]]; then
    echo "skipping HF → F16 (already exists: $F16_GGUF)"
else
    echo "→ converting HF → F16 GGUF: $F16_GGUF"
    "$PYTHON" "$CONVERT" "$MERGED_DIR" --outfile "$F16_GGUF" --outtype f16
fi

echo "→ quantizing → $QUANT: $QUANT_GGUF"
"$QUANTIZE_BIN" "$F16_GGUF" "$QUANT_GGUF" "$QUANT"

echo ""
echo "done: $QUANT_GGUF"
echo ""
echo "next: copy to your model dir and add a runner, e.g."
echo "  cp '$QUANT_GGUF' \"\$HOME/programs/qwen/\""
echo "  cat > \"\$HOME/programs/model-runners/run-rellm.sh\" <<EOF"
echo "#!/usr/bin/env bash"
echo "MODEL_DIR=\"\$HOME/programs/qwen\" exec \"\$(dirname \"\$0\")/serve-llama.sh\" \"${OUT_NAME}-${QUANT}.gguf\""
echo "EOF"
echo "  chmod +x \"\$HOME/programs/model-runners/run-rellm.sh\""
