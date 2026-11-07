---
name: kairos-sync
description: "Promotes verified delta specs to canonical living documentation, cleans up isolated worktrees, and detects specification drift across the codebase."
---

# KAIROS Sync: Living Specs & Drift Detection

Sync completes the development lifecycle, ensuring that documentation remains synchronized with production code.

## Invocation

```text
/kairos:ship
/kairos:sync
/kairos:drift
```

## Procedures

### 1. Promoting Delta Specs to Living Docs (`/kairos:ship`)
When the Judge issues a **READY** verdict:
1. Promote the change:
   ```bash
   python3 scripts/kairos_cli.py archive <change_id>
   ```
   This moves `specs.md` to `.kairos/specs/<feature>.md`, updating the repository's single source of truth.
2. Clean up worktree:
   ```bash
   python3 scripts/kairos_cli.py worktree remove <task_name>
   ```
3. Merge branch or prepare clean Pull Request.

### 2. Specification Drift Detection (`/kairos:drift`)
Run periodically to detect divergence between living specs in `.kairos/specs/` and active source code. Ensures that future manual edits do not rot the architectural documentation.
