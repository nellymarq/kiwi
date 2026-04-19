"""
User Profile — Stores athlete/user profile data for personalized research responses.

Profile is injected into every research query to allow Kiwi to:
- Personalize protein/carb/calorie recommendations
- Contextualize evidence by training status, sex, age
- Compute energy availability, RED-S risk assessment
- Generate sport-specific protocols
"""

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Literal

from . import client_manager

PROFILE_PATH = Path.home() / ".kiwi" / "profile.json"  # kept for backwards compatibility

Sex = Literal["male", "female", "other"]
ActivityLevel = Literal["sedentary", "light", "moderate", "active", "very_active"]

VALID_SEX = {"male", "female", "other"}
VALID_ACTIVITY_LEVEL = {"sedentary", "light", "moderate", "active", "very_active"}
VALID_TRAINING_STATUS = {"novice", "intermediate", "advanced", "elite"}
VALID_PRIMARY_GOAL = {"performance", "body_composition", "health", "longevity", "rehabilitation"}
VALID_MENSTRUAL_STATUS = {
    "normal", "irregular", "amenorrheic", "heavy",
    "postmenopausal", "not_applicable",
}

FIELD_RANGES = {
    "age": (10, 120),
    "weight_kg": (20.0, 300.0),
    "height_cm": (100.0, 250.0),
    "body_fat_pct": (2.0, 60.0),
    "cycle_day": (1, 28),
}

CYCLE_LENGTH_DAYS = 28  # matches CYCLE_PHASES in tools/female_athlete.py


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
        "training_status": str,
        "activity_level": str,
        "primary_goal": str,
        "dietary_restrictions": list,
        "known_deficiencies": list,
        "current_supplements": list,
        "health_conditions": list,
        "menstrual_status": str,
        "injury_history": list,
        "cycle_day": int,
    }

    def __init__(self, client: str | None = None):
        self.client = client
        self.data: dict[str, Any] = self._load()

    def _path(self) -> Path:
        return client_manager.profile_path(self.client)

    def _load(self) -> dict[str, Any]:
        path = self._path()
        if path.exists():
            try:
                return json.loads(path.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        return {}

    def save(self):
        path = self._path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.data, indent=2))

    def set(self, key: str, value: Any) -> bool | str:
        """Set a profile field. Returns True on success, error string on validation failure, False if unknown field."""
        if key not in self.FIELDS:
            return False
        expected_type = self.FIELDS[key]
        try:
            if expected_type == list and isinstance(value, str):
                value = [v.strip() for v in value.split(",") if v.strip()]
            elif expected_type != list:
                value = expected_type(value)
        except (ValueError, TypeError):
            return f"Invalid value for {key}: expected {expected_type.__name__}"

        # Enum validation
        if key == "sex":
            normalized = str(value).lower().strip()
            if normalized in ("m", "male"):
                value = "male"
            elif normalized in ("f", "female"):
                value = "female"
            elif normalized not in VALID_SEX:
                return f"Invalid sex: must be male, female, or other"
        if key == "activity_level" and value not in VALID_ACTIVITY_LEVEL:
            return f"Invalid activity_level: must be one of {', '.join(sorted(VALID_ACTIVITY_LEVEL))}"
        if key == "training_status" and value not in VALID_TRAINING_STATUS:
            return f"Invalid training_status: must be one of {', '.join(sorted(VALID_TRAINING_STATUS))}"
        if key == "primary_goal" and value not in VALID_PRIMARY_GOAL:
            return f"Invalid primary_goal: must be one of {', '.join(sorted(VALID_PRIMARY_GOAL))}"
        if key == "menstrual_status":
            normalized = str(value).lower().strip()
            if normalized not in VALID_MENSTRUAL_STATUS:
                return f"Invalid menstrual_status: must be one of {', '.join(sorted(VALID_MENSTRUAL_STATUS))}"
            value = normalized

        # Range validation
        if key in FIELD_RANGES:
            lo, hi = FIELD_RANGES[key]
            if not (lo <= float(value) <= hi):
                return f"Invalid {key}: must be between {lo} and {hi}"

        self.data[key] = value
        # Auto-stamp the record date when cycle_day is set, for extrapolation
        if key == "cycle_day":
            self.data["cycle_day_set_at"] = datetime.now(timezone.utc).date().isoformat()
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
        if ms := self.data.get("menstrual_status"):
            if self.data.get("sex") == "female":
                lines.append(f"Menstrual status: {ms}")
        if self.data.get("sex") == "female":
            current_day = self.get_current_cycle_day()
            if current_day is not None:
                lines.append(f"Cycle day (today, extrapolated): {current_day}")
        if ih := self.data.get("injury_history"):
            lines.append(f"Injury history: {', '.join(ih)}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        return dict(self.data)

    def get_current_cycle_day(self) -> int | None:
        """Extrapolate today's cycle day from the stored anchor.

        Returns None if cycle_day hasn't been set, or if the stored
        anchor/timestamp is malformed. Uses a hardcoded 28-day cycle.
        Clock-skew protection: if days_elapsed is negative, returns
        the raw anchor.
        """
        anchor = self.data.get("cycle_day")
        anchor_date_str = self.data.get("cycle_day_set_at")
        if anchor is None or not anchor_date_str:
            return None
        try:
            anchor_date = date.fromisoformat(str(anchor_date_str))
            today = datetime.now(timezone.utc).date()
            days_elapsed = (today - anchor_date).days
            if days_elapsed < 0:
                return int(anchor)
            return ((int(anchor) - 1 + days_elapsed) % CYCLE_LENGTH_DAYS) + 1
        except (ValueError, TypeError):
            return None
