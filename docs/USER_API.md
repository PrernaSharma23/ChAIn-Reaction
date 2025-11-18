# User Controller API Reference

## Base URL
```
https://api.chain-reaction.example.com/auth
```

## Authentication
Public endpoints (`/signup`, `/login`) do not require authentication.
Protected endpoints (`/profile`, `/verify_token`) require JWT in `Authorization` header.

---

## Endpoints

### 1. User Sign Up
Register a new user account.

#### Request
```http
POST /auth/signup
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123!"
}
```

#### Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `username` | string | Yes | Unique username (3-32 chars, alphanumeric + underscore) |
| `email` | string | Yes | Valid email address |
| `password` | string | Yes | Minimum 8 characters, must include uppercase, lowercase, number |

#### Response (Success)
```json
HTTP/1.1 201 Created
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "john_doe",
    "email": "john@example.com",
    "created_at": "2025-11-18T10:30:45.123Z"
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNTUwZTg0MDAi...",
  "message": "User created successfully"
}
```

#### Error Responses
```json
HTTP/1.1 400 Bad Request
{
  "error": "username_taken",
  "message": "Username 'john_doe' already exists"
}
```

```json
HTTP/1.1 400 Bad Request
{
  "error": "email_taken",
  "message": "Email 'john@example.com' already registered"
}
```

```json
HTTP/1.1 400 Bad Request
{
  "error": "invalid_password",
  "message": "Password must be at least 8 characters and include uppercase, lowercase, and number"
}
```

```json
HTTP/1.1 400 Bad Request
{
  "error": "invalid_email",
  "message": "Invalid email format"
}
```

```json
HTTP/1.1 400 Bad Request
{
  "error": "missing_field",
  "message": "Required field 'username' missing"
}
```

---

### 2. User Login
Authenticate and receive JWT token.

#### Request
```http
POST /auth/login
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "SecurePass123!"
}
```

#### Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `email` | string | Yes | User's registered email |
| `password` | string | Yes | User's password |

#### Response (Success)
```json
HTTP/1.1 200 OK
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "john_doe",
    "email": "john@example.com",
    "created_at": "2025-11-18T10:30:45.123Z"
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNTUwZTg0MDAi...",
  "expires_in": 86400,
  "message": "Login successful"
}
```

#### Response Fields
| Field | Type | Description |
|-------|------|-------------|
| `user` | object | User details |
| `token` | string | JWT token (valid for 24 hours by default) |
| `expires_in` | integer | Token expiration in seconds |

#### Error Responses
```json
HTTP/1.1 401 Unauthorized
{
  "error": "invalid_credentials",
  "message": "Email or password is incorrect"
}
```

```json
HTTP/1.1 400 Bad Request
{
  "error": "user_not_found",
  "message": "No user registered with email 'john@example.com'"
}
```

```json
HTTP/1.1 400 Bad Request
{
  "error": "missing_field",
  "message": "Required field 'email' missing"
}
```

---

### 3. Get User Profile
Retrieve authenticated user's profile and repositories.

#### Request
```http
GET /auth/profile
Authorization: Bearer <JWT_TOKEN>
```

#### Response
```json
HTTP/1.1 200 OK
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "john_doe",
    "email": "john@example.com",
    "created_at": "2025-11-18T10:30:45.123Z",
    "updated_at": "2025-11-19T14:22:10.456Z"
  },
  "repositories": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "repo_name": "MyJavaProject",
      "repo_url": "https://github.com/user/my-java-project.git",
      "created_at": "2025-11-18T11:45:30.789Z",
      "status": "processed"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "repo_name": "PythonLib",
      "repo_url": "https://github.com/user/python-lib.git",
      "created_at": "2025-11-19T09:15:22.321Z",
      "status": "processing"
    }
  ],
  "repository_count": 2,
  "total_nodes": 1250,
  "total_edges": 3420
}
```

#### Error Responses
```json
HTTP/1.1 401 Unauthorized
{
  "error": "Authorization token required"
}
```

```json
HTTP/1.1 401 Unauthorized
{
  "error": "Invalid token",
  "message": "Token is expired or malformed"
}
```

---

### 4. Verify Token
Check if a JWT token is valid without making other API calls.

#### Request
```http
POST /auth/verify_token
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNTUwZTg0MDAi..."
}
```

#### Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `token` | string | No | Token to verify (if not in header) |

#### Response (Valid Token)
```json
HTTP/1.1 200 OK
{
  "valid": true,
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john_doe",
  "expires_at": "2025-11-20T10:30:45.123Z",
  "expires_in_seconds": 86400
}
```

#### Response (Expired Token)
```json
HTTP/1.1 401 Unauthorized
{
  "valid": false,
  "error": "Token expired",
  "expired_at": "2025-11-19T10:30:45.123Z"
}
```

#### Response (Invalid Token)
```json
HTTP/1.1 401 Unauthorized
{
  "valid": false,
  "error": "Invalid token",
  "message": "Token is malformed or corrupted"
}
```

---

### 5. Update User Profile
Modify user information (username, email, password).

#### Request
```http
PUT /auth/profile
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
  "username": "john_doe_updated",
  "email": "newemail@example.com"
}
```

#### Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `username` | string | No | New username |
| `email` | string | No | New email address |
| `current_password` | string | Yes (if changing password) | Required to verify identity |
| `new_password` | string | No | New password (if changing) |

#### Response
```json
HTTP/1.1 200 OK
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "john_doe_updated",
    "email": "newemail@example.com",
    "created_at": "2025-11-18T10:30:45.123Z",
    "updated_at": "2025-11-19T15:45:30.123Z"
  },
  "message": "Profile updated successfully"
}
```

