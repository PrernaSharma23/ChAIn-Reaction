# ChAIn-Reaction Documentation Index

Welcome to the ChAIn-Reaction documentation! This folder contains comprehensive guides for developers, API consumers, and system administrators.

---

## 📚 Documentation Overview

### Quick Navigation
| Document | Audience | Purpose |
|----------|----------|---------|
| **[README.md](./README.md)** | Everyone | Project overview, architecture, tech stack |
| **[USER_FLOWS.md](./USER_FLOWS.md)** | Product Managers, QA | End-to-end user workflows with examples |
| **[PR_ANALYSIS_FLOW.md](./PR_ANALYSIS_FLOW.md)** | Developers, DevOps | How PR analysis pipeline works internally |
| **[PROJECT_API.md](./PROJECT_API.md)** | Backend/Frontend Devs | Complete graph management API reference |
| **[PR_WEBHOOK_API.md](./PR_WEBHOOK_API.md)** | DevOps, Integrations | GitHub webhook setup and integration |
| **[USER_API.md](./USER_API.md)** | Frontend Devs, Auth | Authentication and user management API |

---

## 🚀 Getting Started

### For New Developers
1. Start with **[README.md](./README.md)** to understand the project
2. Review **[PR_ANALYSIS_FLOW.md](./PR_ANALYSIS_FLOW.md)** to understand the core feature
3. Read the relevant API doc for your work (Project, PR Webhook, or User API)

### For Frontend Developers
1. Read **[USER_API.md](./USER_API.md)** for authentication
2. Read **[PROJECT_API.md](./PROJECT_API.md)** for graph operations
3. Review **[USER_FLOWS.md](./USER_FLOWS.md)** for UX patterns

### For DevOps / Infrastructure
1. Check **[README.md](./README.md)** Deployment section
2. Review **[PR_WEBHOOK_API.md](./PR_WEBHOOK_API.md)** for webhook setup
3. See deployment guide in README

### For Product / QA
1. Read **[USER_FLOWS.md](./USER_FLOWS.md)** for all workflows
2. Review **[PR_ANALYSIS_FLOW.md](./PR_ANALYSIS_FLOW.md)** for feature details
3. Check error scenarios in API references

---

## 📋 Document Descriptions

### [README.md](./README.md) - Project Overview
- Project mission and vision
- Technology stack (Python, Flask, PostgreSQL, Neo4j, etc.)
- High-level architecture diagrams
- Data model (User, Repository, Node, Edge)
- Core features and capabilities
- Deployment and development setup
- Contributing guidelines

**Size**: ~200 lines | **Read Time**: 10 minutes

---

### [USER_FLOWS.md](./USER_FLOWS.md) - End-to-End Workflows
Detailed walkthrough of 6 primary user journeys with request/response examples:

1. **Sign Up** - New user registration
2. **Login** - Authentication and token retrieval
3. **Repository Onboarding** - Adding repos to system
4. **Graph Visualization** - Querying and displaying code structure
5. **Edge Creation** - Manual dependency linking
6. **Profile Management** - User settings and preferences

**Size**: ~400 lines | **Read Time**: 20 minutes

**Best for**: Understanding the complete user experience

---

### [PR_ANALYSIS_FLOW.md](./PR_ANALYSIS_FLOW.md) - PR Analysis Pipeline
In-depth technical documentation of the PR analysis feature:

- Complete 8-step processing pipeline (webhook → diff → AST → delta → impact → LLM → comment)
- Detailed architecture diagrams and data flow
- Error handling and retry logic (exponential backoff for LLM)
- Security considerations (signature verification, token handling)
- Performance notes and optimization tips
- Caching strategy for large graphs
- Troubleshooting guide

**Size**: ~500 lines | **Read Time**: 30 minutes

**Best for**: Understanding how PR analysis works internally

---

### [PROJECT_API.md](./PROJECT_API.md) - Graph Management API
Complete REST API reference for code graph operations:

#### Endpoints (6 total)
- `POST /project/onboard` - Add repository
- `POST /project/graph` - Query graph (nodes + edges)
- `GET /project/nodes` - Get all nodes
- `GET /project/edges` - Get all edges
- `POST /project/edge` - Create manual edge
- `DELETE /project/clear` - Clear graph

#### For Each Endpoint:
- Request format (HTTP method, URL, headers, body)
- Parameters table
- Success response (200/201/202)
- Error responses with status codes
- Request/response JSON examples
- Use cases

**Size**: ~400 lines | **Read Time**: 25 minutes

**Best for**: Building graph management UI and backend integrations

---

### [PR_WEBHOOK_API.md](./PR_WEBHOOK_API.md) - GitHub Webhook Integration
Complete guide to setting up and using GitHub webhooks:

