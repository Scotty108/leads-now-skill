#!/usr/bin/env python3
"""Resolve a US place to coordinates, and filter a contact CSV to a radius.

Offline. Standard library only. Never touches the network.
Reads assets/us_geo.csv.gz (Census 2024 Gazetteer: ZCTA + incorporated place centroids).

  resolve "Myrtle Beach, SC" --radius 50
      -> center coordinates + every state and ZIP3 prefix inside the ring

  filter roster.csv --center 33.7104,-78.8860 --radius 50 --zip-col postal_code -o near.csv
      -> adds distance_mi, keeps rows inside the ring, reports what it could not place
"""
import argparse, csv, gzip, math, os, sys, unicodedata

ASSET = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "us_geo.csv.gz")


def die(msg):
    sys.stderr.write("ERROR: %s\n" % msg)
    raise SystemExit(2)


# Directory city names are typed by humans, not copied from the Census. The
# gazetteer says "Mount Pleasant" and "North Charleston"; a form says "MT
# PLEASANT" and "N CHARLESTON". Without expansion the CENTER fails to resolve
# and the whole run stops on its first step.
ABBREV = {"mt": "mount", "st": "saint", "ft": "fort", "n": "north",
          "s": "south", "e": "east", "w": "west", "nw": "northwest",
          "ne": "northeast", "sw": "southwest", "se": "southeast"}


def norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    toks = s.lower().replace(".", " ").replace("-", " ").split()
    return " ".join(ABBREV.get(t, t) for t in toks)


def load():
    """Returns (zips: {zip5:(lat,lon)}, places: {(name,state):(lat,lon)})."""
    path = os.path.normpath(ASSET)
    if not os.path.exists(path):
        die("missing gazetteer asset at %s" % path)
    zips, places = {}, {}
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("|")
            if len(p) != 5:
                continue
            kind, a, b, lat, lon = p
            try:
                pt = (float(lat), float(lon))
            except ValueError:
                continue
            if kind == "Z":
                zips[a] = pt
            else:
                places[(norm(a), b.upper())] = pt
    return zips, places


def haversine(a, b):
    lat1, lon1, lat2, lon2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 7917.51 * math.asin(min(1.0, math.sqrt(h)))  # mean earth diameter in miles


def zip5(v):
    d = "".join(c for c in str(v or "") if c.isdigit())
    return d[:5] if len(d) >= 5 else None


def parse_center(text, zips, places):
    """Accepts 'lat,lon', a 5-digit ZIP, or 'City, ST'."""
    t = (text or "").strip()
    if "," in t:
        a, b = t.split(",", 1)
        try:
            return (float(a), float(b)), "coordinates %s" % t
        except ValueError:
            pass
    z = zip5(t)
    if z and len(t.strip()) <= 10 and t.strip().replace("-", "").isdigit():
        if z in zips:
            return zips[z], "ZIP %s" % z
        die("ZIP %s is not a Census ZCTA. Pass coordinates as 'lat,lon' instead." % z)
    if "," in t:
        city, st = [x.strip() for x in t.rsplit(",", 1)]
        key = (norm(city), st.upper())
        if key in places:
            return places[key], "%s, %s" % (city, st.upper())
        # Consolidated city-county governments: the Census carries
        # "Lexington-Fayette urban county" where a user types "Lexington".
        # Require a word boundary so "Charleston" cannot absorb into
        # "Charleston Heights" — that would silently move the centre.
        pref = [(n, s) for (n, s) in places
                if s == st.upper() and n.startswith(norm(city) + " ") and len(norm(city)) > 4]
        if len(pref) == 1:
            return places[pref[0]], "%s, %s" % (pref[0][0], st.upper())
        near = sorted({s for (n, s) in places if n == norm(city)})
        if near:
            die("'%s' not found in %s. It exists in: %s" % (city, st.upper(), ", ".join(near)))
        die("place '%s' not found. Pass a ZIP or 'lat,lon'." % t)
    hits = sorted({s for (n, s) in places if n == norm(t)})
    if len(hits) == 1:
        return places[(norm(t), hits[0])], "%s, %s" % (t, hits[0])
    if len(hits) > 1:
        die("'%s' is ambiguous across %d states (%s). Qualify it as 'City, ST'." % (t, len(hits), ", ".join(hits)))
    die("could not resolve '%s'. Pass 'City, ST', a 5-digit ZIP, or 'lat,lon'." % t)


