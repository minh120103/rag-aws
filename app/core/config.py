import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    # Database - Point to the actual location of the database
    SQLITE_DB_PATH: str = os.path.join(os.path.dirname(__file__), "..", "..","data", "db", "movies_cv.db")
    
    # MongoDB for long-term memory
    MONGODB_URL: str = os.getenv("MONGODB_URL")
    MONGODB_DATABASE: str = Field(default="rag_memory", env="MONGODB_DATABASE")
    
    # Azure OpenAIs
    EMBEDDING_AZURE_OPENAI_ENDPOINT: str = os.getenv("EMBEDDING_AZURE_OPENAI_ENDPOINT")
    EMBEDDING_API_VERSION: str = os.getenv("EMBEDDING_API_VERSION")
    
    # Qdrant
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY")
    QDRANT_URL: str = os.getenv("QDRANT_URL")

    # Redis Configuration - Individual parameters
    REDIS_HOST: str = Field(env="REDIS_HOST")
    REDIS_PORT: int = Field(env="REDIS_PORT") 
    REDIS_USERNAME: str = Field(default="default", env="REDIS_USERNAME")
    REDIS_PASSWORD: str = Field(env="REDIS_PASSWORD")
        
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

settings = Settings()
