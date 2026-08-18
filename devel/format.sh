#!/bin/bash
set -euo pipefail

ROOT="$(dirname "$(dirname "$0")")"

cd "$ROOT"

isort ./*.py
isort ./**/*.py
black ./*.py --line-length=120
black ./**/*.py --line-length=120
