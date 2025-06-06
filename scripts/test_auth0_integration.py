"""
Test Auth0 Integration

This script tests the Auth0 integration by:
1. Getting a token from Auth0
2. Testing the public endpoint
3. Testing the protected endpoint with the token
"""
import os
import sys
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.test")

# Auth0 configuration
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")

# API configuration
API_BASE_URL = "http://localhost:8000"

def get_auth0_token():
    """Get an access token from Auth0"""
    url = f"https://{AUTH0_DOMAIN}/oauth/token"
    headers = {"content-type": "application/json"}
    
    payload = {
        "client_id": AUTH0_CLIENT_ID,
        "client_secret": AUTH0_CLIENT_SECRET,
        "audience": AUTH0_AUDIENCE,
        "grant_type": "client_credentials"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()["access_token"]
    except Exception as e:
        print(f"Error getting token: {str(e)}")
        print(f"Response: {response.text}")
        sys.exit(1)

def test_public_endpoint():
    """Test the public endpoint"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/auth0-test/public")
        response.raise_for_status()
        print("✅ Public endpoint test passed")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"❌ Public endpoint test failed: {str(e)}")
        sys.exit(1)

def test_protected_endpoint(token):
    """Test the protected endpoint with a valid token"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/auth0-test/protected",
            headers=headers
        )
        response.raise_for_status()
        print("✅ Protected endpoint test passed")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"❌ Protected endpoint test failed: {str(e)}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        sys.exit(1)

def test_metadata_endpoint():
    """Test the Auth0 metadata endpoint"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/auth0-test/metadata")
        response.raise_for_status()
        print("✅ Metadata endpoint test passed")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"❌ Metadata endpoint test failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    print("🚀 Starting Auth0 integration tests...\n")
    
    # Test public endpoint
    print("🔍 Testing public endpoint...")
    test_public_endpoint()
    
    # Test metadata endpoint
    print("\n🔍 Testing metadata endpoint...")
    test_metadata_endpoint()
    
    # Get Auth0 token
    print("\n🔑 Getting Auth0 token...")
    token = get_auth0_token()
    print(f"✅ Token obtained successfully")
    
    # Test protected endpoint
    print("\n🔒 Testing protected endpoint...")
    test_protected_endpoint(token)
    
    print("\n✨ All tests completed successfully!")
    print("\nYou can now use the following token to authenticate requests:")
    print(f"\n{token}")
