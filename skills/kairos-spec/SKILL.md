---
name: kairos-spec
description: "Drafts and validates Delta Specifications. Manages proposal.md, specs.md, and tasks.md in .kairos/changes/, and spawns the zero-context kairos_critic subagent for adversarial design critique in Gamma mode."
---

# KAIROS Spec: Delta Specifications & Cognitive Critique

KAIROS treats specifications as executable contracts rather than loose documentation.

## Invocation

```text
/kairos:spec <feature_name>
```

## Structure of a Delta Spec

In Mode Beta and Gamma, run `python3 scripts/kairos_cli.py spec <feature_name>`. This creates:
* `.kairos/changes/<id>/proposal.md`: Context, in-scope requirements, and explicit non-goals.
* `.kairos/changes/<id>/specs.md`: Behavioral deltas categorized strictly into **Added**, **Modified**, and **Removed** requirements, plus system invariants.
* `.kairos/changes/<id>/design.md`: Technical architecture, schema models, and error matrix.
* `.kairos/changes/<id>/tasks.md`: Atomic checklist for TDD execution.

## The Cognitive Critique (Mode Gamma)

When operating in Mode Gamma, invoke the subagent `kairos_critic`:
```python
# Pass only the path to specs.md and relevant code files
invoke_subagent(
    Role="Architecture Critic",
    TypeName="kairos_critic",
    Prompt="Review the specification at .kairos/changes/<id>/specs.md with zero context. Find unstated assumptions, missing failure modes, and architectural gaps."
)
```

Incorporate the critic's findings into `specs.md` before starting implementation.
