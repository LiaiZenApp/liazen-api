# Testing Guide for FastAPI Application

This guide provides information on how to run and create tests for the FastAPI application.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Running Tests](#running-tests)
- [Test Structure](#test-structure)
- [Writing New Tests](#writing-new-tests)
- [Test Fixtures](#test-fixtures)
- [Best Practices](#best-practices)
- [Common Issues](#common-issues)

## Prerequisites

Before running tests, ensure you have the following installed:

- Python 3.8+
- Poetry (for dependency management)
- All project dependencies (run `poetry install`)

## Running Tests

### Prerequisites

1. Make sure you have the test dependencies installed:
   ```bash
   pip install -e ".[test]"
   ```

2. Create a `.env.test` file in your project root if you haven't already:
   ```bash
   cp .env.example .env.test
   # Update the values in .env.test as needed for testing
   ```

### Run All Tests

```bash
pytest
```

### Run Specific Tests

Run a specific test file:
```bash
pytest tests/test_auth.py
```

Run a specific test function:
```bash
pytest tests/test_auth.py::test_login_success -v
```

### Common Options

- `-v`: Verbose output (shows test names)
- `-s`: Show output during tests (print statements)
- `-x`: Stop after first failure
- `--pdb`: Drop into debugger on failure

### Coverage Reports

Generate a coverage report:
```bash
pytest --cov=app --cov-report=term-missing
```

Generate an HTML report:
```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html  # View the report in browser
```

## Test Structure

The test files follow the same structure as the application code but are located in the `tests` directory:

```
tests/
├── __init__.py
├── conftest.py          # Test fixtures and configurations
├── test_auth.py         # Authentication tests
├── test_config.py       # Configuration tests
├── test_profile_api.py  # Profile API tests
└── test_rate_limiter.py # Rate limiter tests
```

## Writing New Tests

### Test File Structure

Each test file should follow this structure:

```python
"""
Test module for [feature name]
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

# Test client fixture
@pytest.fixture
def client():
    return TestClient(app)

def test_feature_name(client):
    """Test description"""
    # Test code here
    response = client.get("/api/endpoint")
    assert response.status_code == 200
    assert response.json() == {"message": "Success"}
```

### Testing Authentication

For testing authenticated endpoints, use the `get_current_user` dependency override:

```python
from unittest.mock import MagicMock
from app.core.security import get_current_user
from app.models.schemas import User

def test_authenticated_endpoint(client):
    # Create a mock user
    mock_user = User(
        id="test-user-id",
        email="test@example.com",
        hashed_password="hashed_password_here",
        is_active=True,
        is_verified=True
    )
    
    # Mock the get_current_user dependency
    async def mock_get_current_user():
        return mock_user
    
    # Override the dependency
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    try:
        # Make authenticated request
        response = client.get("/api/protected")
        assert response.status_code == 200
    finally:
        # Clean up
        app.dependency_overrides = {}
```

## Test Fixtures

The `conftest.py` file contains reusable test fixtures. Common fixtures include:

- `client`: FastAPI TestClient instance
- `test_user`: A test user object
- `auth_headers`: Authentication headers for test requests

## Best Practices

1. **Isolation**: Each test should be independent and not rely on the state from other tests.
2. **Descriptive Names**: Use descriptive test function names that explain what's being tested.
3. **Arrange-Act-Assert**: Follow the AAA pattern in tests.
4. **Clean Up**: Always clean up any test data or mocks after each test.
5. **Test Edge Cases**: Include tests for error conditions and edge cases.

## Common Issues

### Database Access in Tests

If your tests require database access, ensure you:

1. Use a separate test database
2. Set up and tear down test data
3. Use transactions or database fixtures to isolate tests

### Environment Variables

Tests use environment variables from `.env.test`. Ensure this file exists and contains the necessary configuration.

### Async Tests

For testing async endpoints, use `pytest-asyncio`:

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_async_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/async-endpoint")
    assert response.status_code == 200
```

## Coverage Reports

To generate an HTML coverage report:

```bash
pytest --cov=app --cov-report=html
```

Open `htmlcov/index.html` in your browser to view the report.

## Debugging Tests

To debug a failing test, use `pdb`:

```python
def test_example():
    import pdb; pdb.set_trace()  # Execution will pause here
    # Test code
```

Or run pytest with `--pdb` to drop into the debugger on failure:

```bash
pytest --pdb
```

## Continuous Integration

This project includes a GitHub Actions workflow (`.github/workflows/test.yml`) that runs tests on push and pull requests.
