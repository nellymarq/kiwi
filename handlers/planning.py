"""Meal-plan and training-plan command handlers (Tier 57).

Async — both handlers invoke agent.run() for LLM-generated plans.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kiwi import Kiwi


async def handle_meal_plan(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /meal_plan — N-day macro-calibrated meal plan."""
    payload = query.split(maxsplit=1)
    days = 3
    if len(payload) > 1:
        try:
            days = int(payload[1].strip().split()[0])
            days = max(1, min(14, days))
        except ValueError:
            pass

    missing = [f for f in ("weight_kg", "height_cm", "age", "sex", "activity_level")
               if not kiwi.profile.get(f)]
    if missing:
        kiwi.console.print(f"[dim red]  Missing profile fields: {', '.join(missing)}. Set with /profile set <field> <value>[/dim red]")
        return

    try:
        m = kiwi.calc.compute_full_metrics(
            weight_kg=kiwi.profile.get("weight_kg"),
            height_cm=kiwi.profile.get("height_cm"),
            age=kiwi.profile.get("age"),
            sex=kiwi.profile.get("sex"),
            activity_level=kiwi.profile.get("activity_level"),
            body_fat_pct=kiwi.profile.get("body_fat_pct"),
        )
        macros_text = m.summary()
    except Exception as e:
        macros_text = f"(could not compute: {e})"

    restrictions = kiwi.profile.get("dietary_restrictions") or []
    restrictions_text = ", ".join(restrictions) if restrictions else "none"
    goal = kiwi.profile.get("primary_goal") or "maintenance"
    sport = kiwi.profile.get("sport") or "general athletic"

    kiwi.console.print(f"[dim]  Generating {days}-day meal plan for {sport}...[/dim]\n")
    result = await kiwi.meal_plan_agent.run({
        "profile_summary": kiwi.profile.to_summary(),
        "macro_targets": macros_text,
        "days": days,
        "training_schedule": f"Sport: {sport}",
        "dietary_restrictions": restrictions_text,
        "goal": goal,
    })
    kiwi._state["last_output"] = result
    kiwi.console.print(result)


async def handle_training_plan(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /training_plan — N-week periodized block for a sport."""
    parts = query.split(maxsplit=2)
    sport = kiwi.profile.get("sport") or "strength"
    weeks = 8
    if len(parts) >= 2:
        try:
            weeks = int(parts[1].strip())
            weeks = max(2, min(24, weeks))
        except ValueError:
            sport = parts[1].strip()
            if len(parts) >= 3:
                try:
                    weeks = int(parts[2].strip().split()[0])
                except ValueError:
                    pass

    goal = kiwi.profile.get("primary_goal") or "strength"

    kiwi.console.print(f"[dim]  Generating {weeks}-week training block for {sport}...[/dim]\n")
    result = await kiwi.training_plan_agent.run({
        "profile_summary": kiwi.profile.to_summary(),
        "sport": sport,
        "weeks": weeks,
        "goal": goal,
        "current_maxes": "",
        "current_load": "",
        "frequency": 4,
    })
    kiwi._state["last_output"] = result
    kiwi.console.print(result)
