#!/usr/bin/env python3
"""Plan NPI registry queries, then turn the fetched JSON into a roster CSV.

Offline. Standard library only. This script NEVER fetches anything: `plan` writes the
URLs, the agent fetches them with its own web tool and saves each response to the path
`plan` assigned, then `parse` reads those files.

  taxonomy "pediatric anesthesiology"
      -> exact registry search strings, plus the PARENT string to broaden with

  plan --taxonomy "Anesthesiology, Pediatric Anesthesiology" --states SC,NC --outdir raw
      -> raw/_plan.tsv : one "savepath <TAB> url" line per fetch

  parse raw --out roster.csv
      -> one row per provider per practice location; reports saturated queries and
         writes raw/_plan_next.tsv when more pages or partitions are required
"""
import argparse, csv, glob, json, os, re, sys, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
TAXONOMY = os.path.normpath(os.path.join(HERE, "..", "assets", "nucc_individual_taxonomy.csv"))
API = "https://npiregistry.cms.hhs.gov/api/"
PAGE = 200          # registry maximum for `limit`
SKIP_MAX = 1000     # registry clamps `skip` here; deeper pages are unreachable
CEILING = SKIP_MAX + PAGE

FIELDS = ["npi", "last_name", "first_name", "middle_name", "credential", "sole_proprietor",
          "matched_term", "primary_taxonomy", "taxonomy_code", "all_taxonomies",
          "license", "license_state", "org_name", "address_1", "address_2", "city", "state",
          "postal_code", "phone", "fax", "location_kind", "enumeration_date", "last_updated",
          "status", "address_shared_by", "source_url"]


def die(msg):
    sys.stderr.write("ERROR: %s\n" % msg)
    raise SystemExit(2)


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-")[:60] or "q"


def load_taxonomy():
    if not os.path.exists(TAXONOMY):
        die("missing taxonomy asset at %s" % TAXONOMY)
    rows = []
    with open(TAXONOMY, encoding="utf-8") as f:
        next(f)
        for line in f:
            p = line.rstrip("\n").split("|")
            if len(p) == 4:
                rows.append(dict(zip(("code", "classification", "specialization", "display"), p)))
    return rows


def search_string(r):
    """The only string the registry's taxonomy_description parameter accepts.

    The registry SEARCHES on the specialization alone, but RETURNS
    'Classification, Specialization' in a result's desc field. Feeding a returned desc
    back in as a query is rejected with 'No taxonomy codes found with entered description'.
    """
    return r["specialization"] or r["classification"]


def cmd_taxonomy(args):
    rows = load_taxonomy()
    q = args.term.lower().strip()
    def hay(r):
        return (r["classification"] + " " + r["specialization"] + " " + r["display"]).lower()
    hits = [r for r in rows if q in hay(r)]
    if not hits:
        toks = [t for t in re.split(r"\W+", q) if len(t) > 3]
        hits = [r for r in rows if toks and all(t in hay(r) for t in toks)]
    if not hits:
        die("no taxonomy matches '%s'. Try a shorter root word (e.g. 'anesthesi', 'cardio')." % args.term)
    print("MATCHES — pass search_string verbatim to `plan --taxonomy`:")
    parents, seen = set(), set()
    for r in sorted(hits, key=lambda r: (r["classification"], r["specialization"]))[:25]:
        s = search_string(r)
        if s not in seen:
            seen.add(s)
            print("  %s  %-46s search_string=%r" % (r["code"], r["display"][:46], s))
        if r["specialization"]:
            parents.add(r["classification"])
    parents = {p for p in parents if p not in seen}
    if parents:
        print("\nPARENT — query these too. A subspecialist who filed only the parent code is\n"
              "invisible to a subspecialty-only search, and that is the usual reason a niche\n"
              "specialty search returns almost nothing:")
        for p in sorted(parents):
            print("  search_string=%r" % p)
    joined = "||".join(sorted(seen) + sorted(parents))
    print("\nPaste this whole string into `plan --taxonomy` — '||' separates terms and every\n"
          "term is queried:\n  --taxonomy %r" % joined)
    return 0


