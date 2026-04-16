# Kiwi — Performance Research Architect

## Quick Reference
- Launch: `python3 kiwi.py`
- Tests: `python3 -m pytest tests/ -x -q` (967 tests)
- GitHub: `nellymarq/kiwi`
- Always run tests before committing code changes.

## Multi-Client Support
- Each client has isolated profile + memory at `~/.kiwi/clients/<name>/`
- Default client `self` is created automatically with legacy data migration
- Active client shown in REPL prompt (e.g., `Kiwi (athlete_a) >`)
- Commands: `/clients`, `/new_client <name>`, `/switch_client <name>`, `/delete_client <name>`

## Architecture
- `agents/`: Planning, Critique/RWL, Protocol, Orchestrator, SportsAgent, **Synthesis** (multi-paper deep review), **NOf1Agent** (experimental design). All async, claude-opus-4-6.
- `tools/`: PubMed, OpenAlex, ClinicalTrials.gov, **EuropePMC** (full-text OA), **Unpaywall** (OA PDF discovery), **Semantic Scholar** (TLDR + citations), **GRADE** (evidence grading), SportsCalc, ResearchExporter, supplements (25), interactions (67), biomarkers (28), body_composition, training_zones, recovery, hydration, periodization, sleep_optimizer, injury_prevention, female_athlete, environmental, mental_performance, food_database, race_predictor
- `memory/`: KiwiMemory (episodic + semantic + threads + archive), UserProfile (validated)

## Literature Sources (5 databases)
- **PubMed** — NCBI biomedical literature
- **OpenAlex** — 250M+ works, sports nutrition journal filter
- **ClinicalTrials.gov** — 500K+ registered trials
- **Europe PMC** — 40M+ articles, 6M+ full-text open access
- **Semantic Scholar** — 200M+ papers with AI-generated TLDR summaries

All deduplicated by DOI, merged into a single context block for Claude.

## Research Methodology
- **GRADE evidence grading** — formal certainty assessment (HIGH/MODERATE/LOW/VERY LOW) with explicit justification
- **Methodology quality tools** — RoB 2 (RCTs), ROBINS-I (observational), AMSTAR 2 (systematic reviews)
- **Ralph Wiggum Loop** — 5-dimension critique (grounding, hierarchy, mechanism, logic, uncertainty)
- **Evidence Synthesis Agent** — structured multi-paper review with consensus/contradiction analysis
- **N-of-1 Protocol Designer** — rigorous single-subject experimental design
- **Citation chasing** — forward (cited by) and backward (references)
- **Full-text access** — Europe PMC + Unpaywall for OA PDFs

## Commands (65+)
- **Research:** direct query · /protocol · /plan
- **Literature:** /pubmed · /openalex · /trials · /tldr · /fulltext <doi> · /citedby <doi>
- **Deep Research:** /synthesize <claim> · /n_of_1 <question> · /grade <tier>
- **Memory:** /memory · /remember · /export · /archive · /stale
- **Threads:** /thread new|use|list
- **Profile:** /profile · /profile set
- **Supplements:** /supp · /supplist · /check · /interact
- **Food:** /food · /food+ · /compare
- **Training:** /session · /load · /blocks · /prilepin
- **Zones:** /hrzones · /powerzones · /pacezones · /vo2max · /hrmax · /distribution
- **Labs:** /labs · /biomarker
- **Sleep:** /sleep · /chronotype · /caffeine · /sleepdebt · /hormones · /bedtime
- **Recovery:** /readiness · /doms · /supercomp · /deload · /recover · /mps
- **Hydration:** /sweat · /sweatest · /rehydrate · /urine · /hyponatremia · /prehydrate
- **Body:** /bodyfat · /ffmi · /ea · /weightplan · /skinfold
- **Injury:** /acwr · /fms · /overuse · /return · /prevent
- **Female:** /cycle · /reds · /iron · /postpartum
- **Environ:** /altitude · /heat · /cold · /airquality · /jetlag
- **Mental:** /anxiety · /burnout · /visualize
- **Sports:** /assess
- **Session:** /clear · /new · /help · /quit

## Also Bundled In
- Kiwi agents are deployed inside `calsanova/backend/kiwi_agents/` for production use.
- kiwi_autonomy.py (in /home/nelly/rwql/) uses Kiwi's pipeline for self-directed research.
