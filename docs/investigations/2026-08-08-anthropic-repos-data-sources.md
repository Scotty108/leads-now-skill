# What Anthropic's own repos have on lead data — and what we took

*2026-08-08. Searched the `anthropics` org via the GitHub API; WebSearch was
exhausted for the session.*

## The headline: nobody official does free public sourcing

`anthropics/knowledge-work-plugins` is the official plugin set, and its
`sales/CONNECTORS.md` states the position plainly:

> | Data enrichment | `~~data enrichment` | **Clay, ZoomInfo, Apollo** | Clearbit, Lusha |

Its `sales/.mcp.json` wires Clay's MCP directly (`api.clay.com/v3/mcp`), and
there is a `partner-built/apollo/` plugin. The lead skills — `lead-triage`,
`call-list` — both **start from "pull leads from HubSpot"**. They rank and route
leads you already bought.

**There is no free public-registry sourcing anywhere in the official plugins.**
That is a validation of this project's position rather than a gap in theirs:
the whole ecosystem assumes the roster already exists, and the roster is exactly
what a registry gives you free.

## Where the real material was: `anthropics/healthcare`

`plugins/healthcare/skills/fraud-detection/` joins claims against **~32 public
reference tables**, all free federal data. Built to catch fraud, not to build
lists — but three mechanisms port directly.

### 1. Resolve from the catalog, never hardcode a URL ⭐ the big one

Their rule, verified live: `data.cms.gov/data.json` carries 158 datasets, and
every CSV sits behind a dated folder **and** a rotating GUID:

```
https://data.cms.gov/sites/default/files/2026-08/303a44ff-27bb-…/Order_and_Referring.csv
```

A hardcoded URL 404s after the next release, and **the failure looks like the
dataset being withdrawn rather than moved.** Our `bulk-sources.md` was
hardcoding URLs; it now resolves by title. Same shape as Socrata's Discovery API
and data.medicaid.gov's DKAN — one rule, three portals.

→ `references/bulk-sources.md`, guarded by `test_resolve_from_catalog_not_url`.

### 2. Seven ways a government site resists you

They catalogue all 51 state Medicaid sites into ~7 architectures — direct file,
monolithic PDF, DOCX, **ASP.NET postback portal** (browser-only, IDs rotate),
HTML-only, **WAF/bot-manager** (curl 403s forever — do not retry), and licence
click-through gates. *The architecture predicts the fix*, so identify it before
spending retries. Plus: **the domain outlives the path.**

→ `references/blocked.md`.

### 3. Read the registry status

Their `fetch-nppes.js` reads `basic.status` — `A` active, `D` deactivated — and
**our ingest never did.** A deactivated provider is a dead lead identical to a
live one on every other field. Sampling 40 of the benchmark roster returned 40
active, so it had not bitten us; that is a property of the sample, not a
guarantee.

Also theirs: a **9-prefix NPI is NPPES-reserved and never issued** — a
data-entry error, not a lookup failure.

→ `registry_status` in `leadkit ingest`, guarded by `test_registry_status_gate`.

## Datasets worth adding to the healthcare pack

All confirmed present in the live catalog:

| Title | Why | Cadence |
|---|---|---|
| `Order and Referring` | Currently eligible to order/refer — **weekly** liveness, far fresher than NPPES | weekly |
| `<Facility> All Owners` (6 variants) | Names the owners behind a facility — a public route into who controls a contracted group | monthly |
| `Medicare Physician & Other Practitioners - by Provider` | Volume per provider; separates a busy practice from a lapsed one | annual |
| `Revoked Medicare Providers and Suppliers` | Exclude before calling | monthly |
| `Opt Out Affidavits` | Opted out of Medicare — different practice model, often different employer | quarterly |

## Not taken

- **OpenSanctions** state Medicaid exclusion aggregation — **CC-BY-NC**, so
  non-commercial only. Their own note says source the underlying state lists
  directly for production.
- The DuckDB reference layer (~37M rows, ~2GB). Right for claims auditing, far
  past what a contact list needs.
- The Clay/Apollo MCP wiring. Paid, and orthogonal to sourcing.