def build_url(taxonomy, state=None, postal=None, city=None, skip=0, etype="NPI-1"):
    q = [("version", "2.1"), ("enumeration_type", etype),
         ("limit", str(PAGE)), ("skip", str(skip))]
    if taxonomy:
        q.append(("taxonomy_description", taxonomy))
    if state:
        q.append(("state", state))
    if postal:
        q.append(("postal_code", postal))
    if city:
        q.append(("city", city))
    return API + "?" + urllib.parse.urlencode(q)


def cmd_plan(args):
    taxes = [t.strip() for t in args.taxonomy.split("||") if t.strip()] or [None]
    if taxes == [None] and args.etype != "NPI-2":
        die("--taxonomy is required for an individual search. Without it the results are dominated "
            "by behaviour technicians and trainees rather than the profession you want. "
            "Run `taxonomy <term>` to get the exact string.")
    if taxes == [None] and not (args.postal or args.cities or args.states):
        die("an organization sweep needs --zip3 or --cities to bound it.")
    states = [s.strip().upper() for s in args.states.split(",") if s.strip()] if args.states else [None]
    zip3s = [z.strip() for z in args.postal.split(",") if z.strip()] if args.postal else [None]
    cities = [c.strip() for c in args.cities.split(",") if c.strip()] if args.cities else [None]
    os.makedirs(args.outdir, exist_ok=True)
    lines = []
    for t in taxes:
        for st in states:
            for z in zip3s:
                for c in cities:
                    name = "npi__%s__%s__%s__s0.json" % (
                        slug(t) if t else "orgs", st or "any", slug(c) if c else (z or "all"))
                    lines.append((os.path.join(args.outdir, name),
                                  build_url(t, state=st, postal=(z + "*") if z and len(z) < 5 else z,
                                            city=c, skip=0, etype=args.etype)))
    path = os.path.join(args.outdir, "_plan.tsv")
    with open(path, "w", encoding="utf-8") as f:
        for sp, url in lines:
            f.write("%s\t%s\n" % (sp, url))
    print("wrote %s with %d fetch(es)" % (path, len(lines)))
    for sp, url in lines:
        print("  %s\n    %s" % (sp, url))
    print("\nFetch each url and save the body verbatim to its savepath, then run:"
          "\n  python3 scripts/npi_query.py parse %s --out roster.csv" % args.outdir)
    return 0


def read_rows(path):
    if not os.path.exists(path):
        die("no such file: %s" % path)
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))
    except (csv.Error, UnicodeDecodeError) as e:
        die("%s is not readable as CSV (%s)" % (path, e))


def norm_zip(v):
    d = "".join(c for c in str(v or "") if c.isdigit())
    return d[:5]


def term_of(url):
    """Which search term pulled this record in — the reason it is on the list."""
    try:
        return urllib.parse.parse_qs(urllib.parse.urlparse(url).query).get("taxonomy_description", [""])[0]
    except Exception:
        return ""


def rows_from_record(rec, source_url, matched_term=""):
    b = rec.get("basic") or {}
    taxes = rec.get("taxonomies") or []
    prim = next((t for t in taxes if t.get("primary")), taxes[0] if taxes else {})
    base = {
        "npi": rec.get("number", ""),
        "matched_term": matched_term,
        "last_name": (b.get("last_name") or b.get("organization_name") or "").title(),
        "first_name": (b.get("first_name") or "").title(),
        "middle_name": (b.get("middle_name") or "").title(),
        "credential": (b.get("credential") or "").replace(".", "").strip(),
        "sole_proprietor": (b.get("sole_proprietor") or "").upper()[:1],
        "primary_taxonomy": prim.get("desc", ""),
        "taxonomy_code": prim.get("code", ""),
        "all_taxonomies": "; ".join(sorted({t.get("desc", "") for t in taxes if t.get("desc")})),
        "license": prim.get("license", ""),
        "license_state": prim.get("state", ""),
        "org_name": b.get("organization_name", "") or "",
        "enumeration_date": b.get("enumeration_date", ""),
        "last_updated": b.get("last_updated", ""),
        "status": b.get("status", ""),
        "source_url": "https://npiregistry.cms.hhs.gov/provider-view/%s" % rec.get("number", ""),
    }
    seen, out = set(), []
    def add(a, kind):
        z = norm_zip(a.get("postal_code"))
        key = (a.get("address_1", "").upper().strip(), z)
        if not z or key in seen:
            return
        seen.add(key)
        r = dict(base)
        r.update({"address_1": a.get("address_1", ""), "address_2": a.get("address_2", ""),
                  "city": (a.get("city") or "").title(), "state": a.get("state", ""),
                  "postal_code": z, "phone": a.get("telephone_number", ""),
                  "fax": a.get("fax_number", ""), "location_kind": kind})
        out.append(r)
    for a in rec.get("addresses") or []:
        if (a.get("address_purpose") or "").upper() == "LOCATION":
            add(a, "primary_practice")
    for a in rec.get("practiceLocations") or []:
        add(a, "other_practice")
    if not out:
        for a in rec.get("addresses") or []:
            add(a, "mailing_only")
    return out


