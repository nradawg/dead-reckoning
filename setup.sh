#!/usr/bin/env bash
# One command setup. Needs Python 3.10 or newer.
set -e
PY=$(command -v python3.12 || command -v python3.11 || command -v python3.10 || command -v python3)
echo "using $PY ($($PY -V))"
$PY -m venv .venv
./.venv/bin/pip install -q --upgrade pip
./.venv/bin/pip install -q -r requirements.txt
[ -f .env ] || cp .env.example .env
echo
echo "Done. Now:"
echo "  1. Fill in .env  (open -e .env)"
echo "  2. ./.venv/bin/python check.py     <- verifies your keys work"
echo "  3. ./.venv/bin/python agents/discover.py   <- find your dead projects"
