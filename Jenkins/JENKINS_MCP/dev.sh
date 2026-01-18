#!/bin/bash
cd "$(dirname "${BASH_SOURCE[0]}")"
source .venv/bin/activate
export DEBUG=true
export LOG_LEVEL=DEBUG
python -m jenkins_mcp_server.main "$@"
