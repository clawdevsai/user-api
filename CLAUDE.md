# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Spec-Driven Backend Development** project for building a User API using **Hexagonal Architecture** and **Domain-Driven Design (DDD)** in Python. The project uses specialized Claude agents to orchestrate feature development through design (architecture) and implementation phases.

### Technology Stack

- **Language**: Python 3.12
- **Framework**: FastAPI ~0.136 (async)
- **ORM**: SQLAlchemy 2.0 (async)
- **Database**: PostgreSQL with Alembic migrations
- **Authentication**: JWT validation via JWKS from external IdP
- **Password Hashing**: argon2-cffi
- **Testing**: pytest + pytest-asyncio + httpx AsyncClient
- **Package Manager**: `uv` (recommended) or pip
- **Dependency Management**: Python 3.12+ with pyproject.toml/uv.lock

### Project Structure

```
.
├── specs/001-user-api/          # Feature specification & design artifacts
│   ├── spec.md                  # Functional requirements & user stories
│   ├── plan.md                  # Architecture, ADRs, technical decisions
│   ├── tasks.md                 # Ordered implementation tasks by phase
│   ├── data-model.md            # Domain entities, value objects, ports
│   ├── quickstart.md            # End-to-end validation scenarios
│   └── research.md              # Phase 0 research & context
│
├── user_api/                    # Source code (Hexagonal Architecture)
│   ├── domain/                  # Pure business logic (no framework imports)
│   │   ├── entities/            # User aggregate root
│   │   ├── value_objects/       # UserId, Email, Password, PasswordHash
│   │   ├── exceptions.py        # Domain errors (EmailAlreadyRegistered, etc.)
│   │   └── ports/               # Protocols (UserRepository, PasswordHasher, Clock, SecurityAuditLogger)
│   │
│   ├── application/             # Use cases (business operations)
│   │   └── use_cases/           # RegisterUser, VerifyCredentials, GetUser, UpdateProfile, DeactivateUser, ListUsers
│   │
│   ├── adapters/                # External integrations (pluggable)
│   │   ├── inbound/http/        # FastAPI routers, schemas, dependency injection
│   │   │   ├── main.py          # FastAPI app initialization
│   │   │   ├── deps.py          # Dependency providers (DI container)
│   │   │   ├── routers/         # Endpoint groups (users, internal_auth)
│   │   │   └── schemas/         # Pydantic request/response models
│   │   │
│   │   └── outbound/            # Persistence, external services
│   │       ├── persistence/     # SQLAlchemy repository, models, session management
│   │       ├── security/        # Argon2 hasher, JWT validator
│   │       └── observability/   # Structured logging (JSON)
│   │
│   └── migrations/              # Alembic database migrations
│
├── tests/                       # Test suite
│   ├── unit/                    # Domain & use case tests with fakes
│   │   ├── fakes.py             # FakeClock, FakeRepository for deterministic testing
│   │   └── ...
│   │
│   └── integration/             # End-to-end tests against real DB/HTTP
│
├── .claude/agents/              # Specialized Claude agent definitions
│   ├── arquiteto-back.md        # Architecture & design agent (Python senior staff)
│   └── dev-back.md              # Implementation agent (follows specs/tasks)
│
└── .specify/                    # SpecKit configuration & templates
```

## Development Workflow

This project uses **Spec-Driven Development (SDD)**. Features follow a two-phase workflow:

### Phase 1: Architecture & Design (arquiteto-back agent)

**When**: Feature is new or scope is ambiguous  
**Trigger**: User requests "design", "architecture", or "plan"

The `arquiteto-back` agent produces three artifacts:

1. **spec.md** — Functional requirements, user stories, success criteria, clarifications
2. **plan.md** — Hexagonal architecture, ADRs (Architecture Decision Records), technical decisions
3. **tasks.md** — Ordered implementation tasks, grouped by phase, with dependencies

**Process** (automatic via Spec Kit skills):
- `speckit-specify` → generate spec.md with requirements
- `speckit-clarify` → resolve ambiguities (up to 5 clarifying questions)
- `speckit-plan` → produce plan.md with architecture decisions
- `speckit-tasks` → break down into granular tasks in tasks.md
- `speckit-analyze` → cross-validate spec ↔ plan ↔ tasks consistency

**Deliverables**: spec.md + plan.md + tasks.md (reviewed before implementation)

### Phase 2: Implementation (dev-back agent)

**When**: spec.md / plan.md / tasks.md are approved and in place  
**Trigger**: User requests "implement", "code", "execute"

The `dev-back` agent implements tasks from `specs/<feature>/tasks.md`, strictly following the spec and plan.

