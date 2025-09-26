"""
Configuration management for Plume & Mimir backend
Uses Pydantic Settings for environment variable validation
"""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from typing import List, Optional, Dict, Any
from enum import Enum
import os

class Environment(str, Enum):
    """Environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class LogLevel(str, Enum):
    """Log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class Settings(BaseSettings):
    """Application settings with validation"""

    # =============================================================================
    # APPLICATION SETTINGS
    # =============================================================================
    VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    ENVIRONMENT: Environment = Field(default=Environment.DEVELOPMENT, env="ENVIRONMENT")
    PORT: int = Field(default=8000, env="PORT")
    HOST: str = Field(default="0.0.0.0", env="HOST")

    # =============================================================================
    # SECURITY SETTINGS
    # =============================================================================
    SECRET_KEY: str = Field(
        default="ag9r5NDYFPERqQkr1ydh7q3sxDy_wXm8DmJmtkb9EIjXXhk5dcNc1hVhTgSwAVdZ",
        env="SECRET_KEY",
        min_length=32
    )
    JWT_SECRET: str = Field(
        default="GihHv0s-XDHQ50JymFHqjn7_LChjpFu37HU5Pb_fjQ8RQg-ZHwvOcTvvmr4rIZDW",
        env="JWT_SECRET",
        min_length=32
    )
    ALLOWED_HOSTS: str = Field(
        default="localhost,127.0.0.1,0.0.0.0",
        env="ALLOWED_HOSTS"
    )
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        env="CORS_ORIGINS"
    )

    # =============================================================================
    # DATABASE SETTINGS
    # =============================================================================
    SUPABASE_URL: str = Field(..., env="SUPABASE_URL")
    SUPABASE_ANON_KEY: str = Field(..., env="SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_KEY: str = Field(..., env="SUPABASE_SERVICE_KEY")
    DATABASE_URL: str = Field(..., env="DATABASE_URL")

    # Database connection settings
    DB_POOL_SIZE: int = Field(default=20, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(default=30, env="DB_MAX_OVERFLOW")
    DB_POOL_TIMEOUT: int = Field(default=30, env="DB_POOL_TIMEOUT")

    # =============================================================================
    # AI SERVICES API KEYS
    # =============================================================================
    CLAUDE_API_KEY: str = Field(..., env="CLAUDE_API_KEY")
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    PERPLEXITY_API_KEY: Optional[str] = Field(default=None, env="PERPLEXITY_API_KEY")
    TAVILY_API_KEY: Optional[str] = Field(default=None, env="TAVILY_API_KEY")
    COHERE_API_KEY: Optional[str] = Field(default=None, env="COHERE_API_KEY")

    # =============================================================================
    # REDIS CACHE SETTINGS
    # =============================================================================
    REDIS_URL: Optional[str] = Field(default=None, env="REDIS_URL")
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")

    # Cache TTL settings (in seconds)
    CACHE_TTL_EMBEDDINGS: int = Field(default=604800, env="CACHE_TTL_EMBEDDINGS")  # 7 days
    CACHE_TTL_TRANSCRIPTIONS: int = Field(default=86400, env="CACHE_TTL_TRANSCRIPTIONS")  # 24 hours
    CACHE_TTL_LLM_RESPONSES: int = Field(default=3600, env="CACHE_TTL_LLM_RESPONSES")  # 1 hour

    # =============================================================================
    # LLM CONFIGURATION
    # =============================================================================
    # Plume (restitution agent) settings
    MAX_TOKENS_PLUME: int = Field(default=4000, env="MAX_TOKENS_PLUME")
    TEMPERATURE_PLUME: float = Field(default=0.3, env="TEMPERATURE_PLUME")
    MODEL_PLUME: str = Field(default="claude-3-opus-20240229", env="MODEL_PLUME")

    # Mimir (archive agent) settings
    MAX_TOKENS_MIMIR: int = Field(default=4000, env="MAX_TOKENS_MIMIR")
    TEMPERATURE_MIMIR: float = Field(default=0.2, env="TEMPERATURE_MIMIR")
    MODEL_MIMIR: str = Field(default="claude-3-opus-20240229", env="MODEL_MIMIR")

    # General LLM settings
    DEFAULT_MODEL: str = Field(default="claude-3-opus-20240229", env="DEFAULT_MODEL")
    EMBEDDING_MODEL: str = Field(default="text-embedding-3-large", env="EMBEDDING_MODEL")
    EMBEDDING_DIMENSIONS: int = Field(default=1536, env="EMBEDDING_DIMENSIONS")

    # =============================================================================
    # RAG SETTINGS
    # =============================================================================
    RAG_CHUNK_SIZE: int = Field(default=500, env="RAG_CHUNK_SIZE")
    RAG_CHUNK_OVERLAP: int = Field(default=50, env="RAG_CHUNK_OVERLAP")
    RAG_TOP_K: int = Field(default=10, env="RAG_TOP_K")
    RAG_SIMILARITY_THRESHOLD: float = Field(default=0.78, env="RAG_SIMILARITY_THRESHOLD")

    # =============================================================================
    # RATE LIMITING
    # =============================================================================
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    RATE_LIMIT_PER_HOUR: int = Field(default=1000, env="RATE_LIMIT_PER_HOUR")
    RATE_LIMIT_PER_DAY: int = Field(default=10000, env="RATE_LIMIT_PER_DAY")

    # Specific endpoint limits
    CHAT_RATE_LIMIT: str = Field(default="10/minute", env="CHAT_RATE_LIMIT")
    SEARCH_RATE_LIMIT: str = Field(default="30/minute", env="SEARCH_RATE_LIMIT")
    TRANSCRIPTION_RATE_LIMIT: str = Field(default="5/minute", env="TRANSCRIPTION_RATE_LIMIT")

    # =============================================================================
    # LOGGING SETTINGS
    # =============================================================================
    LOG_LEVEL: LogLevel = Field(default=LogLevel.INFO, env="LOG_LEVEL")
    STRUCTURED_LOGGING: bool = Field(default=True, env="STRUCTURED_LOGGING")
    LOG_FILE: Optional[str] = Field(default=None, env="LOG_FILE")

    # =============================================================================
    # MONITORING & APM
    # =============================================================================
    DATADOG_API_KEY: Optional[str] = Field(default=None, env="DATADOG_API_KEY")
    NEW_RELIC_LICENSE_KEY: Optional[str] = Field(default=None, env="NEW_RELIC_LICENSE_KEY")
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")

    # =============================================================================
    # FILE PROCESSING
    # =============================================================================
    MAX_UPLOAD_SIZE: int = Field(default=10 * 1024 * 1024, env="MAX_UPLOAD_SIZE")  # 10MB
    ALLOWED_AUDIO_FORMATS: str = Field(
        default="webm,mp3,wav,m4a,ogg",
        env="ALLOWED_AUDIO_FORMATS"
    )
    AUDIO_PROCESSING_TIMEOUT: int = Field(default=300, env="AUDIO_PROCESSING_TIMEOUT")  # 5 minutes

    # =============================================================================
    # BACKGROUND TASKS
    # =============================================================================
    CELERY_BROKER_URL: Optional[str] = Field(default=None, env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: Optional[str] = Field(default=None, env="CELERY_RESULT_BACKEND")
    ENABLE_BACKGROUND_TASKS: bool = Field(default=True, env="ENABLE_BACKGROUND_TASKS")

    # =============================================================================
    # PERFORMANCE SETTINGS
    # =============================================================================
    REQUEST_TIMEOUT: int = Field(default=300, env="REQUEST_TIMEOUT")  # 5 minutes
    MAX_CONCURRENT_REQUESTS: int = Field(default=100, env="MAX_CONCURRENT_REQUESTS")
    ENABLE_COMPRESSION: bool = Field(default=True, env="ENABLE_COMPRESSION")

    # =============================================================================
    # COST MONITORING
    # =============================================================================
    TRACK_TOKEN_USAGE: bool = Field(default=True, env="TRACK_TOKEN_USAGE")
    MAX_MONTHLY_TOKENS: int = Field(default=1000000, env="MAX_MONTHLY_TOKENS")
    MONTHLY_BUDGET_ALERT: float = Field(default=100.0, env="MONTHLY_BUDGET_ALERT")  # EUR
    DAILY_BUDGET_ALERT: float = Field(default=5.0, env="DAILY_BUDGET_ALERT")  # EUR

    # =============================================================================
    # VALIDATORS
    # =============================================================================
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            if v.strip() == "":
                return "http://localhost:3000,http://127.0.0.1:3000"
        return v

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, v):
        if isinstance(v, str):
            if v.strip() == "":
                return "localhost,127.0.0.1,0.0.0.0"
        return v

    @field_validator("ALLOWED_AUDIO_FORMATS", mode="before")
    @classmethod
    def parse_audio_formats(cls, v):
        if isinstance(v, str):
            if v.strip() == "":
                return "webm,mp3,wav,m4a,ogg"
        return v

    @field_validator("SECRET_KEY", "JWT_SECRET", mode="before")
    @classmethod
    def validate_secrets(cls, v):
        if v in ["YOUR_SECRET_KEY_HERE", "YOUR_JWT_SECRET_HERE"] or len(v) < 32:
            import secrets
            return secrets.token_urlsafe(32)
        return v

    @field_validator("TEMPERATURE_PLUME", "TEMPERATURE_MIMIR")
    @classmethod
    def validate_temperature(cls, v):
        if not 0.0 <= v <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v

    @field_validator("RAG_SIMILARITY_THRESHOLD")
    @classmethod
    def validate_similarity_threshold(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Similarity threshold must be between 0.0 and 1.0")
        return v

    # =============================================================================
    # COMPUTED PROPERTIES
    # =============================================================================
    @property
    def redis_connection_kwargs(self) -> Dict[str, Any]:
        """Redis connection parameters"""
        if self.REDIS_URL:
            return {"url": self.REDIS_URL}

        kwargs = {
            "host": self.REDIS_HOST,
            "port": self.REDIS_PORT,
            "db": self.REDIS_DB,
        }

        if self.REDIS_PASSWORD:
            kwargs["password"] = self.REDIS_PASSWORD

        return kwargs

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENVIRONMENT == Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.ENVIRONMENT == Environment.DEVELOPMENT

    @property
    def database_config(self) -> Dict[str, Any]:
        """Database configuration parameters"""
        return {
            "pool_size": self.DB_POOL_SIZE,
            "max_overflow": self.DB_MAX_OVERFLOW,
            "pool_timeout": self.DB_POOL_TIMEOUT,
        }

    @property
    def plume_config(self) -> Dict[str, Any]:
        """Plume agent configuration"""
        return {
            "model": self.MODEL_PLUME,
            "max_tokens": self.MAX_TOKENS_PLUME,
            "temperature": self.TEMPERATURE_PLUME,
        }

    @property
    def mimir_config(self) -> Dict[str, Any]:
        """Mimir agent configuration"""
        return {
            "model": self.MODEL_MIMIR,
            "max_tokens": self.MAX_TOKENS_MIMIR,
            "temperature": self.TEMPERATURE_MIMIR,
        }

    @property
    def cors_origins_list(self) -> List[str]:
        """CORS origins as list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def allowed_hosts_list(self) -> List[str]:
        """Allowed hosts as list"""
        return [host.strip() for host in self.ALLOWED_HOSTS.split(",")]

    @property
    def allowed_audio_formats_list(self) -> List[str]:
        """Audio formats as list"""
        return [fmt.strip().lower() for fmt in self.ALLOWED_AUDIO_FORMATS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()

# Export commonly used configs
PLUME_CONFIG = settings.plume_config
MIMIR_CONFIG = settings.mimir_config
REDIS_CONFIG = settings.redis_connection_kwargs
DATABASE_CONFIG = settings.database_config