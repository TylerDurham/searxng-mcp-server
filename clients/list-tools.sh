#!/usr/bin/env bash
# List the tools exposed by the MCP server over HTTP.
#
# Usage: ./clients/list-tools.sh [url]
#   url defaults to $MCP_URL, then http://127.0.0.1:8000/mcp
#
# Start the server first: MCP_TRANSPORT=http uv run searxng-mcp
set -euo pipefail
source "$(dirname "$0")/lib.sh"

mcp_init "${1:-${MCP_URL:-http://127.0.0.1:8000/mcp}}"
response="$(mcp_request '{"jsonrpc": "2.0", "id": 2, "method": "tools/list"}')"

if command -v jq >/dev/null; then
  echo "$response" | jq '.result.tools'
else
  echo "$response"
fi
