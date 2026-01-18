#!/bin/bash
cd "$(dirname "${BASH_SOURCE[0]}")"
source .venv/bin/activate
python tests/run_tests.py "$@"