- GitHub webhook configuration steps
- Webhook signature verification (HMAC-SHA256)
- Event payload structure (GitHub → System)
- Trigger phrases list (12+ phrases for analysis invocation)
- Processing pipeline overview
- Error responses and edge cases
- Security best practices
- Debugging and manual testing guide
- Example workflow walkthrough

**Size**: ~450 lines | **Read Time**: 25 minutes

**Best for**: DevOps engineers and GitHub integration work

---

### [USER_API.md](./USER_API.md) - Authentication & User Management
Complete REST API reference for user authentication:

#### Endpoints (6 total)
- `POST /auth/signup` - Register new user
- `POST /auth/login` - Authenticate user
- `GET /auth/profile` - Get user profile
- `POST /auth/verify_token` - Verify JWT
- `PUT /auth/profile` - Update profile
- `POST /auth/logout` - Revoke token

#### For Each Endpoint:
- Request/response format
- Parameters and validation rules
- Success and error responses
- JWT token structure and claims
- Password requirements
- Token expiration policies

#### Additional Content:
- Authentication flow diagram
- Security best practices
- Client-side implementation examples
- Complete auth flow example scripts

**Size**: ~400 lines | **Read Time**: 25 minutes

**Best for**: Frontend developers and API consumers

---

## 🔗 Cross-References

### Common API Calls

#### Complete Sign Up & Onboard Flow
```
1. POST /auth/signup → Get JWT token
2. POST /project/onboard → Add repository (using token)
3. Webhook triggers automatically when PR opens with trigger phrase
4. POST /project/graph → Query analysis results
```

#### Complete Authentication Flow
```
1. POST /auth/signup OR POST /auth/login
2. Store JWT in localStorage/sessionStorage
3. Include in all subsequent API calls as: Authorization: Bearer <token>
```

#### Complete PR Analysis Trigger
```
1. GitHub webhook receives PR.opened event
2. Webhook POST /pr/webhook/pr (GitHub → System)
3. System validates signature and trigger phrase
4. Async processing: clone → diff → AST → delta → impact → LLM → comment
5. Comment posted to PR automatically
```

---

## 📊 API Endpoints by Service

### User Service (`/auth`)
- POST /auth/signup - Register
- POST /auth/login - Authenticate
- GET /auth/profile - Get profile
- PUT /auth/profile - Update profile
- POST /auth/verify_token - Verify token
- [Full Reference →](./USER_API.md)

### Project Service (`/project`)
- POST /project/onboard - Add repository
- POST /project/graph - Query graph
- GET /project/nodes - All nodes
- GET /project/edges - All edges
- POST /project/edge - Create edge
- DELETE /project/clear - Clear graph
- [Full Reference →](./PROJECT_API.md)

### PR Service (`/pr`)
- POST /pr/webhook/pr - GitHub webhook endpoint
- [Full Reference →](./PR_WEBHOOK_API.md)

---

## 🏗️ Architecture Quick Reference

### Tech Stack
- **Backend**: Python 3.12 + Flask
- **Databases**: PostgreSQL (metadata), Neo4j (graphs)
- **Auth**: PyJWT + JWT Bearer tokens
- **Code Analysis**: Tree-Sitter + custom extractors
- **LLM**: OpenAI GPT-4 (with retry logic)
- **Git**: GitPython for repo management
- **Webhooks**: GitHub with HMAC-SHA256 verification

### Data Model (Simplified)
```
User
├── Repositories (many)
│   └── Nodes (many, in Neo4j)
│       └── Edges (many, in Neo4j)
```

### Core Concepts
- **Node**: Code element (class, method, function, module)
- **Edge**: Relationship between nodes (depends_on, contains, calls)
- **Delta**: Changes introduced by a PR
- **Impact**: All nodes affected by a delta
- **Trigger Phrase**: Text in PR description that invokes analysis

---

## 🔍 Troubleshooting & FAQ

### "Which API should I use?"
| Goal | Use This API |
|------|--------------|
| Register/login user | USER_API |
| Add repository | PROJECT_API (POST /onboard) |
| Get code structure | PROJECT_API (POST /graph) |
| Setup GitHub webhook | PR_WEBHOOK_API |
| Create dependency link | PROJECT_API (POST /edge) |

