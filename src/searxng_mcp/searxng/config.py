import os
from dataclasses import dataclass


@dataclass(frozen=True)
class SearXNGSettings:
    url: str = "http://localhost:8080"
    timeout: float = 10.0
    language: str = "auto"
    safesearch: int = 1  # 0 = off, 1 = moderate, 2 = strict
    username: str | None = None
    password: str | None = None

    @classmethod
    def from_env(cls) -> "SearXNGSettings":
        return cls(
            url=os.getenv("SEARXNG_URL", cls.url).rstrip("/"),
            timeout=float(os.getenv("SEARXNG_TIMEOUT", cls.timeout)),
            language=os.getenv("SEARXNG_LANGUAGE", cls.language),
            safesearch=int(os.getenv("SEARXNG_SAFESEARCH", cls.safesearch)),
            username=os.getenv("SEARXNG_USERNAME") or None,
            password=os.getenv("SEARXNG_PASSWORD") or None,
        )
