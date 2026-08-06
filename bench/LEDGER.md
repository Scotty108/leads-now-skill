# Bake-off ledger

One row per round. Append, never rewrite — the history is the point.

| Round | UTC | Cond | Skill | People | Reachable | Peds signal | Provenance | Subagents | Wall (s) | Score | Ported this round |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 2026-08-06 | — | both | — | — | — | — | — | — | — | baseline: 18/18 invariants green, no runs yet |
| 1 | 2026-08-06T21:40Z | gate | both | — | — | — | — | — | — | — | 18/18 green — eligible to run |
| 1 | 2026-08-06T21:45Z | ports | both | — | — | — | — | — | — | — | port frontier written TDD-first. Pre-port RED: ours lacks calibrated-email-tiers + unsourced-row-gate; skillit lacks SKILL.md-fallback + qualify-branch. Evidence: bench/preport_evidence.json. Correction: skillit DOES have surface lanes — earlier claim it lacked them was wrong. |
| 1A | 2026-08-06T21:52Z | clamped | ours | 60 | 59 | 0 | 1.00 | 3 | 640 | 0.7245 | 3 emails (pattern_confirmed, cmc-sc.com); 11 blocked sources named |
| 1A | 2026-08-06T21:52Z | clamped | skillit | 72 | 72 | 0 | 1.00 | 0 | 526 | **0.7725** | 0 emails; 5 blocked sources; won on coverage |
| 1B | 2026-08-06T22:15Z | open | ours | 84 | 84 | 2 | 1.00 | 1 | 1179 | **0.7940** | browser unlocked 23 people; FOUND a real peds anesthesiologist at 25mi |
| 1B | 2026-08-06T22:30Z | open | skillit | 72 | 72 | 0 | 1.00 | 0 | 805 | 0.7632 | exhaustive enrichment sweep: 11 sources tried, boundary established |

**ROUND 1 COMPLETE — 4/4 runs.** Ranking: ours/open 0.7940 > skillit/clamped 0.7725 > skillit/open 0.7632 > ours/clamped 0.7245.

CONFOUND: session WebSearch budget exhausted (200/200) before both runs — Condition A is a valid test of registry sourcing and a CRIPPLED test of enrichment. Both skills logged it as a top blocker.

## Per-channel coverage (the real scoreboard)
| Round | Population | Practice ph | Dept ph | Direct | Email | LinkedIn (found) | LI search | Peds signal |
|---|---|---|---|---|---|---|---|---|
| 1A | 131 | 131 | 0 | 0 | 3 | 0 | 0 | 0 |
| 1B (ours) | 84 | 65 | **19** | 0 | 3 | 0 | **84** | **2** |
| 1B (skillit) | 72 | 72 | 0 | 0 | 3 | 0 | 72 | 0 |

### Round 1 findings that changed the answer

**The registry zero was wrong.** Round 1A reported 0 pediatric anesthesiologists
from NPI. Round 1B found **Michelle D. Lee, MD — a registered pediatric
anesthesiologist 25.4 mi out at McLeod Loris**. Her NPI record carries no
pediatric taxonomy; the subspecialty is published only on her hospital's own
directory, a JS shell to plain fetch. Parent-taxonomy querying is necessary and
NOT sufficient. Ported to both, with a test.

**Rung 3 beat rung 4 twice.** Grand Strand's provider data sat in an embedded
`physicianData` JSON in server HTML the clamped run never parsed past `<title>`;
McLeod's sat behind the site's own public Algolia index. Only Tidelands' 403
genuinely needed a browser. The browser's real contribution was DISCOVERING
where to look, not rendering.

**Literature is the wrong instrument here.** OpenAlex + Europe PMC over 60
community anesthesiologists: 0 usable peds signals, 51 of 60 with no scholarly
footprint at all. Ported to both, with a test.

**The refusal fired on a genuinely published address.** `mbuvahfj@gmail.com`
appears verbatim in PMID 26185936 — discarded because the paper's affiliation is
Detroit while the person practices in SC, and it is a personal gmail. Preserved
in `records/refused_emails.json` so the finding is not lost. Five other
tempting false positives were also discarded; counting one would have
manufactured the set's only publication-derived STRONG.

**Channel movement 1A -> 1B:** department phones 0 -> 19, LinkedIn search URLs
0 -> 84, peds signal 0 -> 2. **Work email did not move: 3.**

### THE BOUNDARY (round 1B, skillit — 11 sources tried exhaustively)

