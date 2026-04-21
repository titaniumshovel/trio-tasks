# Hermes-Studio Assessment
**Date:** 2026-04-21 | **Assessed by:** Molty | **Repo:** JPeetz/Hermes-Studio v1.18.1

## What it is
Full-featured web UI for Hermes Agent. React 19 + TanStack + Vite 7 frontend, Node.js BFF server, Python PTY helper for terminal sessions. Built by Joerg because Hermes Agent had no native web UI — now that Hermes has one, this is a more capable alternative.

## Key capability mapping

| Feature | What it does | Maps to our design |
|---------|-------------|-------------------|
| **Multi-agent Crews** | Named crews up to 8 agents, dispatched by task or broadcast to all, live SSE activity feed | Nerve plexus layer |
| **Profile-Scoped Workspaces** | Each crew member isolated to `~/.hermes/profiles/<name>/` | Per-agent L1 isolation |
| **Visual DAG Workflow Builder** | Node-edge pipeline with topological execution, live per-node status | Orchestration layer |
| **Jobs/Cron** | Full CRUD: schedule, prompt, skills, repeat config, pause/resume/run, output viewer | Metacognition + consolidation cron |
| **Memory Browser** | Browse/search/edit `~/.hermes/` memory files | Agent memory admin |
| **Approvals** | approve / approve-and-commit / approve-and-pr / reject / revise | Human-in-the-loop governance |
| **MCP Config** | Edit `~/.hermes/config.yaml` via UI, triggers live reload | Hot-wire new tools without restart |
| **Terminal** | Full PTY via xterm.js, persistent sessions, SSE streaming | Admin shell access |
| **Cost tracking** | Per-agent and per-crew token + cost metering | Usage visibility |

## Concurrent write isolation — direct answer to Coconut's question

**Profile-scoped workspaces solve agent file collision** — each crew member works in `~/.hermes/profiles/<name>/`, so no Hermes-managed files collide between agents.

**MeMex wiki writes are NOT solved by Studio** — if all agents point to the same `wiki/` directory, Studio provides no isolation there. The DAG runner serializes tasks within a workflow, but independent crew sessions can write concurrently.

**The fix**: L1→L2 consolidation cron pattern we already designed. Each agent writes to their own L1 (per-profile wiki branch), a scheduled cron promotes to the shared L2 wiki. Studio's Jobs/Cron screen is the UI for configuring that cron. The architecture fits — it just requires the consolidation layer on top of MeMex.

## Approvals — confirmed manual-only
Review actions (approve, approve-and-commit, approve-and-pr, approve-and-merge, reject, revise) are UI actions, not API-callable hooks. Governance-layer blocking requires the Hermes Agent plugin `pre_tool_call → {"action": "block"}` — separate from Studio's approval UI.

## Runnable today
```bash
git clone https://github.com/JPeetz/Hermes-Studio
cd Hermes-Studio
pnpm install && pnpm dev
```
Requires Hermes Agent running locally. Docker + docker-compose.yml available for deployment.

## Security model
- Password auth with rate limiting (5 req/min)
- Path traversal prevention on file API (sandboxed to workspace root)
- Ignored dirs: `node_modules`, `.git`, `.next`, `.turbo`, `.cache`, `__pycache__`, `.venv`, `dist`
- Dockerfile available for containerized deployment
- SECURITY.md with responsible disclosure policy

## Verdict
**Deploy alongside Hermes Agent + MeMex. This is the admin interface.** Joerg built the thing we kept saying was missing from OpenClaw. Crews → nerve plexus. DAG builder → orchestration layer. Jobs/cron → metacognition and consolidation crons. MCP config hot-reload → skills management without restarts.

**The remaining gap**: MeMex concurrent write isolation. Studio solves per-agent workspace isolation; wiki-level isolation requires the L1→L2 consolidation cron we designed. Studio's Jobs screen is where you configure that cron. Full stack: Hermes Agent + Hermes-Studio + MeMex-Zero-RAG + consolidation cron.