def cmd_parse(args):
    files = sorted(f for f in glob.glob(os.path.join(args.indir, "*.json")))
    if not files:
        die("no .json files in %s — fetch the planned urls first" % args.indir)
    plan = {}
    ppath = os.path.join(args.indir, "_plan.tsv")
    if os.path.exists(ppath):
        for line in open(ppath, encoding="utf-8"):
            if "\t" in line:
                sp, url = line.rstrip("\n").split("\t", 1)
                plan[os.path.basename(sp)] = url
    all_rows, saturated, empty, bad = [], [], [], []
    npis = set()
    for path in files:
        base = os.path.basename(path)
        if base.startswith("_"):
            continue
        try:
            data = json.load(open(path, encoding="utf-8"))
        except Exception as e:
            bad.append("%s (%s)" % (base, e))
            continue
        if isinstance(data, dict) and data.get("Errors"):
            bad.append("%s -> registry error: %s" % (base, data["Errors"]))
            continue
        res = (data or {}).get("results") or []
        if not res:
            empty.append(base)
            continue
        url = plan.get(base, "")
        term = term_of(url)
        for rec in res:
            npis.add(rec.get("number"))
            all_rows.extend(rows_from_record(rec, url, term))
        if len(res) >= PAGE:
            saturated.append((base, url))
    bykey = {}
    for r in all_rows:
        k = (r["npi"], r["address_1"].upper().strip(), r["postal_code"])
        if k in bykey:
            prev = bykey[k]
            terms = [t for t in (prev["matched_term"], r["matched_term"]) if t]
            prev["matched_term"] = "; ".join(sorted(set(terms)))
            continue
        bykey[k] = r
    rows = list(bykey.values())
    # One address carrying dozens of individuals is a corporate headquarters, a billing
    # service, or a credentialing agent — not a place the person can be reached.
    def addrkey(r):
        a = re.sub(r"[^a-z0-9]", "", (r["address_1"] + r["postal_code"]).lower())
        a = a.replace("suite", "ste").replace("street", "st")
        return a
    shared = {}
    for r in rows:
        shared[addrkey(r)] = shared.get(addrkey(r), 0) + 1
    for r in rows:
        r["address_shared_by"] = shared[addrkey(r)]
    hq = sorted({(v, r["address_1"], r["city"]) for r in rows
                 for v in [shared[addrkey(r)]] if v > 50}, reverse=True)
    rows.sort(key=lambda r: (r["last_name"], r["first_name"], r["postal_code"]))
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print("files_read: %d   distinct_providers: %d   location_rows: %d" % (len(files), len(npis), len(rows)))
    print("wrote %s" % args.out)
    for v, a1, city in hq[:5]:
        sys.stderr.write("SHARED ADDRESS: %d individuals list %s, %s — treat as an employer or "
                         "billing address, not a reachable practice site.\n" % (v, a1, city))
    if empty:
        print("empty_responses: %d (%s)" % (len(empty), ", ".join(empty[:4])))
    if bad:
        for b in bad:
            sys.stderr.write("BAD FILE: %s\n" % b)
    nxt, truncated = [], []
    for base, url in saturated:
        if not url:
            sys.stderr.write(
                "UNTRACKED: %s is full but has no url in _plan.tsv, so its next page cannot be "
                "derived. Re-run `plan` so every fetch is recorded, then fetch and parse again.\n" % base)
            continue
        m = re.search(r"[?&]skip=(\d+)", url)
        cur = int(m.group(1)) if m else 0
        if cur < SKIP_MAX:
            sp = os.path.join(args.indir, re.sub(r"__s\d+\.json$", "__s%d.json" % (cur + PAGE), base))
            # Re-queueing a page that is already on disk is what makes a fetch loop never end.
            if not os.path.exists(sp):
                nxt.append((sp, re.sub(r"([?&]skip=)\d+", r"\g<1>%d" % (cur + PAGE), url)))
        else:
            truncated.append((base, url))
    if nxt:
        np_ = os.path.join(args.indir, "_plan_next.tsv")
        with open(np_, "w", encoding="utf-8") as f:
            for sp, url in nxt:
                f.write("%s\t%s\n" % (sp, url))
        # _plan.tsv is the cumulative index of every fetch. Without appending here, the
        # next parse cannot resolve the page it just asked for and re-requests it forever.
        known = set(plan)
        with open(ppath, "a", encoding="utf-8") as f:
            for sp, url in nxt:
                if os.path.basename(sp) not in known:
                    f.write("%s\t%s\n" % (sp, url))
        print("\nINCOMPLETE: %d quer%s returned a full page, so more results exist."
              % (len(nxt), "y" if len(nxt) == 1 else "ies"))
        print("Fetch every url in %s to its savepath, then run parse again." % np_)
        return 3
    if truncated:
        sys.stderr.write(
            "\nTRUNCATED: %d quer%s still full at the registry ceiling of %d records, so an unknown\n"
            "number of providers is missing and NO COUNT FROM THIS RUN IS A TOTAL.\n"
            % (len(truncated), "y is" if len(truncated) == 1 else "ies are", CEILING))
        for base, url in truncated:
            sys.stderr.write("  %s\n" % base)
        sys.stderr.write(
            "Split each one and fetch again, descending this ladder only as far as it takes.\n"
            "A postal prefix is enough for most areas but NOT for a dense metro, where a single\n"
            "5-digit ZIP can hold more than the ceiling on its own:\n"
            "  1. --zip3 with the prefixes from `geo_filter.py resolve`\n"
            "  2. --zip3 with full 5-digit ZIPs\n"
            "  3. --cities with the individual city names\n"
            "  4. a narrower --taxonomy\n")
        return 4
    print("\nCOMPLETE: no query returned a full page, so every matching record was retrieved.")
    return 0



