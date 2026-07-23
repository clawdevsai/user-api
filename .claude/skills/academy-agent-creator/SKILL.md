---
name: academy-agent-creator
description: Create Claude agents from predefined prompts in the academy repo. Use when user wants to generate a new agent ("create agent X", "I need a backend architect agent", "set up a DevOps agent"). Searches the academy/prompts library, reads the matching prompt definition, and scaffolds the agent in `.claude/agents/`. Supports fuzzy matching on agent name or description.
compatibility: gh cli (must be installed), Python 3.8+
---

## Overview

Automates agent creation by:
1. Querying the `clawdevsai/academy` repo (GitHub CLI)
2. Finding matching prompt in `prompts/` folder
3. Reading the full prompt definition
4. Generating `.claude/agents/<name>.md` locally

## When to use

- **"Create a backend architect agent"** → finds `criar-agente-backend-architect.md`, scaffolds it
- **"I need code review agent"** → finds `criar-agente-code-review.md`
- **"Set up DevOps"** → finds `criar-agente-devops-engineer.md`
- **"List available agents"** → shows all prompts in academy/prompts/

## Supported agents

Currently available in academy/prompts/:
- `backend-architect` — Design & review Python backend architecture
- `backend-engineer` — Implement backend features from specs
- `bug-fix` — Fix bugs with root cause analysis
- `code-review` — Technical code review & security audit
- `cyber-security` — Security architecture & hardening
- `devops-engineer` — CI/CD, infrastructure, automation
- `qa-engineer` — Test strategy, test generation, QA
- `pre-commit-hook` — Git pre-commit automation

## How it works

### Command form

```
/academy-agent-creator [agent-name]
```

### Examples

```
/academy-agent-creator backend-architect
/academy-agent-creator code-review
/academy-agent-creator list
```

If no agent specified, Claude will:
1. Ask which agent user needs, OR
2. Show available options if context is clear

### Workflow

1. **Match**: Find prompt matching user request (substring, fuzzy name, or exact match)
2. **Fetch**: Clone or `gh api` to get prompt from academy repo
3. **Parse**: Extract agent definition (name, description, tools, instructions)
4. **Create**: Write `.claude/agents/<name>.md` with full prompt content
5. **Confirm**: Show user what was created, where it lives

## Output

Agent file at `.claude/agents/<agent-name>.md`:

```markdown
---
name: my-agent
description: What this agent does
tools: [Read, Edit, Bash, ...]
---

[Full prompt from academy/prompts]
```

Agent is immediately available in Claude Code — no restart needed.

## Edge cases

- **Agent already exists**: Ask user — overwrite, skip, or version (`_v2`)?
- **Multiple matches**: List options, ask user to pick
- **Offline**: Fall back to bundled `references/available-agents.md`
- **Permission denied**: Prompt to run `gh auth login` first

## Configuration

Requires:
- `gh` CLI installed (`brew install gh`)
- Authenticated GitHub access (`gh auth login`)
- Network access (or can use cached copy)

No other config needed.
