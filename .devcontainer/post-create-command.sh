#!/bin/bash

poetry completions bash >> ~/.bash_completion

poetry config virtualenvs.in-project true
poetry env use python
pre-commit install
