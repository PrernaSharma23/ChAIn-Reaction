# User Flows & Workflows

## 1. Signup Flow

### Overview
New users register for ChAIn Reaction and receive a JWT token for API access.

### Steps
```
┌─────────────┐
│   User      │
└──────┬──────┘
       │
       │ 1. POST /api/user/signup
       │    { username, name, password }
       ▼
┌──────────────────────┐
│  User Service        │
│  ├─ Hash password   │
│  ├─ Store in DB    │
│  └─ Return user    │
└──────────────────────┘
       │
       │ 2. Response
       │    { id, username, name }
       ▼
┌─────────────┐
│   User      │
│ (Registered)│
└─────────────┘
```

### Request
```json
POST /api/user/signup
Content-Type: application/json

{
  "username": "john_doe",
  "name": "John Doe",
  "password": "securepassword"
}
```

### Response
```json
200 OK
{
  "id": 1,
  "username": "john_doe",
  "name": "John Doe"
}
```

### Error Cases
- `400 Bad Request` - Missing fields
- `409 Conflict` - Username already exists

---

## 2. Login Flow

### Overview
Existing users authenticate and receive a JWT token valid for subsequent API calls.

### Steps
```
┌─────────────┐
│   User      │
└──────┬──────┘
       │
       │ 1. POST /api/user/login
       │    { username, password }
       ▼
┌──────────────────────┐
│  User Service        │
│  ├─ Lookup user    │
│  ├─ Verify password │
│  ├─ Generate JWT   │
│  └─ Return token   │
└──────────────────────┘
       │
       │ 2. Response
       │    { token, profile }
       ▼
┌─────────────────────────┐
│   User (Authenticated)  │
│   Stores JWT in client  │
└─────────────────────────┘
```

### Request
```json
POST /api/user/login
Content-Type: application/json

{
  "username": "john_doe",
  "password": "securepassword"
}
```

### Response
```json
200 OK
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "profile": {
    "id": 1,
    "username": "john_doe",
    "name": "John Doe",
    "repos": [
      {"id": "uuid-1", "name": "MyProject", "url": "https://github.com/user/myproject"}
    ]
  }
}
```

### Error Cases
- `401 Unauthorized` - Invalid credentials
- `400 Bad Request` - Missing fields

---

## 3. Repository Onboarding Flow

### Overview
User adds a GitHub repository to ChAIn Reaction. On first onboarding, the system clones the repo, extracts the dependency graph, and stores it. Subsequent users adding the same repo avoid re-processing.

### Steps
```
┌─────────────────────────────────────────────────────────────┐
│  User A onboards Repo X (First Time)                        │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────────┐
        ▼                             ▼
┌────────────────────────┐   ┌────────────────────┐
│ ProjectService         │   │ UserRepository     │
│ ├─ Clone Repo X       │   │ ├─ Create entry    │
│ ├─ Extract AST nodes  │   │ │ in repos table    │
│ ├─ Build edges        │   │ └─ Map to user     │
│ └─ Store in Neo4j     │   └────────────────────┘
└────────────────────────┘
        │
        │ Async Processing
        │ (user gets 202 response immediately)
        │
        ├─ Extraction complete
        ├─ Graph stored
        └─ Ready for analysis

            Later...

┌─────────────────────────────────────────────────────────────┐
│  User B onboards same Repo X (Already Processed)            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │ UserRepository             │
        │ ├─ Repo exists?  YES       │
        │ ├─ Skip processing         │
        │ └─ Map existing repo to B  │
        └────────────────────────────┘
```

### Request
```json
POST /api/project/onboard
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
  "repo_name": "MyJavaProject",
  "repo_url": "https://github.com/user/my-java-project.git"
}
```

### Response (First Time - New Repo)
```json
202 Accepted
{
  "saved_repo": {
    "id": "uuid-1",
    "repo_name": "MyJavaProject",
    "repo_url": "https://github.com/user/my-java-project.git",
    "is_new": true
  },
  "message": "Repository onboarded"
}
```

### Response (Subsequent User - Existing Repo)
```json
200 OK
{
  "saved_repo": {
    "id": "uuid-1",
    "repo_name": "MyJavaProject",
    "repo_url": "https://github.com/user/my-java-project.git",
    "is_new": false
  },
  "message": "Repository added to user (already exists in system)"
}
```

### Error Cases
- `401 Unauthorized` - Missing/invalid JWT
- `400 Bad Request` - Missing repo_url
- `500 Internal Server Error` - Git clone or processing failure

---

## 4. Graph Visualization Flow

### Overview
User queries the dependency graph to visualize code structure and relationships across repositories.

