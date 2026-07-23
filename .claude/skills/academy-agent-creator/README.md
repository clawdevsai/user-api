# Academy Agent Creator Skill

Automatiza criação de agentes Claude a partir de prompts predefinidos no repositório [clawdevsai/academy](https://github.com/clawdevsai/academy/tree/main/prompts).

## Overview

- **Fonte**: GitHub repo `clawdevsai/academy/prompts/`
- **Output**: Agentes em `.claude/agents/<nome>.md`
- **Tempo**: ~5-10 segundos por agente (download + setup)
- **Requer**: `gh cli` instalado e autenticado

## Usage

### Via slash command (quando disponível)

```
/academy-agent-creator backend-architect
/academy-agent-creator code-review
/academy-agent-creator list
```

### Via script direto

```bash
python3 scripts/fetch_and_create_agent.py backend-architect
python3 scripts/fetch_and_create_agent.py list
python3 scripts/fetch_and_create_agent.py devops-engineer --output-dir=.claude/agents
```

### Listar agentes disponíveis

```bash
python3 scripts/fetch_and_create_agent.py list
```

Output:
```
backend-architect
backend-enginner
bug-fix
code-review
cyber-security
devops-engineer
qa-engineer
criar-hook-pre-commit
```

## Agentes disponíveis

| Nome | Arquivo | Propósito |
|------|---------|----------|
| **backend-architect** | `criar-agente-backend-architect.md` | Design & review arquitetura Python |
| **backend-engineer** | `criar-agente-backend-enginner.md` | Implementar features de specs |
| **bug-fix** | `criar-agente-bug-fix.md` | Encontrar & corrigir bugs |
| **code-review** | `criar-agente-code-review.md` | Review técnico de código |
| **cyber-security** | `criar-agente-cyber-security.md` | Arquitetura de segurança |
| **devops-engineer** | `criar-agente-devops-engineer.md` | CI/CD, infraestrutura |
| **qa-engineer** | `criar-agente-qa-engineer.md` | Testes, QA, cobertura |
| **pre-commit-hook** | `criar-hook-pre-commit.md` | Git pre-commit setup |

## Quick examples

### 1. Criar agente backend-architect

```bash
# Lista primeiro
python3 scripts/fetch_and_create_agent.py list

# Cria
python3 scripts/fetch_and_create_agent.py backend-architect

# Resultado
✓ Agent created: .claude/agents/backend-architect.md
```

### 2. Criar agente code-review

```bash
python3 scripts/fetch_and_create_agent.py code-review
```

### 3. Criar em local customizado

```bash
python3 scripts/fetch_and_create_agent.py devops-engineer --output-dir=/tmp/agents
```

## Requisitos

### Instalados
- `gh` CLI: `brew install gh` (macOS) ou equivalente
- `python3` 3.8+

### Configurado
- `gh auth login` — autenticar com GitHub

### Verify

```bash
gh auth status
python3 --version
```

## Como funciona internamente

1. **List**: `gh api repos/clawdevsai/academy/contents/prompts`
2. **Fetch**: `gh api repos/clawdevsai/academy/contents/prompts/criar-agente-<nome>.md`
3. **Decode**: Base64 decode do campo `.content`
4. **Write**: Salva em `.claude/agents/<nome>.md`

Tudo via API GitHub — sem clonar repo inteiro.

## Troubleshooting

### Error: `gh: command not found`

Instale GitHub CLI:
```bash
brew install gh
gh auth login
```

### Error: `Failed to fetch ...`

Verifique autenticação:
```bash
gh auth status
gh auth login  # If not authenticated
```

### Agent já existe

Script avisa, mas não sobrescreve por padrão. Remover manualmente:
```bash
rm .claude/agents/backend-architect.md
```

Depois recriar.

## Files

```
academy-agent-creator/
├── SKILL.md                          # Skill definition
├── README.md                         # Este arquivo
├── scripts/
│   └── fetch_and_create_agent.py    # Main script
└── references/
    └── available-agents.md           # Agentes listados
```

## Future improvements

- [ ] Fuzzy match melhorado (typos)
- [ ] Sync automático de atualizações (versioning)
- [ ] Copy to clipboard option
- [ ] Generate from URL (agente customizado via prompt)
- [ ] Merge with existing agente (override prompt only)
