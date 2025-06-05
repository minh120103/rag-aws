"""
Basic test to verify the refactored application setup
"""

import sys
import os

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_imports():
    """Test that all modules can be imported successfully."""
    try:
        from app.core.config import settings
        print("✅ Config import successful")
        from app.schemas.chat import ChatRequest, ChatResponse
        print("✅ Models import successful")
        
        from app.api.routes import router
        print("✅ API routes import successful")
        
        from app.main import app
        print("✅ Main app import successful")
        
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
        
        if not os.path.exists(settings.SQLITE_DB_PATH):
            print("⚠️  Warning: SQLite database not found at specified path")
        
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_resources():
    """Test resources initialization (may fail if env vars not set)."""
    try:
        from app.utils.states import State, QueryOutput
        print("✅ Type definitions imported")
        
        # Try to import LLM and other resources (may fail without proper env vars)
        try:
            from app.utils.states import llm, embedder, vectorstore, db
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
        return True
    except Exception as e:
        print(f"❌ Graph building test failed: {e}")
        return False

def test_rag_service():
    """Test the combined RAG service initialization."""
    try:
        from app.services.rag_service import rag_service
        print("✅ RAG service imported successfully")
        
        # Test that the service can be initialized (without actually connecting to MongoDB)
        if rag_service.graph is None:
            print("✅ RAG service is in initial state (graph not initialized)")
        else:
            print("✅ RAG service graph already initialized")
            
        # Test that the service has all required methods
        assert hasattr(rag_service, 'initialize_graph'), "Missing initialize_graph method"
        assert hasattr(rag_service, 'get_graph'), "Missing get_graph method"
        assert hasattr(rag_service, 'process_question'), "Missing process_question method"
        assert hasattr(rag_service, 'close'), "Missing close method"
        print("✅ RAG service has all required methods")
        
        return True
    except Exception as e:
        print(f"❌ RAG service test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Running comprehensive tests for RAG FastAPI Application\n")
    
    success = True
    
    print("1. Testing imports...")
    success &= test_imports()
    
    print("\n2. Testing configuration...")
    success &= test_configuration()
    
    print("\n3. Testing resources...")
    success &= test_resources()
    
    print("\n4. Testing graph building...")
    success &= test_graph_building()
    
    print("\n5. Testing RAG service...")
    success &= test_rag_service()
    
    print(f"\n{'✅ All tests passed!' if success else '❌ Some tests failed!'}")
    
    if not success:
        print("\n💡 Tips:")
        print("- Make sure your .env file is in the correct location")
        print("- Verify all environment variables are set")
        print("- Check that the database file exists at the specified path")
    
    if success:
        print("\n🎉 Your refactored application is ready to run!")
        print("Next steps:")
        print("1. Copy your .env file with the correct environment variables")
        print("2. Run: python run.py server")
        print("3. Visit: http://localhost:8000/docs")
    
    sys.exit(0 if success else 1)
