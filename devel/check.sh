#!/bin/bash
set -euo pipefail

ROOT="$(dirname "$(dirname "$0")")"

cd "$ROOT"

pytest \
    --pylama \
    --ignore="tests" \
    "$@"
