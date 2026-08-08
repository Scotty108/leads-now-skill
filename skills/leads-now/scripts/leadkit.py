#!/usr/bin/env python3
"""leadkit — deterministic helpers for lead sourcing. Python 3.8+, stdlib only.

One file, three subcommands, no dependencies — so it runs identically in Claude
Code's Bash, a Claude Chat / Cowork code-execution sandbox, or a plain terminal.

  emails  infer an org's email format from known-good addresses, then apply it
  merge   dedupe people across sources, merging field-by-field with provenance
  csv     write the merged records out with a _source beside every value

The load-bearing behaviour is REFUSAL: with no known address for a domain,
`emails` emits nothing. A guessed address that bounces costs more than a blank
cell, so nothing here ever invents a value to fill a column.

Examples
  python3 leadkit.py emails --domain acme.com \
      --known "Jane Doe:jdoe@acme.com" --known "Bob Ray:bray@acme.com" \
      --name "Ann Lee"
  python3 leadkit.py merge records/*.json -o merged.json
  python3 leadkit.py csv merged.json -o leads.csv
"""
from __future__ import annotations

import argparse
import csv as csvmod
import glob
import gzip
import json
import math
import os
import re
import sys
import unicodedata
import urllib.parse
from collections import Counter

FIELDS = ["full_name", "title", "org", "org_domain", "email", "phone",
          "phone_type", "phone_alt", "phone_alt_type", "linkedin", "profile_url"]

# Location travels with the person, not with a contact channel, so it is merged
# on the same first-non-empty-wins rule but kept out of FIELDS — these are not
# contact channels and must not be counted as one. Without them the merge drops
# every address and `bands` has nothing to measure.
LOC_FIELDS = ["city", "state", "postal_code"]

# Computed by `bands`, not observed. Carried through merge so the pipeline works
# in either order — running bands before merge otherwise dropped the distance
# and emitted an empty dist_mi column, which reads as "nobody has a distance"
# rather than as a step run out of order.
DERIVED_FIELDS = ["dist_mi", "dist_basis"]

# Honorifics and post-nominals. Clinical directories are full of "Jane Doe, MD,
# FAAP" and "Dr. Ann Lee", which would otherwise poison both the inferred email
# pattern and the dedupe key.
NOISE = {"dr", "mr", "mrs", "ms", "prof", "md", "do", "rn", "np", "pa", "phd",
         "dds", "dmd", "jr", "sr", "ii", "iii", "iv", "faap", "facs"}

PATTERNS = {
    "first.last": lambda f, l: f"{f}.{l}",
    "firstlast": lambda f, l: f"{f}{l}",
    "flast": lambda f, l: f"{f[0]}{l}",
    "f.last": lambda f, l: f"{f[0]}.{l}",
    "firstl": lambda f, l: f"{f}{l[0]}",
    "first_last": lambda f, l: f"{f}_{l}",
    "last.first": lambda f, l: f"{l}.{f}",
    "lastf": lambda f, l: f"{l}{f[0]}",
    "first": lambda f, l: f,
    "last": lambda f, l: l,
}


def _ascii(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z]", "", s.lower())


def _tokens(full: str) -> list:
    cleaned = (full or "").split(",")[0]
    toks = [_ascii(t) for t in cleaned.replace(".", " ").split()]
    return [t for t in toks if t and t not in NOISE]


# Surname particles. "van der Berg" and "De La Cruz" have a surname that is more
# than the last token, and orgs disagree about how to compact it (vanderberg,
# berg, van_der_berg). Picking one silently and labelling it pattern_confirmed
# is the worst failure this tool can produce: a fabricated address at top
# confidence. Detect the ambiguity and refuse to be certain about it instead.
PARTICLES = {"van", "von", "de", "del", "della", "der", "den", "di", "da",
             "dos", "das", "du", "la", "le", "el", "al", "bin", "ibn",
             "mac", "mc", "st", "san", "santa", "ter", "ten", "op"}


def split_name(full: str):
    """Return (first, last) using only the final token."""
    t = _tokens(full)
    return (t[0], t[-1]) if len(t) >= 2 else None


def surname_variants(full: str):
    """Return the distinct plausible surnames for a name.

    One entry means the surname is unambiguous. More than one means the name
    carries particles and the org's convention is unknown from the samples.
    """
    t = _tokens(full)
    if len(t) < 2:
        return []
    simple = t[-1]
    # Everything from the first particle onward is arguably the surname.
    idx = next((i for i, tok in enumerate(t[1:], start=1) if tok in PARTICLES), None)
    if idx is None:
        return [simple]
    joined = "".join(t[idx:])
    return [simple] if joined == simple else [joined, simple]



SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v", "md", "do", "phd", "esq",
            "dds", "dmd", "rn", "np", "pa", "cpa", "pe"}


def flip_name(raw):
    """"CARR, DAVID LEE JR" -> "David Lee Carr, Jr".

    Registers publish one combined name field in surname-first order; only
    org-sourced records hand you first and last separately. Flipping naively
    strands the suffix mid-name — a real run emitted "Derek Gabriel Ii Ambrose"
    and "James F Sr Carlevatti", which is what a person sees on the CSV.

    Names that are already forename-first are returned unchanged, so this is
    safe to run over a mixed list.
    """
    raw = (raw or "").strip()
    if "," not in raw:
        return raw
    last, rest = [p.strip() for p in raw.split(",", 1)]
    toks = rest.split()
    # A suffix can sit on either side of the comma: "CARR, DAVID JR" and
    # "CARR JR, DAVID" both occur in the same file.
    suf = [t for t in toks if t.strip(".").lower() in SUFFIXES]
    given = [t for t in toks if t.strip(".").lower() not in SUFFIXES]
    ltoks = last.split()
    lsuf = [t for t in ltoks if t.strip(".").lower() in SUFFIXES]
    lname = [t for t in ltoks if t.strip(".").lower() not in SUFFIXES]
    suf += lsuf
    if not given or not lname:
        return raw
    out = " ".join(t.title() for t in given + lname)
    # Roman numerals and post-nominals are not title-case words: "II", not "Ii".
    def _suf(s):
        s = s.strip(".")
        return s.upper() if s.lower() in ("ii", "iii", "iv", "v", "md", "do",
                                          "phd", "dds", "dmd", "rn", "np",
                                          "pa", "cpa", "pe") else s.title()
    return out + (", " + " ".join(_suf(s) for s in suf) if suf else "")


def search_name(full):
    """The name a person USES, for searching — not the name a register filed.

    Registers carry full legal names; public profiles carry the used name.
    Searching the filed string verbatim returns nothing and looks exactly like
    the person having no profile. Measured live: "Alexandra Anatolievna
    Armstrong" returned 0 results, "Alexandra Armstrong" returned 16. The
    middle name was the whole bug, and only a positive control distinguished
    the empty result from a real absence.
    """
    t = _tokens(full)          # already strips honorifics and post-nominals
    return f"{t[0]} {t[-1]}".title() if len(t) >= 2 else (full or "").strip()


# ---------------------------------------------------------------- geo ------
# Radius resolution. The NPI API takes state and postal code, never a radius,
# so a "within 50 miles" ask has to become a set of states and ZIP prefixes
# before it can be queried. Doing this by hand loses providers across a state
# line — a Myrtle Beach radius reaches into North Carolina, and a SC-only
# search silently drops them.

GEO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "..", "assets", "us_geo.csv.gz")


