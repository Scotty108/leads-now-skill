#!/usr/bin/env python3
"""round3 build: merge round2 roster with CMS Doctors & Clinicians (DAC) official filings."""
import csv, json, math, os, re, sys

R2 = '/Users/scotty/leads.now/bench/runs/round2__ours__clamped/result.csv'
HERE = os.path.dirname(os.path.abspath(__file__))

DAC_SRC = ("https://data.cms.gov/provider-data/api/1/datastore/query/mj5m-pzi6/0 "
           "(CMS Doctors and Clinicians National Downloadable File, PECOS Medicare "
           "enrollment; official_filing; released 2026-07-09)")

# --- geo: same city-centroid method round 2 used ------------------------------
MB = (33.6891, -78.8867); GV = (34.8526, -82.3940)
CENT = {
 ('MYRTLE BEACH','SC'):(33.6891,-78.8867), ('NORTH MYRTLE BEACH','SC'):(33.8160,-78.6800),
 ('CONWAY','SC'):(33.8360,-79.0478), ('LORIS','SC'):(34.0563,-78.8905),
 ('LITTLE RIVER','SC'):(33.8718,-78.6094), ('GEORGETOWN','SC'):(33.3768,-79.2945),
 ('PAWLEYS ISLAND','SC'):(33.4293,-79.1220), ('MURRELLS INLET','SC'):(33.5510,-79.0359),
 ('SURFSIDE BEACH','SC'):(33.6060,-78.9739), ('GARDEN CITY','SC'):(33.5849,-79.0006),
 ('MULLINS','SC'):(34.2043,-79.2542), ('ANDREWS','SC'):(33.4507,-79.5620),
 ('SHALLOTTE','NC'):(33.9724,-78.3864), ('BOLIVIA','NC'):(34.0668,-78.1483),
 ('WHITEVILLE','NC'):(34.3363,-78.7050), ('SUNSET BEACH','NC'):(33.8804,-78.5100),
 ('SOUTHPORT','NC'):(33.9215,-78.0203), ('SUPPLY','NC'):(34.0396,-78.2350),
 ('LELAND','NC'):(34.2563,-78.0447), ('CALABASH','NC'):(33.8907,-78.5686),
 ('OCEAN ISLE BEACH','NC'):(33.8946,-78.4283), ('TABOR CITY','NC'):(34.1493,-78.8781),
}
# round-2 published distances, reused verbatim so the two rounds are comparable
R2DIST = {('BOLIVIA','NC'):(49.9,None),('CONWAY','SC'):(13.3,None),('GEORGETOWN','SC'):(31.5,None),
 ('LITTLE RIVER','SC'):(19.5,None),('LORIS','SC'):(25.6,None),('MULLINS','SC'):(40.8,None),
 ('MURRELLS INLET','SC'):(13.3,None),('MYRTLE BEACH','SC'):(1.4,None),('NORTH MYRTLE BEACH','SC'):(14.1,None),
 ('PAWLEYS ISLAND','SC'):(22.3,None),('SHALLOTTE','NC'):(35.5,None),('SUNSET BEACH','NC'):(25.8,None),
 ('WHITEVILLE','NC'):(45.5,None)}

def hav(a,b):
    R=3958.8; p1,p2=map(math.radians,(a[0],b[0])); dp=p2-p1; dl=math.radians(b[1]-a[1])
    h=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(h))

def dist_mb(city,state):
    k=(city.upper().strip(),state.upper().strip())
    if k in R2DIST: return R2DIST[k][0]
    if k in CENT: return round(hav(CENT[k],MB),1)
    return None
def dist_gv(city,state):
    k=(city.upper().strip(),state.upper().strip())
    return round(hav(CENT[k],GV),1) if k in CENT else None

RING = ('283','284','290','294','295')

# --- normalisation ------------------------------------------------------------
SUFF={'jr','sr','ii','iii','iv','md','do','mba','phd','pa','pac','crna','faap','facs'}
def norm(s):
    s=re.sub(r'[^a-z ]',' ',(s or '').lower())
    return ' '.join(w for w in s.split() if w and w not in SUFF)
