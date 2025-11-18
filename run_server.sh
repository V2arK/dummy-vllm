#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${PYTHONPATH:+${PYTHONPATH}:}${SCRIPT_DIR}"

python -m uvicorn src.main:app \
  --host "${DUMMY_VLLM_HOST:-0.0.0.0}" \
  --port "${DUMMY_VLLM_PORT:-8000}" \
  --log-level "${DUMMY_VLLM_LOG_LEVEL:-info}" \
  --reload

