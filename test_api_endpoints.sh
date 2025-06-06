#!/bin/bash

# LiaiZen API Test Script
# This script tests all available API endpoints with curl commands

# Configuration
BASE_URL="http://localhost:8000"
API_BASE="$BASE_URL/api"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to make curl request and show response
test_endpoint() {
    local method=$1
    local url=$2
    local data=$3
    local headers=$4
    local description=$5
    
    echo
    echo "=========================================="
    print_status "Testing: $description"
    print_status "Method: $method"
    print_status "URL: $url"
    
    if [ ! -z "$data" ]; then
        print_status "Data: $data"
    fi
    
    echo "==========================================\n"
    
    if [ "$method" = "GET" ]; then
        if [ ! -z "$headers" ]; then
            curl -X GET "$url" -H "$headers" -w "\n\nHTTP Status: %{http_code}\nTime: %{time_total}s\n" -v
        else
            curl -X GET "$url" -w "\n\nHTTP Status: %{http_code}\nTime: %{time_total}s\n" -v
        fi
    elif [ "$method" = "POST" ]; then
        if [ ! -z "$headers" ]; then
            curl -X POST "$url" -H "Content-Type: application/json" -H "$headers" -d "$data" -w "\n\nHTTP Status: %{http_code}\nTime: %{time_total}s\n" -v
        else
            curl -X POST "$url" -H "Content-Type: application/json" -d "$data" -w "\n\nHTTP Status: %{http_code}\nTime: %{time_total}s\n" -v
        fi
    elif [ "$method" = "PUT" ]; then
        if [ ! -z "$headers" ]; then
            curl -X PUT "$url" -H "Content-Type: application/json" -H "$headers" -d "$data" -w "\n\nHTTP Status: %{http_code}\nTime: %{time_total}s\n" -v
        else
            curl -X PUT "$url" -H "Content-Type: application/json" -d "$data" -w "\n\nHTTP Status: %{http_code}\nTime: %{time_total}s\n" -v
        fi
    elif [ "$method" = "PATCH" ]; then
        if [ ! -z "$headers" ]; then
            curl -X PATCH "$url" -H "Content-Type: application/json" -H "$headers" -d "$data" -w "\n\nHTTP Status: %{http_code}\nTime: %{time_total}s\n" -v
        else
            curl -X PATCH "$url" -H "Content-Type: application/json" -d "$data" -w "\n\nHTTP Status: %{http_code}\nTime: %{time_total}s\n" -v
        fi
    elif [ "$method" = "DELETE" ]; then
        if [ ! -z "$headers" ]; then
            curl -X DELETE "$url" -H "$headers" -w "\n\nHTTP Status: %{http_code}\nTime: %{time_total}s\n" -v
        else
            curl -X DELETE "$url" -w "\n\nHTTP Status: %{http_code}\nTime: %{time_total}s\n" -v
        fi
    fi
    
    echo
    echo "=========================================="
    echo
}

# Function to test file upload endpoints
test_file_upload() {
    local url=$1
    local headers=$2
    local description=$3
    local file_path=$4
    
    echo
    echo "=========================================="
    print_status "Testing: $description"
    print_status "Method: POST (File Upload)"
    print_status "URL: $url"
    print_status "File: $file_path"
    echo "=========================================="
    
    if [ ! -z "$headers" ]; then
        curl -X POST "$url" -H "$headers" -F "file=@$file_path" -w "\n\nHTTP Status: %{http_code}\nTime: %{time_total}s\n" -v
    else
        curl -X POST "$url" -F "file=@$file_path" -w "\n\nHTTP Status: %{http_code}\nTime: %{time_total}s\n" -v
    fi
    
    echo
    echo "=========================================="
    echo
}

# Sample data for testing
SAMPLE_USER_REGISTER='{
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "password": "testpassword123",
    "is_active": true,
    "role": "user"
}'

SAMPLE_USER_LOGIN='{
    "username": "test@example.com",
    "password": "testpassword123"
}'

SAMPLE_USER_UPDATE='{
    "first_name": "Updated",
    "last_name": "User",
    "email": "updated@example.com"
}'

SAMPLE_PASSWORD_UPDATE='{
    "username": "test@example.com",
    "password": "newpassword123"
}'

