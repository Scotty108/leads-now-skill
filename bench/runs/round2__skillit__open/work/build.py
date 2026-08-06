import csv,json,re,unicodedata,os
OUT='/Users/scotty/leads.now/bench/runs/round2__skillit__open'
prof=json.load(open('all_profiles.json'))
idx={x['scheduling_url'].rstrip('/').split('/')[-1]:x for x in json.load(open('mcleod_index.json'))}
def A(s):
    s=unicodedata.normalize('NFKD',s or '');s=''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'[^a-z]','',s.lower())
STOP={'md','do','dr','jr','sr','ii','iii','iv','pa','pac','crna','np','faap','facs','dpm','phd','mbbs','dnp'}
def toks(n):
    t=[A(w) for w in re.split(r'[\s,\.]+',n or '')]
    return [w for w in t if w and w not in STOP]
def key(n):
    t=toks(n); return (t[0],t[-1]) if len(t)>=2 else None
# build directory index; McLeod names come from the Algolia record
P={}
for r in prof:
    nm=r['name']
    if r['system']=='McLeod Health':
        s=r['source_url'].rstrip('/').split('/')[-1]; nm=idx.get(s,{}).get('name') or nm
        r['name']=nm
    k=key(nm)
    if k: P.setdefault(k,[]).append(r)
ANE=re.compile(r'anesthesi|anaesthes',re.I)
CONWAY_DEPT='843-347-8288 / 843-347-8352'
roster=list(csv.DictReader(open('/Users/scotty/leads.now/bench/runs/round2__skillit__clamped/result.csv')))
NEWCOLS=['peds_signal_strength','peds_evidence_field','directory_profile_url','directory_specialties',
         'directory_training_published','none_found_kind','employment_status','department_phone',
         'department_phone_label','department_phone_source','email_withheld_reason']
cols=list(roster[0].keys())+[c for c in NEWCOLS if c not in roster[0]]
matched=0; peds_hits=0; dept=0
rows=[]
for r in roster:
    for c in NEWCOLS: r.setdefault(c,'')
    k=key(r['full_name']); cands=P.get(k,[])
    m=None
    for c in cands:
        if ANE.search((c.get('specialties') or '')+' '+(c.get('practice') or '')): m=c;break
    if m is None and cands: m=cands[0]
    if m:
        matched+=1
        r['directory_profile_url']=m['source_url']; r['directory_specialties']=m.get('specialties','')
        pub=[k2 for k2 in m['fields'] if m['fields'][k2]]
        r['directory_training_published']='; '.join(pub) or 'NONE'
        r['employment_status']=m.get('employment','') or ('mcLeod_physician_associates=%s'%idx.get(m['source_url'].rstrip('/').split('/')[-1],{}).get('mcLeod_physician_associates') if m['system']=='McLeod Health' else '')
        if m['peds']!='none':
            peds_hits+=1
            r['peds_signal_strength']=m['peds']; r['peds_evidence_field']=m['peds_ev']
            r['peds_signal']='%s - %s'%(m['peds'],m['peds_ev'][:180])
            r['peds_source_url']=m['source_url']
            r['confidence']='confirmed' if m['peds']=='strong' else 'probable'
            r['evidence']=('Directory profile: '+m['peds_ev'])[:300]
        else:
            r['peds_signal_strength']='none'
            r['none_found_kind']=('checked_and_absent - directory publishes %s for this person'%r['directory_training_published']) if pub else 'unpublishable - directory publishes no training/certification block for this person'
            r['peds_signal']='NONE_FOUND (%s)'%r['none_found_kind'].split(' - ')[0]
        # department phone
        dp=''
        if m['system']=='McLeod Health':
            rec=idx.get(m['source_url'].rstrip('/').split('/')[-1],{})
            for p in rec.get('practices',[]):
                if ANE.search(p.get('name','')) and p.get('phone'):
                    dp=p['phone']; r['department_phone_label']=p['name']; r['department_phone_source']=m['source_url']; break
        if not dp and m['system']=='Conway Medical Center':
            dp=CONWAY_DEPT; r['department_phone_label']='Conway Medical Center Anesthesia'
            r['department_phone_source']='https://www.conwaymedicalcenter.com/patients-visitors/phone-directory/'
        if dp:
            r['department_phone']=dp; dept+=1
            r['phone']=dp.split(' / ')[0]; r['phone_type']='department'
            r['phone_source']='%s (%s)'%(r['department_phone_label'],r['department_phone_source'])
    else:
        r['none_found_kind']='no_directory_record - person not found in any of the 4 directories read'
        r['peds_signal_strength']='none'
    if not r.get('email'):
        r['email_withheld_reason']=('mcleodhealth.org first.last pattern observed on 15 published addresses, '
          'but this person is not confirmed employed by the pattern owner (McLeod anesthesia shows '
          'mcLeod_physician_associates=False / contracted group) - pattern withheld per employment gate') if 'MCLEOD' in (r.get('org','') or '').upper() else \
          'no address published by any of 1708 directory profiles read; no confirmed employer pattern applies'
    rows.append(r)
