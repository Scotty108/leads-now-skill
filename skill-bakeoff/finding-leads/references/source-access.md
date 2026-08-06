# Reading a source that does not want to be read

Read this before fetching anything from an organization's own website.

Most of a lead run is spent trying to read directories. In a sampled test of four health-system
directories in one metro, **one** was readable by ordinary fetching. The other three returned a
JavaScript shell with no names, or refused the request outright. Plan for that, and never let it
end the run silently.

## Climb the ladder. Stop at the first rung that works.

Each rung costs more and breaks more easily than the one above it. Record which rung produced each
row in `source_rung`, so a later repair knows what to retry.

### Rung 1 — a registry or public data API

Structured, authoritative, complete, and it never blocks you. For anyone licensed or enumerated,
this is the whole discovery layer and the directory is only an enrichment. Always exhaust rung 1
before touching an organization's website.

### Rung 2 — ordinary page fetch

Works on server-rendered sites. Ask one question of the response before parsing it: **does the raw
HTML contain the records?** Search it for the markers the page should have — credential tokens like
`MD` or `RN`, or repeated profile link paths. A 200 response with a large body and zero records is
a JavaScript shell, not a page with no people. Go to rung 3.

### Rung 3 — the endpoint the page itself calls

A JavaScript directory is fetching its data from somewhere. Find that and call it directly. This is
**better than a browser, not a fallback from it**: it returns typed fields instead of rendered text
you must re-parse, it pages cleanly, and it is far cheaper.

How to find it:

1. Fetch the page HTML and search it for `api`, `.json`, `graphql`, `search`, or a search-vendor
   hostname. Client-side search widgets embed their host, application id, and a **public,
   search-only** key directly in the page or its script bundle, because the browser needs them.
2. If a network log is available, read the requests the page made and copy the one returning records.
3. Call the endpoint with the same parameters the page used, and page through it.

A worked example: a health-system directory that returned zero names to a plain fetch was backed by
a hosted search index whose id and public search key sat in the page source. Querying that index
directly returned **942 structured provider records** — name, degree, specialties, practice,
coordinates, profile URL.

Scope limit: use only the public, read-only credential the page already ships to every visitor, and
only for the data that page displays publicly. Do not use a discovered key to reach an index,
record, or field the site does not show. If a key unlocks more than the page shows, stop.

### Rung 4 — browser automation, only if this environment has it

The only rung that reads a site using anti-bot fingerprinting, because it *is* a real browser.

**Check availability first and degrade quietly.** Browser tooling exists in some environments and
not others, and where it exists it may need loading before its tools are visible, so absence from
an initial tool list is not proof it is missing — attempt one navigation, and treat a failure as
absence. In this project it appears as tools whose names begin `mcp__playwright__`. If no such
capability is present, do not describe rung 4 to the user as an option and do not stall — finish on
rungs 1 to 3 and record what stayed unread.

Reserve it for: a hard block, a directory with no findable endpoint, or a page that needs
interaction to reveal records. It is slow, so use it on the few organizations that matter, not the
whole frame.

Measured on one blocked directory: ordinary fetch returned **403**; the same URL in a real browser
returned the page with **17 provider profiles**.

## Getting the bytes, not a summary

A structured source has to reach the parsing step **verbatim**. A fetch that returns a readable
summary of a JSON response has destroyed exactly the thing the parser needs, and the failure looks
like an empty result rather than an error.

Use, in order, whichever the environment actually offers:

1. A fetch that writes the raw response body to a path.
2. Retrieving the body inside code and writing it to the path, where code has network access.
3. A summarising fetch, for prose pages only. Never for a registry or an endpoint response.

If none of the three can deliver a verbatim body, the structured path cannot run. Say so and fall
back to reading pages, rather than filling the gap from memory.

## When you hit a wall

Name which wall it is. They need different responses, and calling them all "failed" loses the
distinction the user needs.

| Signal | Wall | Response |
|---|---|---|
| 403, or a challenge interstitial | Bot fingerprinting | Rung 4 if available, else record unreadable |
| 429 | Rate limit | Slow down, retry a few times, then move on |
| "Verify you are human", CAPTCHA | Human check | Hand off to the user, see below |
| 200, big body, zero records | JavaScript shell | Rung 3 |
| 301/308 to another host | Moved | Not a wall — call the new host and continue |
| 200, real page, no directory | No such source | Record it and stop looking |

**Never attempt to defeat a human check.** No solver service, no fingerprint spoofing, no forged
headers to impersonate a browser you are not, no rotating identities to evade a limit. This is a
prohibition on the action, not a preference: the block is the site stating its terms.

**The correct move is a human handoff.** When a browser is available and the user can see it, stop,
tell them exactly which page is blocked and what you need from it, and ask them to clear the check
themselves. Continue from the page they cleared. When no browser is available, or the user is not
present, record the organization as unreadable with the reason and move on.

## A blocked directory is a partial loss, not a dead end

For a licensed population the registry already gave you the person: name, specialty, location,
identifier, and often a practice phone. The directory adds title, department, and subspecialty —
real enrichment, but not discovery. Losing it costs precision, not the list.

For a business population there is no registry backstop, so the company's own site *is* the
discovery layer. That is where rung 4 earns its cost, and where a block genuinely removes people
from the frame. Escalate effort accordingly rather than fighting a wall for data available elsewhere.

Every organization that stayed unread goes in the delivery brief, with which wall it was.
