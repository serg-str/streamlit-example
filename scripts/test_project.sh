#!/bin/bash
set -ex

# Resolving this script directory
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
PROJECT_DIR="${SCRIPT_DIR}/.."
# Running everything from src/ and failing if we can't
cd "${PROJECT_DIR}" || exit 1

rm -rf htmlcov
poetry -C "${PROJECT_DIR}" run coverage run -m pytest tests -vv . -o log_cli=true
poetry -C "${PROJECT_DIR}" run coverage report
poetry -C "${PROJECT_DIR}" run coverage html