**Process**:
- Follow each task in order (phases are sequential, tasks within a phase can parallelize if no dependency)
- Adhere to Hexagonal Architecture constraints: domain stays pure, adapters are pluggable
- Write tests alongside implementation (pytest + fakes for domain, httpx for HTTP contracts)
- Run validation against `quickstart.md` scenarios before declaring done

**Note**: Never invoke `dev-back` before `arquiteto-back` deliverables are ready. Implementation without approved specs risks rework.

## Common Commands

### Setup

```bash
# Install dependencies
uv sync

# Activate virtual environment (if not using uv run)
source .venv/bin/activate
```

### Database

```bash
# Run all pending migrations
uv run alembic upgrade head

# Create a new migration (after schema change in models.py)
uv run alembic revision --autogenerate -m "description"

# Rollback to previous migration (destructive in production)
uv run alembic downgrade -1
```

### Run & Develop

```bash
# Start development server (auto-reload)
uv run uvicorn user_api.adapters.inbound.http.main:app --reload

# Run with specific host/port
uv run uvicorn user_api.adapters.inbound.http.main:app --host 0.0.0.0 --port 8000
```

### Testing

```bash
# Run all tests
uv run pytest

# Run tests in a specific file
uv run pytest tests/unit/test_register_user.py

# Run a single test by name
uv run pytest tests/unit/test_register_user.py::test_register_user_success

# Run with coverage
uv run pytest --cov=user_api tests/

# Run only unit tests (fast, no DB)
uv run pytest tests/unit/

# Run only integration tests
uv run pytest tests/integration/

# Run with verbose output
uv run pytest -v
```

### Code Quality

```bash
# Lint with ruff
uv run ruff check user_api/ tests/

# Format code with ruff
uv run ruff format user_api/ tests/

# Type check with mypy (strict mode)
uv run mypy --strict user_api/

# Type check with pyright (strict mode, alternative)
uv run pyright --warnings user_api/

# Security audit
uv run bandit -r user_api/

# Dependency vulnerabilities
uv run pip-audit
```

### End-to-End Validation

```bash
# Run all 5 scenarios from quickstart.md (requires local Postgres + running server)
# See specs/001-user-api/quickstart.md for curl examples
# Validates: user registration, credential verification, profile access, deactivation, admin list
```

## Architecture Principles

### Hexagonal (Ports & Adapters)

- **Domain** (`user_api/domain/`) is framework-agnostic: no FastAPI, SQLAlchemy, JWT, hashing libraries imported here
  - Pure business logic: entities, value objects, use cases, domain errors
  - Ports (Protocols) define boundaries: `UserRepository`, `PasswordHasher`, `Clock`, `SecurityAuditLogger`
  
- **Adapters** (`user_api/adapters/`) plug into ports
  - Inbound: FastAPI HTTP layer, dependency injection, schema translation
  - Outbound: SQLAlchemy persistence, Argon2 hashing, JWKS-based JWT validation, structured logging

### Domain-Driven Design (DDD)

- **Aggregate Root**: `User` (single aggregate per service, no cross-aggregate transactions)
- **Value Objects**: `UserId` (UUID), `Email` (format validation), `Password` (policy check, transient), `PasswordHash` (hashed, persisted)
- **Exceptions**: Typed domain errors (`EmailAlreadyRegistered`, `WeakPassword`, `UserInactive`, `Forbidden`, `InvalidCredentials`)
- **No shared state**: Stateless use cases, dependency injection for external services

### Security by Design

- Passwords never logged, exposed in APIs, or stored in plaintext
  - `Password` (text) exists only during `RegisterUser` / `VerifyCredentials`
  - `PasswordHash` stored in DB via Argon2
  
- Credential verification is isolated
  - `VerifyCredentials` use case accessible only via internal service-to-service endpoint (`/internal/credentials/verify`)
  - Requires `X-Internal-Api-Key` header (separate from user JWT auth)
  
- Timing attack mitigation: dummy hash verification for non-existent users (FR-016)

- JWT validation only (never issued by user-api)
  - Validates signature via JWKS from external IdP
  - Checks expiration, issuer, audience
  
- Least Privilege: endpoints check user role before returning admin-only data

### Code Quality

- **DRY, KISS, Fail Fast**: Avoid premature abstraction; no speculative layers
- **No framework coupling**: Domain is testable without mocking the entire FastAPI app
- **Explicit over implicit**: Type annotations (mypy --strict), named dependencies, clear error types
- **Composition over inheritance**: Use protocols and dependency injection, not inheritance hierarchies

## Key Files & Patterns

### Domain Use Case Pattern

```python
# user_api/application/use_cases/register_user.py
class RegisterUser:
    def __init__(self, repo: UserRepository, hasher: PasswordHasher, clock: Clock):
        self.repo = repo
        self.hasher = hasher
        self.clock = clock
    
    async def execute(self, email: str, password: str) -> User:
        # Validate, call domain, persist, return
        pass
```

