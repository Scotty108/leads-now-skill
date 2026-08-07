# Branch: DISCOVER — person-first sourcing

The user described a kind of person and has no list. You have to find them.

This is the branch commercial tools are worst at. Clay returned **two** pediatric
anesthesiologists within 50 miles of Myrtle Beach; the population is far larger.
Their coverage is excellent on common targets and thin on the long tail, which
is exactly where someone bothers to ask an agent.

## Pin the ICP first

Do not search until these are concrete. Ask only for what is missing.

- **Role** — the title as it appears on org sites ("pediatric anesthesiologist",
  not "doctor"). Note acceptable variants; job titles are not standardized.
- **Geography** — a place plus a radius, or an explicit list of orgs.
- **Org type** — hospital system, private practice, Series B SaaS, agency…
- **Size** — how many verified rows is enough? Stop there.
- **Fields** — which columns matter.

Write the ICP back in two lines and begin.

## Order of attack

**1. Registry sweep first, when the vertical has one.**

For clinicians this is the whole game. The NPI registry enumerates every US
provider, free, no key, with a real specialty taxonomy.

**Always query the PARENT taxonomy, not the subspecialty the user named.**
Subspecialty codes are sparsely self-reported, so the narrow query returns an
empty list that looks like a correct answer. Measured on the origin case, within
50 miles of Myrtle Beach:

| Query | Providers |
|---|---|
| `Pediatric Anesthesiology` (what was asked for) | **0** |
| `Anesthesiology` (the parent) | **72** |

Zero is not the answer to "find pediatric anesthesiologists here" — it is the
answer to a question nobody asked. Pull the parent, then establish subspecialty
from directories, fellowships and publication history (see
`references/qualify.md`). Name both taxonomies in the query when the registry
accepts a list, and say in the report which one produced the rows.

Use the toolkit rather than hand-building URLs — it resolves the radius,
plans the pages, and detects the ceiling:

```
python3 leadkit.py geo  --place "Myrtle Beach" --state SC --radius 50
python3 leadkit.py plan --taxonomy "Anesthesiology" --states SC,NC --outdir raw
#   fetch each URL in raw/_plan.tsv with your own web tool, save VERBATIM
python3 leadkit.py ingest raw -o records/npi.json
```

`geo` returns the states AND ZIP3 prefixes the radius touches. **A 50-mile
radius around Myrtle Beach spans SC and NC** — measured, 886 of the
anesthesiology providers returned were in North Carolina, and a single-state
query drops every one of them.

`ingest` exits **3** when a query returned a full page (more remain) and **4**
when it hit the ceiling or started repeating. Treat exit 4 as *this result set
is incomplete* and partition further — never report its count as a total.

Verified working: returns structured JSON records with name, credential,
taxonomy, city, state and NPI.

**The pagination ceiling will silently lie to you.** Verified by direct test:
`&skip=1000` and `&skip=1200` on the same query return the *identical* five
records — same NPIs, same order, `result_count` reported normally, no error and
no truncation flag. Past roughly 1,000 the API repeats instead of advancing, so
a naive pager produces duplicates and a result that looks complete and is not.

Two consequences, both mandatory:

1. **Shard the query instead of deep-paging.** Split by city, then by
   `taxonomy_description` variant, then by `first_name` initial. Each shard is
   its own sub-1,000 result set. Sharding by city alone materially increases
   unique records over a single state-wide sweep.
2. **Detect the repeat.** Track NPIs you have already seen. When a page returns
   nothing new, you have hit the ceiling — stop paging that shard and say so.
   Never report a count that includes repeated pages.

Filter by distance afterward — the API takes state and city, not a radius, so
pull the state, shard by city, and narrow locally.

If an NPI MCP tool is available in the environment, prefer it over hand-built
URLs — but the ceiling above is a property of the underlying API, so the
sharding rule still applies.

**2. Then find organizations, not people.**

Search engines are excellent at orgs and poor at individuals. Shape queries like
the source, not like the question:

- `"pediatric anesthesiology" hospital "Myrtle Beach" OR "Conway" SC`
- `site:.org "medical group" anesthesiology South Carolina`

Aim for 3–5× more orgs than you need people; most yield nothing.

**3. Then read each org's directory** via the escalation ladder in SKILL.md.
Read `references/blocked.md` the first time a source refuses you.

## For B2B, there is no registry

This is the harder half. Nothing enumerates "RevOps leads at Series B fintechs",
so you build the org list first and work down:

- Funding announcements and investor portfolio pages give you the company set
- `/team`, `/about`, `/leadership` give you names
- Careers pages give you hiring signals *and* often a recruiter's real address
- Conference speaker pages and podcast guest lists are current and public
- Press releases name executives and leak email formats

Expect lower yield per org than clinical work, and say so up front rather than
letting the user infer that a thin list means you did a bad job.

## Report the segment before the people

**Default to counts and segments, not a stack of per-person profiles.** Nobody
wants 400 records; they want the twelve worth calling. Lead with the shape of
what you found:

```
41 anesthesiologists within 50 miles of 29577
   6 with pediatric taxonomy (207LP3000X)
  14 at Grand Strand      3 at Conway Medical Center
  12 unreachable — directory blocked or no listing
```

Then let the user choose which segment to pull records for. Making the
per-person pull a deliberate second step is better workflow — it targets before
it harvests — and it keeps the default output a targeting instrument rather than
a pile of dossiers.

Pull full records when the user asks for them, for the segment they named.

## What a record looks like

One record per person, with the source that produced it:

```json
{"full_name":"Sarah Kim, MD","title":"Pediatric Anesthesiologist",
 "org":"Mercy Health","org_domain":"mercyhealth.org",
 "profile_url":"https://mercyhealth.org/providers/sarah-kim",
 "source":"NPI registry"}
```

Write one file per source into `records/` — keeping them separate is what makes
corroboration countable. Then hand off to `merge` and `csv` per SKILL.md Step 6.

## Stop conditions

Stop when you hit the requested count of **verified** rows, or when two
consecutive orgs yield nothing new. Do not pad the list to hit a number. A user
who asked for 30 and got 18 real ones is better served than one who got 30 with
12 invented.