def _haversine(a1, o1, a2, o2) -> float:
    r = 3958.8
    p1, p2 = math.radians(a1), math.radians(a2)
    dp, do = math.radians(a2 - a1), math.radians(o2 - o1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(do / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def _load_geo():
    zip3, places = [], []
    path = os.path.normpath(GEO_PATH)
    if not os.path.exists(path):
        return None, None
    with gzip.open(path, "rt") as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            f = line.rstrip("\n").split("|")
            if f[0] == "Z3" and len(f) >= 5:
                # extent = how far the prefix's farthest ZIP sits from its
                # centroid. Median is ~38mi, so centroid-only matching against a
                # 50mi radius silently drops adjacent prefixes that are half
                # inside it. Capped: a few prefixes have pathological extents.
                zip3.append((f[1], float(f[2]), float(f[3]),
                             min(float(f[4]), 100.0)))
            elif f[0] == "P" and len(f) >= 5:
                places.append((f[1], f[2], float(f[3]), float(f[4])))
    return zip3, places


def cmd_geo(args) -> int:
    zip3, places = _load_geo()
    if zip3 is None:
        print("error: assets/us_geo.csv.gz missing — cannot resolve a radius",
              file=sys.stderr)
        return 2

    if args.lat is not None and args.lon is not None:
        lat, lon, label = args.lat, args.lon, f"{args.lat},{args.lon}"
    else:
        want = (args.place or "").strip().lower()
        st = (args.state or "").strip().upper()
        hits = [p for p in places if p[0].lower() == want and (not st or p[1] == st)]
        if not hits:
            print(f"error: place {args.place!r} not found"
                  + (f" in {st}" if st else "")
                  + " — pass --lat/--lon instead", file=sys.stderr)
            return 2
        _, hst, lat, lon = hits[0]
        label = f"{args.place}, {hst}"
        if len({h[1] for h in hits}) > 1:
            print(f"warn: {args.place!r} exists in "
                  f"{sorted({h[1] for h in hits})}; used {hst}. "
                  f"Pass --state to disambiguate.", file=sys.stderr)

    # A prefix counts as in-range if any part of it could fall inside the
    # radius. Over-inclusion is the safe direction: the precise filter happens
    # later against each provider's actual address.
    prefixes = sorted(z for z, la, lo, ext in zip3
                      if _haversine(lat, lon, la, lo) - ext <= args.radius)
    states = sorted({p[1] for p in places
                     if _haversine(lat, lon, p[2], p[3]) <= args.radius})

    res = {"center": label, "lat": round(lat, 4), "lon": round(lon, 4),
           "radius_miles": args.radius, "states": states,
           "zip3_prefixes": prefixes}
    if args.json:
        _out(json.dumps(res, indent=2), args.output)
    else:
        _out(f"{label}  r={args.radius}mi\n"
             f"  states:  {','.join(states)}\n"
             f"  zip3:    {','.join(prefixes)}\n"
             f"  ({len(prefixes)} prefixes, {len(states)} state(s))", args.output)
    # A radius that crosses a state line is the case hand-built queries miss.
    if len(states) > 1:
        print(f"note: radius spans {len(states)} states — querying one state "
              f"would drop the rest", file=sys.stderr)
    return 0


# -------------------------------------------------------------- bands ------
# A radius is a guess the user made before seeing the data, and it is routinely
# not the radius they meant — the benchmark ran at 50 miles against a territory
# that was actually 15. Those are not different searches: 15 is a subset. Sweep
# wide once, then band, and every radius is readable off the same run.

BANDS = [15, 25, 50, 100]


# City names arrive the way a human typed them into a directory form, not the
# way the Census writes them. Measured on a 786-row roster: 17 cities failed to
# place and almost none were actually missing — they were spelling variants.
# Each miss demotes a row to a postal-prefix centroid with a ~38 mile median
# extent, which is tolerable at a 50-mile ring and fatal at a 15-mile one.
CITY_ABBREV = {"mt": "mount", "st": "saint", "ft": "fort", "n": "north",
               "s": "south", "e": "east", "w": "west", "nw": "northwest",
               "ne": "northeast", "sw": "southwest", "se": "southeast"}


def _city_key(name):
    """Normalised comparison key: case, punctuation and abbreviations."""
    toks = re.sub(r"[^a-z0-9 ]", " ", (name or "").lower()).split()
    return " ".join(CITY_ABBREV.get(t, t) for t in toks)


def _match_place(city, st, places, _cache={}):
    """City -> centroid, trying progressively looser matches.

    The last rung handles consolidated city-county governments: the Census
    carries "Lexington-Fayette" and "Augusta-Richmond County" where a directory
    writes plain "Lexington" and "Augusta". Prefix matching is only allowed
    across a hyphen boundary, so it cannot turn "Charleston" into
    "Charleston Heights" — that would move a row to a different town.
    """
    if not _cache:
        for nm, pst, la, lo in places:
            _cache.setdefault((_city_key(nm), pst), (la, lo))
            head = _city_key(nm).split(" - ")[0] if " - " in _city_key(nm) else None
            if head:
                _cache.setdefault((head, pst), (la, lo))
    key = _city_key(city)
    hit = _cache.get((key, st)) or (_cache.get((key, "")) if not st else None)
    if hit:
        return hit
    # Consolidated government: gazetteer name is "<query> <county-ish tail>".
    for (nm, pst), pt in _cache.items():
        if pst == st and (nm.startswith(key + " ") and len(key) > 4):
            return pt
    return None


def _locate(rec, places, zip3):
    """Best available centroid for a record, with how good it is.

    City beats postal prefix by a wide margin. A 3-digit prefix has a ~38 mile
    median extent, so banding a 15-mile ring on one is noise dressed as a
    number — it is reported, but labelled, and never silently mixed in with
    city-derived distances.
    """
    city = (rec.get("city") or "").strip()
    st = (rec.get("state") or "").strip().upper()
    if city:
        pt = _match_place(city, st, places)
        if pt:
            return pt[0], pt[1], "city_centroid"
    pc = re.sub(r"[^0-9]", "", str(rec.get("postal_code") or ""))[:3]
    if len(pc) == 3:
        for z, la, lo, _ext in zip3:
            if z == pc:
                return la, lo, "zip3_centroid"
    return None, None, None


def cmd_bands(args) -> int:
    zip3, places = _load_geo()
    if zip3 is None:
        print("error: assets/us_geo.csv.gz missing — cannot measure distance",
              file=sys.stderr)
        return 2

    if args.lat is not None and args.lon is not None:
        clat, clon, label = args.lat, args.lon, f"{args.lat},{args.lon}"
    else:
        want, st = (args.place or "").strip().lower(), (args.state or "").strip().upper()
        hits = [p for p in places if p[0].lower() == want and (not st or p[1] == st)]
        if not hits:
            print(f"error: place {args.place!r} not found — pass --lat/--lon",
                  file=sys.stderr)
            return 2
        _, hst, clat, clon = hits[0]
        label = f"{args.place}, {hst}"

    try:
        rows = json.load(open(args.input))
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"error: {args.input} ({e})", file=sys.stderr)
        return 1
    if isinstance(rows, dict):
        rows = [rows]

    unplaced = 0
    for r in rows:
        la, lo, basis = _locate(r, places, zip3)
        if la is None:
            r["dist_mi"], r["dist_basis"] = None, None
            unplaced += 1
            continue
        r["dist_mi"] = round(_haversine(clat, clon, la, lo), 1)
        r["dist_basis"] = basis

    placed = [r for r in rows if r.get("dist_mi") is not None]
    placed.sort(key=lambda r: r["dist_mi"])

    if args.output:
        json.dump(rows, open(args.output, "w"), indent=2, ensure_ascii=False)
        print(f"wrote {args.output}")

    print(f"{len(rows)} record(s) from {label}")
    prev, cum = 0, 0
    for b in BANDS:
        n = sum(1 for r in placed if r["dist_mi"] <= b)
        if n == cum and b != BANDS[0]:
            continue
        print(f"  within {b:>3} mi   {n:>4}   (+{n - cum} over {prev} mi)")
        prev, cum = b, n

    # The near-miss is the whole point of banding: someone at 51 miles is a fact
    # the user can act on, and a hard cutoff hides them in a way that looks
    # exactly like their not existing.
    edge = [r for r in placed if args.radius < r["dist_mi"] <= args.radius * 1.2]
    if edge:
        print(f"  just outside {args.radius} mi: {len(edge)}")
        for r in edge[:5]:
            print(f"      {r.get('full_name', '?')}  {r['dist_mi']} mi"
                  f"  {r.get('city') or ''}")
    z3 = sum(1 for r in placed if r["dist_basis"] == "zip3_centroid")
    if z3:
        print(f"  note: {z3} row(s) placed by 3-digit postal prefix "
              f"(~38mi median extent) — approximate, not city-accurate")
    if unplaced:
        print(f"  {unplaced} row(s) have no city or postal code and are "
              f"UNPLACED — they are not in any band, including yours")
    return 0


# --------------------------------------------------------------- plan ------

NPI_API = "https://npiregistry.cms.hhs.gov/api/"
NPI_PAGE = 200        # registry maximum for `limit`
NPI_SKIP_MAX = 1000   # registry clamps `skip` here; deeper pages repeat


def cmd_plan(args) -> int:
    """Emit the NPI query URLs to fetch. This script never fetches anything —
    the agent fetches with its own tools, which keeps leadkit network-free and
    therefore runnable in a sandbox that has no outbound access."""
    taxonomies = [t.strip() for t in args.taxonomy.split(",") if t.strip()]
    states = [s.strip().upper() for s in args.states.split(",") if s.strip()]
    lines, n = [], 0
    for tax in taxonomies:
        for st in states:
            for skip in range(0, NPI_SKIP_MAX + 1, NPI_PAGE):
                q = {"version": "2.1", "taxonomy_description": tax,
                     "state": st, "limit": NPI_PAGE, "skip": skip}
                url = NPI_API + "?" + urllib.parse.urlencode(q)
                save = os.path.join(args.outdir,
                                    f"{_slug(tax)}__{st}__{skip:04d}.json")
                lines.append(f"{save}\t{url}")
                n += 1
    os.makedirs(args.outdir, exist_ok=True)
    plan_path = os.path.join(args.outdir, "_plan.tsv")
    with open(plan_path, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"wrote {plan_path}  ({n} fetches: "
          f"{len(taxonomies)} taxonomy x {len(states)} state x pages)")
    print("Fetch each URL with your own web tool and save the VERBATIM response "
          "body to its savepath, then run: leadkit ingest " + args.outdir)
    return 0


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40]


