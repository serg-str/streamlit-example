#!/bin/bash
set -ex

# Resolving this script directory
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
# Running everything from src/ and failing if we can't
cd "${SCRIPT_DIR}/.." || exit 1

# shellcheck source=/dev/null
source "${SCRIPT_DIR}/test.sh" --cov-report=html "${@}"
