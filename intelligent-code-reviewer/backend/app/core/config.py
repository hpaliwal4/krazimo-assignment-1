"""
Configuration settings for the Intelligent Code Reviewer.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # Application settings
    app_name: str = "AI Code Reviewer API"
    app_version: str = "1.0.0"
    app_description: str = "AI-Powered Intelligent Code Analysis and Review Platform"
    
    # Database settings
    database_url: str = "sqlite:///./intelligent_code_reviewer.db"
    
    # Vector store settings
    vector_store_path: str = "./vector_store"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # File processing settings
    temp_directory: str = "./temp"
    max_file_size_mb: int = 50
    
    # OpenAI settings for AI Agent
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4"
    openai_max_tokens: int = 4096
    openai_temperature: float = 0.3
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_title: str = "AI Code Reviewer API"
    api_version: str = "1.0.0"
    api_description: str = "AI-Powered Intelligent Code Analysis and Review Platform"
    
    # CORS settings
    cors_origins: list = ["http://localhost:3000", "http://127.0.0.1:3000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list = ["*"]
    cors_allow_headers: list = ["*"]
    
    # Development settings
    debug: bool = True
    reload: bool = True
    
    # Security settings
    secret_key: str = "intelligent-code-reviewer-secret-key-change-in-production"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings() 