# ------------------------------------------------------------- ingest ------

def cmd_ingest(args) -> int:
    """Read fetched NPI JSON, dedupe by NPI, and detect silent truncation.

    The registry repeats the same page past skip=1000 instead of erroring, so a
    naive pager produces duplicates and a count that looks complete. Exit 3
    means a query saturated its page and more remain; exit 4 means a query hit
    the unreachable ceiling and the result set is provably incomplete."""
    seen, rows, saturated, truncated = {}, [], [], []
    files = sorted(glob.glob(os.path.join(args.indir, "*.json")))
    if not files:
        print(f"no JSON files in {args.indir}", file=sys.stderr)
        return 1

    for path in files:
        try:
            data = json.load(open(path))
        except Exception as e:
            print(f"warn: {os.path.basename(path)} unreadable ({e})",
                  file=sys.stderr)
            continue
        results = data.get("results") or []
        base = os.path.basename(path)
        new_here = 0
        for r in results:
            npi = str(r.get("number") or "")
            if not npi or npi in seen:
                continue
            seen[npi] = base
            new_here += 1
            basic = r.get("basic") or {}
            # Type-2 (organization) NPIs carry no first/last name. Left empty
            # they key to "" and merge drops them silently, so name them from
            # the org and mark the type — an anesthesia GROUP is a useful row,
            # but it is not a person and must not be counted as one.
            person = bool(basic.get("first_name") or basic.get("last_name"))
            tax = next((t for t in (r.get("taxonomies") or [])
                        if t.get("primary")), {})
            addrs = r.get("addresses") or []
            addr = next((a for a in addrs
                         if a.get("address_purpose") == "LOCATION"),
                        addrs[0] if addrs else {})
            # The registry publishes a SECOND address with its OWN phone, and
            # reading only LOCATION threw it away on every run. Measured on 70
            # providers: the mailing phone differs 43% of the time, and is
            # switchboard-shaped (ends 00/000) in 3% of cases against 17% for
            # the practice line — roughly 6x less likely to be a front desk.
            #
            # It is NOT labelled `direct`. A mailing phone may be a home office,
            # a billing service, an answering service or a stale practice; the
            # honest claim is "a second number the provider filed", not "this
            # rings the person".
            mail = next((a for a in addrs
                         if a.get("address_purpose") == "MAILING"), {})
            alt = mail.get("telephone_number")
            if alt and alt == addr.get("telephone_number"):
                alt = None
            rows.append({
                "record_type": "person" if person else "organization",
                "full_name": (" ".join(x for x in [basic.get("first_name"),
                                                   basic.get("last_name")] if x).title()
                              if person else (basic.get("organization_name") or "").title()),
                "title": tax.get("desc"),
                "org": (r.get("basic") or {}).get("organization_name"),
                "org_domain": None,
                "email": None,
                "phone": addr.get("telephone_number"),
                "phone_type": "practice" if addr.get("telephone_number") else None,
                "phone_alt": alt,
                "phone_alt_type": "registry_mailing" if alt else None,
                "phone_alt_city": (mail.get("city") if alt else None),
                "linkedin": None,
                "profile_url": f"https://npiregistry.cms.hhs.gov/provider-view/{npi}",
                "source": "NPI registry",
                "npi": npi,
                "credential": basic.get("credential"),
                "taxonomy_code": tax.get("code"),
                "city": addr.get("city"),
                "state": addr.get("state"),
                "postal_code": addr.get("postal_code"),
            })
        # A full page means the query has more behind it.
        if len(results) >= NPI_PAGE:
            saturated.append(base)
            if f"{NPI_SKIP_MAX:04d}" in base:
                truncated.append(base)
        # A page that added nothing new is the silent-repeat signature.
        elif results and new_here == 0:
            truncated.append(base)

    json.dump(rows, open(args.output, "w"), indent=2, ensure_ascii=False)
    print(f"wrote {args.output}")
    npeople = sum(1 for r in rows if r["record_type"] == "person")
    print(f"  {len(files)} file(s) -> {len(rows)} distinct NPI(s): "
          f"{npeople} people, {len(rows) - npeople} organizations")
    if saturated:
        print(f"  {len(saturated)} query(ies) returned a FULL page — more pages exist")
    if truncated:
        print(f"  TRUNCATED: {len(truncated)} query(ies) hit the ceiling or "
              f"repeated. Partition further (by city or taxonomy) — this result "
              f"set is INCOMPLETE.")
        return 4
    if saturated:
        return 3
    print("  COMPLETE: no query returned a full page.")
    return 0


