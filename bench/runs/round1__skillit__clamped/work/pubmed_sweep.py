import urllib.request, urllib.parse, csv, json, re, time, sys
OUT="/Users/scotty/leads.now/bench/runs/round1__skillit__clamped/work"
rows=list(csv.DictReader(open(OUT+"/with_orgs.csv")))
E="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
def get(u):
    return urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'lead-research/1.0'}),timeout=45).read().decode('utf-8','replace')
res=[]
for i,r in enumerate(rows):
    ln=r['last_name'].strip(); fn=r['first_name'].strip()
    if not ln or not fn: continue
    term='%s %s[Author] AND (anesthesi*[Affiliation] OR "South Carolina"[Affiliation] OR "North Carolina"[Affiliation])'%(ln,fn[0])
    try:
        j=json.loads(get(E+"esearch.fcgi?db=pubmed&retmode=json&retmax=8&term="+urllib.parse.quote(term)))
        ids=j['esearchresult'].get('idlist',[])
    except Exception as e:
        res.append((r['npi'],fn,ln,'ERR',str(e)[:60],'')); time.sleep(0.4); continue
    if not ids:
        res.append((r['npi'],fn,ln,'no_hits','','')); time.sleep(0.4); continue
    try:
        x=get(E+"efetch.fcgi?db=pubmed&retmode=xml&id="+",".join(ids))
    except Exception as e:
        res.append((r['npi'],fn,ln,'ERR_fetch',str(e)[:60],'')); time.sleep(0.4); continue
    emails=set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", x))
    hit=[e for e in emails if ln.lower()[:5] in e.lower() or (fn.lower()[:3]+ln.lower()[:1]) in e.lower()]
    peds = 'pediatric' in x.lower() or 'paediatric' in x.lower() or 'children' in x.lower()
    res.append((r['npi'],fn,ln,'hits:%d'%len(ids),";".join(sorted(hit)), 'peds_pub' if peds else ''))
    time.sleep(0.4)
w=csv.writer(open(OUT+"/pubmed_evidence.csv","w",newline=""))
w.writerow(["npi","first_name","last_name","status","emails","peds_pub_signal"])
w.writerows(res)
print("done",len(res))
