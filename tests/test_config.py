"""Tests for the application configuration."""
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.core.config import Settings, settings


def test_default_settings():
    """Test that default settings are correctly set."""
    # Create a new Settings instance without loading .env
    with patch.dict(os.environ, clear=True):
        test_settings = Settings()
        
        # Test default values
    assert test_settings.ENV == "test"
    assert test_settings.DEBUG is False
    assert test_settings.HOST == "0.0.0.0"
    assert test_settings.PORT == 8000
    assert test_settings.RELOAD is True
    assert test_settings.ALLOWED_ORIGINS == "*"
    assert test_settings.DATABASE_URL == "sqlite:///./test.db"
    assert test_settings.SECRET_KEY == "your-secret-key-here"
    assert test_settings.JWT_ALGORITHM == "HS256"
    assert test_settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30
    assert test_settings.REFRESH_TOKEN_EXPIRE_DAYS == 7
    assert test_settings.BCRYPT_ROUNDS == 12
    assert test_settings.UPLOAD_DIR == "uploads"
    assert test_settings.MAX_UPLOAD_SIZE == 5 * 1024 * 1024  # 5MB
    assert test_settings.LOG_LEVEL == "INFO"
    assert test_settings.APP_NAME == "LiaiZen API"
    assert test_settings.APP_VERSION == "1.0.0"


def test_environment_variables_override_defaults():
    """Test that environment variables override default settings."""
    env_vars = {
        "ENV": "test",
        "DEBUG": "True",
        "HOST": "127.0.0.1",
        "PORT": "8080",
        "ALLOWED_ORIGINS": "http://localhost:3000"
    }
    
    with patch.dict(os.environ, env_vars):
        test_settings = Settings()
        
        assert test_settings.ENV == "test"
        assert test_settings.DEBUG is True
        assert test_settings.HOST == "127.0.0.1"
        assert test_settings.PORT == 8080
        assert test_settings.ALLOWED_ORIGINS == "http://localhost:3000"


def test_environment_helper_properties():
    """Test the environment helper properties."""
    # Test development environment
    with patch.dict(os.environ, {"ENV": "development"}):
        test_settings = Settings()
        assert test_settings.is_development is True
        assert test_settings.is_test is False
        assert test_settings.is_production is False
    
    # Test test environment
    with patch.dict(os.environ, {"ENV": "test"}):
        test_settings = Settings()
        assert test_settings.is_test is True
        assert test_settings.is_development is True  # test environment is considered development
        assert test_settings.is_production is False
    
    # Test production environment
    with patch.dict(os.environ, {"ENV": "production"}):
        test_settings = Settings()
        assert test_settings.is_production is True
        assert test_settings.is_development is False
        assert test_settings.is_test is False


def test_database_url_property():
    """Test the database_url property based on environment."""
    # Test in test environment
    with patch.dict(os.environ, {"ENV": "test", "TEST_DATABASE_URL": "sqlite:///test_db.sqlite"}):
        test_settings = Settings()
        assert test_settings.database_url == "sqlite:///test_db.sqlite"
    
    # Test in non-test environment (development)
    with patch.dict(os.environ, {"ENV": "development", "DATABASE_URL": "sqlite:///dev_db.sqlite"}):
        test_settings = Settings()
        assert test_settings.database_url == "sqlite:///dev_db.sqlite"


def test_auth0_url_properties():
    """Test the Auth0 URL properties."""
    with patch.dict(os.environ, {
        "AUTH0_DOMAIN": "test.auth0.com",
        "AUTH0_AUDIENCE": "test-audience",
        "AUTH0_ISSUER": "https://custom-issuer.com/"
    }):
        test_settings = Settings()
        
        # Test with custom issuer
        assert test_settings.auth0_issuer == "https://custom-issuer.com/"
        
        # Test Auth0 URLs
        assert test_settings.auth0_jwks_uri == "https://test.auth0.com/.well-known/jwks.json"
        assert test_settings.auth0_authorization_url == "https://test.auth0.com/authorize"
        assert test_settings.auth0_token_url == "https://test.auth0.com/oauth/token"
        assert test_settings.auth0_userinfo_url == "https://test.auth0.com/userinfo"
    
    # Test with default issuer
    with patch.dict(os.environ, {
        "AUTH0_DOMAIN": "test.auth0.com",
        "AUTH0_AUDIENCE": "test-audience"
    }):
        test_settings = Settings()
        assert test_settings.auth0_issuer == "https://test.auth0.com/"


