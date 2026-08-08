---
name: leads-now
description: Build or improve a verified contact list. Finds people from a description — "pediatric anesthesiologists within 50 miles of Myrtle Beach", "RevOps leads at Series B fintechs" — by sourcing from organization websites and public registries. Also enriches a half-finished spreadsheet the user already has, and grades an existing list for deliverability. Produces a CSV with a source and a confidence label on every field. Use when the user wants leads, prospects, contacts, candidates or sourcing, uploads a partial lead sheet, or is manually visiting sites and copying names into a spreadsheet. Not for sending outreach and not for consumer or personal contact data.
license: MIT
compatibility: Runs in Claude Code, Cowork, and the Claude apps. Needs code execution for the deterministic helpers. Web search and page fetching enable automatic sourcing; without them it still enriches a list you provide. Browser tools are optional and used only for blocked sources. Python 3.8+, standard library only, no API keys or paid services.
---

# leads.now — find, enrich, and verify contact lists

Replaces the manual loop: search for orgs, open each site, find the staff
directory, copy names, cross-check another database, guess the email format.
That loop is where the hours go — the recruiter this was built from spends
about 40% of her week in it.

## What this does and does not do

Stated up front so a reviewer can confirm it in one read.

- **No network calls from any shipped code.** `scripts/leadkit.py` imports only
  `argparse, csv, glob, json, re, sys, unicodedata, collections`. It reads local
  files, transforms them, writes local files. Nothing else.
- **No credentials, no API keys, no accounts.** Nothing to configure.
- **No runtime instruction fetching.** Every behavior is in the files you
  installed. This skill never downloads prose that tells Claude what to do, so
  what you review is what runs.
- **All fetching happens through the host agent's own tools**, under its normal
  permissions — not from inside a script.
- **Writes** the CSV and intermediate JSON to the working directory you point it
  at. It does not touch anything else.

## Step 1 — route to the right job

Read what the user actually brought, pick one branch, say which in one line,
then read that branch's file. Do not run the whole pipeline when they asked for
one part of it.

| They brought | Branch | Read |
|---|---|---|
| A description of people, no list | **DISCOVER** | `references/discover.md` |
| A spreadsheet, CSV, or pasted rows with gaps | **ENRICH** | `references/enrich.md` |
| A finished list, wants it graded or cleaned | **VERIFY** | `references/verify.md` |
| A shortlist, wants to know who is worth calling | **QUALIFY** | `references/qualify.md` |
| "Find me X and get me their emails" | **FULL** | discover, then enrich, then verify |

Signals that separate them: a file or pasted rows means ENRICH. A description of
a kind of person means DISCOVER. Words like *check*, *validate*, *clean*,
*bounce*, *deliverable* mean VERIFY. A quality no directory field carries —
*past* experience, subspecialty depth, "which of these should I call" — means
QUALIFY. When genuinely ambiguous, ask one question — never run a 40-org sweep
for someone who wanted a spreadsheet tidied.

**Enumerate cheap, qualify selective.** QUALIFY is research-grade work and costs
accordingly. Run it on a ranked shortlist, never on a full population: twelve
people researched properly beats four hundred skimmed, and costs less.

If a reference file is missing you were installed from SKILL.md alone. The
essentials of every branch are inlined below; continue without it.

## Step 1b — classify the population, then load its pack

Before choosing a single source, answer one question: **does a roster of these
people exist anywhere, or must you sample?**

Take the highest class that applies:

| Class | The test | Enumerable? |
|---|---|---|
| **Licensed** | Fined or prosecuted for practising without one? | Yes, completely |
| **Public payroll** | Does a taxpayer fund the salary? | Yes |
| **Entity principal** | Is the person the business? | Yes, via the filing |
| **Credentialed** | Letters after the name that somebody verifies? | Partial |
| **Association** | A trade body they would plausibly join? | Partial |
| **Privately employed** | None of the above | **No** |

Enumerable populations get a denominator — "41 of 41". Samplable ones get
"18 across 26 orgs checked", and you never imply that is everyone. **Say which
regime you are in**, or a user reads a sample as a census and concludes the
territory is empty when it is not.

Then load the matching **`references/vertical-*.md`** pack if one exists — it
carries the concrete endpoints and the traps already paid for. **Having no pack
is the normal case**; work `references/sources.md`, which derives the register
for a population nobody wrote a section for.

## Step 2 — check what this surface can do

Capabilities differ across Claude surfaces. Check **before** promising an
outcome, and never announce a plan you cannot execute.

| You can… | Lane | What to do |
|---|---|---|
| Run code **and** fetch pages | **A** | Source automatically across many orgs |
| Run code and search, no bulk fetch | **B** | Small batches, user confirms the org list |
| Run code only | **C** | Enrich the list the user provides |
| No code execution | **D** | Hand over the method, queries and template |

