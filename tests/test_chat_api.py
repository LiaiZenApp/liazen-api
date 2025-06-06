# tests/test_chat_api.py
"""
Test cases for the chat API endpoints.
"""
import pytest
from fastapi import status, FastAPI, Depends, HTTPException
from fastapi.testclient import TestClient
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from unittest.mock import AsyncMock, patch, MagicMock, create_autospec
from app.models.schemas import MessageRequest, MessageDTO, User, TokenData
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from typing import Optional

# Mock user for testing
mock_user = User(
    id=uuid4(),
    email="test@example.com",
    first_name="Test",
    last_name="User",
    is_active=True,
    is_verified=True,
    role="user",
    hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"  # hashed "testpass"
)

# Mock token data
mock_token_data = TokenData(
    sub=str(mock_user.id),
    email=mock_user.email,
    exp=datetime.utcnow() + timedelta(minutes=30)
)

# Mock OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Test client with authentication
class AuthenticatedTestClient(TestClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = "test-token"
    
    def _handle_request(self, method, url, **kwargs):
        headers = kwargs.get('headers', {})
        if 'Authorization' not in headers:
            headers['Authorization'] = f"Bearer {self.token}"
        kwargs['headers'] = headers
        return super()._handle_request(method, url, **kwargs)

# Fixture for authenticated test client
@pytest.fixture
def authenticated_client():
    from fastapi import FastAPI
    from app.api import chat as chat_router
    
    app = FastAPI()
    
    # Mock the get_current_user dependency
    async def mock_get_current_user():
        return mock_user
    
    # Override the dependency in the router
    app.dependency_overrides[chat_router.get_current_user] = mock_get_current_user
    
    app.include_router(chat_router.router)
    
    with AuthenticatedTestClient(app) as client:
        yield client

# Fixture for unauthenticated test client
@pytest.fixture
def test_app():
    from fastapi import FastAPI
    from app.api import chat as chat_router
    
    app = FastAPI()
    app.include_router(chat_router.router)
    
    return app

def test_send_message(authenticated_client):
    # Setup test data
    test_message = MessageDTO(
        id=uuid4(),
        sender_id=str(mock_user.id),
        recipient_id="87654321-4321-8765-4321-876543210987",
        content="Hello, world!",
        created_at=datetime.utcnow(),
        is_read=False
    )
    
    # Mock the chat service
    with patch("app.api.chat.send_message_svc", return_value=test_message) as mock_send:
        # Test data
        message_data = {
            "content": "Hello, world!",
            "recipient_id": "87654321-4321-8765-4321-876543210987",
            "metadata": {}
        }
        
        # Send the request using the authenticated client
        response = authenticated_client.post(
            "/api/chat/messages",
            json=message_data
        )
        
        # Print response content for debugging if test fails
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Unexpected status code: {response.status_code}")
            print(f"Response content: {response.text}")
            
        # Assertions
        assert response.status_code == status.HTTP_201_CREATED, f"Expected status code 201 but got {response.status_code}"
        data = response.json()
        assert data["content"] == "Hello, world!"
        assert data["sender_id"] == str(mock_user.id)
        assert data["recipient_id"] == "87654321-4321-8765-4321-876543210987"
        mock_send.assert_called_once()

def test_get_messages(authenticated_client):
    # Create test messages
    test_messages = [
        MessageDTO(
            id=uuid4(),
            sender_id=str(mock_user.id),
            recipient_id="87654321-4321-8765-4321-876543210987",
            content="Message 1",
            created_at=datetime.utcnow(),
            is_read=False
        ),
        MessageDTO(
            id=uuid4(),
            sender_id="87654321-4321-8765-4321-876543210987",
            recipient_id=str(mock_user.id),
            content="Message 2",
            created_at=datetime.utcnow(),
            is_read=False
        )
    ]
    
    # Mock the chat service
    with patch("app.api.chat.get_messages_svc", return_value=test_messages) as mock_get:
        # Send the request using the authenticated client
        response = authenticated_client.get(
            "/api/chat/messages?recipient_id=87654321-4321-8765-4321-876543210987"
        )
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert data[0]["content"] == "Message 1"
        mock_get.assert_called_once()
        
        # Test with pagination parameters
        response = authenticated_client.get(
            "/api/chat/messages?recipient_id=87654321-4321-8765-4321-876543210987&limit=1&offset=1"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2  # Mock doesn't implement actual pagination
        
        # Test with invalid recipient_id
        with patch("app.api.chat.get_messages_svc", side_effect=ValueError("Invalid recipient ID")) as mock_get_error:
            response = authenticated_client.get(
                "/api/chat/messages?recipient_id=invalid"
            )
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Invalid recipient ID" in response.json()["detail"]
        
        # Test with missing recipient_id
        response = authenticated_client.get("/api/chat/messages")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_send_message_with_invalid_recipient(authenticated_client):
    # Test with invalid recipient ID format
    with patch("app.api.chat.send_message_svc", side_effect=ValueError("Invalid recipient ID")) as mock_send:
        response = authenticated_client.post(
            "/api/chat/messages",
            json={
                "content": "Hello",
                "recipient_id": "invalid-uuid",
                "metadata": {}
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid recipient ID" in response.json()["detail"]

def test_send_message_with_empty_content(authenticated_client):
    # Test with empty content
    response = authenticated_client.post(
        "/api/chat/messages",
        json={
            "content": "",  # Empty content
            "recipient_id": "87654321-4321-8765-4321-876543210987",
            "metadata": {}
        }
    )
    
    # The API returns 400 for empty content, not 422
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "content" in response.json().get("detail", "").lower()

def test_get_messages_unauthorized(test_app, monkeypatch):
    # Import the chat router after patching
    from app.api import chat as chat_router
    
    # Create a new test client with the original router but without auth overrides
    app = FastAPI()
    app.include_router(chat_router.router)
    
    # Mock the get_current_user dependency to raise HTTP_401_UNAUTHORIZED
    async def mock_get_current_user_unauthorized():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Override the dependency in the router
    app.dependency_overrides[chat_router.get_current_user] = mock_get_current_user_unauthorized
    
    # Create test client with the modified app
    client = TestClient(app)
    
    # Make the request without authentication
    response = client.get(
        "/api/chat/messages?recipient_id=87654321-4321-8765-4321-876543210987"
    )
    
    # Should return 401 Unauthorized
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_send_message_service_error(authenticated_client):
    # Test service layer error
    with patch("app.api.chat.send_message_svc", side_effect=Exception("Database error")) as mock_send:
        response = authenticated_client.post(
            "/api/chat/messages",
            json={
                "content": "Hello",
                "recipient_id": "87654321-4321-8765-4321-876543210987",
                "metadata": {}
            }
        )
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to send message" in response.json()["detail"]

def test_get_messages_service_error(authenticated_client):
    # Test service layer error
    with patch("app.api.chat.get_messages_svc", side_effect=Exception("Database error")) as mock_get:
        response = authenticated_client.get(
            "/api/chat/messages?recipient_id=87654321-4321-8765-4321-876543210987"
        )
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to retrieve messages" in response.json()["detail"]