# tests/test_members_api.py
import pytest
from uuid import UUID
from fastapi import status, FastAPI, Depends
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.models.schemas import MemberDTO, UserMemberDto
from app.api.members import router as members_router
from app.core.security import get_current_user

# Mock the get_current_user dependency
def mock_get_current_user():
    return {"sub": "test-user-id", "email": "test@example.com"}

# Create a test app with the members router
@pytest.fixture
def test_app():
    app = FastAPI()
    # Override the dependencies
    app.dependency_overrides[get_current_user] = mock_get_current_user
    app.include_router(members_router)
    return app

@pytest.fixture
def authenticated_client(test_app):
    # Create a test client with the test app
    with TestClient(test_app) as client:
        yield client

# Test for getting a member by user ID
def test_get_member_by_user_id(authenticated_client):
    test_member = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "user_id": "550e8400-e29b-41d4-a716-446655440001",
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com"
    }
    
    with patch("app.api.members.get_member", return_value=test_member) as mock_get:
        user_id = "550e8400-e29b-41d4-a716-446655440001"
        response = authenticated_client.get(f"/api/members/{user_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert data["first_name"] == "Test"
        assert data["last_name"] == "User"
        assert data["email"] == "test@example.com"
        mock_get.assert_called_once_with(user_id)

# Test for getting a member by email
def test_get_member_by_email(authenticated_client):
    test_member = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "user_id": "550e8400-e29b-41d4-a716-446655440001",
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com"
    }
    
    with patch("app.api.members.get_member_by_email", return_value=test_member) as mock_get:
        response = authenticated_client.get("/api/members/email/test@example.com")
        
        # Print response for debugging
        print(response.json())
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "test@example.com"
        mock_get.assert_called_once_with("test@example.com")

# Test for creating a member
def test_create_member(authenticated_client):
    member_data = {
        "user_id": "550e8400-e29b-41d4-a716-446655440001",
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "phone": "+1234567890"
    }
    
    created_member = member_data.copy()
    created_member["id"] = "550e8400-e29b-41d4-a716-446655440000"
    created_member["created_at"] = "2023-01-01T00:00:00"
    created_member["updated_at"] = "2023-01-01T00:00:00"
    
    with patch("app.api.members.create_member", return_value=created_member) as mock_create:
        response = authenticated_client.post(
            "/api/members",
            json=member_data
        )
        
        # Print response for debugging
        print(response.json())
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert data["first_name"] == "Test"
        mock_create.assert_called_once()

# Test for deleting a member
def test_delete_member(authenticated_client):
    with patch("app.api.members.delete_member") as mock_delete:
        response = authenticated_client.delete("/api/members/550e8400-e29b-41d4-a716-446655440000")
        mock_delete.return_value = None
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Member deleted successfully"

# Test for getting relationships
def test_get_relationships(authenticated_client):
    test_relationships = [
        {"id": 1, "name": "Friend", "description": "Personal friend"},
        {"id": 2, "name": "Colleague", "description": "Work colleague"}
    ]
    
    with patch("app.api.members.get_relationships", return_value=test_relationships) as mock_get:
        response = authenticated_client.get("/api/members/relationships/list")
        
        # Print response for debugging
        print(response.json())
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Friend"
        mock_get.assert_called_once()

# Test for inviting a member
def test_invite_member(authenticated_client):
    invite_data = {
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "role": "member",
        "send_invite": True
    }
    
    invite_response = {"status": "invited", "email": "test@example.com"}
    
    with patch("app.api.members.invite_member", return_value=invite_response) as mock_invite:
        response = authenticated_client.post(
            "/api/members/invite",
            json=invite_data
        )
        
        # Print response for debugging
        print(response.json())
        
        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()
        assert data["status"] == "invited"
        assert data["email"] == "test@example.com"
        mock_invite.assert_called_once()


# Additional comprehensive tests

