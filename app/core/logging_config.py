import logging
import logging.handlers
import os
from pathlib import Path

def setup_logging():
    """Configure simple, clean logging to a single file only."""
    
    # Prevent duplicate configuration
    if hasattr(setup_logging, '_configured'):
        return
    setup_logging._configured = True
    
    # Create logs directory
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Clear any existing handlers to prevent duplicates
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Configure root logger - FILE ONLY, NO CONSOLE
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            # ONLY file handler - no console output
            logging.handlers.RotatingFileHandler(
                filename=log_dir / "rag_app.log",
                maxBytes=20*1024*1024,  # 20MB
                backupCount=5,
                encoding='utf-8'
            )
        ],
        force=True
    )
    
    # Set external library log levels to reduce noise
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING) 
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)  # Silence uvicorn errors
    logging.getLogger("watchfiles").setLevel(logging.WARNING)    # Silence file watcher
    
    logging.info("Logging initialized - file only mode")