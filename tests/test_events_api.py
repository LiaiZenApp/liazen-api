# tests/test_events_api.py
import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from app.models.schemas import EventCreate
from app.api.events import router as events_router
from uuid import UUID

# Create a test FastAPI app
@pytest.fixture
def test_app():
    app = FastAPI()
    
    # Mock the auth_scheme to return a valid token
    mock_auth_scheme = MagicMock()
    mock_auth_scheme.return_value = "test-token"
    
    # Override the auth_scheme in the events router
    import app.api.events as events_module
    events_module.auth_scheme = mock_auth_scheme
    
    # Include the router after setting up the mock
    app.include_router(events_router)
    return app

# Create a test client
@pytest.fixture
def test_client(test_app):
    return TestClient(test_app)

# Create an authenticated test client
@pytest.fixture
def authenticated_client(test_client):
    test_client.headers.update({"Authorization": "Bearer test-token"})
    return test_client

# Test data fixtures
@pytest.fixture
def test_event_dict():
    return {
        "id": "223e4567-e89b-12d3-a456-426614174001",
        "title": "Test Event",
        "description": "Test Description",
        "start_time": "2023-01-01T00:00:00",
        "end_time": "2023-01-01T01:00:00",
        "location": "Test Location",
        "organizer_id": "223e4567-e89b-12d3-a456-426614174001",
        "creator_id": "223e4567-e89b-12d3-a456-426614174001",
        "is_virtual": False,
        "meeting_url": None,
        "capacity": None,
        "is_active": True,
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00"
    }

@pytest.fixture
def event_create_data():
    return {
        "title": "Test Event",
        "description": "Test Description",
        "start_time": "2023-01-01T00:00:00",
        "end_time": "2023-01-01T01:00:00",
        "location": "Test Location",
        "is_virtual": False,
        "meeting_url": None,
        "capacity": None,
        "is_active": True
    }

# Test for creating an event
def test_create_event(authenticated_client, test_event_dict, event_create_data):
    # Create a copy of the event data to avoid modifying the fixture
    event_data = event_create_data.copy()
    
    # Mock the create_event function to return our test event
    with patch("app.api.events.create_event") as mock_create:
        # Configure the mock to return our test event dict
        mock_create.return_value = test_event_dict
        
        # Make the request to the API
        response = authenticated_client.post(
            "/api/events",
            json=event_data,
        )
        
        # Check the response
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == "Test Event"
        assert data["id"] == "223e4567-e89b-12d3-a456-426614174001"
        
        # Verify the mock was called exactly once
        mock_create.assert_called_once()

        # Verify the event data was passed correctly
        call_args = mock_create.call_args[0][0]
        assert call_args.title == event_data["title"]
        assert call_args.description == event_data["description"]
        # Convert string to datetime for comparison
        from datetime import datetime
        assert call_args.start_time == datetime.fromisoformat(event_data["start_time"])
        assert call_args.end_time == datetime.fromisoformat(event_data["end_time"])
        assert call_args.location == event_data["location"]
        assert call_args.is_virtual == event_data["is_virtual"]
        assert call_args.meeting_url == event_data["meeting_url"]
        assert call_args.capacity == event_data["capacity"]
        assert call_args.is_active == event_data["is_active"]

# Test for getting user events
def test_get_user_events(authenticated_client, test_event_dict):
    # Create a mock response that matches the expected format
    mock_response = {
        "events": [test_event_dict],
        "total": 1,
        "page": 1,
        "limit": 10
    }
    
    # Mock the get_events_by_user function
    with patch("app.api.events.get_events_by_user") as mock_get:
        # Configure the mock to return our test response
        mock_get.return_value = mock_response
        
        # Make the request to the API with required query parameters
        response = authenticated_client.get(
            "/api/events/user/1",
            params={
                "page": 1,
                "limit": 10,
                "search_text": "",
                "time_zone": "UTC"
            }
        )
        
        # Check the response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "events" in data
        assert isinstance(data["events"], list)
        assert len(data["events"]) == 1
        assert data["events"][0]["title"] == "Test Event"
        assert data["total"] == 1
        assert data["page"] == 1
        assert data["limit"] == 10
        
        # Verify the mock was called with the correct arguments
        mock_get.assert_called_once()

