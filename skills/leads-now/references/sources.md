# Where to look, by vertical

Search engines are the worst way to find people and the best way to find
**organizations**. Use them for Phase 2, then go to the registry or directory
for Phase 3. A registry gives you a canonical name, a specialty and a location;
a search result gives you a press release from 2019.

## Healthcare / clinical

The strongest vertical for this skill, because registration is mandatory and
public.

| Source | What it gives | Notes |
|---|---|---|
| **NPI Registry** (`npiregistry.cms.hhs.gov`) | Every US clinician: name, specialty taxonomy, practice address, NPI | Free JSON API, no key. Authoritative for name + specialty. No email. |
| **State license lookup** | License status, disciplinary history | One per state; search `"<state> medical board license verification"` |
| Hospital "Find a Doctor" | Title, department, bio, headshot, sometimes direct email | Often JS-rendered or paginated |
| Specialty societies | Member directories (ASA, AAP, ACS…) | Frequently members-only; the public officer list is still useful |
| `doximity.com`, `healthgrades.com` | Cross-reference for name/specialty | Aggregators — corroboration only, never the sole source |

**NPI is the cross-reference of choice.** Query by specialty + state, then
filter by distance. Its taxonomy is precise: "Anesthesiology - Pediatric" is a
distinct code from "Anesthesiology", so a specialty search actually means
something.

## B2B / SaaS

| Source | What it gives |
|---|---|
| Company `/about`, `/team`, `/leadership` | Names + titles, highest trust |
| Careers page | Hiring signal, and often the recruiter's own address |
| Press releases / newsroom | Named executives with quotes, and email formats |
| Crunchbase / funding news | Firmographics, round, investors |
| Conference speaker pages | Name, title, org — and usually current |
| Podcast guest pages | Same, plus they are already public-facing |

## Where email formats hide

Before concluding a domain has no known address, check:

1. `/contact`, `/press`, `/media`, `/legal` pages
2. PDFs — press kits and investor decks leak `firstname.lastname@` constantly
3. Job postings ("send your resume to …")
4. WHOIS for smaller orgs
5. GitHub commit history for technical orgs

One confirmed address unlocks the whole domain. It is worth five minutes.

## What not to use

- **Scraped consumer databases** — out of scope, and a compliance problem.
- **Anything behind a login you agreed not to scrape.** Read the terms.
- **Personal social profiles** for personal contact details. Business contact
  data at a business address is the line this skill stays on.
- **Paid aggregators you have not paid for.** If a preview shows a masked
  email, that is not a resolution — leave it blank.
