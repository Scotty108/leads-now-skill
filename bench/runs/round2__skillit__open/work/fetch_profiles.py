import json,sys,os,urllib.request,concurrent.futures as cf,gzip,io
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
def get(u):
    try:
        r=urllib.request.Request(u,headers={"User-Agent":UA,"Accept":"text/html","Accept-Encoding":"gzip"})
        with urllib.request.urlopen(r,timeout=45) as f:
            b=f.read()
            if f.headers.get("Content-Encoding")=="gzip": b=gzip.decompress(b)
            return u,f.status,b.decode("utf-8","replace")
    except Exception as e:
        return u,getattr(e,'code',0),""
urls=[l.strip() for l in open(sys.argv[1]) if l.strip()]
out=sys.argv[2]; os.makedirs(out,exist_ok=True)
ok=0;bad=0
with cf.ThreadPoolExecutor(int(sys.argv[3])) as ex:
    for u,st,body in ex.map(get,urls):
        if st==200 and body:
            fn=out+"/"+u.rstrip("/").split("/")[-1].replace("?","_")[:150]+".html"
            open(fn,"w",encoding="utf-8").write(body);ok+=1
        else: bad+=1;print("FAIL",st,u,file=sys.stderr)
print(f"{out}: {ok} ok, {bad} failed of {len(urls)}")
