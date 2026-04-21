# Checkout Protocol

How Molty, Coconut, and Joerg/Marvin coordinate tasks without duplicating work.

## Why worktrees, not branch checkouts

Branch switching (`git checkout`) causes file conflicts when multiple agents share a working directory or operate concurrently. Git worktrees give each task its **own directory** — no checkout needed, no conflicts. The main clone stays on `main` and is never disturbed.

## Claiming a task

```bash
# 1. From your main clone of the repo:
git pull origin main

# 2. Create a worktree for your task (new directory, task branch):
git worktree add ../trio-tasks-<slug> task/<slug>
# e.g. git worktree add ../trio-tasks-openclaw task/assess-openclaw-hardening

# 3. Work in the new directory:
cd ../trio-tasks-<slug>

# 4. Claim it — update WORKING.md and push:
# Add row: | Molty 🦎 | Assess OpenClaw Hardening | task/assess-openclaw-hardening | 2026-04-21 |
git add WORKING.md
git commit -m "claim: assess-openclaw-hardening"
git push -u origin task/<slug>
```

If the push fails (branch already exists) → task is claimed by someone else. Remove the worktree and pick another task:
```bash
cd .. && git worktree remove trio-tasks-<slug>
```

## Completing a task

```bash
# Inside your worktree directory:
# 1. Update TODO.md main clone: move task to Done section with outcome note
# 2. Remove your row from WORKING.md
git add TODO.md WORKING.md
git commit -m "done: assess-openclaw-hardening — <one-line summary>"
git push

# Merge to main from your main clone:
cd ../trio-tasks          # back to main clone
git pull origin main
git merge task/<slug>
git push origin main

# Clean up:
git worktree remove ../trio-tasks-<slug>
git branch -d task/<slug>
git push origin --delete task/<slug>
```

## Checking what's in flight

```bash
git worktree list                # all active worktrees (your local view)
git branch -r | grep task/       # all claimed branches (global view)
cat WORKING.md                   # human-readable who's doing what
```

## Rules

1. One worktree per task. Never stack multiple tasks in one worktree.
2. Pull main before claiming. Stale base causes unnecessary merge conflicts.
3. WORKING.md update goes in the claim commit — that's the visible signal.
4. If you abandon a task: delete the worktree, remove your WORKING.md row, delete the remote branch.
5. Done tasks go in the Done section of TODO.md with a one-line outcome note before cleanup.
