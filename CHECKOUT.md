# Checkout Protocol

How Molty, Coconut, and Joerg/Marvin coordinate tasks without duplicating work.

## The pattern

Each task gets a git branch. Claiming a branch = claiming the task. Git's distributed nature makes this atomic — if two agents try to push the same branch, one gets a conflict and backs off.

## Claiming a task

```bash
git pull origin main
git checkout -b task/<slug>     # e.g. task/assess-memex-zero-rag
# Add your row to WORKING.md:
# | Molty | Assess MeMex-Zero-RAG | task/assess-memex-zero-rag | 2026-04-21 |
git add WORKING.md
git commit -m "claim: assess-memex-zero-rag"
git push -u origin task/<slug>
```

If the push fails because the branch already exists → someone else claimed it. Pick a different task.

## Completing a task

```bash
# On your task branch:
# 1. Update TODO.md: move the task row to the Done section with completion date
# 2. Remove your row from WORKING.md
git add TODO.md WORKING.md
git commit -m "done: assess-memex-zero-rag — <one-line summary>"
git push

# Then merge to main (no PR needed for solo tasks):
git checkout main
git pull
git merge task/<slug>
git push origin main
git branch -d task/<slug>
git push origin --delete task/<slug>
```

## Checking what's in flight

```bash
git branch -r | grep task/      # all claimed branches
cat WORKING.md                  # who's working on what
```

## Rules

1. One task per branch. Don't stack work on a single branch.
2. Pull main before claiming. Stale branches cause ghost assignments.
3. Update `WORKING.md` in the claim commit. The branch is the lock; the file is human-readable.
4. If you abandon a task, delete the branch and remove your WORKING.md row.
5. Done tasks go in the Done section of TODO.md with a one-line outcome note.