Claude Code and Cowork are usually Lane A. The Claude apps are usually B or C:
they run code in a sandbox that generally has **no outbound network**, so never
fetch from inside Python — fetch with your own tools and pass the text in.

Lane D is deliberate. Without code execution you cannot guarantee the refusal
rule below, so hand over a method rather than a list you cannot stand behind,
and say that is what you are doing.

## The one rule

**Never invent a contact.** A guessed email that bounces costs more than a blank
cell — it burns sender reputation and makes the whole list untrustworthy. Every
row carries its source and how it was obtained. Anything unresolved stays empty.
If the list looks thin and you are tempted to pattern-match a person into
existence, the correct output is a thinner list.

This holds in every branch and every lane. It is the only non-negotiable part.

## Step 3 — the escalation ladder

Most org directories do not give up their names to a plain fetch. Measured
across four hospital systems in one geography: one served clean HTML, two
returned a JavaScript shell with zero names, and one returned **403**. Expect
about half to resist. Climb only as far as you need:

| Rung | Try | Why it is in this order |
|---|---|---|
| **1** | Registry / public JSON API | Structured, authoritative, free, unblocked |
| **2** | Static page fetch | Works on server-rendered directories |
| **3** | The page's own XHR/JSON endpoint | Returns fields, not prose to re-parse |
| **4** | Browser tools, if present | The only rung that reads a 403 |

**Rung 1 first, always.** Where Step 1b found an enumerable class, its register
returns the people outright — structured, free, and indifferent to whether any
employer blocks you. A blocked directory is then only a *partial* loss: you have
the person and are missing their title. Do not open a browser for data a
register already gave you.

Two traps recur in every register measured. **Query the parent category, never
the narrow one** — sub-categories are sparsely self-reported, so the narrow
query returns an empty list that looks like a correct answer. And **registers
truncate silently** — deep paging often repeats instead of advancing, with no
error and a normal-looking total. Shard the query, track seen IDs, and treat a
page that adds nothing new as the ceiling.

**Rung 4 is optional and capability-detected.** Browser tools do not exist in
the Claude apps or Cowork sandboxes. If absent, stop at rung 3 and record the
org as unreadable. Never make the skill depend on them.

Read `references/blocked.md` the first time a source refuses you. Short version:
name which wall it was, never try to defeat a CAPTCHA or bot check, hand off to
the user when a visible browser is available, and always report blocked orgs.

## Step 4 — resolve contacts

Work down this waterfall; stop at the first that yields an address.

1. A work email published on the org's own site
2. Public professional or official sources
3. A role-based inbox (`info@`, `contact@`) — real, but not a person
4. The org's email pattern, inferred from addresses you actually found
5. Where the population publishes — papers, filings, permits, speaker pages —
   the address printed alongside the name, **locked to the employer** or the
   name collides and the address belongs to someone else
6. A contact form or business phone, when email confidence is insufficient

**Yield is set by the population, not by your effort.** Public-payroll and
academic bodies publish addresses outright; licence registers publish a phone
and almost never an inbox. Predict the ceiling from the class before promising
a number — see `references/sources.md`.

Label every phone with what KIND of number it is (`direct` / `department` /
`practice` switchboard). An NPI phone defaults to `practice`. Reporting a
switchboard as reachability overstates the deliverable — round 1 reported 100%
reachable on numbers that were all front desks.

Never automate LinkedIn. Emit a `linkedin_search_url` for a human to click.
See `references/contact-channels.md`.

Never hand-write an address. Run the helper:

```
python3 leadkit.py emails --domain acme.com \
  --known "Jane Doe:jdoe@acme.com" --known "Bob Ray:bray@acme.com" \
  --name "Ann Lee"
```

Two agreeing samples give `pattern_confirmed`; one gives `pattern_likely`;
**zero known addresses produce nothing at all.** Before concluding a domain has
none, check `/contact`, `/press` and `/legal`, PDFs and press kits, job
postings, and public commit history. One confirmed address unlocks the domain.

**Label how each address was obtained** — do not collapse these into one
"verified" flag:

`first_party_published` · `official_filing` · `public_professional_profile` ·
`role_based` · `pattern_inferred` · `smtp_accepted` · `catch_all` ·
`commercial_provider` · `previously_delivered`

`catch_all` matters: such a domain accepts every address, so a validity check
passes for nonsense. Treating that as verification is how a list looks perfect
and bounces anyway.

## Step 5 — merge, emit, report

```
python3 leadkit.py merge records/*.json -o merged.json
python3 leadkit.py bands merged.json --place "Myrtle Beach" --state SC \
        --radius 50 -o banded.json
python3 leadkit.py csv banded.json -o leads.csv
```

`bands` measures each person from the centre and prints the distance bands.
Run it whenever the ask named a place — it is what makes any radius readable
off one sweep. A row it cannot place keeps a **null** distance and never a
zero, so an unplaceable person is never sorted to the top as the closest lead.

