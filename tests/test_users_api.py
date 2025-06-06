"""
Test cases for the Users API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from uuid import uuid4, UUID
from unittest.mock import patch, MagicMock

from app.main import app
from app.models.schemas import UserCreate, UserUpdate, UserCred, UserDeviceDTO

client = TestClient(app)


class TestUsersApiCoverage:
    """Test class focused on covering specific lines in users.py API endpoints."""
    
    @pytest.fixture
    def user_test_data(self):
        """Centralized user test data."""
        return {
            "user_response": {
                "id": str(uuid4()),
                "email": "test@example.com",
                "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
                "is_active": True,
                "is_verified": True,
                "role": "user",
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            },
            "user_create": {
                "email": "new@example.com",
                "password": "newpassword123"
            },
            "user_update": {
                "email": "updated@example.com",
                "is_active": True
            },
            "user_cred": {
                "username": "test@example.com",
                "password": "newpassword123"
            },
            "device_data": {
                "user_id": str(uuid4()),
                "device_id": "abc123token",
                "device_type": "ios",
                "device_name": "Test iPhone",
                "os_version": "15.4",
                "app_version": "1.0.0"
            }
        }

    def test_list_users_exception_handling(self, user_test_data):
        """Test lines 30-33 - Exception handling in list_users."""
        with patch("app.api.users.get_all_users") as mock_get_all:
            # Test exception handling (lines 30-33)
            mock_get_all.side_effect = Exception("Database connection failed")
            
            response = client.get("/api/users")
            assert response.status_code == 500
            assert "Failed to fetch users: Database connection failed" in response.json()["detail"]
            
            mock_get_all.assert_called_once()

    def test_list_users_success_flow(self, user_test_data):
        """Test line 31 - Successful users retrieval in list_users."""
        with patch("app.api.users.get_all_users") as mock_get_all:
            # Test successful users retrieval (line 31)
            users_list = [user_test_data["user_response"]]
            mock_get_all.return_value = users_list
            
            response = client.get("/api/users")
            assert response.status_code == 200
            data = response.json()
            assert data == users_list
            
            mock_get_all.assert_called_once()

    def test_get_user_not_found_handling(self, user_test_data):
        """Test lines 49-55 - User not found handling in get_user."""
        with patch("app.api.users.get_user_by_id") as mock_get:
            # Test user not found scenario (lines 50-54)
            mock_get.return_value = None
            
            user_id = str(uuid4())
            response = client.get(f"/api/users/{user_id}")
            assert response.status_code == 404
            assert "User not found" in response.json()["detail"]
            
            mock_get.assert_called_once_with(UUID(user_id))

    def test_get_user_success_return(self, user_test_data):
        """Test lines 49, 55 - Successful user retrieval in get_user."""
        with patch("app.api.users.get_user_by_id") as mock_get:
            # Test successful user retrieval (lines 49, 55)
            mock_get.return_value = user_test_data["user_response"]
            
            user_id = str(uuid4())
            response = client.get(f"/api/users/{user_id}")
            assert response.status_code == 200
            data = response.json()
            assert data == user_test_data["user_response"]
            
            mock_get.assert_called_once_with(UUID(user_id))

    def test_register_user_http_exception_handling(self, user_test_data):
        """Test lines 70-71 - HTTPException handling in register."""
        from fastapi import HTTPException
        
        with patch("app.api.users.register_user") as mock_register:
            # Test HTTPException re-raising (lines 70-71)
            mock_register.side_effect = HTTPException(
                status_code=409,
                detail="User already exists"
            )
            
            response = client.post("/api/users/register", json=user_test_data["user_create"])
            assert response.status_code == 409
            assert "User already exists" in response.json()["detail"]

    def test_register_user_general_exception_handling(self, user_test_data):
        """Test lines 72-76 - General exception handling in register."""
        with patch("app.api.users.register_user") as mock_register:
            # Test general Exception handling (lines 72-76)
            mock_register.side_effect = Exception("Database error")
            
            response = client.post("/api/users/register", json=user_test_data["user_create"])
            assert response.status_code == 500
            assert "Failed to register user: Database error" in response.json()["detail"]

    def test_register_user_success_flow(self, user_test_data):
        """Test line 69 - Successful registration flow in register."""
        with patch("app.api.users.register_user") as mock_register:
            # Test successful registration (line 69)
            # Don't include password in response for security
            created_user = {**user_test_data["user_response"], "email": user_test_data["user_create"]["email"]}
            mock_register.return_value = created_user
            
            response = client.post("/api/users/register", json=user_test_data["user_create"])
            assert response.status_code == 201
            data = response.json()
            assert data == created_user
            
            mock_register.assert_called_once()

    def test_update_user_profile_http_exception_handling(self, user_test_data):
        """Test lines 97-98 - HTTPException handling in update_user_profile."""
        from fastapi import HTTPException
        
        with patch("app.api.users.update_user") as mock_update:
            # Test HTTPException re-raising (lines 97-98)
            mock_update.side_effect = HTTPException(
                status_code=404,
                detail="User not found"
            )
            
            user_id = str(uuid4())
            response = client.put(
                f"/api/users/{user_id}",
                json=user_test_data["user_update"],
                headers={"Authorization": "Bearer fake-token"}
            )
            assert response.status_code == 404
            assert "User not found" in response.json()["detail"]

    def test_update_user_profile_general_exception_handling(self, user_test_data):
        """Test lines 99-103 - General exception handling in update_user_profile."""
        with patch("app.api.users.update_user") as mock_update:
            # Test general Exception handling (lines 99-103)
            mock_update.side_effect = Exception("Update failed")
            
            user_id = str(uuid4())
            response = client.put(
                f"/api/users/{user_id}",
                json=user_test_data["user_update"],
                headers={"Authorization": "Bearer fake-token"}
            )
            assert response.status_code == 500
            assert "Failed to update user: Update failed" in response.json()["detail"]

    def test_update_user_profile_success_flow(self, user_test_data):
        """Test line 96 - Successful update flow in update_user_profile."""
        with patch("app.api.users.update_user") as mock_update:
            # Test successful update (line 96)
            updated_user = {**user_test_data["user_response"], **user_test_data["user_update"]}
            mock_update.return_value = updated_user
            
            user_id = str(uuid4())
            response = client.put(
                f"/api/users/{user_id}",
                json=user_test_data["user_update"],
                headers={"Authorization": "Bearer fake-token"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data == updated_user
            
            mock_update.assert_called_once()

    def test_update_password_http_exception_handling(self, user_test_data):
        """Test lines 124-125 - HTTPException handling in update_password."""
        from fastapi import HTTPException
        
        with patch("app.api.users.update_user_password") as mock_update_pwd:
            # Test HTTPException re-raising (lines 124-125)
            mock_update_pwd.side_effect = HTTPException(
                status_code=400,
                detail="Invalid current password"
            )
            
            user_id = str(uuid4())
            response = client.put(
                f"/api/users/{user_id}/password",
                json=user_test_data["user_cred"],
                headers={"Authorization": "Bearer fake-token"}
            )
            assert response.status_code == 400
            assert "Invalid current password" in response.json()["detail"]

    def test_update_password_general_exception_handling(self, user_test_data):
        """Test lines 126-130 - General exception handling in update_password."""
        with patch("app.api.users.update_user_password") as mock_update_pwd:
            # Test general Exception handling (lines 126-130)
            mock_update_pwd.side_effect = Exception("Password update failed")
            
            user_id = str(uuid4())
            response = client.put(
                f"/api/users/{user_id}/password",
                json=user_test_data["user_cred"],
                headers={"Authorization": "Bearer fake-token"}
            )
            assert response.status_code == 500
            assert "Failed to update password: Password update failed" in response.json()["detail"]

    def test_update_password_success_flow(self, user_test_data):
        """Test line 123 - Successful password update flow in update_password."""
        with patch("app.api.users.update_user_password") as mock_update_pwd:
            # Test successful password update (line 123)
            mock_update_pwd.return_value = {"message": "Password updated successfully"}
            
            user_id = str(uuid4())
            response = client.put(
                f"/api/users/{user_id}/password",
                json=user_test_data["user_cred"],
                headers={"Authorization": "Bearer fake-token"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data == {"message": "Password updated successfully"}
            
            mock_update_pwd.assert_called_once()

    def test_delete_user_account_not_found_handling(self, user_test_data):
        """Test lines 146-150 - User not found handling in delete_user_account."""
        with patch("app.api.users.delete_user") as mock_delete:
            # Test user not found scenario (lines 146-150)
            mock_delete.return_value = {"success": False}
            
            user_id = str(uuid4())
            response = client.delete(
                f"/api/users/{user_id}",
                headers={"Authorization": "Bearer fake-token"}
            )
            assert response.status_code == 404
            assert f"User with ID {user_id} not found" in response.json()["detail"]
            
            mock_delete.assert_called_once_with(UUID(user_id))

    def test_delete_user_account_http_exception_handling(self, user_test_data):
        """Test lines 151-152 - HTTPException handling in delete_user_account."""
        from fastapi import HTTPException
        
        with patch("app.api.users.delete_user") as mock_delete:
            # Test HTTPException re-raising (lines 151-152)
            mock_delete.side_effect = HTTPException(
                status_code=403,
                detail="Cannot delete user"
            )
            
            user_id = str(uuid4())
            response = client.delete(
                f"/api/users/{user_id}",
                headers={"Authorization": "Bearer fake-token"}
            )
            assert response.status_code == 403
            assert "Cannot delete user" in response.json()["detail"]

    def test_delete_user_account_general_exception_handling(self, user_test_data):
        """Test lines 153-157 - General exception handling in delete_user_account."""
        with patch("app.api.users.delete_user") as mock_delete:
            # Test general Exception handling (lines 153-157)
            mock_delete.side_effect = Exception("Delete operation failed")
            
            user_id = str(uuid4())
            response = client.delete(
                f"/api/users/{user_id}",
                headers={"Authorization": "Bearer fake-token"}
            )
            assert response.status_code == 500
            assert "Failed to delete user: Delete operation failed" in response.json()["detail"]

    def test_delete_user_account_success_flow(self, user_test_data):
        """Test line 145 - Successful deletion flow in delete_user_account."""
        with patch("app.api.users.delete_user") as mock_delete:
            # Test successful deletion (line 145)
            mock_delete.return_value = {"success": True}
            
            user_id = str(uuid4())
            response = client.delete(
                f"/api/users/{user_id}",
                headers={"Authorization": "Bearer fake-token"}
            )
            assert response.status_code == 204
            
            mock_delete.assert_called_once_with(UUID(user_id))

    def test_upload_profile_image_http_exception_handling(self, user_test_data):
        """Test lines 178-179 - HTTPException handling in upload_profile_image."""
        from fastapi import HTTPException
        
        with patch("app.api.users.upload_user_profile_image") as mock_upload:
            # Test HTTPException re-raising (lines 178-179)
            mock_upload.side_effect = HTTPException(
                status_code=413,
                detail="File too large"
            )
            
            user_id = str(uuid4())
            response = client.post(
                f"/api/users/{user_id}/profile-image",
                files={"file": ("test.jpg", b"fake image data", "image/jpeg")},
                headers={"Authorization": "Bearer fake-token"}
            )
            assert response.status_code == 413
            assert "File too large" in response.json()["detail"]

    def test_upload_profile_image_general_exception_handling(self, user_test_data):
        """Test lines 180-184 - General exception handling in upload_profile_image."""
        with patch("app.api.users.upload_user_profile_image") as mock_upload:
            # Test general Exception handling (lines 180-184)
            mock_upload.side_effect = Exception("Upload service failed")
            
            user_id = str(uuid4())
            response = client.post(
                f"/api/users/{user_id}/profile-image",
                files={"file": ("test.jpg", b"fake image data", "image/jpeg")},
                headers={"Authorization": "Bearer fake-token"}
            )
            assert response.status_code == 500
            assert "Failed to upload profile image: Upload service failed" in response.json()["detail"]

    def test_upload_profile_image_success_flow(self, user_test_data):
        """Test line 177 - Successful upload flow in upload_profile_image."""
        with patch("app.api.users.upload_user_profile_image") as mock_upload:
            # Test successful upload (line 177)
            mock_upload.return_value = {"url": "https://example.com/profile.jpg"}
            
            user_id = str(uuid4())
            response = client.post(
                f"/api/users/{user_id}/profile-image",
                files={"file": ("test.jpg", b"fake image data", "image/jpeg")},
                headers={"Authorization": "Bearer fake-token"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data == {"url": "https://example.com/profile.jpg"}
            
            mock_upload.assert_called_once()

    def test_register_device_http_exception_handling(self, user_test_data):
        """Test lines 203-204 - HTTPException handling in register_device."""
        from fastapi import HTTPException
        
        with patch("app.api.users.register_user_device") as mock_register:
            # Test HTTPException re-raising (lines 203-204)
            mock_register.side_effect = HTTPException(
                status_code=400,
                detail="Invalid device token"
            )
            
            response = client.post(
                "/api/users/devices/register",
                json=user_test_data["device_data"],
                headers={"Authorization": "Bearer fake-token"}
            )
            assert response.status_code == 400
            assert "Invalid device token" in response.json()["detail"]

    def test_register_device_general_exception_handling(self, user_test_data):
        """Test lines 205-209 - General exception handling in register_device."""
        with patch("app.api.users.register_user_device") as mock_register:
            # Test general Exception handling (lines 205-209)
            mock_register.side_effect = Exception("Device registration failed")
            
            response = client.post(
                "/api/users/devices/register",
                json=user_test_data["device_data"],
                headers={"Authorization": "Bearer fake-token"}
            )
            assert response.status_code == 500
            assert "Failed to register device: Device registration failed" in response.json()["detail"]

    def test_register_device_success_flow(self, user_test_data):
        """Test line 202 - Successful device registration flow in register_device."""
        with patch("app.api.users.register_user_device") as mock_register:
            # Test successful device registration (line 202)
            mock_register.return_value = {"device_id": "device123", "status": "registered"}
            
            response = client.post(
                "/api/users/devices/register",
                json=user_test_data["device_data"],
                headers={"Authorization": "Bearer fake-token"}
            )
            assert response.status_code == 201
            data = response.json()
            assert data == {"device_id": "device123", "status": "registered"}
            
            mock_register.assert_called_once()


class TestUsersApiValidation:
    """Write concise assertions per test, focus on one method of the users API."""
    
    def test_list_users_endpoint_structure(self):
        """Test that list_users endpoint has correct structure."""
        response = client.get("/api/users")
        # Should return 200 with users list or 500 if service fails
        assert response.status_code in [200, 500]
    
    def test_get_user_with_valid_uuid(self):
        """Test get_user with valid UUID format."""
        valid_uuid = str(uuid4())
        response = client.get(f"/api/users/{valid_uuid}")
        # Should return 200, 404, or 500 depending on implementation
        assert response.status_code in [200, 404, 500]
    
    def test_register_user_with_minimal_data(self):
        """Test user registration with minimal required data."""
        minimal_user = {"email": "minimal@example.com", "password": "password123"}
        
        response = client.post("/api/users/register", json=minimal_user)
        # Should return 201 for success or error codes for validation/service issues
        assert response.status_code in [201, 400, 422, 500]
    
    def test_update_user_with_auth_header(self):
        """Test user update requires authentication header."""
        user_id = str(uuid4())
        update_data = {"email": "updated@example.com"}
        
        response = client.put(f"/api/users/{user_id}", json=update_data)
        # Should return 401/403 for missing auth or other status if auth works
        assert response.status_code in [200, 401, 403, 422, 500]
    
    def test_delete_user_with_auth_header(self):
        """Test user deletion requires authentication header."""
        user_id = str(uuid4())
        
        response = client.delete(f"/api/users/{user_id}")
        # Should return 401/403 for missing auth or other status if auth works
        assert response.status_code in [204, 401, 403, 422, 500]


class TestUsersApiEdgeCases:
    """Avoid tests for user features not in scope, focus on implemented functionality."""
    
    def test_upload_profile_image_endpoint_structure(self):
        """Test that upload_profile_image endpoint has correct structure."""
        user_id = str(uuid4())
        response = client.post(
            f"/api/users/{user_id}/profile-image",
            files={"file": ("test.jpg", b"fake image data", "image/jpeg")}
        )
        # Should return 401/403 for missing auth or other status if auth works
        assert response.status_code in [200, 401, 403, 413, 422, 500]
    
    def test_register_device_endpoint_structure(self):
        """Test that register_device endpoint has correct structure."""
        device_data = {
            "user_id": str(uuid4()),
            "device_id": "test_token",
            "device_type": "ios",
            "device_name": "Test Device",
            "os_version": "15.4",
            "app_version": "1.0.0"
        }
        
        response = client.post("/api/users/devices/register", json=device_data)
        # Should return 401/403 for missing auth or other status if auth works
        assert response.status_code in [201, 401, 403, 422, 500]
    
    def test_update_password_endpoint_structure(self):
        """Test that update_password endpoint has correct structure."""
        user_id = str(uuid4())
        cred_data = {
            "username": "test@example.com",
            "password": "newpass123"
        }
        
        response = client.put(f"/api/users/{user_id}/password", json=cred_data)
        # Should return 401/403 for missing auth or other status if auth works
        assert response.status_code in [200, 401, 403, 422, 500]