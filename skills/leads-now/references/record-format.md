# Record format

Write one JSON file per source into `records/`, then merge. Keeping sources in
separate files is what makes corroboration countable — if you append everything
to one file you lose the ability to say "two independent sources agree".

## A record

```json
{
  "full_name": "Sarah Kim, MD",
  "title": "Pediatric Anesthesiologist",
  "org": "Mercy Health",
  "org_domain": "mercyhealth.org",
  "email": null,
  "phone": "843-555-0142",
  "linkedin": null,
  "profile_url": "https://mercyhealth.org/providers/sarah-kim",
  "source": "NPI registry"
}
```

Only `full_name` is required. **Omit or null anything you did not observe** —
never carry a placeholder forward, because the merge treats any non-empty value
as fact.

`source` should name the source, not the file (`"NPI registry"`, not
`"records/3.json"`). It ends up in the CSV as the audit trail.

## How merging behaves

`leadkit merge` keys on normalized name + org, so these collapse to one
person:

- `Sarah Kim, MD`
- `Dr. Sarah Kim`
- `SARAH KIM, M.D.`

For each field the **first non-empty value wins**. Order your inputs so the
most trustworthy source is read first:

```bash
python3 scripts/leadkit.py merge records/npi.json records/hospital.json records/linkedin.json -o merged.json
```

Here NPI's title survives even though the hospital's marketing page also has
one. Reverse the order and you get the marketing title. Choose deliberately.

## Confidence

Two levels, both mechanical — neither is a judgment call:

- `corroborated` — the person appeared in 2+ independent sources
- `single_source` — exactly one

Email confidence is separate and comes from `leadkit emails`:

- `pattern_confirmed` — 2+ known addresses agree on the format
- `pattern_likely` — exactly one known address
- blank — no known address; nothing was generated

A row can be `corroborated` with a blank email. That is a good row: the person
is real and you have not invented a way to contact them.