`merge` collapses one person found via several orgs and keeps every source URL.
**Order inputs most-trustworthy-first** — the first non-empty value wins, so the
registry before the marketing page keeps the registry's title. In the Claude
apps, write the CSV in the sandbox and attach it.

Then report, in this order:

1. **Counts** — orgs searched, people found, emails resolved, split by label
2. **Distance bands** — see below
3. **The gaps** — blocked orgs with the reason, people with a single source
4. **The file**

Never give a row count without saying how many rows carry a real email. "312
leads" where 40 have addresses is a misleading number.

### Always band by distance, and sort nearest first

A radius is a guess the user made before seeing the data, and it is often not
the radius they meant. Sweep at the wider number, then report in bands so **any
radius is readable off one run** without a re-search:

```
within 15 mi   18      within 30 mi   +12      within 50 mi   +11
just outside   4 at 51-60 mi  (Jane Doe 53, ...)
```

Include the CSV column `dist_mi` and sort ascending — a territory is worked
outward from the centre, so nearest-first is the order the list gets used in.

**Name the near-misses explicitly.** Someone at 51 miles is a fact the user can
act on; a hard cutoff hides them and looks identical to their not existing. The
territory is still theirs to decide — surface the row, do not re-scope the job.

## Where data may come from

| Zone | Sources | Use |
|---|---|---|
| **Green** | Government and registry bulk data, first-party company sites, OpenAlex, ORCID, GLEIF, Overture | Freely, as customer-facing fact |
| **Yellow** | Scraped dataset mirrors with unclear provenance | Candidate generation only, then verify independently — never as the stated source |
| **Red** | Breach dumps, stolen databases, credential collections | Never |

Business contact data only. Do not scrape sites behind a login whose terms
forbid it, do not collect consumer or personal contact details, and do not send
outreach. What the user does with the CSV is subject to CAN-SPAM, GDPR and CCPA.

## The toolkit

The helpers are deterministic on purpose: the refusal must not depend on a model
deciding to be careful on a given run.

**If `scripts/leadkit.py` is present, use it.** That is the full version.

**If it is missing**, you were installed from SKILL.md alone — some install
paths carry only this file. Write the block below to `leadkit.py` and use it
identically. Same three commands, same refusal.

It is plain readable Python, standard library only, with no network access and
no shell-out — the same code as `scripts/leadkit.py`, condensed.

```python
# leadkit.py — fallback. Python 3.8+, stdlib only.
import argparse,csv as C,glob,json,re,sys,unicodedata
from collections import Counter
F=["full_name","title","org","org_domain","email","phone","linkedin","profile_url"]
L=["city","state","postal_code"]   # location must survive the merge, or a radius cannot be measured
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
    # A domain can run TWO formats at once (measured: 3 first.last AND 2 flast
    # on the same host). Majority-reporting hides a coin flip, so downgrade.
    rivals={p:c for p,c in v.items() if p!=top and c>=1}
    if rivals and conf=="pattern_confirmed": conf="pattern_likely"
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
                      "mixed_format_domain":bool(rivals),"competing_patterns":rivals or None,
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
        if key not in M: M[key]={f:None for f in F+L};M[key]["_sources"]=[];M[key]["_field_sources"]={}
        e=M[key];s=x.get("source") or x.get("profile_url") or "unknown"
        if s not in e["_sources"]: e["_sources"].append(s)
        for f in F+L:
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
    h+=L+["confidence","source_count","all_sources"]
    with open(a.output,"w",newline="",encoding="utf-8") as fh:
        w=C.writer(fh);w.writerow(h)
        for r in rows:
            fs=r.get("_field_sources") or {};row=[]
            for f in F: row+=[r.get(f) or "",fs.get(f,"")]
            row+=[r.get(f) or "" for f in L]
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

## Reference files

Read on the trigger named in Step 1; each holds one branch's detail so only the
relevant one loads.

| File | Read when |
|---|---|
| `references/discover.md` | Branch is DISCOVER or FULL |
| `references/enrich.md` | Branch is ENRICH, or a file was uploaded |
| `references/verify.md` | Branch is VERIFY, or grading deliverability |
| `references/qualify.md` | Branch is QUALIFY, or the ask involves past experience |
| `references/contact-channels.md` | Resolving emails, phones or LinkedIn for anyone |
| `references/blocked.md` | A source returns 403, a CAPTCHA, or an empty shell |
| `references/sources.md` | **Any population with no pack below** — derives its register |
| `references/bulk-sources.md` | Verified free endpoints — FMCSA, NPI, SEC Form D, Socrata |
| `references/vertical-healthcare.md` | Physicians, nurses, allied health, practices |
| `references/record-format.md` | Writing records, or deciding merge order |
