# Quickstart Validation: User API

Guia de validação ponta-a-ponta (não é passo de implementação — ver `tasks.md` para isso).

## Pré-requisitos

- Python 3.12, `uv` instalado
- Postgres local (ou container) acessível via DSN em `.env`
- Migrações Alembic aplicadas (`alembic upgrade head`)

## Setup

```bash
uv sync
uv run alembic upgrade head
uv run uvicorn user_api.adapters.inbound.http.main:app --reload
```

## Cenários de validação (mapeados às User Stories do spec.md)

### 1. Registro (User Story 1)

```bash
curl -X POST localhost:8000/users -d '{"email":"a@x.com","password":"Senha123!"}'
# Esperado: 201, corpo sem password_hash
curl -X POST localhost:8000/users -d '{"email":"a@x.com","password":"Outra123!"}'
# Esperado: 409 EMAIL_ALREADY_REGISTERED
```

### 2. Verificação de credenciais interna (User Story 2)

```bash
curl -X POST localhost:8000/internal/credentials/verify \
  -H "X-Internal-Api-Key: $INTERNAL_KEY" \
  -d '{"email":"a@x.com","password":"Senha123!"}'
# Esperado: 200 com claims mínimas (id, roles, status)

curl -X POST localhost:8000/internal/credentials/verify \
  -H "X-Internal-Api-Key: $INTERNAL_KEY" \
  -d '{"email":"a@x.com","password":"errada"}'
# Esperado: 401 (mesma resposta que email inexistente)
```

### 3. Acesso autenticado a perfil (User Story 2 + 3)

```bash
curl localhost:8000/users/me -H "Authorization: Bearer $JWT_DO_IDP"
# Esperado: 200 com dados do usuário, sem password_hash
curl -X PATCH localhost:8000/users/me -H "Authorization: Bearer $JWT_DO_IDP" -d '{"...campo permitido..."}'
# Esperado: 200 com dados atualizados
```

### 4. Desativação (User Story 4)

```bash
curl -X POST localhost:8000/users/<id>/deactivate -H "Authorization: Bearer $JWT_DO_IDP"
# Esperado: 204
curl -X POST localhost:8000/internal/credentials/verify -d '{"email":"a@x.com","password":"Senha123!"}'
# Esperado: 401 mesmo com senha correta — usuário inativo (FR-011)
curl -X POST localhost:8000/users/<id>/deactivate -H "Authorization: Bearer $JWT_DO_IDP"
# Esperado: 204 novamente (idempotente)
```

### 5. Listagem administrativa (User Story 5)

```bash
curl "localhost:8000/users?page=1&page_size=20" -H "Authorization: Bearer $JWT_ADMIN"
# Esperado: 200, lista paginada, sem password_hash em nenhum item
curl "localhost:8000/users?page=1&page_size=20" -H "Authorization: Bearer $JWT_USER_COMUM"
# Esperado: 403
```

## Critério de aceite do quickstart

Todos os 5 cenários acima devem passar em ambiente local antes de considerar a feature pronta para revisão — cobre as 5 User Stories do spec.md (P1–P3) e os requisitos de segurança críticos (FR-011, FR-015, FR-016).
