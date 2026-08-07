# Round 4 — ours, clamped: the domain-unlock hunt

**Result: 5 emails, up from 4. Zero wrong-format addresses.**
The rival's 22 stands at roughly 10 real and 12 fabricated. We did not beat 22.
We beat what 22 was worth.

## What the hunt actually found

Two domains were unlocked by spending fetches. **Both turned out to run two
email formats at the same time.** That is the finding of the round, and it is
worse news for the rival than the brief assumed.

### mcleodhealth.org — 9 personal addresses observed, no propagable pattern

Recovered by querying McLeod's own Algolia content indexes (`live_site`,
`live_news`) for indexed page text — the search index the physician finder uses,
pointed at prose instead of provider records:

| Address | Person | Shape |
|---|---|---|
| `Maureen.finger@` | Maureen Finger, Dietetic Internship Director | first.last |
| `maggie.jackson@` | Maggie Jackson, Nurse Recruiting | first.last |
| `logan.doriety@` | *(given in brief)* | first.last |
| `rserrano@` | Raquel Serrano, Cancer Support | **flast** |
| `dsawyer@` | Davis Sawyer, McLeod Foundation | **flast** |
| `aploeg@` `cpernell@` `hburgin@` `jcauble@` | unnamed | **flast-shaped** |

Three name-confirmed `first.last`, two name-confirmed `flast`, four more that
carry no dot and so cannot be `first.last`. **Checked 9 of 9 personal addresses
observed; roughly 6 of 9 are flast.**

The brief scored the rival's `flast` as *wrong* on the strength of one
counter-example. The truth is stranger: **flast is the more common shape on that
domain, and it still isn't safe**, because `first.last` is live alongside it.
No propagation from mcleodhealth.org can be right more than about two-thirds of
the time. **14 roster members, 0 emitted.**

### A round-2 finding, falsified

`references/contact-channels.md` states that *every* McLeod anesthesiologist
carries `mcLeod_physician_associates: false`. Pulling the complete anesthesiology
slice of `live_physicians` — **29 of 29, nbPages 1, no truncation** — shows
**8 TRUE and 21 FALSE**. Bishara, Davidson, Gore, Macpherson, Palliser, Perry,
Pommerenke and Vadney are McLeod-employed.

So the contractor guard alone would *not* have stopped a run from emitting for
two roster members. Only the mixed-format finding does. The denominator lesson,
recurring: round 2 read a sample and wrote a universal.

### orthosc.org — unlocked, and mixed too

`https://www.orthosc.com/contact/` returns a 404 page whose footer still carries
`ann.vennell@orthosc.org`. `/careers/` adds `miranda.amos@orthosc.org` and
`mmccorkle@orthosc.org`. Note the mail domain is **.org**, the website **.com** —
a guess would have missed it.

Two `first.last`, one `flast`. `leadkit emails` returns
**`first.last (pattern_confirmed, 2 samples)`** — and that label is wrong here.
The helper counts votes for the winning pattern and never reports that a rival
format was also observed. **Overridden to `pattern_likely`**, alternate
`kwenz@orthosc.org` shipped in the row.

> **Toolkit defect worth fixing:** `leadkit emails` should downgrade to
> `pattern_likely` and surface the runner-up whenever two or more distinct
> patterns are observed on one domain — the same treatment it already gives
> compound surnames.

## What was emitted

| Person | Address | Label | Why |
|---|---|---|---|
| Kenneth Wenz | `kenneth.wenz@orthosc.org` | `pattern_likely` + alternate | **NEW.** orthosc.org unlocked; downgraded for mixed format |
| Farayi Mbuvah | `farayi.mbuvah@cmc-sc.com` | `pattern_confirmed` | carried, 5 observations |
| Frederick Bellamy | `frederick.bellamy@cmc-sc.com` | `pattern_confirmed` | carried |
| Ihor Melnytskyy | `ihor.melnytskyy@cmc-sc.com` | `pattern_confirmed` | carried |
| Jon Halling | `Jon.Halling@hcahealthcare.com` | `first_party_published` | carried, the only bulk-safe row |

## What was withheld, and why

- **mcleodhealth.org — 14 people.** Mixed format; employment contested.
- **hcahealthcare.com — 5 people.** TeamHealth contractors (`hcaEmployee=false`).
  Re-checked the directory this round: JS shell, no email field, no employment
  flag. Nothing overturned the prior.
- **Joshua Gore — 1.** CMS PECOS says `ORTHOSC LLC`; McLeod's directory says
  `mcLeod_physician_associates: true`. Two first-party-grade sources name
  different employers, so no pattern applies to him.
- **novanthealth.org — 1.** `jsmoreb@` / `mssaylor@` cannot separate
  *f+m+surname* from *f+truncated-surname* on two samples. No third obtainable.
  Emitted nothing, as instructed.
- **cmc-sc.com — 0 marginal.** Conway's `wp-json/wp/v2/providers` payload
  (100 records, 1.5 MB) carries **no email field at all**; the contact page
  re-confirms only `sandy.moore@`. The domain was already fully harvested.

## The domains that stayed shut — and the real reason

**72 of 120 roster members sit on five private anesthesia groups whose mail
domain was never found.** Not blocked — *undiscoverable*:

| Group | Roster | Hostnames DNS-probed | Outcome |
|---|---|---|---|
| Atlantic Coast Anesthesia Services PC | **24** | 10 | all NXDOMAIN |
| Tidelands Anesthesia Group LLC | 13 | 4 | all NXDOMAIN |
| MedStream Anesthesia PLLC | 13 | 9 | all NXDOMAIN |
| Southeast Anesthesiology Consultants PLLC | 11 | 4 | parked lander |
| Providence Anesthesiology Associates PA | 11 | 5 | **critic blog, not the employer** |

Every search transport failed: **WebSearch exhausted (200/200), DuckDuckGo html
returns nothing, Mojeek serves an empty shell, crt.sh 502s on all five
certificate-transparency queries, and Bing `?format=rss` returns HTTP 200 with
unrelated cached results** (Eiffel Tower pages for a MedStream query).

**A live MX is not proof of identity.** `providenceanesthesiology.com` and
`providenceanesthesia.com` both resolve with working mail and both serve a
third-party blog titled *"The Truth About Providence Anaesthesia"*.
`atlanticanesthesia.com` has live Outlook mail and returned 503 — plausible, and
not confirmed, so not used. `beachanesthesia.com` has a working self-hosted mail
server and a **404 at its web root**: mail exists, site does not.

**This is the honest headline for condition A.** The propagation logic was never
the bottleneck. Domain *discovery* is, and it is the one step that requires a
search engine. The rival's volume advantage came from guessing hostnames and
formats; when both are unknowable, the correct output is a thin list.

## Counts

```
120 people, 119 in radius, 1 out (locums)
  primary phone    119  (0 direct, 20 department, 98 practice, 1 answering service)
  secondary phone   46  (0 direct, 17 department, 29 practice)
  department lines  37 total across both columns
  email              5  (1 first_party_published, 3 pattern_confirmed, 1 pattern_likely)
  linkedin           0 verified, 120 search URLs provided
  peds               1 STRONG (Michelle D. Lee, MD), 119 NONE_FOUND
```

**Only the 1 `first_party_published` address clears a 2% bounce ceiling.** The
4 derived rows are for a human to try one at a time — do not load them into a
sequencer.

`python3 leadkit.py audit result.csv` → **PASS: 120 rows; every row sourced,
every email labelled, every phone typed.**
