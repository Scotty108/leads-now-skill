#!/usr/bin/env python3
"""The delivery gate. Refuses a contact list that cannot show where its facts came from,
and computes the coverage numbers that go in the brief.

Offline. Standard library only.

  audit_list.py final.csv --population 72 --in-radius 72
      -> PASS/FAIL plus a coverage block to paste into the delivery

Fails when a row asserts something it cannot source, because an unsourced row is
indistinguishable from an invented one once it reaches a spreadsheet.
"""
import argparse, csv, os, re, sys
from collections import Counter, defaultdict

REQUIRED = ["full_name", "org", "title", "city", "state", "source_url", "confidence"]
TIERS = ["confirmed", "probable", "unconfirmed"]


def die(msg):
    sys.stderr.write("ERROR: %s\n" % msg)
    raise SystemExit(2)


def norm(s):
    return " ".join((s or "").lower().split())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("infile")
    ap.add_argument("--retrieved", "--population", dest="retrieved", type=int,
                    help="distinct people the source returned, before the target filter")
    ap.add_argument("--in-scope", "--in-radius", dest="in_scope", type=int,
                    help="how many of those actually matched the target (radius, firmographics)")
    ap.add_argument("--blocked", default="",
                    help="comma separated orgs that could not be read, with the reason")
    args = ap.parse_args()

    if not os.path.exists(args.infile):
        die("no such file: %s" % args.infile)
    try:
        with open(args.infile, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
    except (csv.Error, UnicodeDecodeError) as e:
        die("%s is not readable as CSV (%s). Fix or re-export the file; do not work around it."
            % (args.infile, e))
    if not rows:
        die("%s has no data rows. Deliver the coverage brief explaining why, never an "
            "empty file on its own." % args.infile)

    cols = list(rows[0].keys())
    missing = [c for c in REQUIRED if c not in cols]
    fails = []
    if missing:
        fails.append("missing required column(s): %s" % ", ".join(missing))

    unsourced, bad_tier, no_email_status = [], [], []
    ident = defaultdict(list)
    for i, r in enumerate(rows, 2):
        if "source_url" in r and not re.match(r"https?://", (r.get("source_url") or "").strip()):
            unsourced.append(i)
        tier = norm(r.get("confidence"))
        if "confidence" in r and tier not in TIERS:
            bad_tier.append((i, r.get("confidence")))
        if (r.get("email") or "").strip() and not (r.get("email_status") or "").strip():
            no_email_status.append(i)
        ident[(norm(r.get("full_name")), norm(r.get("org")))].append(i)

    dupes = {k: v for k, v in ident.items() if len(v) > 1 and k[0]}
    if unsourced:
        fails.append("%d row(s) have no source url (lines %s)"
                     % (len(unsourced), ", ".join(map(str, unsourced[:8]))))
    if bad_tier:
        fails.append("%d row(s) have a confidence outside %s (e.g. line %d = %r)"
                     % (len(bad_tier), "/".join(TIERS), bad_tier[0][0], bad_tier[0][1]))
    if no_email_status:
        fails.append("%d row(s) carry an email with no email_status, so a guess is "
                     "indistinguishable from a published address (lines %s)"
                     % (len(no_email_status), ", ".join(map(str, no_email_status[:8]))))
    if dupes:
        fails.append("%d duplicate identit%s (e.g. %r)"
                     % (len(dupes), "y" if len(dupes) == 1 else "ies", sorted(dupes)[0][0]))

    conf = Counter(norm(r.get("confidence")) for r in rows)
    est = Counter((r.get("email_status") or "none").strip() for r in rows)
    withe = sum(1 for r in rows if (r.get("email") or "").strip())
    withp = sum(1 for r in rows if (r.get("phone") or "").strip())

    print("=== COVERAGE ===")
    if args.retrieved is not None:
        print("retrieved from source:   %d  (searched area, wider than the target)" % args.retrieved)
    if args.in_scope is not None:
        print("matched the target:      %d  <- THIS is the denominator for the brief" % args.in_scope)
    print("delivered rows:          %d" % len(rows))
    print("with an email:           %d (%.0f%%)" % (withe, 100.0 * withe / len(rows)))
    print("with a phone:            %d (%.0f%%)" % (withp, 100.0 * withp / len(rows)))
    print("confidence:              %s" % ", ".join("%s=%d" % (k or "(blank)", v)
                                                    for k, v in conf.most_common()))
    print("email_status:            %s" % ", ".join("%s=%d" % (k, v) for k, v in est.most_common()))
    blocked = [b.strip() for b in args.blocked.split(",") if b.strip()]
    print("unreadable sources:      %s" % ("; ".join(blocked) if blocked else "none"))
    if args.in_scope and len(rows) < args.in_scope:
        print("NOT DELIVERED:           %d who matched the target but are missing from the file — "
              "the brief must account for these" % (args.in_scope - len(rows)))

    if fails:
        sys.stderr.write("\nFAIL\n")
        for f in fails:
            sys.stderr.write("  - %s\n" % f)
        sys.stderr.write("Fix these before delivering. A row that cannot name its source is a "
                         "row the user cannot defend to the person they contact.\n")
        return 1
    print("\nPASS: every row is sourced, tiered, and unique.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
