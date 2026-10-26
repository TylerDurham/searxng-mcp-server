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

## Use with Claude Code

Install the `searxng-mcp` command, then register it with Claude Code:

```sh
just install    # or: uv build && uv tool install --reinstall dist/searxng_mcp-*.whl

claude mcp add SearXNG -s user -e SEARXNG_URL=https://searx.example.com -- searxng-mcp
```

`-s user` makes it available in every project; leave it off to add it to the current project only. Start a new Claude Code session to load the tools, which appear as `mcp__SearXNG__search` and `mcp__SearXNG__fetch`.

The installed command doesn't read this repo's `.env`, so pass settings with `-e`. Add one `-e` per setting, for example `-e SEARXNG_SAFESEARCH=0`. Without `SEARXNG_URL`, searches fail with `Request to SearXNG at http://localhost:8080 failed`.

To run from a checkout instead of installing (using its `.env`):

```sh
claude mcp add SearXNG -- uv run --directory /path/to/searxng-mcp-server searxng-mcp
```

Check the server with `claude mcp get SearXNG`, and remove it with `claude mcp remove SearXNG -s user`.

## Tools

### `search`

Searches the web through your SearXNG instance. Takes a `query` plus optional `max_results` (default 10), `categories`, `language`, `time_range` (`day`, `month`, or `year`), and `page`. Returns each result's title, URL, snippet, and engine, along with any answers and suggestions.

### `fetch`

Fetches a web page and returns its main content as Markdown, with menus, footers, and ads stripped out. Takes a `url` and an optional `max_length` (default 20000 characters). Returns the final URL after redirects, the page title, the content, and whether it was truncated. Plain-text and JSON responses are returned as-is; other content types, such as images, are rejected.

Settings:

| Variable | Default | Purpose |
|---|---|---|
| `FETCH_TIMEOUT` | `15` | Request timeout, in seconds |
| `FETCH_MAX_BYTES` | `5000000` | Largest download allowed |
| `FETCH_ALLOW_PRIVATE` | `false` | Allow `localhost` and private network addresses |

By default, `fetch` refuses URLs that resolve to `localhost`, private network, or link-local addresses, and checks every redirect. This stops anyone who can reach the server from using it to probe your internal network. Only set `FETCH_ALLOW_PRIVATE=true` when running over STDIO or on a trusted network. The check doesn't defend against DNS rebinding, so it's not a substitute for authentication on a public endpoint.

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

### Fetch

```sh
./clients/fetch.sh https://example.com            # up to 20000 characters
./clients/fetch.sh https://example.com 5000       # choose the limit
./clients/fetch.sh https://example.com > page.md  # save just the content
```

Prints the page content as Markdown to stdout, and the title and final URL to stderr, so redirecting stdout saves only the content. Errors (for example, a blocked private address) go to stderr and the script exits with status 1.

## Docker

The simplest way is Docker Compose, which reads settings from `.env` and serves HTTP on `127.0.0.1:8000`:

```sh
docker compose up -d --build
```

Compose always runs the container in HTTP mode, even if your `.env` sets `MCP_TRANSPORT=stdio` for local use.

To run the image without Compose, pass your settings and override the transport settings yourself:

```sh
docker build -t searxng-mcp .
docker run -d -p 127.0.0.1:8000:8000 --env-file .env \
  -e MCP_TRANSPORT=http -e MCP_HOST=0.0.0.0 -e MCP_PORT=8000 searxng-mcp
```

`.env` is excluded from the image, so settings are never baked in.

The HTTP endpoint has no authentication, which is why the port is bound to localhost. Don't expose it publicly without a protected reverse proxy in front of it.
