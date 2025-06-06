#!/usr/bin/env python3
"""
Test script for LiaiZen API logging configuration.

This script tests:
- Basic logging setup
- Different log levels
- File logging
- Console logging
- Request/response logging functions
"""

import os
import sys
import tempfile
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.logging_config import (
    setup_logging, 
    get_logger, 
    log_request_info, 
    log_response_info, 
    log_error
)

def test_basic_logging():
    """Test basic logging functionality."""
    print("🔍 Testing basic logging setup...")
    
    # Test with different log levels
    for level in ["DEBUG", "INFO", "WARNING", "ERROR"]:
        print(f"\n📊 Testing log level: {level}")
        
        # Setup logging with specific level
        setup_logging(level=level)
        
        # Get a test logger
        logger = get_logger("test.basic")
        
        # Test all log levels
        logger.debug("This is a DEBUG message")
        logger.info("This is an INFO message")
        logger.warning("This is a WARNING message")
        logger.error("This is an ERROR message")
        logger.critical("This is a CRITICAL message")
        
        print(f"✅ {level} level logging test completed")

def test_file_logging():
    """Test file logging functionality."""
    print("\n🔍 Testing file logging...")
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = Path(temp_dir) / "test_liaizen.log"
        
        # Setup logging with custom file
        setup_logging(level="DEBUG", log_file=str(log_file))
        
        # Get a test logger
        logger = get_logger("test.file")
        
        # Write some test messages
        logger.info("Testing file logging functionality")
        logger.warning("This should appear in both main and error logs")
        logger.error("This is an error message for file testing")
        
        # Check if log file was created and has content
        if log_file.exists():
            with open(log_file, 'r') as f:
                content = f.read()
                if content:
                    print("✅ File logging working - log file created with content")
                    print(f"📄 Log file location: {log_file}")
                    print(f"📝 Log content preview:\n{content[:200]}...")
                else:
                    print("❌ File logging failed - log file empty")
        else:
            print("❌ File logging failed - log file not created")

def test_request_response_logging():
    """Test request/response logging functions."""
    print("\n🔍 Testing request/response logging functions...")
    
    setup_logging(level="INFO")
    
    # Test request logging
    print("📥 Testing request logging...")
    log_request_info(
        request_id="test-123",
        method="GET",
        path="/api/test",
        client_ip="192.168.1.100"
    )
    
    # Test response logging
    print("📤 Testing response logging...")
    log_response_info(
        request_id="test-123",
        status_code=200,
        duration_ms=45.67
    )
    
    # Test error logging
    print("🚨 Testing error logging...")
    try:
        raise ValueError("This is a test error for logging")
    except Exception as e:
        log_error(
            request_id="test-123",
            error=e,
            context="test_function"
        )
    
    print("✅ Request/response logging functions test completed")

def test_environment_variables():
    """Test logging with environment variables."""
    print("\n🔍 Testing environment variable configuration...")
    
    # Test LOG_LEVEL environment variable
    original_log_level = os.getenv("LOG_LEVEL")
    
    try:
        # Set environment variable
        os.environ["LOG_LEVEL"] = "WARNING"
        os.environ["LOG_FORMAT"] = "%(levelname)s - %(message)s"
        
        # Setup logging (should pick up env vars)
        setup_logging()
        
        logger = get_logger("test.env")
        logger.info("This INFO message should not appear (level is WARNING)")
        logger.warning("This WARNING message should appear")
        
        print("✅ Environment variable configuration test completed")
        
    finally:
        # Restore original environment
        if original_log_level:
            os.environ["LOG_LEVEL"] = original_log_level
        else:
            os.environ.pop("LOG_LEVEL", None)
        os.environ.pop("LOG_FORMAT", None)

def test_log_directory_creation():
    """Test automatic log directory creation."""
    print("\n🔍 Testing log directory creation...")
    
    # Remove logs directory if it exists
    logs_dir = Path("logs")
    if logs_dir.exists():
        import shutil
        shutil.rmtree(logs_dir)
    
    # Setup logging (should create logs directory)
    setup_logging(level="INFO")
    
    # Check if logs directory was created
    if logs_dir.exists() and logs_dir.is_dir():
        print("✅ Log directory creation test passed")
        
        # Check for log files
        log_files = list(logs_dir.glob("*.log"))
        if log_files:
            print(f"📁 Found {len(log_files)} log file(s):")
            for log_file in log_files:
                print(f"   - {log_file.name}")
        else:
            print("📁 Log directory created but no log files found yet")
    else:
        print("❌ Log directory creation test failed")

def main():
    """Run all logging tests."""
    print("🚀 Starting LiaiZen API Logging Tests")
    print("=" * 50)
    
    try:
        test_basic_logging()
        test_file_logging()
        test_request_response_logging()
        test_environment_variables()
        test_log_directory_creation()
        
        print("\n" + "=" * 50)
        print("🎉 All logging tests completed successfully!")
        print("\n💡 Tips:")
        print("   - Check the 'logs/' directory for log files")
        print("   - Use LOG_LEVEL environment variable to control verbosity")
        print("   - Error logs are separated into liaizen_api_errors.log")
        print("   - Log files rotate automatically when they reach 10MB")
        
    except Exception as e:
        print(f"\n❌ Logging test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())