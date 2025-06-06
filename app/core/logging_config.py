import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional
from fastapi.logger import logger as fastapi_logger

def setup_logging(level: Optional[str] = None, log_file: Optional[str] = None):
    """
    Enhanced logging configuration for LiaiZen API.
    
    Features:
    - Environment-based log level configuration
    - File and console logging
    - Structured log format with timestamps
    - Rotating file handlers to prevent disk space issues
    - Separate error log file for critical issues
    - Request ID tracking support
    
    Args:
        level: Log level override (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Custom log file path
    """
    # Get log level from environment or parameter
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO")
    
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Define log format with more detailed information
    log_format = os.getenv(
        "LOG_FORMAT",
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    )
    
    # Create formatter
    formatter = logging.Formatter(
        fmt=log_format,
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(log_level)
    
    # Console handler for all logs
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler for all logs (rotating)
    if log_file is None:
        log_file = log_dir / "liaizen_api.log"
    
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Separate error log file for WARNING and above
    error_log_file = log_dir / "liaizen_api_errors.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.WARNING)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)
    
    # Configure FastAPI logger
    fastapi_logger.setLevel(log_level)
    
    # Configure uvicorn loggers
    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.setLevel(log_level)
    
    uvicorn_error = logging.getLogger("uvicorn.error")
    uvicorn_error.setLevel(log_level)
    
    # Configure SQLAlchemy logger (reduce verbosity in production)
    sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
    if log_level >= logging.INFO:
        sqlalchemy_logger.setLevel(logging.WARNING)
    else:
        sqlalchemy_logger.setLevel(log_level)
    
    # Log the logging configuration
    logging.info(f"Logging configured - Level: {level}, File: {log_file}")
    logging.info(f"Log directory: {log_dir.absolute()}")
    
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)

def log_request_info(request_id: str, method: str, path: str, client_ip: str):
    """
    Log incoming request information.
    
    Args:
        request_id: Unique request identifier
        method: HTTP method
        path: Request path
        client_ip: Client IP address
    """
    logger = get_logger("liaizen.requests")
    logger.info(f"[{request_id}] {method} {path} - Client: {client_ip}")

def log_response_info(request_id: str, status_code: int, duration_ms: float):
    """
    Log response information.
    
    Args:
        request_id: Unique request identifier
        status_code: HTTP status code
        duration_ms: Request duration in milliseconds
    """
    logger = get_logger("liaizen.responses")
    logger.info(f"[{request_id}] Response: {status_code} - Duration: {duration_ms:.2f}ms")

def log_error(request_id: str, error: Exception, context: str = ""):
    """
    Log error information with context.
    
    Args:
        request_id: Unique request identifier
        error: Exception that occurred
        context: Additional context information
    """
    logger = get_logger("liaizen.errors")
    logger.error(f"[{request_id}] Error in {context}: {str(error)}", exc_info=True)
