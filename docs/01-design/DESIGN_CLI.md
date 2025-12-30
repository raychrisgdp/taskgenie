# CLI Design

## Entry Points

The CLI provides three main interaction modes:

- **Interactive TUI (Primary):** `tgenie` → full-screen Textual app with task list, detail view, and keyboard navigation. See `DESIGN_TUI.md` for full details.
- **Non-interactive commands:** `tgenie add/list/show/...` → scripting-friendly subcommands (PR-009)
- **Chat (Primary inside TUI):** Chat is a pane/workflow inside interactive mode; `tgenie chat` remains for chat-only/one-shot use if desired.

## Primary Interface

The CLI is the **primary and recommended way** to interact with the system. It's designed to be:
- **Scriptable** - Pipe to other tools, use in automation
- **Familiar** - Similar to git, docker, kubectl patterns
- **Fast** - Instant responses, no web latency
- **Conversational** - Natural language for complex queries

## Command Structure

```
tgenie <command> [options] [arguments]

Examples:
  tgenie add "Review PR" --attach github:owner/repo/pull/123
  tgenie list --status pending
  tgenie chat
  tgenie show abc123
```

## Commands

### 1. `add` - Create new task

**Usage:**
```bash
tgenie add "Task title" [options]
```

**Options:**
| Option | Short | Description | Example |
|---------|---------|--------------|----------|
| `--description` | `-d` | Detailed description | `-d "Fix auth bug"` |
| `--attach` | `-a` | Attach URL/Gmail/GitHub | `-a gmail:msg-id-123` |
| `--eta` | `-e` | Due date/time | `-e "2025-01-15"` or `-e "tomorrow"` |
| `--status` | `-s` | Initial status | `-s in_progress` |
| `--priority` | `-p` | Priority level | `-p high` |

**Examples:**

**Simple task:**
```bash
$ tgenie add "Buy groceries"
✓ Task created: abc123
```

**Task with details:**
```bash
$ tgenie add "Review PR #123" \
  -d "Fix authentication bug in login flow" \
  -a github:owner/repo/pull/123 \
  -e "2025-01-15" \
  -p high
✓ Task created: abc123
  Title: Review PR #123
  ETA: 2025-01-15
  Priority: high
  Status: pending
```

**Task with Gmail attachment:**
```bash
$ tgenie add "Respond to client" \
  -a gmail:18e4f7a2b3c4d5e \
  -e "tomorrow 10am"
✓ Task created: abc123
  Attachment: Gmail thread "Client meeting request"
```

**Interactive mode:**
```bash
$ tgenie add --interactive
Title: Prepare presentation
Description (Ctrl+D to finish): Quarterly review slides
Attachment (optional): github:owner/repo/issues/456
ETA (optional): next Friday
Priority [low/medium/high]:
✓ Task created: abc123
```

---

### 2. `list` - List tasks

**Usage:**
```bash
tgenie list [filters]
```

**Filters:**
| Filter | Description | Example |
|--------|--------------|----------|
| `--status` | Filter by status | `--status pending` |
| `--tag` | Filter by tag | `--tag frontend` |
| `--priority` | Filter by priority | `--priority high` |
| `--due` | Filter by due date | `--due today`, `--due overdue` |
| `--search` | Keyword search | `--search authentication` |
| `--limit` | Limit results | `--limit 10` |

**Examples:**

**List all pending tasks:**
```bash
$ tgenie list
Pending Tasks (3):
─────────────────────────────────────────────────────────────
abc123  ⏰ 2025-01-15  Review PR #123           [high]
def456  ⏰ 2025-01-17  Send project update       [medium]
ghi789  ⏰ 2025-01-18  Fix authentication bug    [high]

Attachments:
  abc123 → GitHub: owner/repo/pull/123
  def456 → Gmail: 18e4f7a2b3c4d5e
```

**List high-priority tasks:**
```bash
$ tgenie list --priority high
High Priority Tasks (2):
─────────────────────────────────────────────────────────────
abc123  ⏰ 2025-01-15  Review PR #123        [high]
ghi789  ⏰ 2025-01-18  Fix authentication bug [high]
```

