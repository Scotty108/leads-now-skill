# Getting an actual contact channel

Measured, round 1, 131 clinicians across two independent skill runs:

| Channel | Coverage |
|---|---|
| Practice phone | 131 / 131 |
| **Work email** | **3 / 131** |
| **LinkedIn** | **0 / 131** |

Phones look solved and are not. Emails look broken and are mostly a sourcing
gap. This file is how to close both without guessing and without automating
anything you should not.

## Phones: say which kind of number it is

Every one of those 131 numbers came from the NPI registry, which publishes the
**practice location phone** — a front desk or a switchboard. A switchboard is not a direct dial and not the
same as reaching the person, and reporting "131 reachable" implies something
the data does not support.

Label every number:

| `phone_type` | What it is | Use |
|---|---|---|
| `direct` | A direct dial that rings the person | Best |
| `department` | Rings their unit or service line | Good |
| `practice` | Front desk / switchboard (NPI default) | Weak |
| `answering_service` | After-hours or third-party | Poor |

**Default an NPI phone to `practice`.** Only upgrade it when a source says
otherwise — a department page, a hospital directory listing a service line, a
bio with a direct extension.

Report the split, never the total alone:

```
59 with a phone: 0 direct, 6 department, 53 practice
```

Department numbers are the realistic win here. Hospital "Contact us" and
service-line pages routinely publish the anesthesiology department line, which
is materially better than the main switchboard and costs one fetch per org.

## Emails: papers publish what hospitals do not

Health systems almost never publish clinician addresses. **Academic publishing
does** — corresponding-author addresses are printed on the paper, and for
physicians in teaching hospitals the coverage is real.

The trap is name collision. A PubMed search for "Michael Alvarado" returns
every Michael Alvarado alive. Round 1 produced 8 such hits and they were
correctly thrown away rather than used — the query has to be **affiliation-
locked** before an address means anything.

**Affiliation-locked means:** the paper's author affiliation must match the
person's known organization, city, or health system before you accept the
address as theirs. Name + specialty is not enough. Name + affiliation is.

Order of attack:

1. **OpenAlex** (`api.openalex.org` — now metered, see corrections below). Search the author, then
   confirm `last_known_institution` or the affiliation on the specific work
   matches their practice. OpenAlex also gives affiliation history with dates,
   which feeds `qualify.md`.
2. **Europe PMC** (`ebi.ac.uk/europepmc/webservices/rest`, free, no key).
   Full-text search exposes corresponding-author emails that abstract-only
   sources drop.
3. **PubMed / NCBI E-utilities** (free; a key only raises rate limits).

Label anything found this way `first_party_published` when the paper itself
carries it — it was published by the author, not inferred. Record the DOI or
PMID as the source. An address from a 2009 paper is real but stale; note the
year, because people change institutions.

If affiliation cannot be confirmed, **discard the address.** A plausible
address for the wrong person is worse than a blank.


## What a confidence label is worth

Measured by leave-one-out against known-good addresses: an inferred address is
right about **36%** of the time from zero observations, **68%** from one, and
**91%** from two that agree. Providers throttle senders above roughly a **2%**
bounce rate.

| Observations | Label | Accuracy | Implied bounce | Bulk-sendable |
|---|---|---|---|---|
| 0 | *(nothing emitted)* | 36% | 64% | Never |
| 1 | `pattern_likely` | 68% | 32% | No |
| 2+ agreeing | `pattern_confirmed` | 91% | 9% | **No** |

Read the last column carefully. **No derived tier clears a 2% bounce ceiling —
not even `pattern_confirmed`.** 91% accurate means 9 bounces per 100, which is
4x over the line where providers start throttling.

So an inferred address is fine for a human to try one at a time, and is not
safe to load into a bulk sequencer. Only `first_party_published` and
`previously_delivered` clear the ceiling. Say this when you hand over a list —
a recruiter who bulk-mails 59 `pattern_confirmed` addresses will burn their
sending domain and will reasonably blame the tool that produced them.

## Other free sources worth the fetch

