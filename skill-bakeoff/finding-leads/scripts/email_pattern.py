#!/usr/bin/env python3
"""Learn an organization's email format from observed addresses, apply it, and price the risk.

Offline. Standard library only. Never sends, probes, or resolves anything.
An address this script produces is a DERIVED GUESS, never a verified address. Only an
address a source actually published is `observed`.

  learn --evidence evidence.csv
      evidence.csv needs: email, first_name, last_name  (source_url recommended)
      -> the pattern each domain uses, how many people support it, and the tier

  apply --roster roster.csv --patterns patterns.csv -o out.csv
      roster.csv needs: first_name, last_name, email_domain  (or --domain)
      -> email, email_status, email_risk, plus a separate file for the unsendable tier

  hygiene list.csv --email-col email
      -> role accounts, syntax failures, duplicates, and the expected bounce rate
"""
import argparse, csv, os, re, sys, unicodedata
from collections import defaultdict

# Expected hard-bounce rate per tier, from a leave-one-out measurement over observed
# name/address pairs at institutional domains: a global-prior guess with no observation
# at the domain lands ~36% of the time, one observation ~68%, and two UNANIMOUS
# observations ~91%. Mailbox providers treat sustained hard bounces above 2% as a
# reputation problem and start account review around 5%, so no tier below `observed`
# clears the ceiling on its own. That is the finding, not a defect in the scoring.
BOUNCE_RATE = {"observed": 0.02, "pattern_confirmed": 0.09, "pattern_single": 0.32,
               "unverified_guess": 0.64}
BOUNCE_CEILING = 0.02
SENDABLE = ("observed", "pattern_confirmed")

# RFC 2142 infrastructure and automation mailboxes. These are complaint desks and
# robots; abuse@ is literally where a recipient reports you. Never send to one.
ROLE_HARD = {
    "abuse", "postmaster", "hostmaster", "webmaster", "noc", "security", "usenet",
    "news", "uucp", "ftp", "www", "no-reply", "noreply", "donotreply", "do-not-reply",
    "bounce", "bounces", "mailer-daemon", "root", "admin", "administrator",
}
# Staffed shared mailboxes. Not a person, so they never belong in a personalised
# send, but for a small practice this is often the ONLY real route in — so they are
# reported as the org's contact route rather than deleted.
ROLE_SOFT = {
    "info", "contact", "hello", "help", "support", "sales", "marketing", "billing",
    "accounts", "accounting", "hr", "careers", "jobs", "recruiting", "office", "team",
    "mail", "email", "privacy", "legal", "press", "media", "inquiries", "enquiries",
    "general", "frontdesk", "reception", "appointments", "scheduling", "referrals",
    "medicalrecords", "records", "clinic", "practice", "newpatients",
}
ROLE_LOCALS = ROLE_HARD | ROLE_SOFT

CREDENTIALS = {
    "md", "do", "mbbs", "phd", "dds", "dmd", "dvm", "pharmd", "np", "fnp", "aprn", "pa",
    "pac", "rn", "bsn", "msn", "crna", "do.", "facs", "facc", "faap", "facp", "fache",
    "mph", "mba", "ms", "ma", "bs", "ba", "esq", "cpa", "mha", "edd", "psyd", "lcsw",
}
SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}
PARTICLES = {"van", "von", "de", "del", "della", "der", "den", "di", "da", "dos", "du",
             "la", "le", "st", "mac", "mc", "o"}

PATTERNS = {
    "first.last":  lambda f, l: "%s.%s" % (f, l),
    "firstlast":   lambda f, l: "%s%s" % (f, l),
    "first_last":  lambda f, l: "%s_%s" % (f, l),
    "first-last":  lambda f, l: "%s-%s" % (f, l),
    "flast":       lambda f, l: "%s%s" % (f[:1], l),
    "f.last":      lambda f, l: "%s.%s" % (f[:1], l),
    "f_last":      lambda f, l: "%s_%s" % (f[:1], l),
    "firstl":      lambda f, l: "%s%s" % (f, l[:1]),
    "first.l":     lambda f, l: "%s.%s" % (f, l[:1]),
    "first":       lambda f, l: f,
    "last":        lambda f, l: l,
    "last.first":  lambda f, l: "%s.%s" % (l, f),
    "lastfirst":   lambda f, l: "%s%s" % (l, f),
    "lastf":       lambda f, l: "%s%s" % (l, f[:1]),
    "fl":          lambda f, l: "%s%s" % (f[:1], l[:1]),
}


