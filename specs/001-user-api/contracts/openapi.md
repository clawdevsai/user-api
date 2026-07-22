# API Contract: User API

Contrato descrito em formato resumido (OpenAPI completo a ser gerado por `tasks.md` a partir dos schemas Pydantic — FastAPI gera `/openapi.json` automaticamente a partir destes).

## Autenticação

- Endpoints públicos de usuário: `Authorization: Bearer <jwt>` — JWT emitido pelo IdP externo, validado pela user-api (assinatura via JWKS, `exp`, `iss`, `aud`).
- Endpoint interno (`/internal/credentials/verify`): autenticação service-to-service (header `X-Internal-Api-Key` ou mTLS, conforme infraestrutura de deploy), NUNCA aceita JWT de usuário final, NUNCA exposto via ingress público.

## Endpoints

### `POST /users` — Registrar usuário (público)

- **Request**: `{ "email": string, "password": string }`
- **201**: `{ "id": uuid, "email": string, "status": "ACTIVE", "roles": ["USER"], "created_at": datetime }`
- **409**: email já cadastrado
- **422**: email malformado ou senha fora da política mínima

### `POST /internal/credentials/verify` — Verificar credenciais (interno, service-to-service)

- **Request**: `{ "email": string, "password": string }`
- **200**: `{ "id": uuid, "roles": ["USER"], "status": "ACTIVE" }` — nunca inclui senha/hash
- **401**: credencial inválida OU usuário inexistente OU usuário inativo — resposta idêntica nos três casos (FR-016)
- **403**: chamador não autorizado a usar este canal (falha na auth service-to-service, antes mesmo de consultar a credencial)

### `GET /users/me` — Consultar próprio perfil (autenticado)

- **200**: `{ "id": uuid, "email": string, "status": string, "roles": [string], "created_at": datetime, "updated_at": datetime }`
- **401**: token ausente/inválido/expirado
- **403**: usuário resolvido do token está inativo

### `PATCH /users/me` — Atualizar próprio perfil (autenticado)

- **Request**: campos permitidos de profile (lista exata em `tasks.md`; exclui senha e roles nesta v1)
- **200**: perfil atualizado (mesmo shape de `GET /users/me`)
- **409**: conflito (ex.: novo email já em uso por outro usuário)
- **422**: dados inválidos

### `POST /users/{id}/deactivate` — Desativar conta (self ou admin)

- **204**: desativado (idempotente — repetir a chamada em usuário já inativo também retorna 204)
- **403**: chamador não é o próprio usuário nem admin
- **404**: usuário não encontrado

### `GET /users?page=&page_size=` — Listar usuários (admin)

- **200**: `{ "items": [ {id, email, status, roles, created_at} ], "page": int, "page_size": int, "total": int }`
- **403**: chamador não é admin
- **422**: parâmetros de paginação inválidos (normalizados para limites seguros quando possível, ver spec Edge Cases)

## Erros (formato consistente)

```json
{ "error": { "code": "EMAIL_ALREADY_REGISTERED", "message": "..." } }
```

Códigos de erro estáveis (contrato), mensagens podem evoluir sem quebrar clientes.
