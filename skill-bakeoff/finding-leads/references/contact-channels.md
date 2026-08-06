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

1. **OpenAlex** (`api.openalex.org`, free, no key). Search the author, then
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
