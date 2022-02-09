#!/bin/bash

ROOT="$(dirname $(dirname $0))"

isort *.py
isort **/*.py
black *.py --line-length=120
black **/*.py --line-length=120
