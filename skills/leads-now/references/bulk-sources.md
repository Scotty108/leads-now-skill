# Verified bulk sources — free, keyless, no CAPTCHA

Read this when Step 1b classified the population as **Licensed**, **Entity
principal** or **Public payroll**, and you need the actual endpoint.

Everything below was hit live and the counts are real. **Rows marked ✅ were
verified directly; rows marked ◑ were reported by research and not
independently confirmed** — check them before promising a client anything.

**Fetch with your own tools.** The shipped scripts make no network calls, by
design: the Claude apps sandbox has no outbound access, so a script that fetches
is a script that silently fails there.

## The traps that apply to all of them

Both are in `sources.md` and both cost real coverage:

1. **A sample row is not the schema** — `$limit=1` on the carrier census returns
   34 fields and hides `cell_phone`, which has 1.87M values.
2. **`NOT NULL` is not populated** — sentinel strings like `'NA'` masquerade as
   data. Test the value, not the null-ness.

## Phone-bearing sources

| Source | Endpoint | Scale | Status |
|---|---|---|---|
| **FMCSA carrier census** | `data.transportation.gov/resource/az4n-8mr2.json` | 4,480,554 rows; **1,874,212 with `cell_phone`**; `company_officer_1` names a human | ✅ |
| **NPI registry** | `npiregistry.cms.hhs.gov/api/?version=2.1&…` | ~8M clinicians; **two** addresses each, each with its own phone | ✅ |
| **SEC Form D** | search `efts.sec.gov/LATEST/search-index?q=…&forms=D`, then fetch `sec.gov/Archives/edgar/data/{cik}/{accession}/primary_doc.xml` | Named officer + title + issuer phone in one XML | ✅ |
| CA CSLB master list | `cslb.ca.gov/OnlineServices/DataPortal/…` | ~243K licensees, ~47% sole owner | ◑ |
| WA L&I contractors | `data.wa.gov/resource/m8qx-ubtq.json` | ~160K; **PDDL public-domain dedication** | ◑ |
| Oregon CCB | `data.oregon.gov/resource/g77e-6bhs.json` | ~56K, plus a named principal | ◑ |
| NY attorney registrations | `data.ny.gov/resource/eqw2-r5nb.json` | ~311K of 432K with phone | ◑ |

**FMCSA is the standout, and it is the one place free public data beats the
paid vendors outright.** On a one-power-unit carrier the business phone *is* the
owner's mobile — verified: `KENDALL R GUITHER`, phone and cell both
`8158785175`, officer the same person. Contributory networks are fed by office
workers' inboxes, so the person who owns one truck is in nobody's Outlook.

**SEC Form D is the only free source that structurally links a named individual,
their title, and a phone in one document.** Verified on a real filing: `Scope
Anesthesia of North Carolina, PLLC` → `301-651-5496`, `Thomas Wherry`,
Executive Officer. Send a descriptive `User-Agent` with contact details — that
is the SEC's published policy.

**But state the denominator.** Form D only covers entities that raised capital
through a private placement. Searched for two specific anesthesia contractor
groups that had blocked an earlier run: **0 of 2 had filed.** Real channel,
narrow applicability.

## Finding a source for a state you have not worked

Socrata hosts hundreds of state and city portals, and its **catalog** is
queryable — so you never hand-maintain a source list:

```
https://api.us.socrata.com/api/catalog/v1?q=<topic>&only=dataset&limit=40
→ each result carries resource.columns_field_name[]
→ keep datasets with a column matching /phone|telephone|email/
```

✅ Verified: returns Delaware professional licences with `cellphone` and
`companyemailaddress`, Illinois with `home_phone`, Missouri with
`manager_phone`, plus contractor and business-licence files across WA, OR, NY,
LA and AZ.

⚠️ **Coverage is not national.** South Carolina runs no Socrata portal at all —
`data.sc.gov` does not resolve and the catalog holds no SC domain. Check the
state before promising the channel.

## Personal numbers: what is actually there

Some portals publish a genuine personal mobile. Delaware's professional-licence
file has a `cellphone` column, and the positive control passes — `Davidson,
Mark`: company `(302) 684-8030`, **cell `(302) 236-6400`**, genuinely different.

**And the denominator matters more than the example.** Of 588 rows, 30 have a
cellphone and **22 differ from the business line — 3.7%.**

That is the honest shape of free personal-mobile data: real, lawful, published
by a government body, and **thin**. Do not build a plan around it.

## Verified dead ends — do not spend time

- **Secretary of State filings** — no phone column in the bulk layouts checked.
  Useful for *names* to join against a phone-bearing source, not for contact.
- **WHOIS / RDAP** — post-GDPR the registrant fields are empty.
- **OpenCorporates** — now key-gated, returns `401`.
- **SEC company submissions** — publishes a phone, but it is a switchboard.
- **SAM.gov** — phone is FOUO, not in the public tier.
- **NMLS** — terms forbid use "for purposes of soliciting". Do not.