# Test for getting a single event
def test_get_event(authenticated_client, test_event_dict):
    event_id = 1
    
    # Mock the get_event_by_id function
    with patch("app.api.events.get_event_by_id") as mock_get:
        # Configure the mock to return our test event
        mock_get.return_value = test_event_dict
        
        # Make the request to the API
        response = authenticated_client.get(f"/api/events/{event_id}")
        
        # Check the response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verify the response data matches our test event
        assert data["id"] == test_event_dict["id"]
        assert data["title"] == test_event_dict["title"]
        assert data["description"] == test_event_dict["description"]
        assert data["start_time"] == test_event_dict["start_time"]
        assert data["end_time"] == test_event_dict["end_time"]
        assert data["location"] == test_event_dict["location"]
        assert data["organizer_id"] == test_event_dict["organizer_id"]
        assert data["creator_id"] == test_event_dict["creator_id"]
        assert data["is_virtual"] == test_event_dict["is_virtual"]
        assert data["meeting_url"] == test_event_dict["meeting_url"]
        assert data["capacity"] == test_event_dict["capacity"]
        assert data["is_active"] == test_event_dict["is_active"]
        assert data["created_at"] == test_event_dict["created_at"]
        assert data["updated_at"] == test_event_dict["updated_at"]
        
        # Verify the mock was called with the correct event_id
        mock_get.assert_called_once_with(event_id)


# Additional comprehensive tests

class TestEventsApiCoverage:
    """Test class focused on covering specific lines in events.py API endpoints."""
    
    @pytest.fixture
    def common_auth_headers(self):
        """Centralized authentication headers."""
        return {"Authorization": "Bearer test-token"}
    
    @pytest.fixture
    def mock_event_service_responses(self):
        """Centralized mock responses for event services."""
        return {
            "create_success": {
                "success": True,
                "event": {"id": 1, "title": "Test Event"},
                "message": "Event created successfully"
            },
            "get_user_events": {
                "success": True,
                "user_id": 1,
                "search_text": "test",
                "time_zone": "UTC",
                "events": [],
                "count": 0
            },
            "get_event": {
                "success": True,
                "event": {"id": 1, "title": "Sample Event"}
            },
            "delete_success": {
                "success": True,
                "deleted_id": 1,
                "message": "Event 1 deleted successfully"
            }
        }

    def test_create_event_http_exception_handling(self, authenticated_client, event_create_data, mock_event_service_responses):
        """Test lines 28-31 - HTTPException handling in create_event."""
        from fastapi import HTTPException, status
        
        with patch("app.api.events.create_event") as mock_create:
            # Test HTTPException re-raising (line 28-29)
            mock_create.side_effect = HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid event data"
            )
            
            response = authenticated_client.post("/api/events", json=event_create_data)
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Invalid event data" in response.json()["detail"]
    
    def test_create_event_general_exception_handling(self, authenticated_client, event_create_data):
        """Test lines 30-34 - General exception handling in create_event."""
        with patch("app.api.events.create_event") as mock_create:
            # Test general Exception handling (lines 30-34)
            mock_create.side_effect = Exception("Database connection failed")
            
            response = authenticated_client.post("/api/events", json=event_create_data)
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to create event: Database connection failed" in response.json()["detail"]

    def test_get_user_events_http_exception_handling(self, authenticated_client):
        """Test lines 53-56 - HTTPException handling in get_user_events."""
        from fastapi import HTTPException, status
        
        with patch("app.api.events.get_events_by_user") as mock_get:
            # Test HTTPException re-raising (lines 53-54)
            mock_get.side_effect = HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
            response = authenticated_client.get("/api/events/user/999")
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "User not found" in response.json()["detail"]
    
    def test_get_user_events_general_exception_handling(self, authenticated_client):
        """Test lines 55-59 - General exception handling in get_user_events."""
        with patch("app.api.events.get_events_by_user") as mock_get:
            # Test general Exception handling (lines 55-59)
            mock_get.side_effect = Exception("Service unavailable")
            
            response = authenticated_client.get("/api/events/user/1")
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to fetch user events: Service unavailable" in response.json()["detail"]

    def test_get_event_http_exception_handling(self, authenticated_client):
        """Test lines 74-77 - HTTPException handling in get_event."""
        from fastapi import HTTPException, status
        
        with patch("app.api.events.get_event_by_id") as mock_get:
            # Test HTTPException re-raising (lines 74-75)
            mock_get.side_effect = HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
            
            response = authenticated_client.get("/api/events/1")
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert "Access denied" in response.json()["detail"]
    
    def test_get_event_general_exception_handling(self, authenticated_client):
        """Test lines 76-80 - General exception handling in get_event."""
        with patch("app.api.events.get_event_by_id") as mock_get:
            # Test general Exception handling (lines 76-80)
            mock_get.side_effect = Exception("Event retrieval failed")
            
            response = authenticated_client.get("/api/events/1")
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to fetch event: Event retrieval failed" in response.json()["detail"]

    def test_delete_event_success_flow(self, authenticated_client, mock_event_service_responses):
        """Test lines 93-99 - Successful delete flow."""
        with patch("app.api.events.delete_event") as mock_delete:
            # Test successful deletion (lines 93-99)
            mock_delete.return_value = mock_event_service_responses["delete_success"]
            
            response = authenticated_client.delete("/api/events/1")
            assert response.status_code == status.HTTP_204_NO_CONTENT
            mock_delete.assert_called_once_with(1)
    
    def test_delete_event_not_found_handling(self, authenticated_client):
        """Test lines 95-99 - Event not found handling in delete."""
        with patch("app.api.events.delete_event") as mock_delete:
            # Test event not found scenario (lines 95-99)
            mock_delete.return_value = {"success": False}
            
            response = authenticated_client.delete("/api/events/999")
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "Event with ID 999 not found" in response.json()["detail"]
    
    def test_delete_event_http_exception_handling(self, authenticated_client):
        """Test lines 100-101 - HTTPException handling in delete_event."""
        from fastapi import HTTPException, status
        
        with patch("app.api.events.delete_event") as mock_delete:
            # Test HTTPException re-raising (lines 100-101)
            mock_delete.side_effect = HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete event"
            )
            
            response = authenticated_client.delete("/api/events/1")
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert "Cannot delete event" in response.json()["detail"]
    
    def test_delete_event_general_exception_handling(self, authenticated_client):
        """Test lines 102-106 - General exception handling in delete_event."""
        with patch("app.api.events.delete_event") as mock_delete:
            # Test general Exception handling (lines 102-106)
            mock_delete.side_effect = Exception("Delete operation failed")
            
            response = authenticated_client.delete("/api/events/1")
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to delete event: Delete operation failed" in response.json()["detail"]


