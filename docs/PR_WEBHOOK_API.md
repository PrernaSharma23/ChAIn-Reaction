# PR Webhook API Reference

## Overview
The ChAIn-Reaction system integrates with GitHub via **webhooks** to automatically analyze pull requests and post intelligent comments. When a PR is opened or updated and contains one of the trigger phrases, the system extracts the diff, analyzes the code structure, computes impact, and generates LLM-powered insights.

---

## Webhook Configuration

### GitHub Setup
1. Grant ChAIn-Reaction-Bot access to your github repository
1. Go to repository **Settings** → **Webhooks** → **Add webhook**
2. Configure:
   - **Payload URL**: `https://api.chain-reaction.example.com/webhook/pr`
   - **Content type**: `application/json`
   - **Secret**: Set to your `GITHUB_WEBHOOK_SECRET` (store safely)
   - **Events**: Select "Issue Comments"
   - **Active**: ✓ Checked

### Signature Verification
GitHub signs each webhook request with an HMAC-SHA256 hash using the secret. The signature is in the `X-Hub-Signature-256` header:

```
X-Hub-Signature-256: sha256=<hex_digest>
```

The system verifies this signature to ensure authenticity. Invalid signatures are rejected with **401 Unauthorized**.

---

## Endpoint

### PR Analysis Webhook
Receive GitHub PR events and automatically analyze changes.

#### Request (GitHub → System)
```http
POST /webhook/pr
Content-Type: application/json
X-Hub-Signature-256: sha256=abcdef1234567890...
X-GitHub-Event: pull_request
X-GitHub-Delivery: 12345678-1234-1234-1234-123456789012

{
  "action": "created",
  "comment" : {
    "id" : "12",
    "body" : "start chain reaction"
    ...
  }
  "issue" : {
    ...
    pull_request": {
        "id": 1296269,
        "number": 1,
        "state": "open",
        "title": "Fix auth flow bug".
        "head": {
        "ref": "feature-branch",
        "sha": "6dcb09b5b57875f334f61aebed695e2e4193db5e"
        },
        "base": {
        "ref": "main",
        "sha": "db8c55ebf77f72cd2481888d46a0e71f4e7e4a4a"
        }
    }
  } 
  
}
```

#### Response
```json
HTTP/1.1 200 OK
{
  "ok": true,
  "pr_number": 1,
  "repo_name": "Hello-World",
  "message": "PR analysis queued asynchronously"
}
```

---

## Trigger Phrases

The system listens for specific phrases in PR descriptions to determine whether to analyze:

| Phrase | 
|--------|
@ChAIn-Reaction-Bot
| `@chain-reaction-bot : start analysis` |
| `@chain-reaction-bot : analyze pr` |
| `@chain-reaction-bot : analyze impact` |
| `@chain-reaction-bot analyze impact` |
| `@chain-reaction : start analysis` |
| `Start Chain Reaction` |
| `Trigger Chain Reaction` |
| `Analyze PR` |
| `Start Analysis` |
| `Analyze impact` |
| `Check Impact` |

### Example PR Comment
```markdown
Start Chain Reaction
```

---

## Processing Pipeline

When a valid trigger phrase is found:


1. **Extract Diff** - Parse PR files using GitHub API
3. **AST Analysis** - Extract code structure (classes, methods, dependencies)
4. **Delta Computation** - Find nodes/edges changed vs. main
5. **Impact Analysis** - Query Neo4j to find all affected nodes
6. **LLM Analysis** - Generate insights
7. **Post Comment** - Add comment to PR with findings



## Webhook Payload Structure

