#!/usr/bin/env bash
# Call the search tool on the MCP server over HTTP.
#
# Usage: ./clients/search.sh <query> [max_results]
#   Server URL comes from $MCP_URL, defaulting to http://127.0.0.1:8000/mcp
#
# Start the server first: MCP_TRANSPORT=http uv run searxng-mcp
set -euo pipefail
source "$(dirname "$0")/lib.sh"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <query> [max_results]" >&2
  exit 1
fi
if ! command -v jq >/dev/null; then
  echo "This script needs jq: https://jqlang.org" >&2
  exit 1
fi

request="$(jq -n --arg query "$1" --argjson max "${2:-5}" '{
  jsonrpc: "2.0", id: 2, method: "tools/call",
  params: {name: "search", arguments: {query: $query, max_results: $max}}
}')"

mcp_init "${MCP_URL:-http://127.0.0.1:8000/mcp}"
response="$(mcp_request "$request")"

if [[ "$(echo "$response" | jq '.result.isError // false')" == "true" ]]; then
  echo "$response" | jq -r '.result.content[0].text' >&2
  exit 1
fi
echo "$response" | jq '.result.structuredContent // .result // .error'
