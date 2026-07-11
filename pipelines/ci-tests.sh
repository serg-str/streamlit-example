#!/bin/bash
set -e

# Resolving this script directory
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
PROJECT_DIR="$(realpath "${SCRIPT_DIR}/..")"
# Running everything from src/ and failing if we can't
cd "${PROJECT_DIR}" || exit 1
# Fixing the PATH
export PATH="${PATH}:${HOME}/.local/bin"

pip install poetry

set -o allexport
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/ci.env"
set +o allexport
export PYTHONPATH="${PROJECT_DIR}"

poetry config virtualenvs.in-project true
poetry install --no-root --all-extras
poetry run alembic upgrade head
poetry run python python_example/initial_data.py
poetry run pytest \
    --junitxml=test-reports/junit.xml \
    --cov-report=xml:test-reports/coverage/cobertura-coverage.xml \
    --cov-report=term-missing \
    --cov=python_example \
    tests
