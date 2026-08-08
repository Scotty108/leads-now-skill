# The bake-off is complete — `skills/leads-now/` is the shipping skill

`finding-leads/` is the SKILLIT-generated competitor. It is kept for the
benchmark record and the port tests, and it is **not shipped**:
`scripts/build-skill-zip.sh` packages `skills/leads-now/` only.

## Why it ended

Four rounds of head-to-head plus a universality run. Cross-pollination worked
in both directions and the two converged — final means **0.6939 (ours)** vs
**0.7149 (skillit)** under the corrected channel-weighted scoring, a gap inside
the run-to-run spread. Further rounds against the same roster were producing
diminishing returns; the marginal value moved to production use.

Shipping two competing skills is a maintenance burden and a confusing product,
so the best of both now lives in one.

## What was ported out of skillit before archiving

| Ported | Why |
|---|---|
| **ZIP5 gazetteer** (33,791 ZCTA centroids) | Placement precision 96% -> 100%. Every row our city matcher missed — military installations, boroughs, CDPs — has a ZIP5. A 3-digit prefix has a ~38 mile median extent, which is noise at a 15-mile ring. |
| **`source_rung`** | Records which escalation rung produced a row, so a repair knows what to retry — and because the rung is itself a quality signal. |
| **NUCC taxonomy code set** | Resolving a specialty to its code, and to its PARENT, which is the query that actually returns people. Now a healthcare vertical asset. |
| calibrated email tiers, `audit` refusal, domain-unlock hunt, employer-by-address join | Ported during rounds 1-4; see `bench/LEDGER.md`. |

## What was deliberately not ported

Its four separate scripts (`audit_list.py`, `email_pattern.py`, `geo_filter.py`,
`npi_query.py`). One file matters: some install paths carry only `SKILL.md` and
drop `scripts/` entirely, which is why the shipping skill embeds a working
fallback in its own body. Four scripts cannot do that.

Its ~700KB gazetteer was also ZIP5-only with no per-prefix extent, and the
extent is what lets `geo` plan registry queries that take a prefix rather than
a radius. The merged asset keeps both.
