# Shared helpers for the MCP client scripts. Source this file, don't run it.
#
# Provides:
#   mcp_init <url>        Open a session (sets MCP_SESSION_ID)
#   mcp_request <json>    Send a JSON-RPC request and print the JSON response

MCP_HEADERS=(-H "Content-Type: application/json" -H "Accept: application/json, text/event-stream")

mcp_init() {
  MCP_ENDPOINT="$1"
  local header_file
  header_file="$(mktemp)"

  curl -sS -D "$header_file" -o /dev/null "${MCP_HEADERS[@]}" -X POST "$MCP_ENDPOINT" -d '{
    "jsonrpc": "2.0", "id": 1, "method": "initialize",
    "params": {
      "protocolVersion": "2025-06-18",
      "capabilities": {},
      "clientInfo": {"name": "searxng-mcp-clients", "version": "0.1.0"}
    }
  }' || { rm -f "$header_file"; return 1; }

  MCP_SESSION_ID="$(grep -i '^mcp-session-id:' "$header_file" | cut -d' ' -f2 | tr -d '\r')"
  rm -f "$header_file"
  if [[ -z "$MCP_SESSION_ID" ]]; then
    echo "No mcp-session-id returned by $MCP_ENDPOINT. Is the server running in HTTP mode?" >&2
    return 1
  fi
  MCP_HEADERS+=(-H "mcp-session-id: $MCP_SESSION_ID")

  curl -sS -o /dev/null "${MCP_HEADERS[@]}" -X POST "$MCP_ENDPOINT" \
    -d '{"jsonrpc": "2.0", "method": "notifications/initialized"}'
}

# Responses may come back as SSE ("data: {...}"), so strip that prefix.
mcp_request() {
  curl -sS "${MCP_HEADERS[@]}" -X POST "$MCP_ENDPOINT" -d "$1" | sed -n 's/^data: //p'
}
