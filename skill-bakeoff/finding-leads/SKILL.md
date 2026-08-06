---
name: finding-leads
description: Builds a verified contact list — names, organizations, titles, work emails, phones, with a source for every row — for a described population, using only free public sources; also enriches or scores a list the user already has. Use whenever someone wants to find people matching a description ("pediatric anesthesiologists within 50 miles of Myrtle Beach", "RevOps leads at Series B fintechs"), build a prospect or candidate list, source clinicians, fill in missing emails, titles or companies on a spreadsheet, or judge which rows of a list are trustworthy. Also use when they say "find leads", "build me a list", "source candidates", "get me contacts at", "enrich this CSV", "find their emails", "is this list still any good", or paste a half-finished sheet with gaps to fill, even if they never say lead generation. Do not use for writing the outreach message, for looking up one person who is already named, or for tidying a spreadsheet that needs no new contact data.
---

# Finding leads

Turn a description of a kind of person into a contact list the user can act on tomorrow, where
every row names its source and every address says whether it was published or derived.

## The rule that decides whether this run was any good

**Report the denominator, always.** A list of 12 means nothing. "72 anesthesiologists practice
within 50 miles; 31 have a reachable address; 12 are confirmed pediatric-capable" is the answer.
A run that cannot say how big the population was has not searched it, only sampled it.

The failure this skill exists to prevent: a plausible list of famous employers with invented
email addresses and no way to tell which rows are real. Guarding against that costs recall
nowhere, because the registries below are census-grade and free.

**Search one level broader than the request, then narrow with evidence.** A specialty, seniority,
or job-title filter applied at the query is applied to a *self-reported* field, so it silently
deletes most of the population. Query the parent category, then qualify individuals from what
sources actually say about them. Measured on the origin case: providers within 50 miles of Myrtle
Beach filed under *Pediatric Anesthesiology* number **zero**, while providers filed under the
parent *Anesthesiology* number **72**. The narrow query returns an empty list that looks like a
correct answer to a question with no answer.

## Pick the branch, say which one, then read only its file

Name the branch in one line before starting. Route on what the user brought, not on what they
called it.

| They brought | Branch | Read now |
|---|---|---|
| A description of people, no list | DISCOVER | `references/discover-people.md` |
| A file, paste, or list with gaps | ENRICH | `references/enrich-list.md` |
| A list they doubt, or "is this any good" | VERIFY | `references/verify-list.md` |
| A description plus a way to reach them | FULL | `references/discover-people.md` first; the others when their step begins |

When the request names a population *and* attaches a file, the file is the frame: run ENRICH.
When a branch finishes and the user's stated outcome needs the next one, chain without asking.
"How do I reach them", "with contact info", and "and their emails" all mean FULL.

Two files serve every branch. Read `references/source-access.md` before fetching anything from an
organization's own website. Read `references/email-tradecraft.md` before writing any email address
into any output.

## Sources

Free, no key, and reachable by ordinary fetching:

- **NPI Registry** (`npiregistry.cms.hhs.gov/api/`) — every US clinician, by specialty and place.
  Mandatory enumeration makes it a census, not a sample. The discovery layer for anyone licensed.
- **NUCC provider taxonomy** — the specialty code set. Shipped at `assets/nucc_individual_taxonomy.csv`.
- **Census gazetteer** — ZIP and place centroids for radius work. Shipped at `assets/us_geo.csv.gz`.
- **PubMed E-utilities** — corresponding-author addresses. One of the few sources of *published*
  work emails for clinicians and academics.
- **SEC EDGAR full-text search**, **YC company list**, **public job boards** — company frames and
  hiring signals for business populations.
- The organization's own site — team, leadership, provider, and press pages.

Everything else is the open web. There is no paid contact database here, and none is needed for
discovery; paid tools reach under 25% of independent clinicians, which is the gap this exploits.

## The spine every branch runs

1. **Restate the target as a filter** — population, place, radius, and what disqualifies someone.
   Say it back in one line before working.
2. **Build the frame.** Enumerate the whole population from a registry or a company list before
   looking at any individual. Never start from a search engine; it returns the famous and hides
   the tail.
3. **Bound it.** Radius work resolves the centre first — a 50-mile ring routinely crosses a state
   line, and querying only the state the user named silently drops half the ring.
