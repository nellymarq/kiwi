# Kiwi — Performance Research Architect

## Quick Reference
- Launch: `python3 kiwi.py`
- Tests: `python3 -m pytest tests/ -x -q` (890 tests)
- GitHub: `nellymarq/kiwi`
- Always run tests before committing code changes.

## Architecture
- `agents/`: Planning, Critique/RWL, Protocol, Orchestrator, SportsAgent (all async, claude-opus-4-6)
- `tools/`: PubMed, OpenAlex (20 sports nutrition journals), SportsCalc, ResearchExporter, supplements (19), interactions, body_composition, training_zones, recovery, hydration, periodization, biomarkers, sleep_optimizer, injury_prevention, female_athlete, environmental, mental_performance, food_database, race_predictor
- `memory/`: KiwiMemory (episodic + semantic + threads + archive), UserProfile (validated)

## Literature Sources
- **PubMed** — biomedical literature via NCBI E-utilities (primary)
- **OpenAlex** — 250M+ works, filtered to sports nutrition journals (JISSN, BJSM, IJSNEM, Sports Medicine, Nutrients, Frontiers, MSSE, etc.)
- Deduplicated by DOI, merged into single context block

## Commands (55+)
- **Research:** direct query · /protocol · /plan
- **Literature:** /pubmed · /openalex
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
