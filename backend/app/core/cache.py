"""
Unified caching system with in-memory, file, and Redis backends.
"""
import json
import hashlib
import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union, TypeVar, Callable
from datetime import datetime, timedelta
import pickle
import zlib

# Type variable for generic return types
T = TypeVar('T')

# Configure logging
logger = logging.getLogger(__name__)

class CacheMissError(Exception):
    """Raised when a key is not found in cache."""
    pass

class CacheBackend:
    """Abstract base class for cache backends."""
    
    def get(self, key: str) -> Any:
        """Get a value from the cache."""
        raise NotImplementedError
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in the cache with optional TTL (in seconds)."""
        raise NotImplementedError
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        raise NotImplementedError
    
    def delete(self, key: str) -> None:
        """Delete a key from the cache."""
        raise NotImplementedError

class MemoryCache(CacheBackend):
    """In-memory cache implementation."""
    
    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}
    
    def get(self, key: str) -> Any:
        """Get a value from the in-memory cache."""
        if key not in self._store:
            raise CacheMissError(f"Key not found in memory cache: {key}")
        
        entry = self._store[key]
        if entry['expires'] and entry['expires'] < datetime.utcnow():
            del self._store[key]
            raise CacheMissError(f"Key expired in memory cache: {key}")
            
        return entry['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in the in-memory cache."""
        expires = None
        if ttl is not None:
            expires = datetime.utcnow() + timedelta(seconds=ttl)
            
        self._store[key] = {
            'value': value,
            'expires': expires,
            'created_at': datetime.utcnow()
        }
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in the in-memory cache."""
        try:
            self.get(key)
            return True
        except CacheMissError:
            return False
    
    def delete(self, key: str) -> None:
        """Delete a key from the in-memory cache."""
        self._store.pop(key, None)

class FileSystemCache(CacheBackend):
    """Filesystem-based cache implementation."""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_path(self, key: str) -> Path:
        """Get the filesystem path for a cache key."""
        # Use first 2 chars as directory, rest as filename
        key_dir = self.cache_dir / key[:2]
        key_dir.mkdir(exist_ok=True)
        return key_dir / f"{key}.json"
    
    def get(self, key: str) -> Any:
        """Get a value from the filesystem cache."""
        cache_file = self._get_cache_path(key)
        
        if not cache_file.exists():
            raise CacheMissError(f"Cache file not found: {cache_file}")
            
        try:
            with open(cache_file, 'rb') as f:
                # Read compressed data
                compressed_data = f.read()
                # Decompress
                json_data = zlib.decompress(compressed_data).decode('utf-8')
                entry = json.loads(json_data)
                
            # Check expiration
            if entry.get('expires') and datetime.fromisoformat(entry['expires']) < datetime.utcnow():
                cache_file.unlink()
                raise CacheMissError(f"Cache entry expired: {key}")
                
            return entry['value']
            
        except (json.JSONDecodeError, zlib.error, KeyError) as e:
            # If corrupted, delete the file
            if cache_file.exists():
                cache_file.unlink()
            raise CacheMissError(f"Invalid cache entry: {e}")
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in the filesystem cache."""
        cache_file = self._get_cache_path(key)
        
        expires = None
        if ttl is not None:
            expires = (datetime.utcnow() + timedelta(seconds=ttl)).isoformat()
        
        entry = {
            'value': value,
            'expires': expires,
            'created_at': datetime.utcnow().isoformat(),
            'key': key
        }
        
        try:
            # Create parent directory if it doesn't exist
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Serialize and compress
            json_data = json.dumps(entry, default=str).encode('utf-8')
            compressed_data = zlib.compress(json_data)
            
            # Write to temp file first, then rename (atomic operation)
            temp_file = cache_file.with_suffix('.tmp')
            with open(temp_file, 'wb') as f:
                f.write(compressed_data)
            
            # On Windows, we need to remove the destination file first if it exists
            if cache_file.exists():
                cache_file.unlink()
            
            temp_file.rename(cache_file)
            
        except Exception as e:
            logger.error(f"Failed to write to cache file {cache_file}: {e}")
            if temp_file.exists():
                temp_file.unlink()
            raise
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in the filesystem cache."""
        try:
            self.get(key)
            return True
        except CacheMissError:
            return False
    
    def delete(self, key: str) -> None:
        """Delete a key from the filesystem cache."""
        cache_file = self._get_cache_path(key)
        try:
            if cache_file.exists():
                cache_file.unlink()
        except Exception as e:
            logger.error(f"Failed to delete cache file {cache_file}: {e}")

class RedisCache(CacheBackend):
    """Redis-based cache implementation."""
    
    def __init__(self, redis_client=None, **kwargs):
        self.redis = redis_client
        self.initialized = redis_client is not None
    
    def _ensure_redis(self):
        """Lazy import and initialize Redis if not already done."""
        if not self.initialized:
            try:
                import redis
                self.redis = redis.Redis(**kwargs)
                # Test connection
                self.redis.ping()
                self.initialized = True
                logger.info("Redis cache initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Redis cache: {e}")
                raise ImportError("Redis is not available") from e
    
    def get(self, key: str) -> Any:
        """Get a value from Redis cache."""
        try:
            self._ensure_redis()
            data = self.redis.get(key)
            if data is None:
                raise CacheMissError(f"Key not found in Redis: {key}")
            return pickle.loads(data)
        except Exception as e:
            logger.warning(f"Redis get failed: {e}")
            raise CacheMissError(f"Redis error: {e}")
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in Redis cache."""
        try:
            self._ensure_redis()
            serialized = pickle.dumps(value)
            if ttl is not None:
                self.redis.setex(key, ttl, serialized)
            else:
                self.redis.set(key, serialized)
        except Exception as e:
            logger.warning(f"Redis set failed: {e}")
            # Fail silently - we'll fall back to other backends
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in Redis."""
        try:
            self._ensure_redis()
            return self.redis.exists(key) == 1
        except Exception:
            return False
    
    def delete(self, key: str) -> None:
        """Delete a key from Redis."""
        try:
            self._ensure_redis()
            self.redis.delete(key)
        except Exception as e:
            logger.warning(f"Redis delete failed: {e}")

class CacheManager:
    """Unified cache manager with multi-level fallback."""
    
    def __init__(self, use_redis: bool = False, redis_kwargs: Optional[dict] = None):
        self.memory = MemoryCache()
        self.filesystem = FileSystemCache()
        self.redis = None
        
        if use_redis:
            try:
                self.redis = RedisCache(**(redis_kwargs or {}))
            except ImportError:
                logger.warning("Redis not available, falling back to memory/filesystem cache")
    
    @staticmethod
    def make_key(*args, **kwargs) -> str:
        """
        Generate a deterministic cache key from input data.
        
        Args:
            *args: Positional arguments to include in the key
            **kwargs: Keyword arguments to include in the key
            
        Returns:
            str: A SHA-256 hash of the input data
        """
        # Convert all inputs to a string and sort keys for deterministic ordering
        def _serialize(obj):
            if isinstance(obj, (str, int, float, bool)) or obj is None:
                return str(obj)
            elif isinstance(obj, (list, tuple)):
                return [_serialize(x) for x in obj]
            elif isinstance(obj, dict):
                return {k: _serialize(v) for k, v in sorted(obj.items())}
            else:
                return str(obj)
        
        # Create a stable string representation
        key_data = {
            'args': _serialize(args),
            'kwargs': _serialize(kwargs)
        }
        
        # Convert to JSON and hash
        key_str = json.dumps(key_data, sort_keys=True).encode('utf-8')
        return hashlib.sha256(key_str).hexdigest()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the cache, trying each backend in order.
        
        Args:
            key: The cache key
            default: Default value to return if key is not found
            
        Returns:
            The cached value or default if not found
        """
        # Try memory cache first
        try:
            value = self.memory.get(key)
            logger.debug(f"Cache hit (memory): {key}")
            return value
        except CacheMissError:
            pass
        
        # Try Redis if available
        if self.redis:
            try:
                value = self.redis.get(key)
                # Cache the value in memory for faster access
                if value is not None:
                    self.memory.set(key, value)
                    logger.debug(f"Cache hit (Redis): {key}")
                    return value
            except Exception as e:
                logger.warning(f"Redis get failed: {e}")
        
        # Try filesystem cache
        try:
            value = self.filesystem.get(key)
            # Cache the value in memory for faster access
            if value is not None:
                self.memory.set(key, value)
                logger.debug(f"Cache hit (filesystem): {key}")
                return value
        except CacheMissError:
            pass
        
        logger.debug(f"Cache miss: {key}")
        return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in the cache across all available backends.
        
        Args:
            key: The cache key
            value: The value to cache (must be JSON-serializable)
            ttl: Time to live in seconds (optional)
        """
        try:
            # Always set in memory
            self.memory.set(key, value, ttl)
            
            # Set in Redis if available
            if self.redis:
                try:
                    self.redis.set(key, value, ttl)
                except Exception as e:
                    logger.warning(f"Failed to set in Redis: {e}")
            
            # Set in filesystem (with longer TTL if specified)
            fs_ttl = ttl * 2 if ttl else None  # Filesystem cache lasts longer
            self.filesystem.set(key, value, fs_ttl)
            
            logger.debug(f"Cache set: {key} (ttl: {ttl}s)")
            
        except Exception as e:
            logger.error(f"Failed to set cache value: {e}", exc_info=True)
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in any cache backend."""
        return (
            self.memory.exists(key) or
            (self.redis and self.redis.exists(key)) or
            self.filesystem.exists(key)
        )
    
    def delete(self, key: str) -> None:
        """Delete a key from all cache backends."""
        self.memory.delete(key)
        if self.redis:
            try:
                self.redis.delete(key)
            except Exception as e:
                logger.warning(f"Failed to delete from Redis: {e}")
        self.filesystem.delete(key)
        logger.debug(f"Cache deleted: {key}")
    
    def clear(self) -> None:
        """Clear all caches."""
        self.memory = MemoryCache()  # Reset memory cache
        if self.redis:
            try:
                self.redis.redis.flushdb()
            except Exception as e:
                logger.warning(f"Failed to clear Redis: {e}")
        # Note: We don't clear the filesystem cache here as it might be shared
        logger.info("Caches cleared")

# Global cache instance
cache = CacheManager(use_redis=False)  # Set use_redis=True to enable Redis

def cached(ttl: int = 3600, key_func: Optional[Callable[..., str]] = None):
    """
    Decorator to cache function results.
    
    Args:
        ttl: Time to live in seconds
        key_func: Optional function to generate cache key from function arguments
    """
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = (
                key_func(*args, **kwargs) 
                if key_func 
                else CacheManager.make_key(func.__name__, *args, **kwargs)
            )
            
            # Try to get from cache
            try:
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Using cached result for {func.__name__} (key: {cache_key[:8]}...)")
                    return cached_result
            except Exception as e:
                logger.warning(f"Cache lookup failed for {func.__name__}: {e}")
            
            # Call the function if not in cache
            result = await func(*args, **kwargs)
            
            # Cache the result
            try:
                cache.set(cache_key, result, ttl=ttl)
            except Exception as e:
                logger.warning(f"Failed to cache result for {func.__name__}: {e}")
            
            return result
        
        return async_wrapper
    
    return decorator
