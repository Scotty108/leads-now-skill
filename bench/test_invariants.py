#!/usr/bin/env python3
"""Shared invariants both lead skills must satisfy. Run before any comparison.

These are not "does it find leads" tests — they are the properties that make a
result trustworthy. A skill that scores well on lead count while failing these
is worse than one that finds fewer, because the failures are silent.

Usage:
  python3 bench/test_invariants.py                 # both skills
  python3 bench/test_invariants.py --skill ours    # one
  python3 bench/test_invariants.py --json -o r.json

Exit 0 = all pass. Exit 1 = a failure. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SKILLS = {
    "ours": {
        "dir": os.path.join(ROOT, "skills", "leads-now"),
        "kit": os.path.join(ROOT, "skills", "leads-now", "scripts", "leadkit.py"),
        "emails": lambda kit, a: [sys.executable, kit, "emails"] + a,
    },
    "skillit": {
        "dir": os.path.join(ROOT, "skill-bakeoff", "finding-leads"),
        "kit": os.path.join(ROOT, "skill-bakeoff", "finding-leads",
                            "scripts", "email_pattern.py"),
        "emails": lambda kit, a: [sys.executable, kit] + a,
    },
}

# Spec-legal frontmatter for claude.ai upload. Anything else is a hard error
# there, so it is a portability failure, not a style note.
ALLOWED_FM = {"name", "description", "license", "compatibility",
              "metadata", "allowed-tools"}

results = []


def check(skill, name, passed, detail=""):
    results.append({"skill": skill, "check": name,
                    "status": "PASS" if passed else "FAIL", "detail": detail})
    print(f"  [{'PASS' if passed else 'FAIL'}] {name}"
          + (f" — {detail}" if detail else ""))
    return passed


def run(cmd, cwd=None):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=120,
                           cwd=cwd)
        return p.returncode, p.stdout + p.stderr
    except Exception as e:
        return -1, str(e)


def test_frontmatter(skill, cfg):
    path = os.path.join(cfg["dir"], "SKILL.md")
    if not os.path.exists(path):
        return check(skill, "SKILL.md exists", False, path)
    body = open(path).read()
    m = re.match(r"^---\n(.*?)\n---\n", body, re.S)
    if not m:
        return check(skill, "frontmatter parses", False)
    keys = [l.split(":")[0] for l in m.group(1).splitlines()
            if re.match(r"^[a-z-]+:", l)]
    bad = [k for k in keys if k not in ALLOWED_FM]
    ok = check(skill, "frontmatter is upload-legal", not bad,
               f"illegal: {bad}" if bad else f"{keys}")
    # Claude-Code-only dynamic context injection breaks on claude.ai / API.
    ok &= check(skill, "no Claude-Code-only body syntax",
                not re.search(r"!`", body))
    return ok


def test_portability(skill, cfg):
    """Scripts must be stdlib-only and must not reach the network themselves:
    the Claude apps sandbox has no outbound access, so a script that fetches is
    a script that silently fails there."""
    sdir = os.path.join(cfg["dir"], "scripts")
    if not os.path.isdir(sdir):
        return check(skill, "scripts/ exists", False)
    bad_imports, netcalls = [], []
    for fn in sorted(os.listdir(sdir)):
        if not fn.endswith(".py"):
            continue
        src = open(os.path.join(sdir, fn)).read()
        for mod in ("requests", "aiohttp", "httpx", "bs4", "lxml", "pandas",
                    "numpy", "dns"):
            if re.search(rf"^\s*(import|from)\s+{mod}\b", src, re.M):
                bad_imports.append(f"{fn}:{mod}")
        if re.search(r"urlopen\(|urlretrieve\(|socket\.(create_connection|socket)\(",
                     src):
            netcalls.append(fn)
    ok = check(skill, "no third-party imports", not bad_imports,
               ", ".join(bad_imports))
    ok &= check(skill, "scripts make no network calls", not netcalls,
                ", ".join(netcalls))
    return ok


def test_refusal(skill, cfg):
    """The load-bearing behaviour: with no evidence, emit no address."""
    kit = cfg["kit"]
    if not os.path.exists(kit):
        return check(skill, "email tool exists", False, kit)
    rc, out = run(cfg["emails"](kit, ["--domain", "acme.com",
                                      "--name", "Ann Lee"]))
    low = out.lower()
    emitted = bool(re.search(r"[a-z]+@acme\.com", low))
    ok = check(skill, "zero evidence -> emits no address", not emitted,
               "leaked an address" if emitted else "refused")

    # A personal address on another domain proves nothing about the org format.
    rc, out = run(cfg["emails"](kit, ["--domain", "acme.com",
                                      "--known", "Jane Doe:jane@gmail.com",
                                      "--name", "Ann Lee"]))
    leaked = bool(re.search(r"[a-z]+@acme\.com", out.lower()))
    ok &= check(skill, "off-domain sample is ignored", not leaked)
    return ok


def test_surname_particles(skill, cfg):
    """'van der Berg' has an ambiguous surname. Emitting one form at top
    confidence is a fabricated address wearing a certainty label."""
    kit = cfg["kit"]
    if not os.path.exists(kit):
        return check(skill, "email tool exists", False)
    rc, out = run(cfg["emails"](kit, [
        "--domain", "acme.com",
        "--known", "Jane Doe:jdoe@acme.com",
        "--known", "Bob Ray:bray@acme.com",
        "--name", "Kwame van der Berg"]))
    low = out.lower()
    # Truncating to the final token AND calling it confirmed is the failure.
    truncated = "kberg@acme.com" in low
    confirmed = "pattern_confirmed" in low or "confirmed" in low
    bad = truncated and confirmed
    return check(skill, "ambiguous surname not top-confidence", not bad,
                 "kberg@ at confirmed" if bad else "handled")


def test_docs_claims(skill, cfg):
    """Guard the two measured facts a skill must not contradict."""
    txt = ""
    for root, _, files in os.walk(cfg["dir"]):
        for f in files:
            if f.endswith(".md"):
                txt += open(os.path.join(root, f), errors="ignore").read()
    low = txt.lower()
    ok = check(skill, "warns about NPI pagination ceiling",
               "skip" in low and ("1000" in low or "ceiling" in low
                                  or "truncat" in low))
    ok &= check(skill, "warns to broaden narrow taxonomy",
                "parent" in low or "broaden" in low)
    return ok




# ---------------------------------------------------------------------------
# PORT TESTS — the cross-pollination frontier.
#
# Each of these encodes a mechanism one skill has and the other does not. They
# are written BEFORE the port and are expected to fail against the pre-port
# version; that failing run is the evidence the port was needed. Once ported,
# the test is what stops a later round from regressing it.
# ---------------------------------------------------------------------------

def _all_md(cfg):
    """All markdown in the skill, whitespace-normalised.

    Markdown hard-wraps prose, so a phrase like "necessary and not sufficient"
    can straddle a newline and fail a naive substring check. Collapsing
    whitespace tests the content rather than the line breaks.
    """
    txt = ""
    for root, _, files in os.walk(cfg["dir"]):
        for f in files:
            if f.endswith(".md"):
                txt += open(os.path.join(root, f), errors="ignore").read() + "\n"
    return re.sub(r"\s+", " ", txt.lower())


def port_surface_lanes(skill, cfg):
    """ours -> skillit. Capability differs per surface; a skill that assumes a
    shell silently fails in the Claude apps. Must name the degraded path."""
    t = _all_md(cfg)
    has = ("lane" in t or "surface" in t) and \
          ("no outbound" in t or "sandbox" in t or "claude apps" in t)
    return check(skill, "PORT: surface capability lanes", has)


def port_skillmd_fallback(skill, cfg):
    """ours -> skillit. Some install paths carry only SKILL.md and drop
    scripts/. Without an embedded fallback the skill is inert there."""
    body = open(os.path.join(cfg["dir"], "SKILL.md"), errors="ignore").read()
    has = "```python" in body and ("fallback" in body.lower()
                                   or "missing" in body.lower())
    return check(skill, "PORT: SKILL.md-only fallback embedded", has)


def port_qualify_branch(skill, cfg):
    """ours -> skillit. 'Past pediatric experience' is the origin ask and no
    directory field carries it; it needs a research branch over a shortlist."""
    t = _all_md(cfg)
    has = ("qualify" in t or "past experience" in t) and \
          ("openalex" in t or "affiliation history" in t or "publication" in t)
    return check(skill, "PORT: qualify branch for past experience", has)


def port_calibrated_email_tiers(skill, cfg):
    """skillit -> ours. Confidence labels without measured accuracy cannot be
    gated against a bounce ceiling; 'likely' is not a number."""
    t = _all_md(cfg)
    has = ("bounce" in t) and re.search(r"\b(36|68|91)\s*%", t) is not None
    return check(skill, "PORT: calibrated email accuracy + bounce gate", has)


def port_unsourced_row_gate(skill, cfg):
    """skillit -> ours. A rule in prose is not a gate. Something must refuse to
    emit a row whose claims carry no source."""
    sdir = os.path.join(cfg["dir"], "scripts")
    src = ""
    if os.path.isdir(sdir):
        for fn in os.listdir(sdir):
            if fn.endswith(".py"):
                src += open(os.path.join(sdir, fn), errors="ignore").read().lower()
    has = ("unsourced" in src or "no source" in src) and \
          ("exit(1)" in src or "return 1" in src or "sys.exit(1)" in src)
    return check(skill, "PORT: tool refuses unsourced rows", has)




def port_corresponding_author_emails(skill, cfg):
    """Both. Health systems publish almost no clinician addresses — 3 emails
    across 131 people in round 1. Academic papers DO publish corresponding-author
    addresses. The trap is name collision, so the query must be affiliation-
    locked; skillit correctly rejected 8 unlocked PubMed hits rather than use
    them, which is the right call and the reason to do it properly."""
    t = _all_md(cfg)
    has = (("corresponding author" in t or "corresponding-author" in t)
           and ("affiliation" in t)
           and ("openalex" in t or "pubmed" in t or "europepmc" in t))
    return check(skill, "PORT: affiliation-locked corresponding-author emails", has)


def port_linkedin_search_url(skill, cfg):
    """Both. 0 LinkedIn across 131 people. Automating LinkedIn is off the table
    (ToS, and the user's account carries the risk), but emitting a precise
    search URL for a human to click costs nothing and is genuinely useful."""
    t = _all_md(cfg)
    emits = ("linkedin.com/search" in t or "search url" in t
             or "search link" in t)
    refuses = ("never automate" in t or "do not automate" in t
               or "not scrape" in t or "never scrape" in t)
    return check(skill, "PORT: LinkedIn search URL, never scraped",
                 emits and refuses)


def port_phone_type(skill, cfg):
    """Both. Round 1 reported ~100% reachable on NPI phones, but every one is a
    practice switchboard. Calling that the same as a direct dial overstates the
    deliverable — the number must carry what KIND of number it is."""
    t = _all_md(cfg)
    has = ("switchboard" in t or "practice phone" in t or "phone_type" in t) \
        and ("direct dial" in t or "direct-dial" in t)
    return check(skill, "PORT: phone type distinguished (switchboard vs direct)",
                 has)




def port_subspecialty_not_in_registry(skill, cfg):
    """Both. THE round-1 finding. Querying the parent taxonomy is necessary and
    NOT sufficient: NPI carries no subspecialty code for many clinicians, so a
    registry-only answer to 'find pediatric anesthesiologists' returns a
    confident ZERO that is wrong. A real pediatric anesthesiologist was found
    25 miles out, published only on her hospital's own directory.

    Requires the explicit instruction, not incidental vocabulary — a registry
    zero must be stated as NOT the final answer.
    """
    t = _all_md(cfg)
    has = ("necessary" in t and "not sufficient" in t) and \
          ("subspecialt" in t) and \
          ("registry zero" in t or "zero is not" in t
           or "not the answer" in t or "not a final answer" in t)
    return check(skill, "PORT: subspecialty absent from NPI, check directories", has)


def port_literature_wrong_instrument(skill, cfg):
    """Both. Measured: 0 of 60 community anesthesiologists yielded a usable
    scholarly signal; 51 had no footprint at all. Sending a research pass at a
    community roster burns the budget for nothing — the signal lives in bios,
    fellowship pages and board certification."""
    t = _all_md(cfg)
    has = ("community" in t) and ("openalex" in t or "literature" in t) and \
          ("no scholarly" in t or "wrong instrument" in t
           or "academic" in t)
    return check(skill, "PORT: literature is wrong instrument for community rosters", has)




def port_openalex_is_metered(skill, cfg):
    """Both. CORRECTION. OpenAlex was documented as 'free, no key'. Measured:
    HTTP 429 'Insufficient budget ... you only have $0 remaining',
    retryAfter 6268s, 0 of 72 queries served even with a polite UA and mailto.
    Documenting a dead source as the primary path sends every future run down
    it.

    Scoped to the sentence around each OpenAlex mention — a 429 elsewhere in
    the docs (the anti-bot table) is not evidence this was corrected.
    """
    t = _all_md(cfg)
    if "openalex" not in t:
        return check(skill, "PORT: OpenAlex metering documented", True, "n/a")
    ok = False
    for m in re.finditer(r"openalex", t):
        window = t[max(0, m.start() - 200): m.start() + 300]
        if "metered" in window or "429" in window or "no longer free" in window:
            ok = True
            break
    return check(skill, "PORT: OpenAlex metering documented", ok)


def port_efetch_beats_europepmc(skill, cfg):
    """Both. Measured: Europe PMC fullTextXML 404'd on all 4 affiliation-locked
    PMIDs including the open-access one, while NCBI efetch db=pmc served every
    corresponding-author address. Both published emails came from efetch."""
    t = _all_md(cfg)
    has = "efetch" in t and ("db=pmc" in t or "pmc" in t)
    return check(skill, "PORT: NCBI efetch db=pmc for full-text emails", has)


def port_full_forename_disambiguation(skill, cfg):
    """Both. Affiliation lock alone is NOT sufficient. Measured: 'Patel D'
    publishing from Grand Strand Health, Myrtle Beach passed the affiliation
    lock perfectly and is Dveet Patel, not roster member Deeran Patel. Only a
    full-forename comparison caught it."""
    t = _all_md(cfg)
    has = ("forename" in t or "full first name" in t or "initial is not" in t) \
        and ("affiliation lock" in t or "affiliation-lock" in t)
    return check(skill, "PORT: full-forename check, initials collide", has)


def port_department_phones_absent(skill, cfg):
    """Both. FALSIFIED a claim I wrote. contact-channels.md predicted department
    numbers were 'the realistic win'. Measured: 8 org sites, ZERO anesthesiology
    department lines — they publish facility switchboards only. Keep the
    phone_type labels, drop the promise."""
    t = _all_md(cfg)
    has = ("switchboard" in t) and \
          ("no department" in t or "zero department" in t
           or "rarely publish" in t or "do not publish a department" in t)
    return check(skill, "PORT: department lines usually absent (measured)", has)




def port_rung3_yields_department_phones(skill, cfg):
    """Both. AMENDS my own round-1B correction. I wrote that department lines
    "mostly do not exist" after fetching 8 org pages and getting zero. Round 2
    proved that true for PAGE FETCHING and false for STRUCTURED PAYLOADS: the
    same orgs carry the anesthesia group's own line inside their directory
    records. Clamped runs pulled 16 and 12. Fetching the page is the wrong
    read; parsing the payload is the right one."""
    t = _all_md(cfg)
    # Must state the amendment, not merely mention departments and rung 3.
    has = ("department" in t) and \
          ("page fetch" in t or "fetching the page" in t) and \
          ("payload" in t or "structured record" in t)
    return check(skill, "PORT: department phones live in rung-3 payloads", has)


def port_search_index_pagination_trap(skill, cfg):
    """Both. A second silent-truncation class, same shape as NPI skip=1000.
    McLeod's Algolia index reports nbHits=805 but nbPages=1 at hitsPerPage=100
    (paginationLimitedTo), so a blind browse returns 100 of 805 and looks
    complete. Any hosted search index has this; check the count against what
    you actually received."""
    t = _all_md(cfg)
    # Requires the specific mechanism, not the words "search index" + "cap".
    has = ("nbhits" in t or "paginationlimitedto" in t) and \
          ("silently" in t or "looks complete" in t)
    return check(skill, "PORT: hosted search index pagination cap", has)


def port_employment_status_gate(skill, cfg):
    """Both. NEW MECHANISM, and the sharpest refusal yet. Three agreeing
    @hcahealthcare.com addresses would have made first.last pattern_confirmed
    for five more people — but the directory's own record set
    hcaEmployee=false: they are contractors. An org's email pattern applies to
    its EMPLOYEES, not to everyone who works in its building. Five plausible
    addresses were withheld on that basis."""
    t = _all_md(cfg)
    has = ("contractor" in t or "locum" in t or "employment status" in t
           or "hcaemployee" in t) and \
          ("pattern" in t) and ("withheld" in t or "do not apply" in t
                                or "does not apply" in t)
    return check(skill, "PORT: employment status gates pattern inference", has)




def port_one_hop_past_the_index(skill, cfg):
    """Both. THE round-2 breakthrough. A search index is a pointer, not the
    record. McLeod's Algolia entries carry no training fields at all — but every
    record's scheduling_url points at /physician/<slug>/, and THOSE pages
    publish Board Certification, Medical School, Residency and Fellowship to a
    plain curl. Round 1 read the index and reported 2 pediatric signals; round 2
    opened the profiles and found 79."""
    t = _all_md(cfg)
    # Requires the instruction itself, not incidental vocabulary.
    has = ("index is a pointer" in t or "one hop past" in t
           or "open the profile" in t)
    return check(skill, "PORT: open the profile, not just the index", has)


def port_silence_is_not_absence(skill, cfg):
    """Both. NONE_FOUND must be explained structurally or it is a lie by
    omission. Measured: Tidelands publishes NO training block for ANY of its 12
    anesthesiologists (it does for other specialties), Grand Strand publishes no
    board-certification row at all (0 of 299), Conway has no such field. Those
    NONE_FOUNDs mean the directory cannot show a fellowship, not that the person
    lacks one — which makes those 12 the HIGHEST-value calls, not the lowest."""
    t = _all_md(cfg)
    has = ("silence is not absence" in t or "silent record" in t) and \
          ("none_found" in t or "none found" in t)
    return check(skill, "PORT: directory silence is not absence of the trait", has)


def port_chrome_string_false_positives(skill, cfg):
    """Both. Page chrome matches like content. Measured: OrthoSC's navigation
    string 'Pediatric Orthopedic Care' graded ALL 33 of its providers pediatric
    until it was stripped, and 18 Conway 'children' hits were personal-life
    mentions in bios. Match inside the record, never across the whole page."""
    t = _all_md(cfg)
    has = ("page chrome" in t or "nav string" in t) and \
          ("match inside the record" in t or "strip" in t)
    return check(skill, "PORT: strip page chrome before matching", has)




def port_negative_needs_a_denominator(skill, cfg):
    """Both. THE META-LESSON, and it caught three of my own false claims.

    Round 2B read 262 of McLeod's 805 records and 443 Tidelands profiles, then
    stated three confident negatives. A fuller sweep (1,708 records) falsified
    all three: Tidelands publishes training for 11 of 12 anesthesiologists (not
    zero), Conway publishes board certification on 258 of 303 profiles (not
    'no such field'), and McLeod publishes 15 first-party clinician emails (not
    'zero across 1,342 pages').

    A negative finding is only as good as its coverage. Never write 'zero'
    without the denominator you searched."""
    t = _all_md(cfg)
    has = ("state the denominator" in t or "never write \'zero\'" in t
           or "no denominator" in t)
    return check(skill, "PORT: state the denominator with every negative", has)


def port_recursive_truncation(skill, cfg):
    """Both. The documented fix for a truncation cap can itself be truncated.
    Partitioning McLeod's index by specialty returned 785 of 805 because two
    facets (Family Medicine 161, Primary Care 132) each silently capped at 100.
    Only a gender + a-z sweep reached 805/805. Verify the partition sums to the
    reported total; do not assume a partition escapes the cap."""
    t = _all_md(cfg)
    has = ("partition can itself" in t or "recursively truncat" in t
           or "partitions truncate too" in t)
    return check(skill, "PORT: partitions can truncate recursively", has)


def port_payload_schema_variance(skill, cfg):
    """Both. Grand Strand's embedded payload yielded ZERO pediatric signals
    until it was keyed on providerSpecialties/providerLocations rather than
    specialties/practiceLocations. Reading the wrong key returns an empty
    result that is indistinguishable from a genuine absence."""
    t = _all_md(cfg)
    has = ("key" in t) and \
          ("schema" in t or "field name" in t) and \
          ("empty" in t or "zero" in t or "silently" in t)
    return check(skill, "PORT: verify payload keys before trusting a zero", has)




def port_aba_diplomate_directory(skill, cfg):
    """Both. The best source found in the benchmark, and the only one that
    fills a training block no hospital directory will publish. The American
    Board of Anesthesiology runs an open, un-captcha'd JSON API — reached by
    climbing into the React bundle's main.js. ProgramType 519 IS Pediatric
    Anesthesiology, the exact subspecialty field rounds 1-2 could not reach.
    Filled 46 certification blocks including a Tidelands anesthesiologist
    sourced entirely from outside Tidelands, which still 403s."""
    t = _all_md(cfg)
    has = ("american board of anesthesiology" in t or "theaba.org" in t) and \
          ("certif" in t)
    return check(skill, "PORT: ABA diplomate directory for board certification", has)


def port_directory_address_is_not_practice(skill, cfg):
    """Both. The sharpest rejection of round 3. A certifying body publishes the
    diplomate's MAILING address, not a practice location. Two brand-new,
    entirely plausible pediatric anesthesiologists appeared 1.5 miles from the
    ring centre; NPI and Doximity independently placed them in Tucson AZ and
    Macon GA. Both withheld. An address field is only a practice location if
    the source says it is."""
    t = _all_md(cfg)
    has = ("mailing address" in t) and \
          ("practice location" in t or "practice address" in t)
    return check(skill, "PORT: a mailing address is not a practice location", has)


def port_structurally_closed_sources(skill, cfg):
    """Both. Three classes are closed by structure, not difficulty, so a browser
    does not rescue them: state medical boards are reCAPTCHA-gated (and the
    skill refuses to defeat a CAPTCHA, so the zero survives into the OPEN
    condition), ASA and SPA publish no member directory at all, and
    residency/fellowship pages are circular for discovery — they are indexed BY
    PROGRAM, which is the field you are trying to fill. Do not re-spend on
    these."""
    t = _all_md(cfg)
    has = ("structurally closed" in t or "closed by structure" in t) and \
          ("circular" in t or "recaptcha" in t)
    return check(skill, "PORT: name the structurally closed sources", has)




def port_cms_doctors_and_clinicians(skill, cfg):
    """Both. The single highest-yield source in the whole benchmark, and it was
    on nobody's list. The CMS Doctors and Clinicians National Downloadable File
    (mj5m-pzi6, 3.39M rows, no key) is Medicare PECOS enrollment — an official
    filing carrying med_sch, grd_yr, pri_spec, sec_spec_1..4, facility_name and
    a practice phone for every enrolled clinician.

    One geography query added 52 net-new in-ring providers, filled 99 training
    blocks from zero, and named all 12 Tidelands anesthesiologists WITH medical
    school and graduation year — the cohort a 403 had hidden for three rounds."""
    t = _all_md(cfg)
    has = ("mj5m-pzi6" in t or "doctors and clinicians" in t) and \
          ("pecos" in t or "med_sch" in t or "downloadable file" in t)
    return check(skill, "PORT: CMS Doctors & Clinicians national file", has)


def port_positive_control_for_absence(skill, cfg):
    """Both. How to prove a field is empty rather than unread. Healthgrades was
    declared checked-and-absent for 12 people only after a CONTROL profile
    (dr-edward-gologorsky-2fywb) returned a 1994 UPMC FELLOW row — proving the
    field exists, renders, and is genuinely empty for the twelve.

    Without a positive control, 'the field was blank' and 'I parsed it wrong'
    are indistinguishable — which is exactly how round 2B produced three false
    negatives."""
    t = _all_md(cfg)
    has = ("control" in t) and \
          ("field exists" in t or "proves the field" in t
           or "renders" in t) and \
          ("absent" in t or "empty" in t)
    return check(skill, "PORT: prove absence with a positive control", has)




def port_verify_location_against_practice_address(skill, cfg):
    """Both. Two runs made OPPOSITE errors on the same two people, and I had to
    check the registry myself to settle it.

    Desiree Aird MD: one run asserted NPI placed her in Tucson AZ; another
    counted her inside the Myrtle Beach ring. The NPI PRACTICE address is
    Greenville SC — neither was right. John Gantomasso: one said Macon GA,
    another counted him in-ring; his practice addresses are New Orleans and
    Lafayette LOUISIANA.

    A location claim is only settled by the authoritative registry's PRACTICE
    address. Not a mailing address, not a certifying body's address, and never
    another run's assertion."""
    t = _all_md(cfg)
    has = ("settle" in t or "adjudicat" in t) and \
          ("practice address" in t) and ("another run" in t or "assertion" in t)
    return check(skill, "PORT: settle location on the registry practice address", has)


def port_search_every_named_territory(skill, cfg):
    """Both. A SCOPE error that survived three rounds and twelve runs. The brief
    said 'map them to Myrtle Beach or Greenville'. Every run enumerated only the
    Myrtle Beach ring, then reported '0 -> Greenville' — a zero produced by
    never searching. A verified Greenville pediatric anesthesiologist exists.

    If the ask names two places, enumerate both. A territory you did not search
    returns zero and looks identical to a territory with nobody in it."""
    t = _all_md(cfg)
    has = ("territor" in t) and \
          ("enumerate both" in t or "never searched" in t
           or "each named" in t)
    return check(skill, "PORT: enumerate every territory the ask names", has)




def port_academic_vs_community_ceiling(skill, cfg):
    """Both. OVERTURNS the benchmark's headline conclusion. Four rounds
    concluded 'work email tops out near 4% — phone is the deliverable'. That was
    true of a COMMUNITY roster and false as a general claim.

    Same specialty, same state, 50-mile ring around an academic centre:
    78 first-party published emails vs 4, and 25 evidenced pediatric
    anesthesiologists vs 1. The ceiling was a property of the POPULATION, not
    of clinical data — and it broke through a medical-school faculty directory,
    not the literature."""
    t = _all_md(cfg)
    has = ("academic" in t and "community" in t) and \
          ("faculty directory" in t) and \
          ("ceiling" in t)
    return check(skill, "PORT: academic vs community changes the email ceiling", has)


def port_registry_addresses_go_stale(skill, cfg):
    """Both. The inverse of the mailing-address trap, and it needs BOTH sources.
    Sara Lathem Walls MD is ABA peds-certified and practises at Prisma
    Greenville, but her NPPES LOCATION still reads Nashville TN on a record
    untouched since 2018 — so the registry puts her OUTSIDE the ring, her
    in-ring NPPES address is mailing-only, and the hospital directory omits her
    from pediatrics entirely. She was found ONLY via current CMS Medicare
    enrollment and qualified ONLY by the certifying body.

    A registry practice address is authoritative but not fresh. Cross-check it
    against a current filing before excluding anyone."""
    t = _all_md(cfg)
    has = ("stale" in t) and ("enrollment" in t or "cms" in t) and \
          ("exclud" in t or "outside the ring" in t)
    return check(skill, "PORT: registry addresses go stale; check enrollment", has)


def port_empty_string_vs_null_filters(skill, cfg):
    """Both. A second silent wrong-key zero, one level past the GUID trap. With
    the CORRECT state GUID the ABA advanced search still returned [] at HTTP
    200, because the API treats an empty string as a LITERAL filter value. The
    client ships JSON null; with nulls the identical query returned 860.

    An empty filter and an absent filter are different queries. Read what the
    real client sends before trusting a zero."""
    t = _all_md(cfg)
    has = ("empty string" in t) and ("null" in t) and \
          ("literal" in t or "filter" in t)
    return check(skill, "PORT: empty string is not an absent filter", has)




def port_domain_unlock_hunt(skill, cfg):
    """Both. The one strategy a rival run genuinely beat us on. It produced ~22
    emails to our 4 by propagating an org pattern across everyone at that
    employer. We had the propagation logic all along and never spent the fetches
    to UNLOCK a domain — one published address is all it takes.

    Budget 3-5 targeted fetches per employer domain (contact, press, staff bios,
    PDFs, job postings) hunting for a single real address. But keep both guards:
    the rival got ~12 of its 22 wrong because it guessed the FORMAT instead of
    observing it (flast at a first.last domain, dotted at a compact domain), and
    emitted employer addresses for contractors its own notes said were employed
    elsewhere."""
    t = _all_md(cfg)
    has = ("unlock" in t) and ("one published address" in t
                               or "one real address" in t) and \
          ("per domain" in t or "per employer" in t)
    return check(skill, "PORT: hunt one address to unlock each domain", has)




def port_mixed_format_domains(skill, cfg):
    """Both. Round 4, and it corrects an analysis I gave the user.

    I told them a rival's flast@mcleodhealth.org addresses were WRONG, on the
    strength of ONE observed address (logan.doriety@). A complete sweep found 9
    personal addresses: 3 name-confirmed first.last AND 2 name-confirmed flast,
    with flast the ~6-of-9 majority. The rival's shape was the MAJORITY and
    still unsafe — because the domain runs BOTH.

    No propagation from a mixed domain beats ~2/3 accuracy, which is far under
    any usable bounce ceiling. Detect the mix, downgrade, and emit nothing."""
    t = _all_md(cfg)
    has = ("mixed" in t or "two formats" in t) and \
          ("same domain" in t or "concurrently" in t or "at once" in t) and \
          ("propagat" in t)
    return check(skill, "PORT: a domain can run two email formats at once", has)




def port_hospital_anesthesia_is_contracted(skill, cfg):
    """Both. THE structural finding, and it is why the email ceiling exists.

    Contracting is not an edge case in this vertical — it is the whole shape.
    CMS PECOS facility_name, queried by street address, proved all four hospital
    employers contract anesthesia to four DIFFERENT groups: Grand Strand ->
    Atlantic Coast Anesthesia Services PC (71 of 71 billing there), Conway ->
    MedStream Anesthesia PLLC, Columbus Regional -> Southeast Anesthesiology
    Consultants PLLC, Novant -> Providence Anesthesiology Associates PA.

    56 addresses were harvested and 3 patterns confirmed, and ZERO were applied.
    The contractor domains have no A record and no MX at all. Determine WHO
    BILLS before propagating any employer pattern."""
    t = _all_md(cfg)
    has = ("71 of 71" in t) or ("zero were applied" in t
                                 and "who bills" in t)
    return check(skill, "PORT: hospital anesthesia is contracted — check who bills", has)


def port_listing_is_not_employment(skill, cfg):
    """Both. A website directory listing a physician is NOT evidence they are
    employed there. A careful sub-hunt built a strong directory-based case that
    three physicians were the hospital's own; CMS enrollment overrode it — and
    one of them turned out to be delisted from that hospital entirely.

    An employer claim needs a filing, not a page."""
    t = _all_md(cfg)
    has = ("listing" in t or "listed" in t) and ("not employment" in t
                                                 or "is not proof of employ" in t)
    return check(skill, "PORT: a directory listing is not employment", has)


PORT_TESTS = [port_hospital_anesthesia_is_contracted,
              port_listing_is_not_employment,
              port_mixed_format_domains,
              port_domain_unlock_hunt,
              port_academic_vs_community_ceiling,
              port_registry_addresses_go_stale,
              port_empty_string_vs_null_filters,
              port_verify_location_against_practice_address,
              port_search_every_named_territory,
              port_cms_doctors_and_clinicians,
              port_positive_control_for_absence,
              port_aba_diplomate_directory,
              port_directory_address_is_not_practice,
              port_structurally_closed_sources,
              port_negative_needs_a_denominator,
              port_recursive_truncation,
              port_payload_schema_variance,
              port_one_hop_past_the_index,
              port_silence_is_not_absence,
              port_chrome_string_false_positives,
              port_rung3_yields_department_phones,
              port_search_index_pagination_trap,
              port_employment_status_gate,
              port_openalex_is_metered,
              port_efetch_beats_europepmc,
              port_full_forename_disambiguation,
              port_department_phones_absent,
              port_subspecialty_not_in_registry,
              port_literature_wrong_instrument,
              port_surface_lanes, port_skillmd_fallback, port_qualify_branch,
              port_calibrated_email_tiers, port_unsourced_row_gate,
              port_corresponding_author_emails, port_linkedin_search_url,
              port_phone_type]




# --- universality: the skill must not silt up with one vertical -------------

VERTICAL_TERMS = ["npi", "anesthesiolog", "pediatric", "clinician", "physician",
                  "pecos", "medicare", "myrtle", "greenville", "mcleod",
                  "tidelands", "grand strand", "conway", "hospital"]


def test_core_files_stay_general(skill, cfg):
    """The skill answers 'find me people like X near Y' for ANY vertical. Four
    rounds benchmarked against one anesthesiology roster is exactly how a
    general skill silts up into a specialist one — every finding was true, and
    every finding was clinical.

    Vertical specifics belong in a file that loads only when it matches. The
    always-read files must stay transferable, or a recruiter sourcing RevOps
    leads gets hundreds of lines about Medicare enrollment.
    """
    GENERAL_TERMS = ["b2b", "saas", "company", "employer", "org ", "domain",
                     "recruiter", "industry", "sector", "vertical", "candidate",
                     "prospect", "team page", "press release"]
    bad = []
    for name in ("SKILL.md", "references/contact-channels.md",
                 "references/discover.md", "references/qualify.md",
                 "references/enrich.md", "references/verify.md"):
        path = os.path.join(cfg["dir"], name)
        if not os.path.exists(path):
            continue
        t = open(path, errors="ignore").read().lower()
        vert = sum(t.count(k) for k in VERTICAL_TERMS)
        gen = sum(t.count(k) for k in GENERAL_TERMS)
        # A core file may ILLUSTRATE with a vertical; it may not be ABOUT one.
        # More vertical vocabulary than general vocabulary means it has tipped.
        if vert > max(gen, 1) * 1.5:
            bad.append(f"{name} {vert}v/{gen}g")
    return check(skill, "core files stay vertical-neutral", not bad,
                 "; ".join(bad))


def test_vertical_pack_exists(skill, cfg):
    """Vertical specifics must live somewhere loadable, not be deleted. The
    NPI/CMS/ABA findings are the most valuable thing the benchmark produced —
    they just must not sit in the always-read path."""
    import glob as _g
    packs = _g.glob(os.path.join(cfg["dir"], "references", "vertical-*.md"))
    return check(skill, "vertical pack exists", bool(packs),
                 os.path.basename(packs[0]) if packs else "none")


def test_router_loads_vertical_pack(skill, cfg):
    """A pack nothing routes to is a deleted pack.

    Moving the clinical detail out of the always-read path only works if the
    router puts it back when the population matches. The first version of this
    refactor left `vertical-healthcare.md` on disk with ZERO references from
    SKILL.md — the specifics were not decluttered, they were orphaned.
    """
    body = open(os.path.join(cfg["dir"], "SKILL.md"), errors="ignore").read().lower()
    routes = "vertical-" in body
    return check(skill, "router loads the matching vertical pack", routes,
                 "SKILL.md never names a vertical-*.md pack" if not routes else "")


def test_population_class_method(skill, cfg):
    """Universality is a METHOD for an unseen population, not a longer list.

    Listing healthcare and B2B sources makes a two-vertical skill. What makes it
    general is a procedure that answers "where does a roster of THESE people
    live?" for commercial roofers, school superintendents or insurance
    producers — populations nobody wrote a section for.

    The discriminator is structural: whether the population is enumerable at all
    (a mandatory register, a public-payroll disclosure, an entity filing) or
    only samplable (privately employed, no register). That single question
    decides the whole plan, so the skill has to ask it explicitly.
    """
    t = _all_md(cfg)
    has_classes = sum(k in t for k in
                      ("licensed", "register", "public payroll", "public employ",
                       "entity filing", "secretary of state", "credential",
                       "association")) >= 4
    has_verdict = ("enumerab" in t or "enumerate the population" in t) and \
                  ("samplab" in t or "sample" in t)
    has_derivation = "license lookup" in t or "license verification" in t
    ok = has_classes and has_verdict and has_derivation
    return check(skill, "derives sources for an unseen population", ok,
                 f"classes={has_classes} verdict={has_verdict} derive={has_derivation}")


def test_bands_are_computable(skill, cfg):
    """Banding must be a computation, not a paragraph asking Claude to be tidy.

    Prose alone regressed twice in this loop. The distances have to come out of
    a deterministic helper, and the location fields have to SURVIVE the merge —
    the first cut of this dropped city/state/postal_code at merge, so the
    banding step silently had nothing to measure and emitted an empty column,
    which reads as "nobody has a distance" rather than as a broken pipeline.
    """
    script = os.path.join(cfg["dir"], "scripts", "leadkit.py")
    if not os.path.exists(script):
        return check(skill, "distance banding is computed", True, "no leadkit")
    src = open(script, errors="ignore").read()
    if "def cmd_bands" not in src:
        return check(skill, "distance banding is computed", False,
                     "no bands subcommand")

    import subprocess, tempfile, json as _j
    recs = [{"full_name": "Near Person", "city": "MYRTLE BEACH", "state": "SC",
             "source": "test"},
            {"full_name": "Far Person", "city": "CHARLESTON", "state": "SC",
             "source": "test"},
            {"full_name": "Unplaced Person", "source": "test"}]
    with tempfile.TemporaryDirectory() as td:
        src_p = os.path.join(td, "r.json")
        _j.dump(recs, open(src_p, "w"))
        # Both orders must work: merge->bands and bands->merge.
        outs = []
        for order in (("merge", "bands"), ("bands", "merge")):
            cur, ok = src_p, True
            for step in order:
                nxt = os.path.join(td, f"{step}_{order[0]}.json")
                cmd = [sys.executable, script, step, cur, "-o", nxt]
                if step == "bands":
                    cmd += ["--place", "Myrtle Beach", "--state", "SC",
                            "--radius", "50"]
                p = subprocess.run(cmd, capture_output=True, text=True)
                if p.returncode != 0:
                    ok = False
                    break
                cur = nxt
            outs.append(_j.load(open(cur)) if ok else None)

    bad = []
    for order, rows in zip(("merge->bands", "bands->merge"), outs):
        if rows is None:
            bad.append(f"{order} failed")
            continue
        by = {r.get("full_name"): r for r in rows}
        near, far = by.get("Near Person"), by.get("Far Person")
        if not near or near.get("dist_mi") is None:
            bad.append(f"{order}: near person lost its distance")
        elif not far or far.get("dist_mi") is None:
            bad.append(f"{order}: far person lost its distance")
        elif not (near["dist_mi"] < far["dist_mi"]):
            bad.append(f"{order}: {near['dist_mi']} !< {far['dist_mi']}")
        unp = by.get("Unplaced Person")
        # An unplaceable row must stay null, never default to 0 — a 0 would sort
        # it to the top and read as the closest lead in the territory.
        if unp and unp.get("dist_mi") is not None:
            bad.append(f"{order}: unplaced row got dist {unp['dist_mi']}")
    return check(skill, "distance banding is computed", not bad, "; ".join(bad))


def test_city_name_variants_place(skill, cfg):
    """Directories write city names the way a human typed them.

    Measured on a real 786-row roster: 17 distinct cities failed to place, and
    almost none were missing from the gazetteer — they were spelling variants.
    "MT PLEASANT" vs Mount Pleasant, "N CHARLESTON" vs North Charleston,
    "WINSTON SALEM" vs Winston-Salem, "PORT ST LUCIE" vs Port Saint Lucie.

    Each miss silently demotes a row to a coarse postal-prefix centroid with a
    ~38 mile median extent. At a 50-mile ring that is tolerable noise; at the
    15-mile ring a real territory actually uses, it is the whole answer.
    """
    VARIANT_PLACES = ["Mt Pleasant, SC", "N Charleston, SC",
                      "Winston Salem, NC", "St Petersburg, FL"]

    # Every skill must at minimum resolve a variant CENTER. Failing that is a
    # hard stop on the first step of the run: "within 15 miles of Mt Pleasant"
    # errors out before any sourcing happens.
    geo = os.path.join(cfg["dir"], "scripts", "geo_filter.py")
    if os.path.exists(geo):
        broke = []
        for p in VARIANT_PLACES:
            rc, out = run([sys.executable, geo, "resolve", p, "--radius", "15"])
            if rc != 0 or "not found" in out.lower():
                broke.append(p)
        return check(skill, "city name variants place precisely", not broke,
                     "; ".join(broke))

    script = os.path.join(cfg["dir"], "scripts", "leadkit.py")
    if not os.path.exists(script):
        return check(skill, "city name variants place precisely", True, "n/a")
    import importlib.util
    spec = importlib.util.spec_from_file_location("_lk_v", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "_locate"):
        return check(skill, "city name variants place precisely", False, "no _locate")
    z3, places, _z5 = mod._load_geo()
    if z3 is None:
        return check(skill, "city name variants place precisely", False, "no gazetteer")

    VARIANTS = [("MT PLEASANT", "SC"), ("N CHARLESTON", "SC"),
                ("WINSTON SALEM", "NC"), ("PORT ST LUCIE", "FL"),
                ("W COLUMBIA", "SC"), ("ST PETERSBURG", "FL")]
    bad = []
    for city, st in VARIANTS:
        _, _, basis = mod._locate({"city": city, "state": st}, places, z3)
        if basis != "city_centroid":
            bad.append(f"{city},{st}->{basis}")
    return check(skill, "city name variants place precisely", not bad,
                 "; ".join(bad))


def test_merge_without_org_uses_location(skill, cfg):
    """Two people with the same name and no employer must not become one.

    The merge key is name + org. That is safe for org-sourced records and
    silently wrong for a REGISTER, which is the highest-value source there is
    and almost never carries an employer. With org absent the key degenerates
    to the name alone.

    Measured on 11,087 Florida roofing licensees: 107 distinct people collapsed
    — different cities, different licence numbers, merged into one blended row
    carrying one person's address and another's licence. That is a fabricated
    record, which is the single thing this skill exists to prevent.

    The same key must also survive a city spelling variant: PORT ST LUCIE and
    PORT SAINT LUCIE at the same postcode are one person, not two.
    """
    script = os.path.join(cfg["dir"], "scripts", "leadkit.py")
    if not os.path.exists(script):
        return check(skill, "merge without org keys on location", True, "n/a")
    import tempfile, json as _j
    recs = [
        # Same name, no org, DIFFERENT places -> two people.
        {"full_name": "David Lee Carr", "city": "ST. AUGUSTINE",
         "state": "FL", "postal_code": "32092", "source": "reg"},
        {"full_name": "David Lee Carr", "city": "BROOKSVILLE",
         "state": "FL", "postal_code": "34601", "source": "reg"},
        # Same name, no org, same postcode, spelling variant -> one person.
        {"full_name": "Andrew Allocco", "city": "PORT ST LUCIE",
         "state": "FL", "postal_code": "34986", "source": "reg"},
        {"full_name": "Andrew Allocco", "city": "PORT SAINT LUCIE",
         "state": "FL", "postal_code": "34986", "source": "reg2"},
    ]
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "r.json")
        out = os.path.join(td, "m.json")
        _j.dump(recs, open(src, "w"))
        rc, _ = run([sys.executable, script, "merge", src, "-o", out])
        if rc != 0:
            return check(skill, "merge without org keys on location", False, "merge failed")
        merged = _j.load(open(out))
    carr = [m for m in merged if (m.get("full_name") or "").lower() == "david lee carr"]
    allo = [m for m in merged if "allocco" in (m.get("full_name") or "").lower()]
    bad = []
    if len(carr) != 2:
        bad.append(f"distinct-city same name collapsed to {len(carr)}, want 2")
    if len(allo) != 1:
        bad.append(f"city variant split into {len(allo)}, want 1")
    return check(skill, "merge without org keys on location", not bad,
                 "; ".join(bad))