def cmd_resolve(args):
    zips, places = load()
    center, how = parse_center(args.place, zips, places)
    r = args.radius
    states, prefixes = {}, set()
    for (n, st), pt in places.items():
        d = haversine(center, pt)
        if d <= r:
            states[st] = min(states.get(st, 9e9), d)
    for z, pt in zips.items():
        if haversine(center, pt) <= r:
            prefixes.add(z[:3])
    print("center: %.4f,%.4f  (from %s)" % (center[0], center[1], how))
    print("radius_mi: %g" % r)
    print("states_in_radius: %s" % ",".join(sorted(states, key=lambda s: states[s])))
    print("zip3_prefixes_in_radius: %s" % ",".join(sorted(prefixes)))
    if len(states) > 1:
        sys.stderr.write(
            "NOTE: the ring crosses %d states. Query every state listed above, "
            "not just the one the user named.\n" % len(states))
    return 0


def cmd_filter(args):
    if not os.path.exists(args.infile):
        die("no such file: %s" % args.infile)
    zips, places = load()
    center, how = parse_center(args.center, zips, places)
    try:
        with open(args.infile, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
    except (csv.Error, UnicodeDecodeError) as e:
        die("%s is not readable as CSV (%s). Fix or re-export the file; do not work around it."
            % (args.infile, e))
    if not rows:
        die("%s has no data rows" % args.infile)
    cols = list(rows[0].keys())
    for c in (args.zip_col, "distance_mi"):
        if c == "distance_mi" and c not in cols:
            cols.append(c)
    if args.zip_col not in rows[0]:
        die("column '%s' not in %s (has: %s)" % (args.zip_col, args.infile, ", ".join(rows[0])))
    kept, unplaced, outside = [], [], 0
    for row in rows:
        z = zip5(row.get(args.zip_col))
        pt = zips.get(z) if z else None
        if not pt:
            row["distance_mi"] = ""
            unplaced.append(row)
            continue
        d = haversine(center, pt)
        row["distance_mi"] = "%.1f" % d
        if d <= args.radius:
            kept.append(row)
        else:
            outside += 1
    kept.sort(key=lambda r: float(r["distance_mi"]))
    collapsed = 0
    if args.dedupe_by:
        if args.dedupe_by not in rows[0]:
            die("cannot dedupe on '%s' — not a column in %s" % (args.dedupe_by, args.infile))
        best, out = set(), []
        for r in kept:                       # already nearest-first
            k = (r.get(args.dedupe_by) or "").strip()
            if k and k in best:
                collapsed += 1
                continue
            if k:
                best.add(k)
            out.append(r)
        kept = out
    if args.keep_unplaced:
        kept.extend(unplaced)
    with open(args.outfile, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(kept)
    print("center %.4f,%.4f from %s; radius %g mi" % (center[0], center[1], how, args.radius))
    print("in:  %d rows" % len(rows))
    print("kept: %d   outside: %d   unplaceable_zip: %d" % (len(kept), outside, len(unplaced)))
    if args.dedupe_by:
        print("collapsed %d extra practice location(s) — each %s kept at its nearest site"
              % (collapsed, args.dedupe_by))
    print("wrote %s" % args.outfile)
    if unplaced and not args.keep_unplaced:
        sys.stderr.write("NOTE: %d rows had no usable ZIP and were DROPPED. Report them as "
                         "coverage loss, or rerun with --keep-unplaced.\n" % len(unplaced))
    return 0


BANDS = [15, 25, 50, 100]


def cmd_bands(args):
    """Band by distance instead of cutting at one radius.

    `filter` answers the radius the user typed. That radius is a guess made
    before seeing the data and is routinely not the one they meant — a sweep ran
    at 50 miles against a territory that was actually 15. Those are not
    different searches: 15 is a subset. Banding answers every radius off one
    sweep, and surfaces the near-miss at 51 miles that a hard cutoff hides in a
    way that looks exactly like nobody being there.
    """
    if not os.path.exists(args.infile):
        die("no such file: %s" % args.infile)
    zips, places = load()
    center, how = parse_center(args.center, zips, places)
    try:
        with open(args.infile, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
    except (csv.Error, UnicodeDecodeError) as e:
        die("%s is not readable as CSV (%s)." % (args.infile, e))
    if not rows:
        die("%s has no data rows" % args.infile)
    if args.zip_col not in rows[0]:
        die("column '%s' not in %s (has: %s)"
            % (args.zip_col, args.infile, ", ".join(rows[0])))

    cols = list(rows[0].keys())
    if "distance_mi" not in cols:
        cols.append("distance_mi")
    placed, unplaced = [], 0
    for row in rows:
        z = zip5(row.get(args.zip_col))
        pt = zips.get(z) if z else None
        if not pt:
            # Never default an unplaceable row to 0 — it would sort to the top
            # and read as the closest lead in the territory.
            row["distance_mi"] = ""
            unplaced += 1
            continue
        row["distance_mi"] = "%.1f" % haversine(center, pt)
        placed.append(row)
    placed.sort(key=lambda r: float(r["distance_mi"]))

    if args.outfile:
        with open(args.outfile, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            w.writerows(placed + [r for r in rows if r.get("distance_mi") == ""])
        print("wrote %s" % args.outfile)

    print("center %.4f,%.4f from %s" % (center[0], center[1], how))
    print("%d rows" % len(rows))
    prev = cum = 0
    for b in BANDS:
        n = sum(1 for r in placed if float(r["distance_mi"]) <= b)
        if n == cum and b != BANDS[0]:
            continue
        print("  within %3d mi   %4d   (+%d over %g mi)" % (b, n, n - cum, prev))
        prev, cum = b, n
    edge = [r for r in placed
            if args.radius < float(r["distance_mi"]) <= args.radius * 1.2]
    if edge:
        print("  just outside %g mi: %d" % (args.radius, len(edge)))
        for r in edge[:5]:
            nm = r.get("full_name") or r.get("name") or "?"
            print("      %s  %s mi" % (nm, r["distance_mi"]))
    if unplaced:
        print("  %d row(s) UNPLACED — in no band, including yours" % unplaced)
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("resolve", help="place -> coordinates, states and ZIP3s in the ring")
    r.add_argument("place")
    r.add_argument("--radius", type=float, default=50)
    r.set_defaults(fn=cmd_resolve)
    fl = sub.add_parser("filter", help="annotate a CSV with distance and keep the ring")
    fl.add_argument("infile")
    fl.add_argument("--center", required=True, help="'lat,lon' | ZIP | 'City, ST'")
    fl.add_argument("--radius", type=float, required=True)
    fl.add_argument("--zip-col", default="postal_code")
    fl.add_argument("--keep-unplaced", action="store_true")
    fl.add_argument("--dedupe-by", help="column identifying one person, e.g. npi; keeps the nearest location")
    fl.add_argument("-o", "--outfile", required=True)
    fl.set_defaults(fn=cmd_filter)
    bd = sub.add_parser("bands", help="band by distance instead of cutting at one radius")
    bd.add_argument("infile")
    bd.add_argument("--center", required=True, help="'lat,lon' | ZIP | 'City, ST'")
    bd.add_argument("--radius", type=float, default=50, help="the ring to flag near-misses around")
    bd.add_argument("--zip-col", default="postal_code")
    bd.add_argument("-o", "--outfile")
    bd.set_defaults(fn=cmd_bands)
    a = ap.parse_args()
    raise SystemExit(a.fn(a))


if __name__ == "__main__":
    main()
