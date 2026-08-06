# Round 3 — CLAMPED — can a new class of source fill what the directories cannot?

**Gate: PASS** (`audit.txt`) — every row sourced, tiered, unique.

## The filter, restated

Physician anesthesiologists whose nearest practice location is within 50 miles of Myrtle Beach,
SC (33.6891, -78.8867), with pediatric capability established by a source rather than assumed.

## The denominator

```
777   retrieved from NPI in the searched area (rounds 1-2, not re-fetched)
 77   matched the target  <- the denominator
 77   delivered
 77   with a phone   (0 direct, 12 department, 65 practice switchboard)
  3   with an email  (2 observed, 1 pattern_confirmed, 0 new this round)
  1   confirmed pediatric anesthesiologist in the ring
```

## Answer to the round-3 question

**Yes — one new class landed, and it is the highest-provenance source in the whole benchmark.
Four of the five landed nothing, and three of those four are structurally closed, not merely hard.**

### The win: the certifying board's own directory

The **American Board of Anesthesiology Diplomate Directory** runs on an open, unauthenticated,
un-captcha'd JSON API discovered by climbing the ladder exactly as the skill prescribes —
`theaba.org/directory/` -> React shell at `directoryreact.theaba.org` -> `main.js` -> the API base
and endpoint shapes, all in shipped client code:

```
GET  https://directoryreactapi.theaba.org/lookups/getCertifications
GET  https://directoryreactapi.theaba.org/lookups/getstates
GET  https://directoryreactapi.theaba.org/searchResults/basic?FirstName=&LastName=
POST https://directoryreactapi.theaba.org/searchResults/advanced
       {FirstName,LastName,City,StateId,ABAId,ProgramType}
GET  https://directoryreactapi.theaba.org/doctorRecord/getDoctorRecords?ABAId=<digits, no dash>
```

`ProgramType 519` **is** Pediatric Anesthesiology. This is the exact subspecialty field every
prior round was missing, published by the body that grants it.

**Yield: 48 of 77 roster members matched; 46 now carry a board-certification block that no
directory in rounds 1-2 could show.** That is the single largest new-evidence gain of the
benchmark, and it comes from an official certifying-board record, not a marketing page.

Areas of certification recovered: Anesthesiology 45, Pain Medicine 8, Pediatric Anesthesiology 1,
Critical Care Medicine 1, Adult Cardiac Anesthesiology 1.

### The NONE_FOUND reclassification — the thing round 2 asked for

Round 2 could only say "the directory cannot show a fellowship." Round 3 can say which kind of
silence each person is in:

| `peds_check_kind` | n | Meaning |
|---|---|---|
| `confirmed_at_certifying_board` | 1 | Michelle D. Lee, MD — ABA-certified in Pediatric Anesthesiology |
| `checked_and_absent_at_certifying_board` | 47 | The board that grants the certificate holds no such certificate for them |
| `unpublishable_no_certifying_board_record_matched` | 29 | Still genuinely unchecked |

The 29 unmatched are structurally explained, not hand-waved: **12** carry NPI taxonomy *Student in
an Organized Health Care Education/Training Program* (trainees, not yet board-eligible), **1 PA-C**
and **1 CRNA** are not ABA-eligible at all, and the remainder are MD/DO with no diplomate record in
their state. Those 29 — not the previous 12 Tidelands — are now the highest-value calls in the set.

Tidelands specifically: of its 3 roster anesthesiologists, **Ryan Joseph Galica now has a
certification block** (Anesthesiology + Pain Medicine, both Certified through 2027-12-31) sourced
from the ABA rather than from Tidelands, whose site still 403s. The other two have no ABA record.

### The rejection that matters more than the win

The ABA advanced search returned **53 board-certified pediatric anesthesiologists in SC** and
**117 in NC**. Filtered to the 50-mile ring by Census place centroid, three fell inside:

- Michelle Dianne Lee, MD — Little River SC, 19.4 mi — **accepted**, now double-sourced
- Desiree Aird, MD — "Myrtle Beach SC", 1.5 mi — **REJECTED**
- John Gantomasso, DO — "Myrtle Beach SC", 1.5 mi — **REJECTED**

**The ABA `City`/`State` is the diplomate's mailing address, not a practice location.**
Corroboration killed both:

- **Desiree Aird** — NPI 1528471406 *and* her Doximity profile both place her at 1501 N Campbell
  Ave, Tucson AZ (University of Arizona; residency Wayne State 2015-18, fellowship Pediatric
  Anesthesiology DMC/Wayne State). Two independent sources against one.
- **John Gantomasso** — NPI 1396064481, 777 Hemlock St, Macon GA, taxonomy
  *Anesthesiology, Pediatric Anesthesiology*.

Two perfectly plausible pediatric anesthesiologists, both apparently 1.5 miles from the target,
both withheld. **The pediatric count in the ring is still exactly 1** — now confirmed by a second,
higher-provenance, independent source rather than by a single hospital directory.

### Ceiling caught

`searchResults/advanced` for NC + ProgramType 513 (Anesthesiology) returned **exactly 1000**
records — the same silent-truncation shape as NPI `skip=1000` and McLeod's `paginationLimitedTo`.
That count is not a total. SC 513 returned 860 and the peds queries returned 53 / 117, all under
the ceiling, so the subspecialty frame used here is complete.

## The four that landed nothing, and why

