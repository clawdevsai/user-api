# Tasks: User API

**Input**: Design documents from `specs/001-user-api/` (plan.md, spec.md, data-model.md, contracts/openapi.md, research.md, quickstart.md)

**Tests**: incluídas (testabilidade é gate de prioridade 4 do arquiteto; domínio deve ser testável isolado de infra desde o início).

## Phase 1: Setup

- [ ] T001 Inicializar projeto com `uv init` e `pyproject.toml` (Python 3.12), configurar `ruff`, `mypy --strict` (ou `pyright` strict), `pre-commit` em `/Users/dieg/workspace/lab/project`
- [ ] T002 Criar esqueleto de pastas conforme `plan.md` (`user_api/domain`, `user_api/application/use_cases`, `user_api/adapters/inbound/http`, `user_api/adapters/outbound/{persistence,security,observability}`, `tests/{unit,contract,integration}`)
- [ ] T003 [P] Adicionar dependências via `uv add fastapi sqlalchemy[asyncio] asyncpg alembic pyjwt argon2-cffi pydantic-settings` e dev deps `uv add --dev pytest pytest-asyncio httpx ruff mypy`
- [ ] T004 [P] Configurar `user_api/config.py` (Pydantic Settings): DSN Postgres, JWKS URL do IdP, `issuer`/`audience` esperados do JWT, chave de API interna (`INTERNAL_API_KEY`)

## Phase 2: Foundational (bloqueante para todas as user stories)

- [ ] T005 Implementar VOs em `user_api/domain/value_objects/user_id.py`, `email.py`, `password.py` (Password texto puro transiente + PasswordHash) — ver data-model.md
- [ ] T006 Implementar exceções de domínio em `user_api/domain/exceptions.py` (`EmailAlreadyRegistered`, `WeakPassword`, `InvalidCredentials`, `UserNotFound`, `UserInactive`, `Forbidden`)
- [ ] T007 Implementar entidade `User` (aggregate root) em `user_api/domain/entities/user.py` com métodos `register`, `deactivate`, `update_profile`, `verify_password` — SEM import de FastAPI/SQLAlchemy/PyJWT/argon2
- [ ] T008 [P] Definir Ports (Protocols) em `user_api/domain/ports/`: `user_repository.py`, `password_hasher.py`, `clock.py`, `security_audit_logger.py`
- [ ] T009 [P] Implementar adapter `Clock` real (`utcnow()`) e um `FakeClock` em `tests/unit/fakes.py` para testes determinísticos
- [ ] T010 Configurar engine/sessionmaker async em `user_api/adapters/outbound/persistence/session.py` e ORM model `models.py` (tabela `users`, índice único `lower(email)`), gerar migração Alembic inicial em `user_api/migrations/`
- [ ] T011 [P] Implementar `SQLAlchemyUserRepository` em `user_api/adapters/outbound/persistence/user_repository_sqlalchemy.py` implementando o Port `UserRepository`
- [ ] T012 [P] Implementar `Argon2PasswordHasher` em `user_api/adapters/outbound/security/argon2_password_hasher.py` implementando `PasswordHasher`, com hash dummy de custo equivalente para caminho "usuário não existe" (mitigação de timing attack, FR-016)
- [ ] T013 [P] Implementar `StructuredSecurityAuditLogger` (JSON logging) em `user_api/adapters/outbound/observability/structured_logger.py` implementando `SecurityAuditLogger`
- [ ] T014 Montar app FastAPI base em `user_api/adapters/inbound/http/main.py` + injeção de dependências (`deps.py`: providers de repo/hasher/clock/logger via `Depends`)
- [ ] T015 Implementar `JwtValidator` (valida assinatura via JWKS cacheado, `exp`, `iss`, `aud`) em `user_api/adapters/outbound/security/jwt_validator.py` e dependency FastAPI `get_current_user` em `deps.py` que usa o use case `ResolveAuthenticatedUser`

**Checkpoint**: domínio testável isolado + infra base pronta. Nenhuma user story ainda entrega valor de ponta a ponta.

## Phase 3: User Story 1 - Cadastro de usuário (P1)

**Goal**: visitante registra conta com email/senha; conta passa a existir e ser consultável.