def test_surname_first_names_flip(skill, cfg):
    """Registers publish ONE combined name field, surname first.

    Only org-sourced records hand you first and last separately. Flipping
    "AMBROSE, DEREK GABRIEL II" naively strands the suffix mid-name — a real
    run emitted "Derek Gabriel Ii Ambrose" and "James F Sr Carlevatti", which
    is what the user reads off the CSV. The suffix also sits on either side of
    the comma in the same file.
    """
    script = os.path.join(cfg["dir"], "scripts", "leadkit.py")
    if not os.path.exists(script):
        return check(skill, "surname-first names flip cleanly", True, "n/a")
    import importlib.util
    spec = importlib.util.spec_from_file_location("_lk_n", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "flip_name"):
        return check(skill, "surname-first names flip cleanly", False, "no flip_name")
    CASES = [("AMBROSE, DEREK GABRIEL II", "Derek Gabriel Ambrose, II"),
             ("CARLEVATTI, JAMES F SR", "James F Carlevatti, Sr"),
             ("ALLOCCO JR, ANDREW", "Andrew Allocco, Jr"),
             ("CARR, DAVID LEE", "David Lee Carr"),
             ("Jane Doe", "Jane Doe")]          # already forename-first
    bad = [f"{i!r}->{mod.flip_name(i)!r} want {w!r}"
           for i, w in CASES if mod.flip_name(i) != w]
    return check(skill, "surname-first names flip cleanly", not bad, "; ".join(bad))


