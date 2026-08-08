# Vertical pack: US healthcare

Read this only when the target population is clinical — physicians, nurses,
allied health, practice owners. Everything here was measured against a real
roster; the transferable rules live in `contact-channels.md`, and this file is
the concrete instance of them.

## The source ladder for clinicians

| Rung | Source | What it gives |
|---|---|---|
| 1 | **NPI registry** (`npiregistry.cms.hhs.gov`, free, no key) | Enumerates every US clinician: name, credential, taxonomy, practice address, practice phone |
| 1 | **CMS Doctors & Clinicians** (`data.cms.gov` dataset `mj5m-pzi6`, 3.39M rows, no key) | Medicare enrollment: `med_sch`, `grd_yr`, `pri_spec`, `sec_spec_1..4`, `facility_name`, phone |
| 2 | Hospital provider directories | Title, department, sometimes fellowship |
| 3 | Directory payloads / search indexes | The same data, structured |
| 4 | Credentialing bodies | Board certification and subspecialty |

**Start with both federal files.** NPI enumerates; CMS tells you who currently
bills and where. Between them you get a roster with 100% phone coverage before
touching a single hospital website.

The full NUCC provider taxonomy code set ships at
`assets/nucc_individual_taxonomy.csv` — use it to resolve a specialty name to
its code and, critically, to find a code's **parent** before querying.

## More free CMS datasets, resolved from the catalog

Anthropic's own healthcare plugin wires ~32 public CMS tables. These are the
ones that matter for building a roster rather than auditing claims. **Resolve
each by title from `data.cms.gov/data.json` — never hardcode the URL** (see
`bulk-sources.md`); all were confirmed present in the live catalog.

| Dataset title | Why it helps | Cadence |
|---|---|---|
| `Order and Referring` | Providers currently eligible to order/refer — a **weekly** liveness signal, far fresher than NPPES | weekly |
| `Medicare Physician & Other Practitioners - by Provider` | Volume and specialty per provider; separates a busy practice from a lapsed one | annual |
| `<Facility> All Owners` (6 variants) | Names the **owners** behind a facility — the one public route into who actually controls a contracted group | monthly |
| `Revoked Medicare Providers and Suppliers` | Exclude the revoked before you call them | monthly |
| `Opt Out Affidavits` | Providers who opted out of Medicare — a different practice model, often a different employer | quarterly |

`Order and Referring` deserves emphasis: it refreshes **weekly**, where an NPPES
record can sit stale for years. Where the two disagree about whether someone is
still practising, the weekly file is the better evidence.

## Read the registry status — a deactivated NPI is a dead lead

NPPES publishes `basic.status`: `A` active, `D` deactivated. `leadkit ingest`
now records it as `registry_status`, and it is **recorded, never silently
dropped** — the caller decides whether a deactivated provider belongs on the
list.

Also: **a 9-prefix NPI is reserved and never issued.** It cannot resolve, so
treat it as a data-entry error rather than a lookup failure.

## Query the parent taxonomy, never the subspecialty

Measured, 50 miles around one metro:

| Query | Providers |
|---|---|
| `Pediatric Anesthesiology` | **0** |
| `Anesthesiology` (parent) | **72** |

Subspecialty codes are sparsely self-reported. The narrow query returns an empty
list that looks like a correct answer. **Pull the parent, then establish
subspecialty from directories and credentialing bodies.**

## NPI silently repeats past skip=1000

`&skip=1000` and `&skip=1200` return identical records — same NPIs, same order,
`result_count` reported normally, no error, no truncation flag. A naive pager
produces duplicates and a total that looks complete.

Shard by city, then by taxonomy variant, then by first-initial. Track seen NPIs
and stop a shard when a page adds nothing new.

## The reassignment file names the employer NPPES will not

**The most valuable file in this vertical.** `Revalidation Clinic Group Practice
Reassignment` (resolve by title from `data.cms.gov/data.json`, ~537MB, refreshed
within days) links every individual to the group they reassigned Medicare
billing rights to:

```
Group Legal Business Name · Group State Code · Individual NPI ·
Individual Name · Individual Specialty Description · Individual Total Employer Associations
```

Measured on 3,373,759 rows against a 786-person roster:

| | Before | After |
|---|---|---|
| People with a known employer | **0** | **582 (74%)** |
| Reassigning to >1 group | — | **384** |

It also enumerates a contracted group outright — the thing four earlier rounds
failed to do:

| Group | Members | Composition |
|---|---|---|
| Atlantic Coast Anesthesia Services PC | **258** | 160 CRNA · 73 anesthesiology · 23 AA |
| Southeast Anesthesiology Consultants PLLC | **243** | 224 anesthesiology |
| Tidelands Anesthesia Group LLC | **64** | 43 CRNA · 21 anesthesiology |