# ---------------------------------------------------------------- emails ----

def cmd_emails(args) -> int:
    known = []
    for e in args.known:
        if ":" in e:
            n, addr = e.rsplit(":", 1)
            known.append((n.strip(), addr.strip()))
    if args.known_file:
        for line in open(args.known_file):
            if ":" in line.strip():
                n, addr = line.strip().rsplit(":", 1)
                known.append((n.strip(), addr.strip()))

    names = list(args.name)
    if args.names_file:
        names += [l.strip() for l in open(args.names_file) if l.strip()]

    votes: Counter = Counter()
    for full, addr in known:
        if "@" not in addr:
            continue
        local, dom = addr.split("@", 1)
        # An address on another domain says nothing about this org's format.
        if dom.strip().lower() != args.domain.lower():
            continue
        parts = split_name(full)
        if not parts:
            continue
        f, l = parts
        for pname, fn in PATTERNS.items():
            try:
                if fn(f, l) == local.strip().lower():
                    votes[pname] += 1
            except IndexError:
                pass

    if not votes:
        out = {"domain": args.domain, "pattern": None, "confidence": "unknown",
               "reason": "no known-good address for this domain; refusing to guess",
               "resolved": [], "unresolved": names}
        _out(json.dumps(out, indent=2) if args.json else
             f"No pattern for {args.domain} — need at least one known address.\n"
             f"{len(names)} name(s) unresolved. Nothing guessed.", args.output)
        return 0

    top, n = votes.most_common(1)[0]
    tied = sorted([p for p, v in votes.items() if v == n], key=lambda p: (-len(p), p))
    top = tied[0]
    conf = "pattern_confirmed" if n >= 2 else "pattern_likely"

    # A domain can run TWO formats at once. Measured: mcleodhealth.org shows 3
    # name-confirmed first.last AND 2 name-confirmed flast among 9 observed
    # addresses. Reporting the majority as pattern_confirmed hides a coin flip —
    # no propagation from a mixed domain can beat roughly 2/3 accuracy, which is
    # far under any usable bounce ceiling. Downgrade and name the rival, the
    # same treatment an ambiguous surname already gets.
    rivals = {p: v for p, v in votes.items() if p != top and v >= 1}
    mixed = bool(rivals)
    if mixed and conf == "pattern_confirmed":
        conf = "pattern_likely"

    resolved, unresolved = [], []
    for full in names:
        parts = split_name(full)
        if not parts:
            unresolved.append(full)
            continue
        variants = surname_variants(full)
        try:
            candidates = [PATTERNS[top](parts[0], v) for v in variants]
        except IndexError:
            unresolved.append(full)
            continue
        entry = {"name": full, "email": f"{candidates[0]}@{args.domain}",
                 "pattern": top, "confidence": conf,
                 "source": "inferred_from_known_addresses"}
        if len(candidates) > 1:
            # The org's handling of the particle is unknown, so this address is
            # a coin flip between forms. Never let that carry top confidence.
            entry["confidence"] = "pattern_likely"
            entry["ambiguous_surname"] = True
            entry["alternates"] = [f"{c}@{args.domain}" for c in candidates[1:]]
            entry["note"] = ("surname contains a particle; org convention "
                             "unknown — confirm before sending")
        resolved.append(entry)

    res = {"domain": args.domain, "pattern": top, "confidence": conf,
           "evidence_count": n, "candidates_considered": dict(votes),
           "mixed_format_domain": mixed,
           "competing_patterns": rivals or None,
           "resolved": resolved, "unresolved": unresolved}
    if mixed:
        res["warning"] = ("domain runs multiple formats "
                          f"({top} x{n} vs {rivals}); propagation is unsafe — "
                          "verify each address individually")
    if args.json:
        _out(json.dumps(res, indent=2), args.output)
    else:
        lines = [f"{args.domain}: {top} ({conf}, {n} sample(s))"]
        lines += [f"  {r['email']:<40} {r['name']}" for r in resolved]
        lines += [f"  (unresolved) {u}" for u in unresolved]
        _out("\n".join(lines), args.output)
    return 0


