import os
import sys
import pytest
import tempfile
from unittest.mock import MagicMock, patch

# Set test environment variables before importing any app code
os.environ["ENV"] = "test"
os.environ["TESTING"] = "true"

# Import security test fixtures from organized structure
from tests.security.fixtures import SecurityTestFixtures, SecurityTestHelpers

# Now import other modules that depend on the security module
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends
from datetime import datetime, timedelta
from jose import jwt
from typing import Dict, Any, List, Optional

# Now import the app and other modules
from app.main import app as _app
from app.core.config import settings
from app.api.schemas import User, TokenResponse, EventDTO, MessageRequest, UserMemberDto, MemberDTO

# Define test user data
TEST_USER_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword"
TEST_USER_ID = 1

# Override environment variables for testing
os.environ["ENV"] = "test"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ALGORITHM"] = "HS256"

# Mock Auth0JWTBearer
class MockAuth0JWTBearer:
    def __init__(self, auto_error: bool = True):
        self.auto_error = auto_error
    
    async def __call__(self, request) -> Dict[str, Any]:
        return {
            "sub": "auth0|testuser123",
            "email": "test@example.com",
            "permissions": ["read:users", "write:users"]
        }

# Test application with overridden dependencies
@pytest.fixture
def test_app():
    return _app

@pytest.fixture
def sync_test_client():
    with TestClient(_app) as client:
        yield client

@pytest.fixture
async def async_test_client():
    async with TestClient(_app) as client:
        yield client

# For backward compatibility
@pytest.fixture
def test_client(sync_test_client):
    return sync_test_client

@pytest.fixture
def test_user():
    return User(
        id=1,
        email=TEST_USER_EMAIL,
        firstName="Test",
        lastName="User",
        userName="testuser",
        addressLine1="123 Test St",
        city="Test City",
        state="Test State",
        country="Test Country",
        pinCode="12345",
        phoneNumber="+1234567890",
        roleId=1,
        memberId=1,
        memberRelationUserId=1,
        memberRelationUniqueId="test123",
        memberUserRelationshipId=1
    )

@pytest.fixture
def test_token():
    # Create a test JWT token
    token_data = {
        "sub": str(TEST_USER_ID),
        "email": TEST_USER_EMAIL,
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }
    return jwt.encode(token_data, settings.SECRET_KEY, algorithm="HS256")

@pytest.fixture
def authenticated_client(test_client, test_token):
    test_client.headers.update({"Authorization": f"Bearer {test_token}"})
    return test_client

@pytest.fixture
async def async_authenticated_client(async_test_client, test_token):
    async_test_client.headers.update({"Authorization": f"Bearer {test_token}"})
    return async_test_client

@pytest.fixture
def admin_user():
    return User(
        id=2,
        email="admin@example.com",
        firstName="Admin",
        lastName="User",
        userName="admin",
        roleId=2,  # Assuming 2 is admin role
        memberId=2,
        memberRelationUserId=2,
        memberRelationUniqueId="admin123",
        memberUserRelationshipId=2
    )

@pytest.fixture
def admin_token(admin_user):
    token_data = {
        "sub": str(admin_user.id),
        "email": admin_user.email,
        "is_superuser": True,
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }
    return jwt.encode(token_data, settings.SECRET_KEY, algorithm="HS256")

@pytest.fixture
def admin_client(test_client, admin_token):
    test_client.headers.update({"Authorization": f"Bearer {admin_token}"})
    return test_client

@pytest.fixture
async def async_admin_client(async_test_client, admin_token):
    async_test_client.headers.update({"Authorization": f"Bearer {admin_token}"})
    return async_test_client

@pytest.fixture
def test_event(test_user):
    return EventDTO(
        eventId=1,
        title="Test Event",
        details="Test Description",
        startTime=(datetime.utcnow() + timedelta(days=1)).isoformat(),
        endTime=(datetime.utcnow() + timedelta(days=1, hours=2)).isoformat(),
        createdBy=test_user.id,
        attendees=[],
        externalUsers=[]
    )

@pytest.fixture
def test_member():
    return MemberDTO(
        memberId=1,
        email="member@example.com",
        firstName="Test",
        lastName="Member",
        userId=1,
        relationshipId=1
    )

@pytest.fixture
def test_user_member():
    return UserMemberDto(
        userId=1,
        uniqueMatchID="test123",
        name="Test User",
        memberEmail="member@example.com",
        memberName="Test Member",
        memberId=1
    )

@pytest.fixture
def test_message(test_user):
    return {
        "id": 1,
        "content": "Test Message",
        "sender_id": test_user.id,
        "recipient_id": 2,
        "created_at": datetime.utcnow().isoformat()
    }

@pytest.fixture
def test_connection(test_user):
    return {
        "id": 1,
        "user_id": test_user.id,
        "target_user_id": 2,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat()
    }

@pytest.fixture
def test_notification(test_user):
    return {
        "id": 1,
        "user_id": test_user.id,
        "title": "Test Notification",
        "message": "This is a test notification",
        "is_read": False,
        "created_at": datetime.utcnow().isoformat()
    }

@pytest.fixture
def temp_file():
    # Create a temporary file for testing file uploads
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
        f.write(b"test file content")
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    try:
        os.unlink(temp_path)
    except:
        pass