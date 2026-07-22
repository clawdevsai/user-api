# Implementation Plan: User API

**Branch**: `001-user-api` | **Date**: 2026-07-21 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-user-api/spec.md`

## Summary

Serviço de domínio User (cadastro, verificação de credenciais para IdP externo, consulta/atualização de perfil, desativação soft-delete, listagem administrativa paginada). Arquitetura Hexagonal completa: domínio puro (entidade `User`, VOs `UserId`/`Email`/`PasswordHash`) isolado de FastAPI/SQLAlchemy; casos de uso dependem apenas de Ports; Adapters HTTP (FastAPI) e persistência (SQLAlchemy/Postgres) plugam nas bordas. JWT é validado (nunca emitido) pela user-api; a porta interna `VerifyCredentials` é o único canal que vê a senha em texto puro, restrito a chamada service-to-service do IdP externo.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: FastAPI ~0.136 (ver [PyPI](https://pypi.org/project/fastapi/)), Pydantic ~2.10, SQLAlchemy ~2.0 (async), Alembic, PyJWT ~2.10 (validação de JWT via JWKS do IdP), argon2-cffi (hash de senha — preferido a passlib, que está sem manutenção ativa; ver [PyPI](https://pypi.org/project/argon2-cffi/))

**Storage**: PostgreSQL (tabela `users`, unicidade de email via constraint de banco)

**Testing**: pytest + pytest-asyncio (casos de uso com fakes dos Ports); httpx `AsyncClient` para testes de contrato dos endpoints FastAPI

**Target Platform**: Linux server (container), deploy como serviço HTTP standalone

**Project Type**: web-service (backend único, sem frontend nesta feature)

**Performance Goals**: CRUD-tier informal — sem SLA formal definido pelo produto; alvo de engenharia p95 < 200ms em operações de leitura/escrita simples sob carga interna típica (não validado por benchmark; medir em staging antes de comprometer com SLA formal)

**Constraints**: sem HA multi-region; disponibilidade de instância única + réplica é suficiente neste estágio; sem requisito de offline

**Scale/Scope**: serviço de domínio único (User), estimativa inicial de dezenas de milhares de contas — sem necessidade de particionamento de banco nesta fase

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

`.specify/memory/constitution.md` está no template default, sem princípios de projeto preenchidos — não há gates específicos do projeto a checar. Gates aplicados são os princípios do próprio arquiteto (ordem de prioridade: segurança > corretude > simplicidade > testabilidade > performance > escalabilidade > observabilidade > conveniência):

| Gate | Avaliação |
|------|-----------|
| Domínio livre de framework/infra | PASS — `domain/` não importa FastAPI/SQLAlchemy/PyJWT/argon2 |
| Senha nunca em texto puro persistida/exposta | PASS — VO `PasswordHash` só guarda hash; `Password` (texto puro) é transiente, existe só durante `RegisterUser`/`VerifyCredentials`, nunca serializado em resposta ou log |
| Least Privilege no canal sensível | PASS — `VerifyCredentials` exposto apenas via rota interna, autenticação service-to-service separada do JWT de usuário final |
| Sem abstração especulativa | PASS — sem event bus, sem CQRS, sem multi-tenancy; um único agregado, repositório único, sem message broker (não solicitado) |
| Complexidade hexagonal proporcional | PASS COM RESSALVA — single-aggregate service normalmente dispensaria hexagonal completo (ver nota abaixo); aqui justificado por regra de segurança explícita (isolar hashing/JWT/persistência do domínio de credenciais) |

**Nota de proporcionalidade (transparência obrigatória)**: para um serviço de domínio único como este, Hexagonal completo tem custo real — mais indireção, mais arquivos, mais superfície para revisão — frente a um FastAPI+SQLAlchemy direto. A decisão (registrada em ADR-001 abaixo) foi confirmada explicitamente como requisito do usuário ("Hexagonal completo"), portanto aplicada sem alternativa mais simples proposta aqui.

## Project Structure

### Documentation (this feature)

```text
specs/001-user-api/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md         # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── openapi.md
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
user_api/
├── domain/
│   ├── entities/
│   │   └── user.py                # Aggregate root User (comportamento: activate/deactivate/update_profile)
│   ├── value_objects/
│   │   ├── user_id.py              # UserId (UUID)
│   │   ├── email.py                # Email (validação de formato)
│   │   └── password.py             # Password (política de complexidade, texto puro, transiente) + PasswordHash
│   ├── exceptions.py                # DomainError, EmailAlreadyRegistered, WeakPassword, UserInactive, ...
│   └── ports/
│       ├── user_repository.py       # Protocol: save, get_by_id, get_by_email, list_paginated
│       ├── password_hasher.py       # Protocol: hash(plain) -> str, verify(plain, hash) -> bool
│       ├── clock.py                 # Protocol: now() -> datetime (testabilidade de timestamps)
│       └── security_audit_logger.py # Protocol: log_event(event_type, user_id, metadata)
│
├── application/
│   └── use_cases/
│       ├── register_user.py
│       ├── verify_credentials.py    # porta interna, consumida pelo IdP externo
│       ├── resolve_authenticated_user.py  # usado pelo dependency de auth HTTP (a partir de claims do JWT já validado)
│       ├── get_user_by_id.py
│       ├── update_user_profile.py
│       ├── deactivate_user.py
│       └── list_users.py
│
├── adapters/
│   ├── inbound/
│   │   └── http/
│   │       ├── main.py               # app FastAPI, montagem de routers
│   │       ├── deps.py               # injeção de dependências (repos, hasher, use cases), dependency de auth JWT
│   │       ├── routers/
│   │       │   ├── users.py          # POST /users, GET/PATCH /users/me, POST /users/{id}/deactivate, GET /users
│   │       │   └── internal_auth.py  # POST /internal/credentials/verify (service-to-service)
│   │       └── schemas/              # Pydantic request/response models (não vazam para o domínio)
│   │           ├── user_schemas.py
│   │           └── auth_schemas.py
│   └── outbound/
│       ├── persistence/
│       │   ├── models.py             # SQLAlchemy ORM model (tabela users)
│       │   ├── user_repository_sqlalchemy.py  # implementa UserRepository
│       │   └── session.py            # engine/sessionmaker async
│       ├── security/
│       │   ├── argon2_password_hasher.py  # implementa PasswordHasher
│       │   └── jwt_validator.py            # valida JWT recebido (assinatura via JWKS do IdP, exp, iss)
│       └── observability/
│           └── structured_logger.py  # implementa SecurityAuditLogger (JSON logs)
│
├── migrations/                        # Alembic
└── config.py                          # settings (Pydantic Settings): DSN, JWKS URL do IdP, chave de API interna

tests/
├── unit/
│   └── domain/                        # testes do agregado User e VOs, sem infra
├── contract/
│   └── application/                   # casos de uso com fakes dos Ports (in-memory repo, hasher fake)
└── integration/
    └── http/                          # httpx AsyncClient contra app FastAPI + Postgres de teste (testcontainers ou DB efêmero)
```

**Structure Decision**: Single project hexagonal (`user_api/domain` → `application` → `adapters`), sem separação backend/frontend (não há frontend nesta feature). `domain/` e `application/` não importam `adapters/`; `adapters/` importam `application`/`domain`. Dependência sempre aponta para dentro (Dependency Rule).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|---------------------------------------|
| Hexagonal completo para serviço de agregado único | Requisito explícito do usuário; canal de credenciais (senha em texto puro) exige isolamento estrito de infra para reduzir superfície de vazamento e permitir troca de hasher/JWT sem tocar regra de negócio | FastAPI+SQLAlchemy direto (CRUD simples) foi considerado e é objetivamente menos código, mas foi descartado por decisão explícita do usuário, não por análise de custo-benefício deste arquiteto — registrado para transparência |