# ----------------------------------------------------------------- merge ----

def cmd_merge(args) -> int:
    records = []
    for pat in args.inputs:
        for path in (glob.glob(pat) or [pat]):
            try:
                data = json.load(open(path))
            except FileNotFoundError:
                print(f"warn: {path} not found", file=sys.stderr)
                continue
            except json.JSONDecodeError as e:
                print(f"warn: {path} invalid JSON ({e})", file=sys.stderr)
                continue
            for item in (data if isinstance(data, list) else [data]):
                if isinstance(item, dict) and item.get("full_name"):
                    item.setdefault("source", path)
                    records.append(item)
    if not records:
        print("no usable records", file=sys.stderr)
        return 1

    merged = {}
    for r in records:
        dom = re.sub(r"^www\.", "", (r.get("org_domain") or "").strip().lower())
        # Employer is the natural discriminator, but a REGISTER — the strongest
        # source there is — almost never carries one. With org absent the key
        # degenerates to the name alone and two different people with the same
        # name become one blended row: one person's address against another's
        # licence, which is a fabricated record. Measured on 11,087 Florida
        # roofing licensees: 107 distinct people collapsed that way.
        #
        # Location is the fallback because a register always publishes it. Match
        # on postcode when present, else the normalised city — normalised with
        # the same rules as the geo lookup, so PORT ST LUCIE and PORT SAINT
        # LUCIE at one postcode stay one person rather than splitting.
        loc = re.sub(r"[^0-9]", "", str(r.get("postal_code") or ""))[:5]
        if not loc:
            loc = _city_key(r.get("city") or "")
            st = (r.get("state") or "").strip().upper()
            loc = f"{loc}|{st}" if loc else ""
        key = (" ".join(_tokens(r.get("full_name", ""))),
               dom or _ascii(r.get("org", "")) or loc)
        if not key[0]:
            continue
        if key not in merged:
            # Start every field empty rather than seeding from this record, so
            # the fill loop below is the ONLY place values are set and every
            # field gets its source recorded. Seeding here left the first
            # source's fields with values but no provenance — which silently
            # hollowed out the per-field audit trail this tool exists for.
            e = {f: None for f in FIELDS + LOC_FIELDS + DERIVED_FIELDS}
            e["_sources"], e["_field_sources"] = [], {}
            merged[key] = e
        e = merged[key]
        src = r.get("source") or r.get("profile_url") or "unknown"
        if src not in e["_sources"]:
            e["_sources"].append(src)
        for f in FIELDS + LOC_FIELDS + DERIVED_FIELDS:
            v = r.get(f)
            # First non-empty value wins, so input order encodes trust: put the
            # registry before the marketing page and the registry's title survives.
            if v not in (None, "", []) and e.get(f) in (None, "", []):
                e[f] = v
                e["_field_sources"][f] = src

    out = []
    for e in merged.values():
        c = len(e["_sources"])
        e["_confidence"] = "corroborated" if c >= 2 else "single_source"
        e["_source_count"] = c
        out.append(e)
    out.sort(key=lambda x: (x.get("org") or "", x.get("full_name") or ""))

    if args.output:
        json.dump(out, open(args.output, "w"), indent=2, ensure_ascii=False)
        print(f"wrote {args.output}")
    else:
        print(json.dumps(out, indent=2, ensure_ascii=False))
    corr = sum(1 for m in out if m["_confidence"] == "corroborated")
    em = sum(1 for m in out if m.get("email"))
    print(f"  {len(records)} record(s) in -> {len(out)} person(s)")
    print(f"  {corr} corroborated, {len(out)-corr} single-source")
    print(f"  {em} with an email, {len(out)-em} without")
    return 0


