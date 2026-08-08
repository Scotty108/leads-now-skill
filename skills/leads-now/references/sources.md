# Deriving the sources for a population you have never sourced before

Read this when the ask names a kind of person you have no pack for — commercial
roofers, school superintendents, insurance producers, veterinary practice
owners, machine-shop buyers. **Do not guess at websites.** Classify the
population first; the class tells you whether a roster exists at all, which is
the single fact that decides the whole plan.

## Step 1 — classify the population

Ask these in order and stop at the first yes. Each question is about the
*structure* of the occupation, not the industry.

| # | Ask | Class | Roster lives in |
|---|---|---|---|
| 1 | Can you be **fined or prosecuted** for doing this work without a licence? | **Licensed** | A mandatory public register |
| 2 | Does a **taxpayer** fund the salary? | **Public payroll** | Salary disclosure, staff directory, org chart |
| 3 | Is the person **the business** — owner, principal, sole practitioner? | **Entity principal** | Corporate filings, permits, DBAs |
| 4 | Are there **letters after the name** that somebody verifies? | **Credentialed** | The certifying body's verification tool |
| 5 | Is there a **trade body** they would plausibly join? | **Association** | Member directory, or at minimum the officer list |
| 6 | None of the above | **Privately employed** | Nowhere central |

A population is often two at once — a hospital-employed physician is Licensed
*and* privately employed; a city engineer is Licensed *and* public payroll.
**Take the highest class that applies**, because that is the one that
enumerates.

## Step 2 — enumerable or only samplable?

This is the fork the user needs stated out loud, because it sets what a complete
answer even looks like.

| Class | Can you enumerate? | What "done" means |
|---|---|---|
| Licensed | **Yes, completely** | Every licensee in the radius, minus lapsed |
| Public payroll | **Yes** | Every published post in the named bodies |
| Entity principal | **Yes, via the entity** | Every registered business of that type |
| Credentialed | **Partial** | Everyone who holds the credential, not everyone qualified |
| Association | **Partial** | Members only; non-members are invisible |
| Privately employed | **No** | You sampled orgs; say how many you checked |

**Enumerable populations get a denominator; samplable ones do not.** For the
first four you can say "41 of 41". For the last, "18 found across 26 orgs
checked" — and never imply that is everyone.

Say which regime you are in when you report. A user who thinks a sample is a
census will believe the territory is empty when it is not.

## Step 3 — find the actual register

For **Licensed**, the register exists; the only work is locating it. In order:

1. **Navigate the licensing body's own site to its public-records page** — this
   works with **zero searches** and is the first thing to try. Measured: from
   `myfloridalicense.com`, three hops (instant public records → construction
   industry → public records) reached a **48 MB CSV of all 270,487 licensees**,
   HTTP 200, no key, no CAPTCHA, no login. Look for "public records",
   "data downloads", "licensee files", "extracts".
2. `"<state> <profession> license lookup"` / `license verification`
3. `"<state> board of <profession>"` — then its "verify a licence" tool
4. `site:.gov "<profession>" licensee` — reaches rosters no search box exposes
5. **The state open-data portal** — `data.<state>.gov`, searching the profession
6. National register, where one exists and supersedes the states

### Two ways a bulk dataset lies about what it holds

**A sample row is not the schema.** Querying the federal carrier census with
`$limit=1` returns **34 fields, and `cell_phone` is not one of them** — yet an
explicit `$select=cell_phone` returns **1,874,212 populated values**. Reading one
row and concluding "no phone column" writes off the largest free source of real
mobile numbers in the country.

**Enumerate columns from the dataset's metadata**, never from a sample row.
Socrata's Discovery API exposes `resource.columns_field_name[]`; most portals
have an equivalent. Then `$select` the ones you want explicitly.

**`NOT NULL` is not populated.** An Illinois licence file reports 1,522 rows
where `home_phone IS NOT NULL` — and **77** once you exclude the literal string
`'NA'`. 95% of that column is a sentinel wearing data's clothes.

Test against sentinels — `NA`, `N/A`, `NONE`, `UNKNOWN`, `0000000000`, `-`,
`XXX` — before counting anything as coverage. This is the same failure as an
empty string being read as an absent filter, seen from the other side.

**Bulk file before lookup form, always.** One download beats ten thousand
queries, forms are where the CAPTCHAs are, and a form cannot tell you the
denominator. Rung 1 is listed first because **web search is a budget that runs
out** — a real run exhausted its search allowance and still reached the register
by navigating from the root domain.

For **Public payroll**: state and municipal transparency portals, district and
agency staff directories, published org charts, board-meeting minutes and
budget documents naming post-holders.

For **Entity principal**: Secretary of State business search (names officers and
registered agents), trade-specific permits — contractor, liquor, food service,
childcare — which name the qualifying individual, and federal licensees.

