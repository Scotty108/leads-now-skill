import csv,json,os,re,urllib.parse
BASE='../round1__ours__open/result.csv'
rows=list(csv.DictReader(open(BASE)))
FIELDS=list(rows[0].keys())
if 'row_origin' not in FIELDS: FIELDS.append('row_origin')
if 'peds_citation' not in FIELDS: FIELDS.append('peds_citation')
for r in rows: r['row_origin']='round1_roster'; r.setdefault('peds_citation','')

def key(n):
    n=re.sub(r'[^A-Za-z \-]',' ',(n or '')).lower().replace('-',' ')
    stop={'dr','md','do','rn','np','pa','phd','crna','dnp','jr','sr','ii','iii','iv','faap','facs','fnp','bc','cpnp','msn','aprn'}
    t=[w for w in n.split() if w and w not in stop]
    return (t[0]+' '+t[-1]) if len(t)>=2 else ' '.join(t)
idx={}
for r in rows: idx.setdefault(key(r['full_name']),[]).append(r)

log=[]
def upd(r,**kw):
    for k,v in kw.items():
        if v not in (None,''): r[k]=v

# ---------- McLeod ----------
mp={p['url']:p for p in json.load(open('raw/mcleod_profiles_full.json'))}
alg=json.load(open('raw/mcleod_live_physicians_ALL.json'))
mc_read=0; mc_hits=0
for x in alg:
    u=x.get('scheduling_url')
    if u not in mp: continue
    p=mp[u]; mc_read+=1
    k=key(x['name'])
    if k not in idx: continue
    specs=[s.get('name','') for s in (x.get('specialties') or [])]+[s.get('name','') for s in (x.get('specialties_specific') or [])]
    tb=(p.get('training_block') or '').strip()
    peds = bool(re.search(r'pediatric',' '.join(specs),re.I)) or bool(re.search(r"pediatric|children'?s hospital",tb,re.I))
    for r in idx[k]:
        upd(r, title=', '.join(specs), org_domain='mcleodhealth.org', profile_url=u)
        if tb:
            r['training']=tb
            r['peds_citation']=u
            if peds:
                r['peds_signal']='STRONG'; mc_hits+=1
                r['peds_evidence']=("McLeod Health published physician profile — Board Certification / training block reads: \"%s\" — %s"%(tb[:400],u))
            else:
                r['peds_signal']='NONE_FOUND'
                r['peds_evidence']=("NONE_FOUND = evidence absent, not a claim of no pediatric experience. Read McLeod's own published profile in full; the published Board Certification / Medical School / Residency / Fellowship block names no pediatric training and the directory specialty is '%s'. Block verbatim: \"%s\" — %s"%(', '.join(specs),tb[:300],u))
        else:
            r['peds_citation']=u
            r['peds_evidence']=("NONE_FOUND = evidence absent. McLeod profile read; this provider publishes NO training block at all (no board certification, medical school, residency or fellowship on the page), so no subspecialty could be read either way. Directory specialty '%s' — %s"%(', '.join(specs),u))
        # phone from the nearest practice
        prs=x.get('practices') or []
        if prs:
            r['phone']=prs[0].get('phone') or r['phone']
            r['phone_type']='department'
            r['org']=prs[0].get('name') or r['org']
        r['all_sources']=(r['all_sources']+' | ' if r['all_sources'] else '')+u
        r['source_count']=str(int(r['source_count'] or 1)+1)
        r['confidence']='corroborated'
log.append(('mcleod_profiles_read',mc_read))

