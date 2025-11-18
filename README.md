# ChAIn Reaction - Impact Analysis Platform

> 📚 **Start here**: [Documentation Index](./docs/INDEX.md) for complete guides and API references

## Project Overview

**ChAIn Reaction** is an intelligent code impact analysis platform that helps development teams understand the ripple effects of code changes across interconnected repositories. By building dependency graphs of codebases and leveraging LLM-powered analysis, it provides data-driven insights into how pull request changes propagate through the system.

### What It Does

- **Dependency Graph Extraction**: Automatically extracts Abstract Syntax Trees (AST) from Java and Python codebases, identifying entities (classes, methods, functions) and their relationships.
- **Cross-Repository Impact Analysis**: Connects multiple repositories to track dependencies and data flows across team projects.
- **Pull Request Impact Detection**: When a developer opens a PR, the system:
  - Compares changed code against the baseline dependency graph
  - Identifies all potentially impacted nodes (entities that depend on the changes)
  - Uses LLM to analyze semantic impact and suggest testing areas
  - Posts findings as comments on the GitHub PR
- **Real-Time Notifications**: GitHub webhook integration provides instant feedback during code review.

**[→ Learn more about PR Analysis Flow](./docs/PR_ANALYSIS_FLOW.md)**

---

## Tech Stack & Technologies

### Backend
- **Language**: Python 3.12
- **Web Framework**: Flask (lightweight REST API)
- **Database**: 
  - PostgreSQL (user & repository metadata)
  - Neo4j (dependency graph storage & querying)
- **Authentication**: JWT tokens for API security
- **Task Queue**: Async task runner for background processing

### Code Analysis
- **Tree-Sitter**: Language-agnostic parsing for Java and Python
- **AST Extraction**: Custom extractors for Java (via Tree-Sitter) and Python
- **Language Support**: Java, Python

### LLM Integration
- **Provider**: OpenAI (GPT-4)
- **Retry Logic**: Exponential backoff with jitter for reliability
- **Usage**: Semantic analysis of impacted code regions

### GitHub Integration
- **Webhooks**: Receive PR comments and events in real-time
- **HMAC Verification**: Secure webhook payload validation (SHA-256)
- **API**: REST calls to post comments and retrieve file diffs


---

## High-Level Architecture

```
┌─────────────────┐
│   GitHub UI     │
│   (PR, Issues)  │
└────────┬────────┘
         │
         │ (Webhook Events)
         ▼
┌─────────────────────────────────┐
│   Flask Application             │
├─────────────────────────────────┤
│  Controllers                    │
│  ├─ user_controller            │
│  ├─ project_controller         │
│  └─ pull_request_controller    │
│                                 │
│  Services                       │
│  ├─ user_service              │
│  ├─ project_service           │
│  ├─ pull_request_service      │
│  ├─ llm_service (GPT-4)        │
│  └─ comment_notification      │
│                                 │
│  Processors                     │
│  ├─ repo_processor            │
│  ├─ tree_sitter_extractor     │
│  └─ diff_processor            │
└────────┬────────────────────────┘
         │
    ┌────┴────┬──────────┐
    ▼         ▼          ▼
PostgreSQL  Neo4j   OpenAI API
(Users)     (Graphs) (LLM)
```

