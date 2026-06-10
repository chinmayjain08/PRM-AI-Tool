# PRM Tool — Project & Resource Management

A Python console application for managing people, projects, and timesheets across three roles: Admin, Manager, and Employee.

Built as the Learn & Code Final Project with a strong emphasis on Clean Code, SOLID principles, and Design Patterns.

---

## Prerequisites

| Tool | Minimum Version |
|------|----------------|
| Python | 3.11 |
| Docker | 24 (for PostgreSQL) |
| PostgreSQL (if not using Docker) | 15 |

---

## How to Run

### Option A: Running with SQLite (Local Development)

SQLite is the default and recommended database for local development because it does not require external setup or Docker containers.

#### Step 1 — Set up the server
```bash
cd server
pip install -r requirements.txt
cp .env.example .env
# Open .env and set SECRET_KEY to any long random string
```

#### Step 2 — Create the database and tables
```bash
$env:DATABASE_URL="sqlite:///./test.db"
alembic upgrade head
```

#### Step 3 — Seed the database
```bash
python seed.py
```

#### Step 4 — Start the server
```bash
$env:PYTHONUNBUFFERED="1"
$env:DATABASE_URL="sqlite:///./test.db"
uvicorn main:app --port 8000
```

---

### Option B: Running with PostgreSQL & Docker

#### Step 1 — Start the database
```bash
docker-compose up -d
```
Starts a PostgreSQL 15 container on port 5432.

#### Step 2 — Set up the server
```bash
cd server
pip install -r requirements.txt
cp .env.example .env
# Open .env and set SECRET_KEY to any long random string
# Make sure DATABASE_URL points to the postgres connection string:
# DATABASE_URL=postgresql://postgres:postgres@localhost:5432/prm_db
```

#### Step 3 — Create the tables
```bash
alembic upgrade head
```

#### Step 4 — Seed the first Admin account
```bash
python seed.py
```

Output:
```
Admin account created.
  Username : admin
  Password : Admin@1234
  → You will be asked to change this password on first login.
```

#### Step 5 — Start the server
```bash
uvicorn main:app --reload
```

---

### Step 6 — Start the client (new terminal)

From the project root directory:
```bash
cd client
python main.py
```

---

## Default Login

| Username | Password | Role |
|----------|----------|------|
| admin | Admin@1234 | Admin |

> You will be forced to set a new password on first login.

---

## Application Features

### Admin
- Create and manage user accounts (Admin, Manager, Employee)
- View and update employee profiles, skills, department
- Assign managers to employees
- Create and update projects and milestones
- View all resource allocations across the organisation
- Configure LLM provider, API key, and scheduler interval

### Manager
- View team resource dashboard (Bench / Allocated)
- Allocate employees to projects (with utilisation validation)
- End active allocations
- View own projects with health status (🟢 ON_TRACK / 🟡 ATTENTION / 🔴 AT_RISK)
- View team timesheets for any week (including MISSED entries)
- AI-assisted skill matching for open requirements
- AI-generated plain-English project risk summary

### Employee
- Submit weekly timesheets with hours and activity tags
- View full timesheet history (SUBMITTED and MISSED weeks)
- View active project allocations
- Receive ⚠ reminder on login if last week's timesheet is missing

---

## Architecture

```
client/ (Python console)
  screens/      ← One file per BRD screen
  api_client/   ← HTTP calls to server (screens never call requests directly)
  utils/        ← display.py, input_helpers.py, constants.py

server/ (FastAPI)
  api/          ← Route handlers (HTTP only — no business logic)
  services/     ← Business rules (no SQL, no HTTP)
  repositories/ ← SQL queries (no business rules)
  models/       ← SQLAlchemy ORM table definitions
  schemas/      ← Pydantic request/response shapes
  core/         ← Config, security, database, scheduler
  llm/          ← LLM adapters (Adapter + Factory pattern)
```

### Three-Layer Rule

| Layer | What it does | What it must NOT do |
|-------|-------------|-------------------|
| Routes | Receive HTTP, call service, return response | Write SQL, contain business rules |
| Services | All business rules and validation | Write SQL, return HTTP responses |
| Repositories | All database queries | Contain business logic |

---

## SOLID Principles

### S — Single Responsibility
Each file/class has exactly one reason to change.
```
auth_service.py     → authentication rules only
allocation_service.py → allocation rules only
user_service.py     → user account rules only
```
If `allocation_service` needs to change its validation logic, `auth_service` is never touched.

### O — Open / Closed
```python
# server/app/llm/base_adapter.py
class LLMAdapter:
    def complete(self, prompt: str) -> str:
        raise NotImplementedError("Subclasses must implement complete()")
```
To add a new LLM provider (e.g. Anthropic), you create `anthropic_adapter.py` and add one line to `adapter_factory.py`. The existing adapters and all callers are unchanged.

