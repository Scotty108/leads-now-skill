import json,urllib.request,concurrent.futures as cf
APP="JUNR3SUCF2";KEY="ad6044da492ef74aedd8e768a1c21b5d"
URL=f"https://{APP}-dsn.algolia.net/1/indexes/live_physicians/query"
def q(body):
    r=urllib.request.Request(URL,data=json.dumps(body).encode(),
        headers={"X-Algolia-API-Key":KEY,"X-Algolia-Application-Id":APP,"Content-Type":"application/json"})
    return json.load(urllib.request.urlopen(r,timeout=45))
facets=json.load(open('alg_facets.json'))["facets"]
specs=list(facets["specialties.name"].keys())
recs={}
def pull(s):
    out=[]
    body={"query":"","hitsPerPage":100,"facetFilters":[[f"specialties.name:{s}"]],"page":0}
    d=q(body); out+=d["hits"]; tot=d["nbHits"]; np=d["nbPages"]
    for p in range(1,np):
        body["page"]=p; out+=q(body)["hits"]
    return s,tot,out
with cf.ThreadPoolExecutor(12) as ex:
    for s,tot,hits in ex.map(pull,specs):
        if len(hits)<tot: print("TRUNCATED",s,len(hits),tot)
        for h in hits: recs[h["objectID"]]=h
print("unique from specialty partition:",len(recs),"of nbHits 805")
# also practices partition to catch records with no specialty facet
pracs=list(facets["practices.name"].keys())
def pullp(s):
    out=[];body={"query":"","hitsPerPage":100,"facetFilters":[[f"practices.name:{s}"]],"page":0}
    d=q(body);out+=d["hits"];np=d["nbPages"]
    for p in range(1,np): body["page"]=p;out+=q(body)["hits"]
    return out
with cf.ThreadPoolExecutor(12) as ex:
    for hits in ex.map(pullp,pracs):
        for h in hits: recs.setdefault(h["objectID"],h)
print("after practices partition:",len(recs))
json.dump(list(recs.values()),open('mcleod_index.json','w'))
