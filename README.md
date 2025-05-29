# RAG FastAPI Application

A refactored FastAPI application for a RAG-based movie information assistant with SQL and Vector search capabilities.

## Features

- **Multi-route RAG**: Supports SQL database queries, vector similarity search, and general conversation
- **Conversation Memory**: Maintains context across conversations using MongoDB or in-memory storage
- **Hybrid Retrieval**: Combines BM25 and vector search for optimal results
- **FastAPI**: Modern, fast web framework with automatic API documentation
- **Modular Architecture**: Clean separation of concerns with services, models, and utilities

## Installation

1. Clone the repository and navigate to the project directory:
```bash
cd rag-fastapi-app
```

2. Create a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
copy .env.example .env
# Edit .env with your actual values
```

## Environment Variables

Create a `.env` file with the following variables:

```env
MONGODB_URL=your_mongodb_connection_string
EMBEDDING_AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint
EMBEDDING_API_VERSION=your_api_version
QDRANT_API_KEY=your_qdrant_api_key
QDRANT_URL=your_qdrant_url
GOOGLE_API_KEY=your_google_api_key
DEBUG=true
```

## Usage

### Start the Server

```bash
python -m app.main
```

The server will start on `http://0.0.0.0:8000`

### API Endpoints

- **GET `/`** - Root endpoint with basic info
- **GET `/api/health`** - Health check
- **GET `/api/info`** - Application information
- **POST `/api/chat`** - Main chat endpoint with conversation memory
- **POST `/api/generate`** - Simple generation endpoint (backward compatibility)
- **GET `/docs`** - Automatic API documentation (Swagger UI)

### Example Usage

#### Chat Endpoint
```bash
curl -X POST "http://localhost:8000/api/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "question": "What movies did Christopher Nolan direct?",
       "thread_id": "user123"
     }'
```

#### Generate Endpoint (Legacy)
```bash
curl -X POST "http://localhost:8000/api/generate" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Tell me about Inception movie script"}'
```

## Architecture

### RAG Pipeline

The application uses a three-route RAG system:

1. **SQL Route**: For structured data queries about movies (cast, directors, ratings, etc.)
2. **Vector Route**: For semantic search through movie scripts and content
3. **General Route**: For conversational responses and general questions

### Components

- **Graph Service**: Manages the LangGraph workflow with MongoDB checkpointing
- **RAG Service**: Processes questions through the RAG pipeline
- **Resources**: Centralizes LLM, embeddings, and database connections
- **Nodes**: Individual processing steps in the RAG workflow

## Development

### Running in Development Mode

```bash
python -m app.main
```

This will start the server with auto-reload enabled when `DEBUG=true`.

### API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

## Dependencies

- FastAPI: Web framework
- LangChain: LLM orchestration
- LangGraph: Workflow management
- Qdrant: Vector database
- MongoDB: Conversation memory
- Google Generative AI: LLM provider
- Azure OpenAI: Embeddings provider

## License

This project is licensed under the MIT License.
