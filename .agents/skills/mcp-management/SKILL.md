---
name: mcp-management
description: Use when the user asks to manage MCP integrations.
---

# MCP Management

Skill for managing and interacting with Model Context Protocol (MCP) servers.

## Overview

MCP is an open protocol enabling AI agents to connect to external tools and data sources. This skill provides scripts and utilities to discover, analyze, and execute MCP capabilities from configured servers without polluting the main context window.

**Key Benefits**:
- Progressive disclosure of MCP capabilities (load only what's needed)
- Intelligent tool/prompt/resource selection based on task requirements
- Multi-server management from single config file
- Context-efficient: subagents handle MCP discovery and execution
- Persistent tool catalog: automatically saves discovered tools to JSON for fast reference

## When to Use This Skill

Use this skill when:
1. **Discovering MCP Capabilities**: Need to list available tools/prompts/resources from configured servers
2. **Task-Based Tool Selection**: Analyzing which MCP tools are relevant for a specific task
3. **Executing MCP Tools**: Calling MCP tools programmatically with proper parameter handling
4. **MCP Integration**: Building or debugging MCP client implementations
5. **Context Management**: Avoiding context pollution by delegating MCP operations to subagents

## Core Capabilities

### 1. Configuration Management

MCP servers configured in `.claude/.mcp.json`.

**Gemini CLI integration** (one optional path, when that CLI is the exposed
capability): create a symlink to `.gemini/settings.json`:
```bash
mkdir -p .gemini && ln -sf .claude/.mcp.json .gemini/settings.json
```

See [references/configuration.md](references/configuration.md) and [references/gemini-cli-integration.md](references/gemini-cli-integration.md).

### 2. Capability Discovery

```bash
npx tsx scripts/cli.ts list-tools  # Saves to assets/tools.json
npx tsx scripts/cli.ts list-prompts
npx tsx scripts/cli.ts list-resources
```

Aggregates capabilities from multiple servers with server identification.

### 3. Intelligent Tool Analysis

LLM analyzes `assets/tools.json` directly - better than keyword matching algorithms.

### 4. Tool Execution

**Capability-first and provider-neutral**: use whichever MCP execution path the
current executor actually exposes. Gemini CLI is one supported path, not a
required provider. An equivalent host MCP client, Chrome DevTools MCP,
Playwright, or another executor-native capability is equally valid when it
satisfies the task contract. Do not add a second router or registry.

**Example path: Gemini CLI** (if available)
```bash
gemini -y -m gemini-2.5-flash -p "Take a screenshot of https://example.com"
```

**Secondary: Direct Scripts**
```bash
npx tsx scripts/cli.ts call-tool memory create_entities '{"entities":[...]}'
```

**Fallback: mcp-manager Subagent**

See [references/gemini-cli-integration.md](references/gemini-cli-integration.md) for complete examples.

## Implementation Patterns

### Pattern 1: Gemini CLI Auto-Execution (example provider)

Use Gemini CLI for automatic tool discovery and execution. See [references/gemini-cli-integration.md](references/gemini-cli-integration.md) for complete guide.

**Quick Example**:
```bash
gemini -y -m gemini-2.5-flash -p "Take a screenshot of https://example.com"
```

**Benefits**: Automatic tool discovery, natural language execution, faster than subagent orchestration.

### Pattern 2: Subagent-Based Execution (Fallback)

Use the `mcp-manager` agent (or the equivalent delegation capability) when a
direct execution path is unavailable or context cost matters. Subagent discovers tools, selects relevant ones, executes tasks, reports back.

**Benefit**: Main context stays clean, only relevant tool definitions loaded when needed.

### Pattern 3: LLM-Driven Tool Selection

LLM reads `assets/tools.json`, intelligently selects relevant tools using context understanding, synonyms, and intent recognition.

### Pattern 4: Multi-Server Orchestration

Coordinate tools across multiple servers. Each tool knows its source server for proper routing.

## Scripts Reference

### scripts/mcp-client.ts

Core MCP client manager class. Handles:
- Config loading from `.claude/.mcp.json`
- Connecting to multiple MCP servers
- Listing tools/prompts/resources across all servers
- Executing tools with proper error handling
- Connection lifecycle management

### scripts/cli.ts

Command-line interface for MCP operations. Commands:
- `list-tools` - Display all tools and save to `assets/tools.json`
- `list-prompts` - Display all prompts
- `list-resources` - Display all resources
- `call-tool <server> <tool> <json>` - Execute a tool

**Note**: `list-tools` persists complete tool catalog to `assets/tools.json` with full schemas for fast reference, offline browsing, and version control.

## Quick Start

**Method 1: Gemini CLI** (one example path, when available)
```bash
npm install -g gemini-cli
mkdir -p .gemini && ln -sf .claude/.mcp.json .gemini/settings.json
gemini -y -m gemini-2.5-flash -p "Take a screenshot of https://example.com"
```

**Method 2: Scripts**
```bash
cd .claude/skills/mcp-management/scripts && npm install
npx tsx cli.ts list-tools  # Saves to assets/tools.json
npx tsx cli.ts call-tool memory create_entities '{"entities":[...]}'
```

**Method 3: mcp-manager Subagent**

See [references/gemini-cli-integration.md](references/gemini-cli-integration.md) for complete guide.

## Technical Details

See [references/mcp-protocol.md](references/mcp-protocol.md) for:
- JSON-RPC protocol details
- Message types and formats
- Error codes and handling
- Transport mechanisms (stdio, HTTP+SSE)
- Best practices

## Integration Strategy

### Execution Selection

Selection is capability-first. No provider gets semantic authority merely
because documentation exists for it:

1. Discover the MCP capabilities the current executor/runtime actually exposes.
2. Select the smallest suitable existing execution path for the bounded task.
3. Do not add routing logic, a registry, or a provider preference order.

Equally valid existing paths, chosen by what is actually exposed:

- **Host/native MCP capability**: use the MCP client the current executor
  already provides, when it exposes the needed tools.
- **Direct CLI scripts**: manual tool specification when you need specific
  tool/server control.
  - Execute: `npx tsx scripts/cli.ts call-tool <server> <tool> <args>`
- **Gemini CLI**: one example path, valid when that CLI is the exposed
  capability.
  - Check: `command -v gemini`
  - Execute: `gemini -y -m gemini-2.5-flash -p "<task>"`
- **mcp-manager subagent (or equivalent delegation)**: context-efficient
  delegation; keeps the main context clean.

### Integration with Agents

The `mcp-manager` agent uses this skill to:
- Check which MCP execution capability the current executor actually exposes
- Execute via `gemini` command if available
- Fallback to direct script execution
- Discover MCP capabilities without loading into main context
- Report results back to main agent

This keeps main agent context clean and enables efficient MCP integration.
