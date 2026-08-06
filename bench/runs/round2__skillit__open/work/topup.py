import json,urllib.request,concurrent.futures as cf,string
APP="JUNR3SUCF2";KEY="ad6044da492ef74aedd8e768a1c21b5d"
URL=f"https://{APP}-dsn.algolia.net/1/indexes/live_physicians/query"
def q(b):
    r=urllib.request.Request(URL,data=json.dumps(b).encode(),headers={"X-Algolia-API-Key":KEY,"X-Algolia-Application-Id":APP,"Content-Type":"application/json"})
    return json.load(urllib.request.urlopen(r,timeout=45))
recs={h["objectID"]:h for h in json.load(open('mcleod_index.json'))}
before=len(recs)
def pull(args):
    spec,gen=args
    ff=[[f"specialties.name:{spec}"]]
    if gen: ff.append([f"gender:{gen}"])
    out=[];b={"query":"","hitsPerPage":100,"facetFilters":ff,"page":0}
    d=q(b);out+=d["hits"]
    for p in range(1,d["nbPages"]): b["page"]=p;out+=q(b)["hits"]
    return out
jobs=[(s,g) for s in ["Family Medicine","Primary Care"] for g in ["Male","Female","male","female"]]
with cf.ThreadPoolExecutor(8) as ex:
    for hits in ex.map(pull,jobs):
        for h in hits: recs.setdefault(h["objectID"],h)
print("after gender subpartition:",len(recs))
def pl(l):
    out=[];b={"query":l,"hitsPerPage":100,"page":0}
    d=q(b);out+=d["hits"]
    for p in range(1,d["nbPages"]): b["page"]=p;out+=q(b)["hits"]
    return out
with cf.ThreadPoolExecutor(12) as ex:
    for hits in ex.map(pl,list(string.ascii_lowercase)):
        for h in hits: recs.setdefault(h["objectID"],h)
print("after letter sweep:",len(recs),"(was",before,")")
json.dump(list(recs.values()),open('mcleod_index.json','w'))
