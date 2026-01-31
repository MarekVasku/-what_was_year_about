"""
Caching with Time-To-Live (TTL) support.
Replaces @lru_cache with granular control over cache expiration.
"""

from datetime import datetime, timedelta
from typing import TypeVar, Generic, Callable, Any, Dict, Tuple
import pandas as pd

T = TypeVar("T")


class CachedDataLoader(Generic[T]):
    """
    Generic cache with TTL support for expensive data operations.
    
    Features:
    - Time-based expiration
    - Configurable cache size
    - Cache statistics
    - Manual invalidation
    """
    
    def __init__(self, ttl_seconds: int = 3600, max_size: int = 10):
        """
        Initialize cache.
        
        Args:
            ttl_seconds: Time-to-live for cached items in seconds (default 1 hour)
            max_size: Maximum number of cached items (default 10)
        """
        self.ttl = timedelta(seconds=ttl_seconds)
        self.max_size = max_size
        self.cache: Dict[Tuple, Tuple[T, datetime]] = {}
        self.hits = 0
        self.misses = 0
    
    def get(self, key: Tuple, loader_fn: Callable[..., T]) -> T:
        """
        Get cached value or compute and cache it.
        
        Args:
            key: Cache key (typically tuple of function arguments)
            loader_fn: Callable that computes the value if not cached
            
        Returns:
            Cached or freshly computed value
        """
        # Check if key exists and hasn't expired
        if key in self.cache:
            data, timestamp = self.cache[key]
            if datetime.now() - timestamp < self.ttl:
                self.hits += 1
                return data
            else:
                # Expired, remove it
                del self.cache[key]
        
        # Miss: compute fresh data
        self.misses += 1
        data = loader_fn()
        
        # Enforce max size (FIFO)
        if len(self.cache) >= self.max_size:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        self.cache[key] = (data, datetime.now())
        return data
    
    def clear(self):
        """Clear all cached items."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def invalidate(self, key: Tuple = None):
        """
        Invalidate specific cache entry or all entries.
        
        Args:
            key: Cache key to invalidate. If None, clears entire cache.
        """
        if key is None:
            self.clear()
        elif key in self.cache:
            del self.cache[key]
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "size": len(self.cache),
            "max_size": self.max_size,
        }


# Convenience function for decorator-style usage
def cached_operation(cache_instance: CachedDataLoader, *args, **kwargs):
    """
    Decorator-style caching for expensive operations.
    
    Usage:
        data_cache = CachedDataLoader(ttl_seconds=3600)
        
        @cached_operation(data_cache)
        def expensive_computation(param1, param2):
            return result
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Create cache key from function arguments
            cache_key = (func.__name__, args, tuple(sorted(kwargs.items())))
            return cache_instance.get(cache_key, lambda: func(*args, **kwargs))
        return wrapper
    return decorator
