# Getting an actual contact channel

How to turn a name into a way of reaching someone, without inventing anything.

Everything here was measured, most of it against a clinical roster. The vertical
specifics live in `vertical-healthcare.md`; what follows is the part that
transfers to any population.

## The territory is a constraint, not a variable

Someone asks for people **within X of Y**. That geography usually comes from a
territory assignment, a colleague's patch, or a client footprint. **It is not
yours to optimise.**

Maximise inside the ring you were given. Never tell the user a different city
would be a better hunt — they usually cannot go there, and it reads as refusing
the job.

Reporting *adjacent* findings as information is fine and often useful: "18
in-ring; 4 more at 53 miles, just outside". That is a fact they can act on.
"Search somewhere else instead" is not.

## Say which kind of number it is

Registries and directories publish the **practice or switchboard** number, which
is not the same as reaching the person. Label every number:

| `phone_type` | What it is |
|---|---|
| `direct` | A direct dial that rings the person |
| `department` | Their unit, service line or team |
| `practice` | Front desk or main switchboard (the usual default) |
| `answering_service` | After-hours or third party |

Report the split, never the total: *"119 with a phone: 0 direct, 37 department,
82 switchboard"*. A single reachability number invites the reader to think they
have 119 people's contact details.

**Department numbers hide in structured payloads, not on rendered pages.**
Fetching eight organisation pages yielded zero; parsing their directory payloads
and a phone-directory table yielded 37.

### One record often carries TWO numbers — take both

A register may publish more than one address per person, each with its own
phone. NPI publishes a `LOCATION` and a `MAILING` address; reading only the
first threw the second away on every run for months.

Measured on 70 providers:

| | Practice line | Mailing line |
|---|---|---|
| Switchboard-shaped (ends `00`/`000`) | 17% | **3%** |
| Differs from the other number | — | **43%** |

The second number is **~6x less likely to be a front desk**, and in 20 of 70
cases it sits in a different city entirely.

**Do not label it `direct`.** A mailing phone may be a home office, a billing
service, an answering service or a stale practice. The honest label is its own
(`registry_mailing`) and the honest claim is "a second number the person filed",
not "this rings them". Carry it as `phone_alt` and let the caller decide.

Generalise the habit: **enumerate every address block a record exposes** before
concluding you have its phone.

## Email: unlock the domain, then infer conservatively

### One published address unlocks an employer

Budget **3-5 targeted fetches per employer domain** before writing it off:
`/contact`, `/press`, `/newsroom`, press releases, PDFs, job postings, staff
bios, and any directory payload carrying an email field. Rank domains by how
many roster members sit on each and unlock the biggest first.

A rival run produced 22 emails to our 4 purely by doing this. The propagation
logic was never the gap — spending fetches on discovery was.

### Certificate Transparency finds the domains a search engine cannot

Every public TLS certificate is logged, publicly, by design (RFC 6962). Querying
those logs is not scraping: no login, no CAPTCHA, no key, no ToS question, and
**it does not consume a web-search budget** — which matters, because search is
the resource that runs out first.

```
https://api.certspotter.com/v1/issuances?domain=<d>&include_subdomains=true&expand=dns_names
```

Certificates name **sibling and acquired-entity domains** an organisation's
website never mentions. Hostnames beginning `autodiscover.`, `mail.`, `smtp.`,
`owa.`, `webmail.` or `mx` identify which of those domains actually carry mail —
exactly the domains an email pattern would live on.

`crt.sh` is the better-known endpoint and was **returning 502** when measured.
Have a second CT source; do not build on one.

### Then confirm the link with an MX comparison

Two domains sharing an MX **host with the same tenant id** are one mail system,
so a pattern observed on one legitimately applies to the other:

```
tidelandshealth.org          mxa-001b3801.gslb.pphosted.com
gmhsc.com                    mxa-001b3801.gslb.pphosted.com   <- same tenant
georgetownhospitalsystem.org mxa-001b3801.gslb.pphosted.com   <- same tenant
```

The hex or numeric id inside the MX hostname is the discriminator, not the
provider: countless unrelated organisations use Proofpoint or IronPort, so
matching on `pphosted.com` alone proves nothing.

