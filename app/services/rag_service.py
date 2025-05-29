from typing import Dict, Any
import logging
from langgraph.checkpoint.mongodb import MongoDBSaver
from ..utils.nodes import build_graph
from ..core.config import settings
from langchain_core.messages import HumanMessage
from ..models.chat import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.graph_builder = build_graph()
        self.graph = None
        self.checkpointer = None
        self._mongodb_context = None
        
    def initialize_graph(self):
        """Initialize graph with MongoDB checkpointer."""
        if not settings.MONGODB_URL:
            raise ValueError("MONGODB_URL is required but not set in environment variables")
        
        try:
            # Use context manager for MongoDB checkpointer
            self._mongodb_context = MongoDBSaver.from_conn_string(settings.MONGODB_URL)
            self.checkpointer = self._mongodb_context.__enter__()
            self.graph = self.graph_builder.compile(checkpointer=self.checkpointer)
            logger.info("Graph initialized with MongoDB checkpointer")
        except Exception as e:
            error_msg = f"Failed to initialize graph with MongoDB checkpointer: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    def get_graph(self):
        """Get the graph instance, initializing if necessary."""
        if self.graph is None:
            self.initialize_graph()
        return self.graph
    
    def close(self):
        """Clean up resources."""
        try:
            if self._mongodb_context:
                self._mongodb_context.__exit__(None, None, None)
                self._mongodb_context = None
            elif self.checkpointer and hasattr(self.checkpointer, 'close'):
                self.checkpointer.close()
        except Exception as e:
            logger.error(f"Error closing checkpointer: {e}")
        finally:
            self.checkpointer = None
            self.graph = None
    
    def process_question(self, request: "ChatRequest") -> "ChatResponse":
        """Process a question through the RAG pipeline."""
        # Import at runtime to avoid circular imports
        
        config = {"configurable": {"thread_id": request.thread_id}}
        
        final_answer = None
        route = None
        
        try:
            # Convert string question to HumanMessage
            question_message = HumanMessage(content=request.question)
            
            # Get the graph
            graph = self.get_graph()
            
            for step in graph.stream(
                {"question": [question_message]}, 
                config=config, 
                stream_mode="updates"
            ):
                if "generate_vector_answer" in step:
                    final_answer = step["generate_vector_answer"]["answer"]
                    route = "vector"
                elif "generate_sql_answer" in step:
                    final_answer = step["generate_sql_answer"]["answer"]
                    route = "sql"
                elif "generate_general_answer" in step:
                    final_answer = step["generate_general_answer"]["answer"]
                    route = "general"
            
            if final_answer:
                return ChatResponse(answer=final_answer, route=route)
            else:
                return ChatResponse(answer="Sorry, I couldn't process your question.")
                
        except Exception as e:
            logger.error(f"Error in RAG processing: {e}")
            import traceback
            traceback.print_exc()
            return ChatResponse(answer=f"Error processing question: {str(e)}")

# Global RAG service instance
rag_service = RAGService()