def test_second_phone_from_mailing_address(skill, cfg):
    """A registry record can carry TWO phones. Keep both, and label them.

    NPI publishes a LOCATION address and a MAILING address, each with its own
    telephone. Ingest read only LOCATION, so the second number was discarded on
    every run. Measured on 70 real providers: the mailing phone DIFFERS from the
    practice phone 43% of the time, and is switchboard-shaped (ends 00/000) in
    only 3% of cases versus 17% for the practice line — i.e. it is ~6x less
    likely to be a front desk.

    It must NOT be labelled `direct`: a mailing phone may be a home office, a
    billing service, an answering service or an old practice. It is a second,
    distinct, non-switchboard number, and the honest label is its own.
    """
    script = os.path.join(cfg["dir"], "scripts", "leadkit.py")
    if not os.path.exists(script):
        return check(skill, "keeps the mailing-address second phone", True, "n/a")
    import tempfile, json as _j
    payload = {"results": [{
        "number": "1234567890",
        "basic": {"first_name": "Ann", "last_name": "Lee", "credential": "MD"},
        "taxonomies": [{"desc": "Anesthesiology", "code": "207L00000X", "primary": True}],
        "addresses": [
            {"address_purpose": "LOCATION", "city": "MYRTLE BEACH", "state": "SC",
             "postal_code": "29572", "telephone_number": "843-692-1000"},
            {"address_purpose": "MAILING", "city": "HOPE MILLS", "state": "NC",
             "postal_code": "28348", "telephone_number": "910-309-8067"},
        ]}]}
    with tempfile.TemporaryDirectory() as td:
        indir = os.path.join(td, "in")
        os.makedirs(indir)
        out = os.path.join(td, "recs.json")
        _j.dump(payload, open(os.path.join(indir, "npi.json"), "w"))
        rc, txt = run([sys.executable, script, "ingest", indir, "-o", out])
        if rc not in (0, 3, 4) or not os.path.exists(out):
            return check(skill, "keeps the mailing-address second phone", False,
                         f"ingest rc={rc}")
        recs = _j.load(open(out))
    if not recs:
        return check(skill, "keeps the mailing-address second phone", False, "no records")
    r = recs[0]
    blob = _j.dumps(r).lower()
    bad = []
    if "910-309-8067" not in blob:
        bad.append("mailing phone discarded")
    if "843-692-1000" not in blob:
        bad.append("practice phone lost")
    # Must not overclaim: the second number is not a proven direct dial.
    if r.get("phone_alt_type") == "direct" or r.get("phone_type") == "direct":
        bad.append("labelled 'direct' without evidence")
    return check(skill, "keeps the mailing-address second phone", not bad,
                 "; ".join(bad))


