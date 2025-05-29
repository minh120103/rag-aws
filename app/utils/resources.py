import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_qdrant import QdrantVectorStore
from langchain_community.utilities import SQLDatabase
from typing_extensions import TypedDict, Annotated
from typing import Literal, Sequence
from langchain_openai import AzureOpenAIEmbeddings
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from ..core.config import settings

# Type Definitions
class State(TypedDict):
    question: Annotated[Sequence[BaseMessage], add_messages]
    answer: Annotated[Sequence[BaseMessage], add_messages]
    query: str
    result: str
    route: Literal["sql", "vector", "general"]

class QueryOutput(TypedDict):
    """Generated SQL query."""
    query: Annotated[str, ..., "Syntactically valid SQL query."]

# LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

# Embedder
embedder = AzureOpenAIEmbeddings(
    model="text-embedding-3-small",
    azure_endpoint=settings.EMBEDDING_AZURE_OPENAI_ENDPOINT,
    api_version=settings.EMBEDDING_API_VERSION
)

# Vector Store
vectorstore = QdrantVectorStore.from_existing_collection(
    embedding=embedder,
    api_key=settings.QDRANT_API_KEY,
    collection_name="MovieScriptsAzure",
    url=settings.QDRANT_URL,
    prefer_grpc=True,
)

# Database
db = SQLDatabase.from_uri(f"sqlite:///{settings.SQLITE_DB_PATH}", sample_rows_in_table_info=0)
