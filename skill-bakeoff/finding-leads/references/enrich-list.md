# ENRICH — the user brought a list

The input is somebody's working spreadsheet: inconsistent headers, credentials welded onto names,
duplicate people, blank cells, a URL where a domain belongs. Normalise before enriching, or every
later step inherits the mess and the output looks confidently wrong.

Rehearse on `assets/fixture/messy_list.csv`, which carries each of these defects deliberately.

## 1. Read the file before planning anything

Print the header row and the first few rows. Then state, in one line each:

- How many rows, and how many are complete.
- Which of `name`, `org`, `title`, `domain`, `email`, `phone` are present under some spelling.
- What is missing, which is the actual job.

Never assume the column names. `Name`, `Full Name`, `Contact`, `Provider`, and `Physician` all
appear; so do `Company`, `Employer`, `Practice`, `Organization`, `Website`.

## 2. Normalise

- **Split names.** `Alvarado, Michael A., M.D.` is one person in last-first order with a credential
  and a middle initial. Keep the credential in its own column; it is a useful signal, not noise.
- **Domains.** `https://MyGrandStrandHealth.com/` and `www.mygrandstrandhealth.com` are one domain.
  Strip scheme, `www`, path, and case.
- **Duplicates.** Match on name plus organization, not on name alone — two people share a name more
  often than intuition suggests, and merging them invents a person. When two rows disagree on a
  field, keep both values and mark the row for checking rather than silently choosing.
- **Blank identity.** A row with an organization and a title but no name is a *role to fill*, not a
  person. Move it to a separate section; do not invent a holder for it.

Preserve every original column and append new ones. The user has to reconcile this against their own
file, and reordering their columns makes that job harder for no gain.

## 3. Fill the gaps, cheapest field first

Order matters, because each field unlocks the next:

1. **Organization** — from the domain, or from the registry record if the person is licensed.
2. **Domain** — from the organization's own site. Confirm it resolves to the org, not to a
   look-alike. Read `email-tradecraft.md` on multi-domain organizations before trusting it.
3. **Title and department** — from the organization's own page for that person. A title from a
   conference bio or an old press release is a *former* title; mark it `probable` and note the age
   in `evidence`.
4. **Phone** — the registry or the organization's directory. Published phones are real.
5. **Email** — last, and only under `email-tradecraft.md`.

If the person is a clinician, the registry resolves identity, specialty, licence, and practice
address from a name plus a state in one lookup. Use it before any web search.

## 4. Say what you did to their file

Return, alongside the enriched file:

- Rows in, rows out, and rows merged as duplicates.
- Fill rate per field, before and after.
- Rows changed rather than only added to, since the user needs to re-check those.
- Rows that could not be enriched, grouped by why. "No public directory" and "blocked" are
  different problems with different fixes.

Then run the audit script and fix what it reports.
