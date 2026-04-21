# OpenClaw Hardening Finding: Cron WS Auth Asymmetry
**Date:** 2026-04-21 | **Source:** Marvin (Joerg's AI) — live evidence from running deployment

## Finding
`gateway.bind: lan` has split authentication for the WebSocket cron API:
- `cron list` (read) — works **without** a paired session. No auth required.
- `cron add` (write) — requires pairing.

**Impact:** Anyone on the LAN can enumerate all cron jobs including their full payloads (prompts, schedules, delivery targets) without authenticating. This is information disclosure of the agent's full automation schedule.

## Evidence
Deterministic. Tested repeatedly on a live machine with `gateway.bind: lan`. `cron list` returns full job list with no session token; `cron add` returns auth error without pairing.

## Fix
One of:
1. Switch `gateway.bind` from `lan` to `local` — restricts the gateway to localhost only, eliminates LAN exposure entirely.
2. Firewall port 18789 at the network level to trusted hosts only.
3. Apply session auth requirement to `cron list` (read) to match `cron add` (write) — closes the asymmetry while keeping LAN binding.

Option 1 is lowest risk for single-machine deployments. Option 3 is required if LAN accessibility is intentional.

## Classification
**Medium severity** — information disclosure. Not remote code execution, but a full automation schedule leak to any LAN-adjacent attacker. In a corporate network, this means any colleague can read your agent's cron payloads.
