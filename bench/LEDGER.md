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

| 2B | 2026-08-06T23:20Z | open | ours | 160 | 97 | **79** | 1.00 | 2 | 3060 | **0.9500** | peds channel OPENED: 2 -> 79 signals; 1342 profiles read |

### Round 2B: the index was a pointer, not the record

**Best score of the bake-off: 0.9500.** Round 1 read McLeod's search index and
reported 2 pediatric signals. Round 2 went ONE HOP PAST it — every index record
carries a `scheduling_url` to `/physician/<slug>/`, and those pages publish
Board Certification, Medical School, Residency and Fellowship **to a plain
curl**. 1,342 profiles read across 5 systems.

| Channel | R1 open | R2 open |
|---|---|---|
| People | 84 | **160** |
| Peds signal | 2 | **79** (39 STRONG + 40 MODERATE) |
| Department phones | 19 | **33** |
| Emails | 3 | **0 from 1,342 pages** |

**The honest pediatric answer, both numbers:** 76 in-radius providers carry a
published pediatric signal, but in ANAESTHESIA the ring contains exactly
**one** — Michelle D. Lee, MD, now evidenced as "Board Certification:
Anesthesiology; Pediatric Anesthesiology, Residency 2007 Children's Hospital
Colorado". A facet count over the full 805-record index returns exactly 1.

**Silence is not absence, and it marks the best calls.** Tidelands publishes NO
training block for ANY of its 12 anesthesiologists (while publishing one for
other specialties — verified). Grand Strand publishes no board-cert row at all
(0/299). Conway has no such field. Those NONE_FOUNDs mean the directory cannot
show a fellowship — which makes those 12 the HIGHEST-value calls in the set,
because everyone else's absence has been checked and theirs has not.

**Guards fired:** OrthoSC's nav string "Pediatric Orthopedic Care" graded all
33 of its providers pediatric until stripped; 18 Conway "children" hits were
personal-life bio mentions. Also caught: the round-1 roster of 84 contains 5
duplicate people — it is really ~79 distinct.

**Ported (each with a test that failed pre-port):** open the profile not just
the index; silence-is-not-absence with the high-value inversion; strip page
chrome before matching.

| 2B | 2026-08-06T23:45Z | open | skillit | 108 | 108 | 89 | 1.00 | 0 | 3300 | **0.9500** | 1708 profiles; FALSIFIED 3 of my own corrections |

**ROUND 2 COMPLETE — 4/4 runs.** ours/open 0.9500 = skillit/open 0.9500 (TIE),
skillit/clamped 0.7918, ours/clamped 0.7690.

### Round 2B (skillit) falsified three claims I had ported as fact

A fuller sweep — 1,708 profile records against the earlier 1,342 — overturned
three confident negatives written into the reference last round:

| Claimed | Measured |
|---|---|
| Tidelands publishes NO training block for ANY of its 12 anesthesiologists | Publishes for **11 of 12** |
| Conway has no board-certification field | Publishes on **258 of 303** |
| Zero clinician emails across 1,342 profiles | McLeod publishes **15 first-party addresses** |

**THE META-LESSON: state the denominator with every negative.** Round 2B read
262 of McLeod's 805 records and reported its zeros as properties of the world.
They were properties of the sample. A negative from a partial sweep is a
hypothesis, not a finding.

**Truncation is recursive.** The documented fix for the pagination cap is itself
capped: partitioning by specialty returned 785/805 because Family Medicine (161)
and Primary Care (132) each silently hit the same 100 limit. Practice partition
804. Only gender + a-z reached 805/805.

**A wrong payload key reads exactly like absence.** Grand Strand yielded zero
peds until keyed on `providerSpecialties`/`providerLocations` rather than
`specialties`/`practiceLocations`.

**What held under the fuller sweep:** exactly ONE pediatric anesthesiologist in
the ring, reproduced independently by both skills from the record itself. And
the email discipline held as coverage improved — McLeod's 15 observed addresses
establish `first.last@mcleodhealth.org` on 15 samples and were applied to ZERO
people, because every McLeod anesthesiologist is `mcLeod_physician_associates:
false`, a contracted group on another mail domain. A previously derived address
was also WITHDRAWN when efetch showed the paper publishes a different author's.


## Round 3 — the first DRY round
| 3A | 2026-08-07T00:10Z | clamped | skillit | 77 | 77 | 1 | 1.00 | 0 | 780 | — | **DRY: 0 new people/emails/peds/phones.** 46 training blocks filled. |

**marginal_vs_round2 = {people: 0, emails: 0, peds: 0}.** Per LOOP.md this is a
dry round: no new reachable contact through any channel after genuinely trying
four new source classes.

