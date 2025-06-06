# Security Test Suite

This directory contains a comprehensive security test suite for the FastAPI application, providing organized testing for authentication, authorization, JWT handling, password management, and API endpoints.

## File Structure

```
tests/security/
├── __init__.py                          # Package initialization with documentation
├── README.md                            # This documentation file
├── fixtures.py                          # Shared test fixtures and helpers
├── test_auth0_jwt_bearer.py            # Auth0JWTBearer class tests
├── test_mock_auth0_jwt_bearer.py       # MockAuth0JWTBearer class tests
├── test_password_functions.py          # Password hashing/verification tests
├── test_jwt_functions.py               # JWT and token function tests
├── test_auth_api.py                    # Authentication API endpoint tests
├── test_dependencies.py               # Dependency injection tests
├── test_environment.py                # Environment and configuration tests
└── test_security_comprehensive.py     # Comprehensive integration tests
```

## Test Organization

### 1. Centralized Test Data and Helpers

The `fixtures.py` file contains:
- `SecurityTestFixtures`: Factory for creating test data objects
- `SecurityTestHelpers`: Common assertion and validation methods

This centralization eliminates duplicate test data creation, mock setup, and assertion logic across multiple test files.

### 2. Focused Test Files

Each test file focuses on a specific component or functionality:
- **Auth0JWTBearer Tests**: Authentication bearer token handling
- **MockAuth0JWTBearer Tests**: Development environment authentication
- **Password Function Tests**: Password hashing and verification
- **JWT Function Tests**: Token creation, validation, and decoding
- **Auth API Tests**: Authentication endpoint functionality
- **Dependencies Tests**: User authentication and authorization dependencies
- **Environment Tests**: Configuration and environment variable handling
- **Comprehensive Tests**: Integration testing across all components

### 3. Standardized Error Handling

Common validation methods provide consistent error checking:
- `assert_http_exception()`: HTTP exception validation
- `assert_user_properties()`: User object validation
- `assert_token_response()`: Token response structure validation

### 4. Systematic Test Coverage

The test suite provides:
- Unit tests for individual components
- Integration tests for component interactions
- Environment-specific tests for different configurations
- Comprehensive test coverage across all security functionality

## Usage Examples

### Running Specific Test Categories

```bash
# Run all security tests
pytest tests/security/

# Run only Auth0JWTBearer tests
pytest tests/security/test_auth0_jwt_bearer.py

# Run only password function tests
pytest tests/security/test_password_functions.py

# Run comprehensive integration tests
pytest tests/security/test_security_comprehensive.py

# Run with coverage
pytest tests/security/ --cov=app.core.security --cov-report=html
```

### Adding New Tests

1. **For new security functions**: Create a new test file following the naming convention
2. **For existing functionality**: Add tests to the appropriate existing file
3. **For new test data**: Add fixtures to `fixtures.py`
4. **For new assertions**: Add helpers to `SecurityTestHelpers`

### Example Test Structure

```python
class TestNewSecurityFeature:
    """Test new security feature functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.fixtures = SecurityTestFixtures()
        self.helpers = SecurityTestHelpers()
    
    def test_feature_success_case(self):
        """Test successful operation."""
        # Arrange
        test_data = self.fixtures.create_test_data()
        
        # Act
        result = security_function(test_data)
        
        # Assert
        self.helpers.assert_expected_result(result)
    
    def test_feature_error_case(self):
        """Test error handling."""
        with pytest.raises(HTTPException) as exc_info:
            security_function(invalid_data)
        
        self.helpers.assert_http_exception(
            exc_info.value,
            expected_status,
            expected_message
        )
```

## Benefits

1. **Reduced Maintenance**: Changes require fewer file modifications
2. **Improved Test Reliability**: Consistent test patterns reduce flaky tests
3. **Shared Components**: Common fixtures and helpers can be used across test files
4. **Enhanced Readability**: Clear structure makes tests easier to understand
5. **Faster Development**: New tests can leverage existing fixtures and helpers
6. **Better Coverage**: Systematic approach ensures comprehensive testing
7. **Easier Debugging**: Focused test files make issue isolation simpler

## Migration from Old Tests

The old security test files have been consolidated and reorganized:

- `tests/test_security.py` → Functionality distributed across focused files
- `tests/test_core_security.py` → Split into component-specific test files
- `tests/test_auth.py` → Moved to `test_auth_api.py`
- `tests/test_dependencies.py` → Refactored in `test_dependencies.py`
- `tests/test_security_production.py` → Integrated into environment tests

All functionality is preserved while improving organization and maintainability.

## Test Components

### Authentication Testing
- Auth0 JWT bearer token validation
- Mock authentication for development
- Token creation and verification
- User authentication flows

### Password Security Testing
- Password hashing with bcrypt
- Password verification
- Security property validation

### API Endpoint Testing
- Login endpoint functionality
- Token refresh mechanisms
- Rate limiting validation
- Error handling scenarios

### Dependency Testing
- User authentication dependencies
- Role-based authorization
- User status verification
- Admin user validation

### Environment Testing
- Configuration validation
- Environment variable handling
- Test vs production behavior
- Auth scheme configuration

### Integration Testing
- End-to-end security flows
- Component interaction testing
- Cross-functional validation
- Complete security pipeline testing

This organized test suite provides comprehensive coverage for all security functionality while maintaining clear structure and easy maintenance.