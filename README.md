# LiaiZen API

A FastAPI application for iOS/Android apps with Auth0 authentication, PostgreSQL database, and Azure-ready deployment.

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL (if running locally without Docker)
- Auth0 account (for authentication)

### Environment Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/LiaiZenApp/liaizen-api.git
   cd liazen-api
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   ```

3. **Configure environment variables** (see [Environment Configuration](#environment-configuration))

### Running the Application

#### Option 1: Docker Compose (Recommended)

```bash
# Start all services (API + PostgreSQL)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

#### Option 2: Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL (ensure it's running)
# Update .env with your local database credentials

# Run the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Option 3: Production Docker

```bash
# Build optimized production image
docker build -f Dockerfile.prod -t liaizen-api:latest .

# Run with production settings
docker run -d \
  --name liaizen-api \
  -p 8000:8000 \
  --env-file .env \
  liaizen-api:latest
```

### API Access

- **API Base URL**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 📋 Environment Configuration

Create a `.env` file with the following variables:

```env
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/liaizen
POSTGRES_DB=liaizen
POSTGRES_USER=user
POSTGRES_PASSWORD=password

# Auth0 Configuration
AUTH0_DOMAIN=your-domain.auth0.com
AUTH0_AUDIENCE=your-api-identifier
AUTH0_CLIENT_ID=your-client-id
AUTH0_CLIENT_SECRET=your-client-secret

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# API Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
DEBUG=true
LOG_LEVEL=INFO

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# File Upload
MAX_FILE_SIZE_MB=10
UPLOAD_PATH=./uploads
```

## 🏗️ Architecture

### Project Structure

```
├── app/
│   ├── api/                 # API route handlers
│   │   ├── auth.py          # Authentication endpoints
│   │   ├── users.py         # User management
│   │   ├── connections.py   # User connections
│   │   ├── chat.py          # Chat functionality
│   │   ├── events.py        # Event management
│   │   ├── members.py       # Member operations
│   │   ├── notification.py  # Notifications
│   │   ├── profile.py       # User profiles
│   │   └── auth0_test.py    # Auth0 testing
│   ├── common/              # Common utilities (e.g., response schemas)
│   ├── core/                # Core functionality
│   │   ├── config.py        # Configuration management
│   │   ├── security.py      # Security utilities
│   │   ├── logging_config.py# Logging setup
│   │   └── rate_limiter.py  # Rate limiting
│   ├── models/              # Data models
│   │   └── schemas.py       # Pydantic schemas
│   ├── services/            # Business logic
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── connection_service.py
│   │   ├── chat_service.py
│   │   ├── event_service.py
│   │   ├── member_service.py
│   │   ├── notification_service.py
│   │   └── profile_service.py
│   ├── db/                  # Database configuration
│   └── main.py              # Application entry point
├── logs/                    # Application logs
├── uploads/                 # Uploaded files storage
├── tests/                   # Test suite
├── scripts/                 # Utility scripts (e.g., test and deployment scripts)
├── docker/                  # Docker configurations
├── docs/                    # Documentation
└── requirements.txt         # Python dependencies
```

### Key Features

- **FastAPI Framework**
- **Auth0 Integration** (to be added later)
- **PostgreSQL Database** (to be added later)
- **Rate Limiting** (untested)
- **File Uploads** (untested)
- **Comprehensive Testing**
- **Docker Support**
- **API Documentation** (untested)
- **Logging**

## 🔧 Development

### Setting up Development Environment

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run tests**
   ```bash
   # Run all tests
   pytest

   # Run with coverage
   pytest --cov=app --cov-report=html

   # Run specific test file
   pytest tests/test_users_api.py
   ```

3. **Code quality**
   ```bash
   # Run tests with coverage and style checks
   pytest --cov=app --cov-report=html --cov-report=term

   # Check code style (manual review recommended)
   # TODO: Consider adding black, flake8, mypy if needed for your development workflow
   ```

### API Testing

Use the provided test script to validate all endpoints:

```bash
# Make script executable
chmod +x test_api_endpoints.sh

# Run all endpoint tests
./test_api_endpoints.sh

# Test specific endpoints
curl -X GET http://localhost:8000/health
curl -X GET http://localhost:8000/api/users
```

