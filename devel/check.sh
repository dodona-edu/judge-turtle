#!/bin/bash
set -euo pipefail

ROOT="$(dirname "$(dirname "$0")")"

cd "$ROOT"

ruff check .
ruff format --check .
mypy turtle_judge.py judge/
