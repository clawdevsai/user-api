# Feature Specification: User API

**Feature Branch**: `001-user-api`

**Created**: 2026-07-21

**Status**: Draft

**Input**: User description: "user-api backend. Serviço de domínio User: cadastro, autenticação (validação de JWT emitido externamente), consulta, atualização e desativação (soft-delete) de usuários. Value Objects: Email, Password, UserId. Aggregate root: User (id, email, password_hash, status, roles, created_at, updated_at). Casos de uso: RegisterUser, AuthenticateUser, GetUserById, UpdateUserProfile, DeactivateUser, ListUsers (paginado)."

## Clarifications

### Session 2026-07-21

- Q: A user-api valida a senha do usuário (login) ou apenas valida JWTs já assinados por um IdP externo, sem nunca ver a senha em texto puro após o registro? → A: user-api é a fonte de verdade da credencial (email + password_hash) e expõe uma porta interna de verificação de credenciais (`VerifyCredentials`), consumida apenas por um IdP externo via chamada service-to-service autenticada (mTLS ou API key, não exposta publicamente). O IdP externo continua sendo o único emissor/assinante do JWT; a user-api nunca emite token, apenas valida os JWTs recebidos nas demais rotas.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cadastro de usuário (Priority: P1)

Um novo usuário se registra fornecendo email e senha, recebendo confirmação de que sua conta foi criada.

**Why this priority**: sem cadastro não há usuários no sistema; é o ponto de entrada de todo o resto.

**Independent Test**: enviar dados válidos de registro e verificar que o usuário passa a existir e pode ser consultado.

**Acceptance Scenarios**:

1. **Given** nenhum usuário com o email informado, **When** o visitante se registra com email e senha válidos, **Then** o usuário é criado com status ativo e os dados sensíveis (senha) nunca retornam em texto puro.
2. **Given** um usuário já existe com o email informado, **When** um novo registro é tentado com o mesmo email, **Then** o sistema rejeita com erro de conflito, sem revelar se o email já existe por motivo de segurança vs. usabilidade (ver Assumptions).
3. **Given** uma senha que não atende à política mínima, **When** o registro é tentado, **Then** o sistema rejeita explicando o motivo.

---

### User Story 2 - Autenticação e acesso a recursos protegidos (Priority: P1)

Um usuário autenticado (portador de um token emitido por serviço externo) acessa endpoints que exigem identidade confirmada. Internamente, o IdP externo que emitiu esse token consultou a user-api para verificar a credencial (email/senha) antes de assinar o JWT.

**Why this priority**: sem autenticação, não há como restringir acesso aos próprios dados ou a operações administrativas.

**Independent Test**: enviar uma requisição com token válido e verificar acesso concedido; com token ausente/inválido/expirado, verificar acesso negado. Separadamente, testar a porta interna de verificação de credenciais com credenciais corretas e incorretas.

**Acceptance Scenarios**:

1. **Given** um token válido e não expirado, **When** o usuário acessa um recurso protegido, **Then** o acesso é concedido e a identidade do usuário é resolvida a partir do token.
2. **Given** um token ausente, inválido, expirado ou de um usuário desativado, **When** o acesso é tentado, **Then** o sistema nega o acesso com erro apropriado (401/403).
3. **Given** uma chamada interna autenticada (service-to-service) de um IdP autorizado com email e senha corretos, **When** a verificação de credenciais é solicitada, **Then** o sistema confirma a credencial e retorna claims mínimas (id, roles, status) sem nunca retornar a senha ou o hash.
4. **Given** uma chamada interna com credenciais incorretas ou usuário inativo, **When** a verificação é solicitada, **Then** o sistema nega a verificação sem detalhar o motivo exato (mesma resposta para "não existe" e "senha errada").

---

### User Story 3 - Consulta e atualização de perfil (Priority: P2)

Um usuário autenticado consulta seus próprios dados e atualiza informações de perfil.

**Why this priority**: valor incremental sobre cadastro/autenticação; não bloqueia o MVP de ter usuários existindo e autenticando.