- **Department and "contact us" pages** — service-line emails and phones
- **Press releases and newsroom** — named contacts, and they leak the org's
  address format, which unlocks the whole domain via `leadkit emails`
- **Residency and fellowship program pages** — program coordinators publish
  addresses, and the alumni lists feed qualification
- **Conference programs and speaker pages** — current, public, and often list
  an address for correspondence
- **Grant and trial registries** (NIH RePORTER, ClinicalTrials.gov) — the
  contact for a trial is frequently the clinician themselves

## LinkedIn: hand over a search, never a scrape

Do not automate LinkedIn. Its terms forbid automated collection, enforcement is
aggressive, and the account that gets restricted is the user's, not the tool's.
No exceptions, no browser, no "just one page".

What is both legitimate and useful: emit a **precise search URL** the user can
click. It costs nothing, needs no network call, and puts a human in the loop
where the terms require one.

```
https://www.linkedin.com/search/results/people/?keywords=<name>%20<org>
```

Put it in a `linkedin_search_url` column — never `linkedin_url`, because you
have not verified a profile exists. If a public bio, conference page or
practice site links their profile, record that as `linkedin_url` with the page
you found it on as the source. Found on a public page is fine; harvested from
LinkedIn is not.

## What to report

Give the channel breakdown, not a single reachability number:

```
59 people
  phone     59  (0 direct, 6 department, 53 practice switchboard)
  email      3  (3 pattern_confirmed, 0 first_party_published)
  linkedin   0 verified, 59 search URLs provided
```

A reader can act on that. "59 reachable" invites them to think they have 59
people's contact details, which is not what happened.


## Corrections from measurement (round 1B)

Four things in this file were wrong or incomplete. Measured against 72
community anesthesiologists.

### OpenAlex is metered now — do not lead with it

Documented here as "free, no key". It is not. Measured: **HTTP 429,
"Insufficient budget. This request costs $0.001 but you only have $0
remaining", retryAfter 6268s.** Zero of 72 queries were served, even with a
polite user-agent and a mailto. Treat OpenAlex as best-effort and never as the
primary path.

### Use NCBI efetch, not Europe PMC full text

Europe PMC's `fullTextXML` **404'd on all four affiliation-locked PMIDs**,
including the one flagged open-access. `NCBI efetch db=pmc` served every one,
and both real published addresses came from it.

```
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=<PMCID>
```

Order: PubMed esearch to find the paper → **efetch db=pmc** for the full text,
where the corresponding-author address actually lives. Abstract-level records
drop it.

### An affiliation lock is not enough — compare full forenames

"Patel D" publishing from **Grand Strand Health, Myrtle Beach** passed the
affiliation lock perfectly. It is **Dveet** Patel. The roster member is
**Deeran** Patel. Same surname, same initial, same employer, same city —
different person.

PubMed indexes authors by initial, so the initial is not a discriminator.
**Require the full first name to match** before accepting any address, and
where the paper only gives an initial, treat the match as unconfirmed and
discard it. A near-miss that survives an affiliation lock is more dangerous
than an obvious mismatch, because it looks verified.

### Department phone lines mostly do not exist

This file predicted department numbers were "the realistic win". **Falsified.**
Measured across 8 organization sites — Conway Medical Center, Grand Strand,
McLeod Seacoast, Columbus Regional, OrthoSC, Tidelands, Novant Brunswick — the
yield was **zero department lines**. Hospitals rarely publish a department
number at all — they publish a facility switchboard and nothing else.

Keep labelling `phone_type`; the labels are still the honest thing to report.
Drop the expectation that fetching org pages will upgrade a `practice` number
to a `department` one. In one browser-enabled run 19 of 84 department lines
were recovered, so it is not impossible — it is just not reliable, and it is
not worth a fetch per org on a cold roster.

### Where the boundary actually is

**69 of 72 have no affiliation-locked paper, trial or grant anywhere.** Every
academic channel — OpenAlex, Europe PMC, PubMed, ClinicalTrials.gov, NIH
RePORTER — is capped at the 3 people who publish, and a thorough sweep reached
exactly those 3. That is the ceiling, and it is a property of the population,
not of the tooling.

