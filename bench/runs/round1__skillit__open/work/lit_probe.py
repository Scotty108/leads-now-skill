#!/usr/bin/env python3
"""Affiliation-locked literature probe: PubMed E-utilities + Europe PMC.
Emits per-person hits with author-level affiliation + any published email.
Stdlib only. Rate-limited."""
import json, re, sys, time, threading, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
from xml.etree import ElementTree as ET

ROSTER = json.load(open(sys.argv[1]))
OUT = sys.argv[2]
UA = "leads-bench/1.0 (mailto:scotty.pittsford@cascadian.ai)"

RING_CITIES = ["myrtle beach", "conway", "georgetown", "murrells inlet", "pawleys island",
               "loris", "mullins", "little river", "north myrtle beach", "surfside",
               "shallotte", "bolivia", "whiteville", "sunset beach", "supply", "socastee"]
RING_SYSTEMS = ["grand strand", "tidelands", "conway medical", "mcleod", "brunswick",
                "novant", "waccamaw", "seacoast", "coastal carolina", "carolina forest",
                "columbus regional", "marion county", "grand strand medical"]
LEGAL = {"llc", "pc", "pa", "inc", "plc", "pllc", "p.a.", "the", "and", "of", "llp", "md"}
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")

_lock = threading.Lock()
_last = [0.0]
def throttle(gap):
    with _lock:
        d = time.time() - _last[0]
        if d < gap:
            time.sleep(gap - d)
        _last[0] = time.time()

def get(url, data=None, gap=0.40, tries=3):
    for t in range(tries):
        throttle(gap)
        try:
            req = urllib.request.Request(url, data=data, headers={"User-Agent": UA})
            return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
        except Exception as e:
            if t == tries - 1:
                return "ERR:%s" % e
            time.sleep(1.2 * (t + 1))

def org_tokens(org):
    return [w for w in re.split(r"[^a-z]+", (org or "").lower())
            if len(w) > 4 and w not in LEGAL]

def classify(aff, p):
    """Return (lock_level, matched_token) for an author affiliation string."""
    a = (aff or "").lower()
    if not a:
        return ("none", "")
    city = p["city"].lower()
    if city and city in a:
        return ("strong", p["city"])
    for t in org_tokens(p["org"]):
        if t in a:
            return ("strong", t)
    for c in RING_CITIES:
        if c in a:
            return ("regional", c)
    for s in RING_SYSTEMS:
        if s in a:
            return ("regional", s)
    if "south carolina" in a or ", sc" in a or "north carolina" in a:
        return ("state_only", "state")
    return ("none", "")

def pubmed(p):
    """esearch on author, verify author-level affiliation via efetch."""
    term = '%s %s[Author]' % (p["last"], p["first"][0])
    q = urllib.parse.urlencode({"db": "pubmed", "term": term, "retmax": "60",
                                "retmode": "json", "tool": "leads-bench",
                                "email": "scotty.pittsford@cascadian.ai"})
    r = get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?" + q)
    if r.startswith("ERR:"):
        return {"error": r, "ids": 0, "hits": []}
    try:
        ids = json.loads(r)["esearchresult"]["idlist"]
    except Exception:
        return {"error": "parse", "ids": 0, "hits": []}
    if not ids:
        return {"ids": 0, "hits": []}
    q2 = urllib.parse.urlencode({"db": "pubmed", "id": ",".join(ids[:60]),
                                 "retmode": "xml", "tool": "leads-bench",
                                 "email": "scotty.pittsford@cascadian.ai"})
    x = get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?" + q2, gap=0.45)
    if x.startswith("ERR:"):
        return {"error": x, "ids": len(ids), "hits": []}
    hits = []
    try:
        root = ET.fromstring(x)
    except Exception:
        return {"error": "xmlparse", "ids": len(ids), "hits": []}
    for art in root.iter("PubmedArticle"):
        pmid = (art.findtext(".//PMID") or "").strip()
        year = (art.findtext(".//PubDate/Year") or art.findtext(".//PubDate/MedlineDate") or "")[:4]
        title = (art.findtext(".//ArticleTitle") or "")[:120]
        for au in art.iter("Author"):
            ln = (au.findtext("LastName") or "").lower()
            fn = (au.findtext("ForeName") or au.findtext("Initials") or "")
            if ln != p["last"].lower():
                continue
            if fn and fn[0].upper() != p["first"][0].upper():
                continue
            affs = [(a.findtext("Affiliation") or "") for a in au.iter("AffiliationInfo")]
            for aff in affs:
                lvl, tok = classify(aff, p)
                em = EMAIL_RE.findall(aff)
                if lvl in ("strong", "regional") or em:
                    hits.append({"pmid": pmid, "year": year, "title": title,
                                 "author": fn + " " + (au.findtext("LastName") or ""),
                                 "aff": aff[:400], "lock": lvl, "tok": tok, "emails": em})
    return {"ids": len(ids), "hits": hits}

