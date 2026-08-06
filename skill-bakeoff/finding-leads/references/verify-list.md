# VERIFY — score a list the user already has

The question is "which of these rows can I act on", so the output is a **verdict per row plus a
ranked list of what to fix**, not a general opinion about the file.

Verify by re-deriving, not by re-reading. Confirming a row against the same page it came from tests
nothing.

## Check each row against four failure modes

Score every row on all four. They fail independently, and a row can be perfectly sourced and still
be two years stale.

1. **Sourced.** Does `source_url` open, and does it still contain this person? A dead link or a page
   that no longer names them drops the row to `unconfirmed` immediately.
2. **Current.** Does the person still hold this role at this organization? Staff pages, registry
   update dates, and recent announcements answer this. Anything only supported by a source with no
   date is `probable` at best.
3. **Corroborated.** Does a second, independent source agree? Two pages of the same site are one
   source. A registry plus the employer's own page are two.
4. **Reachable.** Is there a route to this person that came from a source rather than a formula —
   a published address, a published phone, or a contact route?

## Then run the mechanical checks

```
python3 scripts/email_pattern.py hygiene list.csv --email-col email
python3 scripts/audit_list.py list.csv
```

Between them these catch role addresses, syntax failures, duplicate addresses, duplicate identities,
missing sources, addresses carrying no tier, and a projected bounce rate over the ceiling. Do these
first: they are free, exact, and they usually explain most of a bad list before any judgement is
applied.

## The staleness signals that actually predict a bad row

- A registry record not updated in several years. This is the common case, not the exception:
  about half of individual registry records are five or more years old and roughly a third are ten
  or more, so an old `last_updated` lowers confidence in the *address and employer* while leaving
  the identity intact. Downgrade the row's employer claim, not the person.
- A title containing "Interim", "Acting", or "Co-" — these expire quietly and quickly.
- An organization that merged or was acquired. Both the domain and the employer name may be wrong
  while the person is right, and that combination bounces while looking correct.
- A single-source row whose one source is an aggregator, a conference programme, or a press release.
  These are the rows most likely to be a former employee.

## Deliver

Return the file with `confidence`, `email_status`, and a `verify_note` naming the specific reason
for any downgrade — "profile page no longer lists this person", not "could not verify".

Then, above it:

- Counts by verdict, from the audit script.
- The **top three fixes ranked by rows recovered per unit of work**. "Twelve rows share one
  organization whose directory is readable in a browser" beats a list of twelve individual problems.
- What the run could not check, and why.

Never silently drop a row. A user who sees 200 rows become 140 with no accounting cannot tell
whether the list improved or the run failed.