def die(msg):
    sys.stderr.write("ERROR: %s\n" % msg)
    raise SystemExit(2)


def deaccent(s):
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c))


def clean_name(raw):
    """'Alvarado, Michael A., M.D.' -> ('michael','alvarado'); returns lowercase ascii."""
    s = deaccent(raw or "").strip()
    if not s:
        return "", ""
    if "," in s:
        head, tail = s.split(",", 1)
        toks_tail = [t for t in re.split(r"[\s,]+", tail) if t]
        keep = [t for t in toks_tail if re.sub(r"[^a-z]", "", t.lower()) not in CREDENTIALS | SUFFIXES]
        s = (" ".join(keep) + " " + head).strip() if keep else head.strip()
    toks = [t for t in re.split(r"[\s]+", s) if t]
    out = []
    for t in toks:
        bare = re.sub(r"[^a-zA-Z]", "", t).lower()
        if bare in CREDENTIALS or bare in SUFFIXES or not bare:
            continue
        out.append(t)
    if not out:
        return "", ""
    toks = [re.sub(r"[^a-zA-Z'\-]", "", t).lower() for t in out]
    toks = [t for t in toks if t]
    if not toks:
        return "", ""
    first = toks[0]
    # Walk back from the end to find where the surname starts. A middle name or initial
    # is discarded, but a particle belongs to the surname: collapsing 'van der Berg' to
    # 'berg' invents a surname and hides that it was invented.
    i = len(toks) - 1
    while i - 1 > 0 and toks[i - 1] in PARTICLES:
        i -= 1
    last = " ".join(toks[i:]) if len(toks) > 1 else ""
    return first, last


def local_forms(name):
    """Surnames with a particle, hyphen or apostrophe have several plausible local parts.

    Ordered longest-first so the fully-joined form is the one applied, and the shorter
    variants exist so `learn` can still recognise the format from evidence.
    """
    base = name.strip()
    alt = {base.replace("'", "").replace("-", "").replace(" ", "")}
    if "-" in base:
        alt.add(base.split("-")[0].replace("'", "").replace(" ", ""))
    toks = base.split()
    if len(toks) > 1:
        alt.add(toks[-1].replace("'", "").replace("-", ""))
        alt.add("".join(toks).replace("'", "").replace("-", ""))
    return sorted((a for a in alt if a), key=lambda x: (-len(x), x))


def risks(first, last, dupes):
    r = []
    if not first or not last:
        r.append("incomplete_name")
    if len(first) == 1:
        r.append("initial_only_first")
    if "-" in last or "'" in last:
        r.append("compound_surname")
    toks = last.split()
    if len(toks) > 1:
        r.append("multi_token_surname")
    if toks and toks[0] in PARTICLES:
        r.append("particle_surname")
    if dupes > 1:
        r.append("name_collision_x%d" % dupes)
    return r


def read_csv(path):
    if not os.path.exists(path):
        die("no such file: %s" % path)
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
    except (csv.Error, UnicodeDecodeError) as e:
        die("%s is not readable as CSV (%s). Fix or re-export the file; do not work around it."
            % (path, e))
    if not rows:
        die("%s has a header but no data rows" % path)
    return rows


def need(rows, cols, path):
    missing = [c for c in cols if c not in rows[0]]
    if missing:
        die("%s is missing column(s): %s. It has: %s"
            % (path, ", ".join(missing), ", ".join(rows[0])))