This solves *the employer is not the employer* from the infrastructure side
rather than by guessing. **Positive control before trusting it:** run it against
an organisation whose real mail domain you already know. It correctly
rediscovered a domain relationship that had previously cost four rounds of
manual work.

### But observe the format; never guess it

That same run got roughly **half its addresses wrong** by assuming a shape.
Measured against addresses actually observed:

| It assumed | Observed | |
|---|---|---|
| `first.last@` | `sandy.moore@` | correct |
| `flast@` | `hhawthorne@` | correct |
| `flast@` | `logan.doriety@` | **wrong** |
| `first.last@` | `jsmoreb@` | **wrong** |

**The pattern must come from an address observed on that domain.** Never a house
style, a sibling organisation, or a plausible default.

### A domain can run two formats at once

One domain showed **3 name-confirmed `first.last` AND 2 name-confirmed `flast`**
among 9 observed addresses. Majority-reporting hides a coin flip: no propagation
from a mixed domain beats roughly 2/3 accuracy, far under any usable bounce
ceiling.

**Correct output for a mixed domain is zero addresses.** `leadkit emails`
detects this and downgrades, reporting `mixed_format_domain` and naming the
competing pattern.

### Two samples characterise nothing

Twice a domain's format was called from two observations and was wrong both
times. On a wider sweep one domain proved mixed, and another had **two live
conventions split geographically** across 19 addresses. Two agreeing samples are
the floor for emitting; they are not enough to *characterise* a domain.

### What a confidence label is worth

Leave-one-out accuracy: **36%** from zero observations, **68%** from one, **91%**
from two agreeing. Providers throttle above roughly a **2% bounce rate**.

**No derived tier clears that ceiling** — 91% accurate is 9 bounces per 100, 4x
over the line. Inferred addresses are fine to try one at a time and unsafe to
bulk-send. Only `first_party_published` and `previously_delivered` clear it. Say
so when handing over a list.

### Label how each address was obtained

`first_party_published` / `official_filing` / `public_professional_profile` /
`role_based` / `pattern_inferred` / `smtp_accepted` / `catch_all` /
`commercial_provider` / `previously_delivered`

Never collapse these into one "verified" flag. `catch_all` especially: such a
domain accepts every address, so a validity check passes for nonsense.

## The employer is often not the employer

Large organisations routinely contract out whole functions to outside firms. The
people staffing a building are frequently employed, paid and **emailed** by a
different company on a different domain — one that may have no public web
presence at all.

**Determine who actually employs someone before applying an employer pattern.**
Look for a billing entity, a filing, or a contract note. A directory record
carrying an employment flag is gold.

**A listing is not employment.** A well-sourced case built from an
organisation's own website that three people were its employees was overridden
by a federal filing — and one of them turned out to be delisted entirely. An
employer claim needs a filing, not a page.

**A live MX is not proof of identity.** Two candidate domains had working mail
servers and served an unrelated critic blog; another had working mail and a 404
web root. Confirm the domain belongs to the employer before treating an address
there as real.

## LinkedIn: discover through the index, never automate the site

Do not automate LinkedIn. Its terms forbid automated collection and the account
that gets restricted is the user's.

What is both legitimate and effective: **find the profile through a search
engine's public index, verify it from the result snippet, and record the URL.**
Match on name *plus* role *plus* region before accepting — and refuse when you
cannot. A comparison run using exactly this method recorded ~13 profiles and
correctly declined ~5 it could not confirm.

Where no profile can be confirmed, emit a `linkedin_search_url` the user clicks:

```
https://www.linkedin.com/search/results/people/?keywords=<name>%20<org>
```

Record a verified profile as `linkedin_url`; keep the two columns separate.

## State the denominator with every negative

The most important rule here, because it has produced false claims repeatedly —
including three in an earlier version of this file that a wider sweep overturned.

A partial sweep read 262 of 805 records and reported its zeros as properties of
the world. They were properties of the sample. **"0 emails" is a claim about
reality; "0 emails across 262 of 805" is a claim about your sweep** — and only
the second is true.

Report negatives as `checked N of M`. Treat any zero where `N < M` as
provisional.

**Prove absence with a positive control.** Before recording that a field is
structurally empty, find one record where it is populated. Without that, "the
field was blank" and "I parsed it wrong" are indistinguishable.