SAMPLE_DEVICE_REGISTER='{
    "user_id": "12345678-1234-5678-1234-567812345678",
    "device_id": "sample-device-token",
    "device_type": "ios",
    "device_name": "iPhone 13",
    "os_version": "15.4",
    "app_version": "1.0.0"
}'

SAMPLE_MESSAGE='{
    "recipient_id": "87654321-4321-8765-4321-876543210987",
    "content": "Hello, this is a test message!"
}'

SAMPLE_EVENT='{
    "title": "Test Event",
    "description": "This is a test event",
    "start_time": "2024-12-31T10:00:00",
    "end_time": "2024-12-31T12:00:00",
    "location": "Test Location",
    "is_virtual": false,
    "capacity": 50
}'

SAMPLE_CONNECTION='{
    "target_user_id": "87654321-4321-8765-4321-876543210987",
    "status": "pending"
}'

SAMPLE_MEMBER='{
    "user_id": "12345678-1234-5678-1234-567812345678",
    "first_name": "Test",
    "last_name": "Member",
    "email": "member@example.com",
    "phone": "+1234567890"
}'

SAMPLE_MEMBER_INVITE='{
    "email": "invite@example.com",
    "first_name": "Invited",
    "last_name": "Member",
    "phone": "+1234567890",
    "role": "member",
    "send_invite": true
}'

SAMPLE_NOTIFICATION='{
    "title": "Test Notification",
    "message": "This is a test notification",
    "notification_type": "info"
}'

SAMPLE_PROFILE='{
    "user_id": "12345678-1234-5678-1234-567812345678",
    "bio": "This is a test bio",
    "location": "Test City",
    "website": "https://example.com",
    "birth_date": "1990-01-01",
    "gender": "Other",
    "phone_number": "+1234567890",
    "preferred_language": "en",
    "timezone": "UTC"
}'

SAMPLE_PROFILE_UPDATE='{
    "bio": "Updated bio",
    "location": "Updated City"
}'

# Sample UUIDs for testing
SAMPLE_USER_ID="12345678-1234-5678-1234-567812345678"
SAMPLE_TARGET_USER_ID="87654321-4321-8765-4321-876543210987"
SAMPLE_CONNECTION_ID="11111111-2222-3333-4444-555555555555"
SAMPLE_NOTIFICATION_ID="66666666-7777-8888-9999-000000000000"
SAMPLE_EVENT_ID="1"

# Sample JWT token (you'll need to replace this with a real token after login)
SAMPLE_JWT_TOKEN="Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

print_status "Starting LiaiZen API Tests"
print_status "Base URL: $BASE_URL"
print_warning "Note: Some endpoints require authentication. Update SAMPLE_JWT_TOKEN with a real token after login."

# ==========================================
# ROOT AND HEALTH ENDPOINTS
# ==========================================

test_endpoint "GET" "$BASE_URL/" "" "" "Root endpoint"
test_endpoint "GET" "$BASE_URL/health" "" "" "Health check endpoint"

# ==========================================
# AUTH ENDPOINTS
# ==========================================

test_endpoint "POST" "$API_BASE/auth/login" "$SAMPLE_USER_LOGIN" "" "User login"
test_endpoint "POST" "$API_BASE/auth/refresh" '{"access_token": "sample_token", "refresh_token": "sample_refresh_token", "expires_in": 3600, "token_type": "Bearer"}' "" "Refresh token"

# ==========================================
# USER ENDPOINTS
# ==========================================

test_endpoint "GET" "$API_BASE/users" "" "" "Get all users"
test_endpoint "POST" "$API_BASE/users/register" "$SAMPLE_USER_REGISTER" "" "Register new user"
test_endpoint "GET" "$API_BASE/users/$SAMPLE_USER_ID" "" "" "Get user by ID"
test_endpoint "PUT" "$API_BASE/users/$SAMPLE_USER_ID" "$SAMPLE_USER_UPDATE" "Authorization: $SAMPLE_JWT_TOKEN" "Update user profile"
test_endpoint "PUT" "$API_BASE/users/$SAMPLE_USER_ID/password" "$SAMPLE_PASSWORD_UPDATE" "Authorization: $SAMPLE_JWT_TOKEN" "Update user password"
test_endpoint "DELETE" "$API_BASE/users/$SAMPLE_USER_ID" "" "Authorization: $SAMPLE_JWT_TOKEN" "Delete user account"
test_endpoint "POST" "$API_BASE/users/devices/register" "$SAMPLE_DEVICE_REGISTER" "Authorization: $SAMPLE_JWT_TOKEN" "Register user device"