### "Where do I find error codes?"
- **Authentication errors**: [USER_API.md](./USER_API.md#error-codes)
- **Graph API errors**: [PROJECT_API.md](./PROJECT_API.md#error-codes)
- **Webhook errors**: [PR_WEBHOOK_API.md](./PR_WEBHOOK_API.md#error-responses)

### "How do I debug webhooks?"
See **[PR_WEBHOOK_API.md - Debugging Webhooks](./PR_WEBHOOK_API.md#debugging-webhooks)** section

### "What's the JWT token format?"
See **[USER_API.md - JWT Token Structure](./USER_API.md#jwt-token-structure)** section

### "How do I handle token expiration?"
See **[USER_API.md - Authentication Flow](./USER_API.md#authentication-flow-diagram)** section

---

## 📝 Common Code Examples

### Example 1: Complete Backend Integration (Python)
```python
import requests

API_BASE = "https://api.chain-reaction.example.com"

# Step 1: Signup
signup_response = requests.post(
    f"{API_BASE}/auth/signup",
    json={
        "username": "dev_user",
        "email": "dev@example.com",
        "password": "SecurePass123!"
    }
)
token = signup_response.json()['token']

# Step 2: Onboard repository
headers = {"Authorization": f"Bearer {token}"}
onboard_response = requests.post(
    f"{API_BASE}/project/onboard",
    json={
        "repo_name": "MyProject",
        "repo_url": "https://github.com/user/myproject.git"
    },
    headers=headers
)

# Step 3: Query graph
graph_response = requests.post(
    f"{API_BASE}/project/graph",
    json={"repo_ids": [onboard_response.json()['saved_repo']['id']]},
    headers=headers
)
nodes, edges = graph_response.json()['nodes'], graph_response.json()['edges']
```

### Example 2: Frontend Integration (JavaScript/React)
```javascript
const API_BASE = "https://api.chain-reaction.example.com";

// Signup
const signup = async (username, email, password) => {
  const response = await fetch(`${API_BASE}/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, email, password })
  });
  const data = await response.json();
  localStorage.setItem('jwt_token', data.token);
  return data.user;
};

// Make authenticated request
const apiCall = async (endpoint, options = {}) => {
  const token = localStorage.getItem('jwt_token');
  return fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
};

// Onboard repository
const onboardRepo = async (repo_name, repo_url) => {
  const response = await apiCall('/project/onboard', {
    method: 'POST',
    body: JSON.stringify({ repo_name, repo_url })
  });
  return response.json();
};
```

### Example 3: Webhook Testing (Bash)
```bash
# See full example in: PR_WEBHOOK_API.md - Debugging Webhooks
```

---

## 📞 Support & Contributing

### Getting Help
1. Check relevant API reference (USER_API, PROJECT_API, PR_WEBHOOK_API)
2. Search error codes in [Troubleshooting & FAQ](#troubleshooting--faq)
3. Review examples in respective documentation
4. Check GitHub issues: [ChAIn-Reaction Issues](https://github.com/impact-unplugged-hackathon/chain-reaction/issues)

### Contributing Documentation
1. Update relevant `.md` file in `/docs`
2. Follow existing formatting and structure
3. Include request/response examples
4. Add error cases and edge cases
5. Submit PR with documentation improvements

---

## 📄 Document Versions

| Document | Last Updated | Version |
|----------|--------------|---------|
| README.md | Nov 18, 2025 | 1.0 |
| USER_FLOWS.md | Nov 18, 2025 | 1.0 |
| PR_ANALYSIS_FLOW.md | Nov 18, 2025 | 1.0 |
| PROJECT_API.md | Nov 18, 2025 | 1.0 |
| PR_WEBHOOK_API.md | Nov 18, 2025 | 1.0 |
| USER_API.md | Nov 18, 2025 | 1.0 |
| INDEX.md (this file) | Nov 18, 2025 | 1.0 |

---

## 🎯 Quick Start by Role

### I'm a Frontend Developer
1. Read: [USER_FLOWS.md](./USER_FLOWS.md) - understand UX
2. Implement: [USER_API.md](./USER_API.md) - auth forms
3. Implement: [PROJECT_API.md](./PROJECT_API.md) - graph visualization
4. Reference: [USER_API.md](./USER_API.md#examples) - code examples

### I'm a Backend Developer
1. Read: [README.md](./README.md) - architecture
2. Study: [PR_ANALYSIS_FLOW.md](./PR_ANALYSIS_FLOW.md) - core logic
3. Reference: All API docs for endpoints you're working on
4. Integrate: [PR_WEBHOOK_API.md](./PR_WEBHOOK_API.md) - webhook handling

### I'm a DevOps Engineer
1. Read: [README.md](./README.md) - deployment section
2. Configure: [PR_WEBHOOK_API.md](./PR_WEBHOOK_API.md) - GitHub webhooks
3. Monitor: Logs and error responses from all services
4. Maintain: Environment variables and secrets

### I'm a QA / Tester
1. Learn: [USER_FLOWS.md](./USER_FLOWS.md) - all workflows
2. Test: [USER_API.md](./USER_API.md) - auth edge cases
3. Test: [PROJECT_API.md](./PROJECT_API.md) - graph operations
4. Test: [PR_WEBHOOK_API.md](./PR_WEBHOOK_API.md) - webhook scenarios

---

**Happy coding! 🚀**
