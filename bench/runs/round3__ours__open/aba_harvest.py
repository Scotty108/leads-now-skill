#!/usr/bin/env python3
"""Harvest ABA diplomate certifications for the round3 clamped roster.
Plain HTTPS via urllib (no browser). Fills board_certification only for
people already geography-locked by NPI/hospital directory. ABA publishes a
MAILING address, so it is NEVER used to place a person or add a new person.
"""
import csv, json, re, sys, time, unicodedata, urllib.request, urllib.error, urllib.parse
from concurrent.futures import ThreadPoolExecutor

API = "https://directoryreactapi.theaba.org"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
HDR = {"User-Agent": UA, "Origin": "https://directoryreact.theaba.org",
       "Referer": "https://directoryreact.theaba.org/", "Accept": "application/json"}

def get(url, data=None):
    req = urllib.request.Request(url, headers=dict(HDR))
    if data is not None:
        req.add_header("Content-Type", "application/json")
        req.data = json.dumps(data).encode()
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8", "replace")), r.status
        except urllib.error.HTTPError as e:
            return None, e.code
        except Exception:
            time.sleep(1.5 * (attempt + 1))
    return None, -1

def norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z]", "", s.lower())

SUFF = {"md", "do", "mbbs", "mb", "bs", "dds", "dmd", "phd", "jr", "sr", "ii", "iii", "iv", "facs", "faap"}

def parse_aba_name(full):
    """'Michelle D. Lee, M.D.' -> (first, last)"""
    base = full.split(",")[0]
    toks = [t for t in re.split(r"\s+", base.replace(".", " ")) if t]
    toks = [t for t in toks if norm(t) not in SUFF and len(norm(t)) > 0]
    if len(toks) < 2:
        return None
    return norm(toks[0]), norm(toks[-1])

def roster_name(full):
    toks = [t for t in re.split(r"\s+", (full or "").replace(".", " ")) if t]
    toks = [t for t in toks if norm(t) not in SUFF and norm(t)]
    if len(toks) < 2:
        return None
    return norm(toks[0]), norm(toks[-1])

def main(csv_path, out_path):
    rows = list(csv.DictReader(open(csv_path)))
    people = []
    for r in rows:
        nm = roster_name(r["full_name"])
        if nm:
            people.append({"row": r, "first": nm[0], "last": nm[1]})

    def work(p):
        r = p["row"]
        surname = r["full_name"].split()[-1]
        res, code = get(f"{API}/searchResults/basic?FirstName=&LastName={urllib.parse.quote(surname)}")
        out = {"full_name": r["full_name"], "npi": r.get("npi", ""),
               "city": r.get("city", ""), "state": r.get("state", ""),
               "http": code, "n_candidates": len(res or []), "matches": [],
               "aba_id": "", "areas": [], "peds": False, "status": ""}
        if not res:
            out["status"] = "NO_RESULTS" if code == 200 else f"HTTP_{code}"
            return out
        for c in res:
            pn = parse_aba_name(c.get("FullName") or "")
            if not pn:
                continue
            # FULL FORENAME + surname lock. Initial-only never matches.
            if pn[0] == p["first"] and pn[1] == p["last"]:
                out["matches"].append({"FullName": c["FullName"], "ABAId": c["ABAId"],
                                       "City": c.get("City"), "State": c.get("State")})
        if not out["matches"]:
            out["status"] = "NO_FULL_FORENAME_MATCH"
            return out
        # Prefer a match whose ABA mailing state agrees with the practice state,
        # but record the ambiguity when several share the name.
        cands = out["matches"]
        same_state = [m for m in cands if (m.get("State") or "") == r.get("state", "")]
        if len(cands) > 1 and len(same_state) == 1:
            pick = same_state[0]
            out["status"] = "MATCHED_state_disambiguated"
        elif len(cands) == 1:
            pick = cands[0]
            out["status"] = "MATCHED_unique_national"
        elif same_state:
            pick = same_state[0]
            out["status"] = "AMBIGUOUS_multiple_same_state"
        else:
            out["status"] = "AMBIGUOUS_no_state_agreement"
            return out
        out["aba_id"] = pick["ABAId"]
        out["aba_city"] = pick.get("City")
        out["aba_state"] = pick.get("State")
        recs, code2 = get(f"{API}/doctorRecord/getDoctorRecords?ABAId={pick['ABAId'].replace('-','')}")
        out["rec_http"] = code2
        if recs:
            seen = []
            for x in recs:
                a = x.get("AreaOfCert")
                if a:
                    seen.append({"area": a, "status": x.get("BoardStatus"),
                                 "type": x.get("CertType"), "issued": (x.get("DateIssued") or "")[:10],
                                 "expires": (x.get("DateExpired") or "")[:10],
                                 "moca_peds": x.get("MOCAStatusPeds")})
            out["areas"] = seen
            out["peds"] = any("Pediatric Anesthesiology" in (s["area"] or "") for s in seen)
        return out

    results = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        for i, res in enumerate(ex.map(work, people)):
            results.append(res)
            if (i + 1) % 20 == 0:
                print(f"  {i+1}/{len(people)}", file=sys.stderr, flush=True)
    json.dump(results, open(out_path, "w"), indent=1)
    m = [r for r in results if r["aba_id"]]
    print(f"people={len(results)} aba_matched={len(m)} "
          f"with_areas={sum(1 for r in m if r['areas'])} peds={sum(1 for r in results if r['peds'])}")

if __name__ == "__main__":
    import urllib.parse
    main(sys.argv[1], sys.argv[2])