**Independent Test**: autenticar, buscar o próprio perfil, alterá-lo, e confirmar que a alteração persiste.

**Acceptance Scenarios**:

1. **Given** um usuário autenticado, **When** ele solicita seus próprios dados, **Then** o sistema retorna os dados do usuário sem o hash de senha.
2. **Given** um usuário autenticado, **When** ele atualiza campos permitidos do próprio perfil, **Then** as mudanças são persistidas e refletidas em consultas subsequentes.
3. **Given** um usuário autenticado, **When** ele tenta atualizar o perfil de outro usuário sem permissão administrativa, **Then** o sistema nega a operação.

---

### User Story 4 - Desativação de conta (Priority: P2)

Um usuário ou administrador desativa uma conta (soft-delete), preservando o histórico mas impedindo autenticação futura.

**Why this priority**: necessário para compliance/operação, mas não bloqueia o fluxo primário de cadastro+autenticação.

**Independent Test**: desativar um usuário e confirmar que ele não consegue mais autenticar (nem via JWT existente, nem via verificação de credenciais), mas o registro permanece consultável por administradores.

**Acceptance Scenarios**:

1. **Given** um usuário ativo, **When** a desativação é solicitada por si mesmo ou por um administrador, **Then** o status muda para inativo e autenticações futuras desse usuário são rejeitadas.
2. **Given** um usuário já desativado, **When** a desativação é solicitada novamente, **Then** o sistema responde de forma idempotente, sem erro.

---

### User Story 5 - Listagem administrativa de usuários (Priority: P3)

Um administrador lista usuários cadastrados de forma paginada, para fins de gestão.

**Why this priority**: funcionalidade administrativa de suporte; não essencial ao MVP de cadastro/autenticação/perfil.

**Independent Test**: com múltiplos usuários cadastrados, um administrador solicita a lista e recebe páginas de resultado consistentes.

**Acceptance Scenarios**:

1. **Given** N usuários cadastrados, **When** um administrador solicita a listagem paginada, **Then** o sistema retorna os resultados em páginas de tamanho controlado, sem expor hash de senha.
2. **Given** um usuário sem permissão administrativa, **When** ele tenta listar todos os usuários, **Then** o sistema nega a operação.

### Edge Cases

- O que acontece quando o token é válido mas o usuário correspondente foi desativado ou excluído após a emissão do token? → acesso deve ser negado (revalidação de status a cada requisição, ver FR-011).
- Como o sistema trata tentativas concorrentes de registro com o mesmo email? → apenas uma tentativa deve ter sucesso (unicidade garantida na camada de persistência).
- Como o sistema trata solicitação de atualização de email para um já usado por outro usuário? → rejeitar com erro de conflito.
- Como o sistema trata paginação com parâmetros inválidos (página negativa, tamanho excessivo)? → normalizar para limites seguros ou rejeitar com erro de validação.
- Como o sistema trata uma chamada à porta interna de verificação de credenciais vinda de um chamador não autorizado (não é o IdP registrado)? → rejeitar antes mesmo de consultar a credencial (autenticação service-to-service falha primeiro).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema DEVE permitir que um novo usuário se registre com email e senha.
- **FR-002**: O sistema DEVE validar formato de email e impor unicidade de email entre usuários ativos e inativos.
- **FR-003**: O sistema DEVE impor uma política mínima de complexidade de senha e nunca armazenar ou expor a senha em texto puro.
- **FR-004**: O sistema DEVE validar tokens de identidade (JWT) emitidos por um provedor de identidade externo, incluindo assinatura, expiração e emissor.
- **FR-005**: O sistema DEVE resolver a identidade do usuário autenticado a partir das claims do token validado.
- **FR-006**: O sistema DEVE permitir que um usuário autenticado consulte seus próprios dados, sem expor o hash de senha.
- **FR-007**: O sistema DEVE permitir que um usuário autenticado atualize campos permitidos do próprio perfil.
- **FR-008**: O sistema DEVE impedir que um usuário atualize ou consulte dados de outro usuário, exceto administradores.
- **FR-009**: O sistema DEVE permitir a desativação (soft-delete) de uma conta, preservando o registro histórico.
- **FR-010**: O sistema NÃO DEVE excluir fisicamente registros de usuário via operação de desativação.
- **FR-011**: O sistema DEVE rejeitar autenticação/acesso de usuários com status inativo, mesmo com token tecnicamente válido.
- **FR-012**: O sistema DEVE permitir que administradores listem usuários de forma paginada.
- **FR-013**: O sistema DEVE negar operações administrativas (listagem geral, atualização/desativação de terceiros) a usuários sem papel administrativo.
- **FR-014**: O sistema DEVE registrar (log) eventos de segurança relevantes: registro, autenticação com falha, desativação de conta.
- **FR-015**: O sistema DEVE expor uma porta de verificação de credenciais (email + senha) restrita a chamadas service-to-service autenticadas de um IdP externo autorizado, retornando apenas claims mínimas (id, roles, status) sem expor senha ou hash, e nunca emitindo o JWT em si (responsabilidade do IdP).
- **FR-016**: O sistema DEVE responder de forma indistinguível a "credencial inexistente" e "senha incorreta" na verificação de credenciais, para não permitir enumeração de contas por esse canal.

