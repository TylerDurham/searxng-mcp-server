# searxng-mcp-server
A simple MCP Server for the SearXNG hosted search service.

## Setup

```sh
uv sync
cp .env.example .env
```

## Run

```sh
# Local (STDIO)
uv run searxng-mcp

# Remote (HTTP) — serves at http://127.0.0.1:8000/mcp
MCP_TRANSPORT=http uv run searxng-mcp
```

Settings are read from `.env` (see `.env.example`). Real environment variables take precedence.

Only `.env` is loaded — `.env.example` is just a template. Set `SEARXNG_URL` to your SearXNG instance, which must have the JSON format enabled in its `settings.yml`:

```yaml
search:
  formats: [html, json]
```

## Clients

The `clients/` directory has bash scripts for talking to the server over HTTP. They require `curl` and `jq`, and the server must be running in HTTP mode:

```sh
MCP_TRANSPORT=http uv run searxng-mcp
```

The scripts connect to `http://127.0.0.1:8000/mcp` by default. Set `MCP_URL` to point them at another server.

### List tools

```sh
./clients/list-tools.sh
./clients/list-tools.sh http://myhost:8000/mcp   # or pass the URL directly
```

Prints each tool's name, description, and input schema.

### Search

```sh
./clients/search.sh "fastmcp python"       # 5 results by default
./clients/search.sh "fastmcp python" 10    # choose how many
MCP_URL=http://myhost:8000/mcp ./clients/search.sh "fastmcp python"
```

Prints the results as JSON. If the search fails (for example, SearXNG is unreachable), the error goes to stderr and the script exits with status 1.

## Docker

The image runs the server in HTTP mode on port 8000:

```sh
docker build -t searxng-mcp .
docker run -d -p 8000:8000 --env-file .env searxng-mcp
```

Pass settings with `--env-file` or `-e` (for example, `-e SEARXNG_URL=https://searx.example.com`). `.env` is excluded from the image, so settings are never baked in.

The HTTP endpoint has no authentication. Don't expose it publicly without a protected reverse proxy in front of it.
