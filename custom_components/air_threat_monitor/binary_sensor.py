"""Binary sensors for Air Threat Monitor."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import AirThreatConfigEntry
from .const import asset_url
from .entity import AirThreatEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AirThreatConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the local air-alert binary sensor."""

    async_add_entities([AirAlertBinarySensor(entry)])


class AirAlertBinarySensor(AirThreatEntity, BinarySensorEntity):
    """Report whether an air alert affects the configured location."""

    _attr_translation_key = "air_alert"
    _attr_device_class = BinarySensorDeviceClass.SAFETY

    def __init__(self, entry: AirThreatConfigEntry) -> None:
        super().__init__(entry.runtime_data, entry, "air_alert")

    @property
    def is_on(self) -> bool:
        """Return true while a local air alert is active."""

        return self.coordinator.data.local_alert is not None

    @property
    def icon(self) -> str:
        """Return a state-aware icon."""

        alert = self.coordinator.data.local_alert
        if alert is None:
            return "mdi:shield-check"
        return (
            "mdi:shield-alert-outline"
            if alert.level.value == "yellow"
            else "mdi:shield-alert"
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return details about the matched administrative area."""

        data = self.coordinator.data
        alert = data.local_alert
        area = data.raion or data.oblast
        return {
            "area": (
                alert.name
                if alert and alert.name
                else area.name
                if area and area.name
                else None
            ),
            "oblast": (
                alert.oblast
                if alert and alert.oblast
                else area.oblast
                if area and area.oblast
                else None
            ),
            "alert_since": alert.since if alert else None,
            "alert_level": alert.level.value if alert else None,
            "alert_reasons": list(alert.reasons) if alert else [],
            "status_since": (
                data.status_since.isoformat() if data.status_since else None
            ),
            "scope": alert.scope.value if alert else None,
        }
