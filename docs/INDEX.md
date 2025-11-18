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
2. Read **[USER_FLOWS.md](./USER_FLOWS.md)** for all workflows
3. Read **[PROJECT_API.md](./PROJECT_API.md)** for graph operations
4. Review **[PR_ANALYSIS_FLOW.md](./PR_ANALYSIS_FLOW.md)** to understand the core feature
5. Read the relevant API doc for your work (Project, PR Webhook, or User API)


## 📋 Document Descriptions

### [README.md](./README.md) - Project Overview
- Project mission and vision
- Technology stack (Python, Flask, PostgreSQL, Neo4j, etc.)
- High-level architecture diagrams
- Data model (User, Repository, Node, Edge)
- Core features and capabilities
- Deployment and development setup

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
- Troubleshooting guide

**Size**: ~500 lines | **Read Time**: 30 minutes

**Best for**: Understanding how PR analysis works internally

---

### [PROJECT_API.md](./PROJECT_API.md) - Graph Management API
Complete REST API reference for code graph operations:

#### Endpoints (6 total)
- `POST api/project/onboard` - Add repository
- `POST api/project/graph` - Query graph (nodes + edges)
- `POST api/project/edge` - Create manual edge

#### For Each Endpoint:
- Request format (HTTP method, URL, headers, body)
- Parameters table
- Success response (200/201/202)
- Error responses with status codes
- Request/response JSON examples
- Use cases

**Size**: ~400 lines | **Read Time**: 25 minutes

**Best for**: Graph management UI and Backend Integrations

---

### [PR_WEBHOOK_API.md](./PR_WEBHOOK_API.md) - GitHub Webhook Integration
Complete guide to setting up and using GitHub webhooks:

- GitHub webhook configuration steps
- Webhook signature verification (HMAC-SHA256)
- Event payload structure (GitHub → System)
- Trigger phrases list (12+ phrases for analysis invocation)
- Processing pipeline overview
- Error responses and edge cases
- Example workflow walkthrough

**Size**: ~450 lines | **Read Time**: 25 minutes

**Best for**: GitHub integration work

---

### [USER_API.md](./USER_API.md) - Authentication & User Management
Complete REST API reference for user authentication:

#### Endpoints (6 total)
- `POST /api/user/signup` - Register new user
- `POST /api/user/login` - Authenticate user
- `GET /api/user/profile` - Get user profile

#### For Each Endpoint:
- Request/response format
- Parameters and validation rules
- Success and error responses

#### Additional Content:
- Authentication flow diagram
- Client-side implementation examples
- Complete auth flow example scripts

**Size**: ~400 lines | **Read Time**: 25 minutes

**Best for**: Frontend developers and API consumers

---

## 🔗 Cross-References

### Common API Calls

#### Complete Sign Up & Onboard Flow
```
1. POST /api/user/signup → Get JWT token
2. POST /api/project/onboard → Add repository (using token)
3. Webhook triggers automatically when PR opens with trigger phrase
4. POST /api/project/graph → Query analysis results
```

#### Complete Authentication Flow
```
1. POST /api/user/signup OR POST /api/user/login
2. Store JWT in localStorage/sessionStorage
3. Include in all subsequent API calls as: Authorization: Bearer <token>
```

#### Complete PR Analysis Trigger
```
1. GitHub webhook receives PR.comment created event
2. Webhook POST /webhook/pr (GitHub → System)
3. System validates signature and trigger phrase
4. Async processing: clone → diff → AST → delta → impact → LLM → comment
5. Comment posted to PR automatically
```

---

## 📊 API Endpoints by Service

### User Service (`/api/user`)
- POST /api/user/signup - Register
- POST /api/user/login - Authenticate
- GET /api/user/profile - Get profile
- [Full Reference →](./USER_API.md)

### Project Service (`/api/project`)
- POST /api/project/onboard - Add repository
- POST /api/project/graph - Query graph
- POST /api/project/edge - Create edge
- [Full Reference →](./PROJECT_API.md)

### PR Service (`/webhook`)
- POST /webhook/pr - GitHub webhook endpoint
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
- **Trigger Phrase**: Text in PR comment that invokes analysis

---

See **[USER_API.md - Authentication Flow](./USER_API.md#authentication-flow-diagram)** section

---