def test_search_name_differs_from_registry_name(skill, cfg):
    """Search the name a person USES, not the name a register filed.

    Registers carry full legal names. Searching one verbatim returns zero and
    looks exactly like the person having no profile. Measured live:
    `"Alexandra Anatolievna Armstrong"` -> 0 results;
    `"Alexandra Armstrong"` -> 16. The middle name was the bug, and a positive
    control was the only thing that told absence from a bad query.
    """
    script = os.path.join(cfg["dir"], "scripts", "leadkit.py")
    if not os.path.exists(script):
        return check(skill, "searches the used name, not the filed name", True, "n/a")
    import importlib.util
    spec = importlib.util.spec_from_file_location("_lk_s", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "search_name"):
        return check(skill, "searches the used name, not the filed name", False,
                     "no search_name")
    CASES = [("Alexandra Anatolievna Armstrong", "alexandra armstrong"),
             ("Andrew Lee Criser", "andrew criser"),
             ("Sarah Kim, MD", "sarah kim"),
             ("Dr. Ann Lee", "ann lee")]
    bad = [f"{i!r}->{mod.search_name(i)!r} want {w!r}"
           for i, w in CASES if mod.search_name(i).lower() != w]
    return check(skill, "searches the used name, not the filed name", not bad,
                 "; ".join(bad))


