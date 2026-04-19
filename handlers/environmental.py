"""Environmental command handlers (Tier 43).

Sync-only. All return None implicitly. Same pattern as handlers/injury.py
(Tier 41 pilot).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from rich import box
from rich.panel import Panel

from tools.environmental import (
    air_quality_adjustment,
    altitude_training_protocol,
    cold_exposure_protocol,
    format_air_quality,
    format_altitude_protocol,
    format_cold_protocol,
    format_heat_protocol,
    format_jet_lag,
    heat_acclimatization_protocol,
    jet_lag_protocol,
)

if TYPE_CHECKING:
    from kiwi import Kiwi


def handle_altitude(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /altitude — altitude training protocol (LHTL model)."""
    parts = query[9:].strip().split()
    if len(parts) >= 1:
        try:
            target = int(parts[0])
            current = int(parts[1]) if len(parts) > 1 else 0
            weeks = int(parts[2]) if len(parts) > 2 else 3
            sport = parts[3] if len(parts) > 3 else kiwi.profile.data.get("sport", "endurance")
            result = altitude_training_protocol(target, current, weeks, sport)
            output = format_altitude_protocol(result)
            kiwi.console.print(Panel(output, title="[cyan]Altitude Training[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
            kiwi._state["last_output"] = output
        except ValueError:
            kiwi.console.print("[dim]  Usage: /altitude <target_m> [current_m] [weeks] [sport][/dim]")
    else:
        kiwi.console.print("[dim]  Usage: /altitude <target_m> [current_m] [weeks] [sport][/dim]")


def handle_heat(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /heat — WBGT-based heat acclimatization protocol."""
    parts = query[5:].strip().split()
    if len(parts) >= 1:
        try:
            wbgt = float(parts[0])
            acclim = parts[1].lower() in ("yes", "true", "y", "1") if len(parts) > 1 else False
            result = heat_acclimatization_protocol(wbgt, acclimatized=acclim)
            output = format_heat_protocol(result)
            kiwi.console.print(Panel(output, title="[cyan]Heat Acclimatization[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
            kiwi._state["last_output"] = output
        except ValueError:
            kiwi.console.print("[dim]  Usage: /heat <wbgt_celsius> [acclimatized:yes/no][/dim]")
    else:
        kiwi.console.print("[dim]  Usage: /heat <wbgt_celsius> [acclimatized:yes/no][/dim]")


def handle_cold(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /cold — cold exposure protocol with wind chill."""
    parts = query[5:].strip().split()
    if len(parts) >= 1:
        try:
            temp = float(parts[0])
            wind = float(parts[1]) if len(parts) > 1 else 0.0
            precip = parts[2].lower() in ("yes", "true", "y", "1") if len(parts) > 2 else False
            result = cold_exposure_protocol(temp, wind_speed_kmh=wind, precipitation=precip)
            output = format_cold_protocol(result)
            kiwi.console.print(Panel(output, title="[cyan]Cold Exposure[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
            kiwi._state["last_output"] = output
        except ValueError:
            kiwi.console.print("[dim]  Usage: /cold <temp_c> [wind_kmh] [precipitation:yes/no][/dim]")
    else:
        kiwi.console.print("[dim]  Usage: /cold <temp_c> [wind_kmh] [precipitation:yes/no][/dim]")


def handle_airquality(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /airquality — AQI-based training modification."""
    parts = query[11:].strip().split()
    if len(parts) >= 1:
        try:
            aqi = int(parts[0])
            result = air_quality_adjustment(aqi)
            output = format_air_quality(result)
            kiwi.console.print(Panel(output, title="[cyan]Air Quality[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
            kiwi._state["last_output"] = output
        except ValueError:
            kiwi.console.print("[dim]  Usage: /airquality <aqi_0_500>[/dim]")
    else:
        kiwi.console.print("[dim]  Usage: /airquality <aqi_0_500>[/dim]")


def handle_jetlag(kiwi: "Kiwi", query: str, q_lower: str) -> None:
    """Handle /jetlag — time-zone travel adjustment protocol."""
    parts = query[7:].strip().split()
    if len(parts) >= 1:
        try:
            zones = int(parts[0])
            direction = parts[1] if len(parts) > 1 else "east"
            result = jet_lag_protocol(zones, direction)
            output = format_jet_lag(result)
            kiwi.console.print(Panel(output, title="[cyan]Jet Lag Protocol[/cyan]", border_style="cyan", box=box.ROUNDED, padding=(0, 2)))
            kiwi._state["last_output"] = output
        except ValueError:
            kiwi.console.print("[dim]  Usage: /jetlag <time_zones> [east|west][/dim]")
    else:
        kiwi.console.print("[dim]  Usage: /jetlag <time_zones> [east|west][/dim]")
