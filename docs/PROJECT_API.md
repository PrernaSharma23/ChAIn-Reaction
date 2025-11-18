# Project Controller API Reference


## Authentication
All endpoints (except public routes) require a JWT token in the `Authorization` header:
```
Authorization: Bearer <JWT_TOKEN>
```

---

## Endpoints

### 1. Onboard Repository
Create or link a GitHub repository to the user's account and trigger initial processing.

#### Request
```http
POST /api/project/onboard
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
  "repo_name": "MyJavaProject",
  "repo_url": "https://github.com/user/my-java-project.git"
}
```

#### Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `repo_name` | string | Yes | Human-readable repository name |
| `repo_url` | string | Yes | Git HTTPS URL of the repository |

#### Response (First Time - New Repository)
```json
HTTP/1.1 202 Accepted
{
  "saved_repo": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "repo_name": "MyJavaProject",
    "repo_url": "https://github.com/user/my-java-project.git",
    "is_new": true
  },
  "message": "Repository onboarded and processing started asynchronously"
}
```

#### Response (Existing Repository)
```json
HTTP/1.1 200 OK
{
  "saved_repo": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "repo_name": "MyJavaProject",
    "repo_url": "https://github.com/user/my-java-project.git",
    "is_new": false
  },
  "message": "Repository added to user (already exists in system)"
}
```

#### Error Responses
```json
HTTP/1.1 400 Bad Request
{
  "error": "repo_url missing"
}
```

```json
HTTP/1.1 401 Unauthorized
{
  "error": "Authorization token required"
}
```

---

### 2. Query Graph for Repositories
Retrieve nodes and edges for one or more repositories, useful for visualization.

#### Request
```http
POST /api/project/graph
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
  "repo_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "550e8400-e29b-41d4-a716-446655440001"
  ]
}
```

#### Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `repo_ids` | array[string] | Yes | List of repository IDs to query |

#### Response
```json
HTTP/1.1 200 OK
{
  "nodes": [
    {
      "id": "550e8400:src/main/java/com/example:class:UserService",
      "repoId": "550e8400-e29b-41d4-a716-446655440000",
      "repoName": "MyJavaProject",
      "type": "class",
      "name": "UserService",
      "path": "src/main/java/com/example",
      "meta": "{\"visibility\": \"public\"}",
      "labels": ["Entity"]
    },
    {
      "id": "550e8400:src/main/java/com/example:method:authenticate",
      "repoId": "550e8400-e29b-41d4-a716-446655440000",
      "repoName": "MyJavaProject",
      "type": "method",
      "name": "authenticate",
      "path": "src/main/java/com/example",
      "meta": "{}",
      "labels": ["Entity"]
    }
  ],
  "edges": [
    {
      "from": "550e8400:src/main/java/com/example:class:UserService",
      "type": "CONTAINS",
      "to": "550e8400:src/main/java/com/example:method:authenticate"
    },
    {
      "from": "550e8401:src/api:module:auth",
      "type": "DEPENDS_ON",
      "to": "550e8400:src/main/java/com/example:class:UserService"
    }
  ]
}
```

#### Error Responses
```json
HTTP/1.1 400 Bad Request
{
  "error": "repo_ids must be a non-empty list"
}
```

```json
HTTP/1.1 500 Internal Server Error
{
  "error": "Neo4j query timeout"
}
```


---

### 5. Create Edge (Manual Dependency)
Manually create a dependency edge between two nodes to represent relationships not captured by AST.

#### Request
```http
POST /api/project/edge
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
  "from": "550e8400:src/main/java/com/example:class:UserService",
  "to": "550e8401:src/api:module:auth",
  "type": "DEPENDS_ON"
}
```

#### Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `from` | string | Yes | Source node UID |
| `to` | string | Yes | Destination node UID |
| `type` | string | Yes | Edge type: CONTAINS, DEPENDS_ON, READS_FROM, WRITES_TO |

