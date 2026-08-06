# DISCOVER — from a description to a population

The user has no list. Build the frame first, filter second, enrich third. Never begin with a search
engine: it ranks by fame, so it returns the academic medical centre and the unicorn and hides the
solo practice and the 40-person company, which is where the people nobody else has actually live.

Decide which frame exists for this population:

- **Licensed or enumerated people** (clinicians, and anyone with a public licence) → registry frame.
- **People defined by their employer** (roles at companies matching firmographics) → company frame.

## Registry frame — clinicians

The registry is a census: enumeration is mandatory to bill, so essentially every practising US
clinician is in it. This is why a free approach beats a paid one here.

### 1. Resolve the geography before anything else

```
python3 scripts/geo_filter.py resolve "Myrtle Beach, SC" --radius 50
```

It returns the centre, **every state the ring touches**, and the ZIP3 prefixes inside it. A 50-mile
ring around Myrtle Beach reaches into North Carolina; a search of South Carolina alone loses that
side of the ring and nobody notices, because the missing people leave no trace.

**Query by ZIP3 prefix, not by state.** It is narrower, it needs far fewer fetches, and it avoids
the registry's result ceiling. Use states only when the user asked for a whole state.

### 2. Resolve the specialty, and take the parent too

```
python3 scripts/npi_query.py taxonomy "pediatric anesthesiology"
```

The registry searches on the specialisation string alone. The string it *returns* in results is
`Classification, Specialization`, and feeding that back as a query is rejected — the script gives
you the form that works.

**Always query the parent classification alongside the subspecialty.** Subspecialists routinely
file only their parent code, and the subspecialty field is self-reported and under-used. This is
the single highest-recall decision in the whole run.

How much it matters, measured on the origin case: **inside the 50-mile ring**, the number of
providers carrying the *Pediatric Anesthesiology* code is **zero**, while the number carrying the
parent *Anesthesiology* code is **72**. A subspecialty-only search returns an empty list that looks
like a correct answer to a question with no answer.

Expect the subspecialty query to return records anyway, because a ZIP3 prefix reaches well beyond
the ring — the origin-case plan pulls subspecialists from Charleston that the radius filter then
drops. Seeing them at the fetch step does not contradict the count; judge recall only after
filtering.

The consequence for the branch: for a subspecialty request, the registry gives you the **candidate
pool**, not the answer. Which of those 72 actually treat children is settled during enrichment —
from the hospital's own department page, a children's hospital affiliation, a fellowship, or a
board certification. Say this in the brief, and label those rows `probable` until a source confirms.

### 3. Plan, fetch, parse

```
python3 scripts/npi_query.py plan --taxonomy "Pediatric Anesthesiology||Anesthesiology" \
        --zip3 283,284,294,295 --outdir raw
```

Fetch every URL in `raw/_plan.tsv` yourself and save each response to the path beside it. Pause
briefly between fetches. Then:

```
python3 scripts/npi_query.py parse raw --out roster.csv
```

- Exit 3: more pages exist. Fetch `raw/_plan_next.tsv` and parse again. Repeat until it exits 0.
- Exit 4: a query is truncated at the ceiling of about 1,200 records. **Its count is unknown, not
  large.** Re-plan it split by ZIP3 and fetch again. Never report a number from a truncated query.
- Exit 0: every matching record was retrieved. Only now is a count a total.

`parse` emits one row per practice location, which is what lets a clinician whose mailing address
is elsewhere still be found at the site where they actually work.

### 4. Filter to the ring

```
python3 scripts/geo_filter.py filter roster.csv --center "Myrtle Beach, SC" --radius 50 \
        --zip-col postal_code --dedupe-by npi -o near.csv
```

`--dedupe-by npi` keeps each person once, at their nearest location. Rows whose ZIP is not a Census
ZIP area are dropped and counted — put that count in the brief rather than losing it.

### 5. Resolve the employer from the practice address

An individual registry record carries no employer, so `org` comes back blank and the whole list
looks anonymous. Organizations enumerate at the same street address, which makes the address the
join key:

```
python3 scripts/npi_query.py plan --zip3 <zips-in-your-filtered-list> --etype NPI-2 --outdir orgs
python3 scripts/npi_query.py employers --roster near.csv --orgdir orgs -o with_orgs.csv
```

Plan the organization fetch across the ZIPs your filtered list actually contains, not the whole
frame. On the origin case this resolved an organization for **83%** of rows and a
specialty-matching one for **58%**.

What it returns is more useful than a hospital name: it surfaces the **physician group**, which is
usually a separate company from the hospital and carries its own email domain. A site with several
organizations is normal — hospital, physician group, billing entity, and unrelated tenants of the
same medical office building all enumerate there. `org_specialty_match` marks the candidate whose
name shares a word with the person's specialty; treat it as the lead hypothesis and confirm it on
a page that names the person.

Group names also carry subspecialty signal that the taxonomy field does not: a children's or
paediatric group at the address is evidence toward a subspecialty request that no registry code
provided.

### 6. Enrich each person

The registry gives name, credential, specialty, practice address, and often a **published practice
phone**. It does not give employer, title, or department. Get those from the organization's site
using the ladder in `source-access.md`.

The practice phone is a real, published number, and for clinicians it is usually a higher-confidence
route than any derived email. Lead with it when the email tiers come back weak.

Two traps the registry sets, both of which fail silently:

- **A practice address shared by dozens of people is an employer, a billing service, or a
  credentialing agent — not a place to reach someone.** `parse` counts this into
  `address_shared_by` and warns above 50. On the origin-case data, 125 individuals list a single
  Charleston street address. Use those rows for the person, never for "where they work".
- **Registry addresses are self-maintained and go stale.** Roughly half of individual records have
  not been touched in five years. Treat the address as a strong lead, not as fact, and say so.

Other free sources worth a pass: the CMS clinician dataset adds group affiliation and organization
size; PubMed gives *published* addresses for anyone who publishes. State licence lookups confirm
status, credentials, and disciplinary history — **join them for those attributes, not for
geography, because their addresses are markedly less accurate than the registry's.**

If the user needs a whole state or the nation rather than a radius, the API cannot prove it
enumerated everything and caps out long before a dense state is covered. Say that plainly and
offer the bulk registry download as the alternative frame; do not silently deliver a truncated
count.

Filter to the profession asked for. A specialty search returns physicians, physician assistants,
and nurse anaesthetists together, distinguished by the `credential` and taxonomy columns.

**Budget the expensive rungs.** Group the remaining rows by organization and climb to endpoint
discovery or a browser only for the few organizations covering the most people, hardest first.
Three organizations covering 40 rows are worth the effort; twelve covering one row each are not.
Record the rest as unreadable and move on.

## Company frame — business populations

No registry exists, so build the company list first and the people second. Never search for the
people directly.

1. **Build the company frame** from sources that enumerate rather than rank: the YC company list
   (one JSON file, thousands of companies with domains, size, stage), SEC EDGAR full-text search
   for private-placement filings, accelerator and portfolio pages, association member directories,
   and category listings. Filter on the firmographics the user gave.
2. **Confirm each company's domain** before anything else. A wrong domain wastes every later step.
3. **Find the people** on the company's own site: team, leadership, and about pages first, then
   press releases and conference speaker lists, then job posts, which name the hiring manager's
   team and confirm the function exists.
4. **Read the hiring signal.** An open role for the function means the team exists and is funded.
   A job post that names a reporting line names a person.

Coverage expectation to state plainly in the brief: for small and mid-sized organizations outside
tech, confidently usable contact coverage runs roughly 15-30%. That is not underperformance — the
best-funded commercial waterfalls reach under 25% of independent clinicians and under 40% of local
businesses, because their data comes from the inboxes of people who already sell to that segment.
Compete on identifying the whole population, which public registries make possible and paid tools
genuinely cannot, rather than on guessing personal addresses, which nobody wins.

## Before handing off

Every row needs a `source_url`. Then run the audit script with the population and filter counts, so
the brief's denominator comes from a script rather than from memory.
