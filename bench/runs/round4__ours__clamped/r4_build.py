import csv, json, datetime
SRC='../round3__ours__clamped/result.csv'
rows=list(csv.DictReader(open(SRC)))
fields=list(rows[0].keys())
NEW=['round4_delta','employer_mail_domain','domain_unlock_status','email_alternate','mixed_format_domain']
for f in NEW:
    if f not in fields: fields.append(f)

# --- domain decisions, evidence-driven ---
EMIT={  # full_name -> (email, confidence, label, evidence, alt)
 'Kenneth Wenz':('kenneth.wenz@orthosc.org','pattern_likely','pattern_inferred',
   'orthosc.org observed first-party: ann.vennell@orthosc.org + miranda.amos@orthosc.org (first.last) via https://www.orthosc.com/contact/ and https://www.orthosc.com/careers/; COMPETING format mmccorkle@orthosc.org (flast, Melissa McCorkle) observed on same domain -> downgraded from pattern_confirmed to pattern_likely',
   'kwenz@orthosc.org'),
}
WITHHELD={
 'mcleodhealth.org':'WITHHELD_mixed_format+employment_contested',
 'hcahealthcare.com':'WITHHELD_contractor (hcaEmployee=false, round 2)',
 'novanthealth.org':'WITHHELD_pattern_underivable_from_2_samples',
}
MPA_TRUE={'Alisha F. Palliser','Joshua Gore'}   # McLeod directory mcLeod_physician_associates=true
MCLEOD_PEOPLE={'Ahmed Elhaimer','Alisha F. Palliser','David O. Atkinson','Daniela Smith','Edward Wallace',
 'Frederick Bellamy','Jonathan Ward','Joshua Gore','Kenneth Sinclair Houghton','Ligia E. Cisneros-Gonzalez',
 'Michael D. Wingfield','Michael James Warden','Michelle Lee','Morganne B Beard','Olga Chrisman',
 'Robert O’Connor',"Robert O'Connor",'Brandon Sloop'}

out=[]
for r in rows:
    for f in NEW: r.setdefault(f,'')
    n=r['full_name']
    r['round4_delta']=''
    if n in EMIT:
        e,conf,lab,ev,alt=EMIT[n]
        r['email']=e; r['email_confidence']=conf; r['email_label']=lab
        r['email_evidence_source']=ev; r['email_source']=ev
        r['email_alternate']=alt; r['mixed_format_domain']='true'
        r['employer_mail_domain']='orthosc.org'
        r['domain_unlock_status']='UNLOCKED_mixed_format (2 first.last : 1 flast observed)'
        r['round4_delta']='NEW EMAIL via domain-unlock hunt on orthosc.org'
    elif n in MCLEOD_PEOPLE:
        r['employer_mail_domain']='mcleodhealth.org'
        r['domain_unlock_status']=WITHHELD['mcleodhealth.org']
        mpa='mcLeod_physician_associates=true' if n in MPA_TRUE else 'mcLeod_physician_associates=false (contracted group)'
        r['round4_delta']=('EMAIL WITHHELD: mcleodhealth.org runs TWO live formats concurrently — '
          '3 name-confirmed first.last (Maureen.finger@, maggie.jackson@, logan.doriety@) vs 2 name-confirmed '
          'flast (rserrano@ Raquel Serrano, dsawyer@ Davis Sawyer) + 4 further flast-shaped (aploeg@, cpernell@, '
          'hburgin@, jcauble@); 9 personal addresses observed, ~67% flast. No propagable pattern. '
          'Employment also contested: '+mpa+' vs CMS PECOS employer_group. Checked 9 of 9 observed personal addresses.')
    elif (r.get('org_domain') or '')=='hcahealthcare.com' or 'mygrandstrandhealth' in (r.get('org_domain') or ''):
        r['employer_mail_domain']='hcahealthcare.com'
        r['domain_unlock_status']=WITHHELD['hcahealthcare.com']
        if not r.get('email'):
            r['round4_delta']=('EMAIL WITHHELD: Jon.Halling@hcahealthcare.com is first-party published (first.last) '
              'but Grand Strand anesthesia is contracted (TeamHealth; hcaEmployee=false, round 2). '
              'Directory payload re-checked this round: no email field, no employment flag exposed. Contractor -> different mail domain.')
    elif n=='William Myers':
        r['employer_mail_domain']='novanthealth.org (uncertain)'
        r['domain_unlock_status']=WITHHELD['novanthealth.org']
        r['round4_delta']=('EMAIL WITHHELD: novanthealth.org samples jsmoreb@ / mssaylor@ are compact/non-dotted; '
          '2 samples cannot distinguish f+m+last from f+last-truncated and no third sample was obtainable under the clamp. '
          'Employer also ambiguous (CHARLESTON CARENOW URGENT CARE LLC | NOVANT HEALTH URGENT CARES LLC).')
    elif n=='Joshua Gore':
        pass
    if n=='Joshua Gore':
        r['employer_mail_domain']='orthosc.org / mcleodhealth.org (conflict)'
        r['domain_unlock_status']='WITHHELD_employment_conflict'
        r['round4_delta']=('EMAIL WITHHELD: CMS PECOS employer_group=ORTHOSC LLC but McLeod directory sets '
          'mcLeod_physician_associates=true. Two first-party-grade sources name different employers -> employment unknown -> withhold.')
    if not r['round4_delta']:
        eg=(r.get('employer_group') or '').split('|')[0].strip()
        r['employer_mail_domain']=''
        r['domain_unlock_status']='NOT_UNLOCKED_domain_undiscoverable' if eg else 'NO_EMPLOYER_ON_RECORD'
        r['round4_delta']=('EMAIL WITHHELD: no address observed on '+(eg or 'any')+"'s mail domain; domain itself not "
          'discoverable under clamp A (no search engine available; DNS-probed candidate hostnames all NXDOMAIN or parked).') if eg else \
          'EMAIL WITHHELD: no employer of record, so no domain to unlock.'
    out.append(r)

with open('result.csv','w',newline='',encoding='utf-8') as fh:
    w=csv.DictWriter(fh,fieldnames=fields); w.writeheader()
    for r in out: w.writerow(r)
print("wrote result.csv rows=%d cols=%d emails=%d"%(len(out),len(fields),sum(1 for r in out if r.get('email'))))