@patch('app.core.config.load_dotenv')
@patch('app.core.config.os.getenv')
@patch('app.core.config.Path')
def test_settings_customise_sources(mock_path, mock_getenv, mock_load_dotenv):
    """Test the settings_customise_sources class method."""
    # Setup mocks
    mock_path_instance = MagicMock()
    mock_path.return_value = mock_path_instance
    mock_path_instance.exists.return_value = True
    mock_getenv.return_value = "test"
    
    # Call the method directly
    result = Settings.settings_customise_sources(
        settings_cls=Settings,
        init_settings=MagicMock(),
        env_settings=MagicMock(),
        dotenv_settings=MagicMock(),
        file_secret_settings=MagicMock()
    )
    
    # Assertions
    mock_getenv.assert_called_with("ENV")
    # The method calls Path() twice - once for .env.test and once for checking if it exists
    assert mock_path.call_count >= 1
    mock_load_dotenv.assert_called_with(".env.test", override=True)
    assert len(result) == 4  # Should return a tuple of 4 items


def test_required_auth0_fields():
    """Test that required Auth0 fields are properly set and validated."""
    # Test that all required fields are present in the model
    required_fields = {"AUTH0_DOMAIN", "AUTH0_CLIENT_ID", 
                      "AUTH0_CLIENT_SECRET", "AUTH0_AUDIENCE"}
    
    # Check that all required fields are defined in the Settings class
    settings_fields = Settings.model_fields
    for field in required_fields:
        assert field in settings_fields, f"{field} is not defined in Settings"
    
    # Test that we can create Settings with all required fields
    env_vars = {
        "AUTH0_DOMAIN": "test.auth0.com",
        "AUTH0_CLIENT_ID": "test-client-id",
        "AUTH0_CLIENT_SECRET": "test-client-secret",
        "AUTH0_AUDIENCE": "test-audience"
    }
    
    with patch.dict(os.environ, env_vars, clear=True):
        settings = Settings()
        for field in required_fields:
            assert getattr(settings, field) == env_vars[field], f"{field} was not set correctly"


# Additional comprehensive tests

class TestConfigCoverage:
    """Test class focused on covering specific lines in config.py."""
    
    def test_is_production_property_line_71(self):
        """Test line 71 - is_production property returns True for production environment."""
        with patch.dict(os.environ, {"ENV": "production"}):
            test_settings = Settings()
            # Test line 71: return self.ENV.lower() == "production"
            assert test_settings.is_production is True
            assert test_settings.ENV.lower() == "production"
    
    def test_is_production_property_false_cases(self):
        """Test line 71 - is_production property returns False for non-production environments."""
        # Test with development environment
        with patch.dict(os.environ, {"ENV": "development"}):
            test_settings = Settings()
            # Test line 71: return self.ENV.lower() == "production"
            assert test_settings.is_production is False
            assert test_settings.ENV.lower() != "production"
        
        # Test with test environment
        with patch.dict(os.environ, {"ENV": "test"}):
            test_settings = Settings()
            # Test line 71: return self.ENV.lower() == "production"
            assert test_settings.is_production is False
            assert test_settings.ENV.lower() != "production"
        
        # Test with custom environment
        with patch.dict(os.environ, {"ENV": "staging"}):
            test_settings = Settings()
            # Test line 71: return self.ENV.lower() == "production"
            assert test_settings.is_production is False
            assert test_settings.ENV.lower() != "production"

    @patch('app.core.config.Path')
    @patch('app.core.config.load_dotenv')
    @patch('app.core.config.os.getenv')
    def test_settings_customise_sources_fallback_to_env_line_116(self, mock_getenv, mock_load_dotenv, mock_path):
        """Test line 116 - Fallback to .env when environment-specific file doesn't exist."""
        # Setup mocks
        mock_getenv.return_value = "production"
        
        # Mock Path behavior - environment-specific file doesn't exist, but .env does
        def path_side_effect(filename):
            mock_path_obj = MagicMock()
            if filename == ".env.production":
                mock_path_obj.exists.return_value = False  # Environment-specific file doesn't exist
            elif filename == ".env":
                mock_path_obj.exists.return_value = True   # .env file exists
            return mock_path_obj
        
        mock_path.side_effect = path_side_effect
        
        # Call the method
        result = Settings.settings_customise_sources(
            settings_cls=Settings,
            init_settings=MagicMock(),
            env_settings=MagicMock(),
            dotenv_settings=MagicMock(),
            file_secret_settings=MagicMock()
        )
        
        # Verify line 116: env_file = ".env" is executed
        # This happens when the environment-specific file doesn't exist
        mock_getenv.assert_called_once_with("ENV")
        
        # Verify Path was called (the exact calls may vary due to implementation details)
        assert mock_path.call_count >= 2
        
        # Verify load_dotenv was called with .env (the fallback)
        mock_load_dotenv.assert_called_once_with(".env", override=True)
        
        # Verify return value structure
        assert len(result) == 4

    @patch('app.core.config.Path')
    @patch('app.core.config.load_dotenv')
    @patch('app.core.config.os.getenv')
    def test_settings_customise_sources_env_specific_file_exists(self, mock_getenv, mock_load_dotenv, mock_path):
        """Test settings_customise_sources when environment-specific file exists (line 116 not executed)."""
        # Setup mocks
        mock_getenv.return_value = "development"
        
        # Mock Path behavior - environment-specific file exists
        def path_side_effect(filename):
            mock_path_obj = MagicMock()
            if filename == ".env.development":
                mock_path_obj.exists.return_value = True   # Environment-specific file exists
            elif filename == ".env":
                mock_path_obj.exists.return_value = True   # .env file also exists
            return mock_path_obj
        
        mock_path.side_effect = path_side_effect
        
        # Call the method
        result = Settings.settings_customise_sources(
            settings_cls=Settings,
            init_settings=MagicMock(),
            env_settings=MagicMock(),
            dotenv_settings=MagicMock(),
            file_secret_settings=MagicMock()
        )
        
        # Verify line 116 is NOT executed (env_file remains ".env.development")
        mock_getenv.assert_called_once_with("ENV")
        
        # Verify Path was called (implementation details may vary)
        assert mock_path.call_count >= 1
        
        # Verify load_dotenv was called with environment-specific file, not .env
        mock_load_dotenv.assert_called_once_with(".env.development", override=True)
        
        # Verify return value structure
        assert len(result) == 4

    @patch('app.core.config.Path')
    @patch('app.core.config.load_dotenv')
    @patch('app.core.config.os.getenv')
    def test_settings_customise_sources_no_env_variable(self, mock_getenv, mock_load_dotenv, mock_path):
        """Test settings_customise_sources when ENV variable is not set."""
        # Setup mocks
        mock_getenv.return_value = None  # No ENV variable set
        
        # Mock Path behavior - when ENV is None, the code uses "test" as default
        def path_side_effect(filename):
            mock_path_obj = MagicMock()
            if filename == ".env.test":  # Default fallback when env is None
                mock_path_obj.exists.return_value = False
            elif filename == ".env":
                mock_path_obj.exists.return_value = True
            return mock_path_obj
        
        mock_path.side_effect = path_side_effect
        
        # Call the method
        result = Settings.settings_customise_sources(
            settings_cls=Settings,
            init_settings=MagicMock(),
            env_settings=MagicMock(),
            dotenv_settings=MagicMock(),
            file_secret_settings=MagicMock()
        )
        
        # Verify the fallback logic works when ENV is None
        mock_getenv.assert_called_once_with("ENV")
        
        # Should fall back to .env due to line 116
        mock_load_dotenv.assert_called_once_with(".env", override=True)
        
        # Verify return value structure
        assert len(result) == 4


