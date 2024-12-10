import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Flask configuration
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # OpenAI configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Database Configuration
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "loadapp")
    DATABASE_URL = os.getenv('DATABASE_URL', f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    
    # API configuration
    API_PREFIX = '/api'
    
    # Frontend URL for CORS
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:8501')
