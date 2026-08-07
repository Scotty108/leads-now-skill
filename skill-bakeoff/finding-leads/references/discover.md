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

**1. Registry or official-filing sweep first, when the vertical has one.**

Regulated professions have public registers; companies have corporate filings.
These enumerate a population outright and cannot block you. See the matching
`references/vertical-*.md` pack for the concrete sources and their traps.

An official register is the strongest possible start: it enumerates rather than
samples, it is free, and it does not care whether a company website blocks you.

Two traps that recur across every register measured:

- **Query the parent category, never the narrow one.** Sub-categories are
  sparsely self-reported; the narrow query returns an empty list that looks like
  a correct answer.
- **Registers truncate silently.** Deep paging often repeats instead of
  advancing, with no error and a normal-looking count. Shard the query and track
  seen IDs; treat any page that adds nothing new as the ceiling.

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
