#!/bin/bash
set -ex

# Resolving this script directory
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
PROJECT_DIR="${SCRIPT_DIR}/.."

poetry -C "${PROJECT_DIR}" run python -m python_example.main