# ------------------------------------------------------------------- csv ----

def cmd_csv(args) -> int:
    try:
        rows = json.load(open(args.input))
    except FileNotFoundError:
        print(f"error: {args.input} not found", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"error: {args.input} invalid JSON ({e})", file=sys.stderr)
        return 1
    if isinstance(rows, dict):
        rows = [rows]

    dropped = 0
    if args.only_with_email:
        keep = [r for r in rows if r.get("email")]
        dropped, rows = len(rows) - len(keep), keep

    header = []
    for f in FIELDS:
        header += [f, f"{f}_source"]
    header += LOC_FIELDS + ["dist_mi", "dist_basis",
                            "confidence", "source_count", "all_sources"]

    # Nearest first: a territory gets worked outward from its centre, so that is
    # the order the list is actually used in. Rows with no distance sort last
    # rather than to the front, where they would look like the closest leads.
    if any(r.get("dist_mi") is not None for r in rows):
        rows = sorted(rows, key=lambda r: (r.get("dist_mi") is None,
                                           r.get("dist_mi") or 0.0))

    with open(args.output, "w", newline="", encoding="utf-8") as fh:
        w = csvmod.writer(fh)
        w.writerow(header)
        for r in rows:
            fs = r.get("_field_sources") or {}
            row = []
            for f in FIELDS:
                row += [r.get(f) or "", fs.get(f, "")]
            row += [r.get(f) or "" for f in LOC_FIELDS]
            row += [r.get("dist_mi") if r.get("dist_mi") is not None else "",
                    r.get("dist_basis") or "",
                    r.get("_confidence", ""), r.get("_source_count", ""),
                    " | ".join(r.get("_sources") or [])]
            w.writerow(row)

    em = sum(1 for r in rows if r.get("email"))
    print(f"wrote {args.output}")
    # Row count alone is misleading: 312 rows with 40 emails is not 312 leads.
    print(f"  {len(rows)} row(s), {em} with an email")
    if dropped:
        print(f"  {dropped} row(s) dropped for having no email")
    return 0



# ------------------------------------------------------------- audit ------