### But the round found the best source in the benchmark

The **American Board of Anesthesiology Diplomate Directory** — an open,
un-captcha'd JSON API at `directoryreactapi.theaba.org`, reached by climbing
into the React bundle's `main.js`. `ProgramType 519` IS Pediatric
Anesthesiology, the exact field rounds 1-2 could not reach. It filled **46
board-certification blocks**, including one Tidelands anesthesiologist sourced
entirely from outside Tidelands (which still 403s).

The gain is evidential, not volumetric: 48 NONE_FOUNDs moved from
*unpublishable* to *checked-and-absent at the body that grants the certificate*.

### The sharpest rejection yet

ABA publishes a **mailing address**, not a practice location. Two brand-new,
entirely plausible pediatric anesthesiologists appeared 1.5 miles from centre —
Desiree Aird MD and John Gantomasso DO. NPI and Doximity independently placed
them in **Tucson AZ** and **Macon GA**. Both withheld. The ring still holds
exactly **1** (Michelle D. Lee MD, now double-sourced with certificate dates
2026-01-01 to 2030-12-31).

The full-forename lock again did heavy work: 94 raw ABA hits -> 85 forename
matches -> 47 accepted; 38 withheld including **Michelle Pae Lee (Fullerton CA)**
— a near-miss on the single person the whole benchmark turns on.

### Three classes structurally closed (a browser does not rescue them)

- **State medical boards**: reCAPTCHA v2. The skill refuses to defeat a CAPTCHA,
  so this zero survives into the OPEN condition unchanged. NCMB bulk roster is
  $150; SC bulk verification is a login wall.
- **ASA / SPA**: no public member directory exists at all. Only paid list rental.
- **Residency & fellowship pages**: circular for discovery — indexed BY PROGRAM,
  which is the field being filled. 0 of 77 names on the MUSC residency page.
- **Doximity is inverted**: publishes training where place fails to corroborate,
  gates it where place does. Useful for rejection, not filling.

**New highest-value calls:** the 15 genuine unknowns (of 29 unmatched — 12 are
NPI trainees, 1 PA-C, 1 CRNA, none ABA-eligible), replacing round 2's Tidelands 12.

| 3A | 2026-08-07T00:25Z | clamped | ours | 119 | 119 | 1 | 1.00 | 1 | 999 | — | **+52 people, +99 training blocks** via CMS PECOS; email dry 4th round |

### Round 3A (ours): the source nobody listed

**CMS Doctors and Clinicians National Downloadable File** (`mj5m-pzi6`, 3.39M
rows, no key) — Medicare PECOS enrollment, an official filing carrying
`med_sch`, `grd_yr`, `pri_spec`, `facility_name` and a practice phone.

One geography query: **68 -> 120 people**, **0 -> 99 training blocks**,
dept phones **16 -> 37**, NPIs resolved for all 6 previously NPI-less rows.

**It named all 12 Tidelands anesthesiologists with medical school and grad year
while tidelandshealth.org was still 403ing.** Three rounds of blocked-directory
workarounds beaten by going to a different filing entirely. When a directory
blocks you, look for the regulator's filing.

### A CROSS-RUN CONTRADICTION — unresolved, being tested

- **skillit/clamped R3:** found an OPEN un-captcha'd ABA JSON API at
  `directoryreactapi.theaba.org` by climbing into the React bundle's `main.js`;
  `ProgramType 519` = Pediatric Anesthesiology; 46 certification blocks filled.
- **ours/clamped R3:** concluded "theaba.org has NO public diplomate lookup at
  all."

Both cannot be true. Ours did not climb into the bundle — which makes its zero
a partial-sweep negative, exactly the failure round 2B taught. round3__ours__open
is testing it directly. **This is the denominator lesson recurring on itself.**

### Peds is exactly 1, confirmed by three independent structures
- CMS DAC has **no Pediatric Anesthesiology value** in its vocabulary
- SC LLR's dropdown has 27 pediatric codes, **no anesthesia intersection**
- NPI `207LP2900X` sweep returns **0 across all five target cities**

### Absence proved with a positive control
Healthgrades recorded checked-and-absent for 12 people only after a control
profile returned a 1994 UPMC `FELLOW` row — proving the field exists, renders,
and is genuinely empty. Without a control, "blank" and "parsed wrong" are
indistinguishable.

**EMAIL: dry for the 4th consecutive round.** 0 marginal, 4 total, across 12
source classes, 2 skills, ~1,700 profiles and a 3.39M-row federal file.