def test_profile_match_needs_corroboration(skill, cfg):
    """A name match alone is a namesake, not a person.

    Live test on our own roster: `Ahmed Elhaimer` resolved to a profile at
    MedStar St. Mary's when the record said McLeod Health, and
    `Alexander Varzari` to one in Charlottesville when the record said NC. Both
    scored top marks on name-in-title plus name-in-slug — an unrelated person
    wearing every signal a name-only scorer checks.

    Accepting requires employer OR geography to corroborate. This mirrors the
    rule the skill already holds for records: the full forename must match and
    a near-miss that survives every other check is the dangerous one.
    """
    t = _all_md(cfg)
    has_rule = ("namesake" in t or "same name" in t or "name alone" in t)
    needs_corr = (("corrobor" in t or "employer" in t) and
                  ("snippet" in t or "profile" in t))
    never_auto = ("never automate linkedin" in t or "do not automate linkedin" in t)
    ok = has_rule and needs_corr and never_auto
    return check(skill, "profile match needs corroboration", ok,
                 f"rule={has_rule} corr={needs_corr} noauto={never_auto}")


def test_bulk_data_traps(skill, cfg):
    """Two ways a bulk dataset lies about what it contains. Both measured.

    1. A SAMPLE ROW IS NOT THE SCHEMA. Querying the federal carrier census with
       `$limit=1` returns 34 fields and `cell_phone` is not among them —
       yet `$select=cell_phone` returns 1,874,212 populated values. Reading one
       row and concluding "no phone column" is wrong on the single highest-value
       free phone source in the country.

    2. NOT NULL IS NOT POPULATED. An Illinois licence file reports 1,522 rows
       where `home_phone IS NOT NULL`, and 77 once you exclude the literal
       string 'NA'. 95% of the column is a sentinel wearing data's clothes.

    Both generalise: enumerate columns from the metadata, and test the value
    against sentinels before counting it as coverage.
    """
    t = _all_md(cfg)
    schema = ("sample row" in t or "naive query" in t or "hidden column" in t
              or "not the schema" in t)
    sentinel = "sentinel" in t or "'na'" in t or '"na"' in t
    return check(skill, "knows the bulk-data traps", schema and sentinel,
                 f"schema={schema} sentinel={sentinel}")