def cmd_audit(args) -> int:
    """Refuse to pass a list whose claims cannot be audited.

    A rule in prose is not a gate. This exits non-zero on the failures that
    make a list untrustworthy, so a run cannot quietly ship one:
      - a row with no source anywhere (unsourced)
      - an email with no confidence label
      - an email on a domain with no observed address (a guess)
      - a phone with no phone_type (a switchboard passed off as a contact)
    """
    try:
        with open(args.input, newline="", encoding="utf-8") as fh:
            rows = list(csvmod.DictReader(fh))
    except FileNotFoundError:
        print(f"ERROR: {args.input} not found", file=sys.stderr)
        return 2
    if not rows:
        print("ERROR: no data rows", file=sys.stderr)
        return 2

    ROW_PROV = ("source", "source_url", "all_sources", "evidence", "profile_url")
    problems = []
    for i, r in enumerate(rows, start=2):
        who = (r.get("full_name") or f"row {i}").strip()

        has_src = any((r.get(c) or "").strip() for c in ROW_PROV) or \
            any(k.endswith("_source") and (v or "").strip() for k, v in r.items())
        if not has_src:
            problems.append(f"{who}: unsourced — no source on any field")

        email = (r.get("email") or "").strip()
        if email:
            conf = (r.get("email_confidence") or r.get("confidence")
                    or r.get("email_status") or "").strip().lower()
            if not conf or conf in ("unknown", "guess", "guessed"):
                problems.append(f"{who}: email {email} has no confidence label")
            elif conf in ("pattern_likely", "pattern_confirmed") and \
                    not (r.get("email_source") or "").strip():
                problems.append(f"{who}: inferred email {email} names no source")

        phone = (r.get("phone") or "").strip()
        if phone and not (r.get("phone_type") or "").strip():
            problems.append(f"{who}: phone {phone} has no phone_type "
                            f"(a switchboard is not a direct dial)")

    n = len(rows)
    if problems:
        print(f"FAIL: {len(problems)} problem(s) across {n} row(s)")
        for p in problems[:args.max_show]:
            print(f"  - {p}")
        if len(problems) > args.max_show:
            print(f"  ... and {len(problems) - args.max_show} more")
        return 1
    print(f"PASS: {n} row(s); every row sourced, every email labelled, "
          f"every phone typed")
    return 0


def _out(text: str, path) -> None:
    if path:
        open(path, "w").write(text + "\n")
        print(f"wrote {path}")
    else:
        print(text)


def main() -> int:
    ap = argparse.ArgumentParser(prog="leadkit", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("geo", help="resolve a place+radius to states and ZIP3s")
    g.add_argument("--place"); g.add_argument("--state")
    g.add_argument("--lat", type=float); g.add_argument("--lon", type=float)
    g.add_argument("--radius", type=float, default=50)
    g.add_argument("--json", action="store_true"); g.add_argument("-o", "--output")
    g.set_defaults(fn=cmd_geo)

    b = sub.add_parser("bands", help="distance-band a merged file, nearest first")
    b.add_argument("input")
    b.add_argument("--place"); b.add_argument("--state")
    b.add_argument("--lat", type=float); b.add_argument("--lon", type=float)
    b.add_argument("--radius", type=float, default=50)
    b.add_argument("-o", "--output", help="write back with dist_mi/dist_basis")
    b.set_defaults(fn=cmd_bands)

    pl = sub.add_parser("plan", help="emit NPI query URLs to fetch")
    pl.add_argument("--taxonomy", required=True, help="comma-separated; include the PARENT")
    pl.add_argument("--states", required=True)
    pl.add_argument("--outdir", default="raw")
    pl.set_defaults(fn=cmd_plan)

    ing = sub.add_parser("ingest", help="parse fetched NPI JSON; detect truncation")
    ing.add_argument("indir")
    ing.add_argument("-o", "--output", default="records/npi.json")
    ing.set_defaults(fn=cmd_ingest)

    e = sub.add_parser("emails", help="infer + apply an org email pattern")
    e.add_argument("--domain", required=True)
    e.add_argument("--known", action="append", default=[], help='"Name:email"')
    e.add_argument("--known-file")
    e.add_argument("--name", action="append", default=[])
    e.add_argument("--names-file")
    e.add_argument("--json", action="store_true")
    e.add_argument("-o", "--output")
    e.set_defaults(fn=cmd_emails)

    m = sub.add_parser("merge", help="dedupe + merge records across sources")
    m.add_argument("inputs", nargs="+")
    m.add_argument("-o", "--output")
    m.set_defaults(fn=cmd_merge)

    au = sub.add_parser("audit", help="refuse a list that cannot be audited")
    au.add_argument("input")
    au.add_argument("--max-show", type=int, default=12)
    au.set_defaults(fn=cmd_audit)

    c = sub.add_parser("csv", help="write merged records to CSV")
    c.add_argument("input")
    c.add_argument("-o", "--output", required=True)
    c.add_argument("--only-with-email", action="store_true")
    c.set_defaults(fn=cmd_csv)

    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
