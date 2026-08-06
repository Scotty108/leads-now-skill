import json,sys,time,os
P="/Users/scotty/leads.now/bench/runs/round3__skillit__clamped/log.jsonl"
def log(**kw):
    kw["ts"]=time.strftime("%Y-%m-%dT%H:%M:%S%z")
    with open(P,"a") as f: f.write(json.dumps(kw)+"\n")
if __name__=="__main__":
    log(**json.loads(sys.argv[1]))
