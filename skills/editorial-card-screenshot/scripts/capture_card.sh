#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd "$(dirname "$0")" && pwd)"
exec "${PYTHON_BIN:-python3}" "$script_dir/capture_card.py" "$@"
