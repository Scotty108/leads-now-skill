# Anesthesiology providers within 50 miles of Myrtle Beach — OPEN condition (browser allowed)

Skill under test: `skills/leads-now/` · Condition **B (open)** · run dir `bench/runs/round1__ours__open/`
Branch taken: **DISCOVER → QUALIFY → ENRICH** (FULL). Registry sweep reused from the clamped run per
instruction; the whole budget went to rungs 3 and 4.

---

## 1. Counts

```
84 people in the list — all 84 within 50 miles of Myrtle Beach
   60  NPI registry (reused from the clamped run)
  +23  people the clamped run could not see at all  <-- what the browser bought
    1  extra row from a dual affiliation (F. Bellamy listed at both CMC and McLeod Loris)

Pediatric signal
    1  STRONG — a registered PEDIATRIC ANESTHESIOLOGIST, 25 mi out (see §2)
    1  STRONG — pediatric critical care, credentialed at Grand Strand
   82  NONE_FOUND — searched, nothing published. NOT "no experience".

Contact channels (never report the total alone)
   phone     84   0 direct · 19 department · 65 practice switchboard · 0 answering service
   email      3   0 first_party_published · 3 pattern_confirmed (cmc-sc.com) · 0 guessed
   linkedin   0 verified profile URLs · 84 linkedin_search_url emitted for a human to click

Corroboration
    7  corroborated (2+ independent sources)   77  single_source
   83  carry a title    33  carry a named employing org
```

`python3 skills/leads-now/scripts/leadkit.py audit result.csv` → **PASS**, 84 rows.

**Territory: 84 Myrtle Beach / 0 Greenville.** Not a missing answer — Greenville SC is 190–215 miles from
every practice address found. Nothing inside a 50-mile Myrtle Beach radius is ever nearer to Greenville.

---

## 2. The finding the clamped run could not reach

> **Michelle D. Lee, MD — Anesthesiology, *Pediatric Anesthesiology***
> McLeod Anesthesia – Loris, 3655 Mitchell St, Loris SC — **25.4 mi** from Myrtle Beach
> also McLeod Anesthesiology – Seacoast, 4000 Highway 9 E, Little River SC — **17.8 mi**
> Department lines **(843) 716-7370** and **(843) 390-8128** · `phone_type = department`
> Source: McLeod Health physician finder, the site's own `live_physicians` search index

Round 1 reported **zero** pediatric anesthesiologists within 50 miles, and that was an honest read of the
registry — her NPI record carries no pediatric taxonomy code. The subspecialty exists only on the hospital
directory, which was a JavaScript shell to a plain fetch. This is the exact failure mode `discover.md` warns
about, one layer deeper: querying the parent taxonomy rescues you from a zero roster, but the *subspecialty
itself* still only lives on the org site.

Second STRONG: **Asfawossen B Asfaw, MD** — Pediatric Critical Care Medicine, credentialed at Grand Strand
Medical Center (Myrtle Beach), employed through Sheridan Children's Healthcare. Peds-adjacent, not
anesthesia. His listed address is the staffing agency's FL headquarters, not his work site — flagged in the
`hospital_affiliation` column rather than silently mapped to Florida.

---

## 3. Which rung produced each org's data

The ladder was climbed in order, and rung 3 was tried before rung 4 every time.

| Org | Rung used | What happened |
|---|---|---|
| NPI registry | **1** | 60 in-radius providers (reused from clamped run) |
| mygrandstrandhealth.com | **2 → 3** | sitemap readable at rung 2; the real payload was an embedded `physicianData` JSON in each profile's server HTML — 6 people with NPI, specialties, training, group phone |
| mcleodhealth.org | **3** | browser network log exposed the site's own Algolia endpoint (public search-only key, shipped to every visitor). Index `live_physicians`, 805 records → 29 anesthesiology → **10 in radius** |
| tidelandshealth.org | **4** | rung 3 died on 403 at the network layer. Only the browser read it. 301 providers enumerated, **12 anesthesiology** |
| conwaymedicalcenter.com | 2 | carried over from clamped run |
| novanthealth.org | — | not attempted (Brunswick NC, outside the 50-mile ring; deprioritised inside the timebox) |

