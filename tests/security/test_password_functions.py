"""
Password hashing and verification function tests.
Tests password hashing and verification functionality using bcrypt.
"""

import pytest
from unittest.mock import patch
import bcrypt

from app.core.security import get_password_hash, verify_password


class TestGetPasswordHash:
    """Test get_password_hash function."""
    
    def test_get_password_hash_returns_string(self):
        """Test that get_password_hash returns a string."""
        password = "testpassword123"
        result = get_password_hash(password)
        
        assert isinstance(result, str)
        assert result != password  # Should be different from original
    
    def test_get_password_hash_bcrypt_format(self):
        """Test that get_password_hash returns proper bcrypt format."""
        password = "testpassword123"
        result = get_password_hash(password)
        
        assert result.startswith("$2b$")
        assert len(result) > 50  # bcrypt hashes are typically 60 characters
    
    def test_get_password_hash_different_passwords_different_hashes(self):
        """Test that different passwords produce different hashes."""
        password1 = "password1"
        password2 = "password2"
        
        hash1 = get_password_hash(password1)
        hash2 = get_password_hash(password2)
        
        assert hash1 != hash2
    
    def test_get_password_hash_same_password_different_hashes(self):
        """Test that same password produces different hashes due to salt."""
        password = "testpassword123"
        
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Due to salt, same password should produce different hashes
        assert hash1 != hash2
    
    def test_get_password_hash_bcrypt_operations(self):
        """Test the actual bcrypt operations in get_password_hash."""
        with patch('bcrypt.gensalt') as mock_gensalt, \
             patch('bcrypt.hashpw') as mock_hashpw:
            
            # Setup mocks
            mock_salt = b'$2b$12$test_salt'
            mock_hashed = b'$2b$12$hashed_password'
            mock_gensalt.return_value = mock_salt
            mock_hashpw.return_value = mock_hashed
            
            result = get_password_hash("testpassword")
            
            # Verify bcrypt.gensalt() was called
            mock_gensalt.assert_called_once()
            
            # Verify bcrypt.hashpw() was called with correct parameters
            mock_hashpw.assert_called_once_with("testpassword".encode('utf-8'), mock_salt)
            
            # Verify return value
            assert result == mock_hashed.decode('utf-8')


class TestVerifyPassword:
    """Test verify_password function."""
    
    def test_verify_password_correct_password(self):
        """Test verify_password with correct password."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        result = verify_password(password, hashed)
        
        assert result is True
    
    def test_verify_password_incorrect_password(self):
        """Test verify_password with incorrect password."""
        password = "testpassword123"
        wrong_password = "wrongpassword456"
        hashed = get_password_hash(password)
        
        result = verify_password(wrong_password, hashed)
        
        assert result is False
    
    def test_verify_password_empty_password(self):
        """Test verify_password with empty password."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        result = verify_password("", hashed)
        
        assert result is False
    
    def test_verify_password_bcrypt_checkpw_operation(self):
        """Test the actual bcrypt.checkpw operation in verify_password."""
        with patch('bcrypt.checkpw') as mock_checkpw:
            mock_checkpw.return_value = True
            
            result = verify_password("plaintext", "hashed")
            
            # Verify bcrypt.checkpw was called with correct parameters
            mock_checkpw.assert_called_once_with(
                "plaintext".encode('utf-8'),
                "hashed".encode('utf-8')
            )
            
            assert result is True
    
    def test_verify_password_bcrypt_checkpw_false(self):
        """Test verify_password when bcrypt.checkpw returns False."""
        with patch('bcrypt.checkpw') as mock_checkpw:
            mock_checkpw.return_value = False
            
            result = verify_password("plaintext", "hashed")
            
            mock_checkpw.assert_called_once()
            assert result is False


class TestPasswordFunctionsIntegration:
    """Test integration between password functions."""
    
    def test_hash_and_verify_integration(self):
        """Test that hashed password can be verified correctly."""
        passwords = [
            "simple",
            "complex_password_123!",
            "with spaces and symbols @#$%",
            "unicode_password_ñáéíóú",
            "very_long_password_" * 10
        ]
        
        for password in passwords:
            hashed = get_password_hash(password)
            
            # Correct password should verify
            assert verify_password(password, hashed) is True
            
            # Incorrect password should not verify
            assert verify_password(password + "_wrong", hashed) is False
    
    def test_multiple_hashes_same_password_all_verify(self):
        """Test that multiple hashes of same password all verify correctly."""
        password = "testpassword123"
        
        # Generate multiple hashes
        hashes = [get_password_hash(password) for _ in range(5)]
        
        # All hashes should be different due to salt
        assert len(set(hashes)) == 5
        
        # All hashes should verify the original password
        for hashed in hashes:
            assert verify_password(password, hashed) is True
    
    def test_password_security_properties(self):
        """Test security properties of password functions."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        # Hash should not contain the original password
        assert password not in hashed
        
        # Hash should be significantly longer than password
        assert len(hashed) > len(password) * 2
        
        # Hash should start with bcrypt identifier
        assert hashed.startswith("$2b$")
        
        # Verification should work
        assert verify_password(password, hashed) is True