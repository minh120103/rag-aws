from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sys
import os
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.api.routes import router
from app.services.rag_service import rag_service
from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="RAG Movie Assistant",
    description="A RAG-based movie information assistant with SQL and Vector search capabilities",
    version="1.0.0")

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
    return {"status": "healthy"}

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