For a community clinical roster, plan on **phone as the deliverable channel**
and treat email as a bonus on the small academic minority.


## Round 2 corrections — including one to the section above

### Department phones: I had this backwards

The correction above says department lines "mostly do not exist", measured at
0 across 8 organization sites. That is true for **page fetching** and false for
**structured payloads**. Two clamped runs pulled **16 and 12 department lines**
from the same organizations — the anesthesia group's own number sits inside the
directory record, not on the rendered page.

So: fetching the page is the wrong read. Parsing the payload is the right one.
Conway Medical Center is the honest control — 304 provider pages parsed, still
only a switchboard, because that org genuinely publishes nothing else.

### Hosted search indexes cap pagination silently

A second silent-truncation class, the same shape as the NPI `skip=1000` ceiling.

McLeod's Algolia index reports `nbHits: 805` but `nbPages: 1` at
`hitsPerPage=100`, because of `paginationLimitedTo`. A blind browse returns
**100 of 805 and looks complete** — no error, no flag, and the response even
tells you the true total in a field you did not read.

**Always compare the reported total against what you actually received.** When
they disagree, partition the query (by specialty, by location, by letter)
instead of paging. Round 2 used specialty-scoped queries for exactly this
reason.

### An org's email pattern applies to its employees, not its building

The sharpest refusal so far. Three agreeing `@hcahealthcare.com` addresses
would have made `first.last` **pattern_confirmed** for five more anesthesiologists
at Grand Strand. Their own directory record set `hcaEmployee: false` — they are
Teamhealth contractors working in an HCA facility, not HCA staff.

**Zero addresses were emitted for them — five plausible addresses withheld.** A confirmed pattern belongs to an
employer's mail domain; someone who merely works in the building is on a
different domain entirely, and the inferred address would bounce while looking
perfectly reasonable.

A confirmed pattern does not apply to a contractor. Check employment
status before applying a pattern. Directory payloads often
carry it (`hcaEmployee`, `employmentType`, "locum", "contractor", staffing-agency
addresses). Where the status is unknown, the pattern is unconfirmed for that
person — say so and withhold.

### What round 2 proved about the browser

Both clamped runs reproduced the two rung-3 wins **with `curl` alone**: Grand
Strand's `physicianData` parsed from profile server HTML (299/299), and
McLeod's Algolia credentials (`app JUNR3SUCF2`, public search-only key) read
straight out of `/search-physician-finder/` server HTML.

That includes the pediatric finding. **Michelle D. Lee, MD was reached without
a browser.** The only residual browser-only source is Tidelands, which 403s.

The lesson stands and strengthens: climb the ladder in order, because rung 3
keeps beating rung 4.


## Round 2B — the subspecialty channel, opened

### The index is a pointer, not the record

Round 1 read McLeod's search index and reported **2** pediatric signals across
84 people. Round 2 went **one hop past** it and found **79** across 160.

The index carries no training fields at all. But every record has a
`scheduling_url` pointing at `/physician/<slug>/`, and *those* pages publish
**Board Certification, Medical School, Residency and Fellowship** — to a plain
`curl`, no browser. Round 1 never opened one.

**Open the profile.** A search index exists to help you find the page; it is
not the page. Read 1,342 profiles this way across five systems and the
subspecialty question stopped being unanswerable.

### The honest answer to the pediatric question

76 in-radius providers carry a published pediatric signal. But in **anaesthesia
specifically the ring contains exactly one**: Michelle D. Lee, MD — now
evidenced as *"Board Certification: Anesthesiology; Pediatric Anesthesiology,
Residency 2007 Children's Hospital Colorado"*, not merely a specialty string. A
facet count over the full 805-record index returns exactly 1.

Report both numbers. "76 pediatric providers" and "1 pediatric
anesthesiologist" are answers to different questions and a recruiter needs the
second.

### Silence is not absence — and it marks your best calls

A `NONE_FOUND` must be explained structurally or it misleads. Measured:

- **Tidelands publishes no training block for any of its 12 anesthesiologists**
  — while publishing one for other specialties. Verified, not assumed.
