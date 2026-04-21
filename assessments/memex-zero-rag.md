# MeMex-Zero-RAG Assessment
**Date:** 2026-04-21 | **Assessed by:** Molty

## What it is
Zero-RAG, LLM-agnostic personal knowledge base based on Karpathy's LLM Wiki pattern.
Knowledge *compiles* once into a structured wiki and compounds over time — not re-derived per query.
Git-native. No databases, no embeddings, no servers.

## Architecture
```
L1/        → Private session context (git-ignored): identity.md, rules.md, credentials.md
raw/       → Immutable source documents (LLM reads, never modifies)
wiki/      → LLM-maintained knowledge: sources/, entities/, concepts/, synthesis/, index.md, log.md, contradictions.md
outputs/   → Generated artifacts (reports, exports)
```

## MCP Server (production-ready, 519 lines)
Compatible with Claude Code, Hermes Agent, and any MCP client.
Tools: `wiki_search`, `wiki_read`, `wiki_list`, `wiki_query`, `wiki_ingest`, `wiki_lint`, `wiki_graph`, `wiki_stats`

Install: `pip install mcp` + add to `~/.claude/mcp.json`. Runnable today.

## Input sources supported
- PDF ingestion (pymupdf), web clipping (httpx+readability), voice capture (Whisper), batch API (50% cost)

## Anti-hallucination protocol
- Every claim must cite source. Unsourced = error, not warning.
- Conflicts go to `contradictions.md` — human decides truth, LLM never does.
- L1 credentials never committed (git-ignored by default).

## Mapping to our architecture
| MeMex | Our Design |
|-------|-----------|
| `L1/identity.md` | Per-session L1 context |
| `wiki/` | L2 compiled knowledge base |
| `raw/` | L1 raw input layer |
| MCP server | Agent query interface |
| `wiki_lint` | Health check for metacognition cron |
| `wiki_graph` export | Feeds Hermes-Studio knowledge graph visualization |

## Integration with Hermes-Studio
Hermes-Studio's knowledge graph panel almost certainly visualizes `wiki_graph` output.
Hermes Agent queries MeMex via MCP tools directly. The two are designed to work together.

## Gaps for multi-agent use
- **Per-chat isolation**: Single-user wiki, not multi-tenant. Gaps matter for trio coordination, not for Joerg's TrendAI single-user setup.
- **L1→L2 promotion with sensitivity labels**: Our spec described gating what gets promoted from per-chat L1 to shared L2. Not built in — would need a wrapper cron.
- **Concurrent write isolation**: Multiple agents writing to `wiki/` simultaneously needs worktree isolation (same pattern as trio-tasks).

## Verdict
**Deploy immediately for TrendAI.** Joerg is already using this — we just need to wire the MCP server into our Claude Code config and the knowledge graph starts feeding Hermes-Studio. For multi-agent trio use, the isolation gaps need a consolidation cron layer on top.

## One-line deploy for Claude Code
```json
{ "mcpServers": { "memex": { "command": "python", "args": ["/path/to/MeMex-Zero-RAG/mcp/server.py"], "cwd": "/path/to/your/wiki" } } }
```
