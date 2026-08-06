# Round 2 — the pediatric channel, pushed hard

Condition B (open / browser). Branch = **QUALIFY** over the round-1B roster of 84.
Registry not re-fetched. Browser closed at the end.

## The answer to the question

**How many pediatric-experienced providers exist in the ring?**

Round 1 found **2** signals out of 84, both accidents of what a directory happened
to print. Reading **1,342 provider profiles across five org directories** this
round found **76 in-radius providers carrying a published pediatric signal** —
36 STRONG, 40 MODERATE — every one with a citation URL.

But the number that matters for the original ask is smaller and sharper:

> **In anaesthesia specifically, the ring contains exactly one pediatric
> anesthesiologist: Michelle D. Lee, MD.**

A facet count over McLeod's **entire 805-physician index** returns exactly one
provider with a "Pediatric Anesthesiology" specialty. Tidelands' 12
anesthesiologists: zero pediatric mentions. Grand Strand's 5: zero. Conway's 4
anesthesia/pain physicians: zero. That is 31 anesthesia providers read at profile
level across four systems, and one of them is peds.

Round 1 called Michelle Lee a directory hit. She now has a training record:

```
Michelle D. Lee, MD - McLeod Anesthesia Loris / McLeod Anesthesiology Seacoast
  Pediatric signal: STRONG
    Board Certification: Anesthesiology; Pediatric Anesthesiology
    Medical School:      2002 - Creighton University School of Medicine, Omaha, NE
                         2006 - University of Colorado Health Sciences Center, Denver, CO
    Residency:           2007 - Children's Hospital Colorado, Aurora, CO
    https://www.mcleodhealth.org/physician/michelle-d-lee/
  NPI taxonomy: no pediatric code. The subspecialty exists only here.
  Phone: (843) 716-7370 department (Loris) / (843) 390-8128 department (Seacoast)
```

## The channel that opened this round

Round 1B pulled McLeod's Algolia index and stopped there. The Algolia record
carries **no training fields at all** — which is why round 1 could only say
"the specialty string says Pediatric Anesthesiology".

Every one of the 805 Algolia records carries a populated `scheduling_url`
pointing at `/physician/<slug>/`. **Those pages publish Board Certification,
Medical School, Residency and Fellowship, and they are readable by plain curl.**
Round 1B never opened one. 262 were fetched this round (243 in-radius + all 29
anesthesiology); 157 publish a training block.

That is the marginal finding: the subspecialty lives one hop past the search
index, on a page nobody clicked.

## What each directory actually publishes

| Org | Access | Profiles read | Publishes training? | Peds signals | Emails |
|---|---|---|---|---|---|
| **McLeod Health** | rung 2 curl + Algolia browse | 262 of 805 indexed | **Yes** - Board Cert / Med School / Residency / Fellowship (157 of 262) | 7 in-radius | 0 |
| **Tidelands Health** | **rung 4** - hard 403 to curl, browser reads it | **443** (round 1B stopped at 301) | Yes for most specialties, **never for anesthesiology** | 25 in-radius | 0 |
| **Grand Strand (HCA)** | rung 2/3 - embedded `physicianData` JSON | 299 of 299 | Partly - school/residency/fellowship rows, **never a board-cert row** | 14 | 0 |
| **Conway Medical Center** | rung 2 curl | 304 of 305 | Yes, but **no board-cert field** - certs only in free-text bio | 25 kept after filtering | 0 |
| **OrthoSC** | rung 2 | 33 | Yes | 2 (after stripping a nav string that falsely matched all 33) | 0 |
| Novant Health | 404 on /find-a-doctor | 0 | - | - | - |
| MUSC Health | 1 page | 1 | - | 0 | - |

**1,342 profiles read. Zero clinician email addresses on any of them.**

### Three negatives worth as much as the positives

1. **Tidelands anesthesiology publishes no training block at all.** Not for one of
   the 12. Other Tidelands specialties get a full Medical Education / Residency /
   Fellowship / Board-certification block - verified on `heather-grabowski-do`.
   So NONE_FOUND for those 12 is a *publishing policy*, not a read on the people.
   They are the highest-value phone calls precisely because the record is silent.
2. **Grand Strand's `credentialsAndAccreditations` never carries a board
   certification.** 0 of 299. Board certification exists only as a bare
   `boardCertified` boolean with no board, no subspecialty, no year. A pediatric
   anesthesiology certificate is structurally invisible on that directory.
