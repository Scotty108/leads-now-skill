import csv,json,re,urllib.parse
R1='/Users/scotty/leads.now/bench/runs/round1__ours__clamped/result.csv'
rows=list(csv.DictReader(open(R1,newline='',encoding='utf-8')))
hdr=list(rows[0].keys())
NEWCOLS=['phone_type','phone2','phone2_type','phone2_source','linkedin_search_url','round2_delta']
for c in NEWCOLS:
    if c not in hdr: hdr.append(c)
for r in rows:
    for c in NEWCOLS: r.setdefault(c,'')
    r['phone_type']='practice' if (r.get('phone') or '').strip() else ''
    r['linkedin_search_url']='https://www.linkedin.com/search/results/people/?keywords='+urllib.parse.quote(r['full_name']+' anesthesiology')
    r['round2_delta']=''

by={r['full_name']:r for r in rows}

MCL='https://www.mcleodhealth.org/ (public Algolia index live_physicians, app JUNR3SUCF2 — rung 3, no browser)'
GS='https://www.mygrandstrandhealth.com/ (embedded physicianData JSON in profile server HTML — rung 3, no browser)'

# ---- McLeod roster matches: org + department phone + profile ----
mcl={
 'Olga Chrisman': ('Olga Chrisman','McLeod Health — McLeod Anesthesiology – Seacoast','Little River, SC','(843) 390-8128','https://www.mcleodhealth.org/physician/olga-chrisman/',''),
 'Frederick Bellamy': ('Frederick W. Bellamy','McLeod Health — McLeod Anesthesia – Loris','Loris, SC','(843) 716-7370','https://www.mcleodhealth.org/physician/frederick-w-bellamy/',''),
 'Joshua Gore': ('Joshua R. Gore','McLeod Health — McLeod Anesthesiology – Seacoast','Little River, SC','(843) 390-8128','https://www.mcleodhealth.org/physician/joshua-r-gore/',''),
 'Michelle Lee': ('Michelle D. Lee','McLeod Health — McLeod Anesthesia – Loris','Loris, SC','(843) 716-7370','https://www.mcleodhealth.org/physician/michelle-d-lee/','PEDS'),
 'Edward Wallace': ('Edward A. Wallace','McLeod Health — McLeod Anesthesia – MRMC','Florence, SC','(843) 777-8752','https://www.mcleodhealth.org/physician/edward-wallace/',''),
}
delta={'people':0,'emails':0,'peds':0,'dept':0}
for nm,(disp,org,city,ph,url,flag) in mcl.items():
    r=by[nm]
    d=[]
    if not (r.get('org') or '').strip():
        r['org']=org; r['org_source']=MCL; d.append('org')
    if not (r.get('org_domain') or '').strip():
        r['org_domain']='mcleodhealth.org'; r['org_domain_source']=MCL
    if not (r.get('profile_url') or '').strip():
        r['profile_url']=url; r['profile_url_source']=MCL; d.append('profile_url')
    r['phone2']=ph; r['phone2_type']='department'; r['phone2_source']=MCL
    delta['dept']+=1; d.append('department_phone')
    if flag=='PEDS':
        r['peds_signal']='STRONG'
        r['peds_evidence']=("Board Certification: Anesthesiology; Pediatric Anesthesiology — https://www.mcleodhealth.org/physician/michelle-d-lee/ "
          "|| Residency 2007 Children's Hospital Colorado, Aurora CO; med school Creighton 2002 / Univ of Colorado HSC 2006 — same page "
          "|| McLeod live_physicians Algolia record carries specialties [Anesthesiology, Pediatric Anesthesiology]; she is the ONLY pediatric "
          "anesthesiologist in the entire 805-physician McLeod index. NOT in NPI: taxonomy 207LP3000X is absent from her NPI record.")
        delta['peds']+=1; d.append('peds_signal=STRONG')
    r['round2_delta']='+'.join(d)

# ---- Grand Strand roster matches ----
gs={
 'Derek Horstemeyer': ('Man In The Box Anesthesia','(843) 692-1061','https://www.mygrandstrandhealth.com/physicians/profile/Dr-Derek-L-Horstemeyer-MD'),
 'Dwayne Livigni': ('Teamhealth Anesthesia','(843) 692-1062','https://www.mygrandstrandhealth.com/physicians/profile/Dr-Dwayne-LiVigni-DO'),
}
for nm,(grp,ph,url) in gs.items():
    r=by[nm]; d=[]
    if not (r.get('org') or '').strip():
        r['org']='Grand Strand Medical Center (HCA) — '+grp; r['org_source']=GS; d.append('org')
    if not (r.get('org_domain') or '').strip():
        r['org_domain']='mygrandstrandhealth.com'; r['org_domain_source']=GS
    if not (r.get('profile_url') or '').strip():
        r['profile_url']=url; r['profile_url_source']=GS; d.append('profile_url')
    r['phone2']=ph; r['phone2_type']='department'; r['phone2_source']=GS+' providerLocations['+grp+']'
    delta['dept']+=1; d.append('department_phone')
    d.append('hcaEmployee=False -> hcahealthcare.com pattern email WITHHELD')
    r['round2_delta']='+'.join(d)

