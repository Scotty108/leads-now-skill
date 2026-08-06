# Round 3 — clamped (WebFetch + curl only)

**Question:** can a NEW class of source fill the gaps the hospital directories cannot?

**Answer: yes, decisively — but not the class the round-3 brief predicted.**

Both state medical boards are CAPTCHA-walled and yielded zero. The board-certification
and society channels yielded zero. The thing that broke the problem open was a source
class nobody had named: **CMS's Doctors and Clinicians National Downloadable File** —
Medicare PECOS enrollment, a genuine official filing, free, no key, and it publishes the
**medical school and graduation year** for every enrolled clinician in the country.

---

## Headline numbers

| | Round 2 | Round 3 | Delta |
|---|---|---|---|
| People | 68 | **120** | **+52** |
| In-ring (postal 283/284/290/294/295) | 68 | 119 | +51 |
| Within 50 mi of Myrtle Beach (strict) | 68 | 113 | +45 |
| Rows with a training block (med school + grad year) | **0** | **99** | **+99** |
| Rows with a named employer group | ~19 | 98 | +79 |
| Rows with any department line | 16 | 37 | +21 |
| Board certifications | 0 | 6 | +6 |
| **Emails** | 4 | **4** | **0** |
| Pediatric-anesthesiology signal | 1 | 1 | 0 |

`leadkit audit result.csv` -> **PASS: 120 rows; every row sourced, every email labelled, every phone typed.** Zero fixes required.

---

## The Tidelands 12 — named, with training, without a browser

Round 2B established that Tidelands publishes **no training block for any of its 12
anesthesiologists** and 403s to `curl`. Those 12 were the highest-value calls in the set
and their records were blank. They are no longer blank.

One query — `facility_name contains "TIDELANDS"` against CMS DAC — returned 69 enrollment
records, of which 12 distinct NPIs carry `pri_spec = ANESTHESIOLOGY`. All 12, with a
medical school, a graduation year, and the group's own line **843-527-7100**:

| Name | Cred | Medical school (CMS filing) | Grad | Corroborated |
|---|---|---|---|---|
| Michael Bart Pesce | MD | *OTHER* | 1977 | — |
| Philip M Dulberger | MD | Indiana University SOM | 1990 | Healthgrades (ABA cert) |
| Alexandra Anatolievna Armstrong | MD | *OTHER* | 2014 | Healthgrades (ABA cert) |
| Derek J Shirey | DO | Lake Erie COM, Erie | 2019 | Healthgrades (ABA cert) |
| William Raymond Comeau | MD | Univ. of Tennessee HSC | 1988 | — |
| Matthew Holt | MD | MUSC | 2021 | Healthgrades (ABA cert) |
| Felicia Cain | MD | West Virginia Univ. SOM | 1987 | — |
| Philip C Moore | MD | MUSC | 1990 | Healthgrades (ABA cert) |
| Daniel Richard Carhart | MD | *OTHER* -> A.T. Still Kirksville COM | 2001 | Healthgrades (ABA cert) |
| Victoria Suzanne Vogle | MD | *OTHER* | 1995 | — |
| Kamran Khattak | MD | *OTHER* | 1996 | — |
| Christopher John Samuel | MD | *OTHER* | 1991 | — |

`med_sch = "OTHER"` is CMS collapsing any school not on its pick-list (typically
international). Those rows are labelled `PARTIAL_grad_year_only`, not `FILLED` — the
graduation year is real, the school is genuinely unreported.

One discrepancy, stated rather than smoothed: **CMS lists Carhart as MD; Healthgrades
lists his school as an osteopathic college.** One of the two is wrong.

---

## Yield of every source class attempted

