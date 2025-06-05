import logging
from typing import Dict, List, Optional
from datetime import datetime
from ..core.config import settings
from langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory
from langchain_core.messages import BaseMessage

logger = logging.getLogger(__name__)

class MemoryService:
    def __init__(self):
        self.mongodb_url = settings.MONGODB_URL
        self.database_name = settings.MONGODB_DATABASE
        self._validated = False
        self._validate_connection()
    
    def _validate_connection(self):
        """Validate MongoDB connection once on startup."""
        if not self.mongodb_url:
            logger.warning("MongoDB not configured - memory service disabled")
            return
            
        try:
            from pymongo import MongoClient
            client = MongoClient(self.mongodb_url, serverSelectionTimeoutMS=3000)
            client.admin.command('ping')
            client.close()
            self._validated = True
            logger.info("MongoDB connection validated")
        except Exception as e:
            logger.error(f"MongoDB validation failed: {e}")
            self._validated = False
    
    def _get_chat_history(self, session_id: str) -> Optional[MongoDBChatMessageHistory]:
        """Get MongoDB chat message history instance."""
        if not self._validated:
            return None
        
        return MongoDBChatMessageHistory(
            connection_string=self.mongodb_url,
            session_id=session_id,
            database_name=self.database_name,
            collection_name="chat_sessions"
        )
    
    def save_conversation(self, thread_id: str, question: str, answer: str, route: str) -> bool:
        """Save conversation to MongoDB chat history."""
        try:
            chat_history = self._get_chat_history(thread_id)
            if not chat_history:
                return False
            
            chat_history.add_user_message(question)
            chat_history.add_ai_message(answer)
            return True
            
        except Exception as e:
            logger.error(f"Failed to save conversation: {e}")
            return False
    
    def get_messages_for_langchain(self, session_id: str) -> List[BaseMessage]:
        """Get messages in LangChain format."""
        try:
            chat_history = self._get_chat_history(session_id)
            return chat_history.messages if chat_history else []
        except Exception as e:
            logger.error(f"Failed to get messages: {e}")
            return []
    
    def clear_session_history(self, session_id: str) -> bool:
        """Clear chat history for a session."""
        try:
            chat_history = self._get_chat_history(session_id)
            if chat_history:
                chat_history.clear()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to clear session: {e}")
            return False
    
    def get_session_summary(self, session_id: str) -> Dict:
        """Get session summary."""
        try:
            chat_history = self._get_chat_history(session_id)
            if not chat_history:
                return {"message_count": 0, "last_activity": None}
            
            messages = chat_history.messages
            return {
                "message_count": len(messages),
                "last_activity": datetime.utcnow() if messages else None,
                "session_id": session_id
            }
        except Exception as e:
            logger.error(f"Failed to get session summary: {e}")
            return {"message_count": 0, "last_activity": None}

# Global service instance
memory_service = MemoryService()
