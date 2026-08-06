# The bake-off loop

A test-driven, cross-pollinating comparison between the two lead skills. Each
round measures both on the same task, finds what one does better, ports it to
the other, and locks the improvement in with a test so it can never regress.

## The two skills

| | Path | Built by |
|---|---|---|
| **ours** | `skill/leads-now/` | this session, portability-first |
| **skillit** | `skill-bakeoff/finding-leads/` | the SKILLIT skill-builder |

## The task

> Find anesthesiology providers — especially pediatric anesthesiologists or
> people with pediatric experience — within 50 miles of Myrtle Beach, then
> identify whether they should map to Myrtle Beach or Greenville, and return
> contact details / LinkedIn if possible. Even past hospital experience was
> useful, so it did not have to be only people currently working at a specific
> hospital.

Two conditions, run for both skills — four runs per round:

| Condition | Tools allowed |
|---|---|
| **A — clamped** | Registry + HTTP fetch only. No browser. |
| **B — open** | Adds Playwright / Claude in Chrome for blocked sources. |

Condition A is the honest floor: it is what a Claude apps or Cowork user gets.
Condition B measures what a browser actually buys.

## One round

**1. Gate.** `python3 bench/test_invariants.py` must be green before any run.
A skill that fails an invariant is not eligible to compete — fix it first.

**2. Run.** Four runs, each in its own subagent, each logging to
`bench/runs/<UTC>__<skill>__<condition>/`:

- `log.jsonl` — one line per step: `{ts, step, detail, elapsed_s}`
- `result.csv` — the leads
- `meta.json` — `{skill, condition, subagents, wall_clock_s, tool_calls}`

**3. Score.** `python3 bench/score.py bench/runs/<dir>` — never by eye.

**4. Diff and port.** For every metric where one skill wins, port the mechanism
to the other. Both skills improve every round; this is not elimination.

**5. Lock it in.** Every ported mechanism gets a test in `test_invariants.py`
*before* the port is called done. That test is what stops the next round from
regressing it.

**6. Append** one row to `bench/LEDGER.md`, then start the next round.

## Scoring

Deliverability is weighted above volume on purpose — a big list with guessed
addresses is worth less than a small verified one.

| Metric | Weight | Definition |
|---|---|---|
| Verified people in radius | 25% | Distinct, address inside 50mi, sourced |
| Reachable | 25% | Has a phone OR an email above `pattern_likely` |
| Pediatric signal | 20% | Graded STRONG/MODERATE with a citation |
| Provenance completeness | 15% | % of populated fields carrying a source |
| Honest gaps | 10% | Blocked orgs named; truncation declared |
| Cost | 5% | Wall clock, subagents, tool calls (lower better) |

**Disqualifying, regardless of score:**
- Any address emitted with no known-good sample for its domain
- A total reported from a truncated query without saying so
- A per-person claim with no source URL

## Known state entering round 1

Both at 18/18 invariants. Deltas already identified:

**Ours → port to skillit:** four-lane surface detection; SKILL.md-only embedded
fallback; QUALIFY branch (OpenAlex affiliation history for *past* experience);
smaller gazetteer (307K vs 688K, with per-prefix extent).

**Skillit → port to ours:** calibrated email accuracy tiers (0 obs 36% / 1 obs
68% / 2 unanimous 91%) with a 2% bounce ceiling gate; `audit_list.py` refusing
to pass unsourced rows; the Algolia endpoint discovery that beat a browser on
McLeod; employer resolution by address join (83% org recovery).

**Open in both:** neither has run the Myrtle Beach ↔ Greenville territory
mapping. Neither has resolved LinkedIn (nor should it automate LinkedIn —
surface the profile URL for a human, do not scrape it).

## Rules for the loop

- **Never edit a skill without adding the test first.** TDD, not vibes.
- **Never delete a losing mechanism** until its replacement passes the test.
- **Log the number, not the impression.** "72 providers, 0 with peds taxonomy"
  beats "worked well".
- **Stop a round early** if the gate is red; fixing an invariant outranks
  running a comparison.
- **A tie is a real result.** Record it and move on rather than manufacturing a
  winner.


## Termination: find the boundary, do not assume it

Three rounds is the floor, not the goal. **Keep looping until marginal
enrichment per round reaches zero** — a round that adds no new reachable
contact through any channel, on either skill, after genuinely trying a new
source. Two consecutive dry rounds means the boundary is real.

The deliverable is a defensible answer to: *what fraction of a clinical
population can be fully contacted from free public sources, and where exactly
does that stop?* That number decides whether the product thesis holds. Nobody
currently knows it — Clay and Apollo will not publish it, and round 1 only
established a floor.

### Per-channel coverage is the scoreboard

Track every round, per channel, as `n / population`:

| Channel | Round 1 | Ceiling hypothesis |
|---|---|---|
| Practice phone | 131/131 | Solved — NPI publishes it |
| Department phone | 0/131 | Reachable; hospital service-line pages |
| Direct dial | 0/131 | Probably near-zero from public sources |
| Work email | 3/131 | **The open question** |
| LinkedIn URL (public page) | 0/131 | Partial; never scraped |
| LinkedIn search URL | 0/131 | Trivially 131/131 |
| Peds signal | 0/131 | Needs OpenAlex/ORCID, untried |

A channel is **exhausted** only when a round tried a *new* source for it and
added nothing. "We did not get any" is not evidence of a ceiling; "we tried
Europe PMC affiliation-locked and it yielded 4 more" is.

### Sources not yet tried — work down this list

Each round must attempt at least one untried source and record the yield:

1. OpenAlex corresponding-author, affiliation-locked
2. Europe PMC full-text (exposes addresses abstracts drop)
3. NIH RePORTER and ClinicalTrials.gov contacts
4. Hospital department / service-line pages for department phones
5. State medical board licensee records
6. Residency and fellowship program pages, alumni lists
7. Society member directories (ASA, AAP)
8. Doximity and Healthgrades as corroboration only
9. Press releases and newsroom for name + email format
10. Practice websites for the ~2 of 12 domains that resolve

### Honest stopping

When a channel is exhausted, say so with the evidence and stop spending on it.
**Do not manufacture coverage to hit a target.** If work email tops out at 12%
of a community-anesthesiology population, that is the finding, and it is more
valuable than a padded list — it tells the user the product needs a paid
waterfall for that field, or that phone is the channel.

The loop ends when every channel is either saturated or has a named, evidenced
reason it cannot go further.
