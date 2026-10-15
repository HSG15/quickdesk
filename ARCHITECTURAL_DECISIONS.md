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

---

## Phase 2: Database Models, Migrations, Seed Data & RBAC Authentication

### ADR 2.1: Native bcrypt Hashing over Legacy Passlib
- **Context**: Passlib has historically been standard in FastAPI tutorials, but it relies on Python's legacy `crypt` module which is deprecated in Python 3.11+ and completely removed in Python 3.13.
- **Decision**: Use the modern, maintained `bcrypt` package directly (`bcrypt.hashpw` and `bcrypt.checkpw`) with automatic random salt generation.
- **Why this choice**: 
  - Zero deprecation warnings on modern Python 3.13 runtime.
  - Constant-time password verification prevents side-channel timing attacks.
  - Generates secure, salted modular crypt format strings (`$2b$12$...`).
- **Interview Talking Point**: *"Rather than relying on passlib—which triggers deprecation warnings in Python 3.13 due to the removal of the standard library `crypt` module—we integrated the native `bcrypt` C-extension directly. This ensures forward compatibility, faster hashing, and timing-attack resistant password verification."*

---

### ADR 2.2: Stateless JWT Bearer Authentication
- **Context**: The client must authenticate requests to both REST endpoints and Server-Sent Event (SSE) streams across independent HTTP requests.
- **Decision**: Issue signed HMAC-SHA256 (HS256) JSON Web Tokens (JWT) upon successful login, including `sub` (user_id), `email`, and `role`.
- **Why this choice**:
  - Statelessness: The server does not need to maintain server-side session tables in memory or Redis for authentication verification.
  - Fast decoding: Verification only requires cryptographically validating the signature with `JWT_SECRET_KEY` and checking expiration.
  - Decoupled authorization: The user's role is embedded in the verified claims, enabling immediate role inspection before querying the database.
- **Security Considerations & Trade-offs**:
  - Storing JWTs in browser memory or `localStorage` carries an XSS risk if client-side code is compromised.
  - Mitigation: In production, tokens should be transmitted in `HttpOnly`, `SameSite=Strict` secure cookies to prevent JavaScript read access. For our internal assessment API client, we use Authorization Bearer headers with strict backend validation.

---

### ADR 2.3: Declarative Role Enforcement via FastAPI Dependency Injection
- **Context**: Support agents must perform administrative actions (viewing all tickets, overriding AI classifications, replying, viewing metrics) that employees must NEVER be able to perform. Hiding buttons in the frontend is insufficient.
- **Decision**: Enforce authorization strictly on the server using composable FastAPI dependencies:
  - `get_current_user`: extracts Bearer token, validates signature/expiration, fetches user from database. Returns `HTTP 401 Unauthorized` if invalid.
  - `require_agent`: consumes `get_current_user` and verifies `current_user.role == "agent"`. Returns `HTTP 403 Forbidden` if user is an employee.
  - `require_employee`: consumes `get_current_user` and verifies `current_user.role == "employee"`.
- **Why this choice**:
  - Declarative route decoration: `@router.get("/metrics", dependencies=[Depends(require_agent)])`. A developer cannot accidentally forget the authorization check inside the route function.
  - Clean separation between *authentication* (who are you? -> 401) and *authorization* (what are you allowed to do? -> 403).

---

### ADR 2.4: Schema Design — Immutable AI Baselines vs Active Ticket State
- **Context**: The application requires tracking AI accuracy and agent overrides over time.
- **Decision**: In `models/ticket.py`, we separate:
  1. `ai_suggested_category` and `ai_suggested_priority` (set at ticket creation, never updated).
  2. `category` and `priority` (active values, initially equal to AI suggestion, but updatable by agents).
  3. `override_audit_logs` table (atomic audit record of ticket_id, agent_id, field_name, old_value, new_value, created_at).
- **Why this choice**:
  - Maintains historical ground truth for model evaluation and audit logs.
  - Enables calculating exact override rates: $\frac{\text{Tickets where active category} \ne \text{AI suggested category}}{\text{Total tickets with AI suggestions}} \times 100$.

---

### Important Code Deep Dives (Phase 2)

#### 1. RBAC Guard Dependency (`backend/app/api/deps.py`)
```python
def require_agent(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "agent":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Support Agent role required",
        )
    return current_user
```
*How it works*: FastAPI's dependency injection resolves `get_current_user` first. If the token is missing or expired, it immediately halts with a `401`. If valid, it inspects the database-backed `current_user.role`. If not `"agent"`, it aborts with `403 Forbidden`. The protected route handler never even executes.

#### 2. Salted bcrypt Hashing (`backend/app/core/security.py`)
```python
def get_password_hash(password: str) -> str:
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")
```
*How it works*: `bcrypt.gensalt()` generates a cryptographically random 128-bit salt with default cost factor 12 ($2^{12} = 4,096$ iterations). Even if two users choose the identical password `"password123"`, their hashes will be completely different, protecting against pre-computed rainbow table attacks.

---

### Important Interview Questions & Answers (Phase 2)

1. **Q: What is the difference between HTTP 401 Unauthorized and HTTP 403 Forbidden in your API?**
   - **Answer**: *"HTTP 401 means unauthenticated: the client failed to provide a valid JWT token, or the token expired. The client can retry by logging in. HTTP 403 means authenticated but unauthorized: we know who the user is (e.g., an employee), but their role lacks permission to execute the requested action (e.g., an agent-only override or metrics endpoint). Re-authenticating with the same user will not grant access."*

2. **Q: Why don't you trust the user ID or role sent in the request body from the client?**
   - **Answer**: *"A client can manipulate any headers or JSON bodies sent over the wire. We derive the user's identity and role exclusively from the cryptographically verified JWT payload (`sub` claim) signed with our server secret. Furthermore, our dependency verifies that the user ID actually exists in PostgreSQL to guard against tokens issued before an account was deleted."*

3. **Q: How does your database prevent duplicate users or tickets with non-existent employees?**
   - **Answer**: *"We enforce relational integrity at the PostgreSQL engine level. `users.email` has a `UNIQUE` index constraint. `tickets.employee_id` has a `FOREIGN KEY` constraint referencing `users.id` with `ON DELETE CASCADE`. If someone attempts to insert a ticket with a fictitious employee ID, PostgreSQL immediately raises an integrity violation error, preventing orphaned or corrupt records."*

