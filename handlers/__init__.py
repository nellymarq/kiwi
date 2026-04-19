"""Kiwi slash-command handlers.

Organized by domain. Each handler is a module-level function taking a
Kiwi instance as its first argument. The dispatcher in kiwi.py delegates
to handlers via one-line calls.

Architecture chosen Tier 41 (Injury pilot):
- Option B: function + kiwi arg (string forward-ref to avoid circular import)
- Sync handlers return None; async handlers are async def and the
  dispatcher awaits them
- Dispatcher elif chain preserved; bodies extracted verbatim

Phasing plan (26 domains, Tier 41 → ~Tier 66+):
  41 Injury (pilot)  42 Mental  43 Environ  44 Female
  45 Training Zones  46 Body Comp  47 Sleep  48 Recovery
  49 Hydration  50 Labs  51 Food+Supps  52 Training Load
  53 Progress+Team  54 Interventions  55 Sports (first async)
  56 Literature  57 Planning  58 CompetitionPrep  59 Wearable
  60 Orchestration  61 Optimization  62 Intel  63 Deep Research
  64 Delivery  65 Sessions  66+ cleanup
"""