### Key Entities

- **User (Aggregate Root)**: representa uma conta no sistema. Atributos: identificador único, email, senha (armazenada apenas como hash), status (ativo/inativo), papéis/roles, timestamps de criação e atualização.
- **Email (Value Object)**: endereço de email validado quanto a formato, único no sistema.
- **Password (Value Object)**: representa a senha do usuário exclusivamente em sua forma de hash; a senha em texto puro nunca é persistida nem retorna em nenhuma resposta.
- **Role**: papel atribuído ao usuário (ex.: usuário comum, administrador), usado para autorização.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Um novo usuário consegue se registrar e, em seguida, ser autenticado com sucesso (via IdP externo consultando a user-api) em uma única sessão de uso, sem etapas manuais adicionais.
- **SC-002**: 100% das respostas do sistema (registro, consulta, listagem, verificação de credenciais) nunca expõem senha em texto puro ou hash de senha.
- **SC-003**: Usuários desativados têm 100% das tentativas de acesso a recursos protegidos e de verificação de credenciais negadas, verificável em auditoria.
- **SC-004**: Tentativas de registro com email duplicado são rejeitadas em 100% dos casos, mesmo sob tentativas concorrentes.
- **SC-005**: Uma listagem administrativa de usuários retorna resultados consistentes e paginados independente do volume de usuários cadastrados.

## Assumptions

- A emissão e assinatura de JWT é responsabilidade exclusiva de um IdP externo; a user-api nunca emite token. A user-api é a fonte de verdade da credencial e expõe uma porta interna de verificação (`VerifyCredentials`) consumida apenas pelo IdP via chamada service-to-service autenticada (ver Clarifications).
- Papéis (roles) são um conjunto fechado e simples (ex.: `user`, `admin`) definidos estaticamente, sem necessidade de sistema de permissões granular neste momento.
- Mensagens de erro de registro com email duplicado podem informar explicitamente o conflito (prioriza usabilidade sobre enumeração de contas), por se tratar de um serviço interno/CRUD-tier, não uma aplicação pública de alto risco. Já a verificação de credenciais (login) segue a prática padrão de resposta indistinguível, por ser um caminho de maior sensibilidade a ataques de enumeração/força bruta.
- Sem requisito formal de SLA de disponibilidade multi-region; alvo informal de resposta rápida (sub-segundo) sob carga típica de aplicação interna.
- Exclusão física (hard delete) de usuários está fora de escopo desta feature; apenas soft-delete (desativação) é suportado.
- Atualização de perfil não inclui troca de senha nem de papéis/roles nesta versão (fora de escopo v1).
