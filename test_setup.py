"""
Comprehensive test to verify the RAG Movie Assistant application setup
"""

import sys
import os

# Add app directory to path
sys.path.append(os.path.dirname(__file__))

def test_imports():
    """Test that all modules can be imported successfully."""
    try:
        from app.core.config import settings
        print("✅ Config import successful")
        
        from app.schemas.chat import ChatRequest, ChatResponse
        print("✅ Schema models import successful")
        
        from app.api.routes import router
        print("✅ API routes import successful")
        
        from app.main import app
        print("✅ Main app import successful")
        
        from app.services.rag_service import rag_service
        print("✅ RAG service import successful")
        
        from app.services.memory_service import memory_service
        print("✅ Memory service import successful")
        
        from app.services.redis_checkpointer import redis_checkpointer
        print("✅ Redis checkpointer import successful")
        
        from app.services.redis_cache_service import redis_cache_service
        print("✅ Redis cache service import successful")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_configuration():
    """Test configuration and paths."""
    try:
        from app.core.config import settings
        print(f"📁 SQLite DB Path: {settings.SQLITE_DB_PATH}")
        print(f"🗄️  DB exists: {os.path.exists(settings.SQLITE_DB_PATH)}")
        
        # Check required environment variables
        required_vars = ['GOOGLE_API_KEY', 'REDIS_HOST', 'REDIS_PASSWORD']
        missing_vars = []
        
        for var in required_vars:
            if not hasattr(settings, var) or not getattr(settings, var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        else:
            print("✅ All required environment variables present")
        
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_resources():
    """Test resources initialization."""
    try:
        from app.utils.states import State, QueryOutput
        print("✅ Type definitions imported")
        
        # Try to import models (may fail without proper env vars)
        try:
            from app.factories.models import llm, embedder, vectorstore, db
            print("✅ Resources imported (LLM, embedder, vectorstore, db)")
        except Exception as e:
            print(f"⚠️  Resources import warning (may need environment variables): {e}")
        
        return True
    except Exception as e:
        print(f"❌ Resources test failed: {e}")
        return False

def test_graph_building():
    """Test graph building functionality."""
    try:
        from app.utils.nodes import build_graph
        graph_builder = build_graph()
        print("✅ Graph builder created successfully")
        
        # Test that all required nodes exist
        expected_nodes = ["router", "write_query", "execute_query", 
                         "generate_sql_answer", "generate_vector_answer", "generate_general_answer"]
        
        for node in expected_nodes:
            if node in graph_builder.nodes:
                print(f"✅ Node '{node}' found")
            else:
                print(f"❌ Node '{node}' missing")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Graph building test failed: {e}")
        return False

def test_services():
    """Test service initialization."""
    try:
        from app.services.rag_service import rag_service
        print("✅ RAG service imported successfully")
        
        # Test service methods exist
        required_methods = ['process_question', 'health_check', 'clear_conversation_state', 'get_session_info']
        for method in required_methods:
            if hasattr(rag_service, method):
                print(f"✅ Method '{method}' exists")
            else:
                print(f"❌ Method '{method}' missing")
                return False
        
        # Test memory service
        from app.services.memory_service import memory_service
        print("✅ Memory service imported")
        
        # Test cache service
        from app.services.redis_cache_service import redis_cache_service
        print("✅ Redis cache service imported")
        
        return True
    except Exception as e:
        print(f"❌ Services test failed: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Running comprehensive tests for RAG Movie Assistant\n")
    
    success = True
    
    print("1. Testing imports...")
    success &= test_imports()
    
    print("\n2. Testing configuration...")
    success &= test_configuration()
    
    print("\n3. Testing resources...")
    success &= test_resources()
    
    print("\n4. Testing graph building...")
    success &= test_graph_building()
    
    print("\n5. Testing services...")
    success &= test_services()

    print(f"\n{'✅ All tests passed!' if success else '❌ Some tests failed!'}")
    
    if not success:
        print("\n💡 Tips:")
        print("- Make sure your .env file is properly configured")
        print("- Verify all environment variables are set")
        print("- Check that the database file exists")
        print("- Ensure Redis and MongoDB are accessible")
    
    if success:
        print("\n🎉 Your RAG Movie Assistant is ready to run!")
        print("Next steps:")
        print("1. Start the backend: python app/main.py")
        print("2. Start the frontend: streamlit run app/static/frontend.py")
        print("3. Visit: http://localhost:8000/docs for API docs")    
    sys.exit(0 if success else 1)
