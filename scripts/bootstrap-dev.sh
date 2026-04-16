#!/usr/bin/env bash
# One-shot dev environment setup: venv → install deps → install pre-commit → smoke-test.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_DIR}"

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV="${REPO_DIR}/.venv"

echo "→ Creating venv at ${VENV}"
"${PYTHON_BIN}" -m venv "${VENV}"

# shellcheck disable=SC1091
source "${VENV}/bin/activate"

echo "→ Upgrading pip"
python -m pip install --upgrade pip

echo "→ Installing project + dev deps"
pip install -e ".[dev]"

echo "→ Installing pre-commit hooks"
pre-commit install

echo "→ Running checks"
ruff check .
ruff format --check .
mypy src
pytest -q

echo
echo "✓ Dev environment ready. Activate with:  source .venv/bin/activate"
