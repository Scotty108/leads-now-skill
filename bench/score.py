#!/usr/bin/env python3
"""Score one benchmark run. Never score by eye.

Reads a run directory produced by the bake-off protocol and returns a weighted
score plus the disqualifiers. Deliverability outranks volume on purpose: a big
list of guessed addresses is worth less than a small verified one, so raw count
is capped at 25% while reachability and provenance together carry 40%.

Usage:
  python3 bench/score.py bench/runs/round1__ours__clamped
  python3 bench/score.py bench/runs/*__clamped --compare
  python3 bench/score.py <dir> --json -o score.json

Stdlib only.
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import re
import sys

# Weights sum to 1.0. Change them in LOOP.md too — the loop optimises whatever
# is written here, faithfully, for hours.
WEIGHTS = {
    "in_radius": 0.25,
    "reachable": 0.25,
    "peds_signal": 0.20,
    "provenance": 0.15,
    "honest_gaps": 0.10,
    "cost": 0.05,
}

# Normalisation ceilings. A run that hits the ceiling scores 1.0 on that axis;
# these are targets, not observed maxima, so scores stay comparable across
# rounds even as both skills improve.
TARGET_IN_RADIUS = 75
TARGET_REACHABLE = 60
TARGET_PEDS = 12
COST_BUDGET_S = 1500  # ~25 min timebox


def _read_meta(d):
    p = os.path.join(d, "meta.json")
    if not os.path.exists(p):
        return None, f"meta.json missing in {d}"
    try:
        return json.load(open(p)), None
    except Exception as e:
        return None, f"meta.json unreadable: {e}"


def _read_rows(d):
    p = os.path.join(d, "result.csv")
    if not os.path.exists(p):
        return []
    try:
        with open(p, newline="", encoding="utf-8", errors="replace") as fh:
            return list(csv.DictReader(fh))
    except Exception:
        return []


def _provenance_ratio(rows):
    """Share of populated value fields that carry a source.

    Skills use different provenance conventions — per-field `<field>_source`
    columns, a row-level `source_url`, or an `evidence` string. All are valid,
    so all count; recognising only one would score a convention rather than a
    property. Label and derived columns are excluded: `confidence` is a
    judgement, `dist_to_*_mi` is arithmetic, and neither is a sourceable claim.
    """
    if not rows:
        return 0.0

    ROW_LEVEL = ("source_url", "evidence", "all_sources", "source",
                 "source_rung", "external_id")
    SKIP_EXACT = {"confidence", "source_count", "record_type", "territory",
                  "email_status", "email_risk", "last_verified_note"}

    def is_meta(k):
        kl = k.lower()
        return (kl in SKIP_EXACT or kl in ROW_LEVEL
                or kl.endswith("_source") or kl.startswith("source_")
                or kl.startswith("dist_to_") or kl.endswith("_note"))

    populated = sourced = 0
    for r in rows:
        row_prov = any((r.get(c) or "").strip() for c in ROW_LEVEL)
        for k, v in r.items():
            if is_meta(k) or not (v or "").strip():
                continue
            populated += 1
            if (r.get(f"{k}_source") or "").strip() or row_prov:
                sourced += 1
    return (sourced / populated) if populated else 0.0


def _disqualifiers(meta, rows):
    """Hard failures. Any one of these invalidates the run regardless of score.

    These encode the skill's own promises: never emit an unevidenced address,
    never report a truncated count as a total, never make an unsourced claim.
    """
    dq = []

    # An address at top confidence with no supporting evidence.
    for r in rows:
        email = (r.get("email") or "").strip()
        if not email:
            continue
        conf = (r.get("email_confidence") or r.get("confidence")
                or r.get("email_status") or "").lower()
        if conf in ("", "unknown", "guess", "guessed"):
            dq.append(f"address {email!r} carries no confidence label")
            break

    # A total reported from a truncated query without saying so. Search the
    # REPORT only — searching the meta blob too would match its own
    # "truncation_detected" key and make this check self-satisfying.
    if meta.get("truncation_detected"):
        disclosed = re.search(r"truncat|incomplete|partition|ceiling",
                              _report_text(meta.get("_dir", "")))
        note = (meta.get("notes") or "").lower()
        if not disclosed and not re.search(r"truncat|incomplete|partition", note):
            dq.append("truncation detected but not declared in the report")

    return dq


def _report_text(d):
    p = os.path.join(d, "report.md")
    return open(p, errors="replace").read().lower() if os.path.exists(p) else ""


def score_run(d):
    meta, err = _read_meta(d)
    if err:
        return {"dir": d, "error": err, "score": 0.0}
    meta["_dir"] = d
    rows = _read_rows(d)

    n_radius = int(meta.get("in_radius") or 0)
    n_reach = int(meta.get("reachable") or 0)
    n_peds = int(meta.get("peds_signal_strong") or 0) + \
        int(meta.get("peds_signal_moderate") or 0)
    prov = _provenance_ratio(rows)

    # Honest gaps: naming blocked sources and declaring truncation is worth
    # points, because the alternative — silence — looks identical to success.
    blocked = meta.get("blocked_sources") or []
    gaps = 0.0
    if blocked:
        gaps += 0.6
        if all((b.get("reason") or "").strip() for b in blocked):
            gaps += 0.2
    else:
        gaps += 0.4  # plausibly nothing blocked; not rewarded as much as naming
    if _report_text(d):
        gaps += 0.2
    gaps = min(gaps, 1.0)

    wall = float(meta.get("wall_clock_s") or COST_BUDGET_S)
    cost = max(0.0, 1.0 - (wall / COST_BUDGET_S))

    parts = {
        "in_radius": min(n_radius / TARGET_IN_RADIUS, 1.0),
        "reachable": min(n_reach / TARGET_REACHABLE, 1.0),
        "peds_signal": min(n_peds / TARGET_PEDS, 1.0),
        "provenance": prov,
        "honest_gaps": gaps,
        "cost": cost,
    }
    total = sum(parts[k] * WEIGHTS[k] for k in WEIGHTS)
    dq = _disqualifiers(meta, rows)

    return {
        "dir": os.path.basename(d),
        "skill": meta.get("skill"),
        "condition": meta.get("condition"),
        "raw": {"in_radius": n_radius, "reachable": n_reach,
                "peds": n_peds, "provenance": round(prov, 3),
                "rows": len(rows), "subagents": meta.get("subagents"),
                "wall_clock_s": meta.get("wall_clock_s"),
                "blocked": len(blocked)},
        "parts": {k: round(v, 3) for k, v in parts.items()},
        "score": 0.0 if dq else round(total, 4),
        "disqualified": dq,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("-o", "--output")
    args = ap.parse_args()

    targets = []
    for d in args.dirs:
        targets.extend(sorted(glob.glob(d)) if any(c in d for c in "*?[") else [d])

    out = [score_run(d) for d in targets if os.path.isdir(d)]
    if not out:
        print("no run directories found", file=sys.stderr)
        return 1

    for r in out:
        if r.get("error"):
            print(f"{r['dir']}: {r['error']}")
            continue
        print(f"\n{r['dir']}  [{r['skill']} / {r['condition']}]")
        print(f"  raw   {r['raw']}")
        print(f"  parts {r['parts']}")
        print(f"  SCORE {r['score']}")
        for d in r["disqualified"]:
            print(f"  ** DISQUALIFIED: {d}")

    if args.compare and len(out) > 1:
        ranked = sorted((r for r in out if not r.get("error")),
                        key=lambda r: -r["score"])
        print("\n--- ranking ---")
        for i, r in enumerate(ranked, 1):
            print(f"  {i}. {r['skill']}/{r['condition']}  {r['score']}")
        if len(ranked) > 1 and ranked[0]["score"] == ranked[1]["score"]:
            print("  (tie — record it as a tie rather than manufacturing a winner)")

    if args.output or args.json:
        blob = json.dumps(out, indent=2)
        if args.output:
            open(args.output, "w").write(blob + "\n")
            print(f"\nwrote {args.output}")
        else:
            print(blob)
    return 0


if __name__ == "__main__":
    sys.exit(main())