- **Grand Strand publishes no board-certification row at all** (0 of 299).
- **Conway has no board-certification field.**

Those `NONE_FOUND`s mean *the directory cannot show a fellowship*, not that the
person lacks one. Which inverts the usual reading: **those 12 Tidelands
anesthesiologists are the highest-value calls in the set**, precisely because
the record is silent. Everyone else's absence has been checked; theirs has not.

Say which kind of `NONE_FOUND` you are reporting — checked-and-absent, or
unpublishable.

### Strip page chrome before matching

Page chrome matches exactly like content. Measured: OrthoSC's navigation string
*"Pediatric Orthopedic Care"* graded **all 33** of its providers pediatric until
it was stripped, and 18 Conway hits for "children" were personal-life mentions
in bios ("father of three").

**Match inside the record**, never across the whole page. Scope to the profile
block, drop nav, footer and sidebars first, and require the term in a training,
certification or specialty field rather than anywhere in the HTML.

### Department phone directories do exist

Amending twice-corrected guidance once more: Conway publishes a full
`/phone-directory/` HTML table including **Anesthesia 843-347-8288 and
843-347-8352**, plus PACU and OR-scheduling lines. McLeod publishes anesthesia
practice lines; Tidelands publishes 843-652-1190.

Department phones went 0 → 12/16 → **33 of 160**. Look for a phone-directory
page by name; it is a different artifact from a provider profile.

### Email: still zero, now from 1,342 pages

**Not one clinician address across 1,342 profiles.** Combined with the academic
sweep — 69 of 72 with no publication anywhere — the email ceiling on a
community clinical roster is real and it is low. Phone is the deliverable.


## Round 2B was wrong — three negatives falsified by a fuller sweep

This file confidently asserted three zeros. A larger sweep (1,708 profile
records against the earlier 1,342) falsified **all three**:

| Claimed here | Measured on a fuller sweep |
|---|---|
| "Tidelands publishes NO training block for ANY of its 12 anesthesiologists" | Publishes training for **11 of 12**. Only one is genuinely unpublishable. |
| "Conway has no board-certification field" | Publishes board certification on **258 of 303** profiles. |
| "Zero clinician addresses across 1,342 profiles" | McLeod publishes **15 first-party clinician emails**. |

### State the denominator with every negative

That is the lesson, and it is the most important rule in this file.

Round 2B read **262 of McLeod's 805** records and 443 Tidelands profiles, then
reported its zeros as properties of the world. They were properties of the
sample. **Never write "zero" without the denominator you actually searched** —
"0 emails" is a claim about reality; "0 emails across 262 of 805 records" is a
claim about your sweep, and only the second one is true.

A negative from a partial sweep is a hypothesis, not a finding. Report it as
`checked N of M`, and treat any zero where `N < M` as provisional.

### A partition can itself truncate — recursively truncated caps

The documented workaround for a pagination cap is itself capped. Partitioning
McLeod's index by specialty returned **785 of 805**, because two facets —
Family Medicine (161) and Primary Care (132) — each silently hit the same
100-record limit. A practice partition got 804. Only a gender + a–z sweep
reached **805 of 805**.

**Verify the partition sums to the reported total.** If it does not, the
partition is truncating too, and you need a finer key. The cap does not
announce itself at any level.

### Verify payload keys before trusting a zero

Grand Strand's embedded payload returned **zero** pediatric signals until it was
keyed on `providerSpecialties` / `providerLocations` instead of `specialties` /
`practiceLocations`. Reading the wrong key returns an empty list that is
indistinguishable from a genuine absence.

Before recording a zero from a structured payload, dump one full record and
confirm the schema — that the field name you are reading actually exists.
A wrong key returns empty and silently reads as absence.

### What still holds

- Exactly **one** pediatric anesthesiologist in the ring, reproduced
  independently by both skills from the record itself.
- The email pattern discipline held even as coverage improved: McLeod's 15
  observed addresses establish `first.last@mcleodhealth.org` on 15 samples, and
  it was applied to **zero** people — every McLeod anesthesiologist has
  `mcLeod_physician_associates: false`, a contracted group on a different mail
  domain. A 15-observation pattern is still the wrong pattern for a contractor.
