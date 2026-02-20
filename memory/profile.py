"""
User Profile — Stores athlete/user profile data for personalized research responses.

Profile is injected into every research query to allow Kiwi to:
- Personalize protein/carb/calorie recommendations
- Contextualize evidence by training status, sex, age
- Compute energy availability, RED-S risk assessment
- Generate sport-specific protocols
"""

import json
from pathlib import Path
from typing import Literal, Any

PROFILE_PATH = Path.home() / ".kiwi" / "profile.json"

Sex = Literal["male", "female", "other"]
ActivityLevel = Literal["sedentary", "light", "moderate", "active", "very_active"]


class UserProfile:
    """Persistent user profile for personalized Kiwi responses."""

    FIELDS = {
        "name": str,
        "age": int,
        "sex": str,
        "weight_kg": float,
        "height_cm": float,
        "body_fat_pct": float,
        "sport": str,
        "position": str,
        "training_status": str,   # novice, intermediate, advanced, elite
        "activity_level": str,
        "primary_goal": str,      # performance, body_composition, health, longevity
        "dietary_restrictions": list,
        "known_deficiencies": list,
        "current_supplements": list,
        "health_conditions": list,
    }

    def __init__(self):
        self.data: dict[str, Any] = self._load()

    def _load(self) -> dict[str, Any]:
        if PROFILE_PATH.exists():
            try:
                return json.loads(PROFILE_PATH.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        return {}

    def save(self):
        PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        PROFILE_PATH.write_text(json.dumps(self.data, indent=2))

    def set(self, key: str, value: Any) -> bool:
        """Set a profile field. Returns False if field is unknown."""
        if key not in self.FIELDS:
            return False
        expected_type = self.FIELDS[key]
        try:
            if expected_type == list and isinstance(value, str):
                value = [v.strip() for v in value.split(",") if v.strip()]
            elif expected_type != list:
                value = expected_type(value)
        except (ValueError, TypeError):
            return False
        self.data[key] = value
        self.save()
        return True

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def is_complete(self) -> bool:
        """Check if minimum required fields are set for personalization."""
        required = {"weight_kg", "sex", "age", "activity_level"}
        return required.issubset(self.data.keys())

    def to_summary(self) -> str:
        """Format profile as a concise context string for agent injection."""
        if not self.data:
            return "No user profile configured. Use /profile set <field> <value>."

        lines = []
        if name := self.data.get("name"):
            lines.append(f"Name: {name}")
        if age := self.data.get("age"):
            lines.append(f"Age: {age}")
        if sex := self.data.get("sex"):
            lines.append(f"Sex: {sex}")
        if w := self.data.get("weight_kg"):
            lines.append(f"Weight: {w} kg")
        if h := self.data.get("height_cm"):
            lines.append(f"Height: {h} cm")
        if bf := self.data.get("body_fat_pct"):
            lines.append(f"Body fat: {bf}%")
        if sport := self.data.get("sport"):
            lines.append(f"Sport: {sport}")
        if pos := self.data.get("position"):
            lines.append(f"Position: {pos}")
        if ts := self.data.get("training_status"):
            lines.append(f"Training status: {ts}")
        if al := self.data.get("activity_level"):
            lines.append(f"Activity level: {al}")
        if goal := self.data.get("primary_goal"):
            lines.append(f"Primary goal: {goal}")
        if restrictions := self.data.get("dietary_restrictions"):
            lines.append(f"Dietary restrictions: {', '.join(restrictions)}")
        if deficiencies := self.data.get("known_deficiencies"):
            lines.append(f"Known deficiencies: {', '.join(deficiencies)}")
        if supplements := self.data.get("current_supplements"):
            lines.append(f"Current supplements: {', '.join(supplements)}")
        if conditions := self.data.get("health_conditions"):
            lines.append(f"Health conditions: {', '.join(conditions)}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        return dict(self.data)