# File upload endpoint (requires a test image file)
if [ -f "test_image.jpg" ]; then
    test_file_upload "$API_BASE/users/$SAMPLE_USER_ID/profile-image" "Authorization: $SAMPLE_JWT_TOKEN" "Upload profile image" "test_image.jpg"
else
    print_warning "Skipping profile image upload test - test_image.jpg not found"
fi

# ==========================================
# CHAT ENDPOINTS
# ==========================================

test_endpoint "POST" "$API_BASE/chat/messages" "$SAMPLE_MESSAGE" "Authorization: $SAMPLE_JWT_TOKEN" "Send chat message"
test_endpoint "GET" "$API_BASE/chat/messages?recipient_id=$SAMPLE_TARGET_USER_ID&limit=10&offset=0" "" "Authorization: $SAMPLE_JWT_TOKEN" "Get chat messages"

# ==========================================
# EVENT ENDPOINTS
# ==========================================

test_endpoint "POST" "$API_BASE/events" "$SAMPLE_EVENT" "Authorization: $SAMPLE_JWT_TOKEN" "Create event"
test_endpoint "GET" "$API_BASE/events/user/$SAMPLE_EVENT_ID" "" "Authorization: $SAMPLE_JWT_TOKEN" "Get user events"
test_endpoint "GET" "$API_BASE/events/user/$SAMPLE_EVENT_ID?search_text=test&time_zone=UTC" "" "Authorization: $SAMPLE_JWT_TOKEN" "Get user events with filters"
test_endpoint "GET" "$API_BASE/events/$SAMPLE_EVENT_ID" "" "Authorization: $SAMPLE_JWT_TOKEN" "Get event by ID"
test_endpoint "DELETE" "$API_BASE/events/$SAMPLE_EVENT_ID" "" "Authorization: $SAMPLE_JWT_TOKEN" "Delete event"

# ==========================================
# CONNECTION ENDPOINTS
# ==========================================

test_endpoint "POST" "$API_BASE/connections" "$SAMPLE_CONNECTION" "Authorization: $SAMPLE_JWT_TOKEN" "Create connection"
test_endpoint "GET" "$API_BASE/connections" "" "Authorization: $SAMPLE_JWT_TOKEN" "Get all connections"
test_endpoint "GET" "$API_BASE/connections?connection_status=pending" "" "Authorization: $SAMPLE_JWT_TOKEN" "Get connections by status"
test_endpoint "PATCH" "$API_BASE/connections/$SAMPLE_CONNECTION_ID?status=accepted" "" "Authorization: $SAMPLE_JWT_TOKEN" "Update connection status"
test_endpoint "DELETE" "$API_BASE/connections/$SAMPLE_CONNECTION_ID" "" "Authorization: $SAMPLE_JWT_TOKEN" "Delete connection"

# ==========================================
# MEMBER ENDPOINTS
# ==========================================

test_endpoint "GET" "$API_BASE/members/$SAMPLE_USER_ID" "" "Authorization: $SAMPLE_JWT_TOKEN" "Get member by user ID"
test_endpoint "GET" "$API_BASE/members/email/test@example.com" "" "Authorization: $SAMPLE_JWT_TOKEN" "Get member by email"
test_endpoint "POST" "$API_BASE/members" "$SAMPLE_MEMBER" "Authorization: $SAMPLE_JWT_TOKEN" "Create member"
test_endpoint "DELETE" "$API_BASE/members/$SAMPLE_USER_ID" "" "Authorization: $SAMPLE_JWT_TOKEN" "Delete member"
test_endpoint "GET" "$API_BASE/members/relationships/list" "" "Authorization: $SAMPLE_JWT_TOKEN" "Get relationships"
test_endpoint "POST" "$API_BASE/members/invite" "$SAMPLE_MEMBER_INVITE" "Authorization: $SAMPLE_JWT_TOKEN" "Invite member"

