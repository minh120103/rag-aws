from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_qdrant import QdrantVectorStore
from langchain_community.utilities import SQLDatabase
from langchain_ollama import OllamaEmbeddings
from ..core.config import settings


# LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

# Embedder
# embedder = AzureOpenAIEmbeddings(
#     model="text-embedding-3-small",
#     azure_endpoint=settings.EMBEDDING_AZURE_OPENAI_ENDPOINT,
#     api_version=settings.EMBEDDING_API_VERSION
# )

embedder = OllamaEmbeddings(model="mxbai-embed-large")

# Vector Store
# vectorstore = QdrantVectorStore.from_existing_collection(
#     embedding=embedder,
#     api_key=settings.QDRANT_API_KEY,
#     collection_name="MovieScriptsAzure",
#     url=settings.QDRANT_URL,
#     prefer_grpc=True,
# )

vectorstore = QdrantVectorStore.from_existing_collection(
    embedding=embedder,
    api_key=settings.QDRANT_API_KEY,
    collection_name="MovieScriptsOllama",
    url=settings.QDRANT_URL,
    prefer_grpc=True,
)

# Database
db = SQLDatabase.from_uri(f"sqlite:///{settings.SQLITE_DB_PATH}", sample_rows_in_table_info=3)