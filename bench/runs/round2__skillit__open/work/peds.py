import json,re
rows=json.load(open('all_profiles.json'))
PED=re.compile(r'\b(pediatric|paediatric|peds|neonat|childrens?\s+hospital|child health)',re.I)
STRONGF={'board certification','board certifications','certification','fellowship','specialty','training'}
def grade(r):
    hits=[]
    strong=False;mod=False
    for k,v in r['fields'].items():
        if not v: continue
        m=PED.search(v)
        if m:
            hits.append(f"{k}: {v[:120]}")
            if k.strip().lower() in STRONGF: strong=True
            else: mod=True
    sp=r.get('specialties') or ''
    if PED.search(sp):
        hits.append("Specialty: "+sp[:120]); strong=True
    return ('strong' if strong else 'moderate' if mod else 'none'), hits
for r in rows:
    g,h=grade(r); r['peds']=g; r['peds_ev']=' || '.join(h[:3])
ANE=re.compile(r'anesthesi|anaesthes|nurse anesthet|crna',re.I)
def isane(r):
    return bool(ANE.search(r.get('specialties') or '')) or bool(ANE.search((r.get('practice') or '')))
tot=len(rows)
sig=[r for r in rows if r['peds']!='none']
print("PROFILES READ: %d"%tot)
print("ANY pediatric signal (record-scoped): %d  (strong %d, moderate %d)"%(len(sig),
      sum(1 for r in sig if r['peds']=='strong'),sum(1 for r in sig if r['peds']=='moderate')))
ane=[r for r in rows if isane(r)]
aneped=[r for r in ane if r['peds']!='none']
print("ANESTHESIA providers across all directories: %d"%len(ane))
print("  of those with a pediatric signal: %d"%len(aneped))
for r in aneped: print("   *",r['system'],"|",r['name'],"|",r['peds'],"|",r['peds_ev'][:150])
from collections import Counter
print("\nby system (any peds signal):",Counter(r['system'] for r in sig))
print("by system (profiles):",Counter(r['system'] for r in rows))
# chrome control: how many would have matched on WHOLE page text (bio included)
bio_only=[r for r in rows if r['peds']=='none' and PED.search(r.get('bio') or '')]
print("\nCHROME/BIO CONTROL: %d profiles mention pediatric ONLY in free-text bio (excluded)"%len(bio_only))
json.dump(rows,open('all_profiles.json','w'))
# emails published in McLeod directory
em=[r for r in rows if any(k.lower()=='email' for k in r['fields'])]
print("\nDIRECTORY-PUBLISHED EMAIL fields: %d"%len(em))
for r in em[:20]: print("   ",r['system'],r['name'],"=>",[v for k,v in r['fields'].items() if k.lower()=='email'][0][:70])
