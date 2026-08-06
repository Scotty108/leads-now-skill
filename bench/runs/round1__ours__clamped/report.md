# Anesthesiology providers within 50 miles of Myrtle Beach

Run: `round1__ours__clamped` — skill `leads-now`, branch **FULL** (DISCOVER → QUALIFY → enrich → verify).
Condition A (clamped): WebFetch / WebSearch / Bash only. No browser automation, so escalation-ladder
rung 4 was unavailable by design. Wall clock ~11 min. 3 subagents.

## 1. Counts

| | |
|---|---|
| Registry sweep, state-wide (NC + SC) | 2,327 distinct NPIs — **TRUNCATED, not a total** (see §4) |
| Registry sweep, ZIP3-partitioned (283/284/290/294/295) | 1,017 distinct NPIs — 786 people, 231 organizations |
| **People within 50 mi of Myrtle Beach** | **60** |
| Rows in `result.csv` | **59** (merge collapsed two NPIs on one name) |
| Anesthesia **organizations** (type-2 NPI) in radius | 42 (`records/npi_orgs_in_radius.json`) |
| Rows with a **real email** | **3** |
| Rows with a business phone | **59** |
| Rows with an org profile URL | 5 |
| Rows with a LinkedIn URL | **0** |
| Territory: Myrtle Beach / Greenville | **60 / 0** |

### The segment, before the people

```
60 anesthesiology providers within 50 mi of Myrtle Beach
   0 with a registered Pediatric Anesthesiology taxonomy  (207LP3000X)
   0 graded STRONG or MODERATE for pediatric experience from open sources
  23 Myrtle Beach   7 Conway   6 Bolivia NC   5 Pawleys Island   4 Whiteville NC
   3 each: Georgetown, Loris, Shallotte NC   2 Murrells Inlet
   1 each: N Myrtle Beach, Little River, Mullins, Sunset Beach NC
   5 matched to a hospital bio page  ·  54 with no readable org directory
```

### Email confidence, split by label

| Label | Count |
|---|---|
| `pattern_inferred` @ `pattern_confirmed` | 3 |
| `first_party_published` (org contact, not a provider) | 2 (`sandy.moore@cmc-sc.com`, `Sydney.Causey@cmc-sc.com`) |
| `role_based` | 1 (`cmcrecruiter@cmc-sc.com`) |
| nothing emitted (refusal) | 56 |

The three provider addresses:

- `frederick.bellamy@cmc-sc.com` — Frederick Bellamy MD, Conway Medical Center
- `ihor.melnytskyy@cmc-sc.com` — Ihor Melnytskyy MD, Conway Medical Center
- `farayi.mbuvah@cmc-sc.com` — Farayi Mbuvah MD, Conway Medical Center

All three are `pattern_confirmed`: `leadkit emails` derived `first.last` from **two** addresses actually
published on Conway Medical Center's own site (`/contact-us/`, `/careers/`). All three people are listed
on CMC's own provider directory. **Caveat to disclose to the recruiter:** directory listing proves
affiliation, not employment, and a third CMC address (`sgasque@cmc-sc.com`) is `flast`-shaped with no
attributable name — so a second format may coexist. Verify before a bulk send.

For every other domain the toolkit found **zero** known-good addresses and therefore emitted nothing.
That is the refusal working, not a gap in effort.

## 2. Pediatric signal — the honest answer

The user's actual question was pediatric experience, including *past* experience. The answer is a
negative, and it is a well-supported one:

- **0 of 60** carry a Pediatric Anesthesiology taxonomy in the NPI registry, in any position
  (primary or secondary). The 30 peds-taxonomy NPIs returned by the ZIP3 shards all practice
  outside the radius — **22 in Charleston SC, 2 in Wilmington NC**, the rest out of state.
- **0 of 60** graded STRONG or MODERATE from open scholarly sources. All 60 were queried against
  OpenAlex works, OpenAlex authors, and the ORCID public API. 26 returned literally nothing.
  Every pediatric-looking hit was traced to a same-name collision and rejected explicitly —
  e.g. the Boston Children's trail for "Patricia Grant" belongs to **P. Ellen Grant**, a pediatric
  neuroradiologist (ORCID 0000-0003-1005-4013), not the Pawleys Island anesthesiologist.
- **5 of 60** had a readable hospital bio. None showed a pediatric fellowship, a children's hospital,
  or a pediatric society. Two of the five (Grand Strand) render their training block client-side,
  so peds could be neither confirmed **nor ruled out** for them.

**`NONE_FOUND` != "no pediatric experience."** 54 of these 60 have no readable bio and no publication
record at all. This is a roster of non-publishing community anesthesiologists; scholarly sources are
the wrong instrument for them. The evidence is absent, not negative — a recruiter can still call.

