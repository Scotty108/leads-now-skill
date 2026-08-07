# Greenville SC territory — pediatric anesthesiologists, 50-mile ring

**Run:** round 3, skill `finding-leads`, condition B (open / browser available). Territory: **Greenville SC**, not Myrtle Beach.
**Gate:** `audit_list.py` -> **PASS** (every row sourced, tiered, unique). Full output in `audit.txt`.

## 1. The filter, restated

Physicians practising **pediatric anesthesiology** whose **practice location** (not mailing address) lies within
**50 miles of Greenville SC (34.8369, -82.3630)**. Enumerate the **parent** taxonomy (Anesthesiology) first, then
qualify the pediatric attribute from what sources actually say. Disqualifiers: practice location outside the ring,
non-physician credential, mailing-only address.

The ring **crosses three states** — SC, NC, GA — ZIP3 prefixes `280 281 287 288 291 293 296 305 306`.

## 2. Why this run exists

Every prior run in this benchmark enumerated only the Myrtle Beach ring and then reported "all -> Myrtle Beach,
0 -> Greenville". **That zero was an artefact of never searching Greenville.** This run enumerates Greenville the
same way, and the two territories turn out to have materially different population profiles.

## 3. The denominator

| Stage | Count |
|---|---|
| Retrieved from NPI registry across the 9 ZIP3 prefixes | **833** distinct providers (1,331 location rows) |
| CMS DAC (3,387,942 rows parsed) across the same prefixes | **680** distinct NPIs |
| NPI registry, inside the 50-mile radius | **426** |
| CMS DAC, inside the 50-mile radius | **281** (231 overlap, **50 net-new**) |
| **Union delivered** | **476** |
| Of those, physicians (MD/DO/MBBS) | **430** titled Anesthesiologist + **14** titled Pediatric Anesthesiologist |
| Non-physicians retained but downgraded | 6 CRNA, 1 AA, 25 credential-unresolved |
| **Pediatric-anaesthesia signal, physicians, in ring** | **25** (14 `confirmed`, 11 `probable`) |

Reported exactly: `unconfirmed=451, probable=11, confirmed=14`; `first_party_published=78, none_found=398`;
phone `465/476` (156 `department`, 309 `practice`, 11 none).

## 4. The headline: Greenville is not Myrtle Beach

| | Myrtle Beach (rounds 1-3) | **Greenville (this run)** |
|---|---|---|
| In-ring anesthesiology providers | 72 -> 120 | **476** |
| NPI `207LP3000X` peds-anaesthesia taxonomy in ring | **0** | **20** |
| Pediatric anesthesiologists, physicians, evidenced | **1** (Michelle D. Lee) | **25** (14 confirmed, 11 probable) |
| First-party published work emails | **4**, after ~1,700 profile pages + a 3.39M-row federal file across four rounds | **78**, from **one HTML page** |
| Named anaesthesia department phone lines | 33 of 160 (round 2B), 37 (round 3) | **10 distinct lines**, 156 rows labelled `department` |

The pediatric zero in Myrtle Beach was real. **It is not a property of the search — it is a property of that market.**
Greenville's peds-anaesthesia population is 20-25x larger and it is *visible in the registry itself*: ZIP3 296 alone
returns 23 providers filed under `Pediatric Anesthesiology`, where all nine Myrtle Beach prefixes returned 0.

## 5. The email ceiling broke — but not where the hypothesis said

The brief asked whether the literature/email channels dry in Myrtle Beach would open in an academic market.
Both halves were tested with stated denominators.

**Literature: hypothesis FALSIFIED.** Checked **81 of 426** (21 of 21 peds + the first 60 of 405 by surname), 162
NCBI calls. 20 of 21 peds return *some* PubMed record on a bare `Lastname F[au]` query — that is name collision,
not footprint. **10 of 21** survived the affiliation lock. **1 of 21** survived affiliation *and* full-forename locks
(Laura Leduc, PMID 32109313, *"Department of Anesthesiology, GHS Greenville Memorial Hospital, Greenville, USA"*),
and it has no PMC record, so no address. **Emails from literature: 0 of 81.** Statistically identical to the
Myrtle Beach community baseline. The locks did real work — 397 author rows rejected on affiliation, 221 on forename;
`Greenville[ad]` was pulling in **Greenville, NORTH CAROLINA** (East Carolina University). OpenAlex still HTTP 429.

