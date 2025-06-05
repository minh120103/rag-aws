from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sys
import os
import logging
from contextlib import asynccontextmanager
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.api.routes import router
from app.services.redis_checkpointer import redis_checkpointer
from app.services.redis_cache_service import redis_cache_service
from app.services.rag_service import rag_service


logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan with Redis validation."""
    # Startup
    logger.info("Starting RAG Movie Assistant API")
    
    try:
        # Initialize Redis cache early
        redis_cache_service.initialize_llm_cache()

        health = rag_service.health_check()
        if health["status"] == "healthy":
            logger.info("Service startup completed successfully")
        else:
            logger.warning("Service starting with degraded functionality")

    except Exception as e:
        logger.warning(f"Startup health check failed: {e}")

    yield
    
    # Shutdown
    logger.info("Shutting down RAG Movie Assistant API")

    redis_checkpointer.close()

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="RAG Movie Assistant",
    description="A RAG-based movie information assistant with Redis state persistence",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api", tags=["RAG"])

@app.get("/")
async def root():
    return {
        "message": "RAG Movie Assistant API", 
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }

@app.get("/health")
def health_check():
    """Health check endpoint including Redis status."""
    return rag_service.health_check()

if __name__ == "__main__":
    """Run the FastAPI server."""
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        # log_config= None,
        reload=True
    )

