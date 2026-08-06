# Phase 1 decomposition — kept so a later repair traces against the same ground

## 0. What the runtime has

Target surfaces differ, so the skill is built to the intersection:

| Capability | Code CLI | Cowork | Chat apps |
|---|---|---|---|
| Agent-side web fetch / search | yes | yes | yes |
| Local code execution | yes | yes | yes (sandboxed) |
| **Outbound network from inside code** | yes | varies | **no** |
| Browser automation | sometimes | no | no |
| Subagents | yes | varies | no |

**Architectural consequence, and the reason the scripts look the way they do:** every script is
offline and standard-library only, and all fetching happens through the agent. A script that called
the network would work while being built and fail silently for most users. Browser automation is
capability-detected and optional; nothing depends on it.

Sources confirmed reachable and free during Phase 1:

- NPI Registry API — verified live, no key, JSON.
- NUCC taxonomy code set — downloadable, shipped as an asset.
- Census gazetteer — downloadable, shipped as an asset.
- Organization websites — reachable but frequently unreadable; see the ladder.

## 1. The job to be done

Not "a list of names." The outcome is **a contact list the user can act on tomorrow morning
without personally re-checking every row**, where the count is the real population size rather
than whatever one source happened to surface.

Chained up a level: the recruiter is not hiring a list, she is hiring **placements**, and she
currently spends about 40% of her week hand-assembling the list. The two properties that decide
whether the list is worth anything are **recall on the long tail** and **not burning her sending
domain or her credibility on invented rows**.

## 2. The practitioner

Two, and the skill serves both:

- A healthcare sourcing recruiter who triangulates the provider registry, state licence lookups,
  and hospital directories, and knows the registry's specialty field is self-reported.
- An outbound data engineer who builds lists from company sites, infers email formats from observed
  addresses, and manages bounce rate as a hard operating constraint.

## 3. The outcome contract

A CSV shaped like `assets/output_template.csv`, plus a brief. Two properties separate a great run
from an acceptable one:

1. **The denominator is stated** — population, filtered, delivered, and what was unreachable.
2. **Every row is traceable and every address is tiered** — a derived address is never presented
   as a found one.

## 4. Micro-job sequence

| # | Step | Mechanical? |
|---|---|---|
| 1 | Route to the branch from what the user brought | No — judgement |
| 2 | Restate the target as a filter with explicit bounds | No |
| 3 | Choose the frame: registry census vs company-first | No — the key fork |
| 4 | Resolve geography to centre, states, ZIP3 prefixes | **Yes** — `geo_filter.py resolve` |
| 5 | Resolve specialty to search strings plus parent | **Yes** — `npi_query.py taxonomy` |
| 6 | Plan queries, page them, detect saturation and ceiling | **Yes** — `npi_query.py plan/parse` |
| 7 | Filter to radius, dedupe to nearest location | **Yes** — `geo_filter.py filter` |
| 8 | Read each organization's site, climbing the access ladder | No — judgement per site |
| 9 | Collect observed addresses; infer format | **Yes** — `email_pattern.py learn` |
| 10 | Apply format, tier each address, hold the weak ones | **Yes** — `email_pattern.py apply` |
| 11 | Hygiene and bounce pricing | **Yes** — `email_pattern.py hygiene` |
| 12 | Gate the deliverable, compute coverage | **Yes** — `audit_list.py` |
| 13 | Write brief naming denominator, blocked orgs, unknowns | No |

Everything marked mechanical became a script, because each is arithmetic, parsing, or a rule that
must produce the identical answer every run. Everything else was researched in Phase 2.

## 5. Where the defects concentrated

Ranked by how much damage they do:

1. Guessed emails presented as found ones.
2. No denominator, so a thin list is indistinguishable from a small population.
3. Subspecialty-only registry query, which returns near-zero and looks like an answer.
4. Radius treated as a city name, dropping everything across the state line.
5. Silently skipped blocked sources.
6. Paging and ceiling handling, where a saturated query reads as a total.

Each maps to exactly one mechanism in the shipped package.

## 6. Assumptions made while building this

Logged because a wrong one here is invisible in the output and expensive later.

1. **Scripts must never touch the network.** Assumed the thinnest target surface has no outbound
   access from inside sandboxed code. Everything is built to that floor, which costs the richer
   surfaces nothing.
2. **Bundling geography beats looking it up.** ZIP and place centroids ship as a compressed asset
   rather than being fetched, so radius work is deterministic and works offline. Costs about
   700 KB.
3. **The bounce rates per tier are planning estimates**, taken from a leave-one-out measurement
   over observed name-and-address pairs, not from sending. They are used only to rank and to warn,
   never reported as a prediction about a specific address.
4. **The `confirmed` / `probable` / `unconfirmed` vocabulary is this skill's invention.** No
   industry standard exists. It is enforced by the audit script so it stays consistent.
5. **A 50-mile default radius** is assumed when a user names a place with no distance.
6. **A person is placed at their nearest practice location.** Registry records list several; the
   nearest is assumed to be the relevant one, which is right for a geographic search and wrong for
   someone whose main site is elsewhere. Flagged by keeping `location_kind` on the row.
7. **The taxonomy asset is a point-in-time copy** of a code set revised twice a year. New codes
   appear before this file knows about them; the registry itself remains the authority.
8. **Browser automation is optional and absent by default.** Assumed most runs have rungs 1-3 only.
9. **Cross-surface portability outranks depth on any single surface.** Where the two conflicted,
   portability won — which is why no platform, model, or tool name appears in the body.
