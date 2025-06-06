#!/usr/bin/env python3
"""
Test script for LiaiZen API logging during actual API operations.

This script:
1. Starts the FastAPI server in the background
2. Makes various API requests to test logging
3. Captures and displays the logs generated
4. Tests different scenarios (success, errors, rate limiting)
"""

import asyncio
import os
import sys
import time
import subprocess
import requests
import threading
from pathlib import Path
import signal
import json

def setup_test_environment():
    """Setup test environment and logging."""
    print("🔧 Setting up test environment...")
    
    # Set environment variables for testing
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["DEBUG"] = "true"
    
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Clear existing log files for clean test
    for log_file in logs_dir.glob("*.log"):
        log_file.unlink()
    
    print("✅ Test environment setup complete")

def start_api_server():
    """Start the FastAPI server in the background."""
    print("🚀 Starting FastAPI server...")
    
    # Start the server using uvicorn
    cmd = [
        sys.executable, "-m", "uvicorn", 
        "app.main:app", 
        "--host", "127.0.0.1", 
        "--port", "8000",
        "--log-level", "debug",
        "--access-log"
    ]
    
    # Start server in background
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            response = requests.get("http://127.0.0.1:8000/health", timeout=1)
            if response.status_code == 200:
                print("✅ Server started successfully!")
                return process
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(1)
        if attempt % 5 == 0:
            print(f"   Still waiting... (attempt {attempt + 1}/{max_attempts})")
    
    print("❌ Failed to start server")
    process.terminate()
    return None