### L — Liskov Substitution
`GeminiAdapter` and `GroqAdapter` both extend `LLMAdapter`. Any code that works with `LLMAdapter` works identically with either subclass — no special cases needed.

### I — Interface Segregation
Each repository file exposes only the functions relevant to its domain.
```
user_repository.py      → only user-related SQL
employee_repository.py  → only employee-related SQL
```
`auth_service` imports from `user_repository`. It does not know `employee_repository` exists.

### D — Dependency Inversion
Services do not create their own database sessions. They receive them via FastAPI dependency injection. This means you can test a service in isolation by passing a test session.
```python
# Bad — direct dependency
def login():
    db = SessionLocal()   # tightly coupled

# Good — inverted dependency
def login(db: Session):   # injected from outside
```

---

## Design Patterns

### Repository Pattern
All SQL is in `server/app/repositories/`. Services call repository functions — they never write SQL directly. If you switch from PostgreSQL to another database, only the repository files need to change.

### Adapter Pattern
```
LLMAdapter (base)
  ├── GeminiAdapter   → wraps Google Gemini SDK
  └── GroqAdapter     → wraps Groq SDK
```
The `ai_skill_matcher` and `ai_risk_summarizer` call `llm.complete(prompt)` — they do not know or care whether Gemini or Groq is responding.

### Factory Pattern
```python
# adapter_factory.py — callers get the right adapter without knowing which one
def get_llm_adapter(db) -> LLMAdapter:
    config = load_system_config(db)
    if config.llm_provider == "gemini":
        return GeminiAdapter(api_key=config.llm_api_key)
    ...
```

### Strategy Pattern
`ai_skill_matcher.py` and `ai_risk_summarizer.py` are two AI strategies with the same calling convention. The manager router calls whichever is needed without knowing how either works internally.

### Singleton Pattern
```python
# config.py — loaded once at startup
settings = Settings()   # one instance, shared everywhere
```

---

## Clean Code Principles

### Named Constants — Never Magic Numbers
Every numeric threshold lives in `server/app/core/config.py`:
```python
MAX_UTILISATION_PERCENT          = 100
MIN_PASSWORD_LENGTH              = 8
DEFAULT_MAX_WEEKLY_HOURS         = 40
DEFAULT_SCHEDULER_INTERVAL_HOURS = 4
ATTENTION_DAYS_BEFORE_DEADLINE   = 30
LOW_EFFORT_THRESHOLD_PERCENT     = 50
```
Every client-side constant lives in `client/utils/constants.py`:
```python
BOX_WIDTH    = 46
ACTIVITY_TAGS = [...]
HEALTH_ICONS  = {...}
```
You will find the number `100` or `8` nowhere in the business logic — only named constants.

### Small Functions
Every function does one thing and fits on a single screen (~20 lines max). When a function started to grow, the extra logic was extracted into a helper with a clear name.
```python
# auth_service.py — three focused functions instead of one big login() function
def login(...):              # orchestrates
def change_password(...):    # one job
def validate_password_strength(...):  # one job
```

### DRY — Don't Repeat Yourself
All user input in the client goes through `client/utils/input_helpers.py`. All console formatting goes through `client/utils/display.py`. No screen contains duplicate input validation logic.

### No Dead Code
No commented-out code anywhere. Git history preserves anything removed. If a function is not called, it is deleted.

### Fail Fast
Validation happens at the start of every service function, before any database write. If an allocation would exceed 100%, the error is raised before any row is inserted.

### Meaningful Names
```python
# Bad
def do_emp(db, e_id):   ...

# Good
def deactivate_employee(db: Session, employee_id: int) -> None:  ...
```

---

## Background Scheduler

The scheduler starts automatically when the server starts (`lifespan` in `main.py`). It runs three jobs on every tick:
1. Recompute employee BENCH/ALLOCATED status
2. Flag missed timesheets for past complete weeks
3. Update project health status (ON_TRACK / ATTENTION / AT_RISK)

The interval is configured in the System Configuration screen and read from `system_config` table — not hardcoded.

---

## AI Features

The LLM provider and API key are configured in the Admin → System Configuration screen. Supported providers: `gemini`, `groq`.

### Skill Match
- Reads requirement text (natural language)
- Filters out employees without enough free capacity
- Sends a structured prompt to the LLM
- Returns a ranked list with name, reason, and suggested allocation %

### Risk Summary
- Reads project milestones, due dates, effort data
- Collects risk flags from the health service
- Returns a 3–5 sentence plain-English paragraph
