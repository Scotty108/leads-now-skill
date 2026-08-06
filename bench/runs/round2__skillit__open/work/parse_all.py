import re,glob,json,html,os
U=lambda s: html.unescape(re.sub(r'<[^>]+>',' ',s or '')).replace('\xa0',' ')
W=lambda s: re.sub(r'\s+',' ',U(s)).strip()
PED=re.compile(r'\b(pediatric|paediatric|peds|children\'?s|neonat|infant|adolescen)',re.I)
out=[]

# ---------- McLeod: h6 Label: / p value pairs (record-scoped; nav has no h6 pairs) ----------
idx={x['scheduling_url'].rstrip('/').split('/')[-1]:x for x in json.load(open('mcleod_index.json'))}
mc=0
for f in glob.glob('p_mcleod/*.html'):
    h=open(f,encoding='utf-8',errors='replace').read(); slug=os.path.basename(f)[:-5]
    # scope: the doctor record block only
    m=re.search(r'<div class="doctor-right"(.*?)<div class="google-map-wrapper"',h,re.S)
    scope=m.group(1) if m else ''
    fields={}
    for lab,val in re.findall(r'<h6>\s*([^<:]{2,40}):?\s*</h6>\s*<p>(.*?)</p>',scope or h,re.S):
        fields[W(lab)]=W(val)
    rec=idx.get(slug,{})
    specs='; '.join(s['name'] for s in rec.get('specialties',[]) if s.get('name'))
    pr=(rec.get('practices') or [{}])[0]
    out.append(dict(system='McLeod Health',source_url=f"https://www.mcleodhealth.org/physician/{slug}/",
        name=rec.get('name') or W(re.search(r'<h1[^>]*>(.*?)</h1>',h,re.S).group(1)) if re.search(r'<h1',h) else slug,
        degree=rec.get('degree',''),specialties=specs,fields=fields,
        practice=pr.get('name',''),city=pr.get('city',''),state=pr.get('state',''),zip=pr.get('zip',''),
        phone=pr.get('phone',''),npi='',employment='',bio=''))
    mc+=1

# ---------- Grand Strand: physicianData JSON ----------
gs=0
for f in glob.glob('p_gs/*.html'):
    h=open(f,encoding='utf-8',errors='replace').read()
    i=h.find('"physicianData":')
    if i<0: continue
    dec=json.JSONDecoder()
    try: d,_=dec.raw_decode(h[i+len('"physicianData":'):])
    except Exception: continue
    creds=d.get('credentialsAndAccreditations') or []
    fields={}
    for c in creds:
        t=(c.get('type') or '').strip()
        v=' '.join(x for x in [c.get('credential'),c.get('organizationOrSchool'),c.get('yearReceived')] if x)
        if t: fields[t]=(fields.get(t,'')+' | '+v).strip(' |')
    sp=d.get('specialties') or d.get('physicianSpecialties') or []
    if isinstance(sp,list): specs='; '.join(x.get('specialtyName') or x.get('name') or str(x) if isinstance(x,dict) else str(x) for x in sp)
    else: specs=str(sp or '')
    locs=d.get('practiceLocations') or d.get('locations') or []
    l0=locs[0] if locs else {}
    nm=' '.join(x for x in [d.get('physicianFirstName'),d.get('physicianMiddleInitial'),d.get('physicianLastName')] if x)
    out.append(dict(system='Grand Strand Health',source_url='https://www.mygrandstrandhealth.com/physicians/profile/'+os.path.basename(f)[:-5],
        name=nm,degree=d.get('physicianDesignation') or '',specialties=specs,fields=fields,
        practice=l0.get('practiceName') or l0.get('name') or '',city=l0.get('city') or '',state=l0.get('state') or '',
        zip=l0.get('postalCode') or l0.get('zip') or '',phone=l0.get('phone') or l0.get('phoneNumber') or '',
        npi=d.get('physicianNpi') or '',employment=('hcaEmployee=%s'%d.get('hcaEmployee')),bio=d.get('physicianBio') or ''))
    gs+=1

# ---------- Conway: wrap divs ----------
cm=0
WRAPS={'providerbiowrap':'Board Certification','residencywrap':'Residency','fellowshipwrap':'Fellowship',
       'medicaleducationwrap':'Medical Education','internshipwrap':'Internship','undergraduateschoolwrap':'Undergraduate',
       'graduateschoolwrap':'Graduate School','specialtywrap':'Specialty'}
for f in glob.glob('p_cmc/*.html'):
    h=open(f,encoding='utf-8',errors='replace').read()
    fields={}
    for w,lab in WRAPS.items():
        m=re.search(r'<div class="%s">(.*?)</div>'%w,h,re.S)
        if m:
            v=W(re.sub(r'<script.*?</script>','',m.group(1),flags=re.S))
            v=re.sub(r'^%s(s)?\b'%re.escape(lab),'',v).strip()
            if v: fields[lab]=v
    t=re.search(r'<title>(.*?)</title>',h,re.S)
    nm=W(t.group(1)).split('|')[0].split(' - ')[0].strip() if t else os.path.basename(f)[:-5]
    sp=re.search(r'<div class="providerspecialtywrap">(.*?)</div>',h,re.S)
    specs=W(sp.group(1)) if sp else ''
    if not specs:
        sp2=re.search(r'class="provider-specialty[^"]*">(.*?)</',h,re.S); specs=W(sp2.group(1)) if sp2 else ''
    ph=re.findall(r'8\d{2}[.\-]\d{3}[.\-]\d{4}',W(re.search(r'<div class="providerlocationwrap">(.*?)</div>',h,re.S).group(1)) if re.search(r'<div class="providerlocationwrap">',h,re.S) else '')
    out.append(dict(system='Conway Medical Center',source_url='https://www.conwaymedicalcenter.com/provider/'+os.path.basename(f)[:-5],
        name=nm,degree='',specialties=specs,fields=fields,practice='',city='Conway',state='SC',zip='',
        phone=ph[0] if ph else '',npi='',employment='',bio=''))
    cm+=1

# ---------- Tidelands ----------
td=0
for r in json.load(open('tide_profiles.json'))['rows']:
    fields={k:v for k,v in (r.get('rec') or {}).items() if k!='_eduRaw' and v}
    out.append(dict(system='Tidelands Health',source_url='https://www.tidelandshealth.org'+r['slug'],
        name=r.get('name',''),degree='',specialties=r.get('specialties',''),fields=fields,
        practice='',city='',state='SC',zip='',phone=(r.get('phones') or [''])[0],npi=r.get('npi',''),
        employment='',bio=r.get('bio','')))
    td+=1

json.dump(out,open('all_profiles.json','w'))
print("parsed: McLeod %d, GrandStrand %d, Conway %d, Tidelands %d, TOTAL %d"%(mc,gs,cm,td,len(out)))
# field-publication census
from collections import Counter
for sysname in ['McLeod Health','Grand Strand Health','Conway Medical Center','Tidelands Health']:
    rows=[r for r in out if r['system']==sysname]
    c=Counter()
    for r in rows:
        for k in r['fields']: c[k]+=1
    print("\n%s (%d profiles) field publication:"%(sysname,len(rows)))
    for k,v in c.most_common(12): print("   %-28s %d"%(k,v))