**Org channel: the ceiling broke through a different door.** Because these physicians hold **USC School of Medicine
Greenville clinical-faculty appointments**, the medical school publishes their work email in an ungated,
server-rendered HTML table — no JS, no auth, no bot wall, plain `curl`:

`https://sc.edu/study/colleges_schools/medicine_greenville/about/faculty/facultydir/index.php`
-> 1,211,791 bytes, 1,457 faculty rows, 1,432 with a `mailto:`, 1,369 `@prismahealth.org`, **88 rows are the
Anesthesiology department**, **78 matched to roster NPIs** and tiered `first_party_published`.

**Deciding numbers: 0 emails from literature (n=81) vs 78 from one faculty directory page (n=426)**, against 4 from
~1,700 hospital profile pages at Myrtle Beach. In an academic market the lever is the **medical school's faculty
directory**, not PubMed. It is doubly true here because **"Greenville Anesthesiology PA" has no website at all**
(`greenvilleanesthesiology.com` is NXDOMAIN) — the medical school page *is* that group's de-facto public directory.

All 78 are **published**, not derived. **Zero addresses were inferred and zero patterns were applied.** These are the
only tier that clears a 2% bounce ceiling; nothing in this file needs the pattern-confidence caveat because nothing
was patterned.

## 6. Three rejections that a looser run would have shipped

1. **Heather Ilene Blomeley, MD — NPI 1073620704.** Carries the `207LP3000X` pediatric-anaesthesia taxonomy and a
   Mill Spring NC 28756 postal code that placed her **36.9 miles inside the ring**. Her only NPI **LOCATION** address
   is `LRMC DEPARTMENT OF ANESTHESIOLOGY, CMR 402, APO AE` — Landstuhl Regional Medical Center, **Germany**. Mill
   Spring is her **MAILING** address. **Rejected.** A mailing address is not a practice location, and this one had
   already passed a geo filter.
2. **Jenna Elizabeth Zauk, MD — NPI 1083077648.** Listed by Prisma's own directory under Pediatric Anesthesiology
   *with* ABA pediatric board certification and a Baylor peds-anaesthesia fellowship — the strongest evidence in the
   set. Prisma publishes **no location** for her; her NPI LOCATION is `5 Richland Medical Park Dr, COLUMBIA SC 29203`
   (~100 mi, the Midlands market), and NPI flags her as a trainee. **Rejected from the Greenville ring.**
   A directory listing is not a practice location either.
3. **Crystal Marie Cmeyla.** Listed by Prisma under Pediatric Anesthesiology at 701 Grove Rd (in ring). NPI taxonomy
   is `Pediatrics` + `Nurse Practitioner, Family`; credential **FNP**. Retained with the location verified,
   **downgraded to `unconfirmed`** with the reason on the row — a request for physicians does not accept an NP
   delivered as one.

## 7. What each source contributed

| Source | Rung | Yield |
|---|---|---|
| NPI registry (`npi_query.py` plan/parse) | API | 833 retrieved, 426 in ring, **20 peds-taxonomy** |
| CMS DAC, 3.39M rows | federal filing | 281 in ring, **50 net-new**, med_sch/grd_yr meaningful on 508 of 680 |
| Prisma Health / Kyruus directory (`doctors.prismahealth.org`) | browser (rung 4) | **132 anesthesiology, 14 peds**, board certs + fellowships + **3 peds signals NPI taxonomy does not carry** (Bracale, Vana, Gonzalez) |
| USC SOM Greenville faculty directory | plain fetch (rung 3) | **78 published emails**, 88 anaesthesia faculty rows |
| PubMed / efetch db=pmc | API | **0 emails**, 1 affiliation+forename-locked paper of 81 checked |
| ABA diplomate directory (`directoryreactapi.theaba.org`) | certifying body | **18 peds-certified of 274** ring diplomates; **12 practice-confirmed in ring**, 9 rejected as practising elsewhere, 2 unresolved |

