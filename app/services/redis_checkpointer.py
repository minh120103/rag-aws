import logging
from typing import Optional
from langgraph.checkpoint.redis import RedisSaver
from ..core.config import settings

logger = logging.getLogger(__name__)

class RedisCheckpointer:
    """Production Redis checkpointer with proper setup."""
    
    def __init__(self):
        self._checkpointer: Optional[RedisSaver] = None
        self._connection_string = None
        self._initialized = False
    
    def _build_connection_string(self) -> str:
        """Build Redis connection string from individual parameters."""
        return f"redis://{settings.REDIS_USERNAME}:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"
    
    def get_checkpointer(self) -> RedisSaver:
        """Get Redis checkpointer with proper setup."""
        if self._checkpointer is not None:
            return self._checkpointer
        
        if self._initialized:
            raise RuntimeError("Redis checkpointer initialization failed previously")
        
        return self._initialize_checkpointer()
    
    def _initialize_checkpointer(self) -> RedisSaver:
        """Initialize Redis checkpointer with proper setup pattern."""
        self._initialized = True
        
        try:
            logger.info("Initializing Redis checkpointer...")
            
            # Build connection string
            self._connection_string = self._build_connection_string()
            
            # Initialize checkpointer with proper 
            ttl_config = {
                "default_ttl": 720,     # Default TTL in minutes
                "refresh_on_read": True,  # Refresh TTL when checkpoint is read
                }

            checkpointer = None
            with RedisSaver.from_conn_string(self._connection_string, ttl=ttl_config) as _checkpointer:
                _checkpointer.setup()
                checkpointer = _checkpointer
            
            self._checkpointer = checkpointer
            logger.info(f"Redis checkpointer initialized successfully")
            return self._checkpointer
            
        except Exception as e:
            logger.error(f"Redis checkpointer initialization failed: {e}")
            raise RuntimeError(f"Redis checkpointer initialization failed: {e}") from e
    
    def close(self):
        """Clean up Redis connections."""
        logger.info("Redis checkpointer cleanup completed")
        self._checkpointer = None
        self._initialized = False

# Global checkpointer service
redis_checkpointer = RedisCheckpointer()
