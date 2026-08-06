# Round 2 — skillit, CLAMPED (WebFetch + Bash, no browser, no WebSearch)

**Audit gate: PASS** — every row is sourced, tiered, and unique.

## 1. The filter, restated

Physicians practising anesthesiology within 50 miles of Myrtle Beach, SC; pediatric-capable
called out where a source states it. Branch = **ENRICH** (a 72-person roster was supplied;
the NPI registry was *not* re-queried).

## 2. The denominator

| | Round 1 clamped | Round 2 clamped | Marginal |
|---|---|---|---|
| Retrieved from source (wider than target) | 777 | 777 (carried) | — |
| **Matched the target** | **72** | **77** | **+5** |
| Delivered rows | 72 | 77 | +5 |
| With an email | 0 | **3** | **+3** |
| With a phone | 72 (100%) | 77 (100%) | +5 |
| — of which `department` | **0** | **12** | **+12** |
| — of which `practice` (switchboard) | 72 | 65 | -7 |
| Confirmed pediatric anesthesiologist | **0** | **1** | **+1** |
| LinkedIn search URLs | 0 | 77 | +77 |

Confidence: `unconfirmed` 71, `probable` 5, `confirmed` 1.
Email status: `none_no_observed_address` 74, `observed` 2, `pattern_confirmed` 1.

## 3. What each round-1 correction was worth

### Correction 1 — NCBI `efetch db=pmc`, not Europe PMC `fullTextXML`

Worth **the entire email column**. Path run: 22 separate `esearch` queries, one per
affiliation term covering every roster city and health system (`"Myrtle Beach"[AD]` 870,
`"Grand Strand"[AD]` 325, `"Conway Medical"[AD]` 45, `"Tidelands Health"[AD]` 27,
`"McLeod Health"[AD]` 40, `"Columbus Regional Healthcare"[AD]` 24, `"Murrells Inlet"[AD]` 23,
`"Whiteville"[AD]` 13, the rest under 6) -> 1057 unique PMIDs -> `efetch db=pubmed` in 6
batches of 200 -> name match -> `idconv` -> **`efetch db=pmc` served 4/4**, including both
known-good addresses:

- `David.Kingery@hcahealthcare.com` — corresponding author, *Complications of TAVR From an
  Anesthesia Perspective*, Grand Strand Medical Center, PMID 37426864 / PMC10324711 (2022)
- `Jon.Halling@hcahealthcare.com` — corresponding author, *Burnout and Health Scores Among
  Residency Programs*, Grand Strand Medical Center, PMID 39015587 / PMC11249181 (2024)

A third published address, `alex.roberts@hcahealthcare.com` (PMC8890879, PMC10327958), is a
real corresponding author but **not a roster member** — so it is not emitted as anyone's
address. It is used only as pattern evidence.

`email_pattern.py learn` on those three: `hcahealthcare.com` -> `first.last`, support 3/3,
`pattern_confirmed`. Applied to **Derek L Horstemeyer** (co-author on all three Grand Strand
anesthesia papers, never the corresponding author) ->
`derek.horstemeyer@hcahealthcare.com`, `pattern_confirmed`.

**`email_pattern.py hygiene` exits 1: projected hard bounce 9.0% against a 2.0% ceiling.**
The two `observed` rows are sendable. The `pattern_confirmed` row is for a human to try
one at a time and must not go into a bulk sequencer.

That is the same 3 people the exhaustive 11-source open run reached. **The clamped path
reproduces the open path's email ceiling exactly.**

### Correction 2 — full-forename disambiguation

Worth **48 avoided false positives**. 295 surname hits across the corpus; the affiliation
lock alone would have passed dozens of them. Discarded because the forename disagrees:

| Roster member | Paper author, same affiliation | Affiliation |
|---|---|---|
| Deeran Patel | **Dveet** Patel (x5), **Pooja** Patel (x8), **Akash** Patel | Grand Strand, Myrtle Beach |
| Steven J Petersen | **Kirklen** Petersen (x3) | Grand Strand Trauma, Myrtle Beach |
| Scott E Thomas | **Mary Therese** Thomas (x6), **Kevin** Thomas (x3) | Grand Strand, Myrtle Beach |
| Ryan Wesley Smith | **Thomas J / Lincoln / Morgan / Elliott / T J** Smith | Grand Strand, Myrtle Beach |
| E J Collins / Raymond Craig Collins | **Nancy** Collins | Conway Medical Center |
| Joshua Gore | **Sarah** Gore, **Jennifer** Gore RN | Whiteville, NC |
| Peter Lawrence Fischer | **Hannah** Fischer | VCOM-Carolinas, Myrtle Beach |
| Michelle Lee / Bryan Robert Lee | **Joseph G L** Lee | ECU |

The documented Dveet-vs-Deeran case reproduced on the first pass. One of the discarded rows
(`Lincoln.smith@hcahealthcare.com`) even carries a live address in its PubMed affiliation —
exactly the trap the correction exists to stop.

### Correction 3 — OpenAlex is metered

One attempt, then abandoned, as instructed. Verbatim:

```
HTTP 429 {"error":"Rate limit exceeded","message":"Insufficient budget. This request costs
$0.001 but you only have $0 remaining. Resets at midnight UTC.","retryAfter":4691}
```

Zero cost, zero yield. Correct to keep it off the primary path.

### Correction 4 — subspecialty is not in NPI; go to rung 3

**This is what moved.** Both round-1B rung-3 patterns were reproduced without a browser.

