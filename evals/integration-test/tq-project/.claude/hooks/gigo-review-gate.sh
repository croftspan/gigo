#!/usr/bin/env bash
set -euo pipefail

SPEC="docs/gigo/specs/2026-03-27-tq-add-list-design.md"

echo "=== Stage 1: Go quality gate ==="
go vet ./...
go test ./...

echo "=== Stage 2: Two-stage review (spec compliance + engineering quality) ==="
claude -p "Run gigo:review on the most recent changes. Two stages: spec compliance first, then engineering quality. Spec: $SPEC"