**And it surfaces the non-physician anesthesia workforce**, which a physician
taxonomy query never returns. Cross-referencing those three groups against the
NPI roster found **453 people the sweep had missed** — and inside a 15-mile
ring, **35 more, every one a CRNA or Anesthesiologist Assistant**. Zero new
physicians in-ring, which is a good sign: the taxonomy sweep had already found
every doctor.

Decide deliberately whether CRNAs and AAs belong on the list. They are anesthesia
providers and are actively recruited; they are also a different credential, and
a user who asked for physicians should be told what they are looking at rather
than handed a blended list.

## Hospital anesthesia is contracted out — check who bills

The single most important fact for this vertical. CMS `facility_name`, queried
by street address, proved four hospitals used four different outside groups:

| Facility | Who actually bills |
|---|---|
| Facility A | Group 1 — 71 of 71 |
| Facility B | Group 2 |
| Facility C | Group 3 |
| Facility D | Group 4 |

56 addresses were harvested, 3 patterns confirmed, and **zero applied** — none
of those people are on the domain they appear to work at, and the contractor
domains had no A record and no MX at all.

This generalises beyond anesthesia: radiology, emergency medicine, pathology and
hospitalist services are routinely contracted. **Determine the billing entity
before propagating any employer email pattern.**

## Credentialing bodies

The American Board of Anesthesiology runs an open, un-captcha'd JSON API,
reachable by reading the API base out of the React bundle's `main.js`:

```
GET  directoryreactapi.theaba.org/lookups/getCertifications
GET  directoryreactapi.theaba.org/searchResults/basic?FirstName=&LastName=
POST directoryreactapi.theaba.org/searchResults/advanced
GET  directoryreactapi.theaba.org/doctorRecord/getDoctorRecords?ABAId=<digits>
```

`ProgramType 519` is Pediatric Anesthesiology. Strip the dash from the ABA ID.
`StateId` is a **GUID, not an integer**, and empty-string filters are treated as
literal values — send JSON `null` for "no filter" or you get a silent `[]`.

Other ABMS member boards have equivalents; `certificationmatters.org` covers all
of them but 403s every plain fetch and needs a browser.

**A certifying body publishes a MAILING address, not a practice location.** Two
plausible in-ring candidates were rejected this way — their practices were in
other states entirely.

## Registry addresses go stale; enrollment is current

One clinician's NPPES location had read the wrong state since 2018. Her in-ring
NPPES address was mailing-only, and her employer's own directory omitted her
from the relevant department. She was found solely through current CMS
enrollment and qualified solely by the certifying body.

**Cross-check a registry address against a current filing before excluding
anyone on location.**

## Where clinician emails come from

- **Academic centres publish faculty directories.** A medical-school faculty
  page yielded 78 addresses where a community roster yielded 5. If there is a
  teaching hospital or medical school in the ring, that page is the single
  highest-yield email source available.
- **Corresponding-author addresses** via `NCBI efetch db=pmc`. Europe PMC's
  `fullTextXML` 404s where efetch succeeds. Affiliation-lock every hit.
- **Community rosters mostly have none.** 69 of 72 had no publication anywhere,
  and the employers contract their anesthesia out.

## Structurally closed for this vertical

Do not spend budget here — a browser does not rescue any of them:

- **State medical boards** — reCAPTCHA / Turnstile gated; bulk rosters are paid
- **ASA and SPA** — no public member directory exists at all
- **Residency and fellowship pages** — circular for discovery: indexed *by
  program*, which is the field you are trying to fill
- **Doximity** — inverted: publishes training only where place fails to
  corroborate, and gates it where place does


## Two more traps specific to this vertical

### The registry zero is not the answer

Querying the parent taxonomy is **necessary and not sufficient**. A registry
reported zero people in the requested **subspecialty** inside the ring; a real
one was practising 25 miles out, with the subspecialty published only on the
employer's own directory. Self-reported taxonomies routinely omit it.

A **registry zero is not the answer** — it means the registry does not track
that subspecialty, not that nobody has it.

### OpenAlex is metered — do not lead with it

Documented publicly as free and keyless. Measured: **HTTP 429**, "Insufficient
budget... you only have $0 remaining", retryAfter 6268s, **0 of 72 queries
served** even with a polite user-agent and mailto. Treat it as best-effort.

Use `NCBI efetch db=pmc` for corresponding-author addresses instead — Europe
PMC's `fullTextXML` 404'd on all four affiliation-locked PMIDs including the
open-access one, while efetch served every single one.

**Literature is the wrong instrument for a community practitioner roster.** A
sweep of 60 returned 0 usable signals, and 51 had no scholarly footprint at all.
These are clinicians, not academics; reach for publication sources only when the
target is academic medicine.
