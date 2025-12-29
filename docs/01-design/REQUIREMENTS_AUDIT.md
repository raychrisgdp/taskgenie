# Requirements & Design Audit

## 🛑 Critical Gaps & Technical Feasibility

### 1. The "Docker Notification" Gap (Major Interaction Issue)
**The Issue:** The design specifies running the app in **Docker** (`DESIGN_ARCHITECTURE.md`) but using **Plyer** (`DESIGN_NOTIFICATIONS.md`) for desktop notifications.
**The Problem:** Docker containers are isolated environments. A Python script running inside a Docker container **cannot** trigger a native desktop notification on your host machine (Windows/Mac/Linux) without complex configuring (X11 forwarding, DBus mapping, or a separate host-side listener).
**Impact:** As designed, notifications **will fail** silently.
**Recommendation:**
*   **Option A (Simpler):** Run the Notification Service *outside* Docker (on the host) while the backend runs in Docker.
*   **Option B (Web):** Rely on Browser Notifications via the Web UI (requires Web UI to be open).
*   **Option C (Bridge):** Build a tiny "host listener" script that listens to the Docker container and triggers the alert.

### 2. Gmail "Attachment" Interaction Flow
**The Issue:** `DESIGN_CLI.md` uses `todo attach --ref 18e4f7a2b3c`.
**The Problem:** Finding a specific Gmail `message-id` is extremely difficult for a normal user (requires "Show Original" in Gmail -> Copy Message-ID header).
**Impact:** Users will find this feature unusable.
**Recommendation:**
*   Change interaction to accept **URL**: `todo attach --ref "https://mail.google.com/mail/u/0/#inbox/FMfcgzGvw..."`
*   System should parse the ID from the URL automatically.

### 3. CLI Chat History Continuity
**The Issue:** `DESIGN_CHAT.md` implies stateful conversations, but CLI tools are stateless by default.
**The Problem:** If I run `todo chat`, ask "What's due?", exit, and then run `todo chat` again 5 minutes later, does it remember the context?
**Recommendation:**
*   Explicitly define default behavior: Does `todo chat` start fresh or resume?
*   Suggest: Default to **Resume** last session (for context continuity), with a `--new` flag to reset.

---

## ⚠️ UI & Interaction Ambiguities

### 1. Web UI "Streaming" Failure States
**Location:** `DESIGN_WEB.md`
**Ambiguity:** The design specifies SSE (Server-Sent Events) for chat.
**Missing Detail:** What is the UI interaction if the stream disconnects or the backend generates an error mid-sentence? Does it show a red "Retry" button? Does it auto-reconnect?
**Proposal:** UI must show a "Connection lost. Reconnecting..." toast and disable the input field.

### 2. CLI "Interactive Mode" Details
**Location:** `DESIGN_CLI.md`
**Ambiguity:** `todo add --interactive`
**Missing Detail:** How are multi-line descriptions handled? (Pressing Enter usually submits).
**Proposal:** Specify that Description uses a temp file (like `git commit`) OR requires a specific terminator (e.g., `Ctrl+D` or `END` on a new line).

### 3. Attachment "Preview" in CLI
**Location:** `DESIGN_CLI.md` (`todo show`)
**Ambiguity:** "View in GitHub" is listed as an action.
**Missing Detail:** In a CLI, does this print the URL? Or try to open the system browser (`xdg-open`)?
**Proposal:** Explicitly state that "View" actions launch the default system browser.

### 4. Search Ranking Interaction
**Location:** `DESIGN_CHAT.md` (RAG Search)
**Ambiguity:** If I search for "budget", and it matches a task title AND an attachment content.
**Missing Detail:** How is this visually distinguished in the CLI list view?
**Proposal:** Group results by source: "Matches in Tasks" vs "Matches in Attachments".

---

## 🔄 Redundancy Check

### 1. Task Schema Definitions
**Observation:** Task fields are defined in `PLAN.md`, `DESIGN_DATA.md` (SQL), and `DESIGN_DATA.md` (Pydantic).
**Status:** **Acceptable.** This is necessary redundancy for different layers (DB vs API).
**Action:** Ensure `status` enums match exactly across all files (`pending` vs `todo`).

### 2. Chat Commands
**Observation:** `todo chat` (CLI) and Web Chat share logic.
**Status:** **Good.** Both should hit the same API endpoint (`POST /api/chat`).
**Risk:** If CLI implements logic locally instead of calling API, logic will diverge.
**Action:** Enforce "Thick Server, Thin Client" - CLI should just be an API client.

---

## ✅ Completeness Checklist

| Component | Status | Notes |
|-----------|--------|-------|
| **Setup Flow** | ✅ Complete | `config` command is well defined |
| **Auth Flow** | ✅ Complete | BYOK and Gmail OAuth flows defined |
| **Error States** | ⚠️ Partial | Missing specific UI error states for Web/CLI |
| **Empty States** | ⚠️ Missing | What does Web UI look like with 0 tasks? |
| **Loading States** | ✅ Complete | Spinners/Progress bars defined |
| **Success States** | ✅ Complete | "✓ Task created" defined |

---

## 📝 Required Decisions

Before generating code, please clarify:

1.  **Docker vs. Notifications:** Do you want to:
    *   (A) Run everything on host (no Docker)?
    *   (B) Run backend in Docker but lose desktop notifications (rely on Web UI)?
    *   (C) Build the complex "Host Bridge" for notifications?
2.  **Gmail Interaction:** Can we switch from `message-id` to `URL` parsing?
3.  **CLI Chat:** Should it default to "Resume Previous Session"?