**Independent Test**: `POST /users` com dados válidos → 201; repetir mesmo email → 409 (ver quickstart.md cenário 1).

- [ ] T016 [P] [US1] Teste unitário do agregado `User.register` (email duplicado é responsabilidade do use case, não do agregado) em `tests/unit/domain/test_user.py`
- [ ] T017 [P] [US1] Teste de contrato do use case `RegisterUser` (fakes de repo/hasher/clock) em `tests/contract/application/test_register_user.py`
- [ ] T018 [US1] Implementar use case `RegisterUser` em `user_api/application/use_cases/register_user.py` (valida unicidade via repo, política de senha via VO `Password`, hash via `PasswordHasher`, persiste, loga evento de segurança)
- [ ] T019 [P] [US1] Schemas Pydantic de request/response em `user_api/adapters/inbound/http/schemas/user_schemas.py` (nunca incluir `password_hash`)
- [ ] T020 [US1] Endpoint `POST /users` em `user_api/adapters/inbound/http/routers/users.py`, mapear `EmailAlreadyRegistered`→409, `WeakPassword`→422
- [ ] T021 [US1] Teste de integração HTTP (httpx AsyncClient + Postgres de teste) cobrindo cenário 1 do quickstart.md em `tests/integration/http/test_register.py`

**Checkpoint**: US1 entregável e testável isoladamente (MVP mínimo).

## Phase 4: User Story 2 - Autenticação e acesso a recursos protegidos (P1)

**Goal**: IdP externo verifica credenciais via canal interno; requisições com JWT válido acessam recursos protegidos; usuários inativos são sempre rejeitados.

**Independent Test**: `POST /internal/credentials/verify` com credenciais corretas/incorretas (ver quickstart.md cenário 2); requisição autenticada com JWT válido/inválido/expirado.

- [ ] T022 [P] [US2] Teste de contrato do use case `VerifyCredentials` (credencial correta, incorreta, usuário inativo, usuário inexistente — resposta indistinguível) em `tests/contract/application/test_verify_credentials.py`
- [ ] T023 [P] [US2] Teste de contrato do use case `ResolveAuthenticatedUser` (usuário ativo resolve, inativo lança `UserInactive`) em `tests/contract/application/test_resolve_authenticated_user.py`
- [ ] T024 [US2] Implementar use case `VerifyCredentials` em `user_api/application/use_cases/verify_credentials.py` (busca por email, verifica hash, checa `status == ACTIVE`, resposta idêntica para "não existe"/"senha errada"/"inativo")
- [ ] T025 [US2] Implementar use case `ResolveAuthenticatedUser` em `user_api/application/use_cases/resolve_authenticated_user.py` (recebe `user_id` das claims já validadas do JWT, busca no repo, rejeita se inativo)
- [ ] T026 [P] [US2] Schemas de request/response do canal interno em `user_api/adapters/inbound/http/schemas/auth_schemas.py`
- [ ] T027 [US2] Endpoint `POST /internal/credentials/verify` em `user_api/adapters/inbound/http/routers/internal_auth.py`, protegido por dependency de auth service-to-service (valida `X-Internal-Api-Key`), NUNCA registrado no router público/ingress externo
- [ ] T028 [US2] Middleware/dependency `get_current_user` (T015) ligado ao `ResolveAuthenticatedUser`, aplicado como dependency nos endpoints protegidos (US3/US4/US5)
- [ ] T029 [US2] Testes de integração HTTP cobrindo cenário 2 e a rejeição de token de usuário inativo em `tests/integration/http/test_verify_credentials.py`

**Checkpoint**: US1 + US2 juntas cobrem o fluxo crítico de segurança completo (registro → autenticação → acesso).

## Phase 5: User Story 3 - Consulta e atualização de perfil (P2)

**Goal**: usuário autenticado vê e edita seus próprios dados; não pode mexer em dados de terceiros sem ser admin.

**Independent Test**: `GET /users/me` e `PATCH /users/me` autenticados; tentativa de editar outro usuário sem ser admin é negada (quickstart.md cenário 3).