- A previously derived address was **withdrawn** on better evidence: efetch
  showed the source paper publishes a different author's address entirely.


## Round 3: the certifying body, and three dead ends named

### The ABA Diplomate Directory is the best source in this benchmark

The American Board of Anesthesiology runs an **open, un-captcha'd JSON API**.
It was reached by climbing the ladder into the React bundle: `theaba.org/directory`
→ `directoryreact.theaba.org` → `main.js` → the API base and endpoint shapes,
shipped in the client code.

```
GET  directoryreactapi.theaba.org/lookups/getCertifications
GET  directoryreactapi.theaba.org/searchResults/basic?FirstName=&LastName=
POST directoryreactapi.theaba.org/searchResults/advanced
       {FirstName, LastName, City, StateId, ABAId, ProgramType}
GET  directoryreactapi.theaba.org/doctorRecord/getDoctorRecords?ABAId=<digits>
```

**`ProgramType 519` is Pediatric Anesthesiology** — the exact subspecialty field
rounds 1 and 2 could not reach. It filled **46 board-certification blocks** on
people no hospital directory publishes, including one Tidelands anesthesiologist
sourced entirely from outside Tidelands, which still 403s.

Strip the dash from the ABA ID; the dashed form 400s. The advanced search
returned exactly **1000** for one query — the same silent ceiling as NPI
`skip=1000`, so treat parent-specialty counts as floors.

For any regulated profession, **go to the body that grants the credential.**
It is the only source that can turn an unpublishable blank into a checked fact.

### A mailing address is not a practice location

The sharpest rejection so far. ABA publishes the diplomate's **mailing
address**, and it produced two brand-new, entirely plausible pediatric
anesthesiologists 1.5 miles from the ring centre. NPI and Doximity
independently placed them in **Tucson AZ** and **Macon GA**.

Both withheld. The ring still holds exactly one.

An address field is a practice location only when the source says so. Registry
addresses, certifying-body addresses and directory addresses answer different
questions, and a certifying body has no reason to know where you work today.

### Three source classes are structurally closed

Closed by structure, not difficulty — **a browser does not rescue any of them**,
so do not spend a rung-4 budget here:

- **State medical boards** (SC LLR, NC Medical Board) are reCAPTCHA v2 gated.
  This skill does not defeat a CAPTCHA, so the zero survives into the open
  condition unchanged. NCMB's bulk roster is a $150 product; SC's bulk
  verification is a login wall.
- **ASA and SPA publish no member directory at all** — not gated, absent. The
  only member-data product is paid mailing-list rental.
- **Residency and fellowship pages are circular for discovery.** They are
  indexed *by program*, and the program is the field you are trying to fill. 0
  of 77 roster names appeared on the MUSC anesthesia residency page.

**Doximity is inverted:** it publishes training exactly where place fails to
corroborate, and gates it behind "Join to view" precisely where place does
corroborate. Useful for rejection, not for filling.

### What a dry round looks like

Round 3 added **0 new people, 0 emails, 0 pediatric hits, 0 department phones**.
The gain was entirely evidential: 48 `NONE_FOUND`s moved from *unpublishable*
to *checked-and-absent at the body that grants the certificate*.

That is a real result. The remaining 29 unmatched are structurally explained —
12 are NPI trainees (not board-eligible), 1 PA-C and 1 CRNA (not ABA-eligible),
and 15 are genuine unknowns. **Those 15 are now the highest-value calls**,
replacing round 2's Tidelands twelve.


## Round 3 clamped: the source nobody listed

### CMS Doctors and Clinicians National Downloadable File

The highest-yield source in the entire benchmark, and it was on no list. Medicare
**PECOS enrollment** — an official filing, 3.39M rows, no key, no CAPTCHA.

```
POST https://data.cms.gov/data-api/v1/dataset/mj5m-pzi6/data
     (filter by NPI, facility_name, or city+state+pri_spec)
```

Every enrolled clinician carries `med_sch`, `grd_yr`, `pri_spec`,
`sec_spec_1..4`, `facility_name` and a practice phone.

