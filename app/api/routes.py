from fastapi import APIRouter, HTTPException
from ..services.rag_service import rag_service
from ..schemas.chat import ChatRequest, ChatResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        logger.info(f"Processing chat request for thread_id: {request.thread_id}")
        response = rag_service.process_question(request)
        return response
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info")
async def get_info():
    """Get application information."""
    return {
        "name": "RAG Movie Assistant",
        "version": "1.0.0",
        "description": "A RAG-based movie information assistant with SQL and Vector search capabilities"
    }


@router.delete("/conversation/{thread_id}/state")
def clear_conversation_state(thread_id: str):
    """Clear conversation state for a specific thread."""
    try:
        success = rag_service.clear_conversation_state(thread_id)
        return {
            "success": success,
            "message": f"Conversation state cleared for thread {thread_id}" if success else "No state found to clear"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