def fl(first,last):
    return (norm(first).split()[0] if norm(first) else '', norm(last).replace(' ',''))

def load(p):
    return json.load(open(os.path.join(HERE,'raw',p)))

dac_roster = load('dac_roster.json')['results']
geo = load('dac_geo.json')
dac_names  = load('dac_bynames.json')
try: dac_extra = load('dac_extra.json')
except Exception: dac_extra=[]

# index DAC by NPI, preferring a record whose city is in our geography
def better(a,b):
    ain=(a['citytown'].upper(),a['state']) in CENT
    bin_=(b['citytown'].upper(),b['state']) in CENT
    if ain!=bin_: return a if ain else b
    # prefer one naming an anesthesia group
    aa='ANESTH' in a['facility_name'].upper(); ba='ANESTH' in b['facility_name'].upper()
    if aa!=ba: return a if aa else b
    return a
DAC={}
for r in dac_roster+geo['tidelands']+geo['geo_anesth']+dac_names+dac_extra:
    n=r['npi']
    DAC[n]=better(DAC[n],r) if n in DAC else r
# all facilities a person enrolls under
FACS={}
for r in dac_roster+geo['tidelands']+geo['geo_anesth']+dac_names+dac_extra:
    FACS.setdefault(r['npi'],set()).add(r['facility_name'])

SWITCHBOARD={'8433477111','8436921000','8436468001','9107211000','9106428011',
             '9104573800','8436521000','8437777000','9103433000','8433479811'}
def phone_kind(rec):
    t=(rec.get('telephone_number') or '').strip()
    if not t: return None,None
    pretty='(%s) %s-%s'%(t[:3],t[3:6],t[6:10]) if len(t)==10 else t
    if 'ANESTH' in rec['facility_name'].upper() and t not in SWITCHBOARD:
        return pretty,'department'
    return pretty,'practice'

def med(rec):
    m=(rec.get('med_sch') or '').strip()
    return m

# --- start from round 2 --------------------------------------------------------
rows=list(csv.DictReader(open(R2)))
COLS=list(rows[0].keys())
NEW=['med_school','med_school_source','grad_year','grad_year_source','cms_primary_specialty',
     'cms_secondary_specialties','employer_group','employer_group_source','training_block_status',
     'round3_delta']
for c in NEW:
    if c not in COLS: COLS.append(c)
for r in rows:
    for c in NEW: r.setdefault(c,'')

# name -> row, for the 6 roster members that carried no NPI
byname={}
for r in rows:
    t=norm(r['full_name']).split()
    if t: byname[(t[0],t[-1])]=r

