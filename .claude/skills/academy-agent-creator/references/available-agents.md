# Available Agents (academy/prompts)

Auto-generated reference. Run `python scripts/fetch_and_create_agent.py list` to refresh.

## Current agents

### backend-architect
- **File**: `criar-agente-backend-architect.md`
- **Purpose**: Design, review, and evolve Python backend architecture
- **Specialization**: Hexagonal architecture, DDD, security, performance, ADRs
- **When to use**: "Design a new feature", "Review architecture decision", "Plan module structure"

### backend-engineer
- **File**: `criar-agente-backend-enginner.md`
- **Purpose**: Implement backend features from approved specs
- **Specialization**: Follows specs/tasks.md, FastAPI, SQLAlchemy, async Python
- **When to use**: "Implement this feature", "Code the backend", "Execute tasks from spec"

### bug-fix
- **File**: `criar-agente-bug-fix.md`
- **Purpose**: Fix bugs with root cause analysis
- **Specialization**: Finds root causes, surgical fixes, prevents regressions
- **When to use**: "Fix this bug", "Debug why X is broken", "Find the real issue"

### code-review
- **File**: `criar-agente-code-review.md`
- **Purpose**: Technical code review with security and quality focus
- **Specialization**: Security audit, performance, maintainability, long-term health
- **When to use**: "Review this PR", "Audit this file", "Check code quality"

### cyber-security
- **File**: `criar-agente-cyber-security.md`
- **Purpose**: Security architecture and hardening
- **Specialization**: Threat modeling, OWASP, pen testing, compliance
- **When to use**: "Design secure system", "Find vulnerabilities", "Audit security posture"

### devops-engineer
- **File**: `criar-agente-devops-engineer.md`
- **Purpose**: CI/CD, infrastructure, containers, observability, automation
- **Specialization**: Python stack, Docker, Kubernetes, monitoring, secrets
- **When to use**: "Set up CI/CD", "Design infrastructure", "Automate deployment"

### qa-engineer
- **File**: `criar-agente-qa-engineer.md`
- **Purpose**: Test strategy, test generation, test automation
- **Specialization**: pytest, coverage, edge cases, regression testing
- **When to use**: "Create test plan", "Generate tests", "Improve test coverage"

### pre-commit-hook
- **File**: `criar-hook-pre-commit.md`
- **Purpose**: Configure and manage git pre-commit hooks
- **Specialization**: Linting, formatting, type checking, security checks
- **When to use**: "Set up pre-commit", "Add linter", "Automate checks"

---

## Quick reference by use case

| Need | Agent |
|------|-------|
| New feature design | backend-architect |
| Implement from spec | backend-engineer |
| Find & fix bug | bug-fix |
| Review PR/code | code-review |
| Security audit | cyber-security |
| Deploy/CI-CD | devops-engineer |
| Test strategy | qa-engineer |
| Pre-commit setup | pre-commit-hook |