- [ ] T030 [P] [US3] Teste de contrato `GetUserById` e `UpdateUserProfile` (autorização: dono ou admin) em `tests/contract/application/test_user_profile.py`
- [ ] T031 [US3] Implementar use case `GetUserById` em `user_api/application/use_cases/get_user_by_id.py`
- [ ] T032 [US3] Implementar use case `UpdateUserProfile` em `user_api/application/use_cases/update_user_profile.py` (checa autorização dono/admin, aplica só campos permitidos — sem senha/roles nesta v1)
- [ ] T033 [US3] Endpoints `GET /users/me` e `PATCH /users/me` em `routers/users.py`
- [ ] T034 [US3] Teste de integração HTTP cobrindo cenário 3 do quickstart.md em `tests/integration/http/test_profile.py`

## Phase 6: User Story 4 - Desativação de conta (P2)

**Goal**: usuário ou admin desativa conta (soft-delete), idempotente; autenticação futura desse usuário é sempre rejeitada.

**Independent Test**: desativar, confirmar 401 em tentativa de auth subsequente, repetir desativação sem erro (quickstart.md cenário 4).

- [ ] T035 [P] [US4] Teste unitário de `user.deactivate()` (idempotência) em `tests/unit/domain/test_user.py`
- [ ] T036 [P] [US4] Teste de contrato `DeactivateUser` (autorização dono/admin, idempotência) em `tests/contract/application/test_deactivate_user.py`
- [ ] T037 [US4] Implementar use case `DeactivateUser` em `user_api/application/use_cases/deactivate_user.py` (loga evento de segurança via `SecurityAuditLogger`)
- [ ] T038 [US4] Endpoint `POST /users/{id}/deactivate` em `routers/users.py`
- [ ] T039 [US4] Teste de integração HTTP cobrindo cenário 4 do quickstart.md em `tests/integration/http/test_deactivate.py`

## Phase 7: User Story 5 - Listagem administrativa de usuários (P3)

**Goal**: admin lista usuários paginados; não-admin é negado.

**Independent Test**: listar com admin (200, paginado) e com usuário comum (403) — quickstart.md cenário 5.

- [ ] T040 [P] [US5] Teste de contrato `ListUsers` (paginação, autorização admin-only) em `tests/contract/application/test_list_users.py`
- [ ] T041 [US5] Implementar use case `ListUsers` em `user_api/application/use_cases/list_users.py` (normaliza/rejeita parâmetros de paginação inválidos)
- [ ] T042 [US5] Adicionar método `list_paginated` ao `SQLAlchemyUserRepository` (T011) com `LIMIT`/`OFFSET` e `COUNT` total
- [ ] T043 [US5] Endpoint `GET /users` em `routers/users.py`
- [ ] T044 [US5] Teste de integração HTTP cobrindo cenário 5 do quickstart.md em `tests/integration/http/test_list_users.py`

## Phase 8: Polish & Cross-Cutting

- [ ] T045 [P] Rodar `ruff check`, `mypy --strict` (ou `pyright --strict`) em todo `user_api/` e corrigir achados
- [ ] T046 [P] Recomendar (não executar) `pip-audit`/`osv-scanner` e `bandit`/`semgrep` sobre as dependências e o código antes do primeiro deploy
- [ ] T047 Adicionar `healthz`/`readyz` (liveness/readiness) em `main.py`, sem depender do domínio
- [ ] T048 Validar manualmente todos os 5 cenários de `quickstart.md` em ambiente local com Postgres real
- [ ] T049 Revisar CI (lint + mypy + pytest) antes do primeiro merge

## Dependencies & Execution Order

- Phase 1 (Setup) → Phase 2 (Foundational) bloqueiam tudo.
- User Story 1 (P1) é o MVP mínimo — nenhuma outra story depende dela para ser testável isoladamente, mas US2 assume que US1 já criou usuários para autenticar.
- US3, US4, US5 dependem de US2 (dependency `get_current_user`) mas são independentes entre si — podem ser feitas em qualquer ordem ou em paralelo após US2.
- Tarefas marcadas `[P]` dentro da mesma fase tocam arquivos diferentes e são paralelizáveis entre si.

## Suggested MVP Scope

Fases 1–4 (Setup, Foundational, US1, US2) entregam o fluxo de segurança completo (registro + verificação de credenciais + acesso autenticado) — MVP demonstrável. US3–US5 são incrementos independentes sobre esse MVP.