NONPI_MAP={  # resolved by full-forename + specialty + employer(McLeod) lock
 ('alisha','palliser'):'1740430164', ('david','atkinson'):'1992755797',
 ('ligia','gonzalez'):'1417350026',  ('ahmed','elhaimer'):'1134240682',
 ('michael','wingfield'):'1447287578',('robert','oconnor'):'1952347643',
}
filled=0; newphones=0; orgfill=0
for r in rows:
    npi=r['npi'].strip()
    if not npi:
        t=norm(r['full_name']).split()
        key=(t[0],t[-1]) if t else None
        if key in NONPI_MAP:
            npi=NONPI_MAP[key]
            r['npi']=npi
            r['round3_delta']='npi_resolved_via_CMS_DAC_full_forename+specialty+employer_lock'
    rec=DAC.get(npi)
    if not rec:
        r['training_block_status']='NOT_IN_CMS_DAC (no Medicare enrollment record matched this NPI)'
        continue
    # full-forename guard
    rf=norm(r['full_name']).split(); df=norm(rec['provider_first_name']).split()
    if rf and df and rf[0]!=df[0]:
        r['training_block_status']='DAC_NAME_MISMATCH_rejected (%s vs %s)'%(rf[0],df[0]); continue
    ms=med(rec); gy=(rec.get('grd_yr') or '').strip()
    if ms:
        r['med_school']=ms; r['med_school_source']=DAC_SRC
    if gy:
        r['grad_year']=gy; r['grad_year_source']=DAC_SRC
    sec=', '.join(x for x in [rec.get('sec_spec_1'),rec.get('sec_spec_2'),rec.get('sec_spec_3'),rec.get('sec_spec_4')] if x)
    r['cms_primary_specialty']=rec.get('pri_spec','')
    r['cms_secondary_specialties']=sec
    facs=sorted(f for f in FACS.get(npi,()) if f)
    if facs:
        r['employer_group']=' | '.join(facs); r['employer_group_source']=DAC_SRC
        if not r['org']:
            r['org']=facs[0]; r['org_source']=DAC_SRC; orgfill+=1
    if ms and ms!='OTHER':
        r['training_block_status']='FILLED_medical_school+grad_year (CMS official filing)'; filled+=1
    elif ms=='OTHER':
        r['training_block_status']='PARTIAL_grad_year_only (CMS reports med_sch="OTHER" — school not on the CMS pick-list, typically international)'
        filled+=1
    p,k=phone_kind(rec)
    if p and not r['phone2']:
        r['phone2']=p; r['phone2_type']=k; r['phone2_source']=DAC_SRC; newphones+=1
    if not r['round3_delta']:
        r['round3_delta']='training_block_filled_from_CMS_DAC'

# --- append new people ---------------------------------------------------------
existing_npi={r['npi'].strip() for r in rows if r['npi'].strip()}
existing_name={(norm(r['full_name']).split()[0],norm(r['full_name']).split()[-1])
               for r in rows if norm(r['full_name']).split()}
newrows=[]
seen=set()
for npi,rec in DAC.items():
    if npi in existing_npi or npi in seen: continue
    if rec.get('pri_spec')!='ANESTHESIOLOGY': continue
    city,state=rec['citytown'].upper(),rec['state'].upper()
    if (city,state) not in CENT: continue
    zip5=(rec.get('zip_code') or '')[:3]
    key=fl(rec['provider_first_name'],rec['provider_last_name'])
    if key in existing_name: continue
    seen.add(npi)
    name=' '.join(x for x in [rec['provider_first_name'].title(),
        (rec['provider_middle_name'] or '').title(), rec['provider_last_name'].title()] if x.strip())
    dmb=dist_mb(city,state); dgv=dist_gv(city,state)
    p,k=phone_kind(rec)
    facs=sorted(f for f in FACS.get(npi,()) if f)
    ms=med(rec); gy=(rec.get('grd_yr') or '').strip()
    row={c:'' for c in COLS}
    row.update({
     'full_name':name,'full_name_source':DAC_SRC,
     'title':rec.get('pri_spec',''),'title_source':DAC_SRC,
     'org':facs[0] if facs else '','org_source':DAC_SRC if facs else '',
     'phone':p or '','phone_source':DAC_SRC if p else '','phone_type':k or '',
     'profile_url':'https://npiregistry.cms.hhs.gov/provider-view/%s'%npi,
     'profile_url_source':DAC_SRC,
     'confidence':'single_source','source_count':'1','all_sources':DAC_SRC,
     'npi':npi,'credential':rec.get('cred',''),'city':city,'state':state,
     'postal_code':rec.get('zip_code',''),
     'territory':'Myrtle Beach' if (dmb is not None and dgv is not None and dmb<dgv) else '',
     'dist_myrtle_beach_mi':dmb if dmb is not None else '',
     'dist_greenville_mi':dgv if dgv is not None else '',
     'territory_basis':'practice address %s, %s — postal %s in ring; %s mi from Myrtle Beach centroid vs %s mi Greenville; geo=city_centroid'%(city,state,zip5,dmb,dgv),
     'all_taxonomies':rec.get('pri_spec',''),
     'peds_taxonomy_registered':'false',
     'peds_signal':'NONE_FOUND',
     'peds_evidence':('NONE_FOUND = UNPUBLISHABLE in this source. The CMS DAC specialty '
        'vocabulary contains no "Pediatric Anesthesiology" value at all (measured: pri_spec '
        'values containing "PEDIATRIC" are only "PEDIATRIC MEDICINE"; sec_spec values '
        'containing "ANESTH" are only ANESTHESIOLOGY / ANESTHESIOLOGY,HOSPICE-PALLIATIVE CARE / '
        'ANESTHESIOLOGY,INTERVENTIONAL PAIN MANAGEMENT). So this official filing cannot express '
        'the subspecialty; absence here is not evidence the person lacks it.'),
     'org_provenance':'official_filing (CMS PECOS Medicare enrollment)',
     'reachable':'yes' if p else 'no',
     'linkedin_search_url':'https://www.linkedin.com/search/results/people/?keywords=%s%%20anesthesiology'%name.replace(' ','%20'),
     'med_school':ms,'med_school_source':DAC_SRC if ms else '',
     'grad_year':gy,'grad_year_source':DAC_SRC if gy else '',
     'cms_primary_specialty':rec.get('pri_spec',''),
     'cms_secondary_specialties':', '.join(x for x in [rec.get('sec_spec_1'),rec.get('sec_spec_2'),rec.get('sec_spec_3'),rec.get('sec_spec_4')] if x),
     'employer_group':' | '.join(facs),'employer_group_source':DAC_SRC if facs else '',
     'training_block_status':('FILLED_medical_school+grad_year (CMS official filing)' if ms and ms!='OTHER'
        else 'PARTIAL_grad_year_only (CMS reports med_sch="OTHER")'),
     'round3_delta':'NEW_PERSON_round3 (CMS DAC anesthesiology enumeration; absent from round-2 roster)',
    })
    newrows.append(row)

