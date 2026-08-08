# Verifying the skill against the official Agent Skills spec

*Last updated 2026-08-08.*

Every frontmatter rule in `bench/test_invariants.py` was originally **inferred
from trial and error** — uploads that failed on claude.ai told us what was
illegal. The spec is now published, so guessing is no longer necessary.

- **Spec:** <https://agentskills.io/specification>
  (`anthropics/skills` → `spec/agent-skills-spec.md` is now a pointer to it)
- **Reference validator:** `skills-ref`, from
  <https://github.com/agentskills/agentskills> → `skills-ref/`

## Running the validator

It needs **Python 3.11+**, which the system `python3` here is not (3.9.6), so
install it with `uv`:

```bash
git clone --depth 1 --filter=blob:none --sparse \
    https://github.com/agentskills/agentskills.git
cd agentskills && git sparse-checkout set skills-ref
uv tool install ./skills-ref

skills-ref validate skills/leads-now
```

`bench/test_invariants.py` runs it automatically when it is on `PATH` (or at
`~/.local/bin/skills-ref`) and **skips rather than fails** when it is absent, so
the suite still runs on a machine without Python 3.11.

## Current status — both skills pass

```
Valid skill: skills/leads-now
Valid skill: skill-bakeoff/finding-leads
```

## The limits, and where we sit

| Field | Spec limit | `leads-now` |
|---|---|---|
| `name` | ≤64 chars, `[a-z0-9-]`, no leading/trailing/double hyphen, **must match the directory name** | `leads-now`, 9 — ok |
| `description` | ≤1024 chars | 664 — ok |
| `compatibility` | ≤500 chars | 336 — ok |
| `license` | free text | `MIT` |

Legal optional fields are exactly `license`, `compatibility`, `metadata`,
`allowed-tools`. Anything else is a hard error on upload — which is what the
hand-rolled `ALLOWED_FM` check has been guarding all along, and it turns out to
have been right.

## The one soft guideline we exceed, deliberately

The spec recommends `SKILL.md` stay **under 500 lines and ~5000 tokens**,
because the whole body loads the moment the skill activates — its size is a tax
on every run.

We sit at **409 lines / ~5134 tokens**: inside the line budget, ~3% over the
token guidance.

The overage is the **embedded stdlib fallback** — roughly 1,700 tokens of
Python in the body. That is deliberate: some install paths carry only `SKILL.md`
and drop `scripts/` entirely, and without the fallback the skill is inert
there. `test_spec_soft_limits` therefore warns at a wider bound (6500) rather
than the recommendation, so real drift is still caught while the known trade-off
does not fail the gate.

**If the body needs to shrink**, cut prose to `references/` before touching the
fallback — progressive disclosure is exactly what the reference directory is
for, and the fallback is the thing that cannot be moved.
