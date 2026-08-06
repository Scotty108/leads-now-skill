# Bake-off ledger

One row per round. Append, never rewrite — the history is the point.

| Round | UTC | Cond | Skill | People | Reachable | Peds signal | Provenance | Subagents | Wall (s) | Score | Ported this round |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 2026-08-06 | — | both | — | — | — | — | — | — | — | baseline: 18/18 invariants green, no runs yet |
| 1 | 2026-08-06T21:40Z | gate | both | — | — | — | — | — | — | — | 18/18 green — eligible to run |
| 1 | 2026-08-06T21:45Z | ports | both | — | — | — | — | — | — | — | port frontier written TDD-first. Pre-port RED: ours lacks calibrated-email-tiers + unsourced-row-gate; skillit lacks SKILL.md-fallback + qualify-branch. Evidence: bench/preport_evidence.json. Correction: skillit DOES have surface lanes — earlier claim it lacked them was wrong. |
| 1A | 2026-08-06T21:52Z | clamped | ours | 60 | 59 | 0 | 1.00 | 3 | 640 | 0.7245 | 3 emails (pattern_confirmed, cmc-sc.com); 11 blocked sources named |
| 1A | 2026-08-06T21:52Z | clamped | skillit | 72 | 72 | 0 | 1.00 | 0 | 526 | **0.7725** | 0 emails; 5 blocked sources; won on coverage |
| 1B | 2026-08-06T22:15Z | open | ours | 84 | 84 | 2 | 1.00 | 1 | 1179 | **0.7940** | browser unlocked 23 people; FOUND a real peds anesthesiologist at 25mi |
CONFOUND: session WebSearch budget exhausted (200/200) before both runs — Condition A is a valid test of registry sourcing and a CRIPPLED test of enrichment. Both skills logged it as a top blocker.

## Per-channel coverage (the real scoreboard)
| Round | Population | Practice ph | Dept ph | Direct | Email | LinkedIn (found) | LI search | Peds signal |
|---|---|---|---|---|---|---|---|---|
| 1A | 131 | 131 | 0 | 0 | 3 | 0 | 0 | 0 |
| 1B (ours) | 84 | 65 | **19** | 0 | 3 | 0 | **84** | **2** |

### Round 1 findings that changed the answer

**The registry zero was wrong.** Round 1A reported 0 pediatric anesthesiologists
from NPI. Round 1B found **Michelle D. Lee, MD — a registered pediatric
anesthesiologist 25.4 mi out at McLeod Loris**. Her NPI record carries no
pediatric taxonomy; the subspecialty is published only on her hospital's own
directory, a JS shell to plain fetch. Parent-taxonomy querying is necessary and
NOT sufficient. Ported to both, with a test.

**Rung 3 beat rung 4 twice.** Grand Strand's provider data sat in an embedded
`physicianData` JSON in server HTML the clamped run never parsed past `<title>`;
McLeod's sat behind the site's own public Algolia index. Only Tidelands' 403
genuinely needed a browser. The browser's real contribution was DISCOVERING
where to look, not rendering.

**Literature is the wrong instrument here.** OpenAlex + Europe PMC over 60
community anesthesiologists: 0 usable peds signals, 51 of 60 with no scholarly
footprint at all. Ported to both, with a test.

**The refusal fired on a genuinely published address.** `mbuvahfj@gmail.com`
appears verbatim in PMID 26185936 — discarded because the paper's affiliation is
Detroit while the person practices in SC, and it is a personal gmail. Preserved
in `records/refused_emails.json` so the finding is not lost. Five other
tempting false positives were also discarded; counting one would have
manufactured the set's only publication-derived STRONG.

**Channel movement 1A -> 1B:** department phones 0 -> 19, LinkedIn search URLs
0 -> 84, peds signal 0 -> 2. **Work email did not move: 3.**
