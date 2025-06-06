"""
LiaiZen API - Configuration Module

This module provides comprehensive configuration management for the LiaiZen API
using Pydantic Settings for type-safe, environment-aware configuration handling.

Key Features:
- Environment-specific configuration loading (.env, .env.test, .env.prod)
- Type-safe configuration with Pydantic validation
- Auth0 integration settings with computed properties
- Database configuration with environment switching
- Security settings with production-ready defaults
- File upload and API configuration
- Comprehensive logging configuration

Architecture:
- Uses Pydantic BaseSettings for automatic environment variable loading
- Supports multiple .env files for different environments
- Provides computed properties for derived configuration values
- Implements validation and type checking for all settings
- Environment-aware defaults for development vs production

Security Considerations:
- Sensitive values loaded from environment variables
- Production-ready security defaults
- Configurable token expiration and encryption settings
- CORS configuration for cross-origin security

Author: LiaiZen Development Team
Version: 1.0
"""

import os
from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional, Any, Tuple, Type, List, Dict, Union
from dotenv import load_dotenv

class Settings(BaseSettings):
    """
    Application settings with environment-aware configuration.
    
    This class manages all configuration for the LiaiZen API, providing
    type-safe access to environment variables and computed configuration
    properties. It supports multiple environments (test, development, production)
    with appropriate defaults and validation.
    
    Configuration Sources (in order of precedence):
    1. Environment variables
    2. .env.{ENV} files (e.g., .env.test, .env.prod)
    3. .env file
    4. Default values defined in this class
    
    Attributes:
        All configuration values are defined as class attributes with
        appropriate types, defaults, and validation rules.
    """
    
    # ========================================================================
    # ENVIRONMENT CONFIGURATION
    # ========================================================================
    
    ENV: str = "test"  # Current environment: test, development, production
    DEBUG: bool = False  # Enable debug mode for development
    
    # ========================================================================
    # SERVER CONFIGURATION
    # ========================================================================
    
    HOST: str = "0.0.0.0"  # Server bind address (0.0.0.0 for Docker compatibility)
    PORT: int = 8000  # Server port
    RELOAD: bool = True  # Enable auto-reload for development
    
    # ========================================================================
    # AUTH0 CONFIGURATION
    # ========================================================================
    
    AUTH0_DOMAIN: str  # Auth0 tenant domain (required)
    AUTH0_CLIENT_ID: str  # Auth0 application client ID (required)
    AUTH0_CLIENT_SECRET: str  # Auth0 application client secret (required)
    AUTH0_AUDIENCE: str  # Auth0 API audience identifier (required)
    AUTH0_ISSUER: str = ""  # Auth0 issuer URL (computed if not provided)
    
    # ========================================================================
    # CORS CONFIGURATION
    # ========================================================================
    
    ALLOWED_ORIGINS: str = "*"  # Comma-separated list of allowed origins
    
    # ========================================================================
    # DATABASE CONFIGURATION
    # ========================================================================
    
    DATABASE_URL: str = "sqlite:///./test.db"  # Primary database URL
    TEST_DATABASE_URL: Optional[str] = "sqlite:///./test.db"  # Test database URL
    
    # ========================================================================
    # SECURITY CONFIGURATION
    # ========================================================================
    
    SECRET_KEY: str = "your-secret-key-here"  # JWT signing key (CHANGE IN PRODUCTION!)
    JWT_ALGORITHM: str = "HS256"  # JWT signing algorithm
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # Access token lifetime
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # Refresh token lifetime
    BCRYPT_ROUNDS: int = 12  # Password hashing rounds (higher = more secure, slower)
    
    # ========================================================================
    # API CONFIGURATION
    # ========================================================================
    
    API_V1_STR: str = "/api/v1"  # API version prefix
    
    # ========================================================================
    # FILE UPLOAD CONFIGURATION
    # ========================================================================
    
    UPLOAD_DIR: str = "uploads"  # Directory for file uploads
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # Maximum file size (5MB)
    
    # ========================================================================
    # LOGGING CONFIGURATION
    # ========================================================================
    
    LOG_LEVEL: str = "INFO"  # Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    # ========================================================================
    # APPLICATION METADATA
    # ========================================================================
    
    APP_NAME: str = "LiaiZen API"  # Application name
    APP_VERSION: str = "1.0.0"  # Application version
    
    # ========================================================================
    # PYDANTIC CONFIGURATION
    # ========================================================================
    
    model_config = SettingsConfigDict(
        env_file=".env",  # Default environment file
        env_file_encoding='utf-8',  # File encoding
        extra="ignore",  # Ignore extra environment variables
        env_nested_delimiter='__',  # Delimiter for nested config (e.g., DB__HOST)
        case_sensitive=True,  # Environment variables are case-sensitive
        validate_default=True,  # Validate default values
        validate_assignment=True,  # Validate on assignment
        protected_namespaces=()  # Allow model_ prefixed fields
    )
    
    # ========================================================================
    # COMPUTED PROPERTIES
    # ========================================================================
    
    @property
    def is_test(self) -> bool:
        """Check if running in test environment."""
        return self.ENV.lower() == "test"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENV.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment (includes test)."""
        return self.ENV.lower() in ("development", "test")
    
    @property
    def database_url(self) -> str:
        """Get the appropriate database URL for the current environment."""
        return self.TEST_DATABASE_URL if self.is_test else self.DATABASE_URL
    
    @property
    def auth0_issuer(self) -> str:
        """Get the Auth0 issuer URL (computed from domain if not explicitly set)."""
        return self.AUTH0_ISSUER or f"https://{self.AUTH0_DOMAIN}/"
    
    @property
    def auth0_jwks_uri(self) -> str:
        """Get the Auth0 JWKS (JSON Web Key Set) URI for token validation."""
        return f"https://{self.AUTH0_DOMAIN}/.well-known/jwks.json"
    
    @property
    def auth0_authorization_url(self) -> str:
        """Get the Auth0 authorization endpoint URL."""
        return f"https://{self.AUTH0_DOMAIN}/authorize"
    
    @property
    def auth0_token_url(self) -> str:
        """Get the Auth0 token endpoint URL for token exchange."""
        return f"https://{self.AUTH0_DOMAIN}/oauth/token"
    
    @property
    def auth0_userinfo_url(self) -> str:
        """Get the Auth0 user info endpoint URL."""
        return f"https://{self.AUTH0_DOMAIN}/userinfo"
    
    # ========================================================================
    # CUSTOM CONFIGURATION LOADING
    # ========================================================================
    
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ) -> Tuple[Any, ...]:
        """
        Customize configuration source loading to support environment-specific .env files.
        
        This method implements a sophisticated configuration loading strategy:
        1. Load environment-specific .env file (.env.test, .env.prod, etc.)
        2. Fall back to generic .env file if environment-specific file doesn't exist
        3. Override with actual environment variables
        
        Loading Order (highest to lowest precedence):
        1. Environment variables
        2. .env.{ENV} file (e.g., .env.production)
        3. .env file
        4. Default values
        
        Args:
            settings_cls: The Settings class being configured
            init_settings: Settings from class initialization
            env_settings: Settings from environment variables
            dotenv_settings: Settings from .env files
            file_secret_settings: Settings from secret files
            
        Returns:
            Tuple of configuration sources in precedence order
            
        Example:
            If ENV=production, will try to load .env.production first,
            then fall back to .env if .env.production doesn't exist.
        """
        # Determine environment and corresponding .env file
        env = os.getenv("ENV") or "test"
        env_file = f".env.{env}" if env else ".env"
        
        # Check if environment-specific file exists, fall back to generic .env
        if not Path(env_file).exists():
            env_file = ".env"
        
        # Load the appropriate .env file if it exists
        if Path(env_file).exists():
            load_dotenv(env_file, override=True)
        
        return (init_settings, env_settings, dotenv_settings, file_secret_settings)

# ============================================================================
# GLOBAL SETTINGS INSTANCE
# ============================================================================

# Create global settings instance
# This instance is imported throughout the application for configuration access
settings = Settings()