### Pull Request Object
```json
{
  "id": 1296269,
  "number": 1,
  "state": "open",
  "title": "string",
  "body": "string",
  "created_at": "2011-01-26T19:01:12Z",
  "updated_at": "2011-01-26T19:01:12Z",
  "closed_at": null,
  "merged_at": null,
  "merge_commit_sha": null,
  "merged": false,
  "draft": false,
  "user": {
    "login": "octocat",
    "id": 1,
    "avatar_url": "https://github.com/images/error/octocat_happy.gif",
    "type": "User"
  },
  "head": {
    "label": "octocat:feature-branch",
    "ref": "feature-branch",
    "sha": "6dcb09b5b57875f334f61aebed695e2e4193db5e",
    "repo": {
      "id": 1296269,
      "name": "Hello-World",
      "full_name": "octocat/Hello-World"
    }
  },
  "base": {
    "label": "octocat:main",
    "ref": "main",
    "sha": "db8c55ebf77f72cd2481888d46a0e71f4e7e4a4a",
    "repo": {
      "id": 1296269,
      "name": "Hello-World",
      "full_name": "octocat/Hello-World"
    }
  },
  "repository": {
    "id": 1296269,
    "name": "Hello-World",
    "full_name": "octocat/Hello-World",
    "owner": {
      "login": "octocat"
    }
  }
}
```

---

## Error Responses

### Invalid Signature
```json
HTTP/1.1 401 Unauthorized
{
  "error": "Invalid webhook signature"
}
```

### Trigger Phrase Not Found
```json
HTTP/1.1 400 Bad Request
{
  "error": "No trigger phrase detected in PR body"
}
```

### Repository Not Onboarded
```json
HTTP/1.1 400 Bad Request
{
  "error": "Repository not found in system. Onboard first via POST /api/project/onboard"
}
```

---

## Event Filters

The system only responds to:
- **Event Type**: `Issue Comment`
- **Actions**: `created`
- **Repository**: Must be onboarded in system
- **Trigger Phrase**: Must be present in PR comment

Other events are silently ignored (200 OK but no processing).

---

## Example Workflow

### Step 1: Developer Creates PR
Developer creates a PR and comments trigger phrase:
```
ChA Reaction 
```

### Step 2: GitHub Sends Webhook
```json
{
  "action": "created",
  "comment": {
    "number": 42,
    "body": "...\nChAIn Reaction"
  }
}
```

### Step 3: System Validates & Queues
```
✓ Signature verified
✓ Trigger phrase found
✓ Repository known
✓ Queued for async processing
→ Return 200 OK immediately
```

### Step 4: Async Processing
```
[1] Clone repo
[2] Extract diff
[3] Analyze AST
[4] Compute delta
[5] Get impact nodes
[6] LLM analysis
[7] Post comment
```

### Step 5: Developer Sees Comment
Comment appears on PR:
```
## 🔍 ChAIn-Reaction Analysis

**Changed Nodes**: 3 (UserService, AuthController, JWTUtil)
**Impact Scope**: High (affects 12 downstream nodes)

**Key Changes**:
- UserService.authenticate() refactored for concurrent access
- New rate limiting logic in AuthController
- JWTUtil token expiration logic simplified

**Affected Components**:
- LoginService → calls UserService (DIRECT)
- AdminDashboard → calls AuthController (DIRECT)
- TokenRefresh → uses JWTUtil (DIRECT)
- 9 indirect dependencies

**LLM Insights**:
This refactoring reduces authentication latency by ~15% and improves thread safety. Consider updating the load test to verify concurrent request handling.
```

---

## Debugging Webhooks

### View Webhook Delivery History
1. GitHub repo → **Settings** → **Webhooks** → your webhook
2. Scroll to **Recent Deliveries**
3. Click on any delivery to see:
   - Request payload
   - Response status code
   - Response body
   - Retry count


---

## See Also
- [Project API](./PROJECT_API.md)
- [User Flows](./USER_FLOWS.md)
- [PR Analysis Flow](./PR_ANALYSIS_FLOW.md)
- [GitHub Webhook Docs](https://docs.github.com/en/developers/webhooks-and-events/webhooks/about-webhooks)