**List tasks due today:**
```bash
$ tgenie list --due today
Due Today (1):
─────────────────────────────────────────────────────────────
abc123  ⏰ 2025-01-15  Review PR #123        [high]
```

**List completed tasks:**
```bash
$ tgenie list --status completed --limit 5
Recently Completed (5):
─────────────────────────────────────────────────────────────
xxx111  ✓ 2025-01-10  Update documentation
xxx222  ✓ 2025-01-09  Setup CI/CD
```

---

### 3. `show` - Show task details

**Usage:**
```bash
tgenie show <task_id>
```

**Examples:**

**Simple task:**
```bash
$ tgenie show abc123
Task: abc123
─────────────────────────────────────────────────────────────
Title: Review PR #123
Description: Fix authentication bug in login flow
Status: pending
Priority: high
Created: 2025-01-10 10:00
ETA: 2025-01-15 14:00
Tags: frontend, bug

Attachments:
  1. GitHub Pull Request
     URL: https://github.com/owner/repo/pull/123
     Title: Fix authentication in login flow
     Status: Open
     Files: 3 changed, +45/-12
```

**Task with multiple attachments:**
```bash
$ tgenie show def456
Task: def456
─────────────────────────────────────────────────────────────
Title: Client meeting preparation
Description: Prepare slides and demo
Status: in_progress
Created: 2025-01-12 09:00
ETA: 2025-01-17 15:00

Attachments:
  1. Gmail Thread
     Subject: Q1 Review Meeting
     From: client@company.com
     Date: 2025-01-11
     Snippet: "Please prepare quarterly review..."

  2. GitHub Issue
     URL: https://github.com/owner/repo/issues/456
     Title: Performance optimization needed
     Labels: bug, high-priority
```

---

### 4. `edit` - Edit task

**Usage:**
```bash
tgenie edit <task_id> [options]
```

**Options:** Same as `add` (only update specified fields)

**Examples:**

**Update status:**
```bash
$ tgenie edit abc123 --status in_progress
✓ Task abc123 updated: pending → in_progress
```

**Update ETA:**
```bash
$ tgenie edit abc123 --eta "2025-01-20"
✓ Task abc123 updated: 2025-01-15 → 2025-01-20
```

**Add attachment:**
```bash
$ tgenie edit abc123 --attach gmail:msg-id-456
✓ Task abc123: Gmail attachment added
```

**Interactive edit:**
```bash
$ tgenie edit abc123 --interactive
Title [Review PR #123]: Review PR #124
Description [Fix authentication...]:
Status [pending]: in_progress
Priority [high]:
ETA [2025-01-15]: 2025-01-18
✓ Task abc123 updated
```

---

### 5. `delete` / `done` - Complete or delete

**Usage:**
```bash
tgenie done <task_id>       # Mark as completed
tgenie delete <task_id>    # Delete task
```

**Examples:**

```bash
$ tgenie done abc123
✓ Task abc123 marked as completed
  Review PR #123 (2025-01-10 → 2025-01-14)

$ tgenie list
Active Tasks (2):
─────────────────────────────────────────────────────────────
def456  ⏰ 2025-01-17  Send project update   [medium]
ghi789  ⏰ 2025-01-18  Fix authentication bug [high]
```

```bash
$ tgenie delete def456
⚠️  Delete task "Send project update"? [y/N]: y
✓ Task def456 deleted
```

---

### 6. `chat` - Chat interface (inside TUI; chat-only mode optional)

**Usage:**
```bash
tgenie chat
```

**Chat is the main mode inside the interactive TUI.** This subcommand is the chat-only interface (useful for smaller terminals or one-shot interactions).

**Example Session:**

