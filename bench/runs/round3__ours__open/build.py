#!/usr/bin/env python3
"""Round 3 OPEN: merge ABA (plain fetch) + ABMS (browser-only) onto the
round3 clamped roster. No new people are added from either source: both
publish a MAILING / board-REPORTED address, which is not a practice location.
Geography stays locked to the NPI / hospital-directory practice address.
"""
import csv, json, re, sys, unicodedata

BASE = "/Users/scotty/leads.now/bench/runs"
CLAMPED = f"{BASE}/round3__ours__clamped/result.csv"
OUT = f"{BASE}/round3__ours__open"

ABA_SRC = ("https://directoryreactapi.theaba.org/searchResults/basic + "
           "/doctorRecord/getDoctorRecords (American Board of Anesthesiology "
           "diplomate directory; open JSON API, reached with plain urllib, NO browser)")
ABMS_SRC = ("https://www.certificationmatters.org/find-my-doctor/ "
            "(ABMS Certification Matters; 403 to curl/WebFetch, read via browser "
            "same-origin fetch; record scope = tr.result-body-row, page chrome stripped)")

SUFF = {"md","do","mbbs","mb","bs","dds","dmd","phd","jr","sr","ii","iii","iv","facs","faap"}

def norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z]", "", s.lower())

def fl(full):
    toks = [t for t in re.split(r"[\s]+", (full or "").replace(".", " ")) if t]
    toks = [t for t in toks if norm(t) not in SUFF and norm(t)]
    if len(toks) < 2:
        return None
    return norm(toks[0]), norm(toks[-1])

def load_eval(path):
    raw = open(path).read().strip()
    d = json.loads(raw)
    if isinstance(d, str):
        d = json.loads(d)
    return d

# ---------- ABMS row parsing ----------
# Row shape: "<Full Name> <City>, <ST> <cert list> View Profile".
# The name/city boundary is not delimited, so anchor it on the roster surname.
ROW = re.compile(r"^(?P<pre>.+?),\s*(?P<st>[A-Z]{2})\s+(?P<certs>.+?)\s*View Profile\s*$")

def parse_abms(rowtext, surname):
    m = ROW.match(rowtext)
    if not m:
        return None
    toks = [t for t in m.group("pre").split() if t]
    idxs = [i for i, t in enumerate(toks) if norm(t) == surname]
    idxs = [i for i in idxs if i < len(toks) - 1] or idxs   # need a city after it
    if not idxs:
        return None
    i = idxs[-1]
    name, city = " ".join(toks[:i + 1]), " ".join(toks[i + 1:])
    certs = []
    for part in re.split(r"(?<=Specialty)\s+|(?<=Subspecialty)\s+", m.group("certs")):
        part = part.strip()
        if not part:
            continue
        mm = re.match(r"^(.*?)\s*[–-]\s*(Subspecialty|Specialty)$", part)
        if mm:
            certs.append({"area": mm.group(1).strip(), "kind": mm.group(2)})
    return {"name": name, "city": city, "state": m.group("st"),
            "certs": certs, "raw": rowtext}