# ==========================================
# NOTIFICATION ENDPOINTS
# ==========================================

test_endpoint "GET" "$API_BASE/notifications" "" "Authorization: $SAMPLE_JWT_TOKEN" "Get notifications"
test_endpoint "GET" "$API_BASE/notifications?skip=0&limit=10&unread_only=true" "" "Authorization: $SAMPLE_JWT_TOKEN" "Get unread notifications"
test_endpoint "POST" "$API_BASE/notifications" "$SAMPLE_NOTIFICATION" "Authorization: $SAMPLE_JWT_TOKEN" "Create notification"
test_endpoint "GET" "$API_BASE/notifications/$SAMPLE_NOTIFICATION_ID" "" "Authorization: $SAMPLE_JWT_TOKEN" "Get notification by ID"
test_endpoint "PUT" "$API_BASE/notifications/$SAMPLE_NOTIFICATION_ID/read" "" "Authorization: $SAMPLE_JWT_TOKEN" "Mark notification as read"
test_endpoint "PUT" "$API_BASE/notifications/read-all" "" "Authorization: $SAMPLE_JWT_TOKEN" "Mark all notifications as read"
test_endpoint "DELETE" "$API_BASE/notifications/$SAMPLE_NOTIFICATION_ID" "" "Authorization: $SAMPLE_JWT_TOKEN" "Delete notification"

# ==========================================
# PROFILE ENDPOINTS
# ==========================================

test_endpoint "GET" "$API_BASE/profiles/me" "" "Authorization: $SAMPLE_JWT_TOKEN" "Get my profile"
test_endpoint "PUT" "$API_BASE/profiles/me" "$SAMPLE_PROFILE_UPDATE" "Authorization: $SAMPLE_JWT_TOKEN" "Update my profile"
test_endpoint "GET" "$API_BASE/profiles/$SAMPLE_USER_ID" "" "Authorization: $SAMPLE_JWT_TOKEN" "Get user profile"
test_endpoint "POST" "$API_BASE/profiles" "$SAMPLE_PROFILE" "Authorization: $SAMPLE_JWT_TOKEN" "Create profile"

# File upload endpoint for profile picture
if [ -f "test_image.jpg" ]; then
    test_file_upload "$API_BASE/profiles/me/picture" "Authorization: $SAMPLE_JWT_TOKEN" "Upload profile picture" "test_image.jpg"
else
    print_warning "Skipping profile picture upload test - test_image.jpg not found"
fi

# ==========================================
# AUTH0 TEST ENDPOINTS
# ==========================================

test_endpoint "GET" "$API_BASE/auth0-test/public" "" "" "Auth0 public endpoint"
test_endpoint "GET" "$API_BASE/auth0-test/protected" "" "Authorization: $SAMPLE_JWT_TOKEN" "Auth0 protected endpoint"
test_endpoint "GET" "$API_BASE/auth0-test/metadata" "" "" "Auth0 metadata"

# ==========================================
# ADDITIONAL ENDPOINTS
# ==========================================

test_endpoint "GET" "$API_BASE/me" "" "Authorization: $SAMPLE_JWT_TOKEN" "Get current user info"

# ==========================================
# API DOCUMENTATION ENDPOINTS
# ==========================================

test_endpoint "GET" "$BASE_URL/docs" "" "" "OpenAPI documentation (Swagger UI)"
test_endpoint "GET" "$BASE_URL/redoc" "" "" "ReDoc documentation"
test_endpoint "GET" "$BASE_URL/openapi.json" "" "" "OpenAPI JSON schema"

print_success "API testing completed!"
print_warning "Remember to:"
print_warning "1. Start the FastAPI server before running this script"
print_warning "2. Update the SAMPLE_JWT_TOKEN with a real token after successful login"
print_warning "3. Create test_image.jpg file for file upload tests"
print_warning "4. Update sample UUIDs with real ones from your database"
print_warning "5. Adjust the BASE_URL if your server runs on a different port"

echo
print_status "To run this script:"
print_status "1. Make it executable: chmod +x test_api_endpoints.sh"
print_status "2. Run it: ./test_api_endpoints.sh"
print_status "3. Or run specific sections by copying individual curl commands"