**CMS DAC pediatric vocabulary — structural zero, positive control passed.** The complete vocabulary is 101 `pri_spec`
+ 81 `sec_spec` values; every value containing "ANESTH" is `ANESTHESIOLOGY`, `ANESTHESIOLOGY ASSISTANT`, `CRNA`,
`DENTAL ANESTHESIOLOGY`. **No pediatric-anaesthesia concept exists in the file at all.** The control: **380,847 rows
have `sec_spec_1` populated**, so the field renders and the absence is real. Peds targeting must come from NPPES
taxonomy or ABA certification, never from this file. This reproduces the round-3-clamped finding on a second market.

Two corrections to the brief, measured: the endpoint `data.cms.gov/data-api/v1/dataset/mj5m-pzi6/data` **404s**
("The requested dataset cannot be found") — `mj5m-pzi6` is a DKAN id. The working path is
`https://data.cms.gov/provider-data/api/1/datastore/query/mj5m-pzi6/0`, and it caps at `limit<5000`; the 840 MB bulk
distribution was pulled instead and parsed to **3,387,942 rows = the API-reported count exactly**, with four live-API
shard cross-checks agreeing (SC 1021, NC 2168, GA 2155, SC-296 274). No shard hit a cap.

## 8. Sources that could not be read

| Host | Status |
|---|---|
| `prismahealth.org`, `doctors.prismahealth.org` | HTTP 200 but a 1,155-byte **Imperva/Incapsula** interstitial to plain `curl`. Read with the browser; **no CAPTCHA was presented and none was defeated.** |
| `greenvilleanesthesiology.com` | **NXDOMAIN** — the group that employs ~190 of the ring has no website |
| `www.ghs.org` | NXDOMAIN (rebranded to Prisma) |
| `api.openalex.org` | HTTP 429, "Insufficient budget" — unchanged from round 1B |
| SC LLR, NC Medical Board | reCAPTCHA. Out of scope; a browser does not change that |
| Shriners Children's Greenville | loads (478 KB) but publishes **0 emails**; department line 864-271-3444 recovered |
| LinkedIn | not automated, by rule. No `linkedin_url` claimed for any row |

## 9. The ABA diplomate directory — the certifying body settles it

The ABA sweep landed after the first cut of this report and is now merged. It is the only source that can
*prove* a pediatric certification rather than repeat someone else's claim about one.

**Denominator: 18 peds-certified diplomates out of 274 ABA diplomates with a mailing address in the ring**
(257 of the 274 hold the parent Anesthesiology certificate). Across the three ring states: **SC 53, NC 117, GA 115**
peds-certified.

- **12 practice-confirmed in the ring**, every one at Prisma Health University Medical Group, Greenville:
  Bebic, Bracale, Doar, Gonzalez, Knox, Leduc, Moore, Shah, Stowe, Vana, **Walls**, Wharton.