| 3B | 2026-08-07T00:45Z | open | ours | 120 | 119 | 4 | 1.00 | 0 | 934 | — | ABA contradiction RESOLVED against our own clamped run |

### Round 3B: two runs disagreed and BOTH were wrong

I verified against the NPI registry directly rather than picking a side:

| Person | skillit claimed | ours claimed | NPI PRACTICE address |
|---|---|---|---|
| Desiree Aird MD | Tucson AZ | inside Myrtle Beach ring | **Greenville SC** |
| John Gantomasso DO | Macon GA | inside Myrtle Beach ring | **New Orleans / Lafayette LA** |

**A SCOPE ERROR SURVIVED THREE ROUNDS AND TWELVE RUNS.** The brief said map to
"Myrtle Beach **or Greenville**". Every run enumerated only the Myrtle Beach
ring, then reported "0 -> Greenville" — a zero produced by never searching
there. Aird proves it wrong: a verified Greenville pediatric anesthesiologist,
invisible to twelve consecutive runs. round3__skillit__open is now sweeping
Greenville properly.

### The ABA contradiction, resolved AGAINST our own run

ours/clamped said "theaba.org has no public diplomate lookup at all." WRONG —
`directoryreactapi.theaba.org` answers plain curl with HTTP 200. Our run probed
guessable hostnames, got 404s, and published a rung-2 negative as a property of
the world, never climbing to rung 3 where the API ships in the React bundle's
main.js. **It cost 3 of the 4 pediatric anesthesiologists.** The denominator
lesson recurring on itself one round later.

### WHAT THE BROWSER IS WORTH — the cleanest measurement in the benchmark

Of 108 certification blocks filled: **101 by both**, **6 by ABA (plain fetch)
only**, **1 by ABMS (browser) only**.

**Browser-alone marginal: 0 people, 0 emails, 0 peds, 0 phones, 1 cert block.**

ABMS is genuinely browser-only (403 curl / 200 Playwright, no challenge shown
or solved) — real, and worth exactly one record.

| 3B | 2026-08-07T01:15Z | open | skillit | 476 | 465 | 25 | 1.00 | 1 | 1637 | **0.9500** | GREENVILLE swept: overturns the headline conclusion |

**ROUND 3 COMPLETE — 4/4 runs.** skillit/open 0.9500 > ours/open 0.8355 >
skillit/clamped 0.7907 > ours/clamped 0.7834.

## THE HEADLINE CONCLUSION WAS WRONG — corrected

Four rounds concluded "work email tops out near 4%; phone is the deliverable."
That was true of a COMMUNITY roster and false as a general claim. Same
specialty, same state, a ring around an academic centre instead of a resort:

| | Myrtle Beach | Greenville |
|---|---|---|
| In-ring providers | 120 | **476** |
| NPI peds taxonomy | 0 | **20** |
| Evidenced peds anesthesiologists | 1 | **25** |
| **First-party published emails** | **4** | **78** |

The ceiling was a property of the **population**, not of clinical data. It broke
through a **medical-school faculty directory** — not the literature, which was
falsified again with a stated denominator (0 emails from 81 of 426 checked).

**Classify the population before predicting the ceiling.**

## The case that needs BOTH new sources

**Sara Lathem Walls MD** — ABA peds-certified, practises at Prisma Greenville.
Her NPPES LOCATION still says *Nashville TN* on a record untouched since 2018,
so the registry puts her OUTSIDE the ring; her in-ring NPPES address is MAILING
only; and Prisma's own directory omits her from pediatrics. Found ONLY via
current CMS Medicare enrollment, qualified ONLY by the ABA.

The exact inverse of the Blomeley rejection (in-ring mailing, out-of-ring
practice). **Neither case is reachable without both the federal filing and the
credentialing body.**

## A second silent wrong-key zero
The GUID fix is necessary but NOT sufficient: with the CORRECT state GUID the
ABA advanced search still returned `[]` at HTTP 200, because the API treats an
empty string as a LITERAL filter value. `main.js` shows the client sends JSON
`null` — with nulls the identical query returned **860**. Fourth truncation
event also caught (NC and GA parent sweeps each exactly 1000; all three peds
sweeps under the cap, so peds enumeration is complete and two paths agree).

## Recorded, not hidden
- 4 peds-certified anesthesiologists at Mission Health Asheville, **53.5 mi** —
  3.5 outside a hard ring. Soft radius takes in-ring 12 -> 16. Stated, not decided.
- Process defect: two agents both wrote `build.py` to shared scratch and one
  silently replaced the other, caught only when a rebuild printed 23 rows
  instead of 476. Namespace files in shared working directories.