def addr_norm(a1, zipc):
    """Address key for joining individuals to the organizations at their site."""
    a = (a1 or "").lower()
    for long, short in (("suite", "ste"), ("street", "st"), ("avenue", "ave"),
                        ("parkway", "pkwy"), ("boulevard", "blvd"), ("drive", "dr"),
                        ("road", "rd"), ("north", "n"), ("south", "s"),
                        ("east", "e"), ("west", "w"), ("floor", "fl")):
        a = a.replace(long, short)
    a = re.sub(r"\b(ste|rm|fl|unit|bldg)\s*[a-z0-9-]+", "", a)
    a = re.sub(r"[^a-z0-9]", "", a)
    return a + "|" + (zipc or "")[:5]


def cmd_employers(args):
    """Join individuals to the organizations enumerated at the same practice address.

    An individual registry record carries no employer. Organizations enumerate at the same
    street address, so the address is the join key — and it surfaces the physician GROUP,
    which is usually a different entity, and a different email domain, from the hospital.
    """
    people = read_rows(args.roster)
    if not people:
        die("%s has no rows" % args.roster)
    for c in ("address_1", "postal_code"):
        if c not in people[0]:
            die("%s needs an '%s' column (run `parse` first)" % (args.roster, c))
    orgs = {}
    files = [f for f in sorted(glob.glob(os.path.join(args.orgdir, "*.json")))
             if not os.path.basename(f).startswith("_")]
    if not files:
        die("no .json files in %s — plan with --etype NPI-2 and fetch them first" % args.orgdir)
    nbad = 0
    for path in files:
        try:
            data = json.load(open(path, encoding="utf-8"))
        except Exception:
            nbad += 1
            continue
        if isinstance(data, dict) and data.get("Errors"):
            nbad += 1
            continue
        for rec in (data or {}).get("results") or []:
            name = ((rec.get("basic") or {}).get("organization_name") or "").strip()
            if not name:
                continue
            for a in (rec.get("addresses") or []) + (rec.get("practiceLocations") or []):
                if (a.get("address_purpose") or "").upper() != "LOCATION":
                    continue
                k = addr_norm(a.get("address_1"), norm_zip(a.get("postal_code")))
                orgs.setdefault(k, set()).add(name)
    def stems(text):
        return {w[:7] for w in re.split(r"[^a-z]+", (text or "").lower()) if len(w) > 5}

    hits, ranked_hits = 0, 0
    for r in people:
        k = addr_norm(r.get("address_1"), r.get("postal_code"))
        cands = sorted(orgs.get(k, []))
        # A medical office building holds many unrelated tenants. Rank an organization
        # first when its name shares a word stem with the person's specialty, which is
        # what distinguishes the physician group from the neighbours.
        want = stems(r.get("primary_taxonomy")) | stems(r.get("matched_term"))
        scored = sorted(cands, key=lambda o: (0 if (stems(o) & want) else 1, o))
        r["org_candidates"] = "; ".join(scored[:6])
        r["org_candidate_count"] = len(cands)
        r["org_specialty_match"] = "yes" if (scored and (stems(scored[0]) & want)) else ""
        if cands:
            hits += 1
        if r["org_specialty_match"]:
            ranked_hits += 1
    cols = list(people[0].keys())
    for c in ("org_candidates", "org_candidate_count", "org_specialty_match"):
        if c not in cols:
            cols.append(c)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(people)
    print("organizations indexed: %d addresses from %d file(s)%s"
          % (len(orgs), len(files), (" (%d unreadable)" % nbad) if nbad else ""))
    print("rows with at least one organization at their address: %d of %d (%.0f%%)"
          % (hits, len(people), 100.0 * hits / len(people)))
    print("rows whose top candidate matches their specialty: %d (%.0f%%)"
          % (ranked_hits, 100.0 * ranked_hits / len(people)))
    print("wrote %s" % args.out)
    print("\nA site with several organizations is normal: the hospital, the physician group, and\n"
          "the billing entity all enumerate there. Pick the employer from the group whose name\n"
          "matches the person's specialty, and confirm it against a page that names them.")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("taxonomy"); t.add_argument("term"); t.set_defaults(fn=cmd_taxonomy)
    p = sub.add_parser("plan")
    p.add_argument("--taxonomy", default="", help="exact search_string; join several with ||. "
                                                  "Omit only for an NPI-2 organization sweep.")
    p.add_argument("--states", help="comma separated, e.g. SC,NC")
    p.add_argument("--zip3", dest="postal",
                   help="comma separated postal prefixes (3 or 5 digit); splits a saturated query")
    p.add_argument("--cities", help="comma separated city names; splits harder than postal in dense metros")
    p.add_argument("--etype", default="NPI-1", choices=["NPI-1", "NPI-2"])
    p.add_argument("--outdir", default="raw")
    p.set_defaults(fn=cmd_plan)
    e = sub.add_parser("employers", help="join individuals to organizations at the same address")
    e.add_argument("--roster", required=True)
    e.add_argument("--orgdir", required=True, help="dir of fetched NPI-2 responses")
    e.add_argument("-o", "--out", required=True)
    e.set_defaults(fn=cmd_employers)
    q = sub.add_parser("parse")
    q.add_argument("indir")
    q.add_argument("--out", required=True)
    q.set_defaults(fn=cmd_parse)
    a = ap.parse_args()
    raise SystemExit(a.fn(a))


if __name__ == "__main__":
    main()