One geography query added **52 net-new in-ring providers** (68 → 120), filled
**99 training blocks from zero**, resolved NPIs for all 6 previously NPI-less
rows, and took department lines 16 → 37.

**It named all 12 Tidelands anesthesiologists — with medical school and
graduation year — while tidelandshealth.org was still returning 403.** Three
rounds of blocked-directory workarounds were beaten by going to a different
filing entirely.

The general rule: **when a directory blocks you, look for the regulator's
filing.** Anyone who bills Medicare is enrolled, and enrollment is public. It
outranks a marketing page on provenance and cannot 403 you.

### Prove absence with a positive control

Healthgrades was recorded as *checked-and-absent* for 12 people only after a
**control profile** (`dr-edward-gologorsky-2fywb`) returned a 1994 UPMC
`FELLOW` row — proving the field exists, renders to a plain fetch, and is
genuinely empty for the twelve.

Without a control, "the field was blank" and "I parsed it wrong" are
indistinguishable. That is precisely how round 2B produced three false
negatives.

**Before recording a structural zero, find one record where the field is
populated.** If you cannot, you have not established absence — you have
established that you did not find it.

### Peds confirmed at exactly 1 by three independent structures

Not a sampling result. Three sources agree for different reasons:

- CMS DAC has **no Pediatric Anesthesiology value at all** in its specialty
  vocabulary
- SC LLR's dropdown carries 27 pediatric codes with **no anesthesia
  intersection**
- An NPI `207LP2900X` taxonomy sweep returns **0 across all five target cities**

When independent vocabularies agree a category is empty, the answer is the
category, not the search.

### Email is dry for the fourth consecutive round

0 marginal, 4 total. Four rounds, twelve source classes, two skills, ~1,700
profiles and a 3.39M-row federal file. **The ceiling is real: phone is the
deliverable channel for a community clinical roster.**


## Round 3 open: two runs disagreed, and both were wrong

### Settle a location on the registry practice address

Two runs made **opposite** errors about the same two people, and only a direct
registry check settled it.

| Person | Run A claimed | Run B claimed | NPI PRACTICE address |
|---|---|---|---|
| Desiree Aird MD | Tucson AZ (out of scope) | inside the Myrtle Beach ring | **Greenville SC** |
| John Gantomasso DO | Macon GA (out of scope) | inside the Myrtle Beach ring | **New Orleans / Lafayette LA** |

Neither was right about either. Aird is a genuine South Carolina pediatric
anesthesiologist — in the *other* territory. Gantomasso is in Louisiana.

**A location claim is settled only by the authoritative registry's PRACTICE
address.** Not a mailing address, not a certifying body's address, and never
another run's assertion. When two sources disagree about where someone works,
go to the registry and adjudicate it rather than averaging or picking.

### Enumerate every territory the ask names

A scope error that survived three rounds and twelve runs.

The brief said *"identify whether they should map to Myrtle Beach **or
Greenville**"*. Every run enumerated only the Myrtle Beach 50-mile ring and
then reported **"0 → Greenville"** — a zero produced entirely by never
searching there. Aird is the proof it was wrong: a verified Greenville
pediatric anesthesiologist, invisible to twelve consecutive runs.

**If the ask names two places, enumerate both.** A territory you did not search
returns zero and looks exactly like a territory with nobody in it. This is the
denominator lesson again, one level up: the missing denominator was not the
number of records read, it was the number of *places* looked at.

### What the browser is actually worth, measured

The cleanest answer in the benchmark. Of 108 certification blocks filled:

- **101** by both ABA (plain fetch) and ABMS (browser)
- **6** by ABA only — plain fetch
- **1** by ABMS only — browser

**Browser-alone marginal: 0 people, 0 emails, 0 pediatric hits, 0 phones, 1
certification block.**

ABMS genuinely is browser-only — 403 to curl, 200 to Playwright, with no
challenge presented and none solved. It is real, and it was worth one record.

### The ABA contradiction, resolved against our own run