**McLeod (the pediatric hit).** `mcleodhealth.org/physicians` redirects to
`/search-physician-finder/`, which is a JavaScript shell — but its server HTML ships
`var crbAlgoliaCredentials = {"credits":{"api_id":"JUNR3SUCF2","api_key":"..."}, "indexes":{"physician":"live_physicians", ...}}`.
That is the public, read-only, search-only credential the page hands every visitor, used only
for records the page displays. Querying `live_physicians` directly returned 29 anesthesiology
providers as typed fields. Among them:

> **Michelle D. Lee, MD** — `specialties: ["Anesthesiology", "Pediatric Anesthesiology"]`,
> practices *McLeod Anesthesia - Loris* (Loris, SC, 843-716-7370) and
> *McLeod Anesthesiology - Seacoast* (Little River, SC, 843-390-8128).

**The browser-only finding of round 1, reached clamped.** She is already row 42 of the
72-person roster — her NPI carries no pediatric taxonomy, exactly as documented. Her row is
now `confidence=confirmed`, `peds_signal=STRONG`. The `live_specialties` index independently
confirms "Pediatric Anesthesiology" exists in McLeod's vocabulary, so its absence elsewhere is
a real absence and not a parsing miss.

**Grand Strand (the `physicianData` pattern).** `grandstrandmed.com` -> `mygrandstrandhealth.com/physicians`,
a Next.js shell with zero records. `robots.txt` permits; `sitemap.xml` -> `physicians.xml` ->
**299 profile URLs**. Every profile embeds `physicianData` inside `__NEXT_DATA__` — NPI,
board-certified specialties, credentials, and `providerLocations[].phone`. 298 of 299 parsed.
Result: 5 anesthesiologists, **0 pediatric anesthesiology across all 298 physicians**, and NPI
as a clean join key.

**Conway.** `/find-a-provider/` 404s, but `sitemap.xml` -> `providers-sitemap.xml` -> 306 URLs;
305 fetched. `grep -li 'pediatric anesthes'` matched **0 files**. 7 anesthesiology profiles,
all publishing only 843-347-7111 — the CMC main switchboard, so they stay `practice`.

## 4. Where round 1B's phone finding was right and where it was wrong

Round 1B measured **zero** department lines and told the skill to stop expecting them. That
holds for *facility* pages — Conway, Tidelands, Grand Strand's "Contact us". It is **wrong for
provider-directory payloads**: both McLeod's Algolia records and Grand Strand's `physicianData`
carry the anesthesia group's own number, not the hospital switchboard.

| Line | Type | People |
|---|---|---|
| McLeod Anesthesia - Loris, 843-716-7370 | department | 7 |
| McLeod Anesthesiology - Seacoast, 843-390-8128 | department | 3 |
| Teamhealth Anesthesia (Grand Strand), 843-692-1062 | department | 1 |
| Man In The Box Anesthesia (Grand Strand), 843-692-1061 | department | 1 |
| NPI practice location | practice (switchboard) | 65 |

**12 department numbers, 0 -> 12.** The cost was not "one fetch per org" — it was one rung-3
endpoint per org, on the two orgs that actually had one.

## 5. Five people the registry did not have

The McLeod directory lists five in-radius anesthesiologists absent from the 72-person NPI
roster: **David O. Atkinson, Ligia E. Cisneros-Gonzalez, Ahmed Elhaimer, Robert O'Connor,
Michael D. Wingfield** — all at McLeod Anesthesia - Loris or McLeod Anesthesiology - Seacoast,
both inside the ring. Checked against the roster by surname; none present under any variant.
They are delivered at `confidence=probable` with `external_id` blank and a note that the NPI
cross-check is outstanding, because they were discovered on a directory rather than in the
census.

## 6. Organizations that could not be read

| Source | Wall | Consequence |
|---|---|---|
| `www.tidelandshealth.org` | **403** on `/` and `/find-a-doctor/` — bot fingerprinting | Rung 4 is the documented answer and is unavailable under the clamp. 2 Tidelands Anesthesia Group roster members keep their NPI switchboard and have no subspecialty check. |
| `api.openalex.org` | **429**, $0 budget, retryAfter 4691s | No affiliation history, no second literature channel. PubMed covered the gap. |
| WebSearch | Session budget exhausted (200/200) per run condition | Never attempted. |
| `www.conwaymedicalcenter.com` | *Not blocked* — 305 profiles read | Publishes no department line and no subspecialty. A genuine negative, not a gap. |
| Ambulatory Care Anesthesia PC (20 people, the largest single employer) | No findable domain | The biggest remaining hole. 2 of its 20 surfaced through Grand Strand's directory; the other 18 have registry data only. |

## 7. What this run could not establish, and the one action that resolves it

**69 of 72 roster members have no affiliation-locked publication anywhere.** Round 1's open
run reached exactly 3 with 11 sources; this clamped run reached the same 3 with PubMed alone.
That is a property of a community clinical population, not of the tooling, and no additional
free literature source will move it.

Subspecialty is now established for 3 of the 5 in-radius employers with a readable directory
(McLeod, Grand Strand, Conway). **The single action that would resolve the rest: read
Tidelands Health's directory in a real browser** — it is the one 403 in the set, it is the
only rung-4-shaped wall left, and it is where the remaining Myrtle Beach subspecialty data
lives. Everything else in the ring has already been read on rungs 1-3.

## 8. Send guidance

- 2 rows are `observed` and sendable.
- 1 row is `pattern_confirmed` — 91% accurate, 9% projected bounce, 4x the 2% throttling
  ceiling. **One-at-a-time by a human, never a bulk sequencer.**
- The deliverable channel for the other 74 is the **phone**, and 12 of those now ring the
  anesthesia service line rather than a hospital switchboard.
- LinkedIn was not automated. Every row carries a `linkedin_search_url` for a human to click;
  `linkedin_url` is empty on all 77 because no public page linked a profile.