class TestConfigEdgeCases:
    """Focus on implemented configuration functionality, avoid unused features."""
    
    def test_environment_case_insensitive_production_check(self):
        """Test that production check is case insensitive."""
        test_cases = ["PRODUCTION", "Production", "production", "PrOdUcTiOn"]
        
        for env_value in test_cases:
            with patch.dict(os.environ, {"ENV": env_value}):
                test_settings = Settings()
                # Line 71 uses .lower() so all these should return True
                assert test_settings.is_production is True, f"Failed for ENV={env_value}"

    def test_environment_properties_consistency(self):
        """Test that environment properties are mutually exclusive."""
        # Test production environment
        with patch.dict(os.environ, {"ENV": "production"}):
            test_settings = Settings()
            assert test_settings.is_production is True
            assert test_settings.is_development is False
            assert test_settings.is_test is False
        
        # Test test environment
        with patch.dict(os.environ, {"ENV": "test"}):
            test_settings = Settings()
            assert test_settings.is_test is True
            assert test_settings.is_production is False
            # Note: is_development returns True for "test" environment (line 75)
            assert test_settings.is_development is True

    @patch('app.core.config.Path')
    @patch('app.core.config.load_dotenv')
    @patch('app.core.config.os.getenv')
    def test_settings_customise_sources_no_files_exist(self, mock_getenv, mock_load_dotenv, mock_path):
        """Test settings_customise_sources when no .env files exist."""
        # Setup mocks
        mock_getenv.return_value = "test"
        
        # Mock Path behavior - no files exist
        mock_path_obj = MagicMock()
        mock_path_obj.exists.return_value = False
        mock_path.return_value = mock_path_obj
        
        # Call the method
        result = Settings.settings_customise_sources(
            settings_cls=Settings,
            init_settings=MagicMock(),
            env_settings=MagicMock(),
            dotenv_settings=MagicMock(),
            file_secret_settings=MagicMock()
        )
        
        # Verify load_dotenv is not called when no files exist
        mock_load_dotenv.assert_not_called()
        
        # Verify return value structure
        assert len(result) == 4