# ---------- Tidelands ----------
TIDE=json.load(open('raw/tidelands_r2_raw.json'))
for t in TIDE['roster_matched']:
    name,href=t[0],t[1]
    url='https://www.tidelandshealth.org'+href
    k=key(name)
    for r in idx.get(k,[]):
        upd(r, org_domain='tidelandshealth.org', profile_url=url)
        r['peds_citation']=url
        r['peds_signal']='NONE_FOUND'
        r['peds_evidence']=("NONE_FOUND = evidence absent, not a claim of no pediatric experience. Full Tidelands profile page read: specialty is Anesthesiology only and NO pediatric/children/neonatal/NICU/PICU term appears anywhere on the page. Note the reason: Tidelands publishes a Medical Education / Residency / Fellowship / Board certification block for other specialties (e.g. https://www.tidelandshealth.org/find-a-physician/profile/heather-grabowski-do/) but publishes NO training block for any of its 12 anesthesiologists, so this directory cannot confirm or exclude a pediatric fellowship. — "+url)
        r['all_sources']=(r['all_sources']+' | ' if r['all_sources'] else '')+url
        r['source_count']=str(int(r['source_count'] or 1)+1); r['confidence']='corroborated'

# ---------- Grand Strand ----------
G=json.load(open('records/grandstrand_r2.json'))
for m in G['roster_matches']:
    k=key(m['roster_name']); url=m['citation']
    tr=' | '.join([e for e in (m.get('fellowship',[])+m.get('residency',[])+m.get('internship',[])+m.get('medical_school',[])) if e])
    for r in idx.get(k,[]):
        upd(r, org_domain='mygrandstrandhealth.com', profile_url=url, training=tr)
        r['peds_citation']=url
        specs=', '.join(s['specialty'] for s in m.get('all_specialties',[]))
        if m['peds_grade'] in ('STRONG','MODERATE'):
            r['peds_signal']=m['peds_grade']
            r['peds_evidence']="Grand Strand Health (HCA) directory, embedded physicianData JSON: %s — %s"%(m['peds_grade_reason'],url)
        else:
            r['peds_signal']='NONE_FOUND'
            r['peds_evidence']=("NONE_FOUND = evidence absent, not a claim of no pediatric experience. Grand Strand physicianData read in full: specialties '%s'; credentialsAndAccreditations = %s; bio empty; no pediatric/neonatal term in any field. Note this directory never publishes a board-certification row (0 of 299 profiles) — only a bare boardCertified boolean — so a pediatric subspecialty certificate would not be visible here. — %s"%(specs, tr or 'no training rows published', url))
        r['all_sources']=(r['all_sources']+' | ' if r['all_sources'] else '')+url
        r['source_count']=str(int(r['source_count'] or 1)+1); r['confidence']='corroborated'

# ---------- Conway / ring (optional) ----------
CR='records/conway_ring_r2.json'
conway_read=0
if os.path.exists(CR):
    C=json.load(open(CR))
    for o in C.get('orgs',[]):
        conway_read+=o.get('profiles_fetched') or 0
        for m in o.get('roster_matches',[]):
            k=key(m.get('roster_name') or m.get('name') or '')
            url=m.get('citation') or m.get('url') or ''
            for r in idx.get(k,[]):
                upd(r, org_domain=o.get('org_domain'), profile_url=url)
                tr=m.get('training') or ' | '.join(filter(None,[m.get('fellowship') if isinstance(m.get('fellowship'),str) else ' '.join(m.get('fellowship') or []),
                                                               m.get('residency') if isinstance(m.get('residency'),str) else ' '.join(m.get('residency') or []),
                                                               m.get('board_certifications') if isinstance(m.get('board_certifications'),str) else ' '.join(m.get('board_certifications') or [])]))
                if tr: r['training']=tr
                if url: r['peds_citation']=url
                g=(m.get('peds_grade') or 'NONE_FOUND').upper().replace(' ','_')
                r['peds_signal']=g
                r['peds_evidence']=(m.get('peds_evidence') or m.get('peds_grade_reason') or
                  "NONE_FOUND = evidence absent, not a claim of no pediatric experience. %s directory profile read; no pediatric term in specialty, training or bio."%o.get('org'))+((' — '+url) if url else '')
                if url:
                    r['all_sources']=(r['all_sources']+' | ' if r['all_sources'] else '')+url
                    r['source_count']=str(int(r['source_count'] or 1)+1); r['confidence']='corroborated'
                dp=m.get('phone') or o.get('department_phone')
                if dp and m.get('phone_is_department'): r['phone']=dp; r['phone_type']='department'