def epmc(p):
    """Europe PMC: author query, then inspect core affiliations for lock + email."""
    query = 'AUTH:"%s %s"' % (p["last"], p["first"])
    q = urllib.parse.urlencode({"query": query, "format": "json", "pageSize": "100",
                                "resultType": "core"})
    r = get("https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + q, gap=0.15)
    if r.startswith("ERR:"):
        return {"error": r, "n": 0, "hits": []}
    try:
        d = json.loads(r)
    except Exception:
        return {"error": "parse", "n": 0, "hits": []}
    res = d.get("resultList", {}).get("result", [])
    hits = []
    for w in res:
        for au in (w.get("authorList", {}) or {}).get("author", []) or []:
            ln = (au.get("lastName") or "").lower()
            fn = (au.get("firstName") or au.get("initials") or "")
            if ln != p["last"].lower():
                continue
            if fn and fn[0].upper() != p["first"][0].upper():
                continue
            affs = []
            if au.get("affiliation"):
                affs.append(au["affiliation"])
            for a in (au.get("authorAffiliationDetailsList", {}) or {}).get("authorAffiliation", []) or []:
                if a.get("affiliation"):
                    affs.append(a["affiliation"])
            for aff in affs:
                lvl, tok = classify(aff, p)
                em = EMAIL_RE.findall(aff)
                if lvl in ("strong", "regional") or em:
                    hits.append({"id": w.get("id"), "src": w.get("source"),
                                 "pmid": w.get("pmid"), "doi": w.get("doi"),
                                 "year": w.get("pubYear"), "title": (w.get("title") or "")[:120],
                                 "aff": aff[:400], "lock": lvl, "tok": tok, "emails": em})
    return {"n": len(res), "hits": hits}

def work(p):
    out = {"full_name": p["full_name"], "npi": p["npi"], "org": p["org"], "city": p["city"]}
    out["pubmed"] = pubmed(p)
    out["epmc"] = epmc(p)
    return out

with ThreadPoolExecutor(max_workers=4) as ex:
    res = list(ex.map(work, ROSTER))
json.dump(res, open(OUT, "w"), indent=1)

npm = sum(r["pubmed"].get("ids", 0) for r in res)
pmh = sum(len(r["pubmed"]["hits"]) for r in res)
eph = sum(len(r["epmc"]["hits"]) for r in res)
pe = sum(len([e for h in r["pubmed"]["hits"] for e in h["emails"]]) for r in res)
ee = sum(len([e for h in r["epmc"]["hits"] for e in h["emails"]]) for r in res)
errs = [r["full_name"] for r in res if r["pubmed"].get("error") or r["epmc"].get("error")]
print("people=%d pubmed_raw_ids=%d pubmed_locked_hits=%d epmc_locked_hits=%d pubmed_emails=%d epmc_emails=%d errors=%d"
      % (len(res), npm, pmh, eph, pe, ee, len(errs)))
if errs:
    print("errored:", errs[:10])
