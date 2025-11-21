# Pull Request Impact Analysis Flow

## Overview

When a developer opens a pull request on a monitored repository, ChAIn Reaction analyzes the changes on comment action and determines their impact across the codebase. The system:

1. Receives a GitHub webhook comment event
2. Extracts the PR diff
3. Creates AST for Changed Files
4. Compares against the baseline dependency graph
5. Identifies all potentially impacted nodes
6. Uses LLM to analyze semantic impact
7. Posts findings back as a PR comment

---

## Detailed Flow

### Step 1: GitHub Webhook Reception

```
┌─────────────────────────────────────┐
│  Developer opens PR & comments     │
│  with trigger phrase on existing PR │
└────────────┬────────────────────────┘
             │
             │ GitHub sends webhook
             │ X-GitHub-Event: issue_comment
             │ action: created
             ▼
┌────────────────────────────────────────┐
│  PR Webhook Receiver (/webhook/pr)  │
│  ├─ Verify HMAC signature             │
│  ├─ Parse JSON payload                │
│  ├─ Check event type & action         │
│  ├─ Extract repo, PR number, comment  │
│  └─ Check for trigger phrases         │
└────────────┬───────────────────────────┘
             │
             │ Valid & has trigger phrase
             ▼
        ┌─────────────────┐
        │ Queue Analysis  │
        │ (Async)         │
        └─────────────────┘
```

### Trigger Phrases
The analysis is triggered when a comment contains any of these phrases (case-insensitive):
- "@chain-reaction-bot : start analysis"
- "@chain-reaction-bot : analyze pr"
- "@chain-reaction-bot : analyze impact"
- "@chain-reaction-bot analyze impact"
- "@chain-reaction : start analysis"
- "start chain reaction"
- "check impact"
- "analyze impact"
- "trigger chain reaction"
- "chain reaction"
- "run analysis"
- ... (see full list in controller)

### Signature Verification
```
GitHub Secret + Webhook Payload
        │
        ▼
HMAC-SHA256 Hash
        │
        ▼
Compare with X-Hub-Signature-256 header
        │
    ┌───┴──┐
    │      │
   OK    REJECT (401 Unauthorized)
    │
    ▼
Continue processing
```

---

### Step 2: Duplicate Prevention

```
┌─────────────────────────────────────┐
│  Check ACTIVE_ANALYSES set          │
│  Key: "repo#pr_number"              │
└────────────┬────────────────────────┘
             │
        ┌────┴────┐
        │         │
     INACTIVE   ACTIVE
        │         │
        │    ┌────────────────────┐
        │    │ Return 200 OK      │
        │    │ message: already_  │
        │    │ in_progress        │
        │    └────────────────────┘
        │
        ▼
Post "analysis in progress..."
     comment and queue analysis
```

---

### Step 3: PR Diff Extraction & File Download

```
┌─────────────────────────────┐
│  GitHub API                 │
│  GET /repos/{owner}/{repo}/ │
│      pulls/{pr}/files       │
└────────────┬────────────────┘
             │
             ▼
┌──────────────────────────────────────┐
│  Array of changed files              │
│  {                                   │
│    "filename": "src/UserService.java"│
│    "sha": "abc123..."                │
│    "patch": "@@ -1,5 +1,10 @@..."  │
│  }                                   │
└────────────┬─────────────────────────┘
             │
             ▼
┌──────────────────────────────────────┐
│  For each file:                      │
│  ├─ Download blob via git/blobs/SHA │
│  ├─ Base64 decode content            │
│  └─ Store in files_content dict      │
└──────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────┐
│  files_content = {                   │
│    "src/UserService.java": "public.."|
│    "src/AuthController.java": "..."  │
│  }                                   │
└──────────────────────────────────────┘
```

---

### Step 4: AST Extraction & Node Identification

