# Kiwi — Performance Research Architect

An AI-powered research and practice management system for sports nutrition, exercise physiology, and human performance optimization. Built for dietitians, coaches, and sports scientists who need evidence-based answers and client-ready deliverables.

## Features

**Research Pipeline** — Multi-agent system with 5 literature sources (PubMed, OpenAlex, ClinicalTrials.gov, Europe PMC, Semantic Scholar), GRADE evidence grading, PRISMA systematic reviews, and n-of-1 experimental design.

**Practice Management** — Multi-client support with per-client profiles, biomarker tracking, progress trends, intervention outcome analysis, and branded PDF reports.

**Evidence Tools** — 35 supplements with dosing protocols, 33 biomarkers with athlete-specific ranges, 56 drug/supplement interactions, effect size calculators (Cohen's d, Hedges' g, RR, OR, NNT).

**Planning** — Meal plan generation, Prilepin-aligned training plans, competition prep (fight week/race week), supplement stack optimization, and 8 protocol templates.

**Intelligence** — Proactive biomarker-to-action recommendations, contradiction detection, risk screening (RED-S, overtraining, iron deficiency), nutrient gap analysis, and natural language command routing.

## Quick Start

```bash
# Clone
git clone https://github.com/nellymarq/kiwi.git
cd kiwi

# Install dependencies
pip install -r requirements.txt

# Set API key
export ANTHROPIC_API_KEY=sk-ant-...

# Launch
python3 kiwi.py
```

## Usage

```
Kiwi > creatine timing for combat sports
Kiwi > /synthesize "iron supplementation in female endurance athletes"
Kiwi > /review "caffeine and repeated sprint performance"
Kiwi > /meal_plan 7
Kiwi > /fight_prep
Kiwi > /optimize_stack
Kiwi > /help
```

## Requirements

- Python 3.12+
- Anthropic API key (Claude Opus 4.6)
- Optional: NCBI API key (higher PubMed rate limits), FDC API key (higher food database limits)

## Architecture

```
kiwi.py              — Interactive CLI (110+ commands)
agents/              — 17 specialized agents
tools/               — 40 tools (literature, supplements, biomarkers, analytics, etc.)
memory/              — 9 modules (per-client profiles, progress, interventions, sessions)
tests/               — 47 test files, 1302 tests
```

## Tests

```bash
python3 -m pytest tests/ -x -q    # 1302 tests, ~2 seconds
```

## License

Private repository. All rights reserved.