```bash
$ tgenie chat
🤖 AI Chat - Type 'exit' to quit, 'help' for commands

You: What tasks do I have due this week?
🤖 You have 3 tasks due this week:

1. Review PR #123
   Due: 2025-01-15 (Wednesday)
   Priority: High
   Status: Pending
   Attachment: GitHub PR #123

2. Send project update
   Due: 2025-01-17 (Friday)
   Priority: Medium
   Status: Pending
   Attachment: Gmail thread with client

3. Fix authentication bug
   Due: 2025-01-18 (Saturday)
   Priority: High
   Status: In Progress
   Attachment: GitHub issue #456

Would you like me to show you the PR details? (y/n)

You: y
🤖 Fetching PR #123 from GitHub...

GitHub Pull Request #123
─────────────────────────────────────────────────────────────
Title: Fix authentication in login flow
Author: johndoe
Status: Open
Files Changed: 3 files (+45, -12)
Description:
  The current JWT token validation doesn't properly handle
  expired tokens, causing users to be logged out unexpectedly.

  This PR adds proper token validation and refresh logic.

Reviews:
  ✅ Approved by janedoe
  🔄 Changes requested by bobsmith

Would you like to mark this task as in progress? (y/n)

You: y
✓ Task abc123 updated: pending → in_progress

You: What should I focus on right now?
🤖 Based on your tasks and current time:

🎯 IMMEDIATE (Due within 24 hours):
   None

📅 UPCOMING (Due this week):
   • Review PR #123 [high, in_progress]
   • Send project update [medium, pending]
   • Fix authentication bug [high, in_progress]

💡 Suggestion: Continue with PR #123 since you're already working on it

You: Show me the Gmail thread for the project update
🤖 [Displays email thread from task def456]
From: client@company.com
To: you@domain.com
Subject: Q1 Review Meeting
Date: 2025-01-11

Hi,

Thanks for the great work on Q1. I'd like to schedule a review
meeting for next week to discuss the roadmap.

Best,
Client

[3 more messages in thread...]

You: exit
👋 Goodbye! (Session saved to chat history)
```

**Chat Features:**
- ✅ Natural language queries
- ✅ Task suggestions
- ✅ RAG search across tasks and attachments
- ✅ Direct actions (mark done, add task, show details)
- ✅ Context awareness (remembers conversation)
- ✅ Streaming responses
- ✅ Exit with `exit` or Ctrl+D

**Chat Commands:**
```
/help     - Show help
/history  - Show conversation history
/clear    - Clear context
/attach   - Attach to current task
/status   - Show all tasks
```

---

### 7. `attach` - Add attachments to task

**Usage:**
```bash
tgenie attach <task_id> --type <type> --ref <reference>
```

**Types:**
- `gmail:<message-id>` - Gmail message/thread
- `github:<url>` - GitHub PR/issue
- `url:<url>` - Generic URL
- `doc:<path>` - Local document

**Examples:**

```bash
$ tgenie attach abc123 --type gmail --ref 18e4f7a2b3c4d5e
✓ Gmail attachment added to task abc123
  Thread: "Client meeting request" (3 messages)

$ tgenie attach abc123 --type github --ref owner/repo/pull/123
✓ GitHub PR attached to task abc123
  PR #123: Fix authentication in login flow

$ tgenie attach abc123 --type url --ref https://docs.google.com/doc/abc123
✓ URL attachment added to task abc123
  Google Docs: "Project documentation"
```

---

### 8. `ui` - Launch web interface

**Usage:**
```bash
tgenie ui [--port PORT]
```

**Examples:**
```bash
$ tgenie ui
🚀 Web UI starting on http://localhost:8080
Press Ctrl+C to stop

# Browser opens automatically
```

---

### 9. `config` - Configuration management

**Usage:**
```bash
tgenie config [options]
```

**Examples:**

**View current config:**
```bash
$ tgenie config
Current Configuration:
─────────────────────────────────────────────────────────────
LLM Provider: openrouter
Model: anthropic/claude-3-haiku
API Key: sk-or-******** (set)
Database: ~/.taskgenie/data/taskgenie.db
Gmail: Not configured
GitHub: Not configured
Notification: Enabled
```

**Set LLM provider:**
```bash
$ tgenie config --llm openrouter --model anthropic/claude-3-haiku
✓ LLM configuration updated

$ tgenie config --api-key sk-or-v1-your-key-here
✓ API key saved to ~/.taskgenie/config.toml
```

**Configure Gmail:**
```bash
$ tgenie config --gmail-auth
Opening browser for Gmail OAuth...
✓ Gmail authenticated successfully
✓ Credentials saved to ~/.taskgenie/credentials.json
```