**Verify payload keys.** One source returned zero until it was keyed on the
right field name. A wrong key returns an empty list that reads exactly like
absence.

## Registries go stale; credentialing bodies publish mail

An authoritative registry address is authoritative, not fresh. One record had
pointed at the wrong state for years while the person had moved. Cross-check
against a current filing before excluding anyone on location.

Conversely, a certifying or credentialing body usually publishes a **mailing
address**, which is not a practice location at all. Two plausible in-ring
candidates were rejected this way — their real practices were in other states.

## Where the emails actually are

The population decides the ceiling, not the tooling.

- **Organisations with a teaching or research arm publish people.** A faculty
  directory yielded 78 addresses where a comparable non-academic roster yielded
  5. If the ring contains a university, teaching hospital or research institute,
  that directory is the highest-yield free email source available.
- **Practitioner populations mostly publish nothing**, especially where the work
  is contracted out to firms with no web presence.

**Classify the population before predicting the ceiling**, and say which kind
you are working when you report.

## Report the channel breakdown

```
119 people
  phone     119  (0 direct, 37 department, 82 switchboard)
  email       5  (5 first_party_published, 0 inferred)
  linkedin    0 verified, 119 search URLs
```

A reader can act on that. "119 reachable" invites them to think they have 119
people's contact details, which is not what happened.


## Mechanisms that recur in every vertical

Compact rules, each one learned by getting it wrong first.

### Enumerate every territory the ask names

If the request names two places, enumerate both. Twelve consecutive runs
reported "0" for a second named territory that nobody had ever searched. A
territory you did not search returns zero and looks exactly like a territory
with nobody in it.

### Settle a location on the registry practice address

Two runs made opposite errors about the same two people; only a direct registry
check settled it. Neither was right, and each had published its assertion
confidently.

A location claim is settled by the authoritative registry's **practice
address** — not a mailing address, not a credentialing body's address, and never
another run's assertion.

### Full forenames — initials collide

A record matching on surname, initial, employer and city was still a different
person. Many indexes store authors and members by initial, so **the initial
discriminates nothing**. Require the full first name to match; where a source
gives only an initial, treat the match as unconfirmed and discard it.

A near-miss that survives every other check is more dangerous than an obvious
mismatch, because it looks verified. One such match rejected 147 of 151
candidates in a single pass, including one that would have produced a false
positive on the exact trait being searched for.

### Employment status gates pattern inference

Three agreeing addresses at a domain would have confirmed a format for five more
people — until their own records showed them as contractors, not employees. Five
plausible addresses were **withheld**.

A confirmed pattern belongs to an employer's mail domain, not to everyone in its
building. Where employment status is unknown, the pattern **does not apply** to
that person.

### Hosted search indexes cap pagination silently

An index reported `nbHits: 805` but `nbPages: 1` at `hitsPerPage=100`. A blind
browse returns 100 of 805, **looks complete**, and tells you the true total in a
field you did not read.

Always compare the reported total against what you received.

### A partition can itself truncate — recursively

The documented fix for a cap is not immune to the cap. Partitioning by one facet
returned 785 of 805, because two facets each silently hit the same limit.
Another key reached 805 of 805.

**Verify the partition sums to the reported total.** If it does not, partition
finer.

### An empty string is not an absent filter

With the correct key, a search still returned `[]` at HTTP 200 — the API treated
an empty string as a **literal filter value**. The real client sent JSON `null`;
with nulls the identical query returned 860 results.

Read what the site's own client sends before trusting a zero. `""` and `null`
are different queries.

### Prove absence with a positive control

Before recording that a field is structurally empty, find one record where it is
populated — proving **the field exists and renders**. A control profile
returning a filled row is what turned "we found nothing" into "this source is
genuinely absent for these twelve".

Without a control, "the field was blank" and "I parsed it wrong" are
indistinguishable.

### Department lines: rarely published on pages, often in payloads

Fetching organisation pages yielded **no department numbers** at all — they
publish a switchboard and nothing else. The same organisations carried the
department line inside their directory **payloads**. Do not conclude a number
does not exist from the rendered page.

## Vertical packs

Load the matching pack when one exists — it carries the concrete sources,
endpoints and traps for that population:

| Pack | When |
|---|---|
| `vertical-healthcare.md` | Physicians, nurses, allied health, practices |
