#!/usr/bin/env bash
# Call the fetch tool on the MCP server over HTTP.
#
# Usage: ./clients/fetch.sh <url> [max_length]
#   Server URL comes from $MCP_URL, defaulting to http://127.0.0.1:8000/mcp
#
# Prints the page content (Markdown) to stdout and the title/URL to stderr,
# so `./clients/fetch.sh <url> > page.md` saves just the content.
#
# Start the server first: MCP_TRANSPORT=http uv run searxng-mcp
set -euo pipefail
source "$(dirname "$0")/lib.sh"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <url> [max_length]" >&2
  exit 1
fi
if ! command -v jq >/dev/null; then
  echo "This script needs jq: https://jqlang.org" >&2
  exit 1
fi

request="$(jq -n --arg url "$1" --argjson max "${2:-20000}" '{
  jsonrpc: "2.0", id: 2, method: "tools/call",
  params: {name: "fetch", arguments: {url: $url, max_length: $max}}
}')"

mcp_init "${MCP_URL:-http://127.0.0.1:8000/mcp}"
response="$(mcp_request "$request")"

if [[ "$(echo "$response" | jq '.result.isError // false')" == "true" ]]; then
  echo "$response" | jq -r '.result.content[0].text' >&2
  exit 1
fi
if [[ "$(echo "$response" | jq 'has("error")')" == "true" ]]; then
  echo "$response" | jq -r '.error.message' >&2
  exit 1
fi

result="$(echo "$response" | jq '.result.structuredContent')"
echo "$result" | jq -r '"\(.title // "(no title)")\n\(.url)\(if .truncated then "  [truncated]" else "" end)\n"' >&2
echo "$result" | jq -r '.content'