4. **Enrich** each row toward title, department, organization, and a route to reach them.
5. **Gate, then deliver.** Run the audit script. Fix every failure. Never hand over a list that
   failed its own gate without saying so on the first line.

## Stop rather than invent

Fabrication is the one failure the user cannot detect. Each of these stops the run:

- The population is ambiguous — "dentists near me" with no location, "fintech" with no size or
  stage. Ask for the missing bound. Do not pick one.
- A place name is ambiguous across states. The geo script refuses and lists the candidates; pass
  the qualified name back, do not guess.
- The frame query hit the registry ceiling. The count is unknown, not large. Split and re-run.
- No source at a domain published any address. Emit the organization's contact route, not a
  formula's output.

When a run partially fails, deliver what it found *and* the accounting. A short sourced list plus
a clear statement of what was unreachable beats a long list nobody can trust.

## Output

Write a CSV using the columns in `assets/output_template.csv`, and a brief above it.

`confidence` scores exactly one proposition: **this person meets the description the user asked
for, at this organization.** When the request was narrower than the frame — a subspecialty, a
seniority, a function — the narrow attribute is part of that proposition, so a person who is
plainly a match for the broad category but unproven on the narrow one is not `confirmed`.

- `confirmed` — a source states the person meets the full description asked for.
- `probable` — a source states most of it, and the rest is a reasonable read of that source.
- `unconfirmed` — the narrow attribute is unestablished. Say what is missing, in `evidence`.

Filter the output to the profession actually requested. A specialty search returns physicians,
physician assistants, and nurse anaesthetists together, and delivering a `PA-C` against a request
for physicians is a defect the user finds in row 4.

`email_status` is separate and about the *address*, and never inherits from `confidence`. A
`confirmed` person routinely has a derived address. The email tradecraft file defines its values.

Every row carries a `source_url` that a person can open. `evidence` is the phrase that justified
the row, quoted or paraphrased in under 15 words.

The brief, above the file, states in this order:

1. The filter, restated.
2. The denominator: population found, how many passed each filter, how many are delivered.
3. Confidence and email_status counts, from the audit script's output.
4. **Organizations that could not be read, and why** — blocked, JavaScript-only, no directory. A
   silently skipped source is indistinguishable from a source with nothing in it.
5. What the run could not establish, and the one action that would resolve it.

Never present a derived address as found. Never fill a title from a specialty. Never round a
count that a script printed exactly.

## Scripts

Call them by their path inside the skill; write every output into a separate working directory,
never into the skill's own folder, so a second run cannot overwrite the first. Standard library,
no installs, and none of them touch the network — fetching is yours to do, which is what keeps
this working where sandboxes have no outbound access.

```
python3 scripts/geo_filter.py   resolve "Myrtle Beach, SC" --radius 50
python3 scripts/geo_filter.py   filter roster.csv --center "Myrtle Beach, SC" --radius 50 \
                                --zip-col postal_code --dedupe-by npi -o near.csv
python3 scripts/npi_query.py    taxonomy "pediatric anesthesiology"
python3 scripts/npi_query.py    plan --taxonomy "A||B" --zip3 283,284,294,295 --outdir raw
python3 scripts/npi_query.py    parse raw --out roster.csv
python3 scripts/npi_query.py    employers --roster near.csv --orgdir orgs -o with_orgs.csv
python3 scripts/email_pattern.py learn --evidence evidence.csv -o patterns.csv
python3 scripts/email_pattern.py apply --roster roster.csv --patterns patterns.csv -o send.csv
python3 scripts/email_pattern.py hygiene send.csv
python3 scripts/audit_list.py   final.csv --retrieved 777 --in-scope 72 --blocked "Org: 403"
```

`npi_query.py parse` exits 3 when more pages exist and 4 when a query is truncated at the
registry ceiling. Treat exit 4 as "this count is not a total" and split the query.

To rehearse or repair any of this without network access, run the scripts against
`assets/fixture/`, which holds a normal registry response, an empty one, and an error one.
`workflow.md` records why each piece exists and which assumptions it rests on; read it before
changing anything here.

## Boundaries

- Read what is published. Do not attempt to defeat a bot check, solve a CAPTCHA, forge headers to
  impersonate a browser, or reach anything behind a login or paywall.
- Do not use browser automation on a site whose terms forbid automated access. Social networks
  generally do; read them by hand or not at all.