Genuine byproduct: five identity-confirmed anesthesia employment trails from OpenAlex, none pediatric —
Miller Van Vliet (Univ. of Rochester Anesthesiology, 1997), Zechariah Harris (MGH Anesthesia/Critical
Care/Pain 2024; Wake Forest 2020-21), Richard Kline (NYU Langone 2011-2020, flagged UNCERTAIN — no
Conway SC link), Kevin Armstrong (Western University / London Health Sciences, flagged UNCERTAIN —
entirely Canadian), Lawrence Montalto (neuromodulation, 2025).

## 3. Territory: all 60 map to Myrtle Beach

Applied by haversine from each provider's practice-city centroid to Myrtle Beach (33.69, -78.89) vs
Greenville (34.85, -82.39). Greenville is 140-165 mi from every point inside a 50-mi Myrtle Beach
radius, so **no provider in this set maps to Greenville**. `result.csv` carries both distances and a
`territory_basis` string per row so the assignment is auditable rather than asserted.

## 4. Gaps and blocked sources

**Truncation.** `leadkit ingest` exited **4** on the first state-wide sweep — both Anesthesiology
queries saturated the registry's `skip=1000` ceiling. That 2,327-NPI count is **incomplete and is not
reported as a total anywhere.** It was partitioned by the ZIP3 prefixes `leadkit geo` returned, via
`postal_code=283*|284*|290*|294*|295*`. Every shard then paged out to a partial page; the Pediatric
Anesthesiology shards exited **0 / COMPLETE**. A combined ingest re-raised exit 4, which on inspection
is a **false positive**: peds-taxonomy NPIs are a subset of the Anesthesiology result, so those files
added zero new NPIs and tripped the "page added nothing new" repeat detector. Confirmed by ingesting
each taxonomy separately (exit 3 and exit 0).

**Blocked / unreadable (11 hosts).** Roughly 20 of the 60 sit behind three orgs that a static fetch
cannot read, and under the clamp there is no rung 4:

| Host | Wall |
|---|---|
| tidelandshealth.org | **403 on every path, including root.** No bot check was attempted or defeated. |
| mcleodhealth.org | `/physicians/` -> 195 KB, zero names. Client-rendered directory. |
| novanthealth.org | `/doctors` -> 18 KB JS shell, zero names. |
| dosher.org, crhealthcare.org | No provider directory exists at any readable path (404s). |
| seasidesurgerycenter.com | 403. |
| mygrandstrandhealth.com | Listing pages are a JS shell; profile pages render only `<title>`. **`physicians.xml` (299 URLs) was readable** and is the way in. |
| myrtlebeachanesthesia.com + 10 others | DNS NXDOMAIN — 10 of 12 probed independent anesthesia-group domains do not exist. |

**WebSearch was exhausted (200/200) before the org-directory subagents ran.** Every result above came
from direct HTTP fetches against guessed or sitemap-derived URLs. This is the single biggest depressor
of the match count: without search, name -> correct-org resolution failed for 54 of 60 people. That is
a budget artifact, not evidence those people lack bio pages.

**Single-source rows.** None. All 59 rows are `corroborated` — but read that carefully: corroboration
here means the person appeared in >=2 of the four input record files (registry, directory, email,
scholarly), and for 54 of them the second and third sources are *negative findings* (searched, found
nothing). It is not four independent confirmations of a contact.

**A rejected match, recorded on purpose.** `conwaymedicalcenter.com/providers/william-myers-md/` is
**W. Charles Myers, MD** — not the roster's William Myers, PA-C. Fuzzy slug matching proposed it; the
bio fetch killed it. Three further surname collisions were rejected the same way (Marie != Dwayne
Livigni, Curtis/Lacey != Kevin Armstrong, Andra != Raymond Collins).

## 5. Highest-value next step

Both hospital sitemaps are static and name-bearing — `mygrandstrandhealth.com/physicians.xml` (299 URLs)
and `conwaymedicalcenter.com/providers-sitemap.xml` (306). They are already downloaded to `pages/`.
Pulling all ~600 bios and fuzzy-matching offline needs **zero** search calls and would lift the
directory-match count well above 5. For pediatric history specifically, the productive probes are the
SC and NC medical board licensure files and the ABMS certification lookup — not scholarly databases.

## 6. The file

- **`result.csv`** — 59 rows, 38 columns. Every populated field carries a `*_source` column;
  every email carries `email_confidence` + `email_label` + `email_evidence_source`.
  **3 of 59 rows carry a real email. 59 of 59 carry a business phone.**
- `leads.csv` — the raw `leadkit csv` output before the peds/territory columns were appended.
- `merged.json`, `records/*.json` — one file per source, so corroboration stays countable.
- `raw/`, `raw2/`, `raw2a/`, `raw2b/` — verbatim NPI API responses. `pages/` — fetched HTML/XML.
- `log.jsonl` — 20 steps. `meta.json` — run metrics.