**69 of 72 have no affiliation-locked paper, trial or grant anywhere.** Every
academic channel is capped at the 3 people who publish, and a thorough sweep
reached exactly those 3. The ceiling is a property of the population, not the
tooling.

| Source tried | Scope | Yield |
|---|---|---|
| OpenAlex | 72 names | **0 — HTTP 429, now metered** |
| PubMed E-utilities | 2630 IDs, 210 author-matched, 183 emails present | 0 |
| PubMed affiliation-restricted | 17 ring [ad] terms | 0 |
| Europe PMC search | 129 records, 120 emails | 0 (all collisions) |
| Europe PMC fullTextXML | 4 locked PMIDs | **0 — 404 on all, incl. the OA one** |
| **NCBI efetch db=pmc** | 4 locked + 6 near-miss | **2** |
| ClinicalTrials.gov v2 | 72 names + 8 ring cities | 0 |
| NIH RePORTER v2 | 72 PIs + 8 cities | 0 |
| Hospital department pages | 8 org sites | **0 department lines** |
| email_pattern learn+apply | 5 observed @hcahealthcare.com | 1 |

**Corrections ported (each with a test that failed pre-port):**
- OpenAlex is metered — documented as "free, no key", returns 429 with $0 budget
- NCBI efetch db=pmc beats Europe PMC fullTextXML (404 on all 4, incl. OA)
- Affiliation lock is NOT sufficient: "Patel D" @ Grand Strand Myrtle Beach
  passed it perfectly and is *Dveet* Patel, not roster member *Deeran* Patel.
  PubMed indexes by initial; require a full-forename match.
- Department phone lines mostly do not exist — my own claim that they were
  "the realistic win" was FALSIFIED at 0/8 org sites.

**Work email ceiling: ~3/72 (4%) from free public sources on a community
clinical roster.** Phone is the deliverable channel; email is a bonus on the
academic minority.

## Round 2 — do the corrections move anything?
| 2 | 2026-08-06T22:40Z | gate | both | — | — | — | — | — | — | — | 18/18 core + 14/14 ports green; eligible |

| 2A | 2026-08-06T22:55Z | clamped | ours | 68 | 68 | 1 | 1.00 | 0 | 730 | 0.7690 | +9 people, +1 email, +1 peds, +16 dept phones vs R1 |
| 2A | 2026-08-06T22:55Z | clamped | skillit | 77 | 77 | 1 | 1.00 | 0 | 746 | **0.7918** | +5 people, +3 emails, +1 peds, +12 dept phones vs R1 |

### Round 2A: the corrections worked, and the browser turned out to be optional

**NOT a dry round.** Every channel moved on both skills.

| Channel | R1 clamped | R2 clamped (ours / skillit) |
|---|---|---|
| People | 60 / 72 | 68 / 77 |
| Emails | 3 / 0 | 1 / 3 |
| Department phones | 0 / 0 | **16 / 12** |
| Peds signal | 0 / 0 | **1 / 1** |

**The browser was not needed for any of it.** Both runs reproduced round 1B's
rung-3 wins with `curl` alone — Grand Strand's `physicianData` from profile
server HTML (299/299) and McLeod's Algolia credentials (`app JUNR3SUCF2`,
public search-only key) read out of `/search-physician-finder/` server HTML.
**Michelle D. Lee MD, the pediatric anesthesiologist, was reached clamped.**
Only Tidelands (403) still requires rung 4.

**The full-forename rule did enormous work:** 147 of 151 surname+geo records
rejected in one run, 48 in the other. It killed "Loris Thomas" (a place name
matching as a forename) and a cross-channel collision that would have reported
"E J Collins" as pediatrician C. Michael Collins — **a false pediatric hit**.

**Three corrections ported (each with a test that failed pre-port):**
- Department phones live in rung-3 PAYLOADS, not on fetched pages. This
  AMENDS my own round-1B claim that they "mostly do not exist" — true for page
  fetching, false for structured records. Conway is the honest control: 304
  pages parsed, still only a switchboard.
- Hosted search indexes cap pagination silently. Algolia reports `nbHits: 805`
  but `nbPages: 1` at `hitsPerPage=100` — a blind browse returns 100 of 805 and
  looks complete. Same class as NPI `skip=1000`.
- **Employment status gates pattern inference.** Three agreeing
  `@hcahealthcare.com` addresses would have made `first.last` pattern_confirmed
  for five more people; their directory records set `hcaEmployee: false` —
  Teamhealth contractors, not HCA staff. Five plausible addresses withheld.

**Email ceiling holds at 3.** 69 of 72 still have no publication anywhere.
