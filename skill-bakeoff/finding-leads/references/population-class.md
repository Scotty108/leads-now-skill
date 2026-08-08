# Classifying a population you have never sourced before

Read this whenever the ask names a kind of person with no `vertical-*.md` pack —
commercial roofers, school superintendents, insurance producers, veterinary
practice owners, machine-shop buyers. **Do not start by guessing at websites.**
The class determines whether a roster exists at all, and that single fact sets
the whole plan and the shape of an honest answer.

## Step 1 — take the highest class that applies

Ask in order and stop at the first yes. Each question is about the *structure*
of the occupation, not the industry.

| # | Ask | Class | Roster lives in |
|---|---|---|---|
| 1 | Fined or prosecuted for doing this work **without a licence**? | **Licensed** | A mandatory public register |
| 2 | Does a **taxpayer** fund the salary? | **Public payroll** | Salary disclosure, staff directory, org chart |
| 3 | Is the person **the business** — owner, principal, sole practitioner? | **Entity principal** | Corporate filings, permits, DBAs |
| 4 | **Letters after the name** that somebody verifies? | **Credentialed** | The certifying body's verification tool |
| 5 | A **trade body** they would plausibly join? | **Association** | Member directory, or the public officer list |
| 6 | None of the above | **Privately employed** | Nowhere central |

Populations are routinely two at once — a hospital-employed physician is
Licensed *and* privately employed; a city engineer is Licensed *and* public
payroll. Take the highest, because that is the one that enumerates.

## Step 2 — enumerable, or only samplable?

This is the fork that decides what "done" means, so state it in the report.

| Class | Enumerable? | What a complete answer is |
|---|---|---|
| Licensed | **Yes, completely** | Every licensee in the radius, minus lapsed |
| Public payroll | **Yes** | Every published post in the named bodies |
| Entity principal | **Yes, via the entity** | Every registered business of that type |
| Credentialed | Partial | Holders of the credential, not everyone qualified |
| Association | Partial | Members only; non-members are invisible |
| Privately employed | **No** | You sampled; say how many orgs you checked |

**Only an enumerable class has a denominator.** "41 of 41" is a census claim and
requires one. "18 found across 26 orgs checked" is the honest form everywhere
else — and never imply it is everyone. A user who reads a sample as a census
concludes the territory is empty when it is not.

## Step 3 — locate the register

For **Licensed**, the register exists and the only work is finding it:

1. `"<state> <profession> license lookup"` / `license verification`
2. `"<state> board of <profession>"` → its "verify a licence" tool
3. `site:.gov "<profession>" licensee` — reaches rosters no search box exposes
4. **The state open-data portal** — `data.<state>.gov`, searching the
   profession. Many states publish the entire licensee file as a downloadable
   CSV. **Check here before paging a lookup form**: one download beats ten
   thousand queries, and the forms are where the CAPTCHAs are.
5. A national register where one exists and supersedes the states

### Resolve from the catalog — never hardcode a download URL

Government portals rotate download paths on every release. Verified on
`data.cms.gov`: each CSV sits behind a dated folder *and* a GUID
(`.../2026-08/303a44ff-27bb-.../Order_and_Referring.csv`), so a URL written down
today 404s after the next release — and **the failure looks exactly like the
dataset being withdrawn** rather than moved.

Every portal publishes a machine-readable catalog carrying the current path:
`data.cms.gov/data.json` (DCAT, resolve by `dataset[].title` regex → newest CSV
`distribution`), Socrata's `api.us.socrata.com/api/catalog/v1`, and
`data.medicaid.gov/api/1/…` (DKAN). Search by title, take the distribution, then
fetch. When a fetch 404s, re-resolve — do not hunt for a new URL by hand.

### Two ways a bulk dataset lies about what it holds

**A sample row is not the schema.** Querying the federal carrier census with
`$limit=1` returns **34 fields, and `cell_phone` is not one of them** — yet an
explicit `$select=cell_phone` returns **1,874,212 populated values**. Reading one
row and concluding "no phone column" writes off the largest free source of real
mobile numbers in the country. Enumerate columns from the dataset's **metadata**
(Socrata's Discovery API exposes `resource.columns_field_name[]`), then `$select`
them explicitly.

**`NOT NULL` is not populated.** An Illinois licence file reports 1,522 rows
where `home_phone IS NOT NULL` — and **77** once you exclude the literal string
`'NA'`. 95% of that column is a sentinel wearing data's clothes. Test against
`NA`, `N/A`, `NONE`, `UNKNOWN`, `0000000000`, `-`, `XXX` before counting
anything as coverage.

**Public payroll** — transparency portals, agency and district staff
directories, published org charts, board minutes and budget documents naming
post-holders.

**Entity principal** — Secretary of State business search (officers and
registered agents), and trade permits (contractor, liquor, food service,
childcare) which name the qualifying individual.

**Credentialed / Association** — the body's own verification tool or directory.
Where the directory is members-only, the **officer and committee list is public**
and is a small, current, high-quality sample.

## Step 4 — predict the email ceiling from the class

Yield varies by more than an order of magnitude, and the class predicts it
better than effort does. Set expectations before starting, not after failing.

| Class | Free work-email yield | Why |
|---|---|---|
| **Public payroll** | **Highest** | Disclosure norms; addresses published outright |
| Entity principal | High | Being contacted is the point of the business |
| Association | Moderate | Directories often carry member contact |
| Licensed | **Low** | Registers publish address and phone, rarely email |
| Privately employed | Low | Entirely dependent on the employer's site |
| Credentialed | Low | Verification confirms status and nothing more |

**A licence register gives you a person and a phone, not an inbox.** Plan to get
the roster from one class and the addresses from a different source, and budget
the domain-unlock hunt accordingly.

Where the radius contains a **university, teaching hospital, public agency or
school district**, that is the highest-yield free email source available in any
vertical — public and academic bodies publish their people.

## Step 5 — search engines find organizations, never people

True in every class. Shape the query like the source, not like the question, and
exclude the job boards explicitly — they dominate role-title searches and none
of them is the person.

```
"<state> <profession> license lookup"
site:.gov "<profession>" licensee list
site:.org "<trade association>" members directory
"<city>" "<role title>" -jobs -indeed -ziprecruiter
```

## Privately employed — the hard class

Nothing enumerates "RevOps leads at Series B fintechs". Build the **org** frame
first, then work each one: funding announcements and investor portfolios for the
company set; `/team`, `/about`, `/leadership` for names; careers pages for a
hiring signal and often a recruiter's real address; conference speakers and
podcast guests for current public names; press releases for executives and email
formats.

Aim for 3–5× more orgs than you need people. Say the lower yield up front rather
than letting a thin list read as a bad run.

## The event-visible overlay

Cutting across every class, people become public when they *do* something:
speaker rosters, award and "40 under 40" lists, permit applications,
disciplinary actions, court filings, published authors, patent assignees, grant
recipients. These never enumerate a population, but they are current, they name
the person, and they usually carry a title.

Use them to **enrich or corroborate** a roster you already built, and to reach
people the register lists but the employer hides.