**Configure notifications:**
```bash
$ tgenie config --notify 24h,6h
✓ Notification schedule: 24 hours, 6 hours before ETA
```

---

### 10. `search` - Semantic search (RAG)

**Usage:**
```bash
tgenie search <query> [--attachments]
```

**Examples:**

**Search by keyword:**
```bash
$ tgenie search "authentication bug"
Found 2 tasks:
─────────────────────────────────────────────────────────────
abc123  Review PR #123                [Match: description, title]
ghi789  Fix authentication bug            [Match: title]
```

**Semantic search with RAG:**
```bash
$ tgenie search "problems with logging in" --attachments
Found 3 results (semantic search):
─────────────────────────────────────────────────────────────
1. Task: abc123 - Review PR #123 (0.95)
   Reasoning: PR #123 discusses JWT token validation issues
   Related content from GitHub PR: "expired tokens causing users
   to be logged out unexpectedly"

2. Task: ghi789 - Fix authentication bug (0.89)
   Reasoning: Task title directly matches
   Related content from task description: "Users unable to log in
   after token expiration"

3. Attachment from abc123 - GitHub PR #123 (0.82)
   Reasoning: PR description contains login flow issues
   Relevant snippet: "The current JWT token validation doesn't
   properly handle expired tokens"
```

---

### 11. `export` / `import` - Backup and restore

**Usage:**
```bash
tgenie export --format json --output backup.json
tgenie import --file backup.json
```

**Examples:**

```bash
$ tgenie export
✓ Exported 5 tasks to backup_2025-01-15.json

$ tgenie import --file backup.json
⚠️  This will merge 5 tasks into your current list. Continue? [y/N]: y
✓ Imported 5 tasks
```

---

## Output Design

### Rich Terminal Output (using Rich library)

**Success:**
```
✓ Task created: abc123
```

**Warning:**
```
⚠️  Task already exists
```

**Error:**
```
✗ Failed to create task: Invalid ETA format
```

**Info:**
```
ℹ️  Fetching from GitHub...
```

### Tables and Formatting

**Task list:**
```
┌────────┬────────────────────┬─────────────┬──────────┬─────────┐
│ ID     │ Title             │ ETA         │ Priority │ Status  │
├────────┼────────────────────┼─────────────┼──────────┼─────────┤
│ abc123 │ Review PR #123    │ 2025-01-15 │ high     │ pending  │
│ def456 │ Send project updat│ 2025-01-17 │ medium   │ pending  │
└────────┴────────────────────┴─────────────┴──────────┴─────────┘
```

**Progress bars:**
```
Fetching from Gmail... ━━━━━━━━━━━━━━━━━━ 100%
Generating embeddings... ━━━━━━━━━━━━━━━━ 50%
```

## Interactive Prompts

When needed, CLI uses prompts for user input:

```bash
$ tgenie add --interactive
Title: [User types]
Description: [User types]
ETA (optional): [User types or Ctrl+D to skip]
Priority [low/medium/high]: [User types or arrows to select]
✓ Task created
```

## Shell Integration

**Shell completion (bash/zsh/fish):**
```bash
$ tgenie add "Fix"<TAB>
--attach      --description  --eta           --priority
--status      --interactive   --help
```

**Shell aliases:**
```bash
# Suggested aliases for ~/.bashrc or ~/.zshrc
alias tg='tgenie'     # If `tg` is already used, consider `alias ti=tgenie`
alias ti='tgenie'
alias ta='tgenie add'
alias tl='tgenie list'
alias tc='tgenie chat'
```

## Configuration File

**Location:** `~/.taskgenie/config.toml`

**Example:**
```toml
[llm]
provider = "openrouter"
model = "anthropic/claude-3-haiku"
api_key = "sk-or-v1-..."

[gmail]
enabled = true
credentials_path = "~/.taskgenie/credentials.json"

[github]
token = "ghp_..."
username = "username"

[notifications]
enabled = true
schedule = ["24h", "6h"]

[database]
path = "~/.taskgenie/data/taskgenie.db"

[web]
port = 8080
host = "localhost"
```
