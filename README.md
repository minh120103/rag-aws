# RAG Movie Assistant - FastAPI Application

A production-ready FastAPI application that combines SQL databases, vector search, and conversational AI to answer movie-related questions through an intelligent routing system.

## 🎯 Features

### Core Capabilities
- **Intelligent Query Routing**: Automatically routes questions to SQL, vector search, or general conversation
- **Multi-Modal RAG**: Combines structured database queries with semantic vector search
- **Conversation Memory**: Persistent chat history using MongoDB Chat Message History
- **Redis State Management**: LangGraph checkpointing with Redis for conversation state
- **LLM Response Caching**: Redis-based caching for improved performance
- **Hybrid Retrieval**: BM25 + Vector similarity search with ensemble ranking

### Technical Architecture
- **FastAPI**: Modern async web framework with automatic OpenAPI documentation
- **LangGraph**: Workflow orchestration with state persistence
- **Google Gemini**: Primary LLM for reasoning and generation
- **Ollama Embeddings**: Local embeddings for vector search
- **Qdrant**: Vector database for semantic search
- **SQLite**: Structured movie database
- **MongoDB**: Chat message history storage
- **Redis**: State persistence and LLM response caching

## 🛠️ Installation

### Prerequisites
- Python 3.12+
- Redis instance (local or cloud)
- MongoDB instance (local or cloud)
- Qdrant vector database
- Ollama (for embeddings)

### Setup Steps

1. **Clone and Navigate**
```bash
git clone <repository-url>
cd rag-fastapi-dev
```

2. **Create Virtual Environment**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment Configuration**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Setup Ollama (for embeddings)**
```bash
# Install Ollama and pull the embedding model
ollama pull mxbai-embed-large
```

## ⚙️ Configuration

Create a `.env` file with the following required variables:

```env
# Google AI
GOOGLE_API_KEY=your_google_api_key

# Redis Configuration
REDIS_HOST=your_redis_host
REDIS_PORT=your_redis_port
REDIS_USERNAME=your_redis_username
REDIS_PASSWORD=your_redis_password

# MongoDB
MONGODB_URL=mongodb://your_mongodb_connection

# Qdrant Vector Database
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_qdrant_api_key

# Optional: Azure OpenAI (if switching from Ollama)
EMBEDDING_AZURE_OPENAI_ENDPOINT=your_azure_endpoint
EMBEDDING_API_VERSION=your_api_version

# Development
DEBUG=true
ENVIRONMENT=development
```

## 🚀 Usage

### Start the Application

**Development Mode:**
```bash
python app/main.py
```

**Production Mode:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Docker:**
```bash
docker build -t rag-movie-assistant .
docker run -p 8000:8000 --env-file .env rag-movie-assistant
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Application info and links |
| `/health` | GET | Health check with service status |
| `/docs` | GET | Interactive API documentation |
| `/api/chat` | POST | Main chat endpoint with memory |
| `/api/info` | GET | Application metadata |
| `/api/conversation/{thread_id}/state` | DELETE | Clear conversation state |

### Chat API Usage

```bash
curl -X POST "http://localhost:8000/api/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "question": "What movies did Christopher Nolan direct?",
       "thread_id": "user123"
     }'
```

**Response:**
```json
{
  "answer": "Christopher Nolan directed movies including Inception, Interstellar, The Dark Knight trilogy, Dunkirk, and Tenet.",
  "route": "sql"
}
```

### Frontend Interface

Launch the Streamlit frontend:
```bash
streamlit run app/static/frontend.py
```

## 🏗️ Architecture

### Request Flow
```
User Question → FastAPI → RAG Service → LangGraph Workflow
    ↓
Router Node → Route Decision (SQL/Vector/General)
    ↓
SQL Route: Database Query → Answer Generation
Vector Route: Semantic Search → RAG Chain → Answer
General Route: Conversational Response
    ↓
Memory Service → MongoDB Chat History
Redis Checkpointer → Conversation State
```

### Service Architecture

```
app/
├── main.py                 # FastAPI application entry point
├── api/
│   └── routes.py          # API endpoint definitions
├── core/
│   ├── config.py          # Environment configuration
│   └── logging_config.py  # Logging setup
├── factories/
│   └── models.py          # LLM, embeddings, databases
├── schemas/
│   └── chat.py            # Pydantic models
├── services/
│   ├── rag_service.py     # Main RAG orchestration
│   ├── memory_service.py  # MongoDB chat history
│   ├── redis_checkpointer.py  # LangGraph state persistence
│   └── redis_cache_service.py # LLM response caching
├── utils/
│   ├── nodes.py           # LangGraph node functions
│   ├── states.py          # State type definitions
│   └── prompts.py         # System prompts
└── static/
    └── frontend.py        # Streamlit UI
```

### Routing Logic

The application intelligently routes questions:

- **SQL Route**: Factual queries about movie data (cast, directors, ratings, box office)
- **Vector Route**: Content-based questions (plot, themes, character analysis)
- **General Route**: Casual conversation and non-movie topics

## 🧪 Testing

Run the comprehensive test suite:
```bash
python test_setup.py
```

This validates:
- ✅ Module imports
- ✅ Configuration loading
- ✅ Resource initialization
- ✅ Graph building
- ✅ Service health

## 📊 Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

**Response includes:**
- Redis connectivity status
- Graph initialization status
- LLM cache statistics
- Overall service health

### Logging
Logs are written to `logs/rag_app.log` with rotation:
- Application events
- Request processing
- Error tracking
- Performance metrics

## 🔧 Development

### Key Components

**RAG Service** (`app/services/rag_service.py`):
- Main orchestration layer
- Graph compilation and execution
- Error handling and fallbacks

**Memory Service** (`app/services/memory_service.py`):
- MongoDB chat message history
- Session management
- Conversation context retrieval

**Redis Services**:
- `redis_checkpointer.py`: LangGraph state persistence
- `redis_cache_service.py`: LLM response caching

**Graph Nodes** (`app/utils/nodes.py`):
- `router`: Question classification
- `write_query`: SQL generation
- `execute_query`: Database execution
- `generate_*_answer`: Response generation

### Adding New Features

1. **New Route**: Add routing logic in `router()` function
2. **New Node**: Create function in `nodes.py` and wire in `build_graph()`
3. **New Service**: Add to `services/` with proper initialization
4. **New Endpoint**: Add to `api/routes.py` with appropriate models

## 📦 Dependencies

### Core Framework
- **FastAPI**: Web framework
- **LangChain/LangGraph**: LLM orchestration and workflows
- **Pydantic**: Data validation

### AI/ML Stack
- **Google Generative AI**: Primary LLM (Gemini 2.0 Flash)
- **Ollama**: Local embeddings (mxbai-embed-large)
- **Qdrant**: Vector database

### Storage & Caching
- **MongoDB**: Chat message history
- **Redis**: State persistence and caching
- **SQLite**: Structured movie database

### Retrieval
- **BM25**: Keyword-based retrieval
- **Vector Similarity**: Semantic search
- **Ensemble**: Hybrid ranking

## 🚀 Deployment

### Docker Deployment
```bash
docker build -t rag-movie-assistant .
docker run -d -p 8000:8000 --env-file .env rag-movie-assistant
```

### Production Considerations
- Use proper CORS origins in production
- Configure Redis and MongoDB with authentication
- Set up proper logging and monitoring
- Use reverse proxy (nginx) for SSL termination
- Configure rate limiting and security headers

## 📝 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## 📞 Support

- Check the health endpoint for service status
- Review logs in `logs/rag_app.log`
- Run `test_setup.py` for diagnostic information
- Ensure all environment variables are properly configured