#### Error Responses
```json
HTTP/1.1 400 Bad Request
{
  "error": "username_taken",
  "message": "Username 'john_doe_updated' already taken"
}
```

```json
HTTP/1.1 401 Unauthorized
{
  "error": "invalid_password",
  "message": "Current password is incorrect"
}
```

---

### 6. Logout / Revoke Token
Invalidate current JWT token (frontend implementation).

#### Implementation (Client-Side)
```javascript
// Remove token from localStorage/sessionStorage
localStorage.removeItem('jwt_token');

// Or clear cookies
document.cookie = "jwt_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
```

**Note**: ChAIn-Reaction doesn't maintain a token blacklist. Token revocation happens when:
1. Token expires naturally (24 hours)
2. User's password changes (invalidates all existing tokens)
3. Client removes token from storage

---

## JWT Token Structure

### Token Claims
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john_doe",
  "email": "john@example.com",
  "iat": 1700383845,
  "exp": 1700470245
}
```

### Token Properties
| Claim | Type | Description |
|-------|------|-------------|
| `user_id` | string | Unique user identifier (UUID) |
| `username` | string | Username for display |
| `email` | string | User's email |
| `iat` | integer | Token issued at (Unix timestamp) |
| `exp` | integer | Token expires at (Unix timestamp) |

### Token Expiration
- **Default**: 24 hours
- **Renewal**: Must login again to get new token
- **Security**: Use HTTPS to prevent token interception

---

## Authentication Flow Diagram

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       │ 1. POST /auth/signup
       │    username, email, password
       ▼
┌─────────────────────────────────┐
│  Register & Get JWT Token       │
│  (201 Created + token)          │
└─────────────────────────────────┘
       │
       │ 2. Store JWT in localStorage
       │
       ▼
┌─────────────────────────────────┐
│  Use JWT in all API calls       │
│  Authorization: Bearer <token>  │
└─────────────────────────────────┘
       │
       ├─► POST /project/onboard
       ├─► POST /project/graph
       ├─► GET /project/nodes
       └─► ... (all protected routes)
       │
       │ 3. On login retry (token expired)
       │    POST /auth/login to get new token
       ▼
┌─────────────────────────────────┐
│  Refresh JWT & Update Storage   │
└─────────────────────────────────┘
```

---

## Security Best Practices

### Client-Side
1. **HTTPS Only**: Always use HTTPS to prevent token interception
2. **Secure Storage**: Store token in `httpOnly` cookie or localStorage (never in URL)
3. **Token Rotation**: Implement refresh token mechanism for long-lived sessions
4. **Logout**: Clear token from storage on logout
5. **Timeout**: Implement client-side timeout for inactivity

### Server-Side
1. **Password Hashing**: Passwords hashed with bcrypt (10 rounds minimum)
2. **Rate Limiting**: Limit login attempts (e.g., 5 attempts/5 minutes per IP)
3. **HTTPS**: Enforce HTTPS for all endpoints
4. **CORS**: Restrict CORS to trusted domains
5. **Token Signing**: Use strong secret key (minimum 32 characters)

### Token Handling
```python
# Example: Using JWT in requests
import requests

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

response = requests.post(
    "https://api.chain-reaction.example.com/project/onboard",
    json={"repo_name": "MyRepo", "repo_url": "https://github.com/..."},
    headers=headers
)
```

---

## Examples

### Example 1: Complete Auth Flow
```bash
#!/bin/bash

API="https://api.chain-reaction.example.com"

# Step 1: Sign up
SIGNUP_RESPONSE=$(curl -X POST "$API/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "jane_dev",
    "email": "jane@example.com",
    "password": "SecurePass123!"
  }')

TOKEN=$(echo $SIGNUP_RESPONSE | jq -r '.token')
echo "✓ Signed up, token: $TOKEN"

# Step 2: Get profile
curl -X GET "$API/auth/profile" \
  -H "Authorization: Bearer $TOKEN" | jq '.'

# Step 3: Use token for project API
curl -X POST "$API/project/onboard" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_name": "MyProject",
    "repo_url": "https://github.com/jane/myproject.git"
  }' | jq '.'
```

### Example 2: Handle Token Expiration
```javascript
// React example
const apiCall = async (endpoint, options = {}) => {
  let token = localStorage.getItem('jwt_token');
  
  let response = await fetch(endpoint, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`
    }
  });

  if (response.status === 401) {
    // Token expired, redirect to login
    window.location.href = '/login';
    return null;
  }

  return response.json();
};
```

### Example 3: Password Change
```bash
curl -X PUT "https://api.chain-reaction.example.com/auth/profile" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "OldPass123!",
    "new_password": "NewSecurePass456!"
  }'
```

---

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Request succeeded |
| 201 | Created - Resource created |
| 400 | Bad Request - Invalid parameters or validation failed |
| 401 | Unauthorized - Invalid/expired token or credentials |
| 409 | Conflict - Resource already exists (username/email taken) |
| 500 | Internal Server Error - Server error |

---

## Error Codes

| Error | HTTP | Description |
|-------|------|-------------|
| `missing_field` | 400 | Required field not provided |
| `invalid_email` | 400 | Email format invalid |
| `invalid_password` | 400 | Password doesn't meet requirements |
| `username_taken` | 409 | Username already registered |
| `email_taken` | 409 | Email already registered |
| `invalid_credentials` | 401 | Email or password incorrect |
| `user_not_found` | 400 | User doesn't exist |
| `authorization_required` | 401 | JWT token missing |
| `invalid_token` | 401 | JWT token invalid or expired |

---

## See Also
- [Project API](./PROJECT_API.md)
- [PR Webhook API](./PR_WEBHOOK_API.md)
- [User Flows](./USER_FLOWS.md)
