#!/usr/bin/env bash
# Thin shell wrapper around build_ticket.py.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/build_ticket.py" "$@"
