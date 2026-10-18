"""Diagnostics support for Air Threat Monitor."""

from __future__ import annotations

from collections import Counter
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import AirThreatConfigEntry
from .const import CONF_LATITUDE, CONF_LONGITUDE, VERSION

_TO_REDACT = {CONF_LATITUDE, CONF_LONGITUDE}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: AirThreatConfigEntry,
) -> dict[str, Any]:
    """Return privacy-safe diagnostics for a config entry."""

    coordinator = entry.runtime_data
    data = coordinator.data
    categories = Counter(item.threat.category.value for item in data.threats)
    nearest = data.threats[0] if data.threats else None

    return {
        "integration_version": VERSION,
        "entry": async_redact_data(dict(entry.data), _TO_REDACT),
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "last_exception": (
                str(coordinator.last_exception)
                if coordinator.last_exception is not None
                else None
            ),
            "update_interval_seconds": (
                coordinator.provider.update_interval.total_seconds()
                if coordinator.provider.update_interval is not None
                else None
            ),
            "updated_at": data.updated_at.isoformat(),
            "status_since": (
                data.status_since.isoformat() if data.status_since else None
            ),
        },
        "snapshot": {
            "alert_active": data.local_alert is not None,
            "alert_scope": (
                data.local_alert.scope.value if data.local_alert else None
            ),
            "alert_level": (
                data.local_alert.level.value if data.local_alert else None
            ),
            "target_count": len(data.threats),
            "stale_target_count": sum(
                item.threat.status == "stale" for item in data.threats
            ),
            "target_categories": dict(categories),
            "within_100_km": sum(
                item.distance_km <= 100 for item in data.threats
            ),
            "nearest": (
                {
                    "category": nearest.threat.category.value,
                    "distance_km": round(nearest.distance_km, 1),
                    "has_heading": nearest.threat.heading is not None,
                    "is_approaching": nearest.is_approaching,
                }
                if nearest
                else None
            ),
        },
    }
