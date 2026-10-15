# QuickDesk — Architectural Decision Records (ADR)

This living document records the key architectural, technical, and engineering decisions made during the development of QuickDesk, organized phase-by-phase. It is designed to help you prepare for and confidently answer design and architecture questions during your interview.

---

## Phase 0: Project Inception & Overall Architecture

### ADR 0.1: Monorepo with Decoupled React Frontend and Python Backend
- **Context**: QuickDesk requires a modern user interface for employees and support agents, combined with an AI pipeline, relational persistence, and role-based authorization.
- **Decision**: Organize the project as a single monorepo with `frontend/` (React + Vite + TypeScript) and `backend/` (FastAPI + Python).
- **Why this choice**: 
  - Monorepo keeps code synchronized, allows a single repository for review, and simplifies local setup.
  - Decoupling frontend and backend allows the backend to be a pure REST + SSE API that can be independently tested with `pytest`.
- **Alternatives Considered**:
  - *Next.js full-stack (Python backend via microservice)*: Unnecessary complexity; running two web servers or handling Python AI pipelines inside Next.js API routes creates unnecessary cognitive load and memory overhead on an 8 GB M1 Mac.
  - *Full microservices*: Overkill for a 5-day assessment. Adds network latency, distributed transactions, and debugging headaches.
- **Interview Talking Point**: *"We chose a decoupled monorepo architecture: FastAPI handles security, database persistence, and AI workflows as a clean REST + SSE API, while React provides a responsive, type-safe internal SaaS UI. This preserves clean boundaries without distributed systems overhead."*

---

### ADR 0.2: FastAPI over Flask / Django
- **Context**: The backend needs to handle synchronous database queries, asynchronous Server-Sent Events (SSE) streaming, and structured JSON validation.
- **Decision**: Use **FastAPI** as the backend web framework.
- **Why this choice**:
  - Native asynchronous (`asyncio`) support is required for Server-Sent Events (SSE). Flask requires non-standard threading or Gevent hacks to keep long-lived connections open.
  - Pydantic v2 validation ensures incoming and outgoing request payloads are strictly validated and typed.
  - Built-in Dependency Injection (`Depends`) makes Role-Based Access Control (RBAC) clean, declarative, and impossible to bypass accidentally.
  - Automatic OpenAPI interactive documentation (`/docs`) makes testing endpoints effortless.
- **Alternatives Considered**:
  - *Flask*: Simple, but async support is bolted on and lacks native request validation.
  - *Django*: Heavyweight ORM and template engine, unnecessary for a dedicated API service with AI/vector database requirements.

---

### ADR 0.3: Server-Sent Events (SSE) instead of WebSockets
- **Context**: Agents need to see new tickets when employees submit them, and employees need to see ticket status updates (e.g. Open -> Resolved) in real time without refreshing.
- **Decision**: Use **Server-Sent Events (SSE)** via HTTP.
- **Why this choice**:
  - **Unidirectional flow**: Support agents and employees only need server-to-client notifications. Client-to-server actions (submitting tickets, resolving tickets) are standard REST HTTP POST/PATCH requests.
  - **Protocol simplicity**: SSE runs over standard HTTP/1.1 or HTTP/2. It does not require protocol upgrading or custom binary framing like WebSockets.
  - **Native browser reconnection**: The browser's native `EventSource` API automatically reconnects if the network drops.
  - **Easy authentication**: Works with standard HTTP bearer tokens or query param tokens with standard middleware.
- **Alternatives Considered**:
  - *WebSockets*: Bidirectional protocol is overkill for push notifications. Requires heartbeat/ping-pong implementation, custom reconnection logic, and custom state management.
  - *Long Polling / Short Polling*: Inefficient, consumes unnecessary bandwidth and database reads.

---

### ADR 0.4: Groq Cloud LLM + Lightweight Local Embeddings
- **Context**: The application must run on an 8 GB RAM Apple Silicon MacBook Air M1 without slowing down the operating system.
- **Decision**: Use **Groq** (`llama-3.3-70b-versatile` or `llama-3.1-8b-instant`) for LLM inference, and lightweight local embeddings (`all-MiniLM-L6-v2`) for vector search via Chroma.
- **Why this choice**:
  - Running a local 7B+ LLM (e.g., via Ollama) on an 8 GB M1 Mac leaves only 2-3 GB of RAM for the OS, PostgreSQL, Python, and Vite dev server, risking heavy swap memory and lag.
  - Groq provides sub-second inference speeds on open-weights Llama 3 models via their fast LPU cloud hardware on an accessible free tier.
  - The embedding model `all-MiniLM-L6-v2` is only ~80 MB in size and executes in <50ms on CPU, consuming negligible memory.
- **Alternatives Considered**:
  - *Local Ollama*: Consumes ~4.5 GB of RAM; too heavy for simultaneous development on an 8 GB M1 Mac.
  - *OpenAI API*: Requires paid billing credits; Groq provides free access for development and evaluation.

---

### ADR 0.5: Immutable Baseline AI Suggestions vs. Active Ticket State
- **Context**: The assessment requires tracking agent overrides and measuring AI classification accuracy.
- **Decision**: In the `tickets` table, maintain `ai_suggested_category` and `ai_suggested_priority` as immutable columns set once at ticket creation. Separate active `category` and `priority` columns store the current state. Any modification generates a row in `override_audit_logs`.
- **Why this choice**:
  - Prevents loss of historical AI predictions when an agent corrects a mistake.
  - Allows calculating the exact override metric: $\frac{\text{Current} \ne \text{Original AI}}{\text{Total with AI suggestions}} \times 100$.
  - Provides a tamper-proof audit trail of who changed what, the previous value, the new value, and the timestamp.

---

## Phase 1: Foundation & Project Skeleton

### ADR 1.1: Isolated Git Repository Initialization
- **Context**: The parent user directory (`~`) had an existing `.git` directory, which could accidentally track or stage external personal files into the QuickDesk project.
- **Decision**: Initialized a dedicated Git repository directly within `/Users/harishankargiri/Desktop/QuickDesk/.git/`, with its own `.gitignore` and default branch `main`.
- **Why this choice**: Ensures QuickDesk remains completely isolated, clean, and safe for submission without leaking home directory files.

---

### ADR 1.2: PostgreSQL Driver Selection (psycopg)
- **Context**: Python 3.13 is installed on Apple Silicon (M1). Older binary drivers (like `psycopg2-binary`) can sometimes face C-extension compilation friction on new Python releases.
- **Decision**: Use SQLAlchemy with `psycopg[binary]` (Psycopg 3) or stable `psycopg2-binary` to connect to PostgreSQL 18.
- **Why this choice**: Modern, officially recommended driver for SQLAlchemy 2.0 with native async and sync engine support.

---

### ADR 1.3: Clean Internal SaaS Visual Theme
- **Context**: The application must look professional, intentional, and readable for enterprise internal users (support agents and employees).
- **Decision**: Built with React, Vite, TypeScript, and Tailwind CSS using a neutral slate/zinc surface palette, clear contrast, restrained indigo/blue accents, and accessible typography (Inter).
- **Why this choice**: Avoids generic unstyled appearance or garish gradients. Focuses on clarity, clear status badges (Open vs. Resolved), and distinct priority indicators (Low, Medium, High).
