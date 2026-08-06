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
    txt = ""
    for root, _, files in os.walk(cfg["dir"]):
        for f in files:
            if f.endswith(".md"):
                txt += open(os.path.join(root, f), errors="ignore").read()
    return txt.lower()


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


PORT_TESTS = [port_surface_lanes, port_skillmd_fallback, port_qualify_branch,
              port_calibrated_email_tiers, port_unsourced_row_gate]


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
