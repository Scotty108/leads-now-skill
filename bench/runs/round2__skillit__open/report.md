# Round 2, Condition B (OPEN) — pediatric channel, reproduced and extended

**Audit gate: PASS** (`audit_list.py result.csv --retrieved 1708 --in-scope 108`) — every row sourced, tiered, unique.

## 1. The filter, restated

Anesthesiologists practising within 50 miles of Myrtle Beach, SC, with a route to reach them, and
specifically: which of them are pediatric-capable. Starting frame was the 77-person NPI roster from
`round2__skillit__clamped/result.csv` (not re-fetched).

## 2. Denominator

| | Count |
|---|---|
| Directory profile records read (4 systems) | **1,708** |
| McLeod index recovered | 805 of 805 |
| Rows delivered | **108** (77 roster + 31 directory-discovered anesthesia providers) |
| With a phone | 108 (100%) — 30 `department`, 78 `practice`, 0 `direct` |
| With an email | 2 (both `observed`, first-party published in PMC full text) |
| Pediatric signal across all 1,708 profiles | **89** (87 strong, 2 moderate) |
| Pediatric **anesthesiologists** | **1** |

## 3. The key move, independently verified

The index is a pointer, not the record — confirmed and pushed further.

McLeod's Algolia records (app `JUNR3SUCF2`, index `live_physicians`, public search-only key read
from `/search-physician-finder/` server HTML) carry **no training fields at all**. Every record
carries `scheduling_url` -> `/physician/<slug>/`, and those pages publish `<h6>Board
Certification:</h6>`, `Medical School`, `Residency`, `Fellowship` to a plain curl.

Reproduced the headline finding from the record itself:

> **Michelle D. Lee, MD** — *Board Certification: Anesthesiology; Pediatric Anesthesiology.*
> Residency 2007, Children's Hospital Colorado. Two anesthesia department lines:
> McLeod Anesthesia – Loris (843) 716-7370 and McLeod Anesthesiology – Seacoast (843) 390-8128.
> `https://www.mcleodhealth.org/physician/michelle-d-lee/`

**Extension: 89 pediatric signals, not 79.** McLeod 39, Conway 26, Tidelands 14, **Grand Strand 10**.
Grand Strand contributed zero on the first pass because its `physicianData` blob keys the fields
`providerSpecialties` / `providerLocations`, not `specialties` / `practiceLocations`. Reading the
right keys also exposed a per-specialty `boardCertified` boolean.

## 4. Truncation is recursive — one level deeper than documented

The reference warns that `nbHits: 805` with `nbPages: 1` silently returns 100 of 805. True, and the
fix (partition by specialty) is **itself truncated**:

- Blind browse: 100 of 805
- Specialty partition: 785 — but `Family Medicine` reported 161 and returned 100, `Primary Care`
  reported 132 and returned 100
- Practice partition: 804
- Gender sub-partition + a-z letter sweep: **805 of 805**

Every partition must re-check its own reported total against what it received. One partition level
is not enough.

## 5. Silence is not absence — which kind of NONE_FOUND

Field-publication census, measured per system:

| System | Profiles | Board Cert | Residency | Fellowship | Med School / Education |
|---|---|---|---|---|---|
| McLeod Health | 805 | 357 (+24 alt) | 446 | 188 | 476 |
| Conway Medical Center | 303 | **258** | 234 | 302 | 253 |
| Tidelands Health | 301 | 0 | 195 | 83 | 273 |
| Grand Strand Health | 299 | 0 (boolean only) | 141 | 76 | 48 |

Every row carries a `none_found_kind` of `checked_and_absent`, `unpublishable`, or
`no_directory_record`.

### Three corrections in the reference are falsified by measurement

1. **"Tidelands publishes no training block for any of its 12 anesthesiologists."** False.
   **11 of 12 publish** Education/Residency/Fellowship in `#profile-info-education`. Only
   William Comeau, MD has no block. So those 11 are `checked_and_absent`, not `unpublishable` —
   the "highest-value calls because the record is silent" reading applies to **one** person, not
   twelve. Tidelands publishes no *board certification* for anyone, which is the real gap.