```
┌──────────────────────────────────────────┐
│  DiffAnalyzerService.analyze_files()     │
│  Processes each changed file:            │
└────────────┬─────────────────────────────┘
             │
        ┌────┴─────────────┐
        ▼                  ▼
  ┌──────────────┐   ┌──────────────────┐
  │ Java File    │   │ Python File      │
  └──────┬───────┘   └────────┬─────────┘
         │                    │
         ▼                    ▼
  ┌─────────────────────────────────────┐
  │ TreeSitterExtractor                 │
  │ ├─ Parse to AST                     │
  │ ├─ Extract symbols (classes,        │
  │ │   methods, functions)             │
  │ └─ Build relationships              │
  └────────┬────────────────────────────┘
           │
           ▼
  ┌─────────────────────────────────────┐
  │ Convert to GraphNodes:              │
  │ {                                   │
  │   uid: "repo:path:class:UserService"│
  │   kind: "class"                     │
  │   name: "UserService"               │
  │   ...                               │
  │ }                                   │
  └────────┬────────────────────────────┘
           │
           ▼
  ┌─────────────────────────────────────┐
  │ nodes = [node1, node2, ...]         │
  │ edges = [(from, to, type), ...]     │
  └─────────────────────────────────────┘
```

---

### Step 5: Delta Computation

```
┌────────────────────────────────────────────┐
│  GraphDeltaService.compute_delta()         │
│                                            │
│  Input:                                    │
│  - pr_nodes: new/modified nodes from PR    │
│  - baseline_nodes: existing graph nodes    │
└────────────┬───────────────────────────────┘
             │
             ▼
  ┌──────────────────────────────────────┐
  │ Compare:                             │
  │ ├─ ADDED: in pr_nodes, not baseline │
  │ ├─ MODIFIED: uid same, content diff │
  │ ├─ DELETED: in baseline, not pr     │
  │ └─ UNCHANGED: no change             │
  └────────────┬─────────────────────────┘
               │
               ▼
  ┌──────────────────────────────────────┐
  │ delta = {                            │
  │   "added": [node1, node2],           │
  │   "modified": [node3],               │
  │   "deleted": [],                     │
  │   "edges_affected": [edge1, edge2]   │
  │ }                                    │
  └──────────────────────────────────────┘
```

---

### Step 6: Impact Propagation

```
┌────────────────────────────────────────────┐
│  GraphDeltaService.get_impacted_nodes()    │
│                                            │
│  Input: delta (added/modified/deleted)    │
└────────────┬───────────────────────────────┘
             │
             ▼
  ┌──────────────────────────────────────┐
  │ For each changed node:               │
  │ ├─ Find all outgoing edges           │
  │ │  (DEPENDS_ON, READS_FROM, etc.)    │
  │ ├─ Add dependent nodes to impacted   │
  │ └─ Recursively expand (BFS/DFS)      │
  └────────────┬─────────────────────────┘
               │
               ▼
  ┌──────────────────────────────────────┐
  │ impacted_nodes = [                   │
  │   {                                  │
  │     uid: "repo:path:class:X",        │
  │     reason: "depends_on_modified",   │
  │     distance: 1                      │
  │   },                                 │
  │   ...                                │
  │ ]                                    │
  └──────────────────────────────────────┘
```

---

### Step 7: LLM Analysis

```
┌────────────────────────────────────────────┐
│  LLMService.call(prompt)                   │
│                                            │
│  Input: delta + impacted_nodes + repo info │
└────────────┬───────────────────────────────┘
             │
             ▼
  ┌──────────────────────────────────────────┐
  │ PromptBuilder.build_impact_prompt()      │
  │                                          │
  │ Template:                                │
  │ "Analyze PR impact:                      │
  │  - Modified: [classes/methods]           │
  │  - Impacted downstream: [entities]       │
  │  - Suggest tests: [areas]                │
  │  - Risk level: [low/med/high]"           │
  └────────────┬─────────────────────────────┘
               │
               ▼
  ┌──────────────────────────────────────────┐
  │ Gemini 2.5-Flash API                         │
  │                                          │
  │ (Retry logic: exponential backoff)       │
  │ ├─ Attempt 1: immediate                  │
  │ ├─ Attempt 2: wait 1s + jitter           │
  │ ├─ Attempt 3: wait 2s + jitter           │
  │ └─ Fail after 3 retries                  │
  └────────────┬─────────────────────────────┘
               │
               ▼
  ┌──────────────────────────────────────────┐
  │ LLM Response:                            │
  │ "This PR modifies UserService which is   │
  │  critical. Impacted components:          │
  │  - AuthController (1 dep away)           │
  │  - PaymentProcessor (2 deps away)        │
  │  Risk: HIGH - impacts auth flow          │
  │  Recommend: run full auth & payment      │
  │  integration tests."                     │
  └──────────────────────────────────────────┘
```