**Two of the three "browser-only" sites did not actually need a browser to render.** Grand Strand's data was
sitting in server HTML the clamped run never parsed past `<title>`; McLeod's was behind an endpoint the page
itself calls. The browser's real job there was *discovery* — it showed where to look. Only Tidelands, the
403, genuinely required rung 4 to read. That is the honest version of what browser access bought.

---

## 4. Blocked / unreadable

| Host | Reason |
|---|---|
| `tidelandshealth.org` | 403 to every plain fetch including the correct directory path. Readable **only** via browser (rung 4). Profiles carry no education block, so it yields org + department phone, no peds signal. |
| `mygrandstrandhealth.com` | `/api/physicians/search`, `/api/physician/search`, `/api/doctors/search` all 403; `/api/providers/search` is POST-only (405 on GET) and was **not** called — this run stayed read-only. Worked around via the embedded JSON. |
| `novanthealth.org/doctors` | JS shell; not retried this run (out of ring, timebox). |
| `dosher.org`, `crhealthcare.org`, `seasidesurgerycenter.com` | carried from clamped run — 404 / no directory / 403 |
| 10 independent anesthesia-group domains | DNS NXDOMAIN — these practices have no web presence |
| **WebSearch (tool, not a host)** | session budget exhausted 200/200 before this run started. Every org here was reached by direct fetch or browser against a known or sitemap-derived URL. No search engine was used at any point. |

No CAPTCHA or human-verification wall was encountered, and none was attempted. LinkedIn was never opened,
fetched or automated — only `linkedin_search_url` values a human can click.

---

## 5. Honest limits

- **19 department lines are the real reachability gain**, not the row count. A switchboard is not a contact;
  the clamped run's 59 phones were all front desks. `phone_type` is on every row so nobody has to guess.
- **3 emails on 84 people.** Every one is `pattern_confirmed` on `cmc-sc.com` from two published addresses.
  Per `contact-channels.md` that is ~91% accurate — **still 9 bounces per 100, 4× over the 2% ceiling where
  providers start throttling.** Fine for a human to try one at a time; do **not** load into a bulk sequencer.
- **No email was invented.** Tidelands, Grand Strand and McLeod publish zero clinician addresses, so
  `leadkit emails` emitted nothing for those three domains. The refusal held.
- **82 NONE_FOUND is a sourcing gap, not a verdict.** Tidelands publishes no training block at all; McLeod's
  index carries specialty but not fellowship; Grand Strand publishes training for only 2 of 6. A recruiter
  can still call someone whose record is thin online.
- **A background OpenAlex / Europe PMC qualification pass over all 60 registry names had not returned when
  this report was written**, so no publication-derived pediatric signal or corresponding-author email is
  included here. The clamped run's equivalent pass returned NONE_FOUND across the board.
- **Frederick Bellamy appears twice** (Conway Medical Center and McLeod Anesthesia – Loris) because the two
  directories spell him differently (`Frederick Bellamy` / `Frederick W. Bellamy`). Both rows are real and
  both affiliations are real; the merge key does not span a middle initial. Left in deliberately rather than
  silently collapsed.

---

## 6. Who to call first

1. **Michelle D. Lee, MD** — the only pediatric anesthesiologist in the ring. (843) 716-7370 (dept).
2. **Asfawossen B Asfaw, MD** — pediatric critical care at Grand Strand; peds-adjacent, worth a call.
3. **The 19 department lines** — Tidelands Health Anesthesia (843-652-1190), McLeod Anesthesia Loris
   (843-716-7370), McLeod Seacoast (843-390-8128), Teamhealth Anesthesia at Grand Strand (843-692-1062).
   One call to each group reaches a scheduler who knows every anesthesiologist on it.

## 7. Files

- `result.csv` — 84 rows, 30 columns, audit PASS
- `leads.csv` — the plain `leadkit csv` output (field + field_source pairs)
- `merged.json` — merged records with per-field provenance
- `records/` — one file per source, so corroboration stays countable
- `raw/` — verbatim captures (Tidelands profiles, Grand Strand `physicianData`, McLeod Algolia hits)
- `log.jsonl` — every step, with the rung it used
