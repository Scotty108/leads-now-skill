# Anesthesiology providers within 50 miles of Myrtle Beach - delivery brief

**Skill:** `finding-leads` (skillit) - **Branch:** FULL (registry frame) - **Condition:** A, clamped
(WebFetch / WebSearch / Bash only; no browser automation) - **File:** `result.csv` (72 rows)

**The gate passed.** `audit_list.py` returned PASS: every row is sourced, tiered, and unique.

---

## 1. The filter, restated

Individual anesthesiology providers with a practice location inside a 50-mile ring around Myrtle
Beach, SC (33.7104, -78.8860). Pediatric anesthesiologists and anyone with pediatric experience,
including past hospital experience, preferred but not required. Each provider assigned to Myrtle
Beach or Greenville SC by whichever is closer to the practice address.

The ring crosses into **North Carolina** (`geo_filter.py resolve` returned states SC,NC and ZIP3
prefixes 283, 284, 294, 295). A South-Carolina-only search would have silently lost the Brunswick /
Columbus county side of the ring - 13 of the 72 delivered rows sit in NC.

## 2. The denominator

| Stage | Count |
|---|---|
| Records retrieved from the NPI Registry (ZIP3 283/284/294/295, taxonomies `Pediatric Anesthesiology` + parent `Anesthesiology`) | **777 distinct providers / 1,188 practice-location rows** |
| Dropped - practice location outside the 50-mile ring | 1,098 location rows |
| Dropped - ZIP not a Census ZIP area, unplaceable | **14 location rows** (coverage loss, not zero) |
| **Inside the ring, deduped to nearest practice site** | **72 providers** |
| Delivered | **72** |

The registry sweep terminated at **`parse` exit 0, COMPLETE**. No query was truncated at the
registry ceiling, so 777 is a true retrieval total and 72 is a true population count, not a sample.

**Truncation was detected once and fixed.** The organization sweep (NPI-2, by ZIP3) hit `parse`
exit 4 - the ~1,200-record registry ceiling - at 3,556 organizations. That count is *unknown, not
large*. The query was re-partitioned across the **16 exact 5-digit ZIPs** the filtered roster
actually contains and re-fetched to **exit 0, COMPLETE, 2,961 organizations**. Employer resolution
below is built on the complete partition, not the truncated one.

## 3. Confidence and email_status counts (from `audit_list.py`)

```
delivered rows:   72
with an email:    0 (0%)
with a phone:     72 (100%)
confidence:       unconfirmed=72
email_status:     none_no_observed_address=72
```

**Rows carrying a real email address: 0 of 72.** Not "a few" - zero. See section 5.

Every row carries a **published practice phone from the NPI Registry** - a real, sourced,
dialable route. For clinicians that is the higher-confidence channel anyway.

**Employer resolved for 60 of 72 rows (83%)** by joining NPI-2 organizations enumerated at the same
street address; 42 rows (58%) have a top candidate whose name matches the person's specialty. That
address join is a *hypothesis*, flagged as such in `org_source` - it is not confirmed on any page
that names the person. The largest clusters: Ambulatory Care Anesthesia PC / Atlantic Coast
Anesthesia (20 rows, Myrtle Beach), Brunswick Community Hospital / Novant (6), Conway Anesthesia
Associates (5), Coastal Carolina Anesthesiologist PA (4), Tidelands / Georgetown groups (6).

## 4. Territory assignment

**All 72 to Myrtle Beach. Zero to Greenville.** This is arithmetic, not judgement: the furthest
provider is 46.2 miles from Myrtle Beach, and the *closest* provider to Greenville SC is 184.3 miles
away. A 50-mile Myrtle Beach ring cannot produce a Greenville-territory provider. Distances to both
centres are on every row (`dist_to_myrtle_beach_mi`, `dist_to_greenville_mi`) so the rule is
auditable.

## 5. Pediatric signal - the honest answer is that none was established

**Confirmed pediatric-capable: 0. Moderate/probable: 0.**

- Providers inside the ring carrying the **Pediatric Anesthesiology** taxonomy (207LP3000X): **0**.
  This is the exact failure mode the skill warns about - a subspecialty-only query would have
  returned an empty list that looks like a correct answer. Querying the parent classification is
  what produced the 72.
- The subspecialty is settled during enrichment - a children's-hospital affiliation, a fellowship,
  a board certification, a department page. **Every enrichment source that could have settled it
  was unreadable in this condition** (section 6), so no row was promoted above `unconfirmed`.
- A PubMed sweep across all 72 names returned peds-related publications for 30 of them. **That
  signal was rejected**, not used: the author query was not affiliation-locked, so "R. Smith
  published on pediatric anesthesia" cannot be attributed to *this* R. Smith. Using it would have
  been the invented-evidence failure this skill exists to prevent.

One row is confirmed on an organization's own page: **Ihor Melnytskyy, MD, ABANES**, named on the
Conway Medical Center provider directory. No pediatric mention there either.

## 6. Sources that could not be read, and why

| Source | Wall | Consequence |
|---|---|---|
| **WebSearch (all queries)** | Session budget exhausted, 200/200 calls used **before this run started** | Could not discover org domains, provider-directory URLs, LinkedIn profiles, or fellowship/CV pages. Single largest cause of the thin enrichment. |
| tidelandshealth.org find-a-doctor | **HTTP 403**, bot fingerprinting | Rung 4 (browser) prohibited under this condition. Unread. Covers ~6 rows. |
| mygrandstrandhealth.com/physicians | **200, "Loading doctors", zero names**, JavaScript shell | Rung 3 (calling the endpoint the page itself uses) not attempted - timebox. Unread. |
| conwaymedicalcenter.com/find-a-provider?specialty=Anesthesiology | 404, retired page | Fell back to `/providers/`, readable, yielded 1 named provider. |
| ambulatorycareanesthesia.com | DNS ENOTFOUND | Guessed domain is wrong; the real domain for the 20-row cluster could not be found without search. |

Nothing was skipped silently. No LinkedIn profile URL was found, because search - the only permitted
way to find one - was unavailable; no LinkedIn page was scraped or automated.

## 7. What this run could not establish, and the one action that fixes it

**Not established:** which of the 72 treat children, and any email address for any of them.

**The one action:** restore web search. With search available, the highest-value single move is to
resolve the domain for the **Ambulatory Care Anesthesia PC / Atlantic Coast Anesthesia** cluster -
20 of 72 rows, 28% of the list, in one place - read its provider pages for observed addresses and
fellowship history, then repeat for the Conway and Brunswick clusters. Two observed addresses at one
of those domains moves that cluster from 0% email coverage to `pattern_confirmed`, the only tier
this skill will let you send to. Second move, cheaper: rung-3 endpoint discovery on the Grand Strand
JavaScript directory.

**What is usable today:** 72 phone-reachable, registry-sourced anesthesiology providers, 100% with
a published practice phone, all assigned to Myrtle Beach, 60 with a probable employer. Call them.
Do not mail-merge them - there is nothing to merge.
