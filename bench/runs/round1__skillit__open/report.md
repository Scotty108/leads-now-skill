# Round 1 · skillit · condition OPEN (non-browser) — the enrichment boundary

**Branch: ENRICH.** The 72-person roster from `round1__skillit__clamped` was the frame; the registry
was not re-fetched. The question is not "who is there" but **how far free public sources carry a
clinician roster past a switchboard.**

**Constraint noted:** condition B, non-browser. Zero `mcp__playwright__*` calls — a shared browser
instance was being driven by another agent. Zero WebSearch — session budget exhausted (200/200).
All fetching was `curl`/`urllib` from Bash plus 6 `WebFetch` calls.

## Delivery gate

- `scripts/audit_list.py result.csv --retrieved 777 --in-scope 72` → **PASS** (every row sourced, tiered, unique).
- `scripts/email_pattern.py hygiene result.csv` → **exit 1, NOT SAFE TO BULK SEND**, projected 63.2%
  against a 2% ceiling. That is dominated by the 69 blanks; only the **2 `first_party_published`**
  rows clear the ceiling.

## Denominator and channel breakdown

```
72 people (in radius, unchanged from round 1)
  phone      72   0 direct, 0 department, 72 practice switchboard, 0 answering_service
  email       3   2 first_party_published, 1 pattern_confirmed, 69 none
  linkedin    0 verified, 72 search URLs provided
  peds        0 strong, 0 moderate, 72 none
confidence: unconfirmed = 72
```

Round 1: 72 phones, 0 emails, 0 LinkedIn. This run: emails **0 → 3**, department phones **0 → 0**.
Everything else is a measured zero.

## Where the boundary is

**The binding constraint is publication, not the APIs.** 69 of 72 have no affiliation-locked
publication, trial or grant anywhere. Community anaesthesiologists in a 50-mile coastal ring have no
public academic surface, so every academic channel is capped at the 3 who publish — and it reached
exactly those 3.

**The lock is the whole game.** 2,630 raw PubMed IDs and 339 author-name-matched affiliation records
collapsed to **3 people** under a strict lock (practice city, practice ZIP, or a distinctive
org/health-system phrase; state-only rejected). 336 were name collisions — UCSF, UW, Johns Hopkins,
Oxford, Mass General Brigham, Royal London, Macquarie, Kaiser Pasadena, Regenexx, Bassett.

### Two near-misses that are the real result

1. **Zechariah Charles Harris** returned Ann & Robert H. Lurie **Children's** Hospital of Chicago and
   MGH paediatric critical care — precisely the paediatric-experience signal this run was asked to
   find. The affiliation is Chicago, not the Grand Strand. Different person. Discarded; peds stays 0.
2. **"Patel D"** publishing from *Grand Strand Health, Myrtle Beach SC* passed the affiliation lock
   perfectly — right city, right hospital, right health system. It is **Dveet** Patel, an internal
   medicine resident, not roster member **Deeran** Patel. Caught only by comparing the full ForeName
   instead of the first initial. Six papers and a published address (`dveetpatel@gmail.com`) rejected.
   *Affiliation lock alone is not sufficient; it must be paired with full-forename identity.*

### Truncation, detected and repaired

39 of 72 PubMed author queries returned exactly `retmax=60` — truncated. Repaired with an
affiliation-restricted `esearch` (17 ring-city/health-system `[ad]` terms, `retmax=200`, none
saturated): 18 candidates → 7 author-level → **3 verified**. The repair added **0** new people, so
the ceiling hid nothing real. The unrepaired run could not have said that.

### Emails live in full text, and Europe PMC did not serve it

The 4 locked papers carry **zero** emails in their PubMed affiliation strings and zero in Europe PMC
`core` records. Europe PMC's own `fullTextXML` endpoint returned **404 on all four**, including the
one flagged `isOpenAccess=Y`. The same four fetched through **NCBI `efetch db=pmc`** returned every
corresponding-author address. Full text is where clinician emails live; on this sample the working
endpoint was PMC, not Europe PMC.

## What was found, per person

