# Work emails without a verification service

Read this before writing any email address into any output.

The whole of this file exists to enforce one distinction: an address a source **published** is
evidence; an address a **formula** produced is a hypothesis. Both look identical in a spreadsheet
cell, which is why the tier column is not optional.

## What is actually achievable

Measured against observed name-and-address pairs at institutional domains, guessing accuracy is:

| Evidence at the domain | Correct | Implied bounce |
|---|---|---|
| None, using the commonest format | ~36% | ~64% |
| One observed address | ~68% | ~32% |
| **Two or more that unanimously agree** | **~91%** | **~9%** |
| Four or more, unanimous | ~95% | ~5% |

Mailbox providers treat sustained hard bounces above **2%** as a reputation problem and begin
account review around **5%**. So even the best guessing rule does not clear the bar on its own.
That is the finding. Do not hide it by relabelling a guess.

Two consequences:

- **Build observation-first.** Pattern inference is a candidate generator and a ranking signal,
  never a send decision.
- **A weak email tier is not a failed row.** A clinician's published practice phone and an
  organization's contact route are real, sourced, and reachable. Deliver those and say so.

## Get observed addresses before guessing anything

Look for addresses the organization itself published:

- Team, staff, provider, and contact pages.
- Press releases and media-contact blocks.
- Conference programmes, speaker pages, and abstract books.
- **Corresponding-author addresses in published papers** — the richest source of real institutional
  addresses for clinicians and academics, and free to search.
- Public filings, permit applications, and grant records.

Two observed addresses at a domain are worth more than any amount of reasoning about the domain.

## Resolve the domain before the format

For clinicians this is a **larger source of error than the format itself**. One physician plausibly
sits at several domains: the health system, a legacy pre-merger domain still in use, a faculty
practice plan with its own name, the affiliated university, or a private practice. Large systems
run multiple live domains at once with **incompatible formats between them**.

Rules:

- Take the domain from where the *person* appears, not from the system's marketing site.
- If two domains are plausible, you have no domain. Say so; do not pick the prettier one.
- Confirm the domain against an address you observed at it, not against the brand name.

## Learn the format, then apply it

```
python3 scripts/email_pattern.py learn --evidence evidence.csv -o patterns.csv
```

`evidence.csv` needs `email`, `first_name`, `last_name`, and ideally `source_url` — one row per
address you actually saw. The script reports the format, how many distinct people support it, and
the tier.

```
python3 scripts/email_pattern.py apply --roster roster.csv --patterns patterns.csv -o send.csv
```

It writes sendable rows to your output and everything weaker to `held_<output>.csv`. Held rows are
not discarded — they are delivered with a contact route instead of an address.

### Tiers, which go in `email_status`

- `observed` — a source published this exact address. Keep the URL.
- `pattern_confirmed` — two or more observed addresses at this domain agree unanimously, and this
  name has no edge case.
- `pattern_single` — one observation, or rival formats fit equally, or the name has an edge case.
- `unverified_guess` — no observation at the domain, or two people share a name so at most one
  address can be right.

Only `observed` and `pattern_confirmed` are sendable. Never promote a tier because a list looks thin.

### Stop guessing entirely when

- Fewer than two observed addresses at the domain.
- The observations disagree at all. Disagreement means multiple formats are live, which is the norm
  rather than the exception at large and academic organizations.
- The surname is not a single plain-ASCII token — compound, hyphenated, or carrying a particle.
- The format is `first@` and the organization has more than ~30 people, or `flast@` and it has more
  than a few thousand. Collisions make the address wrong without making it look wrong.
- The domain is academic and no observed address has a surname of 8 or more characters, so a
  truncation limit would still be invisible.

### Names

Expand a nickname to the formal name, never the reverse — public pages give the preferred name
while accounts are provisioned from the legal one. Strip credentials and suffixes. Fold accents,
except where the organization is German-speaking, where `ü` conventionally becomes `ue`. The script
handles credentials, suffixes, middle names, particles, and accents; check its output on any name
that is not two plain tokens.

## Hygiene and the send verdict

```
python3 scripts/email_pattern.py hygiene send.csv
```

It rejects infrastructure mailboxes outright — those are complaint desks, and one of them is
literally where a recipient reports you. It flags staffed shared mailboxes separately, because for
a small practice that address is often the only real way in: report it as the organization's contact
route, never inside a personalised send.

It then prices the list and exits non-zero when the projected bounce exceeds the ceiling. That
verdict is information for the user, not a wall — when it fails, deliver the list and state which
remedy applies: send only observed rows, run it through a verification service the user already
pays for, or use the phone and contact routes instead.

## What cannot be checked here, and why

There is **no free way to confirm that a specific mailbox exists**. Say this plainly rather than
implying verification happened.

The classic method — opening an SMTP conversation and asking the server about the address — does
not work, for two independent reasons. The outbound port it needs is blocked by default across
every major cloud platform, so the check cannot even be attempted from most environments. And it
would not answer the question anyway: the large mail security gateways in front of essentially every
health system accept all recipients at the perimeter and decide later, so they say yes to everything.

What *is* checkable offline: syntax and length limits, disposable domains, role prefixes, and
duplicates. The script does all of these. Note also that a domain with no MX record is not
necessarily invalid, since mail can fall back to an address record — only a domain that resolves to
nothing at all is a safe reject.
