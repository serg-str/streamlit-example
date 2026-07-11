#!/bin/bash
set -ex

# Resolving this script directory
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
PROJECT_DIR="${SCRIPT_DIR}/.."

# Sort imports one per line, so autoflake can remove unused imports
poetry -C "${PROJECT_DIR}" run isort --recursive  --force-single-line-imports --apply python_example tests

# shellcheck source=/dev/null
source "${SCRIPT_DIR}/format.sh"