class TestMembersApiCoverage:
    """Test class focused on covering specific lines in members.py API endpoints."""
    
    @pytest.fixture
    def common_member_data(self):
        """Consolidate common mock data into fixtures."""
        return {
            "base_member": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "550e8400-e29b-41d4-a716-446655440001",
                "first_name": "Test",
                "last_name": "User",
                "email": "test@example.com",
                "phone": "+1234567890"
            },
            "member_dto": {
                "user_id": "550e8400-e29b-41d4-a716-446655440001",
                "first_name": "New",
                "last_name": "Member",
                "email": "new@example.com"
            },
            "user_member_dto": {
                "email": "invite@example.com",
                "first_name": "Invited",
                "last_name": "User",
                "role": "member",
                "send_invite": True
            }
        }
    
    def test_get_member_by_user_id_exception_handling(self, authenticated_client, common_member_data):
        """Test lines 23-24 - Exception handling in get_member_by_user_id."""
        with patch("app.api.members.get_member") as mock_get:
            # Test Exception handling (lines 23-24)
            mock_get.side_effect = Exception("Member not found")
            
            response = authenticated_client.get("/api/members/invalid-user-id")
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "Member not found" in response.json()["detail"]
    
    def test_get_member_by_user_id_success_return(self, authenticated_client, common_member_data):
        """Test line 22 - Successful return from get_member."""
        with patch("app.api.members.get_member") as mock_get:
            # Test successful return (line 22)
            mock_get.return_value = common_member_data["base_member"]
            
            user_id = "550e8400-e29b-41d4-a716-446655440001"
            response = authenticated_client.get(f"/api/members/{user_id}")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data == common_member_data["base_member"]
            mock_get.assert_called_once_with(user_id)
    
    def test_get_member_by_email_exception_handling(self, authenticated_client):
        """Test lines 36-37 - Exception handling in get_by_email."""
        with patch("app.api.members.get_member_by_email") as mock_get:
            # Test Exception handling (lines 36-37)
            mock_get.side_effect = Exception("Email not found")
            
            response = authenticated_client.get("/api/members/email/nonexistent@example.com")
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "Email not found" in response.json()["detail"]
    
    def test_get_member_by_email_success_return(self, authenticated_client, common_member_data):
        """Test line 35 - Successful return from get_member_by_email."""
        with patch("app.api.members.get_member_by_email") as mock_get:
            # Test successful return (line 35)
            mock_get.return_value = common_member_data["base_member"]
            
            email = "test@example.com"
            response = authenticated_client.get(f"/api/members/email/{email}")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data == common_member_data["base_member"]
            mock_get.assert_called_once_with(email)
    
    def test_create_member_exception_handling(self, authenticated_client, common_member_data):
        """Test lines 49-50 - Exception handling in create."""
        with patch("app.api.members.create_member") as mock_create:
            # Test Exception handling (lines 49-50)
            mock_create.side_effect = Exception("Creation failed")
            
            response = authenticated_client.post("/api/members", json=common_member_data["member_dto"])
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Creation failed" in response.json()["detail"]
    
    def test_create_member_success_return(self, authenticated_client, common_member_data):
        """Test line 48 - Successful return from create_member."""
        with patch("app.api.members.create_member") as mock_create:
            # Test successful return (line 48)
            created_member = {**common_member_data["member_dto"], "id": "new-member-id"}
            mock_create.return_value = created_member
            
            response = authenticated_client.post("/api/members", json=common_member_data["member_dto"])
            
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data == created_member
            mock_create.assert_called_once()
    
    def test_delete_member_exception_handling(self, authenticated_client):
        """Test lines 63-64 - Exception handling in delete."""
        with patch("app.api.members.delete_member") as mock_delete:
            # Test Exception handling (lines 63-64)
            mock_delete.side_effect = Exception("Delete failed")
            
            user_id = "550e8400-e29b-41d4-a716-446655440000"
            response = authenticated_client.delete(f"/api/members/{user_id}")
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "Delete failed" in response.json()["detail"]
    
    def test_delete_member_success_return(self, authenticated_client):
        """Test lines 61-62 - Successful delete operation."""
        with patch("app.api.members.delete_member") as mock_delete:
            # Test successful delete (lines 61-62)
            mock_delete.return_value = None
            
            user_id = "550e8400-e29b-41d4-a716-446655440000"
            response = authenticated_client.delete(f"/api/members/{user_id}")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "success"
            assert data["message"] == "Member deleted successfully"
            mock_delete.assert_called_once_with(user_id)
    
    def test_get_relationships_exception_handling(self, authenticated_client):
        """Test lines 75-76 - Exception handling in relationships."""
        with patch("app.api.members.get_relationships") as mock_get:
            # Test Exception handling (lines 75-76)
            mock_get.side_effect = Exception("Relationships service error")
            
            response = authenticated_client.get("/api/members/relationships/list")
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Relationships service error" in response.json()["detail"]
    
    def test_get_relationships_success_return(self, authenticated_client):
        """Test line 74 - Successful return from get_relationships."""
        with patch("app.api.members.get_relationships") as mock_get:
            # Test successful return (line 74)
            relationships = ["friend", "family", "colleague"]
            mock_get.return_value = relationships
            
            response = authenticated_client.get("/api/members/relationships/list")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data == relationships
            mock_get.assert_called_once()
    
    def test_invite_member_exception_handling(self, authenticated_client, common_member_data):
        """Test lines 88-89 - Exception handling in invite."""
        with patch("app.api.members.invite_member") as mock_invite:
            # Test Exception handling (lines 88-89)
            mock_invite.side_effect = Exception("Invitation failed")
            
            response = authenticated_client.post("/api/members/invite", json=common_member_data["user_member_dto"])
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Invitation failed" in response.json()["detail"]
    
    def test_invite_member_success_return(self, authenticated_client, common_member_data):
        """Test line 87 - Successful return from invite_member."""
        with patch("app.api.members.invite_member") as mock_invite:
            # Test successful return (line 87)
            invite_result = {"invited": True, "email": "invite@example.com"}
            mock_invite.return_value = invite_result
            
            response = authenticated_client.post("/api/members/invite", json=common_member_data["user_member_dto"])
            
            assert response.status_code == status.HTTP_202_ACCEPTED
            data = response.json()
            assert data == invite_result
            mock_invite.assert_called_once()


