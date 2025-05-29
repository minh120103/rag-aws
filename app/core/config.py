import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    # Database - Point to the actual location of the database
    SQLITE_DB_PATH: str = os.path.join(os.path.dirname(__file__), "..", "..","data", "db", "movies_cv.db")
    MONGODB_URL: str = os.getenv("MONGODB_URL")
    
    # Azure OpenAIs
    EMBEDDING_AZURE_OPENAI_ENDPOINT: str = os.getenv("EMBEDDING_AZURE_OPENAI_ENDPOINT")
    EMBEDDING_API_VERSION: str = os.getenv("EMBEDDING_API_VERSION")
    
    # Qdrant
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY")
    QDRANT_URL: str = os.getenv("QDRANT_URL")

    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

settings = Settings()
