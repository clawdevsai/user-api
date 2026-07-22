# Phase 0 Research: User API

Nenhum `NEEDS CLARIFICATION` remanescente no Technical Context (todos resolvidos via defaults confirmados + `speckit-clarify`). Este documento registra as decisões técnicas de suporte e alternativas descartadas.

## 1. Hashing de senha

- **Decision**: `argon2-cffi` (Argon2id), wrapped em `Adapters/outbound/security/argon2_password_hasher.py` implementando o Port `PasswordHasher`.
- **Rationale**: Argon2id é a recomendação atual da OWASP Password Storage Cheat Sheet para hashing de senha de propósito geral; resistente a GPU/ASIC cracking.
- **Alternatives considered**: `passlib` (API mais familiar, porém projeto sem release ativo há anos — risco de manutenção); `bcrypt` puro (aceitável, mas limite de 72 bytes de entrada e sem proteção configurável de memória como Argon2).

## 2. Validação de JWT

- **Decision**: `PyJWT` + cache de JWKS do IdP externo (endpoint `.well-known/jwks.json`), validando assinatura (RS256/ES256 conforme IdP), `exp`, `iss` e `aud`.
- **Rationale**: biblioteca madura, mantida, sem dependência de framework específico — mantém o adapter fino e substituível.
- **Alternatives considered**: `python-jose` (também viável, mas manutenção mais irregular no histórico do projeto); implementação manual de verificação de assinatura (rejeitada — reinventar criptografia é risco de segurança, nunca fazer).

## 3. Persistência

- **Decision**: SQLAlchemy 2.x (estilo `async` com `asyncpg`), migrações via Alembic, constraint `UNIQUE` em `email` no banco (fonte de verdade da unicidade, não apenas checagem em aplicação — evita condição de corrida em registros concorrentes, ver FR-002/SC-004).
- **Rationale**: unicidade garantida apenas em nível de aplicação é vulnerável a race condition entre "checar existência" e "inserir"; constraint de banco fecha essa lacuna sem lock explícito.
- **Alternatives considered**: lock de aplicação (via advisory lock ou lock distribuído) — descartado, complexidade desnecessária quando a constraint de unicidade do Postgres resolve o mesmo problema de forma mais simples e nativa.

## 4. Canal interno de verificação de credenciais (`VerifyCredentials`)

- **Decision**: endpoint HTTP dedicado (`POST /internal/credentials/verify`), protegido por autenticação service-to-service (API key estática rotacionável via secret manager, ou mTLS se a infraestrutura de rede já suportar — decisão de infraestrutura fora do escopo desta feature, documentar como constraint de deploy), roteável apenas na rede interna (não exposto publicamente via ingress externo).
- **Rationale**: menor superfície nova — reaproveita o mesmo transporte HTTP/FastAPI já usado pelos demais endpoints, sem introduzir um segundo protocolo (gRPC) só para este canal.
- **Alternatives considered**: gRPC dedicado para comunicação interna — rejeitado, YAGNI; não há requisito de performance ou multi-linguagem que justifique um segundo protocolo além do REST já existente.

## 5. Resposta indistinguível na verificação de credenciais (FR-016)

- **Decision**: mesmo tempo de resposta aproximado e mesma mensagem de erro genérica para "email não encontrado" e "senha incorreta"; hash é sempre computado (ou um hash dummy de custo equivalente) mesmo quando o email não existe, para não vazar por timing.
- **Rationale**: prática padrão anti-enumeração/anti-timing-attack (OWASP Authentication Cheat Sheet).
- **Alternatives considered**: mensagens diferenciadas (mais amigável para UX de login) — rejeitada para este canal por ser consumido apenas pelo IdP, não por usuário final; UX de erro de login é responsabilidade do IdP, não desta API.

## 6. Observabilidade

- **Decision**: logging estruturado (JSON) via `logging` stdlib + `python-json-logger` (ou `structlog`, a confirmar em `tasks.md` conforme preferência do time), com `request_id`/`correlation_id` propagado via header e incluído em todo log; eventos de segurança (FR-014) logados como categoria própria (`event_type=security`).
- **Rationale**: logs estruturados são suficientes para o CRUD-tier declarado; tracing distribuído completo (OpenTelemetry) é recomendado, mas não obrigatório nesta fase — sem múltiplos serviços a correlacionar além do IdP externo.
- **Alternatives considered**: OpenTelemetry tracing completo desde o dia 1 — descartado por ora (YAGNI dado o SLA CRUD-tier sem SLO formal); documentado como evolução futura de baixo custo (`ponytail:` — adicionar quando houver mais de 2-3 serviços a correlacionar em produção).
