#!/bin/bash
set -ex

# Resolving this script directory
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
PROJECT_DIR="${SCRIPT_DIR}/.."

poetry -C "${PROJECT_DIR}" run mypy python_example tests
poetry -C "${PROJECT_DIR}" run black --check python_example tests
poetry -C "${PROJECT_DIR}" run isort --recursive --check-only python_example tests
poetry -C "${PROJECT_DIR}" run flake8
