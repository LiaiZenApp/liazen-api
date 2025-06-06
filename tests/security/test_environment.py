"""
Environment and configuration tests.
Tests environment variable handling, configuration validation, and environment-specific behavior.
"""

import pytest
import os
import sys
from unittest.mock import patch

from app.core.security import TEST_ENV, Auth0JWTBearer, auth0_scheme
from tests.security.fixtures import SecurityTestFixtures


class TestEnvironmentVariables:
    """Test environment variable handling."""
    
    def test_test_env_variable_consistency(self):
        """Test that TEST_ENV variable is consistent with settings."""
        from app.core.security import TEST_ENV
        from app.core.config import settings
        
        assert TEST_ENV == (settings.ENV == 'test')
    
    def test_test_env_variable_is_boolean(self):
        """Test that TEST_ENV is a boolean value."""
        assert isinstance(TEST_ENV, bool)
    
    def test_test_env_logic_with_different_settings(self):
        """Test TEST_ENV logic with different settings values."""
        from app.core.config import settings
        
        # Test that TEST_ENV is based on settings.ENV
        if settings.ENV == 'test':
            assert TEST_ENV is True
        else:
            assert TEST_ENV is False


class TestAuthSchemeEnvironmentBehavior:
    """Test auth scheme behavior in different environments."""
    
    def test_auth_scheme_test_environment(self):
        """Test auth0_scheme is MockAuth0JWTBearer in test environment."""
        # Since we're in test environment, auth0_scheme should be MockAuth0JWTBearer
        from app.core.security import auth0_scheme
        
        assert auth0_scheme.__class__.__name__ == 'MockAuth0JWTBearer'
    
    def test_auth_scheme_production_environment_logic(self):
        """Test auth0_scheme creation logic for production environment."""
        # Test the class instantiation logic rather than module-level variable
        with patch('app.core.security.TEST_ENV', False), \
             patch('requests.get') as mock_get:
            
            mock_response = SecurityTestFixtures.create_mock_response()
            mock_get.return_value = mock_response
            
            bearer = Auth0JWTBearer()
            assert isinstance(bearer, Auth0JWTBearer)
    
    def test_auth_scheme_type_consistency(self):
        """Test that auth0_scheme type is consistent with environment."""
        from app.core.security import auth0_scheme, TEST_ENV
        
        if TEST_ENV:
            assert auth0_scheme.__class__.__name__ == 'MockAuth0JWTBearer'
        else:
            assert auth0_scheme.__class__.__name__ == 'Auth0JWTBearer'


class TestEnvironmentSwitching:
    """Test behavior when switching between environments."""
    
    def setup_method(self):
        """Set up for environment switching tests."""
        # Store original environment
        self.original_env = os.environ.get('ENV', 'test')
        
        # Clear any cached modules
        modules_to_clear = [
            'app.core.security',
            'app.core.config'
        ]
        for module in modules_to_clear:
            if module in sys.modules:
                del sys.modules[module]
    
    def teardown_method(self):
        """Clean up after environment switching tests."""
        # Restore original environment
        os.environ['ENV'] = self.original_env
        
        # Clear cached modules
        modules_to_clear = [
            'app.core.security',
            'app.core.config'
        ]
        for module in modules_to_clear:
            if module in sys.modules:
                del sys.modules[module]
    
    def test_test_environment_behavior(self):
        """Test behavior in test environment."""
        os.environ['ENV'] = 'test'
        
        # Import fresh modules
        from app.core.security import TEST_ENV, auth0_scheme
        
        assert TEST_ENV is True
        assert auth0_scheme.__class__.__name__ == 'MockAuth0JWTBearer'
    
    def test_production_environment_behavior(self):
        """Test behavior in production environment."""
        os.environ['ENV'] = 'production'
        
        with patch('requests.get') as mock_get:
            mock_response = SecurityTestFixtures.create_mock_response()
            mock_get.return_value = mock_response
            
            # Import fresh modules
            from app.core.security import TEST_ENV, auth0_scheme
            
            assert TEST_ENV is False
            assert auth0_scheme.__class__.__name__ == 'Auth0JWTBearer'
    
    def test_development_environment_behavior(self):
        """Test behavior in development environment."""
        os.environ['ENV'] = 'development'
        
        with patch('requests.get') as mock_get:
            mock_response = SecurityTestFixtures.create_mock_response()
            mock_get.return_value = mock_response
            
            # Import fresh modules
            from app.core.security import TEST_ENV, auth0_scheme
            
            assert TEST_ENV is False  # Only 'test' should be True
            assert auth0_scheme.__class__.__name__ == 'Auth0JWTBearer'


