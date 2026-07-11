#!/bin/bash
set -ex

# Resolving this script directory
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
PROJECT_DIR="${SCRIPT_DIR}/.."

poetry -C "${PROJECT_DIR}" run autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place --exclude=__init__.py python_example tests
poetry -C "${PROJECT_DIR}" run black python_example tests
poetry -C "${PROJECT_DIR}" run isort --recursive --apply python_example tests