def main():
    rows = list(csv.DictReader(open(CLAMPED)))
    aba = {r["full_name"]: r for r in json.load(open(f"{OUT}/aba_records.json"))}
    abms = {}
    for c in (1, 2, 3):
        for x in load_eval(f"{OUT}/abms_chunk{c}.json"):
            # silent truncation: a common-surname query returns non-zero rows
            # whose text is EMPTY. Do not read that as absence.
            x["rows"] = [t for t in (x.get("rows") or []) if len(t) > 5]
            x["truncated"] = bool(x.get("k")) and not x["rows"]
            abms[x["n"]] = x
    for x in load_eval(f"{OUT}/abms_retry.json"):   # state-scoped retry wins
        if x.get("rows"):
            abms[x["n"]] = x

    newcols = ["aba_id", "aba_certifications", "aba_source", "aba_match_status",
               "abms_certifications", "abms_reported_location", "abms_source",
               "abms_match_status", "peds_subspecialty_confirmed",
               "certifying_body_corroboration", "round3_open_delta"]
    fields = list(rows[0].keys()) + [c for c in newcols if c not in rows[0]]

    stats = dict(aba_matched=0, abms_matched=0, peds=0, filled=0, both=0,
                 abms_ambiguous=0, abms_none=0, newly_filled_training=0)
    peds_people = []

    for r in rows:
        name = r["full_name"]
        key = fl(name)
        pr_city = (r.get("city") or "").strip().lower()
        pr_state = (r.get("state") or "").strip().upper()

        # ---- ABA ----
        a = aba.get(name, {})
        aba_peds = False
        r["aba_id"] = a.get("aba_id", "")
        r["aba_match_status"] = a.get("status", "NOT_QUERIED")
        if a.get("areas"):
            stats["aba_matched"] += 1
            parts = []
            for x in a["areas"]:
                parts.append(f"{x['area']} ({x['status']}, {x['type']}, {x['issued']}–{x['expires']})")
            r["aba_certifications"] = "; ".join(parts)
            r["aba_source"] = ABA_SRC
            aba_peds = bool(a.get("peds"))
        else:
            r["aba_certifications"] = ""
            r["aba_source"] = ""

        # ---- ABMS ---- full forename + surname lock, then disambiguate
        b = abms.get(name, {})
        cands = [parse_abms(t, key[1] if key else "") for t in (b.get("rows") or [])]
        cands = [c for c in cands if c]
        exact = [c for c in cands if key and fl(c["name"]) == key]
        abms_peds = False
        pick = None
        if not cands:
            r["abms_match_status"] = "NO_RESULTS"
            stats["abms_none"] += 1
        elif not exact:
            r["abms_match_status"] = "NO_FULL_FORENAME_MATCH (%d name-similar rows rejected)" % len(cands)
            stats["abms_none"] += 1
        elif len(exact) == 1:
            pick = exact[0]
            r["abms_match_status"] = "MATCHED_unique_full_forename"
        else:
            # several exact-name people nationally: require the reported location
            # to agree with the practice city/state, or the ABA mailing city.
            agree = [c for c in exact
                     if c["state"] == pr_state and c["city"].lower() == pr_city]
            if not agree and a.get("aba_city"):
                agree = [c for c in exact if c["city"].lower() == (a.get("aba_city") or "").lower()
                         and c["state"] == (a.get("aba_state") or "")]
            if len(agree) == 1:
                pick = agree[0]
                r["abms_match_status"] = "MATCHED_location_disambiguated (%d homonyms)" % len(exact)
            else:
                r["abms_match_status"] = "AMBIGUOUS_%d_exact_name_matches_withheld" % len(exact)
                stats["abms_ambiguous"] += 1

        if pick:
            stats["abms_matched"] += 1
            r["abms_certifications"] = "; ".join(f"{c['area']} – {c['kind']}" for c in pick["certs"])
            r["abms_reported_location"] = f"{pick['city']}, {pick['state']} (board-REPORTED address, not a verified practice location)"
            r["abms_source"] = ABMS_SRC
            abms_peds = any("Pediatric Anesthesiology" in c["area"] for c in pick["certs"])
        else:
            r["abms_certifications"] = ""
            r["abms_reported_location"] = ""
            r["abms_source"] = ""

        # ---- corroboration + peds ----
        if r["aba_certifications"] and r["abms_certifications"]:
            r["certifying_body_corroboration"] = "ABA + ABMS agree" if (aba_peds == abms_peds) else "ABA/ABMS DISAGREE on pediatric subcert"
            stats["both"] += 1
        elif r["aba_certifications"]:
            r["certifying_body_corroboration"] = "ABA only"
        elif r["abms_certifications"]:
            r["certifying_body_corroboration"] = "ABMS only"
        else:
            r["certifying_body_corroboration"] = "neither body returned a locked match"

        if aba_peds or abms_peds:
            r["peds_subspecialty_confirmed"] = "YES"
            r["peds_signal"] = "STRONG"
            ev = []
            if aba_peds:
                ev.append("ABA: Pediatric Anesthesiology certificate on record")
            if abms_peds:
                ev.append("ABMS: 'Pediatric Anesthesiology – Subspecialty'")
            r["peds_evidence"] = (" | ".join(ev) +
                " | geography from NPI/hospital practice address, NOT from the board's mailing address")
            stats["peds"] += 1
            peds_people.append((name, r.get("city"), r.get("state"), r.get("phone"),
                                aba_peds, abms_peds, r.get("abms_reported_location")))
        else:
            r["peds_subspecialty_confirmed"] = "NO" if (r["aba_certifications"] or r["abms_certifications"]) else "UNCHECKED"

        # training block: previously NONE_FOUND / unpublishable -> now checked at the body
        prev = (r.get("board_certification") or "").strip()
        if (r["aba_certifications"] or r["abms_certifications"]):
            stats["filled"] += 1
            if not prev or prev in ("NONE_FOUND", ""):
                stats["newly_filled_training"] += 1
            if not prev:
                r["board_certification"] = r["aba_certifications"] or r["abms_certifications"]
                r["board_certification_source"] = r["aba_source"] or r["abms_source"]

        deltas = []
        if r["aba_certifications"]:
            deltas.append("ABA cert block filled (plain fetch)")
        if r["abms_certifications"]:
            deltas.append("ABMS cert block filled (BROWSER-ONLY source)")
        if aba_peds or abms_peds:
            deltas.append("PEDIATRIC ANESTHESIOLOGY CONFIRMED")
        r["round3_open_delta"] = "; ".join(deltas) or "no change"

    with open(f"{OUT}/result.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})

    print(json.dumps(stats, indent=1))
    print("\nPEDIATRIC ANESTHESIOLOGISTS (geography from NPI practice address):")
    for p in peds_people:
        print(" ", p)
    return stats

if __name__ == "__main__":
    main()
