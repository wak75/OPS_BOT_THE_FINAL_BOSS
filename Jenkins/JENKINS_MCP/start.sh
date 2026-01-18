#!/bin/bash
cd "$(dirname "${BASH_SOURCE[0]}")"
source .venv/bin/activate
python -m jenkins_mcp_server.main "$@"
