#!/bin/bash

poetry completions bash >> ~/.bash_completion

poetry config virtualenvs.in-project true
poetry env use python
if [ -f .pre-commit-config.yaml ]; then
	pre-commit install
fi