| Class | Attempted | Yield | Kind of zero |
|---|---|---|---|
| **1. State medical boards** | SC LLR `verify.llronline.com/LicLookup/Med/med.aspx?div=13` — full ASP.NET POST with harvested `__VIEWSTATE`/`__EVENTVALIDATION` + cookie jar. NC `portal.ncmedboard.org/verification/search.aspx` — same, plus `__RequestVerificationToken`. | **0** | **Hard-closed.** Both are reCAPTCHA v2. NC returned *"You did not pass CAPTCHA validation... missing-input-response"*; SC returned `<button class="g-recaptcha" data-sitekey="6Lc2X-saAAAAAPC6HatgHFOd8rCxCl-2yPTh44PN">` with `CaptchaIncorrectLabel="Incorrect"` and zero rows. **Not a clamp artifact** — the skill forbids solving a CAPTCHA, so a browser run is equally blocked. Paid/gated alternates: NCMB bulk roster **$150**; SC LLR `OnlineVerificationBulk` and `OnlineVerification2` are login walls. |
| **2. Board certification — ABMS consumer route** | `certificationmatters.org` (403), `abms.org/verify-a-physician/` (404), `apps.abms.org` (NXDOMAIN) | **0** | Closed. The consumer aggregator is shut; the **member board** (ABA) is wide open. Go to the board that grants the certificate, not to the umbrella. |
| **3. Society directories** | SPA `/members/`, `/member-directory/`, `/find-a-member/`; ASA `/member-directory`, `/about-asa/member-center/find-a-member` | **0** | **No public member directory exists.** SPA `/members/` is a login/dues landing page; its only member-data product is paid *SPA Mailing List Rental*. ASA directory URLs 404. |
| **4. Aggregators (corroboration only)** | Doximity `/pub/` for 14 highest-value blanks (all 3 Tidelands + all no-ABA-match); Healthgrades; Vitals | **0** | **Inverted gate.** 5 of 14 were 404 stubs. Of the 9 real profiles, the 2 that publish an Education & Training block (Awe -> Washington DC, Tsichlis -> Hinsdale IL) fail place corroboration and were discarded as different people. The 2 whose place *does* corroborate (Galica -> Mount Pleasant SC, Halling -> Myrtle Beach SC) publish **no** training block — it sits behind *"Join to view full profile"*. Doximity gates exactly the field we need on exactly the people we can verify. Healthgrades serves an identical 1,575,662-byte homepage for a physician URL and for `/`; Vitals 403. Doximity's one real contribution was **negative**: corroborating the Aird rejection. |
| **5. Residency / fellowship program pages** | MUSC anesthesia residency (200, chrome-stripped, link-harvested), MUSC dept page, Children's Colorado peds-anesth fellowship (404), Prisma anesthesiology residency (1160-byte stub) | **0** | **Structurally circular.** A program page is indexed *by program*, and the program is precisely the field we are trying to fill. It can confirm a training claim you already hold; it cannot discover one. 0 of 77 roster names appear on the MUSC residency page. |

## Method notes the hard rules forced

- **Full-forename lock.** 94 raw ABA hits for 77 names -> 85 forename+surname matches -> **47** with
  an agreeing state. 38 forename+surname matches were withheld on state disagreement, including
  `Deeran Patel` (Arlington VA), `Michelle Pae Lee` (Fullerton CA — a near-miss on the one person
  we most needed to get right), and three different `Michael Ford`s. One diminutive was accepted:
  roster *Frederick William Bellamy* <-> ABA *Fred William Bellamy, M.D.*, Myrtle Beach SC, on
  matching middle name + city + state + specialty.
- **Chrome stripped before matching** on every HTML source (MUSC, Doximity), per the OrthoSC
  navigation-string defect. The ABA path is pure JSON and has no chrome to strip.
- **No email emitted.** The tooling produced none this round; none was written.
- **LinkedIn** — 77 `linkedin_search_url`s carried forward, 0 automated.

## Marginal value over round 2 — the termination measurement

| | Round 2 | Round 3 | Marginal |
|---|---|---|---|
| People | 77 | 77 | **0** |
| Emails | 3 | 3 | **0** |
| Pediatric anesthesiologists in ring | 1 | 1 | **0** |
| Department phones | 12 | 12 | **0** |
| **Board-certification / training blocks** | **0** | **46** | **+46** |
| NONE_FOUNDs reclassified checked-vs-unpublishable | 0 | 48 | **+48** |

**Read this honestly.** On every headline number the round is dry — no new people, no new emails,
no new pediatric hits, no new phones. What round 3 bought is *evidential*, not numerical: 46 people
who were `NONE_FOUND` because a hospital chose not to publish a training block now carry one from
the certifying board itself, and the pediatric answer of "1" is now attested by two independent
sources instead of one hospital's search index.

And the sharpest result is the negative one: a source good enough to produce two new, plausible,
in-radius pediatric anesthesiologists was good enough to be wrong about both, and only corroboration
against NPI and Doximity caught it. A run that had trusted the ABA's geography would have shipped
two false rows that looked better than anything else on the sheet.

## What this run could not establish

The 29 roster members with no ABA diplomate record. 14 are structurally explained (12 trainees,
1 PA-C, 1 CRNA). The remaining 15 MD/DOs are the genuine unknowns.

**The one action that would resolve it:** a human solving one reCAPTCHA at
`verify.llronline.com/LicLookup/Med/med.aspx?div=13` per name. SC LLR publishes licence status and
issue date; NC's board additionally publishes education, residency and area of practice. That is
one human interaction per person and it is the only remaining free path.