**[→ See detailed PR Analysis Flow diagram](./docs/PR_ANALYSIS_FLOW.md#processing-pipeline)**

---

## Data Model

### Entity Relationships

```
User (PostgreSQL)
  ├─ many Repos (association table: user_repos)
  └─ Authentication via JWT

Repo (PostgreSQL + Neo4j)
  ├─ id (UUID, primary key)
  ├─ name (unique)
  ├─ url (unique)
  └─ associated Users

GraphNode (Neo4j)
  ├─ uid (unique: "repo_id:path:kind:name")
  ├─ repo_id
  ├─ kind (repo, file, class, method, function, etc.)
  ├─ name
  ├─ path
  └─ meta (JSON metadata)

GraphEdge (Neo4j)
  ├─ type (CONTAINS, DEPENDS_ON, READS_FROM, WRITES_TO)
  ├─ source node (uid)
  └─ target node (uid)
```

---

## Key Features

### 1. User Management
- Sign up / login with JWT authentication
- User profile with associated repositories
- Per-user isolation of data

### 2. Repository Onboarding
- Git clone and shallow extraction of structure
- Automatic AST parsing (Java & Python)
- Deduplication: same repo URL not re-processed for new users
- Async processing to avoid blocking API

### 3. Dependency Graph
- Nodes represent code entities (classes, methods, functions, files)
- Edges represent relationships (contains, depends_on, reads, writes)
- Cross-repo edges tracked via qualified UIDs

### 4. Pull Request Analysis
- Triggered by GitHub webhook (comment with trigger phrases)
- Diff extraction and AST comparison
- Delta computation: identify added/modified/deleted nodes
- Impact propagation: BFS/DFS to find all affected downstream nodes
- LLM semantic analysis of impacted regions
- Results posted back as PR comments

### 5. Graph Querying
- Retrieve nodes/edges for specific repos
- Cross-repo dependency traversal
- Entity lookup by name

---

## Data Flow

### Setup & Onboarding
```
1. User signs up (email/password) → JWT token issued
2. User logs in → receives JWT token
3. User provides repo URL → backend clones & extracts graph
4. Graph stored in Neo4j (nodes + edges)
5. Repo metadata stored in PostgreSQL
```

**[→ See user workflow with examples](./docs/USER_FLOWS.md)**

### Pull Request Analysis
```
1. Developer opens PR on monitored repo
2. Comment with trigger phrase posted on PR
3. GitHub webhook received by ChAIn Reaction
4. Payload verified (HMAC-SHA256)
5. PR diff fetched from GitHub API
6. Changed file contents downloaded
7. AST extracted for changed files
8. Delta computed: which nodes modified?
9. Impact set calculated: which nodes depend on changes?
10. LLM analyzes impacted regions
11. Results posted as PR comment
12. Optional: notification service alerts team
```

**[→ See detailed PR Analysis Flow](./docs/PR_ANALYSIS_FLOW.md)** | **[→ Webhook setup guide](./docs/PR_WEBHOOK_API.md)**

---

## API Endpoints Summary

### User Controller
- `POST /auth/signup` - Register new user
- `POST /auth/login` - Login and get JWT token
- `GET /auth/profile` - Retrieve user profile
- `PUT /auth/profile` - Update profile
- `POST /auth/verify_token` - Verify JWT token

**[→ Full User API Reference](./docs/USER_API.md)**

### Project Controller (Protected with JWT)
- `POST /project/onboard` - Onboard a new repository
- `POST /project/graph` - Query graph for repo IDs
- `GET /project/nodes` - Fetch all nodes
- `GET /project/edges` - Fetch all edges
- `POST /project/edge` - Create new edge between nodes
- `DELETE /project/clear` - Clear all graph data

**[→ Full Project API Reference](./docs/PROJECT_API.md)**

### Pull Request Controller (Webhook)
- `POST /pr/webhook/pr` - GitHub webhook receiver

**[→ Full PR Webhook API Reference](./docs/PR_WEBHOOK_API.md)**

---

## Deployment

### Local Development
```bash
# Setup
python -m venv venv
source venv/bin/activate  # or on Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment variables
export GITHUB_TOKEN=<your-github-token>
export OPENAI_API_KEY=<your-openai-key>
export NEO4J_URI=neo4j://127.0.0.1:7687
export NEO4J_USER=neo4j
export NEO4J_PASS=<password>
export DATABASE_URL=postgresql://user:password@localhost:5432/chain_reaction

# Run
python main.py
```

---

## Configuration

### Environment Variables
- `GITHUB_TOKEN` - GitHub personal access token
- `GITHUB_WEBHOOK_SECRET` - Webhook signature secret
- `OPENAI_API_KEY` - OpenAI API key
- `JWT_SECRET` - JWT signing secret
- `JWT_EXP_SECONDS` - JWT expiry time (default: 86400)
- `NEO4J_URI` - Neo4j connection URI
- `NEO4J_USER` / `NEO4J_PASS` - Neo4j credentials
- `DATABASE_URL` - PostgreSQL connection string

---

## Documentation

Comprehensive documentation is available in the `/docs` folder:

| Document | Purpose |
|----------|---------|
| **[docs/INDEX.md](./docs/INDEX.md)** | Navigation hub and quick start guides by role |
| **[docs/USER_FLOWS.md](./docs/USER_FLOWS.md)** | Complete user workflows (signup, login, onboarding, graphing) |
| **[docs/PR_ANALYSIS_FLOW.md](./docs/PR_ANALYSIS_FLOW.md)** | Detailed PR analysis pipeline with error handling |
| **[docs/PROJECT_API.md](./docs/PROJECT_API.md)** | Graph management API reference (6 endpoints) |
| **[docs/PR_WEBHOOK_API.md](./docs/PR_WEBHOOK_API.md)** | GitHub webhook setup and integration guide |
| **[docs/USER_API.md](./docs/USER_API.md)** | Authentication API reference (6 endpoints) |
| **[docs/DOCUMENTATION_SUMMARY.md](./docs/DOCUMENTATION_SUMMARY.md)** | Overview of documentation suite |

**Recommended reading order**:
1. [docs/INDEX.md](./docs/INDEX.md) for your role (Frontend Dev / Backend Dev / DevOps / QA)
2. [docs/USER_FLOWS.md](./docs/USER_FLOWS.md) to understand the user experience
3. Relevant API reference for your work

---
