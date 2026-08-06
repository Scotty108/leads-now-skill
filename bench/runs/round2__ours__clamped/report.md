# Round 2 — clamped. Does anything move once round 1's corrections are in?

Run: `round2__ours__clamped` — skill `leads-now`, branch **ENRICH** (roster reused, budget spent on channels).
Condition A (clamped): WebFetch / Bash only. No browser (rung 4 unavailable by design). WebSearch budget
exhausted at 200/200 and never called. Roster reused verbatim from `round1__ours__clamped/in_radius.json` —
the NPI registry was **not** re-fetched.

**Answer: yes, materially.** Every one of the four round-1 corrections paid, and the two "rung-3" wins that
round 1B got with a browser were both reproduced **without one**.

## 1. Marginal vs round 1

| | Round 1 | Round 2 | Delta |
|---|---|---|---|
| People found | 60 | **69** | **+9** |
| In radius | 60 | **68** | +8 |
| Rows in `result.csv` | 59 | **68** | +9 |
| Emails | 3 | **4** | **+1** |
| - of those, `first_party_published` | 0 | **1** | **+1** |
| Department phones | 0 | **16** | **+16** |
| Pediatric signal STRONG | 0 | **1** | **+1** |
| LinkedIn search URLs | 0 emitted as a column | **68** | +68 |

`leadkit audit result.csv` -> **PASS: 68 row(s); every row sourced, every email labelled, every phone typed.**

## 2. What each correction bought

### Correction 1 — NCBI `efetch db=pmc`, not Europe PMC `fullTextXML`

Round 1B measured Europe PMC 404-ing on all four locked PMIDs. Round 2 never touched Europe PMC.

Flow actually run:

```
POST esearch db=pubmed
  term = (24 geo/org affiliation terms)[Affiliation] AND (57 roster surnames)[Author]
  -> 705 PMIDs
POST efetch db=pubmed retmode=xml  (4 batches of 200)
  -> per-author LastName / ForeName / Affiliation
GET  efetch db=pmc id=PMC11249181,PMC10324711,PMC10327958,PMC8890879
  -> 4/4 served. Zero 404s.
```

**Affiliation-first, not person-first.** Instead of 60 name queries that each return every same-named human
alive, one query locks the affiliation up front and lets the roster surnames filter it. 705 papers -> 151
author records that are both a roster surname *and* a geo-locked affiliation -> 4 papers.

Yield: **`Jon.Halling@hcahealthcare.com`** — PMC11249181 (2024), *HCA Healthcare Journal of Medicine*,
corresponding-author block reads *"Correspondence to: Jon Halling, MD, MBA (Jon.Halling@hcahealthcare.com)"*,
affiliation *"Grand Strand Medical Center, Myrtle Beach, SC"*. Labelled `first_party_published`. This is the
first address in either round that clears the 2% bounce ceiling — the other three are `pattern_inferred`.

### Correction 2 — full-forename disambiguation

The lock threw away **147 of 151** surname+geo author records. Representative kills:

| Rejected | Why |
|---|---|
| `Loris Thomas` | "Loris" matched as a *place* in the affiliation OR-block; the author's forename is Loris |
| `G Lee`, `S Thomas`, `K S Smith`, `T J Smith` | initial-only forename — unconfirmable, discarded per the rule |
| `Robert Wallace` (6 papers) | roster member is **Edward** Wallace |
| `Raymond Lee`, `Byron K Lee`, `Angela S Lee`, `Phil H Lee` ... | roster member is **Michelle** Lee |
| `Kevin C Ward`, `Patrick J Ward` | roster member is **Jonathan** Ward |

It also caught a collision in a completely different channel: the McLeod name sweep matched roster
**"E J Collins"** to **"C. Michael Collins, MD, Pediatrics"**. Surname identical, forename an initial —
**discarded**. Had that passed, round 2 would have reported a false pediatric hit.

Survivors: Jon Halling (1 paper), Derek Horstemeyer (3 papers). Both Grand Strand, Myrtle Beach.

### Correction 3 — OpenAlex is metered

Not retried. Round 1B measured HTTP 429 / `"Insufficient budget... $0 remaining"` / `retryAfter 6268s` on
72/72 queries. Per the correction it gets one try, and round 1 spent it. Recorded as a blocked source; zero
calls made this round.

### Correction 4 — subspecialty is not in NPI; go get it at rung 3

**Both rung-3 wins reproduced with `curl` only.**

**(a) Grand Strand — embedded `physicianData` JSON in the profile server HTML.** Round 1 recorded these pages
as "only `<title>` renders server-side". False. The JSON is inline; a brace-matched parse from the raw HTML
returns NPI, forename, middle initial, designation, `hcaEmployee`, `providerSpecialties`,
`credentialsAndAccreditations` (residency / internship / fellowship / graduate degree), and
`providerLocations` with the group name and phone. Ran it against **all 299** profiles in `physicians.xml`.
299/299 parsed, 0 failures.

**(b) McLeod — its own public Algolia index.** `search-physician-finder/` ships
`var crbAlgoliaCredentials = {"credits":{"api_id":"JUNR3SUCF2","api_key":"ad6044da..."}, "indexes":{"physician":"live_physicians", ...}}`
in the server HTML. That is a public search-only key the site hands every visitor. Querying
`live_physicians` returns structured records: specialties, subspecialties, practice name, street, phone, geo.

## 3. The pediatric answer, now with evidence