# ---- Jon Halling: first-party published email from PMC ----
r=by['Jon Halling']
r['email']='Jon.Halling@hcahealthcare.com'
r['email_source']='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=PMC11249181'
r['email_confidence']='published'
r['email_label']='first_party_published'
r['email_evidence_source']=('PMID 39015587 / PMC11249181 (2024), HCA Healthcare Journal of Medicine, "Burnout and Health Scores Among '
 'Residency Programs as an Indicator of Wellness." Corresponding author block: "Correspondence to: Jon Halling, MD, MBA '
 '(Jon.Halling@hcahealthcare.com)". Affiliation on the paper: "Grand Strand Medical Center, Myrtle Beach, SC" — affiliation-locked to the '
 'roster city, and FULL FORENAME "Jon" matches roster "Jon Halling" (not an initial).')
if not (r.get('org') or '').strip():
    r['org']='Grand Strand Medical Center (HCA), Myrtle Beach'; r['org_source']=r['email_source']
if not (r.get('org_domain') or '').strip():
    r['org_domain']='hcahealthcare.com'; r['org_domain_source']=r['email_source']
r['round2_delta']='email(first_party_published)+org'
delta['emails']+=1

# ---- 6 NEW in-radius anesthesiologists found only in the McLeod index ----
NEW=[
 ('Alisha F. Palliser','MD','McLeod Health — McLeod Anesthesia – Loris','Loris','SC','29569','(843) 716-7370','https://www.mcleodhealth.org/physician/alisha-f-palliser/'),
 ('David O. Atkinson','MD','McLeod Health — McLeod Anesthesia – Loris','Loris','SC','29569','(843) 716-7370','https://www.mcleodhealth.org/physician/daniel-o-atkinson/'),
 ('Ligia E. Cisneros-Gonzalez','MD','McLeod Health — McLeod Anesthesia – Loris','Loris','SC','29569','(843) 716-7370','https://www.mcleodhealth.org/physician/ligia-e-cisneros-gonzalez/'),
 ('Ahmed Elhaimer','MD','McLeod Health — McLeod Anesthesia – Loris','Loris','SC','29569','(843) 716-7370','https://www.mcleodhealth.org/physician/ahmed-elhaimer/'),
 ('Michael D. Wingfield','DO','McLeod Health — McLeod Anesthesia – Loris','Loris','SC','29569','(843) 716-7370','https://www.mcleodhealth.org/physician/michael-d-wingfield/'),
 ("Robert O'Connor",'MD','McLeod Health — McLeod Anesthesiology – Seacoast','Little River','SC','29566','(843) 390-8128','https://www.mcleodhealth.org/physician/robert-oconnor/'),
]
DIST={'Loris':25.5,'Little River':17.2}
for nm,deg,org,city,st,zp,ph,url in NEW:
    r={c:'' for c in hdr}
    r['full_name']=nm; r['full_name_source']=MCL
    r['title']='Anesthesiology'+(', Critical Care Medicine' if nm=='Ahmed Elhaimer' else ''); r['title_source']=MCL
    r['org']=org; r['org_source']=MCL
    r['org_domain']='mcleodhealth.org'; r['org_domain_source']=MCL
    r['profile_url']=url; r['profile_url_source']=MCL
    r['phone']=ph; r['phone_source']=MCL; r['phone_type']='department'
    r['credential']=deg; r['city']=city.upper(); r['state']=st; r['postal_code']=zp
    r['territory']='Myrtle Beach'; r['dist_myrtle_beach_mi']=DIST[city]
    r['territory_basis']='practice address %s, SC — within 50 mi of Myrtle Beach; geo=city_centroid'%city
    r['confidence']='single_source'; r['source_count']='1'; r['all_sources']=MCL
    r['peds_taxonomy_registered']='unknown (not matched to an NPI record in this run)'
    r['peds_signal']='NONE_FOUND'
    r['peds_evidence']='McLeod directory lists specialty Anesthesiology only; no pediatric board certification or pediatric fellowship on the profile — %s'%url
    r['reachable']='yes'
    r['linkedin_search_url']='https://www.linkedin.com/search/results/people/?keywords='+urllib.parse.quote(nm+' anesthesiology')
    r['round2_delta']='NEW PERSON (not in round-1 NPI roster; found via McLeod rung-3 index)'
    r['org_provenance']='McLeod Health public physician index'
    rows.append(r); delta['people']+=1; delta['dept']+=1

with open('result.csv','w',newline='',encoding='utf-8') as fh:
    w=csv.DictWriter(fh,fieldnames=hdr); w.writeheader()
    for r in rows: w.writerow({k:r.get(k,'') for k in hdr})