- **9 rejected for practising elsewhere:** Dalton (Columbia SC ~95 mi), Blomeley (Augusta GA / APO AE Landstuhl —
  **independently reproducing this run's own rejection from a different source**), Duncan (Iowa City IA),
  Wittman (Grand Rapids MI / Louisville KY / Buffalo NY; her Arden NC address is a **residence**), Bendel
  (Pittsburgh PA), and **Schnepper, Mueller, Perhac, Barton** — all four at Mission Health, **Asheville NC, 53.5 mi**.
- **2 unresolved, and they are different problems:** **Steven Samoya** is peds-certified 2024 but ABA itself flags him
  *"Certified – Not Clinically Active"* with no current Medicare enrollment; **Bradley Stone**'s NPPES record was last
  updated **2007** and his ABA mailing address is the 53.5-mile Asheville cluster. Both are carried as `probable`
  with the specific reason on the row, not merged into one label.

**The certifying body moved 7 rows and added one person no other source could have delivered:**

- **Richard Frederick Knox** — `probable` (NPI self-report only) -> **`confirmed`**, ABA peds-certified 2016.
- **Sara Lathem Walls, MD — NPI 1669764742 — the single best catch of the run.** Her NPPES **LOCATION** is
  *2200 Childrens Way, Nashville TN* and has not been touched since **2018**, so the NPI registry places her **outside
  the ring entirely**; her NPPES *mailing* address is Greenville, which the mailing rule forbids using. She entered this
  roster **only** through the CMS DAC current Medicare enrollment (*Prisma Health University Medical Group, 67 Creekside
  Park Ct, Greenville*), where she sat as `unconfirmed` because neither NPI taxonomy nor Prisma's public directory lists
  her under pediatrics. **ABA certified her in Pediatric Anesthesiology in 2017.** She is a confirmed pediatric
  anesthesiologist in the ring that NPI alone rejects, the hospital directory omits, and only the
  CMS-filing + certifying-body pair recovers.
- Plus Stowe, Bracale, Wharton, Gonzalez, Moore, Doar, Vana, Shah, Bebic, Leduc upgraded from directory-quoted to
  body-verified certification years.

**Two API traps, both recorded.** The brief's warning that `StateId` is a GUID rather than an integer is **necessary
but not sufficient**: with the *correct* SC GUID the advanced search still returned `[]` at HTTP 200, because the API
treats an empty string `""` as a **literal filter value**. Reading `main.js` showed the client sends JSON `null`, never
`""`. With nulls the identical query returned **860**. That is a second silent wrong-key zero of exactly the class this
skill exists to catch. **Truncation:** the NC and GA parent-certificate (513) sweeps each returned **exactly 1000** and
were therefore never used as denominators; all three peds (519) sweeps came in well under the cap (53 / 117 / 115), so
peds enumeration is complete, and the ring denominator was rebuilt from per-city queries (largest single result 106).
Two independent enumeration paths agree on 18 in-ring peds-certified.

**Name disambiguation did real work:** "Jessica Gonzalez" returns 149 NPPES hits and "John Moore" 185. The correct one
is **JOHN DAVIS** Moore (NPI 1164491379, Greenville) — **not** JOHN DAVID Moore (NPI 1396731774), a different
anesthesiologist in St. Louis. Likewise BRADLEY ALLEN Stone is not BRADLEY JARRETT Stone (Little Rock AR).

### What is still open

**The 53.5-mile Asheville cluster is the one judgement call left.** Four peds-certified anesthesiologists sit at Mission
Health, 3.5 miles outside a hard 50-mile ring. They are classified `PRACTICE_ELSEWHERE` here because the brief said 50
miles. **If the radius is soft, the in-ring peds count goes from 12 to 16.** That is a business decision, not a data one.

**Also unresolved:** 25 rows have no parseable credential, and 173 of 426 NPI rows resolved to no organization at their
address. `7 Independence Pt Ste 300` (120 individuals) and `67 Creekside Park Ct` (70) are **group/billing addresses**,
not reachable practice sites — the script flags them, and the `department` phone on those rows is the right thing to
dial, not the street address.

**One process defect worth recording:** the ABA subagent and this agent both wrote `build.py` into the shared working
directory, and the subagent's file silently replaced this run's roster builder. Caught because a rebuild printed 23 rows
instead of 476. The builder was reconstructed as `build_roster.py` and the merge re-run. **A shared scratch directory
needs namespaced filenames**; nothing in the delivered CSV was affected, but the collision was invisible until a count
disagreed.

## 10. How to use the file

`result.csv` — 476 rows, columns per `assets/output_template.csv` plus `phone_type`.

- **Start with the 14 `confirmed`** — 12 cite the **ABA diplomate directory** directly, with a certification year and a
  practice address cross-checked into the ring; the other 2 cite a named pediatric-anaesthesia fellowship on a Prisma
  profile URL you can open.
- **Then the 11 `probable`** — pediatric attribute self-reported to NPI only, or ABA-certified with an unresolved
  practice status (Samoya is flagged *Not Clinically Active* by the ABA itself; Stone's NPPES record is 19 years stale).
  `probable` means one source states the narrow attribute and a second has not confirmed it.
- **78 rows carry a `first_party_published` email**; 12 of them are in the peds cohort — including 11 of the 14 `confirmed`. Nothing was derived, so
  nothing needs the derived-address bounce warning.
- **`phone_type` matters.** 156 `department` rows ring a named anaesthesia service line. 309 `practice` rows ring a
  switchboard. Do not read 465 phones as 465 people reached.
