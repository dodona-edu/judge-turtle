#!/bin/bash
set -euo pipefail

ROOT="$(dirname "$(dirname "$0")")"

cd "$ROOT"

# On macOS, ensure Homebrew libraries (e.g. cairo) are discoverable
if [ "$(uname)" = "Darwin" ] && command -v brew > /dev/null 2>&1; then
    export DYLD_FALLBACK_LIBRARY_PATH="$(brew --prefix)/lib:${DYLD_FALLBACK_LIBRARY_PATH:-}"
fi

LEARN_OUTPUT="YES" pytest tests/test_e2e.py -v -s
