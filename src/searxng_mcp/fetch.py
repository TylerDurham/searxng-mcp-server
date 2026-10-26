import asyncio
import ipaddress
import os
import socket
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
import trafilatura

USER_AGENT = "searxng-mcp/0.1 (+https://github.com/TylerDurham/searxng-mcp-server)"
MAX_REDIRECTS = 5
TEXT_TYPES = ("text/plain", "text/markdown", "application/json")
HTML_TYPES = ("text/html", "application/xhtml+xml")


class FetchError(Exception):
    """Raised when a page can't be fetched or isn't allowed."""


@dataclass(frozen=True)
class FetchSettings:
    timeout: float = 15.0
    max_bytes: int = 5_000_000
    allow_private: bool = False

    @classmethod
    def from_env(cls) -> "FetchSettings":
        return cls(
            timeout=float(os.getenv("FETCH_TIMEOUT", cls.timeout)),
            max_bytes=int(os.getenv("FETCH_MAX_BYTES", cls.max_bytes)),
            allow_private=os.getenv("FETCH_ALLOW_PRIVATE", "false").lower() == "true",
        )


async def _check_url(url: str, allow_private: bool) -> None:
    """Reject non-HTTP URLs and, unless allowed, hosts that resolve to non-public IPs."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise FetchError(f"Only http and https URLs are allowed: {url}")
    if allow_private:
        return

    try:
        infos = await asyncio.get_running_loop().getaddrinfo(
            parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80),
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror as e:
        raise FetchError(f"Could not resolve {parsed.hostname}: {e}") from e

    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
            ip = ip.ipv4_mapped
        if not ip.is_global:
            raise FetchError(
                f"{parsed.hostname} resolves to a non-public address ({ip}). "
                "Set FETCH_ALLOW_PRIVATE=true to allow this."
            )


async def _download(
    client: httpx.AsyncClient, url: str, settings: FetchSettings
) -> tuple[str, str, bytes]:
    """Follow redirects manually so every hop is checked. Returns (final_url, content_type, body)."""
    for _ in range(MAX_REDIRECTS + 1):
        await _check_url(url, settings.allow_private)
        async with client.stream("GET", url) as response:
            if response.is_redirect:
                url = urljoin(url, response.headers["location"])
                continue
            if response.is_error:
                raise FetchError(f"{url} returned HTTP {response.status_code}")

            content_type = response.headers.get("content-type", "").split(";")[0].strip()
            body = bytearray()
            async for chunk in response.aiter_bytes():
                body.extend(chunk)
                if len(body) > settings.max_bytes:
                    raise FetchError(f"{url} is larger than {settings.max_bytes} bytes")
            return url, content_type, bytes(body)

    raise FetchError(f"Too many redirects (more than {MAX_REDIRECTS})")


def _extract(body: bytes, content_type: str, url: str) -> tuple[str | None, str]:
    """Turn a response body into (title, readable text)."""
    if content_type in TEXT_TYPES:
        return None, body.decode("utf-8", errors="replace")
    if content_type not in HTML_TYPES:
        raise FetchError(f"Unsupported content type: {content_type or 'unknown'}")

    content = trafilatura.extract(
        body, url=url, output_format="markdown", include_links=True, include_tables=True
    )
    if not content:
        raise FetchError(f"Could not extract readable content from {url}")
    metadata = trafilatura.extract_metadata(body)
    return (metadata.title if metadata else None), content


async def fetch_page(
    url: str, max_length: int, settings: FetchSettings | None = None
) -> dict[str, Any]:
    settings = settings or FetchSettings.from_env()
    try:
        async with httpx.AsyncClient(
            timeout=settings.timeout, headers={"User-Agent": USER_AGENT}
        ) as client:
            final_url, content_type, body = await _download(client, url, settings)
    except httpx.HTTPError as e:
        raise FetchError(f"Request to {url} failed: {e}") from e

    title, content = await asyncio.to_thread(_extract, body, content_type, final_url)
    return {
        "url": final_url,
        "title": title,
        "content": content[:max_length],
        "truncated": len(content) > max_length,
    }