- Registry data is public record and fine to use. Say so if asked, and keep the source on the row.
- Sending is the user's decision, not this skill's. Produce the list and the risk numbers.


## Contact channels

Read `references/contact-channels.md` when resolving emails, phones or
LinkedIn. Three rules it enforces, all from measured round-1 results:

- **Label the phone type.** NPI publishes the *practice* switchboard, not a
  direct dial. Default `phone_type=practice`; upgrade only on evidence.
  Reporting a switchboard as reachability overstates the deliverable.
- **Corresponding-author emails must be affiliation-locked.** Papers publish
  addresses hospitals do not, but a name-only query collides. Confirm the
  paper's affiliation matches the person's org before accepting the address.
- **Never automate LinkedIn.** Emit a `linkedin_search_url` for a human to
  click; record a `linkedin_url` only when a public page links it.


## If the scripts are missing

Some install paths carry only `SKILL.md` and drop `scripts/` and `assets/` —
saving a skill from a chat does this. Detect it: if `scripts/` is absent, the
bundled geography and the NPI planner are gone too, so say what you lost
(radius resolution and paging determinism) rather than pretending to have them.

The deterministic parts that must survive regardless are the email refusal and
the merge, because they are what stop a fabricated address from shipping.
Write the block below to `leadkit.py` and use it for those two jobs. It is
plain readable Python, standard library only, no network and no shell-out.