| Person | Lock | Source | Email | Tier |
|---|---|---|---|---|
| Jon D Halling | Grand Strand Medical Center, Myrtle Beach SC | PMC11249181 (2024) | Jon.Halling@hcahealthcare.com | `first_party_published` |
| David Redding Kingery | Grand Strand Regional Medical Center, Myrtle Beach SC | PMC10324711 (2023) | David.Kingery@hcahealthcare.com | `first_party_published` |
| Derek L Horstemeyer | Grand Strand Regional Medical Center, Myrtle Beach SC | PMC10327958 / PMC8890879 (2022–23) | derek.horstemeyer@hcahealthcare.com | `pattern_confirmed` — derived |

Horstemeyer published no address of his own; his papers carry a co-author's. His address was produced
by `scripts/email_pattern.py` from **5 observed `first.last@hcahealthcare.com` addresses (support
5/5)** — tool-produced, not typed. Two caveats ride on the row: ~91% accurate so ~9% implied bounce
(does not clear a 2% ceiling), and the domain is the **HCA facility he publishes from** while his NPI
employer is a private anaesthesia group — the multi-domain trap in `email-tradecraft.md`. One-at-a-
time human send only; never a sequence.

**Non-email win:** for these 3 the **workplace is now confirmed by a source that names the person**
(Grand Strand Regional Medical Center), where round 1 had only an NPI address-join to a group practice.

## Phones: still 72/72 practice, 0 department

Eight organisation sites were fetched for a service-line number better than a switchboard. What they
publish is switchboards: Conway Medical Center 843-347-7111, McLeod Seacoast 843-390-8100, McLeod
Loris 843-716-7000, Columbus Regional 910-642-8011, OrthoSC (843) 353-3460, Grand Strand only an
(844) Consult-A-Nurse line. Not one anaesthesiology department line exists on the public web for this
ring. Every phone stays `phone_type=practice`. **Department-phone yield: 0.**

## Sources that could not be read

| Source | Reason |
|---|---|
| `api.openalex.org` | HTTP 429 — *"Insufficient budget. This request costs $0.001 but you only have $0 remaining. Resets at midnight UTC"*, `retryAfter` 6268 s. Retried with polite UA + mailto; identical. **0 of 72 queries served.** |
| `tidelandshealth.org` | HTTP 403 to both curl (honest UA) and the agent fetcher |
| `novanthealth.org` (Brunswick) | 404 on the location path |
| `ambulatorycareanesthesia.com` | DNS does not resolve — the roster's **largest employer (20 of 72)** has no website |
| Europe PMC `fullTextXML` | 404 on all 4 locked PMIDs including the OA one |
| `mcp__playwright__*` | Deliberately unused (shared instance) — JS-only pages out of reach |
| WebSearch | Budget exhausted 200/200 — no open-web discovery layer |

**OpenAlex being metered is a substantive finding.** `references/contact-channels.md` names it as
step 1 of the email attack and calls it "free, no key". That is no longer reliably true. PubMed
E-utilities carried its load; PMC full text carried the part Europe PMC dropped.

## What this run could not establish, and the one action that resolves it

**Paediatric capability, for all 72.** No taxonomy, no locked publication, no trial, no grant, no
readable department page states that any of these anaesthesiologists works with children. The only
paediatric affiliation the literature surfaced belongs to a different person in Chicago.

The action that resolves it: **call the 72 published practice numbers.** Every one is sourced and
dialable, and a front desk answers the paediatric question in one sentence. Free public data is
exhausted on it — the remaining 69 have no public digital surface beyond their registry entry.

*Inherited defect, flagged not fixed:* the roster still carries 1 `PA-C` and 1 `CRNA` against a
physician request. It was the frame for this run, so it was preserved rather than silently trimmed.

## Files

`result.csv` (72 rows; round-1 columns preserved, 9 appended: `phone_type`, `linkedin_url`,
`linkedin_search_url`, `pub_affiliation_lock`, `pub_source_url`, `pub_years`, `affiliation_history`,
`channels_tried`, `channel_notes`) · `log.jsonl` (27 events) · `meta.json` · `work/` (raw API
responses, probe scripts, `email_pattern` evidence/pattern/apply trail)