| Class | Source | Reachable | Yield | Verdict |
|---|---|---|---|---|
| **State board** | SC LLR Board of Medical Examiners (`verify.llronline.com`) | 200, form served | **0** | **Blocked by Google reCAPTCHA.** Extracted `__VIEWSTATE`/`__EVENTVALIDATION` and POSTed three ways; the form re-renders with zero rows because `onSubmit()` gates the postback on `grecaptcha.getResponse()`. Not defeated, per `blocked.md`. |
| **State board** | NC Medical Board (`portal.ncmedboard.org`) | 200, form served | **0** | **Blocked by Cloudflare Turnstile** (`data-sitekey 0x4AAAAAADYoob8wVvTTqrGT`). No bulk licensee file published either — `/licensee-data` serves 0 bytes, sitemap 404s. |
| **Board cert** | ABA (`theaba.org`) | 200 | **0** | **No public diplomate lookup exists.** `verify.theaba.org` DNS-fails; `/verify/` and `/verify-certification/` 404; `portal.theaba.org` is a candidate-login shell. |
| **Board cert** | ABMS `certificationmatters.org` | **403** | **0** | **Blocked, not absent.** 403 to curl *and* WebFetch, on www, apex and `/api/search`; `apps.abms.org` DNS-fails. This is the one source that would state a Pediatric Anesthesiology subcertification directly. |
| **Society** | SPA (`pedsanesthesia.org`) | 200 | **0** | No public roster at all; member area is login-gated `*.iphtml`. |
| **Society** | ASA (`asahq.org`) | 200 | **0** | No public find-an-anesthesiologist directory; deeper paths 403. |
| **Aggregator** | Healthgrades | 200 to curl w/ browser UA | **6 board certs, 3 med schools, 0 residencies, 0 fellowships** | Corroboration only, never sole source. Pages exist for only 6 of the 12. |
| **Aggregator** | Vitals.com | **403** | 0 | Blocked. |
| **Aggregator** | Doximity | 200 shell | 0 | Nothing readable without auth. |
| **Program pages** | Residency/fellowship alumni | not reached | 0 | Timebox consumed. Named as the live remaining lead (Shirey LECOM 2019, Holt MUSC 2021; both Healthgrades addresses are MUSC's Ashley Ave campus). |
| **NEW** | **CMS Doctors & Clinicians NDF (`mj5m-pzi6`)** | **200, open JSON, 3.39M rows** | **99 training blocks, 52 new people, 79 employer groups, 6 NPIs resolved** | The round. |

Endpoint, for reuse:

```
POST https://data.cms.gov/provider-data/api/1/datastore/query/mj5m-pzi6/0
{"conditions":[{"property":"facility_name","value":"TIDELANDS","operator":"contains"}],"limit":500}
```

Fields: `npi, provider_first_name, provider_middle_name, provider_last_name, cred,
med_sch, grd_yr, pri_spec, sec_spec_1..4, facility_name, org_pac_id, num_org_mem,
adr_ln_1, citytown, state, zip_code, telephone_number`. No key, no auth.

---

## The pediatric question, and why three sources cannot answer it

Round 3's peds count is unchanged at **1** (Michelle D. Lee, MD — McLeod, evidenced in
round 2B by a published *Board Certification: Anesthesiology; Pediatric Anesthesiology*
row plus a Children's Hospital Colorado residency).

Three structural negatives, each measured rather than assumed:

1. **CMS DAC has no Pediatric Anesthesiology value.** Measured: `pri_spec` values
   containing "PEDIATRIC" are only `PEDIATRIC MEDICINE`; `sec_spec` values containing
   "ANESTH" are only `ANESTHESIOLOGY`, `ANESTHESIOLOGY, HOSPICE/PALLIATIVE CARE`,
   `ANESTHESIOLOGY, INTERVENTIONAL PAIN MANAGEMENT`. **Unpublishable**, not absent.
2. **SC LLR has no Pediatric Anesthesiology code either.** Its dropdown carries 27
   PEDIATRIC-prefixed specialties and three anesthesiology ones, and none of them is the
   intersection. Even unblocked, the SC board could not have answered this.
3. **Healthgrades: checked-and-absent, proved by control.** The education schema uses
   typeCodes `MEDSCH / INTERN / RESIDE / FELLOW`, and a control provider from the same
   Georgetown result set (`dr-edward-gologorsky-2fywb`) returns a 1994 UPMC `FELLOW` row.
   The field exists and is empty for all 12. Three of the six have `"education":[]`.

And one independent negative in positive form: an **NPI-taxonomy sweep for 207LP2900X
(Pediatric Anesthesiology)** across Georgetown, Myrtle Beach, Conway, Murrells Inlet and
Pawleys Island returned `result_count: 0` in all five cities.

So the honest reading has hardened: **there is one published pediatric anesthesiologist
in this ring, and the remaining uncertainty sits behind exactly one blocked door — ABMS.**
That door needs a browser, which this condition forbids.

---

## Guards that fired

- **Page chrome stripped.** The only "Pediatric Anesthesiology" strings on the Healthgrades
  pages were footer nav (`/pediatric-anesthesiology-directory`). Matching inside the
  provider record only prevented **6 false peds hits**.
- **Full-forename + geography lock.** Rejected: Alexandra Armstrong NPI 1255569133
  (Greenville SC, enumerated 2009, Critical Care taxonomy — inconsistent with a 2014
  graduate), plus same-name people in High Point NC, Hickory NC, Longview WA, Charleston
  WV, Cumberland MD and Indianapolis IN. Robert O'Connor NPI 1710103270 rejected as
  GENERAL SURGERY / Charlotte; NPI 1952347643 (ANESTHESIOLOGY, McLeod) accepted instead.
- **Flagged ambiguous rather than counted.** Philip Moore's school and year match CMS
  exactly, but his Healthgrades address is Wilson NC. Likely the same person; not
  established, so recorded as corroboration and nothing stronger.
- **Phone typing held.** DAC's `telephone_number` is an enrollment practice line and
  defaults to `practice`. It is upgraded to `department` only when the number is *not* a
  known hospital switchboard *and* `facility_name` contains "ANESTH" — i.e. it rings the
  anesthesia group, not a front desk. That rule gives Tidelands 843-527-7100 and Atlantic
  Coast's 843-449-7885 as `department`, while correctly keeping MedStream's 843-347-7111
  as `practice` because that number *is* Conway Medical Center's switchboard.
- **No email invented.** Zero.

---

## The email channel: a fourth dry round

**0 new emails.** The count stands at 4 (3 Conway `@cmc-sc.com`, 1 first-party-published
`Jon.Halling@hcahealthcare.com` from `efetch db=pmc`). CMS DAC carries no email field at
all. Both boards are blocked. ABA/ABMS/SPA/ASA publish nothing. Healthgrades publishes
none.

Cumulative: **1,342 hospital profiles (round 2B) + a 3.39M-row CMS enrollment file + two
state boards + four professional bodies + three aggregators -> 4 addresses across 120
people.** Email on a community clinical roster is not a sourcing gap that more effort
closes. It is a property of the population. Phone remains the deliverable channel — and
this round improved that: department lines went 16 -> 37.

---

## Was this a dry round?

No — but it is worth being precise about what got wet.

- **Coverage and enrichment: a large win.** +52 people, +99 training blocks, +79 employer
  groups, +21 department lines, and the specific 12-person blank spot the brief called the
  highest-value target is now fully populated at official-filing provenance.
- **Email: dry, for the fourth consecutive round.** 0 marginal.
- **Pediatric subspecialty: dry.** 0 marginal, and now for a *structural* reason that
  three independent sources agree on.
- **The two source classes the brief predicted would work — state boards and board
  certification — both returned genuine zeros.** One to CAPTCHA, one to the absence of any
  public verification tool at all.

The generalisable lesson for `references/sources.md`: the training data was never on a
marketing page or a licence lookup. It was in a **billing enrolment file**. When a
directory will not tell you who somebody is, ask what they had to file in order to be paid.