```python
# leadkit.py — fallback. Python 3.8+, stdlib only.
import argparse,csv as C,glob,json,re,sys,unicodedata
from collections import Counter
F=["full_name","title","org","org_domain","email","phone","linkedin","profile_url"]
N={"dr","mr","mrs","ms","prof","md","do","rn","np","pa","phd","dds","dmd","jr","sr","ii","iii","iv","faap","facs"}
P={"first.last":lambda f,l:f+"."+l,"firstlast":lambda f,l:f+l,"flast":lambda f,l:f[0]+l,
   "f.last":lambda f,l:f[0]+"."+l,"firstl":lambda f,l:f+l[0],"first_last":lambda f,l:f+"_"+l,
   "last.first":lambda f,l:l+"."+f,"lastf":lambda f,l:l+f[0],"first":lambda f,l:f,"last":lambda f,l:l}
def A(s):
    s=unicodedata.normalize("NFKD",s or "");s="".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z]","",s.lower())
def T(x):
    t=[A(w) for w in (x or "").split(",")[0].replace("."," ").split()]
    return [w for w in t if w and w not in N]
PART={"van","von","de","del","della","der","den","di","da","dos","das","du","la","le",
      "el","al","bin","ibn","mac","mc","st","san","santa","ter","ten","op"}
def SN(x):
    t=T(x);return (t[0],t[-1]) if len(t)>=2 else None
def SV(x):
    # "van der Berg" -> orgs disagree (vanderberg / berg). Emitting one silently
    # at pattern_confirmed is the worst failure here, so flag the ambiguity.
    t=T(x)
    if len(t)<2: return []
    i=next((j for j,w in enumerate(t[1:],1) if w in PART),None)
    if i is None: return [t[-1]]
    j="".join(t[i:]);return [t[-1]] if j==t[-1] else [j,t[-1]]
def emails(a):
    k=[]
    for e in a.known:
        if ":" in e: n,ad=e.rsplit(":",1);k.append((n.strip(),ad.strip()))
    v=Counter()
    for full,ad in k:
        if "@" not in ad: continue
        loc,dom=ad.split("@",1)
        if dom.strip().lower()!=a.domain.lower(): continue   # other domain proves nothing
        p=SN(full)
        if not p: continue
        for nm,fn in P.items():
            try:
                if fn(*p)==loc.strip().lower(): v[nm]+=1
            except IndexError: pass
    if not v:   # the refusal: no evidence, no output
        print(json.dumps({"domain":a.domain,"pattern":None,"confidence":"unknown",
            "reason":"no known-good address for this domain; refusing to guess",
            "resolved":[],"unresolved":a.name},indent=2));return 0
    n=v.most_common(1)[0][1]
    top=sorted([p for p,c in v.items() if c==n],key=lambda p:(-len(p),p))[0]
    conf="pattern_confirmed" if n>=2 else "pattern_likely"
    r,u=[],[]
    for full in a.name:
        p=SN(full)
        if not p: u.append(full);continue
        vs=SV(full)
        try: cands=[P[top](p[0],v) for v in vs]
        except IndexError: u.append(full);continue
        e={"name":full,"email":cands[0]+"@"+a.domain,"pattern":top,"confidence":conf,
           "source":"inferred_from_known_addresses"}
        if len(cands)>1:
            e["confidence"]="pattern_likely";e["ambiguous_surname"]=True
            e["alternates"]=[c+"@"+a.domain for c in cands[1:]]
        r.append(e)
    print(json.dumps({"domain":a.domain,"pattern":top,"confidence":conf,"evidence_count":n,
                      "resolved":r,"unresolved":u},indent=2));return 0
def merge(a):
    recs=[]
    for pat in a.inputs:
        for path in (glob.glob(pat) or [pat]):
            try: d=json.load(open(path))
            except Exception as e: print("warn: %s (%s)"%(path,e),file=sys.stderr);continue
            for it in (d if isinstance(d,list) else [d]):
                if isinstance(it,dict) and it.get("full_name"): it.setdefault("source",path);recs.append(it)
    if not recs: print("no usable records",file=sys.stderr);return 1
    M={}
    for x in recs:
        dom=re.sub(r"^www\.","",(x.get("org_domain") or "").strip().lower())
        key=(" ".join(T(x.get("full_name",""))),dom or A(x.get("org","")))
        if not key[0]: continue
        # all fields start empty so the fill loop records provenance for every one
        if key not in M: M[key]={f:None for f in F};M[key]["_sources"]=[];M[key]["_field_sources"]={}
        e=M[key];s=x.get("source") or x.get("profile_url") or "unknown"
        if s not in e["_sources"]: e["_sources"].append(s)
        for f in F:
            if x.get(f) not in (None,"",[]) and e.get(f) in (None,"",[]):
                e[f]=x[f];e["_field_sources"][f]=s      # first non-empty wins: order = trust
    out=[]
    for e in M.values():
        c=len(e["_sources"]);e["_confidence"]="corroborated" if c>=2 else "single_source"
        e["_source_count"]=c;out.append(e)
    out.sort(key=lambda x:(x.get("org") or "",x.get("full_name") or ""))
    json.dump(out,open(a.output,"w"),indent=2,ensure_ascii=False) if a.output else print(json.dumps(out,indent=2,ensure_ascii=False))
    corr=sum(1 for m in out if m["_confidence"]=="corroborated");em=sum(1 for m in out if m.get("email"))
    print("  %d record(s) -> %d person(s); %d corroborated; %d with an email"%(len(recs),len(out),corr,em))
    return 0
def tocsv(a):
    rows=json.load(open(a.input))
    if isinstance(rows,dict): rows=[rows]
    if a.only_with_email: rows=[r for r in rows if r.get("email")]
    h=[]
    for f in F: h+=[f,f+"_source"]
    h+=["confidence","source_count","all_sources"]
    with open(a.output,"w",newline="",encoding="utf-8") as fh:
        w=C.writer(fh);w.writerow(h)
        for r in rows:
            fs=r.get("_field_sources") or {};row=[]
            for f in F: row+=[r.get(f) or "",fs.get(f,"")]
            row+=[r.get("_confidence",""),r.get("_source_count","")," | ".join(r.get("_sources") or [])]
            w.writerow(row)
    em=sum(1 for r in rows if r.get("email"))
    print("wrote %s\n  %d row(s), %d with an email"%(a.output,len(rows),em));return 0
ap=argparse.ArgumentParser(prog="leadkit");sub=ap.add_subparsers(dest="cmd",required=True)
e=sub.add_parser("emails");e.add_argument("--domain",required=True);e.add_argument("--known",action="append",default=[])
e.add_argument("--name",action="append",default=[]);e.add_argument("--json",action="store_true");e.set_defaults(fn=emails)
m=sub.add_parser("merge");m.add_argument("inputs",nargs="+");m.add_argument("-o","--output");m.set_defaults(fn=merge)
c=sub.add_parser("csv");c.add_argument("input");c.add_argument("-o","--output",required=True)
c.add_argument("--only-with-email",action="store_true");c.set_defaults(fn=tocsv)
_a=ap.parse_args();sys.exit(_a.fn(_a))
```

Resolve the radius by hand in this mode: query the registry by state, then
filter by the practice city or postal code against the places the user named.
Say in the report that the radius was approximated.
