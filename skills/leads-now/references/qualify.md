# Branch: QUALIFY — research a shortlist

Enumeration tells you a person exists. Qualification tells you whether they are
worth calling. These are different jobs and they cost different amounts, so they
run on different sized sets.

**Never run this branch on a full population.** Enumerate cheaply, rank, then
qualify the top slice. Twelve people researched properly beats four hundred
skimmed, and it costs less.

## What this branch is for

The question a directory field cannot answer. The origin case:

> *"Find anesthesiology providers — especially pediatric anesthesiologists or
> people with pediatric experience — within 50 miles of Myrtle Beach. Even past
> hospital experience was useful; it did not have to be only people currently
> working at a specific hospital."*

**Past experience is the hard part.** A provider whose current title reads
"Anesthesiologist" may have done a pediatric fellowship, spent six years at a
children's hospital, or published on pediatric airway management. The NPI
taxonomy will not say so. The hospital bio might. Their publication record
almost certainly will.

That is a research question per person, and it is the difference between a list
of 41 names and the 6 worth a phone call.

## When to run it

- The user asked for a quality a directory does not carry: *past* experience,
  subspecialty depth, seniority, likely receptiveness
- The list is already narrowed to a shortlist
- The user asks "which of these should I actually contact?"

If a research skill is available in the environment, this is the branch to hand
off to — the work is genuinely multi-source with claim-level citation. If not,
do it inline with the same discipline: cite every claim to a URL.

## Sources for professional history

Free, open, and better than a social profile for clinical work:

| Source | Gives you |
|---|---|
| **OpenAlex** | Publications, co-authors, affiliation history with dates |
| **ORCID** | Self-reported education, employment, funding |
| **NPI history** | Taxonomy changes and address history over time |
| **State license** | Issue date implies career stage; disciplinary record |
| **Hospital bio** | Fellowship, residency, board certifications, interests |
| **Residency/fellowship program pages** | Alumni lists, often by year |
| **Conference programs** | What they present on is what they do |
| **PubMed / journals** | Subject matter over a career |

Affiliation *history* is the unlock. OpenAlex records the institution attached
to each paper, so a provider's publication trail is a dated employment trail —
which is exactly the "past hospital experience" signal, from an open source.

## Output: evidence, not adjectives

For each person, produce a short qualification with every claim tied to a
source. Do not write "extensive pediatric experience" — write what you found and
where.

```
Dr. Sarah Kim, MD — Mercy Health, Anesthesiology
  Pediatric signal: STRONG
    - Fellowship, Pediatric Anesthesiology, [program page URL]
    - 7 papers on pediatric airway management 2018-2024 [OpenAlex]
    - Affiliation history includes Children's Hospital X 2016-2021 [OpenAlex]
  Current taxonomy: Anesthesiology (not peds) [NPI]
  Territory: Myrtle Beach (practice address, 12mi)
```

Grade the signal, and say when it is absent:

- **STRONG** — direct evidence of pediatric training or sustained practice
- **MODERATE** — some pediatric work, or adjacent (peds ICU, NICU, peds surgery)
- **NONE FOUND** — searched, found nothing. Not the same as "no experience"

That last distinction matters. "None found" means the evidence is absent, not
that the person is unqualified. Say which one you mean; a recruiter can still
call someone whose record is simply thin online.

## Do not invent the narrative

The same rule as everywhere else, in a form that is easier to break here. It is
tempting to write a fluent paragraph about someone's career from three data
points. Do not. Every sentence in a qualification should be traceable to a
source you actually read. If you found two facts, write two facts.


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