<!-- ### Database Management

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
``` -->

## 🐳 Docker Deployment

### Development

```bash
# Build and run development environment
docker-compose -f docker-compose.dev.yml up --build

# Run with specific environment
docker-compose --env-file .env.dev up
```

### Production

```bash
# Build production image
docker build -f Dockerfile.prod -t liaizen-api:prod .

# Run production container
docker run -d \
  --name liaizen-api-prod \
  -p 80:8000 \
  --env-file .env.prod \
  --restart unless-stopped \
  liaizen-api:prod
```

### Multi-stage Build Benefits

- **Smaller image size**: Production image excludes development dependencies
- **Security**: Minimal attack surface with distroless base image
- **Performance**: Optimized for production workloads
- **Caching**: Efficient layer caching for faster builds

## 🔒 Security

### Authentication Flow

1. **User Registration**: Users register through Auth0
2. **Token Validation**: JWT tokens validated on protected endpoints
3. **Authorization**: Role-based access control
4. **Rate Limiting**: Prevents abuse and DoS attacks

### Security Features

- **JWT Token Validation**: All protected endpoints validate Auth0 JWT tokens
- **CORS Configuration**: Configurable cross-origin resource sharing
- **Rate Limiting**: Per-endpoint and global rate limits
- **Input Validation**: Pydantic models validate all input data
- **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection
- **File Upload Security**: Validated file types and size limits

## 📊 Monitoring and Logging

### Health Checks

- **Basic Health**: `GET /health`
- **Database Health**: Included in health check response
- **Service Dependencies**: Auth0 connectivity validation

### Logging

- **Structured Logging**: JSON formatted logs for production
- **Log Levels**: Configurable log levels (DEBUG, INFO, WARNING, ERROR)
- **Request Logging**: All API requests logged with timing
- **Error Tracking**: Detailed error logging with stack traces

## 🚀 Deployment

### Azure Container Instances

```bash
# Build and push to Azure Container Registry
az acr build --registry myregistry --image liaizen-api:latest .

# Deploy to Azure Container Instances
az container create \
  --resource-group myResourceGroup \
  --name liaizen-api \
  --image myregistry.azurecr.io/liaizen-api:latest \
  --cpu 1 --memory 2 \
  --ports 8000 \
  --environment-variables \
    DATABASE_URL=$DATABASE_URL \
    AUTH0_DOMAIN=$AUTH0_DOMAIN
```


## 📚 API Documentation

### Authentication

All protected endpoints require a valid JWT token in the Authorization header:

```bash
Authorization: Bearer <your-jwt-token>
```

### Core Endpoints

#### Users
- `GET /api/users` - List all users
- `POST /api/users/register` - Register new user
- `GET /api/users/{user_id}` - Get user by ID
- `PUT /api/users/{user_id}` - Update user
- `DELETE /api/users/{user_id}` - Delete user

#### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Refresh token

#### Connections
- `GET /api/connections` - Get user connections
- `POST /api/connections` - Create connection
- `PATCH /api/connections/{id}` - Update connection status
- `DELETE /api/connections/{id}` - Delete connection

#### Chat
- `POST /api/chat/messages` - Send message
- `GET /api/chat/messages` - Get messages

#### Events
- `POST /api/events` - Create event
- `GET /api/events/user/{user_id}` - Get user events
- `GET /api/events/{event_id}` - Get event details
- `DELETE /api/events/{event_id}` - Delete event

### Error Handling

The API returns consistent error responses:

```json
{
  "detail": "Error description",
  "status_code": 400,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Standards

- Follow PEP 8 style guidelines
- Add type hints to all functions
- Write comprehensive docstrings
- Include unit tests for new features
- Update documentation for API changes

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the `/docs` endpoint for interactive API documentation
- **Issues**: Report bugs and feature requests in the GitHub issues
- **Testing**: Use the provided test script to validate your setup

## 🔄 Changelog

### v1.0.0
- Initial release with core functionality
- Auth0 integration
- User management
- Connection system
- Chat functionality
- Event management
- Comprehensive test suite
- Logging