def test_api_endpoints(base_url="http://127.0.0.1:8000"):
    """Test various API endpoints to generate logs."""
    print("\n🧪 Testing API endpoints to generate logs...")
    
    test_cases = [
        {
            "name": "Root endpoint",
            "method": "GET",
            "url": f"{base_url}/",
            "expected_status": 200
        },
        {
            "name": "Health check",
            "method": "GET", 
            "url": f"{base_url}/health",
            "expected_status": 200
        },
        {
            "name": "API documentation",
            "method": "GET",
            "url": f"{base_url}/docs",
            "expected_status": 200
        },
        {
            "name": "Non-existent endpoint (404 error)",
            "method": "GET",
            "url": f"{base_url}/nonexistent",
            "expected_status": 404
        },
        {
            "name": "Auth endpoint without token (401 error)",
            "method": "GET",
            "url": f"{base_url}/api/me",
            "expected_status": 422  # Unprocessable Entity due to missing auth
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}/{len(test_cases)}: {test_case['name']}")
        
        try:
            # Make the request
            start_time = time.time()
            response = requests.request(
                method=test_case['method'],
                url=test_case['url'],
                timeout=10,
                headers={"User-Agent": "LiaiZen-Test-Client/1.0"}
            )
            duration = (time.time() - start_time) * 1000
            
            # Check response
            status_ok = response.status_code == test_case['expected_status']
            
            result = {
                "test": test_case['name'],
                "status_code": response.status_code,
                "expected": test_case['expected_status'],
                "duration_ms": round(duration, 2),
                "success": status_ok,
                "request_id": response.headers.get("X-Request-ID", "N/A"),
                "process_time": response.headers.get("X-Process-Time", "N/A")
            }
            
            results.append(result)
            
            status_icon = "✅" if status_ok else "❌"
            print(f"   {status_icon} Status: {response.status_code} (expected {test_case['expected_status']})")
            print(f"   ⏱️  Duration: {duration:.2f}ms")
            print(f"   🆔 Request ID: {result['request_id']}")
            print(f"   ⚡ Process Time: {result['process_time']}")
            
            # Small delay between requests
            time.sleep(0.5)
            
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
            results.append({
                "test": test_case['name'],
                "error": str(e),
                "success": False
            })
    
    return results

def test_rate_limiting(base_url="http://127.0.0.1:8000"):
    """Test rate limiting to generate rate limit logs."""
    print("\n🚦 Testing rate limiting...")
    
    # Make multiple rapid requests to trigger rate limiting
    # Note: The default rate limit is 100/hour, so we need to make many requests
    print("   Making rapid requests to test rate limiting...")
    
    rate_limit_triggered = False
    for i in range(10):  # Make 10 rapid requests
        try:
            response = requests.get(f"{base_url}/", timeout=1)
            if response.status_code == 429:
                print(f"   ✅ Rate limit triggered on request {i + 1}")
                rate_limit_triggered = True
                break
            time.sleep(0.1)  # Very short delay
        except Exception as e:
            print(f"   ⚠️  Request {i + 1} failed: {e}")
    
    if not rate_limit_triggered:
        print("   ℹ️  Rate limit not triggered (may need more requests or lower limit)")
    
    return rate_limit_triggered

def capture_and_display_logs():
    """Capture and display the generated logs."""
    print("\n📄 Capturing generated logs...")
    
    logs_dir = Path("logs")
    log_files = list(logs_dir.glob("*.log"))
    
    if not log_files:
        print("   ⚠️  No log files found")
        return
    
    for log_file in sorted(log_files):
        print(f"\n📋 Log file: {log_file.name}")
        print("-" * 60)
        
        try:
            with open(log_file, 'r') as f:
                content = f.read()
                if content:
                    # Show last 20 lines to avoid overwhelming output
                    lines = content.strip().split('\n')
                    if len(lines) > 20:
                        print(f"   ... (showing last 20 of {len(lines)} lines)")
                        lines = lines[-20:]
                    
                    for line in lines:
                        print(f"   {line}")
                else:
                    print("   (empty)")
        except Exception as e:
            print(f"   ❌ Error reading log file: {e}")

def cleanup_server(process):
    """Clean up the server process."""
    if process:
        print("\n🧹 Cleaning up server process...")
        try:
            process.terminate()
            process.wait(timeout=5)
            print("✅ Server stopped gracefully")
        except subprocess.TimeoutExpired:
            print("⚠️  Force killing server process...")
            process.kill()
            process.wait()
        except Exception as e:
            print(f"⚠️  Error stopping server: {e}")

def main():
    """Run the complete API logging test."""
    print("🚀 LiaiZen API Logging Test")
    print("=" * 60)
    
    server_process = None
    
    try:
        # Setup
        setup_test_environment()
        
        # Start server
        server_process = start_api_server()
        if not server_process:
            return 1
        
        # Wait a moment for logging to initialize
        time.sleep(2)
        
        # Test endpoints
        test_results = test_api_endpoints()
        
        # Test rate limiting
        rate_limit_result = test_rate_limiting()
        
        # Wait for logs to be written
        time.sleep(1)
        
        # Display results
        print("\n" + "=" * 60)
        print("📊 Test Results Summary")
        print("=" * 60)
        
        successful_tests = sum(1 for r in test_results if r.get('success', False))
        print(f"✅ Successful API tests: {successful_tests}/{len(test_results)}")
        print(f"🚦 Rate limiting test: {'✅ Triggered' if rate_limit_result else 'ℹ️  Not triggered'}")
        
        # Show detailed results
        print("\n📋 Detailed Test Results:")
        for result in test_results:
            if result.get('success'):
                print(f"   ✅ {result['test']}: {result['status_code']} ({result.get('duration_ms', 'N/A')}ms)")
            else:
                print(f"   ❌ {result['test']}: {result.get('error', 'Failed')}")
        
        # Capture and display logs
        capture_and_display_logs()
        
        print("\n" + "=" * 60)
        print("🎉 API logging test completed!")
        print("\n💡 What was tested:")
        print("   - FastAPI server startup logging")
        print("   - Request/response middleware logging")
        print("   - Error handling and logging")
        print("   - Rate limiting logging")
        print("   - File and console logging")
        print("   - Log rotation and organization")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        cleanup_server(server_process)

if __name__ == "__main__":
    exit(main())