#!/usr/bin/env python3
"""ClinicalTrials.gov v2 + NIH RePORTER probes, affiliation/geo locked. Stdlib only."""
import json, re, sys, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

ROSTER = json.load(open(sys.argv[1]))
OUT = sys.argv[2]
UA = "leads-bench/1.0 (mailto:scotty.pittsford@cascadian.ai)"
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
RING = ["myrtle beach", "conway", "georgetown", "murrells inlet", "pawleys island", "loris",
        "mullins", "little river", "north myrtle beach", "shallotte", "bolivia", "whiteville",
        "sunset beach", "surfside beach", "supply"]

def get(url, data=None, hdrs=None):
    h = {"User-Agent": UA}
    if hdrs:
        h.update(hdrs)
    try:
        req = urllib.request.Request(url, data=data, headers=h)
        return urllib.request.urlopen(req, timeout=45).read().decode("utf-8", "replace")
    except Exception as e:
        return "ERR:%s" % e

# ---------- 1. ClinicalTrials.gov by person name (all fields) ----------
def ct_person(p):
    term = '"%s %s"' % (p["first"], p["last"])
    q = urllib.parse.urlencode({"query.term": term, "pageSize": "20",
                                "fields": "NCTId,BriefTitle,LocationCity,LocationState,LocationFacility,"
                                          "CentralContactName,CentralContactEMail,CentralContactPhone,"
                                          "LocationContactName,LocationContactEMail,LocationContactPhone,"
                                          "OverallOfficialName,OverallOfficialAffiliation,LeadSponsorName"})
    r = get("https://clinicaltrials.gov/api/v2/studies?" + q)
    if r.startswith("ERR:"):
        return {"error": r, "n": 0, "hits": []}
    try:
        d = json.loads(r)
    except Exception:
        return {"error": "parse", "n": 0, "hits": []}
    studies = d.get("studies", [])
    hits = []
    nm = ("%s %s" % (p["first"], p["last"])).lower()
    last = p["last"].lower()
    for s in studies:
        blob = json.dumps(s).lower()
        if last not in blob:
            continue
        geo = [c for c in RING if c in blob]
        emails = EMAIL_RE.findall(json.dumps(s))
        if geo or nm in blob:
            hits.append({"nct": s.get("protocolSection", {}).get("identificationModule", {}).get("nctId")
                         or json.dumps(s)[:0] or "", "geo": geo, "emails": emails,
                         "raw": json.dumps(s)[:1200]})
    return {"n": len(studies), "hits": hits}

# ---------- 2. ClinicalTrials.gov by ring location ----------
def ct_geo():
    out = {}
    for city in ["Myrtle Beach, South Carolina", "Conway, South Carolina",
                 "Georgetown, South Carolina", "Murrells Inlet, South Carolina",
                 "Shallotte, North Carolina", "Whiteville, North Carolina",
                 "Bolivia, North Carolina", "Loris, South Carolina"]:
        q = urllib.parse.urlencode({"query.locn": city, "pageSize": "100",
                                    "fields": "NCTId,BriefTitle,ContactsLocationsModule,OverallOfficialName"})
        r = get("https://clinicaltrials.gov/api/v2/studies?" + q)
        if r.startswith("ERR:"):
            out[city] = {"error": r}
            continue
        try:
            d = json.loads(r)
        except Exception:
            out[city] = {"error": "parse"}
            continue
        st = d.get("studies", [])
        people = []
        for s in st:
            blob = json.dumps(s)
            if not any(c.split(",")[0].lower() in blob.lower() for c in [city]):
                continue
            for m in re.finditer(r'"name"\s*:\s*"([^"]+(?:MD|M\.D\.|DO|PhD|CRNA)[^"]*)"', blob):
                people.append(m.group(1))
            people += EMAIL_RE.findall(blob)
        out[city] = {"studies": len(st), "contacts": sorted(set(people))[:40]}
        time.sleep(0.2)
    return out

# ---------- 3. NIH RePORTER by PI name ----------
def reporter_batch(names):
    body = json.dumps({"criteria": {"pi_names": [{"first_name": f, "last_name": l} for f, l in names]},
                       "include_fields": ["ProjectNum", "ContactPiName", "Organization",
                                          "PrincipalInvestigators", "ProjectTitle", "FiscalYear"],
                       "limit": 500, "offset": 0}).encode()
    r = get("https://api.reporter.nih.gov/v2/projects/search", data=body,
            hdrs={"Content-Type": "application/json"})
    if r.startswith("ERR:"):
        return {"error": r}
    try:
        d = json.loads(r)
    except Exception:
        return {"error": "parse", "raw": r[:300]}
    return {"total": d.get("meta", {}).get("total"),
            "results": [{"pi": x.get("contact_pi_name"),
                         "org": (x.get("organization") or {}).get("org_name"),
                         "state": (x.get("organization") or {}).get("org_state"),
                         "city": (x.get("organization") or {}).get("org_city"),
                         "proj": x.get("project_num"), "fy": x.get("fiscal_year"),
                         "title": (x.get("project_title") or "")[:90]}
                        for x in d.get("results", [])]}

# ---------- 4. NIH RePORTER by organization state (does any ring org hold a grant?) ----------
def reporter_geo():
    body = json.dumps({"criteria": {"org_cities": ["MYRTLE BEACH", "CONWAY", "GEORGETOWN",
                                                   "MURRELLS INLET", "LORIS", "SHALLOTTE",
                                                   "WHITEVILLE", "BOLIVIA"]},
                       "include_fields": ["ContactPiName", "Organization", "ProjectNum", "FiscalYear"],
                       "limit": 100}).encode()
    r = get("https://api.reporter.nih.gov/v2/projects/search", data=body,
            hdrs={"Content-Type": "application/json"})
    if r.startswith("ERR:"):
        return {"error": r}
    try:
        d = json.loads(r)
    except Exception:
        return {"error": "parse", "raw": r[:300]}
    return {"total": d.get("meta", {}).get("total"),
            "results": [{"pi": x.get("contact_pi_name"),
                         "org": (x.get("organization") or {}).get("org_name"),
                         "city": (x.get("organization") or {}).get("org_city")}
                        for x in d.get("results", [])][:50]}

res = {}
with ThreadPoolExecutor(max_workers=5) as ex:
    ct = list(ex.map(ct_person, ROSTER))
res["ct_person"] = {p["full_name"]: c for p, c in zip(ROSTER, ct)}
res["ct_geo"] = ct_geo()
names = [(p["first"], p["last"]) for p in ROSTER]
res["reporter_names"] = reporter_batch(names)
res["reporter_geo"] = reporter_geo()
json.dump(res, open(OUT, "w"), indent=1)

cth = sum(len(v.get("hits", [])) for v in res["ct_person"].values())
cte = sum(len(h["emails"]) for v in res["ct_person"].values() for h in v.get("hits", []))
print("ct_person_studies_scanned=%d ct_person_locked_hits=%d ct_emails=%d"
      % (sum(v.get("n", 0) for v in res["ct_person"].values()), cth, cte))
print("ct_geo:", {k: (v.get("studies"), len(v.get("contacts", []))) for k, v in res["ct_geo"].items()})
print("reporter_names total=%s returned=%d" % (res["reporter_names"].get("total"),
                                               len(res["reporter_names"].get("results", []))))
print("reporter_geo total=%s" % res["reporter_geo"].get("total"))