class TestMembersApiValidation:
    """Keep each test focused on a single scenario."""
    
    def test_get_member_with_valid_uuid(self, authenticated_client):
        """Test get member with valid UUID format."""
        with patch("app.api.members.get_member") as mock_get:
            mock_get.return_value = {"id": "test-id", "email": "test@example.com"}
            
            valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
            response = authenticated_client.get(f"/api/members/{valid_uuid}")
            
            assert response.status_code == status.HTTP_200_OK
            mock_get.assert_called_once_with(valid_uuid)
    
    def test_get_member_by_email_with_valid_email(self, authenticated_client):
        """Test get member by email with valid email format."""
        with patch("app.api.members.get_member_by_email") as mock_get:
            mock_get.return_value = {"email": "valid@example.com"}
            
            response = authenticated_client.get("/api/members/email/valid@example.com")
            
            assert response.status_code == status.HTTP_200_OK
            mock_get.assert_called_once_with("valid@example.com")
    
    def test_create_member_with_required_fields_only(self, authenticated_client):
        """Test create member with minimal required fields."""
        minimal_member = {
            "user_id": "550e8400-e29b-41d4-a716-446655440001",
            "first_name": "Min",
            "last_name": "Member",
            "email": "min@example.com"
        }
        
        with patch("app.api.members.create_member") as mock_create:
            mock_create.return_value = {**minimal_member, "id": "new-id"}
            
            response = authenticated_client.post("/api/members", json=minimal_member)
            
            assert response.status_code == status.HTTP_201_CREATED
            mock_create.assert_called_once()
    
    def test_invite_member_with_minimal_data(self, authenticated_client):
        """Test invite member with minimal required data."""
        minimal_invite = {
            "email": "minimal@example.com",
            "first_name": "Min",
            "last_name": "Invite"
        }
        
        with patch("app.api.members.invite_member") as mock_invite:
            mock_invite.return_value = {"invited": True}
            
            response = authenticated_client.post("/api/members/invite", json=minimal_invite)
            
            assert response.status_code == status.HTTP_202_ACCEPTED
            mock_invite.assert_called_once()


class TestMembersApiEdgeCases:
    """Skip tests for unused member logic, focus on implemented features."""
    
    def test_delete_member_returns_success_message(self, authenticated_client):
        """Test that delete member returns proper success message structure."""
        with patch("app.api.members.delete_member") as mock_delete:
            mock_delete.return_value = None
            
            response = authenticated_client.delete("/api/members/test-id")
            
            assert response.status_code == status.HTTP_200_OK
            # Verify the response structure matches lines 61-62
            data = response.json()
            assert "status" in data
            assert "message" in data
            assert data["status"] == "success"
    
    def test_relationships_endpoint_returns_list(self, authenticated_client):
        """Test that relationships endpoint returns a list structure."""
        with patch("app.api.members.get_relationships") as mock_get:
            mock_get.return_value = ["friend", "family"]
            
            response = authenticated_client.get("/api/members/relationships/list")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 2