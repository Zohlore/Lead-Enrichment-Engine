import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    
    # Database
    CACHE_DB_PATH = "data/cache.db"
    
    # Cache TTL (7 days in seconds)
    CACHE_TTL_SECONDS = 7 * 24 * 60 * 60
    
    # Token limits (cost control)
    MAX_CONTENT_CHARS = 4000
    MAX_SEARCH_RESULTS = 5
    
    # Batch processing
    BATCH_SIZE = 10
    DELAY_BETWEEN_REQUESTS = 1.0  # seconds (rate limiting)
    
    # Model settings
    LLM_MODEL = "gpt-4o-mini"
    TEMPERATURE = 0.2

config = Config()