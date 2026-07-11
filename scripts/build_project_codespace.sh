#!/bin/bash
set -ex

# Resolving this script directory
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
PROJECT_DIR="${SCRIPT_DIR}/.."
# Running everything from src/ and failing if we can't
cd "${PROJECT_DIR}" || exit 1

if [[ ! -f .env ]]; then
    cp example.env .env
fi
poetry -C "${PROJECT_DIR}" install --no-root --all-extras
poetry -C "${PROJECT_DIR}" run alembic upgrade head
poetry -C "${PROJECT_DIR}" run python python_example/initial_data.py
