import logging
import redis
from langchain.globals import set_llm_cache
from langchain_community.cache import RedisCache
from ..core.config import settings

logger = logging.getLogger(__name__)

class RedisCacheService:
    """Redis cache service for LangChain LLM responses."""
    
    def __init__(self):
        self._redis_client = None
        self._cache_initialized = False
    
    def initialize_llm_cache(self):
        """Initialize Redis cache for LangChain LLM responses."""
        if self._cache_initialized:
            return
        
        try:
            # Create Redis client for LLM caching - use default DB (0)
            self._redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                username=settings.REDIS_USERNAME,
                password=settings.REDIS_PASSWORD,
                # Remove db parameter to use default DB (0)
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                max_connections=10
            )
            
            # Test connection
            self._redis_client.ping()

            redis_cache = RedisCache(self._redis_client, ttl=43000)
            set_llm_cache(redis_cache)
            
            self._cache_initialized = True
            logger.info(f"LangChain Redis cache initialized on {settings.REDIS_HOST}:{settings.REDIS_PORT}")
            
        except Exception as e:
            logger.warning(f"Failed to initialize LLM cache: {e}")
            self._cache_initialized = False
    
    def clear_llm_cache(self):
        """Clear all LLM cache entries."""
        if not self._redis_client:
            return False
        
        try:
            # Clear all keys in the LLM cache database
            self._redis_client.flushdb()
            logger.info("LLM cache cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing LLM cache: {e}")
            return False
    
    def get_cache_stats(self) -> dict:
        """Get LLM cache statistics."""
        if not self._redis_client:
            return {"status": "disabled"}
        
        try:
            info = self._redis_client.info()
            return {
                "status": "enabled",
                "keys": self._redis_client.dbsize(),
                "memory_used": info.get("used_memory_human", "0B"),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0)
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"status": "error", "error": str(e)}

# Global Redis cache service
redis_cache_service = RedisCacheService()
