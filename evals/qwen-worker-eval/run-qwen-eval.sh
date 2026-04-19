#!/usr/bin/env bash
# Thin shell wrapper around run_qwen_eval.py.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/run_qwen_eval.py" "$@"