class TestEventsApiRequestBuilding:
    """Extract repeated request-building code into helpers."""
    
    @pytest.fixture
    def event_request_builder(self):
        """Helper for building event requests."""
        def _build_request(method, endpoint, **kwargs):
            headers = kwargs.pop('headers', {"Authorization": "Bearer test-token"})
            return {
                'method': method,
                'url': endpoint,
                'headers': headers,
                **kwargs
            }
        return _build_request
    
    def test_create_event_request_structure(self, authenticated_client, event_create_data, event_request_builder):
        """Test request structure for create event."""
        with patch("app.api.events.create_event") as mock_create:
            mock_create.return_value = {"success": True}
            
            request_data = event_request_builder('POST', '/api/events', json=event_create_data)
            response = authenticated_client.post(request_data['url'],
                                               json=request_data['json'],
                                               headers=request_data['headers'])
            
            assert response.status_code == status.HTTP_201_CREATED
            mock_create.assert_called_once()
    
    def test_get_user_events_with_filters(self, authenticated_client, event_request_builder):
        """Test get user events with various filter combinations."""
        with patch("app.api.events.get_events_by_user") as mock_get:
            mock_get.return_value = {"events": [], "total": 0}
            
            # Test with search_text and time_zone filters
            params = {
                "search_text": "meeting",
                "time_zone": "America/New_York"
            }
            
            response = authenticated_client.get("/api/events/user/1", params=params)
            assert response.status_code == status.HTTP_200_OK
            
            # Verify service was called with correct parameters
            mock_get.assert_called_once_with(1, "meeting", "America/New_York")


class TestEventsApiEdgeCases:
    """Test only edge cases that are actually relevant to the implementation."""
    
    def test_create_event_with_minimal_data(self, authenticated_client):
        """Test create event with minimal required data."""
        minimal_event = {
            "title": "Minimal Event",
            "start_time": "2023-01-01T00:00:00",
            "end_time": "2023-01-01T01:00:00"
        }
        
        with patch("app.api.events.create_event") as mock_create:
            mock_create.return_value = {"success": True, "event": minimal_event}
            
            response = authenticated_client.post("/api/events", json=minimal_event)
            assert response.status_code == status.HTTP_201_CREATED
    
    def test_get_user_events_without_filters(self, authenticated_client):
        """Test get user events without optional filters."""
        with patch("app.api.events.get_events_by_user") as mock_get:
            mock_get.return_value = {"events": [], "total": 0}
            
            response = authenticated_client.get("/api/events/user/1")
            assert response.status_code == status.HTTP_200_OK
            
            # Verify service was called with None for optional parameters
            mock_get.assert_called_once_with(1, None, None)