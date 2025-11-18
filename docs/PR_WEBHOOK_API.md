# PR Webhook API Reference

## Overview
The ChAIn-Reaction system integrates with GitHub via **webhooks** to automatically analyze pull requests and post intelligent comments. When a PR is opened or updated and contains one of the trigger phrases, the system extracts the diff, analyzes the code structure, computes impact, and generates LLM-powered insights.

---

## Webhook Configuration

### GitHub Setup
1. Go to repository **Settings** → **Webhooks** → **Add webhook**
2. Configure:
   - **Payload URL**: `https://api.chain-reaction.example.com/pr/webhook/pr`
   - **Content type**: `application/json`
   - **Secret**: Set to your `GITHUB_WEBHOOK_SECRET` (store safely)
   - **Events**: Select "Pull requests"
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
POST /pr/webhook/pr
Content-Type: application/json
X-Hub-Signature-256: sha256=abcdef1234567890...
X-GitHub-Event: pull_request
X-GitHub-Delivery: 12345678-1234-1234-1234-123456789012

{
  "action": "opened|synchronize|reopened",
  "pull_request": {
    "id": 1296269,
    "number": 1,
    "state": "open",
    "title": "Fix auth flow bug",
    "body": "Fixes #1234\n\n@ChAIn-Reaction analyze_pr",
    "user": {
      "login": "octocat"
    },
    "head": {
      "ref": "feature-branch",
      "sha": "6dcb09b5b57875f334f61aebed695e2e4193db5e"
    },
    "base": {
      "ref": "main",
      "sha": "db8c55ebf77f72cd2481888d46a0e71f4e7e4a4a"
    },
    "merged": false,
    "repository": {
      "id": 1296269,
      "name": "Hello-World",
      "full_name": "octocat/Hello-World",
      "owner": {
        "login": "octocat"
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

| Phrase | Action |
|--------|--------|
| `@ChAIn-Reaction analyze_pr` | Full PR analysis |
| `@ChAIn-Reaction analyze` | Full PR analysis |
| `@ChAIn-Reaction check_impact` | Check impact analysis only |
| `@ChAIn-Reaction ai_comment` | Trigger AI comment generation |
| `@ChAIn-Reaction graph_impact` | Analyze and show graph changes |
| `@ChAIn-Reaction deps` | Show dependencies affected |
| `@ChAIn-Reaction review` | Full code review |
| `@ChAIn-Reaction suggest_tests` | Suggest test cases |

### Example PR Description
```markdown
## Summary
Fixed authentication flow to handle concurrent requests.

Fixes #1234

@ChAIn-Reaction analyze_pr
```

---

## Processing Pipeline

When a valid trigger phrase is found:

1. **Clone Repository** - Download repo from GitHub
2. **Extract Diff** - Parse PR files using GitHub API
3. **AST Analysis** - Extract code structure (classes, methods, dependencies)
4. **Delta Computation** - Find nodes/edges changed vs. main
5. **Impact Analysis** - Query Neo4j to find all affected nodes
6. **LLM Analysis** - Generate insights (with 3-retry exponential backoff)
7. **Post Comment** - Add comment to PR with findings

### Processing Times
- Standard PR (5-10 files): **2-5 seconds**
- Large PR (20-50 files): **5-15 seconds**
- Very large PR (100+ files): **15-60 seconds**

---

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
  "error": "Repository not found in system. Onboard first via POST /project/onboard"
}
```

### Processing Error (Async)
```json
HTTP/1.1 202 Accepted
{
  "ok": true,
  "message": "PR analysis queued. If processing fails, no comment will be posted."
}
```

---

## Event Filters

The system only responds to:
- **Event Type**: `pull_request`
- **Actions**: `opened`, `synchronize`, `reopened`
- **Repository**: Must be onboarded in system
- **Trigger Phrase**: Must be present in PR description

Other events are silently ignored (200 OK but no processing).

---

## Security Considerations

### Webhook Signature Verification
Every incoming webhook is verified using HMAC-SHA256:

```python
# Pseudo-code
expected_signature = "sha256=" + hmac.new(
    secret.encode(),
    body.encode(),
    hashlib.sha256
).hexdigest()

received_signature = request.headers.get("X-Hub-Signature-256")

if not constant_time_compare(expected_signature, received_signature):
    return 401  # Unauthorized
```

**Why**: Prevents malicious actors from sending fake PR events.

### Token Security
- GitHub OAuth token stored in environment variable `GITHUB_TOKEN`
- Never logged or exposed in error messages
- Rotated quarterly

### Rate Limiting (Future)
- Currently: Unlimited webhook processing
- Planned: 100 webhooks/minute per repository

---

## Example Workflow

### Step 1: Developer Creates PR
Developer opens PR with trigger phrase:
```
@ChAIn-Reaction analyze_pr
```

### Step 2: GitHub Sends Webhook
```json
{
  "action": "opened",
  "pull_request": {
    "number": 42,
    "title": "Refactor user service",
    "body": "...\n@ChAIn-Reaction analyze_pr"
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
[6] LLM analysis (with retry)
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

### Enable Debug Logging
Set environment variable:
```bash
export PR_WEBHOOK_DEBUG=true
```

Then check logs:
```bash
docker logs chain-reaction | grep "webhook"
```

### Manual Test
```bash
# Create test payload
cat > payload.json << 'EOF'
{
  "action": "opened",
  "pull_request": {
    "number": 999,
    "title": "Test PR",
    "body": "@ChAIn-Reaction analyze_pr",
    "head": {"sha": "abc123"},
    "base": {"sha": "def456"},
    "repository": {"full_name": "octocat/Hello-World"}
  }
}
EOF

# Sign payload
SECRET="your-webhook-secret"
SIGNATURE=$(echo -n "$(cat payload.json)" | openssl dgst -sha256 -hmac "$SECRET" -hex | sed 's/^.*= //')

# Send to webhook
curl -X POST "http://localhost:5000/pr/webhook/pr" \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=$SIGNATURE" \
  -d @payload.json
```

---

## See Also
- [Project API](./PROJECT_API.md)
- [User Flows](./USER_FLOWS.md)
- [PR Analysis Flow](./PR_ANALYSIS_FLOW.md)
- [GitHub Webhook Docs](https://docs.github.com/en/developers/webhooks-and-events/webhooks/about-webhooks)