Our clamped run reported "theaba.org has no public diplomate lookup at all."
That was **wrong**. `directoryreactapi.theaba.org` answers a plain `curl` with
HTTP 200 and a JSON diplomate array. The clamped run probed guessable hostnames
(`verify.theaba.org`, `/verify/`), got 404s, and published a rung-2 negative as
a property of the world — never climbing to rung 3, where the API base ships in
the React bundle's `main.js`.

**It cost three of the four pediatric anesthesiologists.** The denominator
lesson, recurring on itself one round later.

Two fixes to the endpoint notes: `lookups/getProgramTypes` 404s — use
`getCertifications`. And `StateId` is a **GUID, not an integer**: `StateId:"41"`
returns `[]` silently, a wrong-key zero of exactly the kind described above.

### Another silent-truncation shape

ABMS returns a **non-zero row count with empty row text** for common surnames
(`Michelle Lee`: 3 rows, all `""`). A `len(rows)` check reads that as presence;
reading the text reads it as absence. A state-scoped retry over the 27
unmatched recovered 9 — including Michelle Lee's pediatric subspecialty.


## Round 3 final: the ceiling was the population, not the data

### Academic vs community changes everything

Four rounds concluded *"work email tops out near 4% — phone is the
deliverable"*. That was true of a **community** roster and **false as a general
claim**.

Same specialty, same state, a 50-mile ring around an academic centre instead of
a resort town:

| | Myrtle Beach | Greenville |
|---|---|---|
| In-ring providers | 120 | **476** |
| NPI pediatric taxonomy | 0 | **20** |
| Evidenced pediatric anesthesiologists | 1 | **25** |
| **First-party published emails** | **4** | **78** |

The email ceiling broke through a **medical-school faculty directory** — not
the literature, which was falsified again with a stated denominator (0 emails
from 81 of 426 checked; 1 of 21 candidates survived both the affiliation and
full-forename locks).

**Classify the population before predicting the ceiling.** Academic medicine
publishes faculty; community practice does not. Look for a medical school,
residency program or teaching hospital in the ring — if one exists, the faculty
directory is the highest-yield email source available and it is free.

### Registry addresses go stale — check current enrollment

The exact inverse of the mailing-address trap, and neither case is solvable
with one source.

**Sara Lathem Walls, MD** is ABA pediatric-certified and practises at Prisma
Greenville. Her NPPES **LOCATION** still reads *Nashville TN* on a record
untouched since **2018**, so the registry places her outside the ring. Her
in-ring NPPES address is **mailing only** — forbidden as a locator. The
hospital's own directory omits her from pediatrics entirely.

She was found **only** through current CMS Medicare enrollment and qualified
**only** by the certifying body.

Compare the rejection that looks identical in reverse: Blomeley had an in-ring
*mailing* address and an out-of-ring *practice*, and was thrown out.

A registry practice address is authoritative but **not fresh**. Before
excluding someone on location, check a current filing.

### An empty string is not an absent filter

A second silent wrong-key zero, one level past the GUID trap — and the GUID fix
alone is necessary but not sufficient.

With the **correct** state GUID, the ABA advanced search still returned `[]` at
HTTP 200, because the API treats an empty string as a **literal filter value**.
The client in `main.js` sends JSON `null`. With nulls, the identical query
returned **860**.

Read what the real client sends before trusting a zero. `""` and `null` are
different queries, and only one of them means "no filter".

### Namespace files in a shared working directory

A process defect worth avoiding: two agents both wrote `build.py` into the same
work directory and one silently replaced the other. It was caught only because
a rebuild printed 23 rows where 476 were expected.

No delivered row was affected, but the failure is silent by construction. Use
namespaced filenames when more than one process writes to shared scratch.

### One judgement call, recorded rather than hidden

Four pediatric-certified anesthesiologists practise at Mission Health
**Asheville — 53.5 miles**, which is 3.5 miles outside a hard 50-mile ring.
Classified `PRACTICE_ELSEWHERE`. If the radius is soft, the in-ring count goes
**12 → 16**.

State the boundary rule you applied and show what moves if it changes. A radius
is a business decision, not a fact.