class TestConfigurationValidation:
    """Test configuration validation and consistency."""
    
    def test_auth0_configuration_exists(self):
        """Test that Auth0 configuration exists."""
        from app.core.config import settings
        
        # These should be defined in settings
        assert hasattr(settings, 'AUTH0_DOMAIN')
        assert hasattr(settings, 'AUTH0_AUDIENCE')
        assert hasattr(settings, 'AUTH0_CLIENT_ID')
        assert hasattr(settings, 'AUTH0_CLIENT_SECRET')
    
    def test_auth0_configuration_not_empty(self):
        """Test that Auth0 configuration is not empty."""
        from app.core.config import settings
        
        # In test environment, these might be test values
        if settings.ENV != 'test':
            assert settings.AUTH0_DOMAIN
            assert settings.AUTH0_AUDIENCE
            assert settings.AUTH0_CLIENT_ID
            assert settings.AUTH0_CLIENT_SECRET
    
    def test_jwt_configuration_exists(self):
        """Test that JWT configuration exists."""
        from app.core.config import settings
        
        assert hasattr(settings, 'SECRET_KEY')
        assert hasattr(settings, 'JWT_ALGORITHM')
        assert hasattr(settings, 'ACCESS_TOKEN_EXPIRE_MINUTES')
    
    def test_environment_specific_behavior(self):
        """Test environment-specific behavior configuration."""
        from app.core.config import settings
        from app.core.security import TEST_ENV
        
        # TEST_ENV should match settings.ENV
        expected_test_env = (settings.ENV == 'test')
        assert TEST_ENV == expected_test_env
        
        # Different environments should have different behaviors
        if settings.ENV == 'test':
            # Test environment should use mock authentication
            assert TEST_ENV is True
        elif settings.ENV in ['production', 'staging']:
            # Production environments should use real authentication
            assert TEST_ENV is False
        elif settings.ENV == 'development':
            # Development might use real or mock authentication
            assert isinstance(TEST_ENV, bool)


class TestEnvironmentIsolation:
    """Test that environment changes don't affect other tests."""
    
    def test_environment_isolation_test_to_prod(self):
        """Test isolation when switching from test to production."""
        # Start in test environment
        with patch('app.core.security.TEST_ENV', True):
            from app.core.security import auth0_scheme as test_scheme
            assert test_scheme.__class__.__name__ == 'MockAuth0JWTBearer'
        
        # Switch to production environment
        with patch('app.core.security.TEST_ENV', False), \
             patch('requests.get') as mock_get:
            
            mock_response = SecurityTestFixtures.create_mock_response()
            mock_get.return_value = mock_response
            
            # Create new instance for production
            prod_bearer = Auth0JWTBearer()
            assert isinstance(prod_bearer, Auth0JWTBearer)
    
    def test_environment_isolation_prod_to_test(self):
        """Test isolation when switching from production to test."""
        # Start in production environment
        with patch('app.core.security.TEST_ENV', False), \
             patch('requests.get') as mock_get:
            
            mock_response = SecurityTestFixtures.create_mock_response()
            mock_get.return_value = mock_response
            
            prod_bearer = Auth0JWTBearer()
            assert isinstance(prod_bearer, Auth0JWTBearer)
        
        # Switch to test environment
        with patch('app.core.security.TEST_ENV', True):
            from app.core.security import MockAuth0JWTBearer
            test_bearer = MockAuth0JWTBearer()
            assert isinstance(test_bearer, MockAuth0JWTBearer)
    
    def test_concurrent_environment_handling(self):
        """Test handling of concurrent environment configurations."""
        # Test that different instances can coexist
        from app.core.security import MockAuth0JWTBearer
        test_bearer = MockAuth0JWTBearer()
        
        with patch('requests.get') as mock_get:
            mock_response = SecurityTestFixtures.create_mock_response()
            mock_get.return_value = mock_response
            
            with patch('app.core.security.TEST_ENV', False):
                prod_bearer = Auth0JWTBearer()
        
        # Both should maintain their types
        assert isinstance(test_bearer, MockAuth0JWTBearer)
        assert isinstance(prod_bearer, Auth0JWTBearer)