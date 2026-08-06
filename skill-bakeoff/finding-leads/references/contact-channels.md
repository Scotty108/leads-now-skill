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


## The registry zero is not the answer

Round 1, measured. Querying the parent taxonomy is **necessary and not
sufficient**.

The registry said **0 pediatric anesthesiologists** within 50 miles of Myrtle
Beach. That was an honest read of NPI and a wrong answer to the question. A
browser-enabled run found **Michelle D. Lee, MD — a registered pediatric
anesthesiologist 25 miles out at McLeod Loris**. Her NPI record carries no
pediatric taxonomy code; the subspecialty is published only on her hospital's
own directory, which is a JavaScript shell to a plain fetch.

**NPI taxonomy is self-reported and frequently omits subspecialty.** So:

1. Query the parent taxonomy to enumerate the population (this is what turns 0
   into 72).
2. **Then check each employer's own directory for the subspecialty.** That is
   where fellowship, department and "pediatric" actually appear.
3. Only after both may you say a subspecialty is absent — and say it as
   *no evidence found*, not as *none exist*.

A registry zero is not the answer: it means the registry does not track that
subspecialty, not that nobody in the ring has it.

## Literature is the wrong instrument for a community roster

Also measured, same round: an OpenAlex + Europe PMC pass over 60 community
anesthesiologists returned **0 usable pediatric signals**, and **51 of 60 had
no scholarly footprint at all**. Where papers existed they were uniformly
adult — cardiopulmonary bypass, TAVR, obstetric analgesia.

Community physicians are not academics. Sending a research pass at that roster
spends the budget and returns nothing. Reach for OpenAlex and Europe PMC when
the target is academic medicine — teaching hospitals, department chairs,
fellowship faculty. For a community roster the subspecialty signal lives in
hospital staff bios, residency and fellowship program pages, and board
certification.

The one pediatric hit in round 1 came from a hospital's own search index, not
from a journal.


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