3. **Conway has no board-certification field either** - certs appear only if the
   free-text bio happens to name them (Mbuvah's does; Bellamy's one-line bio does).

Every NONE_FOUND row in the CSV now names which of these it is.

## Department phones - round 1B was right, the clamped sweep was wrong

`contact-channels.md` records a round-1 measurement of **zero department lines
across 8 org sites** and calls the department-phone prediction "falsified". That
generalisation does not hold. Measured this round:

- **Conway Medical Center publishes a full HTML phone directory** at
  `/phone-directory/`: **Anesthesia 843-347-8288 and 843-347-8352**, Surgical
  843-347-1596, OR Scheduling 843-234-5043, PACU 843-347-8189, Pediatrics unit
  843-347-8054, Nursery 843-347-8053.
- **McLeod publishes anesthesia practice lines**: (843) 716-7370 Loris,
  (843) 390-8128 Seacoast, (843) 777-8752 MRMC.
- **Tidelands publishes one**: 843-652-1190 - Tidelands Health Anesthesia.
- **Grand Strand publishes the contracted groups' lines**: (843) 692-1062
  TeamHealth Anesthesia, (843) 692-1061 Man In The Box Anesthesia. These ring the
  anesthesia group, not the 843-692-1000 facility switchboard.

**33 of 160 rows now carry a department line, up from 19 of 84.** The honest
statement: department numbers exist on *some* org sites and not others, and
finding them costs one fetch of `/phone-directory/` or `/contact` per org. The
clamped-sweep zero was a sampling artifact, not a property of hospitals.

## Reachability, stated honestly

```
160 people
  phone    97  (0 direct, 33 department, 64 practice switchboard)
  email     3  (3 pattern_confirmed on cmc-sc.com, 0 first_party_published)
  linkedin  0 verified, 160 search URLs provided
  63 rows have no published phone at all
```

The 3 emails carry over from round 1 and are `pattern_confirmed`, which per
`contact-channels.md` is ~91% accurate - a 9% implied bounce rate, 4x over the 2%
throttling ceiling. **Do not bulk-send them.** One at a time, by a human.

## Refusals and guards

- **Joshua R. Gore.** OrthoSC lists a "Joshua R. Gore, M.D." who is an
  **orthopedic surgeon**. The roster's Joshua R. Gore, MD is an anesthesiologist
  at McLeod Anesthesiology Seacoast. Same name, same metro, different people.
  Not merged. Same failure class as the Dveet/Deeran Patel case.
- **OrthoSC nav string.** "Pediatric Orthopedic Care" appears in OrthoSC's site
  navigation, so a naive text match graded all 33 providers pediatric. Two
  survived after stripping boilerplate.
- **Conway bio false positives.** 18 MODERATE hits came from bio text; those
  matching personal-life patterns ("his 3 children", "supporting the children in
  their...", "volunteered at his local YMCA") were dropped, not counted.
- **No email was invented.** 1,342 pages produced zero clinician addresses and
  the CSV says zero. Grand Strand's `xx@xxxx.xx` form placeholder was rejected.
- **LinkedIn was not automated.** 160 `linkedin_search_url` values, 0 scraped.
- **No CAPTCHA or bot check was defeated.** Tidelands' 403 was read with the
  browser at rung 4 - the documented escalation, not an evasion.

## Roster data-quality note

The round-1 roster of 84 contains duplicate people - Michelle D. Lee, Frederick
Bellamy, Joshua Gore, Olga Chrisman and Derek Horstemeyer each appear twice (once
from NPI, once from a directory) because the merge keys differed. Both copies are
kept and both now carry the same directory evidence, so "84" is closer to
**79 distinct people**. Flagged rather than silently collapsed.

## Files

- `result.csv` - 160 rows; `row_origin` separates the 84 round-1 roster rows from
  the 76 pediatric-signal rows added this round. `peds_citation` is populated on
  every STRONG and MODERATE.
- `raw/mcleod_live_physicians_ALL.json` - all 805 McLeod index records
- `raw/mcleod_profiles_full.json` - 262 McLeod profile pages with training blocks
- `raw/tidelands_r2_raw.json` - Tidelands 443-provider walk
- `records/grandstrand_r2.json`, `records/conway_ring_r2.json`
- `log.jsonl`, `meta.json`
