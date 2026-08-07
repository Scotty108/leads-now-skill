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

## Round 4 — can the unlock hunt close the email gap without the error rate?
| 4 | 2026-08-07T01:40Z | gate | both | — | — | — | — | — | — | — | 18/18 core + 34/34 ports green |

**The challenge:** a prior Cowork run got 22 emails to our 4 by propagating org
patterns. Our own observed data shows ~12 of its 22 were built on the WRONG
format (flast at a first.last domain; dotted at a compact domain), plus it
emitted employer addresses for contractors its own notes flagged.

Target: beat 4 emails **with zero wrong-format addresses**. Every emitted
address must trace to a pattern observed ON that domain, and to a person whose
employment at that domain is verified.

| 4A | 2026-08-07T02:00Z | clamped | ours | 119 | 119 | 1 | 1.00 | 0 | 700 | 0.7933 | 5 emails (+1), **zero wrong-format**; 13 domains attempted, 3 unlocked |

### Round 4A: the unlock hunt works, and it corrected ME

**I was wrong in my own analysis.** I told the user a rival's
`flast@mcleodhealth.org` addresses were WRONG, based on ONE observed address
(`logan.doriety@`). A complete sweep found **9 personal addresses: 3
name-confirmed first.last AND 2 name-confirmed flast**, flast being the ~6-of-9
MAJORITY. The rival's shape was the majority and **still unsafe** — the domain
runs BOTH. My "wrong" was a partial-sweep negative, committed while explaining
partial-sweep negatives to someone else.

**Correct output for a mixed domain is ZERO addresses**, not a majority vote.
No propagation from one beats ~2/3 accuracy, far under any bounce ceiling.
14 McLeod roster members, 0 emitted.

**A real toolkit bug, now fixed.** `leadkit emails` returned
`pattern_confirmed` while silently discarding a competing observation on the
same domain. It now downgrades to `pattern_likely`, sets
`mixed_format_domain: true`, and names the rival — the same treatment ambiguous
surnames already got. Fixed in both the script and the SKILL.md fallback.

**A round-2 claim in our own reference is FALSE.** "Every McLeod
anesthesiologist has `mcLeod_physician_associates: false`" — the complete slice
(29 of 29, no truncation) is **8 TRUE, 21 FALSE**. The contractor guard alone
would NOT have blocked two emissions; only the mixed-format finding does. Two
guards that looked redundant were not — one was wrong.

**The bottleneck is discovery, not propagation.** 72 of 120 roster members sit
on five private anesthesia groups (Atlantic Coast 24, Tidelands 13, MedStream
13, Southeast 11, Providence 11) whose mail domains were never found — 32
hostnames DNS-probed, all NXDOMAIN or parked, every search transport dead under
the clamp.

**A live MX is not proof of identity:** two Providence candidates had working
mail and served a critic blog; beachanesthesia.com has working mail and a 404
web root.