### Steps
```
┌────────────┐
│   User     │
└────┬───────┘
     │
     │ 1. POST /api/project/graph
     │    { repo_ids: ["uuid-1", "uuid-2"] }
     ▼
┌─────────────────────────────┐
│  Neo4j Repository           │
│  ├─ Match nodes for repos  │
│  ├─ Match edges between    │
│  │   nodes in those repos   │
│  └─ Return results         │
└─────────────────────────────┘
     │
     │ 2. Response
     │    { nodes: [...], edges: [...] }
     ▼
┌────────────────────────────┐
│   UI / Frontend            │
│  ├─ Render nodes           │
│  ├─ Draw edges            │
│  └─ Allow interaction     │
└────────────────────────────┘
```

### Request
```json
POST /api/project/graph
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
  "repo_ids": ["uuid-1", "uuid-2"]
}
```

### Response
```json
200 OK
{
  "nodes": [
    {
      "id": "repo1:src/main/java/com/example:Class:UserService",
      "repoId": "uuid-1",
      "repoName": "AuthService",
      "type": "class",
      "name": "UserService",
      "path": "src/main/java/com/example",
      "labels": ["Entity"]
    },
    {
      "id": "repo1:src/main/java/com/example:Method:authenticate",
      "repoId": "uuid-1",
      "repoName": "AuthService",
      "type": "method",
      "name": "authenticate",
      "path": "src/main/java/com/example",
      "labels": ["Entity"]
    }
  ],
  "edges": [
    {
      "from": "repo1:src/main/java/com/example:Class:UserService",
      "type": "CONTAINS",
      "to": "repo1:src/main/java/com/example:Method:authenticate"
    },
    {
      "from": "repo2:src/main/python:Module:api",
      "type": "DEPENDS_ON",
      "to": "repo1:src/main/java/com/example:Class:UserService"
    }
  ]
}
```

### Error Cases
- `401 Unauthorized` - Missing/invalid JWT
- `400 Bad Request` - repo_ids not a list or empty
- `500 Internal Server Error` - Neo4j connection error

---

## 5. Creating Custom Edges (Manual Dependencies)

### Overview
Users can manually create edges between nodes to represent dependencies not captured by AST (e.g., API contracts, data flows).

### Steps
```
┌────────────┐
│   User     │
│ (Viewing   │
│  graph)    │
└────┬───────┘
     │
     │ 1. POST /api/project/edge
     │    { from, to, type }
     ▼
┌──────────────────────────────┐
│  Neo4j Repository            │
│  ├─ Validate nodes exist    │
│  ├─ Validate edge type      │
│  ├─ Create/merge edge       │
│  └─ Return status           │
└──────────────────────────────┘
     │
     │ 2. Response
     │    { ok: true, ... }
     ▼
┌──────────────────────────┐
│   Graph Updated          │
│  New edge visible on     │
│  subsequent queries      │
└──────────────────────────┘
```

### Request
```json
POST /api/project/edge
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
  "from": "repo1:src/main/java/com/example:Class:UserService",
  "to": "repo2:src/main/python:Module:api",
  "type": "DEPENDS_ON"
}
```

### Response
```json
200 OK
{
  "ok": true,
  "from": "repo1:src/main/java/com/example:Class:UserService",
  "to": "repo2:src/main/python:Module:api",
  "type": "DEPENDS_ON"
}
```

### Error Cases
- `401 Unauthorized` - Missing/invalid JWT
- `400 Bad Request` - Missing from, to, or type; or one/both nodes don't exist
- `400 Bad Request` - Invalid edge type (not in CONTAINS, DEPENDS_ON, READS_FROM, WRITES_TO)

---

## 6. User Profile & Repository Management

### Overview
Users can view their profile, associated repositories, and manage onboarded projects.

### Get Profile Request
```json
GET /api/user/profile
Authorization: Bearer <JWT_TOKEN>
```

### Get Profile Response
```json
200 OK
{
  "id": 1,
  "username": "john_doe",
  "name": "John Doe",
  "repos": [
    {
      "id": "uuid-1",
      "name": "MyJavaProject",
      "url": "https://github.com/user/my-java-project.git"
    },
    {
      "id": "uuid-2",
      "name": "MyPythonProject",
      "url": "https://github.com/user/my-python-project.git"
    }
  ]
}
```

---

## Summary

| Action | Endpoint | Auth | Response |
|--------|----------|------|----------|
| Sign up | `POST /api/user/signup` | No | User info |
| Login | `POST /api/user/login` | No | JWT token + profile |
| Get Profile | `GET /api/user/profile` | Yes | User + repos |
| Onboard Repo | `POST /api/project/onboard` | Yes | Repo info + processing status |
| Query Graph | `POST /api/project/graph` | Yes | Nodes + edges |
| Create Edge | `POST /api/project/edge` | Yes | Edge info |