### FastAPI Dependency Injection

```python
# user_api/adapters/inbound/http/deps.py
async def get_user_repository() -> UserRepository:
    # Provide real or test instance
    pass

# user_api/adapters/inbound/http/routers/users.py
@router.post("/users")
async def register(
    req: RegisterUserRequest,
    use_case: RegisterUser = Depends(get_register_user_use_case)
) -> UserResponse:
    user = await use_case.execute(req.email, req.password)
    return UserResponse.from_domain(user)
```

### Testing Pattern

```python
# tests/unit/fakes.py
class FakeUserRepository(UserRepository):
    def __init__(self):
        self.users = []
    
    async def save(self, user: User) -> None:
        self.users.append(user)

# tests/unit/test_register_user.py
async def test_register_user_success():
    repo = FakeUserRepository()
    hasher = FakePasswordHasher()
    clock = FakeClock()
    use_case = RegisterUser(repo, hasher, clock)
    
    user = await use_case.execute("test@example.com", "Senha123!")
    assert user.email.value == "test@example.com"
    assert len(repo.users) == 1
```

## Debugging & Investigation

### Finding where something is used

```bash
# Search for a function name
uv run grep -r "register_user" user_api/ tests/

# Search for a class
uv run grep -r "class User" user_api/

# Search for imports
uv run grep -r "from user_api.domain" user_api/
```

### Checking domain isolation

```bash
# These should have zero matches (domain is framework-free)
grep -r "fastapi\|sqlalchemy\|pydantic\|jwt\|argon2" user_api/domain/
```

### Reviewing a migration

```bash
# See generated migration script
cat user_api/migrations/versions/<latest>.py

# Dry-run a migration
uv run alembic upgrade --sql head
```

## Configuration & Secrets

- `.env` file (not in git): database DSN, internal API key, JWKS URL, etc.
  - Example: `DATABASE_URL=postgresql+asyncpg://user:pass@localhost/user_api`
  
- Loaded at adapter initialization (inbound/http/deps.py or outbound/persistence/session.py)

- Never hardcode secrets; use environment variables

## Links & References

- **Spec & Design**: `specs/001-user-api/spec.md`, `plan.md`, `data-model.md`, `quickstart.md`
- **Agent Configs**: `.claude/agents/arquiteto-back.md`, `dev-back.md` (instructions for specialized agents)
- **SpecKit Templates**: `.specify/templates/` (spec-template.md, plan-template.md, tasks-template.md, etc.)
- **FastAPI Docs**: [fastapi.tiangolo.com](https://fastapi.tiangolo.com) — async path operations, dependency injection, Pydantic models
- **SQLAlchemy Async**: [docs.sqlalchemy.org](https://docs.sqlalchemy.org) — version 2.0+ async support
- **Alembic Migrations**: [alembic.sqlalchemy.org](https://alembic.sqlalchemy.org)
- **Pytest**: [docs.pytest.org](https://docs.pytest.org)
- **Hexagonal Architecture**: Alistair Cockburn's "Ports & Adapters" pattern
- **Domain-Driven Design**: Eric Evans' "Domain-Driven Design" book, or Vernon's "Implementing DDD"

## Quick Decisions

### Should I use the arquiteto-back agent?

✅ **Yes** if:
- Designing a new feature (not in specs/)
- Uncertain about architecture or scope
- Adding a new aggregate or major subsystem
- Proposing changes to ports/adapters pattern

❌ **No** if:
- Following an existing spec.md / tasks.md / plan.md
- Fixing a bug within a single use case
- Adding a simple endpoint that fits existing patterns

### Should I use the dev-back agent?

✅ **Yes** if:
- Implementing tasks from `specs/<feature>/tasks.md`
- Feature has an approved spec.md, plan.md, and tasks.md

❌ **No** if:
- Specs are not yet written (use arquiteto-back first)
- Task is a quick bug fix or refactor unrelated to a spec

## Known Constraints & Trade-offs

1. **Hexagonal overhead**: Full hexagonal pattern adds indirection (ports, adapters) vs. monolithic FastAPI. Justified by security requirements (isolate credential handling) and testability.

2. **Single Aggregate**: This service has one aggregate (User). Multi-aggregate bounded contexts would need event-driven communication (not implemented here).

3. **No caching**: Redis is not included in MVP. Can add if performance testing shows need.

4. **Async-first**: All database operations are async. Mixing sync/async code can cause deadlocks; always use `async`/`await`.

5. **Testing determinism**: Domain tests use `FakeClock` to control time; integration tests can use freezegun if needed.
