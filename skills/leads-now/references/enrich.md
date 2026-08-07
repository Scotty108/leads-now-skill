# Branch: ENRICH — list-first

The user brought a list. It is half-baked: inconsistent headers, duplicates,
partial rows, names carrying credentials, mixed-case domains, maybe a column
that is three fields crammed together. Real exported sheets always are.

Your job is to fill the gaps without damaging what they already had.

## Step 1 — read it before you touch it

Load the file and **show the user what you actually found** before enriching:

- How many rows, how many unique people after normalization
- Which columns map to `full_name / title / org / org_domain / email / phone`
- What is already populated vs blank
- Anything malformed

Column headers lie. `Name` might be `Last, First`. `Company` might hold a
domain. One column might be `Dr. Jane Doe, MD - Mercy Health`. Map by inspecting
values, not by trusting the header.

Never silently drop a row you could not parse. List it.

## Step 2 — normalize into records

Convert to the record shape in `references/record-format.md`, one JSON file.
Keep every original value — enrichment adds columns, it does not overwrite what
the user gave you. If their `title` disagrees with a source you find, keep
theirs and add yours as a separate field rather than replacing it. It is their
data; you do not get to silently correct it.

Set `source` to something like `"user upload: leads_q3.csv"` so provenance
survives into the output.

## Step 3 — resolve the identity gaps

Work in this order, cheapest first:

| Missing | How to get it |
|---|---|
| `org_domain` from a company name | Search the company, take the official site |
| `full_name` from an email | Parse the local part, confirm against the org site |
| `title` | The org's team/provider page, or the registry for clinicians |
| Person exists at all | Registry (NPI) or a second public source |

For clinicians, run the names against the NPI registry — it confirms the person,
their specialty and their city, and it is free. That single step turns a list of
names into a list of *verified* people.

## Step 4 — resolve emails

Group the rows by `org_domain` and run the pattern inference **once per domain**,
not once per person:

```
python3 leadkit.py emails --domain acme.com \
  --known "Jane Doe:jdoe@acme.com" --known "Bob Ray:bray@acme.com" \
  --name "Ann Lee" --name "Carl Ives"
```

The addresses the user already had are your known-good samples — that is the
best thing about an enrichment job. A sheet with 3 real addresses at a domain
unlocks the rest of that domain at `pattern_confirmed`.

If a domain has zero known addresses and you cannot find one on the org's
contact, press or careers pages, that domain's emails stay blank. Do not
hand-write them.

## Step 5 — merge and emit

```
python3 leadkit.py merge records/*.json -o merged.json
python3 leadkit.py csv merged.json -o enriched.csv
```

Put the **user's file first** in the merge order so their values win on conflict.

## Step 6 — report as a diff

An enrichment report is about what changed, not what exists:

- Rows in, unique people out (and how many were duplicates)
- Fields filled, by field: "27 emails added, 14 titles, 9 phones"
- Emails by confidence: `pattern_confirmed` / `pattern_likely` / still blank
- Rows you could not improve, and why
- Anything you could not parse

Then give them the file. If the sandbox has no filesystem the user can reach,
attach it rather than pasting a table.
