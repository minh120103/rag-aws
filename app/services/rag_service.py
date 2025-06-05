import logging
from typing import Dict
from ..utils.nodes import build_graph
from langchain_core.messages import HumanMessage, AIMessage
from ..schemas.chat import ChatRequest, ChatResponse
from .redis_checkpointer import redis_checkpointer
from .redis_cache_service import redis_cache_service
from .memory_service import memory_service

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.graph = None
        self._graph_initialized = False

        redis_cache_service.initialize_llm_cache()
        self._initialize_graph()
        
    def _initialize_graph(self):
        """Initialize graph with Redis checkpointer."""
        if self._graph_initialized:
            return
            
        try:
            checkpointer = redis_checkpointer.get_checkpointer()
            self.graph = build_graph().compile(checkpointer=checkpointer)
            self._graph_initialized = True
            logger.info("Graph initialized successfully")
            
        except Exception as e:
            logger.error(f"Graph initialization failed: {e}")
            self._graph_initialized = False
            raise RuntimeError(f"Cannot initialize RAG service: {e}") from e
    
    def process_question(self, request: ChatRequest) -> ChatResponse:
        """Process question through RAG pipeline."""
        try:
            if not self._graph_initialized:
                raise RuntimeError("Graph not initialized")
            
            config = {"configurable": {"thread_id": request.thread_id}}
            current_state = self.graph.get_state(config)
            
            if current_state and current_state.values.get("messages"):
                graph_input = {
                    "messages": [HumanMessage(content=request.question)],
                    "thread_id": request.thread_id
                }
            else:
                chat_history = memory_service.get_messages_for_langchain(request.thread_id)[-10:]
                all_messages = chat_history + [HumanMessage(content=request.question)]
                graph_input = {
                    "messages": all_messages,
                    "thread_id": request.thread_id
                }
            
            result = self.graph.invoke(graph_input, config=config)
            
            answer = result.get("answer", "Sorry, I couldn't process your question.")
            route = result.get("route", "unknown")
            
            if not answer and result.get("messages"):
                ai_messages = [msg for msg in result["messages"] if isinstance(msg, AIMessage)]
                if ai_messages:
                    answer = ai_messages[-1].content
            
            return ChatResponse(answer=answer, route=route)
            
        except RuntimeError as e:
            logger.error(f"Service unavailable: {e}")
            return ChatResponse(
                answer="Service temporarily unavailable. Please try again.",
                route="error"
            )
        except Exception as e:
            logger.error(f"Error processing question: {e}")
            return ChatResponse(
                answer="Sorry, something went wrong. Please try again.",
                route="error"
            )
    
    def get_conversation_state(self, thread_id: str) -> dict:
        """Get conversation state from Redis."""
        try:
            if not self._graph_initialized:
                raise RuntimeError("Graph not initialized")
            
            config = {"configurable": {"thread_id": thread_id}}
            state = self.graph.get_state(config)
            return state.values if state else {}
            
        except Exception as e:
            logger.error(f"Error getting state: {e}")
            raise RuntimeError(f"Cannot retrieve conversation state: {e}") from e
    
    def clear_conversation_state(self, thread_id: str) -> bool:
        """Clear conversation state."""
        try:
            if not self._graph_initialized:
                raise RuntimeError("Graph not initialized")
            
            config = {"configurable": {"thread_id": thread_id}}
            current_state = self.graph.get_state(config)
            redis_cleared = False
            
            if current_state:
                checkpointer = redis_checkpointer.get_checkpointer()
                if hasattr(checkpointer, 'delete'):
                    checkpointer.delete(config)
                    redis_cleared = True
            
            mongo_cleared = memory_service.clear_session_history(thread_id)
            return redis_cleared or mongo_cleared
            
        except Exception as e:
            logger.error(f"Error clearing state: {e}")
            return False
    
    def get_session_info(self, thread_id: str) -> dict:
        """Get session information."""
        try:
            summary = memory_service.get_session_summary(thread_id)
            state = self.get_conversation_state(thread_id)
            
            return {
                "thread_id": thread_id,
                "message_count": summary.get("message_count", 0),
                "last_activity": summary.get("last_activity"),
                "has_state": bool(state)
            }
        except Exception as e:
            logger.error(f"Error getting session info: {e}")
            return {"thread_id": thread_id, "error": str(e)}

    def health_check(self) -> dict:
        """Check service health."""
        try:
            redis_checkpointer.get_checkpointer()
            
            if not self._graph_initialized:
                raise RuntimeError("Graph not initialized")

            cache_stats = redis_cache_service.get_cache_stats()

            return {
                "status": "healthy",
                "redis_connected": True,
                "graph_initialized": True,
                "llm_cache": cache_stats
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "redis_connected": False,
                "graph_initialized": self._graph_initialized,
                "error": str(e)
            }

# Global service instance
rag_service = RAGService()