# add directory-discovered anesthesia providers not on the NPI roster
have={key(r['full_name']) for r in roster}
added=0
for m in prof:
    if not ANE.search((m.get('specialties') or '')+' '+(m.get('practice') or '')): continue
    k=key(m['name'])
    if not k or k in have: continue
    have.add(k)
    pub=[k2 for k2 in m['fields'] if m['fields'][k2]]
    nr={c:'' for c in cols}
    nr.update(full_name=m['name'],org=m.get('practice') or m['system'],city=m.get('city',''),state=m.get('state','SC'),
      phone=m.get('phone',''),phone_type='practice',
      source_url=m['source_url'],source_rung='2/3 (org directory profile page)',
      confidence='confirmed' if m['peds']=='strong' else ('probable' if m['peds']=='moderate' else 'unconfirmed'),
      evidence=(m['peds_ev'] or 'Directory profile lists anesthesiology; pediatric capability not established')[:300],
      email_status='none_no_observed_address',email_risk='n/a - no address emitted',
      directory_profile_url=m['source_url'],directory_specialties=m.get('specialties',''),
      directory_training_published='; '.join(pub) or 'NONE',employment_status=m.get('employment',''),
      peds_signal_strength=m['peds'],peds_evidence_field=m['peds_ev'],
      peds_signal=(m['peds']+' - '+m['peds_ev'][:180]) if m['peds']!='none' else 'NONE_FOUND',
      peds_source_url=m['source_url'] if m['peds']!='none' else '',
      none_found_kind='' if m['peds']!='none' else ('checked_and_absent' if pub else 'unpublishable - no training block published'),
      external_id='NPI '+m['npi'] if m.get('npi') else 'directory profile (no NPI published)',
      last_verified_note='directory profile read %s'%__import__('datetime').date.today(),
      email_withheld_reason='no address published on this profile',
      linkedin_search_url='https://www.linkedin.com/search/results/people/?keywords='+
        __import__('urllib.parse',fromlist=['q']).quote(m['name']+' '+(m.get('practice') or m['system'])),
      territory='Grand Strand / Pee Dee', name_source=m['source_url'], org_source=m['source_url'],
      taxonomy=m.get('specialties',''))
    if m['system']=='Conway Medical Center':
        nr['department_phone']=CONWAY_DEPT;nr['department_phone_label']='Conway Medical Center Anesthesia'
        nr['department_phone_source']='https://www.conwaymedicalcenter.com/patients-visitors/phone-directory/'
        nr['phone']=CONWAY_DEPT.split(' / ')[0];nr['phone_type']='department'
    if m['system']=='McLeod Health':
        rec=idx.get(m['source_url'].rstrip('/').split('/')[-1],{})
        for p in rec.get('practices',[]):
            if ANE.search(p.get('name','')) and p.get('phone'):
                nr['department_phone']=p['phone'];nr['department_phone_label']=p['name']
                nr['department_phone_source']=m['source_url'];nr['phone']=p['phone'];nr['phone_type']='department';break
    rows.append(nr);added+=1
w=csv.DictWriter(open(OUT+'/result.csv','w',newline=''),fieldnames=cols,extrasaction='ignore')
w.writeheader()
for r in rows: w.writerow({c:r.get(c,'') for c in cols})
dp_total=sum(1 for r in rows if r.get('department_phone'))
print("roster rows %d | matched to a directory profile %d | roster peds hits %d | added from directories %d | TOTAL %d"%(len(roster),matched,peds_hits,added,len(rows)))
print("department phones on rows:",dp_total)
print("phone_type:",__import__('collections').Counter(r.get('phone_type') for r in rows))
print("peds_signal_strength:",__import__('collections').Counter(r.get('peds_signal_strength') for r in rows))
