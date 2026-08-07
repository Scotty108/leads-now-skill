# Branch: QUALIFY — research a shortlist

Enumeration tells you a person exists. Qualification tells you whether they are
worth contacting. Different jobs, different costs, different set sizes.

**Never run this branch on a full population.** Enumerate cheaply, rank, then
qualify the top slice. Twelve people researched properly beats four hundred
skimmed, and costs less.

## What this branch is for

The question a directory field cannot answer — *past* experience, depth in a
niche, seniority, whether they have done this specific thing before.

The origin case was a recruiter who needed people with **prior** experience in a
subspecialty, explicitly not just people whose current title said it. No roster
field carries that. It lives in bios, credentials, training history and
published work.

## When to run it

- The ask names a quality no directory carries
- The list is already narrowed to a shortlist
- The user asks "which of these should I actually contact?"

## The registry zero is not the answer

**Querying the broad category is necessary and not sufficient.**

A registry reported **0** people in the requested subspecialty within the ring.
That was an honest read and a wrong answer: a fully qualified specialist was
practising 25 miles out. Their registry record carried only the parent category;
the subspecialty was published on their employer's own directory.

Self-reported taxonomies routinely omit specialisation. So:

1. Query the parent category to enumerate the population.
2. **Then read each employer's own directory** for the finer detail.
3. Only then may you say a specialisation is absent — and say it as *no evidence
   found*, not *none exist*.

## The index is a pointer, not the record

Reading a search index returned **2** qualifying signals across 84 people.
Following each index record's link to the **individual profile page** returned
**79** across 160 — because the index carried no training fields at all, while
the profile pages published credentials, education and history to a plain fetch.

**Open the profile.** An index exists to help you find the page; it is not the
page.

## Silence is not absence — and it marks your best targets

A `NONE_FOUND` must be explained structurally or it misleads:

- One employer published **no** training block for **any** person in the target
  role, while publishing one for other roles. Verified, not assumed.
- Another published no credential field at all across 299 profiles.

Those `NONE_FOUND`s mean *the source cannot show it*, not that the person lacks
it. Which inverts the priority: **those people are often the highest-value
contacts**, because everyone else's absence has been checked and theirs has not.

Say which kind you are reporting — **checked-and-absent** or **unpublishable**.

## Go to the body that grants the credential

For any regulated or certified profession, the certifying body is the only
source that can turn an unpublishable blank into a checked fact. One such body
filled 46 credential blocks on people no employer directory would publish.

Find it by climbing the ladder — the public search API is often shipped in the
site's own front-end bundle.

Two cautions, both measured: a certifying body publishes a **mailing address**,
not a practice location; and its search may cap results silently.

## Strip page chrome before matching

Page furniture matches exactly like content. A navigation string containing the
target term graded **all 33** of one organisation's people as qualifying until
it was stripped, and 18 hits for a keyword turned out to be personal-life
mentions in bios.

**Match inside the record**, never across the whole page. Require the term in a
credential, training or role field.

## Choose the right instrument for the population

Published literature is the wrong tool for a practitioner population: a sweep of
60 found **0** usable signals, with 51 having no scholarly footprint at all.
Reach for publication and citation sources when the target is academic; for
practitioners the signal is in employer bios, training pages and credentials.

## Output: evidence, not adjectives

Every claim tied to a source. Do not write "extensive experience" — write what
you found and where.

```
Name — Employer, Role
  Signal: STRONG
    - Credential X, granted 2013 [certifying body URL]
    - Prior role at Y, 2016-2021 [employer directory URL]
  Current record shows only the parent category [registry URL]
```

Grade **STRONG** / **MODERATE** / **NONE FOUND**, and never write a fluent
paragraph from three data points. If you found two facts, write two facts.