def test_postcode_places_precisely(skill, cfg):
    """A postcode must place to ZIP5 precision, not a 3-digit prefix.

    City matching covers ~96% of a real roster. The remainder are places the
    Census does not incorporate — military installations, boroughs, CDPs — and
    those fell back to a 3-digit prefix centroid with a ~38 mile median extent.
    That is noise at a 15-mile ring, which is the ring a real territory used.

    Measured: all 30 rows our city matcher could not place have a ZIP5 in the
    gazetteer. Precision goes 96% -> 100% for the cost of a larger asset.
    """
    script = os.path.join(cfg["dir"], "scripts", "leadkit.py")
    if not os.path.exists(script):
        return check(skill, "postcode places to ZIP5 precision", True, "n/a")
    import importlib.util
    spec = importlib.util.spec_from_file_location("_lk_z", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    z, places, z5 = mod._load_geo()
    if z is None:
        return check(skill, "postcode places to ZIP5 precision", False, "no gazetteer")
    # Fort Bragg is not an incorporated place; only its postcode can place it.
    _, _, basis = mod._locate({"city": "FORT BRAGG", "state": "NC",
                               "postal_code": "28310"}, places, z, z5)
    ok = basis == "zip5_centroid"
    return check(skill, "postcode places to ZIP5 precision", ok, f"basis={basis}")


def test_distance_bands(skill, cfg):
    """Report by distance band, so any radius the user names is readable.

    The benchmark ran at 50 miles; the user's actual territory was 15. Those are
    not different searches — 15 is a subset — but a flat list forces a re-run to
    answer it. Banding the output means one sweep serves every radius, and it
    surfaces the near-miss ("4 more at 53 miles") that a hard cutoff hides.
    """
    t = _all_md(cfg)
    ok = ("distance band" in t or "band" in t) and \
         ("nearest first" in t or "sort" in t or "ranked by distance" in t
          or "by distance" in t)
    return check(skill, "reports by distance band", ok)


TESTS = [test_core_files_stay_general,
         test_vertical_pack_exists,
         test_router_loads_vertical_pack,
         test_population_class_method,
         test_distance_bands,
         test_bands_are_computable,
         test_city_name_variants_place,
         test_merge_without_org_uses_location,
         test_surname_first_names_flip,
         test_second_phone_from_mailing_address,
         test_search_name_differs_from_registry_name,
         test_profile_match_needs_corroboration,
         test_bulk_data_traps,
         test_postcode_places_precisely,
         test_frontmatter, test_portability, test_refusal,
         test_surname_particles, test_docs_claims]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill", choices=list(SKILLS) + ["both"], default="both")
    ap.add_argument("--ports", action="store_true",
                    help="also run the port frontier tests (expected red pre-port)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("-o", "--output")
    args = ap.parse_args()

    targets = list(SKILLS) if args.skill == "both" else [args.skill]
    allok = True
    for name in targets:
        cfg = SKILLS[name]
        print(f"\n=== {name} ({cfg['dir']}) ===")
        if not os.path.isdir(cfg["dir"]):
            check(name, "skill directory exists", False, cfg["dir"])
            allok = False
            continue
        for t in TESTS:
            allok &= bool(t(name, cfg))
        if args.ports:
            print(f"  -- port frontier --")
            for t in PORT_TESTS:
                t(name, cfg)   # advisory: does not gate the core suite

    n_fail = sum(1 for r in results if r["status"] == "FAIL")
    print(f"\n{len(results) - n_fail}/{len(results)} passed, {n_fail} failed")
    if args.output or args.json:
        blob = json.dumps({"results": results, "failed": n_fail}, indent=2)
        if args.output:
            open(args.output, "w").write(blob + "\n")
            print(f"wrote {args.output}")
        else:
            print(blob)
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
