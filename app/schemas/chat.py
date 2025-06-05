from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    question: str
    thread_id: Optional[str] = "default"

class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    answer: str
    route: Optional[str] = None