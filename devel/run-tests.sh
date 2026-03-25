#!/bin/bash

ROOT="$(dirname "$(dirname "$0")")"

cd "$ROOT" || exit

# On macOS, ensure Homebrew libraries (e.g. cairo) are discoverable
if [ "$(uname)" = "Darwin" ] && command -v brew > /dev/null 2>&1; then
    export DYLD_FALLBACK_LIBRARY_PATH="$(brew --prefix)/lib:${DYLD_FALLBACK_LIBRARY_PATH:-}"
fi

git submodule update --init

pytest -n auto \
    --cov \
    --cov-branch \
    --cov-report xml \
    --cov-report html \
    "tests/" \
    "$@"