For **Credentialed** and **Association**: the body's own verification or
directory. Where the full directory is members-only, the **officer and committee
list is public** and is a small, high-quality, current sample.

## Step 3b — the roster and the employer are different filings

**The file that enumerates people rarely names who they work for.** This is the
single highest-value thing to check after you have a roster, and it is easy to
miss because the roster file looks complete.

Measured: a 786-person registry roster had an employer on **zero** of them. A
*separate* federal filing — the billing-reassignment list — attributed **582 of
786 (74%)** to a named organisation, and named three contractor groups that had
blocked four earlier rounds entirely.

So look for the second filing:

| Class | Enumerates people | Names the employer |
|---|---|---|
| Licensed | The licence register | Billing reassignment, provider-group filings |
| Entity principal | Business registrations | The filing itself names the principal |
| Public payroll | Staff directory | Salary disclosure names the department |
| Credentialed | The certifying body | Rarely — try the employer's own directory |

**Never conclude "no employer is published" from the roster file alone.**

### An employer is not one value

Of the 582 attributed, **384 reassigned to more than one group.** A contractor,
locum or part-timer bills through several organisations at once, and picking one
silently is how a record ends up asserting a relationship that is only a third
true.

Carry them all, or carry the one you can date — and never propagate an email
pattern from a multi-employer person's *first* listed org.

## Step 4 — where the emails actually are, by class

Yield differs by more than an order of magnitude, and it is the class that
predicts it — not your effort. Set expectations from this before you start.

| Class | Free work-email yield | Why |
|---|---|---|
| **Public payroll** | **Highest** | Disclosure norms; addresses are routinely published outright |
| Entity principal | High | They want to be contacted — it is their business |
| Association | Moderate | Directories often include contact for members |
| Licensed | **Low** | Registers publish address and phone, almost never email |
| Privately employed | Low | Depends entirely on the employer's site |
| Credentialed | Low | Verification tools confirm status, nothing more |

**A licence register gives you a person and a place — check whether it gives
anything else.** Measured: the NPI registry publishes a practice phone, while
Florida's DBPR construction file publishes a mailing address and **no phone and
no email at all** — across 270,487 rows and 22 columns there were 2 stray
`@` cells, both typos inside a name field.

So do not assume a register carries a channel. **Count the populated cells
before promising reachability**, and expect to get the roster from one class and
the contact details from a different source — budget the domain-unlock hunt in
`contact-channels.md` accordingly.

Where the ring contains a **university, teaching hospital, public agency or
school district**, that is the highest-yield free email source available,
whatever the vertical — public and academic bodies publish people.

## Step 5 — search engines find orgs, never people

True in every class. A search result gives you a press release from 2019; a
register gives you a canonical name, a category and an address. Shape queries
like the source rather than like the question:

```
"<state> <profession> license lookup"
site:.gov "<profession>" licensee list
site:.org "<trade association>" members directory
"<city>" "<role title>" -jobs -indeed -ziprecruiter
```

Exclude the job boards explicitly. They dominate role-title queries and none of
them are the person.

## Privately employed — the hard class

Nothing enumerates "RevOps leads at Series B fintechs". Build the **org** list
first, then work each one:

- Funding announcements and investor portfolio pages give you the company set
- `/team`, `/about`, `/leadership` give you names
- Careers pages give a hiring signal *and* often a recruiter's real address
- Conference speaker pages and podcast guest lists are current and public
- Press releases name executives and leak email formats

Aim for 3–5× more orgs than you need people; most yield nothing. Expect lower
yield per org than any enumerable class, and **say so up front** rather than
letting the user infer that a thin list means you did a bad job.

## The event-visible overlay

Cutting across every class: people become public when they *do* something.
Speaker rosters, award and "40 under 40" lists, permit applications, licence
disciplinary actions, court filings, published authors, patent assignees, expert
witnesses, grant recipients. These never enumerate a population, but they are
current, they name the person, and they usually carry a title.

Use them to **enrich or corroborate** a roster you already built, and to reach
people the register lists but the employer hides.

## What not to use

- **Scraped consumer databases** — out of scope, and a compliance problem.
- **Anything behind a login you agreed not to scrape.** Read the terms.
- **Personal social profiles** for personal contact details. Business contact
  data at a business address is the line this skill stays on.
- **Paid aggregators you have not paid for.** A masked email in a preview is not
  a resolution — leave the cell blank.

## Vertical packs

When a pack matches the population, load it — it carries the concrete endpoints
and the traps already paid for:

| Pack | Population |
|---|---|
| `vertical-healthcare.md` | Physicians, nurses, allied health, practices |

No pack for this population is the normal case. Work Steps 1–5, and record what
you learn about the register in the run notes so the next person does not pay
for it twice.
