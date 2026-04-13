#!/usr/bin/env bash
set -euo pipefail

# Start llama-server with Gemma 4 31B for local evals.
# Model stays loaded — hit it with run-local-eval.py or test-executor.py.

MODEL="${1:-$HOME/models/gemma-4-31B-it-UD-Q8_K_XL.gguf}"
PORT="${2:-8080}"
CTX="${3:-32768}"
SLOTS="${4:-1}"

if [ ! -f "$MODEL" ]; then
  echo "Model not found: $MODEL"
  echo ""
  echo "Usage: $0 [MODEL_PATH] [PORT] [CTX_SIZE]"
  echo ""
  echo "Available models in ~/models/:"
  ls -1 ~/models/*.gguf 2>/dev/null || echo "  (none)"
  exit 1
fi

echo "=== Starting llama-server ==="
echo "Model: $MODEL"
echo "Port:  $PORT"
echo "Context: $CTX tokens"
echo "Slots: $SLOTS"
echo ""
echo "API: http://localhost:$PORT/v1/chat/completions"
echo "Health: http://localhost:$PORT/health"
echo ""
echo "Usage: $0 [MODEL_PATH] [PORT] [CTX_SIZE] [SLOTS]"
echo ""

exec ~/llama.cpp/build/bin/llama-server \
  -m "$MODEL" \
  --host 0.0.0.0 \
  --port "$PORT" \
  -c "$CTX" \
  -np "$SLOTS" \
  -ngl 99 \
  --flash-attn on \
  --jinja \
  --slots-endpoint