2. **"Conway has no board-certification field."** False. **258 of 303** Conway profiles publish
   `Board Certified in <specialty>` inside `div.providerbiowrap`.
3. **"Email: still zero, now from 1,342 pages."** False. **McLeod publishes 15 first-party
   clinician addresses** in an `Email:` field on profile pages (e.g.
   `logan.doriety@mcleodhealth.org`), establishing `first.last@mcleodhealth.org` with 15
   agreeing observations.

Confirmed as stated: Grand Strand publishes no board-certification string in 299 profiles.

## 6. Chrome stripping, enforced

Matched only inside record structures — McLeod `<h6>/<p>` pairs scoped to `div.doctor-right`,
Grand Strand `credentialsAndAccreditations` + `providerSpecialties`, Conway `*wrap` divs, Tidelands
`#profile-info-education`. **9 profiles mention a pediatric term only in free-text bio and were
excluded.** The control worked: McLeod's nav carries a `Residency` link on all 805 pages, and a
whole-page match would have graded every one of them as having residency training.

## 7. Emails: the pattern was found and deliberately not applied

A 15-observation `first.last@mcleodhealth.org` pattern is far past `pattern_confirmed`. **It was
applied to zero people.** All 15 observed addresses belong to providers with
`mcLeod_physician_associates: false` (pharmacy staff), and McLeod's anesthesiologists are *also*
`false` — a contracted anesthesia group, not McLeod employees. Employment unverified means the
pattern does not transfer.

**One defect found and repaired in the inherited roster.** `derek.horstemeyer@hcahealthcare.com`
arrived labelled `pattern_confirmed` and sourced to PMC10327958. `efetch db=pmc` on that article
publishes only `alex.roberts@hcahealthcare.com` — the address was derived, not published, and his
org is *Man In The Box Anesthesia*, not HCA. **Withheld**
(`email_status=withheld_employment_unverified`).

Also demoted 5 rows from `probable` to `unconfirmed`: they are plainly anesthesiologists, but the
narrow attribute the user asked for (pediatric) is unproven, and `confidence` scores the full
description.

## 8. Department phones exist, and the phone-directory page is a distinct artifact

**30 of 108 rows now carry a department line, up from 0.** Conway publishes a 106-line
`/phone-directory/` HTML table — *note it 301-redirects to `/patients-visitors/phone-directory/`,
which is why a plain fetch of the documented URL returns nothing.* It yields **Anesthesia
843-347-8288 and 843-347-8352**, plus Recovery Room 843-347-8189, OR Scheduling 843-234-5043,
Pre-Admission Testing 843-347-1585. McLeod department lines come from the anesthesia-named practice
records inside the index payload.

## 9. Sources that resisted

| Host | Wall | Resolution |
|---|---|---|
| tidelandshealth.org | 403 to plain fetch (bot fingerprinting) | Rung 4 browser, same-origin fetch — **301/301 profiles read** |
| conwaymedicalcenter.com/phone-directory/ | 301 redirect | `curl -L` |
| conwaymedicalcenter.com | 2 of 306 sitemap URLs failed | 304 parsed; 2 unread |

No bot check was defeated and LinkedIn was not automated — 108 `linkedin_search_url` values are
emitted for a human to click.

## 10. What this run could not establish

Whether McLeod's and Tidelands' anesthesiologists are employees or contractors. That single fact
gates a 15-observation email pattern across the largest system in the ring. **One call to McLeod
Anesthesia – Loris (843) 716-7370 asking who employs the anesthesia group would resolve it** and
would convert the roster's largest cohort from phone-only to email-reachable.

**Phone remains the deliverable channel.** 108 of 108 have one; 30 of those ring the anesthesia
department rather than a hospital switchboard.