def cmd_learn(args):
    rows = read_csv(args.evidence)
    need(rows, ["email", "first_name", "last_name"], args.evidence)
    per = defaultdict(lambda: defaultdict(set))
    people, bad = defaultdict(set), []
    for r in rows:
        em = (r.get("email") or "").strip().lower()
        if "@" not in em:
            bad.append(em or "(blank)")
            continue
        loc, dom = em.rsplit("@", 1)
        f, l = clean_name("%s %s" % (r.get("first_name", ""), r.get("last_name", "")))
        if not f or not l:
            bad.append(em)
            continue
        people[dom].add((f, l))
        for pname, fn in PATTERNS.items():
            for lf in local_forms(l):
                for ff in local_forms(f):
                    if fn(ff, lf) == loc:
                        per[dom][pname].add((f, l))
    if not per:
        die("no usable evidence rows. Every row needs a real email and a real name.")
    out = []
    for dom, pats in sorted(per.items()):
        ranked = sorted(pats.items(), key=lambda kv: (-len(kv[1]), kv[0]))
        best, sup = ranked[0][0], len(ranked[0][1])
        rivals = [p for p, s in ranked[1:] if len(s) == sup]
        n = len(people[dom])
        if sup >= 2 and not rivals:
            tier = "pattern_confirmed"
        elif sup >= 2 and rivals:
            tier = "pattern_single"   # two formats fit equally; treat as unproven
        else:
            tier = "pattern_single"
        out.append({"domain": dom, "pattern": best, "support_people": sup,
                    "evidence_people": n, "tier": tier,
                    "rival_patterns": " ".join(rivals)})
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["domain", "pattern", "support_people",
                                          "evidence_people", "tier", "rival_patterns"])
        w.writeheader()
        w.writerows(out)
    for o in out:
        print("%-32s %-12s support=%d/%d  %s%s"
              % (o["domain"], o["pattern"], o["support_people"], o["evidence_people"],
                 o["tier"], (" rivals:" + o["rival_patterns"]) if o["rival_patterns"] else ""))
    if bad:
        sys.stderr.write("skipped %d unusable evidence row(s)\n" % len(bad))
    weak = [o for o in out if o["tier"] != "pattern_confirmed"]
    if weak:
        sys.stderr.write(
            "\n%d domain(s) rest on a single person. One address cannot distinguish a format "
            "from a coincidence — find a second published address at that domain before "
            "applying it.\n" % len(weak))
    print("\nwrote %s" % args.out)
    return 0


def cmd_apply(args):
    roster = read_csv(args.roster)
    need(roster, ["first_name", "last_name"], args.roster)
    pats = {}
    if args.patterns:
        for p in read_csv(args.patterns):
            pats[p["domain"].strip().lower()] = p
    counts = defaultdict(int)
    for r in roster:
        f, l = clean_name("%s %s" % (r.get("first_name", ""), r.get("last_name", "")))
        counts[(f, l, (r.get("email_domain") or args.domain or "").strip().lower())] += 1
    keep, dropped = [], []
    for r in roster:
        dom = (r.get("email_domain") or args.domain or "").strip().lower().lstrip("@")
        f, l = clean_name("%s %s" % (r.get("first_name", ""), r.get("last_name", "")))
        existing = (r.get("email") or "").strip().lower()
        rk = risks(f, l, counts[(f, l, dom)])
        if existing and "@" in existing:
            r["email"], r["email_status"] = existing, "observed"
            r["email_risk"] = ";".join(rk)
            keep.append(r)
            continue
        p = pats.get(dom)
        if not dom or not p or not f or not l:
            r["email"] = ""
            r["email_status"] = "no_pattern" if dom else "no_domain"
            r["email_risk"] = ";".join(rk + (["no_evidence_at_domain"] if dom else []))
            dropped.append(r)
            continue
        fn = PATTERNS.get(p["pattern"])
        if not fn:
            die("unknown pattern %r for %s" % (p["pattern"], dom))
        r["email"] = "%s@%s" % (fn(local_forms(f)[0], local_forms(l)[0]), dom)
        tier = p["tier"]
        if ("compound_surname" in rk or "particle_surname" in rk
                or "multi_token_surname" in rk or "initial_only_first" in rk):
            tier = "pattern_single"      # the edge case is exactly where a format breaks
        if any(x.startswith("name_collision") for x in rk):
            tier = "unverified_guess"    # two people, one address: at most one is right
        r["email_status"] = tier
        r["email_risk"] = ";".join(rk)
        (keep if tier in SENDABLE else dropped).append(r)
    cols = list(roster[0].keys())
    for c in ("email", "email_status", "email_risk"):
        if c not in cols:
            cols.append(c)
    def write(path, rows):
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
    write(args.out, keep)
    held = os.path.join(os.path.dirname(os.path.abspath(args.out)) or ".",
                        "held_" + os.path.basename(args.out))
    write(held, dropped)
    tally = defaultdict(int)
    for r in keep + dropped:
        tally[r["email_status"]] += 1
    print("sendable -> %s  (%d rows)" % (args.out, len(keep)))
    print("held     -> %s  (%d rows)" % (held, len(dropped)))
    for k in sorted(tally):
        print("  %-18s %d" % (k, tally[k]))
    print("\nHeld rows are not failures. They are rows whose address could not be established;\n"
          "deliver them with the org's public contact route instead of an invented address.")
    return 0


