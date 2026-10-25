# List available recipes
default:
    @just --list

# Install dependencies and build the Docker image
build:
    uv sync
    uv build
    docker compose build

# Remove build artifacts and caches (keeps .venv)
clean:
    rm -rf dist build .ruff_cache .pytest_cache
    find . -type d -name __pycache__ -not -path './.venv/*' -exec rm -rf {} +

# Install (using uv tool install)
install: clean build
  uv tool install --reinstall dist/searxng_mcp-*.whl

# Run the server locally (stdio or http)
serve transport="stdio":
    MCP_TRANSPORT={{transport}} uv run searxng-mcp

# Run the server in Docker via compose
serve-docker:
    docker compose up --build

# Uninstall (using uv tool uninstall)
uninstall:
  uv tool uninstall searxng-mcp
