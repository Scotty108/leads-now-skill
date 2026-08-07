# Universality proof run — FL licensed roofing contractors, 25mi of Tampa

Deliberately non-healthcare. The population-class method had passing unit tests
and had never touched a real state licensing portal.

## Result

**865 active licensed roofing contractors within 25 miles of Tampa**, from a
free public register, using **zero web searches**.

```
within 15 mi   319      within 25 mi   865      within 50 mi  1442
9,760 active roofing licensees statewide (of 270,487 in the file)
190 UNPLACED — no city or postal code, in no band including yours
```

## What the method got right

- **Classification worked.** Licensed (+ Entity principal); take the highest,
  so Licensed. Enumerable, therefore a denominator exists: 865 of 865.
- **Bulk file before lookup form.** Three hops from the root domain reached a
  48 MB CSV of all 270,487 licensees — HTTP 200, no key, no CAPTCHA, no login.
- **Reaching it without search mattered.** The run exhausted its WebSearch
  budget (200/200) at the first query and still got there by navigating.

## What the method got wrong

**The yield table promised a phone.** It said a licence register "gives you a
person and a phone, not an inbox". Across 270,487 rows x 22 columns this file
carries **no phone and no email at all** — 2 stray `@` cells, both typos inside
a name field. NPI publishes a phone; DBPR does not. Corrected: count the
populated cells before promising reachability.

**Honest reachability from the register alone: 0 of 865.** Address only.

## Two bugs the run exposed, both silent

1. **merge collapsed 107 distinct people.** The key is name + org, and a
   register has no org, so it degenerated to name alone. `David Lee Carr` of
   St. Augustine and `David Lee Carr` of Brooksville — different licences —
   became one blended row. Fixed with a location fallback: +113 people
   recovered, +15 inside the 25-mile ring.
2. **Surname-first names stranded the suffix.** "AMBROSE, DEREK GABRIEL II"
   rendered as "Derek Gabriel Ii Ambrose". Registers publish one combined
   surname-first field; only org sources split first/last. Added `flip_name`.

## The honest gap

Every one of these 865 is a name, a title, a licence number and a street
address. **None is reachable yet.** Enrichment for this population means
resolving the contractor's own business domain — the Entity-principal channel,
where the method predicts high yield — and that half was not run.
