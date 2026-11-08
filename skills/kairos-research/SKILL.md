---
name: kairos-research
description: "Technology Scout & Upstream Research protocol. Scans project manifests, detects knowledge cutoff risks, validates live API documentation and official changelogs, preventing deprecated code generation."
---

# KAIROS Research: Upstream Reconnaissance & Anti-Cutoff Protocol

KAIROS strictly forbids autonomous coding agents from guessing external library APIs based solely on training memory.

## The Cardinal Rule: Research BEFORE Brainstorming
**Never brainstorm architectural designs, state machines, or protocol workarounds without first discovering what the modern framework release already provides natively.**
Brainstorming on stale assumptions results in building fragile, custom wheels for problems that modern updates already solved out-of-the-box (e.g. state synchronization, matchmaking, and reconnection tokens in modern Colyseus; async cookies in Next 15; Schema v2 in Pydantic).

## When to Invoke

* **Mode Alpha:** Disabled by default (UI tweaks and minor copy changes do not justify external doc scraping).
* **Mode Beta:** Run `kairos scout` before brainstorming to inspect local manifests and detect high-risk dependencies.
* **Mode Gamma (Mandatory):** Invoke `kairos_scout` to perform live documentation research and generate `research.md` BEFORE opening any brainstorming session or drafting `design.md`.

---

## CLI Command: `kairos scout`

Run the native stack reconnaissance scanner:
```bash
python3 scripts/kairos_cli.py scout
```

Options:
* `--all`: Display all detected dependencies across all manifests in the project.
* `--save-spec`: Automatically append or create `research.md` inside the active Delta Spec (`.kairos/changes/<active>/`).

---

## The Subagent Invocation (Mode Gamma)

When designing a feature that touches external libraries or modern SDKs, invoke the `kairos_scout` subagent:

```python
invoke_subagent(
    Role="Technology Scout & Research Scientist",
    TypeName="kairos_scout",
    Prompt="""
    Perform an anti-cutoff research investigation for the proposed change at .kairos/changes/<id>/proposal.md.
    1. Scan package.json / pyproject.toml / pubspec.yaml for libraries involved.
    2. Check official documentation, changelogs, and local type definitions for breaking changes.
    3. Produce .kairos/changes/<id>/research.md with verified method signatures and negative constraints.
    """
)
```

---

## Anti-Hallucination Checklist

Before approving a `design.md` or writing code:
1. [ ] Was the library version verified against local manifests (`package.json`, `pyproject.toml`)?
2. [ ] If the library underwent major breaking changes (e.g. Pydantic v2, Next 14/15, React 19, Tailwind v4, Google GenAI SDK), were modern signatures confirmed via live docs or type files?
3. [ ] Are forbidden legacy patterns documented in `research.md` or `design.md` under "Negative Directives"?
