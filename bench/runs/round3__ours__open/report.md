# Round 3 — OURS — OPEN (browser available)

**Question:** after three rounds, is there ANY remaining channel a browser
unlocks that plain fetching cannot?

**Answer:** Yes — exactly one, and it was worth **one record out of 120.**

---

## 1. The ABA contradiction, resolved

**The other skill's round-3 run was right. Our round-3 clamped run was wrong.**

Our clamped run wrote, in its own source table:

> `Board cert | ABA (theaba.org) | 200 | 0 | **No public diplomate lookup exists.**
> verify.theaba.org DNS-fails; /verify/ and /verify-certification/ 404;
> portal.theaba.org is a candidate-login shell.`

That is a false negative, falsified on the **first** call of this run, with
`curl`, no browser:

```
GET https://directoryreactapi.theaba.org/searchResults/basic?FirstName=&LastName=Lee
-> HTTP 200, JSON array of diplomates
```

All four endpoints the other run described are live and un-gated:

| Endpoint | Status | Returns |
|---|---|---|
| `GET /searchResults/basic?FirstName=&LastName=` | 200 | name, ABAId, city, state (substring match on surname) |
| `POST /searchResults/advanced` | 200 | same, filtered by City / StateId / ProgramType |
| `GET /doctorRecord/getDoctorRecords?ABAId=<digits>` | 200 | **AreaOfCert, BoardStatus, CertType, issue + expiry dates** |
| `GET /lookups/getCertifications` | 200 | confirms **519 = Pediatric Anesthesiology** |

Two corrections to the other run's write-up, measured here:

- `lookups/getProgramTypes` **404s**. `lookups/getCertifications` is the working name.
- `StateId` is a **GUID**, not an integer. `StateId:"41"` returns `[]` silently —
  a wrong-key zero, exactly the failure `contact-channels.md` warns about.
  South Carolina is `362052dd-247a-df11-b699-001f29d17639`.

**Why the clamped run missed it.** It probed guessable hostnames (`verify.`,
`portal.`, `/verify/`) and stopped at 404. It never did the one thing that
worked: load `theaba.org/directory`, follow it to `directoryreact.theaba.org`,
read the API base out of `main.js`. That is rung 3 of the skill's own ladder,
and the clamped run declared a structural absence from rung 2. **A NONE_FOUND
was published without the denominator behind it** — "no public lookup exists"
is a claim about the world; "three guessed hostnames 404'd" is a claim about
the sweep, and only the second was true.

---

## 2. ABMS — the browser door, opened

`certificationmatters.org` is genuinely browser-only. Re-measured in the same minute:

| Client | Result |
|---|---|
| `curl` (`www`, real UA) | **403** |
| WebFetch | **403** (round-3 clamped) |
| Playwright | **200**, full page |

No challenge was presented and none was solved. A reCAPTCHA **v3** script is
loaded site-wide, attached to the Gravity Forms contact form; the doctor search
is a plain `GET` form (`lname`, `fname`, `state`, `specialty`) and returned
results directly. Nothing was bypassed.

Once the page was loaded, a same-origin `fetch()` from page context served all
120 roster lookups at 200. Records were read from `tr.result-body-row` only —
**page chrome stripped**, so the nav/`<select>` string "Pediatric Anesthesiology"
never entered a match.

### A third silent-truncation class

ABMS caps results for common surnames by **returning the rows and emptying
their text**:

```
lname=Lee&fname=Michelle&state=     -> k=3 rows, all ""   (reads as absence)
lname=Lee&fname=Michelle&state=SC   -> 1 row, WITH the pediatric subspecialty
```

Same shape as NPI `skip=1000` and McLeod `paginationLimitedTo`, but nastier:
the count is non-zero, so a `len(rows)` check passes. A state-scoped retry
across the 27 unmatched recovered **9**, including the one person the whole
benchmark turns on. Detected and corrected inside this run.

---

## 3. What the browser was actually worth

Both bodies were run over the **same 120 people**, so the comparison is clean.

| Certification block filled by | People (of 120) |
|---|---|
| ABA **and** ABMS agree | 101 |
| ABA only (plain fetch) | 6 |
| **ABMS only (browser-unique)** | **1** |
| Neither | 12 |
| **Any body** | **108** |

**The browser's exclusive contribution to this roster is one record:**
Christopher John Samuel, MD, Georgetown SC — *Anesthesiology – Specialty*.
ABA returned three same-name diplomates with no state agreement, so ABA was
correctly withheld; ABMS resolved him uniquely.

Everything else the browser returned, plain `curl` had already returned.

### Marginal vs. round-3 clamped

| | Clamped | Open | Delta | Attributable to |
|---|---|---|---|---|
| People | 120 | 120 | **0** | — |
| Emails | 4 | 4 | **0** | — |
| Pediatric anesthesiologists | 1 | **4** | **+3** | **plain fetch (ABA)** |
| Board-cert blocks filled | 6 | **108** | **+102** | 101 fetch, **1 browser** |
| Department phones | 37 | 37 | **0** | — |