rows_out=rows+newrows
rows_out.sort(key=lambda r:(r['full_name'] or ''))
with open(os.path.join(HERE,'result.csv'),'w',newline='',encoding='utf-8') as fh:
    w=csv.DictWriter(fh,fieldnames=COLS); w.writeheader()
    for r in rows_out: w.writerow({c:r.get(c,'') for c in COLS})

# also emit a merge-compatible record file
recs=[{ 'full_name':r['full_name'],'title':r['title'],'org':r['org'],'org_domain':r['org_domain'],
        'email':r['email'],'phone':r['phone'],'profile_url':r['profile_url'],
        'source':r['all_sources'] or DAC_SRC } for r in rows_out]
json.dump(recs,open(os.path.join(HERE,'records','round3_all.json'),'w'),indent=1)

strict50=sum(1 for r in rows_out if r['dist_myrtle_beach_mi'] not in ('',None) and float(r['dist_myrtle_beach_mi'])<=50)
inring=sum(1 for r in rows_out if (r['postal_code'] or '')[:3] in RING)
print('rows          : %d  (round2 %d, new %d)'%(len(rows_out),len(rows),len(newrows)))
print('training filled: %d existing rows'%filled)
print('org filled     : %d'%orgfill)
print('phone2 added   : %d'%newphones)
print('with med_school: %d  (non-OTHER %d)'%(sum(1 for r in rows_out if r['med_school']),
       sum(1 for r in rows_out if r['med_school'] and r['med_school']!='OTHER')))
print('with grad_year : %d'%sum(1 for r in rows_out if r['grad_year']))
print('with email     : %d'%sum(1 for r in rows_out if r['email']))
print('in ring postal : %d ; within 50mi of MB: %d'%(inring,strict50))
import collections
print('phone types    :',collections.Counter((r['phone_type'] or 'none') for r in rows_out))
print('phone2 types   :',collections.Counter((r['phone2_type'] or 'none') for r in rows_out))
print('peds STRONG    : %d'%sum(1 for r in rows_out if r['peds_signal']=='STRONG'))