print('rows',len(rows))
print('delta',json.dumps(delta))
em=sum(1 for r in rows if (r.get('email') or '').strip())
dept=sum(1 for r in rows if (r.get('phone_type')=='department') or (r.get('phone2_type')=='department'))
peds=sum(1 for r in rows if r.get('peds_signal')=='STRONG')
print('emails',em,'dept_phone_rows',dept,'peds_strong',peds)
json.dump(delta,open('raw/delta.json','w'),indent=1)

# ================= appended: Grand Strand full-index sweep additions =================
GS2='https://www.mygrandstrandhealth.com/ (all 299 profiles from physicians.xml fetched; physicianData JSON parsed from each — rung 3, no browser)'
CMC='https://www.conwaymedicalcenter.com/providers/farayi-mbuvah-md/'
NEW2=[
 ('Brandon Sloop','MD','1962529578','Grand Strand Medical Center (HCA) — Teamhealth Anesthesia','Myrtle Beach','SC','29572','(843) 692-1062','department','https://www.mygrandstrandhealth.com/physicians/profile/Dr-Brandon-Sloop-MD',1.4,'Myrtle Beach','practice address Myrtle Beach, SC — 1.4 mi from Myrtle Beach centroid'),
 ('Desiree Aird','MD','1528471406','Grand Strand Medical Center (HCA) — Teamhealth Anesthesia','Myrtle Beach','SC','29572','(843) 692-1062','department','https://www.mygrandstrandhealth.com/physicians/profile/Dr-Desiree-Aird-MD',1.4,'Myrtle Beach','practice address Myrtle Beach, SC — 1.4 mi from Myrtle Beach centroid'),
 ('Songoli C Umeh','MD','1356635163','Grand Strand Medical Center (HCA) staff — Weatherby Locums Inc','Fort Lauderdale','FL','','(800) 586-5022','answering_service','https://www.mygrandstrandhealth.com/physicians/profile/Dr-Songoli-C-Umeh-MD',None,'OUT OF RADIUS (locums)','listed on the Grand Strand (Myrtle Beach) medical-staff directory, but her registered practice address is the Weatherby Locums agency in Fort Lauderdale FL — counted as FOUND, NOT counted as in_radius'),
]
rows2=list(csv.DictReader(open('result.csv',newline='',encoding='utf-8')))
hdr2=list(rows2[0].keys())
for nm,deg,npi,org,city,st,zp,ph,pt,url,dist,terr,basis in NEW2:
    r={c:'' for c in hdr2}
    r['full_name']=nm; r['full_name_source']=GS2
    r['title']='Anesthesiology'; r['title_source']=GS2
    r['org']=org; r['org_source']=GS2
    r['org_domain']='mygrandstrandhealth.com'; r['org_domain_source']=GS2
    r['profile_url']=url; r['profile_url_source']=GS2
    r['phone']=ph; r['phone_source']=GS2+' providerLocations'; r['phone_type']=pt
    r['npi']=npi; r['credential']=deg; r['city']=city.upper(); r['state']=st; r['postal_code']=zp
    r['territory']=terr; r['dist_myrtle_beach_mi']=dist if dist else ''
    r['territory_basis']=basis
    r['confidence']='single_source'; r['source_count']='1'; r['all_sources']=GS2
    r['peds_taxonomy_registered']='unknown (NPI record not re-fetched this run)'
    r['peds_signal']='NONE_FOUND'
    r['peds_evidence']='Grand Strand physicianData lists providerSpecialties=[Anesthesiology] only; credentialsAndAccreditations empty/no pediatric fellowship — %s'%url
    r['reachable']='yes'
    r['linkedin_search_url']='https://www.linkedin.com/search/results/people/?keywords='+urllib.parse.quote(nm+' anesthesiology')
    r['round2_delta']='NEW PERSON (Grand Strand 299-profile physicianData sweep)'
    r['org_provenance']='Grand Strand Medical Center public physician directory'
    rows2.append(r)
# Mbuvah clinic line (his own pain clinic, not the CMC switchboard)
for r in rows2:
    if r['full_name']=='Farayi Mbuvah':
        r['phone2']='843-839-4598'; r['phone2_type']='department'
        r['phone2_source']=CMC+' (Pain Management clinic line, 811 82nd Parkway Suite B, Myrtle Beach SC 29572 — his own service line, not the 843-347-7111 CMC switchboard)'
        r['round2_delta']=((r.get('round2_delta') or '')+'+department_phone').lstrip('+')
with open('result.csv','w',newline='',encoding='utf-8') as fh:
    w=csv.DictWriter(fh,fieldnames=hdr2); w.writeheader()
    for r in rows2: w.writerow({k:r.get(k,'') for k in hdr2})
print('FINAL rows',len(rows2))
em=[r['full_name'] for r in rows2 if (r.get('email') or '').strip()]
dept=[r['full_name'] for r in rows2 if r.get('phone_type')=='department' or r.get('phone2_type')=='department']
peds=[r['full_name'] for r in rows2 if r.get('peds_signal')=='STRONG']
print('emails',len(em),em)
print('dept phone rows',len(dept))
print('peds STRONG',peds)