**Michelle D. Lee, MD — McLeod Anesthesia - Loris. `peds_signal = STRONG`.**

- McLeod `live_physicians` record: `specialties: [Anesthesiology, Pediatric Anesthesiology]`
- Her first-party profile page: *"Board Certification: Anesthesiology; **Pediatric Anesthesiology**"*
- *"Residency: 2007 — Children's Hospital Colorado, Aurora, CO"*
- Her NPI record carries **no** `207LP3000X` taxonomy. Round 1's registry-only sweep could not have found her.

She is the **only** pediatric anesthesiologist in the entire 805-physician McLeod index, and the Grand Strand
299-profile sweep found **zero**. So round 1's "0 peds within 50 miles" was not a null result — it was a
**registry-coverage artifact**, and the true count reachable from open sources under this clamp is **1**.

## 4. Department phones — round 1B's "falsified" is itself falsified, partly

Round 1B measured 0 department lines across 8 org sites and concluded fetching org pages does not upgrade a
`practice` number. That holds for the *page-fetch* method. It does **not** hold for rung 3: the structured
records carry the group's own line, not the switchboard.

| Line | Org | Rows |
|---|---|---|
| (843) 716-7370 | McLeod Anesthesia - Loris | 7 |
| (843) 390-8128 | McLeod Anesthesiology - Seacoast, Little River | 3 |
| (843) 777-8752 | McLeod Anesthesia - MRMC | 1 |
| (843) 692-1062 | Teamhealth Anesthesia @ Grand Strand | 3 |
| (843) 692-1061 | Man In The Box Anesthesia @ Grand Strand | 1 |
| 843-839-4598 | Farayi Mbuvah's own pain clinic, 811 82nd Pkwy Ste B | 1 |

**16 rows now carry a department line, up from 0.** Conway Medical Center remains a genuine zero — 304
provider pages scanned, every one publishing only the 843-347-7111 switchboard.

Final channel split:

```
68 people
  phone      68  (0 direct, 16 department, 51 practice switchboard, 1 answering service)
  email       4  (1 first_party_published, 3 pattern_inferred/pattern_confirmed)
  linkedin    0 verified, 68 search URLs provided
  peds        1 STRONG, 67 NONE_FOUND
```

## 5. Nine new people

Six from the McLeod index (all at in-radius facilities, none in the round-1 NPI roster): Alisha F. Palliser,
David O. Atkinson, Ligia E. Cisneros-Gonzalez, Ahmed Elhaimer, Michael D. Wingfield (McLeod Anesthesia -
Loris), Robert O'Connor (McLeod Anesthesiology - Seacoast, Little River).

Three from the Grand Strand sweep: Brandon Sloop MD and Desiree Aird MD (Teamhealth Anesthesia, Myrtle
Beach — both in radius, both with NPIs), and Songoli C Umeh MD, **counted as found but NOT as in-radius** —
she is on Grand Strand's Myrtle Beach medical staff but her registered practice address is the Weatherby
Locums agency in Fort Lauderdale FL. Hence 69 found / 68 in radius.

## 6. An inference the data refused

Three real `@hcahealthcare.com` addresses were recovered from PMC (`Jon.Halling`, `David.Kingery`,
`alex.roberts`) — three agreeing observations of `first.last`, which is `pattern_confirmed` territory and
would have produced five more addresses on the Grand Strand anesthesiologists.

**Withheld.** Grand Strand's own `physicianData` sets `hcaEmployee: false` on **all five** of them
(Horstemeyer, LiVigni, Sloop, Aird, Umeh). They are contracted group anesthesiologists — Teamhealth and Man
In The Box — not HCA employees, so an `@hcahealthcare.com` address for them is a guess wearing a confirmed
pattern's clothes. The rung-3 record that gave us the department phones is also what disqualified the emails.

Zero addresses were emitted that the tooling declined to produce. LinkedIn was never fetched; 68
`linkedin_search_url` values are emitted for a human to click.

## 7. Blocked and unattempted

| Host | Reason |
|---|---|
| `api.openalex.org` | Metered; HTTP 429 `$0 remaining`, retryAfter 6268s (measured round 1B). One try spent; not retried per correction 3. |
| `tidelandshealth.org` | HTTP 403 on every path (round 1). Not re-probed; no browser rung under the clamp. |
| `novanthealth.org` | JS shell, 0 names (round 1). No `physicianData`-style embedded JSON and no public search index found. |
| `crhealthcare.org`, `dosher.org`, `seasidesurgerycenter.com` | No readable provider directory / 403 (round 1). |
| `ebi.ac.uk/europepmc` | Deliberately not used — `fullTextXML` 404'd 4/4 in round 1B. Replaced by `efetch db=pmc`, which served 4/4. |
| WebSearch | Budget exhausted 200/200. Zero calls. Every URL this round was a registry endpoint, a sitemap, or an endpoint read out of server HTML. |

## 8. What still cannot be beaten

The academic-email ceiling is real and is a property of the population, not the tooling. Of 69 people, **2**
have any affiliation-locked, full-forename-confirmed paper at all, and only **1** of those two was a
corresponding author. Sweeping 705 papers to find one address is the honest cost of this channel on a
community clinical roster. Phone remains the deliverable channel — but it is now a *department* line for 16
of them instead of a switchboard for all of them.

## 9. The file

`result.csv` — 68 rows, 40 columns, a `_source` beside every value, `phone_type` on every phone,
`round2_delta` naming exactly what round 2 added to each row.