# ---------- NEW rows: in-radius providers with a pediatric signal ----------
def blank():
    d={f:'' for f in FIELDS}; d['row_origin']='round2_directory_peds'; return d
new=[]
for o in json.load(open('raw/mcleod_peds_in_radius.json')):
    if key(o['name']) in idx: continue
    d=blank()
    d.update(full_name=o['name'],title=', '.join(o['specialties']),org=o['practice'],org_domain='mcleodhealth.org',
             practice_city=o['city'],practice_state='SC',dist_myrtle_beach_mi=str(o['dist']),territory='Myrtle Beach',
             phone=o['phone'] or '',phone_type='department' if o['phone'] else '',profile_url=o['url'],
             peds_signal=o['grade'],peds_citation=o['url'],
             peds_evidence="McLeod Health published physician profile: %s — %s"%(o['evidence'],o['url']),
             training=o['training'],confidence='single_source',source_count='1',
             all_sources=o['url'],source='McLeod Health physician profile page (rung 2)',
             linkedin_search_url='https://www.linkedin.com/search/results/people/?keywords='+urllib.parse.quote(o['name']+' McLeod Health'))
    new.append(d)
for t in json.load(open('raw/tidelands_r2_raw.json'))['peds_new']:
    if key(t['name']) in idx: continue
    d=blank()
    d.update(full_name=t['name'],title=t['specialty'],org=t['practice'],org_domain='tidelandshealth.org',
             practice_city=t.get('city',''),practice_state='SC',territory='Myrtle Beach',
             phone=t.get('phone',''),phone_type=t.get('phone_type','') if t.get('phone') else '',
             profile_url=t['url'],peds_signal=t['grade'],peds_citation=t['url'],
             peds_evidence=t['evidence']+' — '+t['url'],training=t.get('training',''),
             confidence='single_source',source_count='1',all_sources=t['url'],
             source='Tidelands Health provider directory (browser, rung 4)',
             linkedin_search_url='https://www.linkedin.com/search/results/people/?keywords='+urllib.parse.quote(t['name']+' Tidelands Health'))
    new.append(d)
for g in G['peds_hits']:
    nm=g.get('name') or g.get('gsh_name') or ''
    if not nm or key(nm) in idx: continue
    d=blank()
    d.update(full_name=nm,title=', '.join(s['specialty'] for s in (g.get('all_specialties') or [])) or g.get('specialty',''),
             org=g.get('location_name') or g.get('department_or_practice',[''])[0] if g.get('department_or_practice') else g.get('location_name',''),
             org_domain='mygrandstrandhealth.com',practice_city=g.get('city','Myrtle Beach'),practice_state='SC',
             territory='Myrtle Beach',phone=g.get('phone',''),phone_type='practice' if g.get('phone') else '',
             profile_url=g.get('citation') or g.get('url',''),peds_signal=g.get('peds_grade','MODERATE'),
             peds_citation=g.get('citation') or g.get('url',''),
             peds_evidence="Grand Strand Health (HCA) directory, embedded physicianData JSON: %s — %s"%(g.get('peds_grade_reason',''),g.get('citation') or g.get('url','')),
             training=' | '.join((g.get('fellowship') or [])+(g.get('residency') or [])),
             confidence='single_source',source_count='1',all_sources=g.get('citation') or g.get('url',''),
             source='Grand Strand Health (HCA) directory — embedded physicianData JSON',
             linkedin_search_url='https://www.linkedin.com/search/results/people/?keywords='+urllib.parse.quote(nm+' Grand Strand Health'))
    new.append(d)

allrows=rows+new
with open('result.csv','w',newline='',encoding='utf-8') as fh:
    w=csv.DictWriter(fh,fieldnames=FIELDS); w.writeheader()
    for r in allrows: w.writerow({k:r.get(k,'') for k in FIELDS})
from collections import Counter
print('rows',len(allrows),'(round1',len(rows),'+ new',len(new),')')
print('peds',Counter(r['peds_signal'] for r in allrows))
print('phone_type',Counter(r['phone_type'] for r in allrows))
print('emails',sum(1 for r in allrows if r['email']))
print('mcleod_profiles_read',mc_read,'conway',conway_read)