def cmd_hygiene(args):
    rows = read_csv(args.infile)
    col = args.email_col
    if col not in rows[0]:
        die("no column %r in %s (has: %s)" % (col, args.infile, ", ".join(rows[0])))
    ceiling = args.ceiling
    syn = re.compile(r"^[A-Za-z0-9!#$%&'*+/=?^_`{|}~.-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+$")
    seen, problems, soft, blank, n_status, exp = set(), [], [], 0, 0, 0.0
    tally = defaultdict(int)
    for i, r in enumerate(rows, 2):
        e = (r.get(col) or "").strip().lower()
        st = (r.get("email_status") or "").strip()
        if st:
            n_status += 1
            tally[st] += 1
            exp += BOUNCE_RATE.get(st, BOUNCE_RATE["unverified_guess"])
        if not e:
            blank += 1
            continue
        if not syn.match(e):
            problems.append((i, e, "syntax")); continue
        loc = e.rsplit("@", 1)[0]
        base_loc = loc.split("+")[0]
        if loc in ROLE_HARD or base_loc in ROLE_HARD:
            problems.append((i, e, "role_infrastructure"))
        elif loc in ROLE_SOFT or base_loc in ROLE_SOFT:
            soft.append((i, e))
        if e in seen:
            problems.append((i, e, "duplicate"))
        seen.add(e)
    print("rows: %d   distinct_emails: %d   blank: %d   address_problems: %d"
          % (len(rows), len(seen), blank, len(problems)))
    for i, e, why in problems[:40]:
        print("  line %-5d %-42s %s" % (i, e, why))
    if len(problems) > 40:
        print("  ... %d more" % (len(problems) - 40))
    for k in sorted(tally):
        print("  %-18s %d" % (k, tally[k]))
    if soft:
        print("shared_mailboxes: %d (not a person — deliver as the org's contact route, "
              "never in a personalised send)" % len(soft))
        for i, e in soft[:10]:
            print("  line %-5d %s" % (i, e))
    fail = []
    if problems:
        fail.append("%d address problem(s)" % len(problems))
    if n_status:
        rate = exp / n_status
        print("projected_hard_bounce: %.1f%% over %d classified rows (ceiling %.1f%%)"
              % (rate * 100, n_status, ceiling * 100))
        if rate > ceiling:
            fail.append("projected bounce %.1f%% over the %.1f%% ceiling" % (rate * 100, ceiling * 100))
    else:
        fail.append("no email_status column, so bounce risk cannot be priced")
    if not fail:
        print("PASS: safe to bulk send.")
        return 0
    sys.stderr.write("\nNOT SAFE TO BULK SEND: %s.\n" % "; ".join(fail))
    sys.stderr.write(
        "Addresses derived from a format are not verified addresses, and a list of them rarely\n"
        "clears a bounce ceiling on its own. Do one of these and say which in the delivery:\n"
        "  1. Send only the rows marked observed.\n"
        "  2. Run the list through a verification service the user already pays for.\n"
        "  3. Reach these people on the channel whose value came from a source rather than a\n"
        "     formula — the published practice phone, or the organization's contact route.\n")
    return 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("learn"); a.add_argument("--evidence", required=True)
    a.add_argument("-o", "--out", default="patterns.csv"); a.set_defaults(fn=cmd_learn)
    b = sub.add_parser("apply"); b.add_argument("--roster", required=True)
    b.add_argument("--patterns"); b.add_argument("--domain")
    b.add_argument("-o", "--out", required=True); b.set_defaults(fn=cmd_apply)
    c = sub.add_parser("hygiene"); c.add_argument("infile")
    c.add_argument("--email-col", default="email")
    c.add_argument("--ceiling", type=float, default=BOUNCE_CEILING,
                   help="acceptable projected hard-bounce rate, default %.2f" % BOUNCE_CEILING)
    c.set_defaults(fn=cmd_hygiene)
    args = ap.parse_args()
    raise SystemExit(args.fn(args))


if __name__ == "__main__":
    main()
