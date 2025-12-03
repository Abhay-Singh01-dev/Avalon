from __future__ import annotations

from typing import Any, Optional

from app.config import settings
from app.core.cache import CacheManager, cache


class ExternalCache:
    """Simple namespaced cache wrapper for external API responses."""

    def __init__(self, prefix: str = "external", default_ttl: Optional[int] = None):
        self.prefix = prefix
        self.default_ttl = default_ttl or settings.EXTERNAL_CACHE_TTL
        self._cache = cache

    def make_key(self, namespace: str, identifier: Any) -> str:
        return CacheManager.make_key(self.prefix, namespace, identifier)

    def get(self, namespace: str, identifier: Any, default: Any = None) -> Any:
        key = self.make_key(namespace, identifier)
        return self._cache.get(key, default)

    def set(self, namespace: str, identifier: Any, value: Any, ttl: Optional[int] = None) -> None:
        key = self.make_key(namespace, identifier)
        self._cache.set(key, value, ttl=ttl or self.default_ttl)


external_cache = ExternalCache()