Net: **5 emails, zero wrong-format** (vs the rival's ~10 real / ~12 fabricated).
The one gain came from `orthosc.org` — mail domain `.org`, website `.com`.

| 4A | 2026-08-07T02:20Z | clamped | skillit | 85 | 85 | 4 | 1.00 | 2 | 1177 | **0.8274** | 5 emails ALL first-party observed, 0 inferred; 50 withheld as contractor |

### Round 4B: contracting is the whole shape

**CMS PECOS `facility_name` queried by street address settled it.** All four
hospital employers contract anesthesia to four DIFFERENT groups:

| Facility | Who actually bills |
|---|---|
| Grand Strand | **Atlantic Coast Anesthesia Services PC — 71 of 71** |
| Conway | MedStream Anesthesia PLLC |
| Columbus Regional | Southeast Anesthesiology Consultants PLLC |
| Novant Brunswick | Providence Anesthesiology Associates PA |

**56 addresses harvested. 4 of 6 domains unlocked. 3 patterns confirmed. ZERO
applied.** 50 plausible addresses withheld. The contractor domains have no A
record and no MX — unreachable, not merely undiscovered. This explains the
email ceiling better than anything else in the benchmark.

It also WITHDREW round 3's inferred `derek.horstemeyer@hcahealthcare.com`.
Final: **5 emails, every one first-party observed, zero inferred.**

### TWO MORE CORRECTIONS TO MY OWN ANALYSIS

**Novant is UNSETTLED, not "compact".** I characterised it from 2 samples
(`jsmoreb@`, `mssaylor@`). Across **19 addresses / 17 people** two conventions
coexist and the split is **GEOGRAPHIC** — Bolivia sits in the Wilmington orbit
where the **dotted** form dominates, the opposite of my samples. Two samples
characterised nothing.

**A directory listing is not employment.** A well-sourced website case that 3
physicians were CRH employees was overridden by CMS — and one turned out to be
delisted from CRH entirely.

### PEDIATRIC COUNT: 1 -> at least 3

The GME faculty page paid in evidence, not email (8 faculty, 0 addresses):
**Desiree Aird** (Children's Hospital of Michigan peds fellowship) and **Andrew
Criser** (board certified Pediatric Anesthesiology), both placed at 809 82nd
Pkwy Myrtle Beach by CURRENT CMS enrollment — which also settles the round-3
Aird dispute: her NPPES address was stale.

The first answer (1) trusted a registry TAXONOMY. The second trusted a registry
ADDRESS. Both were fixed by the same source: a current federal filing.

---

## Universality cycle — the skill had to survive being pointed elsewhere

Not a scored round: no lead-finding runs. The user's requirement was that the
skill answer *"people like X within N of Y"* for **any** population, with Myrtle
Beach as one benchmark rather than the subject. Five invariants written first,
all red against the pre-cycle version.

### A pack nothing routes to is a deleted pack

The previous cycle moved the clinical detail into `vertical-healthcare.md` and
`SKILL.md` referenced it **zero times**. The specifics were not decluttered,
they were orphaned — the router could never load them back. `test_vertical_pack_
exists` had checked the file was on disk, which it was.

### Universality is a method, not a longer list

`sources.md` was "Where to look, by vertical" — a healthcare table and a B2B
table. That is a two-vertical skill. Rewritten as a derivation: classify the
population by **structure**, and the class says whether a roster exists at all.

| Class | Test | Enumerable |
|---|---|---|
| Licensed | prosecuted without one? | fully |
| Public payroll | taxpayer-funded salary? | yes |
| Entity principal | is the person the business? | via the filing |
| Credentialed / Association | verified letters / a trade body? | partial |
| Privately employed | none of the above | **no** |

The fork matters more than the sources: only an enumerable class has a
denominator. It also predicts the email ceiling — **public payroll is the
highest-yield class in any vertical, a licence register the lowest.** That
reframes round 2's academic-vs-community finding as an instance of a general
law rather than a fact about hospitals.

### 15 miles was answerable from a run already on disk

The territory was 15mi; every round swept 50. Those are not different searches —
15 is a subset — but a flat list forces a re-run. `leadkit bands` measures each
person from the centre and reports bands, so **one sweep answers every radius**:

```
786 NPI people, from Myrtle Beach
  within 15 mi  33    within 25 mi  42    within 50 mi  60
```

Two bugs surfaced only by running it on the real 786-row roster:

1. **`merge` dropped city/state/postal_code** — they were not in `FIELDS`, so
   the location never survived to be measured and `dist_mi` came out empty.
   That reads as "nobody has a distance", not as a broken pipeline.
2. **17 cities failed to place, and almost none were missing.** They were
   spelling variants: `MT PLEASANT` vs Mount Pleasant, `N CHARLESTON` vs North
   Charleston, `WINSTON SALEM` vs Winston-Salem. Each miss silently demoted a
   row to a postal-prefix centroid with a **~38 mile median extent** — tolerable
   at a 50mi ring, fatal at 15mi. Normalising abbreviations took city-accurate
   placement from **737 to 756 of 786**, with our gazetteer still half the size
   of skillit's ZIP5 file.

Skillit was worse: it died on the **centre**. `resolve "Mt Pleasant, SC"` →
`place not found`, a hard stop on step one of any run. Ported both ways; both
now band, and neither drifts (`Charleston` did not absorb into "Charleston
Heights"; `Lexington, KY` correctly resolves to Lexington-Fayette).

An unplaceable row keeps a **null** distance, never a zero — a zero sorts it to
the top and reads as the closest lead in the territory.

**32/32 green, both skills.**

---

## Universality PROOF run — FL roofing contractors, 25mi of Tampa

The previous cycle proved universality with unit tests and vocabulary ratios.
This one pointed the skill at a population it had never seen. Everything below
was found by the method being wrong in public first.

**865 active licensed roofing contractors within 25 miles of Tampa, using zero
web searches.** 9,760 statewide, from a file of 270,487.

### What held

Classification worked: Licensed (+ Entity principal) -> take the highest ->
enumerable -> a denominator exists. "Bulk file before lookup form" paid off
immediately: three hops from `myfloridalicense.com` reached a **48 MB CSV of
every licensee**, HTTP 200, no key, no CAPTCHA, no login.

### Search ran out, and the method survived it

WebSearch hit **200/200 on the first query of the run** — the same exhaustion
that produced 0 LinkedIn profiles in 8 of 14 rounds. The register was still
reachable by navigating from the root domain. `sources.md` Step 3 has been
reordered to put **navigate-the-body's-own-site at rung 1**, ahead of every
search-based rung, because search is a budget and navigation is not.

### The yield table was wrong, and the run proved it

It promised "a person and a phone". Across 270,487 rows x 22 columns this
register carries **no phone and no email at all** — 2 stray `@` cells, both
typos inside a name field. NPI publishes a phone; DBPR does not.

**Honest reachability from the register alone: 0 of 865.** Corrected to: count
the populated cells before promising a channel.

### Two silent bugs only a foreign vertical could surface

1. **merge collapsed 107 distinct people.** The key is name + org, and a
   register has no org, so it degenerated to name alone. `David Lee Carr` of
   St. Augustine and `David Lee Carr` of Brooksville — different licence
   numbers — became one row holding one man's address and the other's licence.
   A fabricated record, which is the one thing this skill exists to prevent.
   Fixed with a location fallback; **+113 people recovered, +15 in-ring**.

   The same fix repaired the opposite error: `PORT ST LUCIE` and `PORT SAINT
   LUCIE` at one postcode had split one person into two.

2. **Surname-first names stranded the suffix.** "AMBROSE, DEREK GABRIEL II"
   rendered as "Derek Gabriel Ii Ambrose". Registers publish one combined
   surname-first field; only org sources split first/last. Added `flip_name`.

### The scorer had the same disease as the skill

`score.py` weighted **`peds_signal` at 20%**, so a non-clinical run could not
exceed 0.80 however good it was. Renamed to `qualifier_signal` — "the trait the
user actually asked for, with a citation" — reading the old keys for
compatibility. Round 4 re-scores identically at 0.7933.

**36/36 green. FL run scores 0.46 — correctly low, because 0 of 865 are
reachable and that is the true state of a licence register.**