*(The brief listed the clamped run at 0 emails; measured, it carries 4 — three
`pattern_inferred` at `cmc-sc.com` and one `first_party_published` at
`hcahealthcare.com`. Neither run emitted a new address.)*

**The honest reading: the biggest gain in this round is not the browser's.** It
is a plain-fetch source the clamped run wrongly declared nonexistent. Had the
clamped run climbed to rung 3 on `theaba.org`, the browser would have been
worth **one certification block and nothing else** — no new people, no new
emails, no new pediatric hits, no new phones.

---

## 4. The pediatric answer changed

The ring contains **four** board-certified pediatric anesthesiologists, not one.
All four are corroborated **independently by both certifying bodies**, and all
four were already on the roster — nobody new was added.

| Name | Practice location (NPI / hospital directory) | Phone | ABA certificate | ABMS |
|---|---|---|---|---|
| **Desiree Aird** | Myrtle Beach, SC | (843) 692-1062 | Peds Anes, **Certified** 2020-10-31 -> 2030-12-31 | yes |
| **John Gantomasso** | Conway, SC | (843) 347-7111 | Peds Anes, **Certified** 2021-02-20 -> 2031-12-31 | yes |
| **Michelle Lee** | Little River, SC | 843-390-8100 | Peds Anes, **Certified (MOC)** 2026-01-01 -> 2030-12-31 | yes |
| **Andrew Lee Criser** | Myrtle Beach, SC | (843) 692-1000 | Peds Anes, **Certified (MOC)** 2024-01-01 -> 2028-12-31 | yes |

Rounds 1-3 all reported **1**. They were reading hospital directories, which
publish a specialty string; the certifying bodies publish the certificate.
Three of these four have no pediatric signal anywhere in the hospital data.

**Criser is the geography test case, and it was passed the right way.** His ABA
mailing address and his ABMS board-reported address both say **Morgantown, WV**.
He stays in the ring because his **NPI practice location is Myrtle Beach, SC** —
the geography lock comes from the practice address, and the boards' addresses
were never allowed to place or displace anyone. Conversely, **no person was
added from an ABA or ABMS address**: both are mailing/reported addresses, and
`contact-channels.md` already recorded two plausible-but-wrong pediatric
anesthesiologists produced exactly that way.

---

## 5. Negatives, with denominators

- **Board certification: checked 120 of 120.** 108 resolved at a certifying
  body; **12 unresolved** — now the highest-value calls, replacing round 3's
  fifteen. Three (Livigni, Dimitrious, Goerz) matched an ABA ID whose record
  returned **no certificate at all** — checked-and-absent. Two returned nothing
  at either body (Kielar, Czechner). Five failed the **full-forename** lock and
  were withheld rather than guessed (Turner is a CRNA and not ABA-eligible;
  "E J Collins" and "Jonathan Hisghman II" have no usable forename). Two
  (O'Connor, Thomas) had 8 same-name diplomates each with no state agreement —
  withheld at both bodies.
- **New emails: 0, across 120 of 120 checked.** Neither certifying body
  publishes an address. The email ceiling on this roster is unchanged.
- **New department phones: 0, across 120 of 120.** Neither body publishes a phone.
- **New people: 0.** Both sources are name-lookups, not enumerable directories —
  ABMS *requires* at least two surname letters, so it cannot be swept for a
  denominator, and ABA's advanced search caps at 1000.
- **State medical boards: not attempted.** SC LLR (reCAPTCHA v2) and NC Medical
  Board (Turnstile) were left untouched. The browser does not change this and
  the skill forbids it. The zero survives into the open condition unchanged.

## 6. Blocked / structurally closed

| Host | Status |
|---|---|
| `certificationmatters.org` | 403 to all plain fetching; **browser-readable, no challenge**. Now open. |
| `apps.abms.org` | DNS failure — does not resolve. |
| `verify.theaba.org` | DNS failure. Irrelevant: the real API is `directoryreactapi.theaba.org`. |
| SC LLR / NC Medical Board | CAPTCHA-gated. Out of scope, not attempted. |
| Tidelands | 403. Not needed — its anesthesiologists' certifications came from ABA/ABMS. |

## 7. What this changes in the skill

1. `theaba.org` **has** an open diplomate API — the clamped run's "no public
   lookup exists" must be struck. Fix two details: `lookups/getCertifications`
   (not `getProgramTypes`), and `StateId` is a GUID.
2. **ABMS is the only remaining browser-only source in this benchmark**, and it
   is worth ~1% of the certification coverage ABA gives for free. Rung 4 still
   loses to rung 3.
3. **Truncation can hide in the row text, not the row count.** After any result
   set, check the rows have *content*, not just that there are rows.

## Files

- `result.csv` — 120 people, 11 new columns, audit **PASS**
- `aba_records.json` — raw ABA harvest (120 queried)
- `abms_chunk{1,2,3}.json`, `abms_retry.json` — raw ABMS captures
- `aba_harvest.py`, `build.py` — reproducible