---

### Step 8: Post Results to PR

```
┌────────────────────────────────────────────┐
│  CommentNotificationService.post_comment() │
└────────────┬───────────────────────────────┘
             │
             ▼
  ┌──────────────────────────────────────────┐
  │ GitHub Issues API                        │
  │ POST /repos/{owner}/{repo}/issues/       │
  │      {pr}/comments                       │
  │                                          │
  │ Body (markdown):                         │
  │ "## 🔗 ChAIn Reaction Analysis Results   │
  │                                          │
  │  **Changed Entities:**                   │
  │  - UserService.authenticate()            │
  │  - UserService.logout()                  │
  │                                          │
  │  **Impacted (2 deps away):**             │
  │  - AuthController                        │
  │  - PaymentProcessor                      │
  │  - NotificationService                   │
  │                                          │
  │  **Analysis:**                           │
  │  [LLM-generated insight]                 │
  │                                          │
  │  **Recommendation:**                     │
  │  - Test auth flow                        │
  │  - Run payment integration tests"        │
  └────────────┬─────────────────────────────┘
               │
               ▼
  ┌──────────────────────────────────────────┐
  │ PR Comment Posted                        │
  │ Developer can now review impact insight  │
  │ and adjust testing strategy accordingly  │
  └──────────────────────────────────────────┘
```

---

## Data Flow Diagram

```
GitHub Event
    │
    ├─ Webhook Verification (HMAC-SHA256)
    │
    ├─ Trigger Phrase Detection
    │
    ├─ Duplicate Prevention (ACTIVE_ANALYSES)
    │
    ├─ PR Diff Extraction
    │    └─ File Content Download (GitHub API)
    │
    ├─ AST Extraction & Parsing
    │    ├─ TreeSitter (Java & Python)
    │    ├─ Symbol Extraction
    │    └─ Relationship Building
    │
    ├─ Delta Computation
    │    └─ Added / Modified / Deleted Analysis
    │
    ├─ Impact Propagation (Graph Traversal)
    │    └─ BFS/DFS from changed nodes
    │
    ├─ LLM Analysis (GPT-4)
    │    ├─ Prompt Building
    │    ├─ Retry Logic (exponential backoff)
    │    └─ Response Parsing
    │
    └─ Result Posting
         └─ GitHub Comment with findings
```

---

## Error Handling

### Graceful Degradation
- **Invalid Signature**: Log warning, return 401, do not process
- **Missing PR Info**: Log error, return 400, notify user via comment
- **AST Extraction Failure**: Log warning, continue with available data
- **LLM Failure**: After 3 retries, post comment with available delta info (without LLM analysis)
- **Graph Query Failure**: Log error, post generic comment, escalate alert

### Retry Logic (LLM Only)
```
Attempt 1: T+0s
  │
  ├─ Success? → Return
  │
  └─ Fail (transient error)

Attempt 2: T + 1s + random(0-0.5)s
  │
  ├─ Success? → Return
  │
  └─ Fail

Attempt 3: T + 2s + random(0-0.5)s
  │
  ├─ Success? → Return
  │
  └─ Fail → Exhaust retries, use delta only
```

---

## Performance Considerations

- **Async Processing**: Analysis runs in background, doesn't block webhook response
- **Duplicate Prevention**: ACTIVE_ANALYSES set prevents redundant processing
- **Temp File Cleanup**: Git repos cleaned up using GitPython (handles locked files)

---

## Security

- **Webhook Validation**: HMAC-SHA256 signature verification (GitHub webhook secret)
- **Rate Limiting**: Implicit via GitHub webhook delivery throttling
- **Data Isolation**: Each user sees only their own repos

---

## Summary

| Phase | Component | Input | Output |
|-------|-----------|-------|--------|
| Reception | PR Webhook | GitHub event | Verified payload |
| Extraction | Diff + AST | PR files | Changed nodes & edges |
| Delta | Graph Delta Service | PR nodes vs baseline | Added/modified/deleted set |
| Impact | Graph Traversal | Delta nodes | Impacted entity set |
| Analysis | LLM Service | Delta + impact | Semantic insights |
| Posting | Notification Service | Findings | PR comment with results |
