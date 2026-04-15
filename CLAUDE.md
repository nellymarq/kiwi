# Kiwi — Performance Research Architect

## Quick Reference
- Launch: `python3 kiwi.py`
- Tests: `python3 -m pytest tests/ -x -q` (825 tests)
- GitHub: `nellymarq/kiwi`
- Always run tests before committing code changes.

## Architecture
- `agents/`: Planning, Critique/RWL, Protocol, Orchestrator (all async, claude-opus-4-6)
- `tools/`: PubMed, OpenAlex (JISSN/BJSM/Nutrients/Frontiers), SportsCalc, ResearchExporter, supplements (19), body_composition, training_zones, interactions, recovery, hydration, sports_agent, injury_prevention, female_athlete, environmental, mental_performance
- `memory/`: KiwiMemory (episodic + semantic + threads), UserProfile

## Also Bundled In
- Kiwi agents are also deployed inside `calsanova/backend/kiwi_agents/` for production use.
