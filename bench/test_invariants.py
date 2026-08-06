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


PORT_TESTS = [port_cms_doctors_and_clinicians,
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


TESTS = [test_frontmatter, test_portability, test_refusal,
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
