# User Controller API Reference

## Authentication
Public endpoints (`/signup`, `/login`) do not require authentication.
Protected endpoints (`/profile`) require JWT in `Authorization` header.

---

## Endpoints

### 1. User Sign Up
Register a new user account.

#### Request
```http
POST /api/user/signup
Content-Type: application/json

{
  "username": "johnD",
  "name": "John Doe",
  "password": "SecurePass123!"
}
```

#### Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `username` | string | Yes | Unique username (3-32 chars, alphanumeric + underscore) |
| `name` | string | Yes | Full Name |
| `password` | string | Yes | Strong Password |

#### Response (Success)
```json
HTTP/1.1 201 Created
{
    "id": 2,
    "name": "John Doe",
    "username": "johnD"
}
```

#### Error Responses
```json
HTTP/1.1 400 Bad Request
{
  "error": "username_taken",
  "message": "Username 'johnD' already exists"
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
POST /api/user/login
Content-Type: application/json

{
  "username": "johnD",
  "password": "SecurePass123!"
}
```

#### Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `username` | string | Yes | User's registered username |
| `password` | string | Yes | User's password |

#### Response (Success)
```json
HTTP/1.1 200 OK
{
    "profile": {
        "id": 1,
        "name": "John Doe",
        "repos": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "repo_name": "MyJavaProject",
                "repo_url": "https://github.com/user/my-java-project.git",
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440002",
                "repo_name": "PythonLib",
                "repo_url": "https://github.com/user/python-lib.git",
            }
        ],
        "username": "johnD"
    },
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNTUwZTg0MDAi..."
}
```

#### Response Fields
| Field | Type | Description |
|-------|------|-------------|
| `profile` | object | User details |
| `token` | string | JWT token (valid for 24 hours by default) |

#### Error Responses
```json
HTTP/1.1 401 Unauthorized
{
  "error": "invalid_credentials",
  "message": "name or password is incorrect"
}
```

```json
HTTP/1.1 400 Bad Request
{
  "error": "user_not_found",
  "message": "No user registered with name 'John Doe'"
}
```

```json
HTTP/1.1 400 Bad Request
{
  "error": "missing_field",
  "message": "Required field 'usernname' missing"
}
```

---

### 3. Get User Profile
Retrieve authenticated user's profile and repositories.

#### Request
```http
GET /api/user/profile
Authorization: Bearer <JWT_TOKEN>
```

#### Response
```json
HTTP/1.1 200 OK
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "johnD",
    "name": "John Doe",
    "repos": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "repo_name": "MyJavaProject",
            "repo_url": "https://github.com/user/my-java-project.git"
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440002",
            "repo_name": "PythonLib",
            "repo_url": "https://github.com/user/python-lib.git"
        }
    ]
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

## Authentication Flow Diagram

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       │ 1. POST /api/user/signup
       │    username, name, password
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
       ├─► POST /api/project/onboard
       ├─► POST /api/project/graph
       ├─► GET /api/project/nodes
       └─► ... (all protected routes)
       │
       │ 3. On login retry (token expired)
       │    POST /api/user/login to get new token
       ▼
┌─────────────────────────────────┐
│  Refresh JWT & Update Storage   │
└─────────────────────────────────┘
```

---

## See Also
- [Project API](./PROJECT_API.md)
- [PR Webhook API](./PR_WEBHOOK_API.md)
- [User Flows](./USER_FLOWS.md)