#### Response
```json
HTTP/1.1 200 OK
{
  "ok": true,
  "from": "550e8400:src/main/java/com/example:class:UserService",
  "to": "550e8401:src/api:module:auth",
  "type": "DEPENDS_ON"
}
```

#### Error Responses
```json
HTTP/1.1 400 Bad Request
{
  "error": "from, to and type are required"
}
```

```json
HTTP/1.1 400 Bad Request
{
  "error": "one_or_both_nodes_missing"
}
```

```json
HTTP/1.1 400 Bad Request
{
  "error": "Invalid edge type: INVALID_TYPE. Allowed: CONTAINS, DEPENDS_ON, READS_FROM, WRITES_TO"
}
```



---

## Node Structure

### Node Object
```typescript
{
  // Unique identifier: "repo_id:path:kind:name"
  "id": "550e8400:src/main/java/com/example:class:UserService",
  
  // Repository association
  "repoId": "550e8400-e29b-41d4-a716-446655440000",
  "repoName": "MyJavaProject",
  
  // Entity classification
  "type": "class",  // class, method, function, file, module, etc.
  "name": "UserService",
  "path": "src/main/java/com/example",
  
  // Neo4j labels
  "labels": ["Entity"],
  
  // Additional metadata (JSON string)
  "meta": "{\"visibility\": \"public\", \"is_abstract\": false}"
}
```

---

## Edge Structure

### Edge Object
```typescript
{
  // Source node UID
  "from": "550e8400:src/main/java/com/example:class:UserService",
  
  // Relationship type
  "type": "CONTAINS",  // or DEPENDS_ON, READS_FROM, WRITES_TO
  
  // Target node UID
  "to": "550e8400:src/main/java/com/example:method:authenticate"
}
```

### Edge Types
| Type | Meaning |
|------|---------|
| `CONTAINS` | Parent-child relationship (e.g., class contains method) |
| `DEPENDS_ON` | Functional dependency (e.g., class/Method A calls class/Method B) |
| `READS_FROM` | Data flow (e.g., code reads from table/variable) |
| `WRITES_TO` | Data flow (e.g., code writes to table/variable) |

---

## Examples

### Example 1: Onboard Multiple Repos
```bash
#!/bin/bash

TOKEN="your-jwt-token-here"
API="https://api.chain-reaction.example.com"

# Repo 1
curl -X POST "$API/api/project/onboard" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_name": "AuthService",
    "repo_url": "https://github.com/myorg/auth-service.git"
  }'

# Repo 2
curl -X POST "$API/api/project/onboard" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_name": "PaymentService",
    "repo_url": "https://github.com/myorg/payment-service.git"
  }'
```

### Example 2: Query Graph for Visualization
```bash
curl -X POST "https://api.chain-reaction.example.com/api/project/graph" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_ids": ["repo-id-1", "repo-id-2"]
  }' | jq '.'
```

### Example 3: Create Cross-Repo Dependency
```bash
curl -X POST "https://api.chain-reaction.example.com/api/project/edge" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "from": "repo1:src/PaymentProcessor:class:PaymentHandler",
    "to": "repo2:src/audit:class:AuditLogger",
    "type": "DEPENDS_ON"
  }'
```

---

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Request succeeded |
| 202 | Accepted - Async operation queued |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Missing/invalid JWT |
| 500 | Internal Server Error - Server error |

---

## Error Codes

| Error | Description |
|-------|-------------|
| `authorization_required` | JWT token missing or invalid |
| `repo_url missing` | Required field `repo_url` not provided |
| `repo_ids must be a non-empty list` | `repo_ids` must be array with at least one element |
| `one_or_both_nodes_missing` | Source or destination node not found in graph |
| `Invalid edge type: ...` | Edge type not in allowed list |

---

## See Also
- [User Flows](./USER_FLOWS.md)
- [PR Analysis Flow](./PR_ANALYSIS_FLOW.md)
- [PR Webhook API](./PR_WEBHOOK_API.md)
