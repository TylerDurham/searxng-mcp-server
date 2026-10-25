from typing import Any

import httpx

from .config import SearXNGSettings


class SearXNGError(Exception):
    """Raised when the SearXNG instance returns an error or unusable response."""


class SearXNGClient:
    """Minimal async client for the SearXNG search API.

    The instance must have the JSON format enabled in settings.yml:

        search:
          formats: [html, json]
    """

    def __init__(self, settings: SearXNGSettings | None = None) -> None:
        self.settings = settings or SearXNGSettings.from_env()
        auth = None
        if self.settings.username and self.settings.password:
            auth = httpx.BasicAuth(self.settings.username, self.settings.password)
        self._http = httpx.AsyncClient(
            base_url=self.settings.url,
            timeout=self.settings.timeout,
            auth=auth,
        )

    async def search(
        self,
        query: str,
        *,
        categories: str | None = None,
        engines: str | None = None,
        language: str | None = None,
        page: int = 1,
        time_range: str | None = None,
        safesearch: int | None = None,
    ) -> dict[str, Any]:
        """Run a search and return the raw SearXNG JSON response."""
        params: dict[str, Any] = {
            "q": query,
            "format": "json",
            "pageno": page,
            "language": language or self.settings.language,
            "safesearch": self.settings.safesearch if safesearch is None else safesearch,
        }
        if categories:
            params["categories"] = categories
        if engines:
            params["engines"] = engines
        if time_range:
            params["time_range"] = time_range  # day, month, or year

        try:
            response = await self._http.get("/search", params=params)
        except httpx.HTTPError as e:
            raise SearXNGError(
                f"Request to SearXNG at {self.settings.url} failed: {e}"
            ) from e

        if response.status_code == 403:
            raise SearXNGError(
                "SearXNG returned 403. Is the JSON format enabled in settings.yml?"
            )
        if response.is_error:
            raise SearXNGError(f"SearXNG returned HTTP {response.status_code}")

        try:
            return response.json()
        except ValueError as e:
            raise SearXNGError("SearXNG returned a non-JSON response") from e

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> "SearXNGClient":
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()
