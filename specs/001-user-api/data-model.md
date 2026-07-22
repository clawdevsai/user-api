# Phase 1 Data Model: User API

## Aggregate Root: `User`

| Campo | Tipo (domínio) | Regras |
|-------|----------------|--------|
| `id` | `UserId` (VO, UUID) | Gerado na criação, imutável |
| `email` | `Email` (VO) | Único no sistema (constraint de banco + checagem em `RegisterUser`); formato validado no VO |
| `password_hash` | `PasswordHash` (VO) | Nunca em texto puro; produzido via `PasswordHasher` port no momento do registro |
| `status` | Enum `UserStatus` (`ACTIVE` \| `INACTIVE`) | Transição unidirecional relevante ao caso de uso: `ACTIVE → INACTIVE` via `DeactivateUser`; não há reativação nesta versão (fora de escopo v1, ver spec Assumptions) |
| `roles` | `frozenset[Role]` | `Role` enum fechado: `USER`, `ADMIN`; default `{USER}` na criação |
| `created_at` | `datetime` (UTC) | Definido na criação via `Clock` port |
| `updated_at` | `datetime` (UTC) | Atualizado em qualquer mutação (`update_profile`, `deactivate`) |

### Invariantes do agregado

- `password_hash` nunca é serializado para fora do domínio (nenhum schema HTTP inclui esse campo).
- Um `User` com `status == INACTIVE` nunca passa em `VerifyCredentials` nem em `ResolveAuthenticatedUser`, independente de token/senha corretos (FR-011).
- `roles` nunca fica vazio; todo usuário tem ao menos `USER`.

### Comportamento (métodos do agregado, não CRUD anêmico)

- `User.register(email, password_hash, clock) -> User` (factory)
- `user.deactivate(clock) -> None` — idempotente (não lança erro se já inativo, ver spec Edge Cases)
- `user.update_profile(fields, clock) -> None` — aplica apenas campos permitidos (a definir a lista exata em `tasks.md`; email de profile NÃO inclui troca de senha/roles, fora de escopo v1)
- `user.verify_password(plain_password, hasher) -> bool` — delega ao `PasswordHasher` port, nunca compara string diretamente

## Value Objects

- **`UserId`**: wrapper de `uuid.UUID`. Igualdade por valor.
- **`Email`**: wrapper de `str`, valida formato no construtor (`__post_init__` levanta `InvalidEmail` se malformado). Normalizado para lowercase antes de comparar/persistir (evita duplicidade `A@x.com` vs `a@x.com`).
- **`Password`** (texto puro, transiente): existe apenas durante `RegisterUser`/`VerifyCredentials`; valida política mínima (comprimento ≥ 8, não está em lista de senhas triviais comuns — checagem simples, não integração com serviço externo de leaked-passwords nesta versão). Nunca persistido, nunca logado, nunca serializado.
- **`PasswordHash`**: wrapper do hash produzido pelo `PasswordHasher` port (string opaca, algoritmo determinado pelo adapter — Argon2id).

## Estados (`UserStatus`)

```text
   register()
       │
       ▼
   ┌────────┐   deactivate()   ┌──────────┐
   │ ACTIVE │ ───────────────► │ INACTIVE │
   └────────┘                  └──────────┘
        ▲                            │
        └────── (fora de escopo v1: reativação) 
```

## Tabela relacional (`adapters/outbound/persistence`)

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('ACTIVE', 'INACTIVE')),
    roles TEXT[] NOT NULL DEFAULT ARRAY['USER'],
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE UNIQUE INDEX ux_users_email ON users (lower(email));
```

- Unicidade de email garantida pelo índice único sobre `lower(email)` — fonte de verdade da unicidade é o banco, não a aplicação (ver research.md item 3).
- `roles` como array simples é suficiente para o conjunto fechado atual (`USER`/`ADMIN`); não é modelado como tabela de junção — YAGNI enquanto não houver necessidade de papéis dinâmicos/granulares.
