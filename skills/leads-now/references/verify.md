# Branch: VERIFY — score an existing list

The user has a list and wants to know what they can trust. No new people are
found in this branch; you are grading what is already there.

## The rule this branch enforces

**Do not collapse provenance into a single `verified` flag.** "Verified" hides
the difference between an address a company published on its own contact page
and one generated from a name pattern. Those are not the same risk, and the user
is about to spend sender reputation on the difference.

## Provenance vocabulary

Label every contact route with how it was obtained:

| Label | Meaning | Trust |
|---|---|---|
| `first_party_published` | On the org's own site | Highest |
| `official_filing` | Registry, license, regulatory filing | Highest |
| `public_professional_profile` | Public professional directory | High |
| `role_based` | `info@`, `contact@` — real but not a person | Medium |
| `pattern_inferred` | Built from a confirmed org format | Medium |
| `smtp_accepted` | Server accepted the address | Medium |
| `catch_all` | Domain accepts everything — proves nothing | Low |
| `commercial_provider` | Bought | Depends |
| `previously_delivered` | Mail reached it before | Highest |

`catch_all` deserves the warning. A catch-all domain accepts every address you
throw at it, so an SMTP check returns "valid" for `asdfgh@domain.com`. Treating
that as verification is how a list looks perfect and bounces anyway.

## Checks, cheapest first

**1. Syntax.** Malformed addresses, obvious typos in the domain, whitespace,
`.con`/`.cmo` endings. Free, no network.

**2. Domain resolves and accepts mail.** An MX lookup tells you whether the
domain can receive mail at all. Free, but it needs DNS — so this runs where
there is network access (Claude Code, Cowork). In a sandbox with no outbound
network, skip it and say you skipped it.

```
dig +short MX example.com
```

No MX records means no mail is being delivered there, regardless of how good the
address looks.

**3. Catch-all detection.** Test a deliberately nonsense local part at the
domain. If it is accepted, the domain is catch-all and per-address verification
there is meaningless. Downgrade every inferred address on that domain.

**4. Corroboration.** How many independent sources produced this person? One
source is not wrong, it is just unconfirmed. This already comes out of
`leadkit merge` as `corroborated` / `single_source`.

**5. Staleness.** When was the source page last updated? A provider directory
listing someone who left in 2023 is a confident, wrong row. Where you can see a
date, record it.

## What not to do

Do not run SMTP probes at volume against a domain. Beyond being rude, it gets
your sending infrastructure blocked and can look like a directory-harvest
attack. If you check at all, check sparsely, and never as a bulk sweep.

## Output

Return the list re-sorted by trust, with a short grading summary:

```
Ready to send        18   first_party_published or official_filing
Probably fine        24   pattern_confirmed, MX present, not catch-all
Use with caution      9   pattern_likely, or single_source
Do not send          11   catch-all domain, or no MX
Unusable              6   no email resolved
```

Then say the one thing the user actually needs: **how many rows are safe to
mail today**, not how many rows exist.
