#!/usr/bin/env python3
"""Merge round-1 roster with round-2 open-channel enrichment into result.csv."""
import csv, json, urllib.parse

SRC = "/Users/scotty/leads.now/bench/runs/round1__skillit__clamped/result.csv"
OUT = "/Users/scotty/leads.now/bench/runs/round1__skillit__open/result.csv"

rows = list(csv.DictReader(open(SRC, encoding="utf-8-sig")))
cols = list(rows[0].keys())
NEW = ["phone_type", "linkedin_url", "linkedin_search_url", "pub_affiliation_lock",
       "pub_source_url", "pub_years", "affiliation_history", "channels_tried", "channel_notes"]

TRIED = ("openalex(HTTP429 budget-exhausted); pubmed_eutils(author+affiliation-locked); "
         "europepmc(AUTH core); pmc_fulltext(efetch db=pmc); clinicaltrials_v2(name+geo); "
         "nih_reporter_v2(pi_names+org_cities); org_dept_pages")

# affiliation-locked publication findings, keyed by full_name
LOCK = {
    "Jon D Halling": {
        "lock": "strong (Grand Strand Medical Center, Myrtle Beach, SC == practice city)",
        "url": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11249181/",
        "years": "2024",
        "hist": "Grand Strand Medical Center, Myrtle Beach SC (2024)",
        "email": "Jon.Halling@hcahealthcare.com",
        "status": "first_party_published",
        "risk": "published by the author on the paper (PMC11249181, 2024); no bounce estimate applies",
        "note": "Email printed as corresponding-author address in PMC full text; abstract-only sources do not carry it.",
    },
    "David Redding Kingery": {
        "lock": "strong (Grand Strand Regional Medical Center, Myrtle Beach, SC == practice city)",
        "url": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10324711/",
        "years": "2022, 2023",
        "hist": "Grand Strand Regional Medical Center, Myrtle Beach SC (2022-2023)",
        "email": "David.Kingery@hcahealthcare.com",
        "status": "first_party_published",
        "risk": "published by the author on the paper (PMC10324711, 2023); no bounce estimate applies",
        "note": "Email printed as corresponding-author address in PMC full text.",
    },
    "Derek L Horstemeyer": {
        "lock": "strong (Grand Strand Regional Medical Center, Myrtle Beach, SC == practice city)",
        "url": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10327958/",
        "years": "2022, 2022, 2023",
        "hist": "Grand Strand Regional Medical Center, Myrtle Beach SC (2022-2023)",
        "email": "derek.horstemeyer@hcahealthcare.com",
        "status": "pattern_confirmed",
        "risk": ("derived by scripts/email_pattern.py from 3 observed first.last addresses at "
                 "hcahealthcare.com; ~91% accurate, ~9% implied bounce - NOT bulk-sendable; "
                 "domain is the HCA facility he publishes from, his NPI employer is a private group"),
        "note": ("No address of his own was published; the 3 papers he co-authors carry another "
                 "author's corresponding address. Derived, not found."),
    },
}

with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols + NEW)
    w.writeheader()
    for r in rows:
        r = dict(r)
        name = r["full_name"].strip()
        org = r["org"].strip()
        # --- phones: every phone in this file came from the NPI registry practice location
        r["phone_type"] = "practice" if r.get("phone") else ""
        # --- linkedin: search url only, never automated
        kw = urllib.parse.quote("%s %s" % (name, org if org else r["city"]))
        r["linkedin_url"] = ""
        r["linkedin_search_url"] = "https://www.linkedin.com/search/results/people/?keywords=" + kw
        r["channels_tried"] = TRIED
        L = LOCK.get(name)
        if L:
            r["pub_affiliation_lock"] = L["lock"]
            r["pub_source_url"] = L["url"]
            r["pub_years"] = L["years"]
            r["affiliation_history"] = L["hist"]
            r["email"] = L["email"]
            r["email_status"] = L["status"]
            r["email_risk"] = L["risk"]
            r["channel_notes"] = L["note"]
            r["evidence"] = (r["evidence"].rstrip(". ") +
                             ". Affiliation-locked publication places them at Grand Strand "
                             "(Regional) Medical Center, Myrtle Beach SC.")
            r["peds_signal"] = ("none - affiliation history is Grand Strand Medical Center only; "
                                "no children's hospital or pediatric fellowship in the publication trail")
        else:
            r["pub_affiliation_lock"] = "none - no publication passed the affiliation lock"
            r["pub_source_url"] = ""
            r["pub_years"] = ""
            r["affiliation_history"] = ""
            r["channel_notes"] = ("PubMed/EuropePMC name hits were name-only collisions at "
                                  "unrelated institutions and were discarded; no trial, grant or "
                                  "department-page contact found")
        w.writerow(r)
print("wrote", OUT, len(rows), "rows")
