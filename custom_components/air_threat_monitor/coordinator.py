"""Coordinate provider updates for Air Threat Monitor."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .alerts import find_local_alert, normalize_alerts
from .calculations import calculate_threat
from .const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    DOMAIN,
)
from .geojson import resolve_area
from .models import (
    ActiveAlert,
    AlertScope,
    CalculatedThreat,
    GeoPoint,
    MonitorData,
    ResolvedArea,
)
from .normalization import extract_threat_rows, normalize_threat
from .provider import AirThreatProvider
from .status import AlertStatusState, parse_datetime, update_alert_status

_LOGGER = logging.getLogger(__name__)


class AirThreatCoordinator(DataUpdateCoordinator[MonitorData]):
    """Calculate one location from the shared provider snapshot."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        provider: AirThreatProvider,
    ) -> None:
        """Initialize the coordinator."""

        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            always_update=False,
        )
        self.provider = provider
        self.home = GeoPoint(
            latitude=float(entry.data[CONF_LATITUDE]),
            longitude=float(entry.data[CONF_LONGITUDE]),
        )
        self.raion: ResolvedArea | None = None
        self.oblast: ResolvedArea | None = None
        self.raion_features: dict[str, Any] = {}
        self.oblast_features: dict[str, Any] = {}
        self.active_alerts: tuple[ActiveAlert, ...] = ()
        self._status_store = Store[dict[str, Any]](
            hass,
            1,
            f"{DOMAIN}.{entry.entry_id}.status",
        )
        self._status_state: AlertStatusState | None = None
        self._area_status_states: dict[str, AlertStatusState] = {}
        self._area_status_keys: dict[
            str,
            tuple[str | None, str | None],
        ] = {}

    @callback
    def async_connect_provider(self) -> Callable[[], None]:
        """Subscribe until this entry unloads, preserving disabled polling."""

        if self.config_entry.pref_disable_polling:
            return lambda: None

        @callback
        def update_location() -> None:
            self.config_entry.async_create_background_task(
                self.hass,
                self.async_refresh(),
                name=f"{DOMAIN} location update",
            )

        return self.provider.async_add_listener(update_location)

    async def async_request_refresh(self) -> None:
        """Keep manual entity refreshes connected to the shared data source."""

        await self.provider.async_request_refresh()
        await super().async_request_refresh()

    async def _async_setup(self) -> None:
        """Resolve the configured point to its district and oblast once."""

        stored = await self._status_store.async_load()
        if isinstance(stored, dict) and isinstance(stored.get("active"), bool):
            stored_since = parse_datetime(stored.get("since"))
            if stored_since is not None:
                self._status_state = AlertStatusState(
                    active=stored["active"],
                    since=stored_since,
                    level=(
                        str(stored["level"])
                        if stored.get("level") in ("red", "yellow")
                        else None
                    ),
                )
            stored_areas = stored.get("areas")
            if isinstance(stored_areas, dict):
                for area_id, raw_area in stored_areas.items():
                    if (
                        not isinstance(area_id, str)
                        or not isinstance(raw_area, dict)
                        or not isinstance(raw_area.get("active"), bool)
                    ):
                        continue
                    area_since = parse_datetime(raw_area.get("since"))
                    if area_since is None:
                        continue
                    raion_key = raw_area.get("raion_key")
                    oblast_key = raw_area.get("oblast_key")
                    normalized_raion_key = (
                        str(raion_key).strip() if raion_key else None
                    )
                    normalized_oblast_key = (
                        str(oblast_key).strip() if oblast_key else None
                    )
                    if not normalized_raion_key and not normalized_oblast_key:
                        continue
                    self._area_status_states[area_id] = AlertStatusState(
                        active=raw_area["active"],
                        since=area_since,
                        level=(
                            str(raw_area["level"])
                            if raw_area.get("level") in ("red", "yellow")
                            else None
                        ),
                    )
                    self._area_status_keys[area_id] = (
                        normalized_raion_key,
                        normalized_oblast_key,
                    )

        snapshot = self.provider.snapshot()
        raions, oblasts = snapshot.raions, snapshot.oblasts

        self.raion = resolve_area(self.home, raions, AlertScope.RAION)
        self.oblast = resolve_area(self.home, oblasts, AlertScope.OBLAST)
        self.raion_features = raions
        self.oblast_features = oblasts
        if self.raion is None and self.oblast is None:
            raise UpdateFailed(
                "Configured location does not match a supported district or oblast"
            )

    async def _async_update_data(self) -> MonitorData:
        """Process the same complete provider snapshot as every other location."""

        snapshot = self.provider.snapshot()
        threat_payload, alert_payload = snapshot.threats, snapshot.alerts

        calculated = []
        for row in extract_threat_rows(threat_payload):
            threat = normalize_threat(row)
            if threat is not None:
                calculated.append(calculate_threat(threat, self.home))
        calculated.sort(key=lambda item: item.distance_km)

        self.active_alerts = normalize_alerts(alert_payload)
        local_alert = find_local_alert(
            self.active_alerts,
            raion_key=self.raion.area_key if self.raion else None,
            oblast_key=self.oblast.area_key if self.oblast else None,
        )

        now = snapshot.updated_at
        self._status_state, status_changed = update_alert_status(
            self._status_state,
            active=local_alert is not None,
            provider_since=local_alert.since if local_alert else None,
            now=now,
            alert_level=local_alert.level.value if local_alert else None,
        )
        area_status_changed = False
        for area_id, (raion_key, oblast_key) in self._area_status_keys.items():
            area_alert = find_local_alert(
                self.active_alerts,
                raion_key=raion_key,
                oblast_key=oblast_key,
            )
            previous_area_status = self._area_status_states.get(area_id)
            area_status, area_changed = update_alert_status(
                previous_area_status,
                active=area_alert is not None,
                provider_since=area_alert.since if area_alert else None,
                now=now,
                alert_level=area_alert.level.value if area_alert else None,
            )
            self._area_status_states[area_id] = area_status
            area_status_changed = area_status_changed or area_changed

        if status_changed or area_status_changed:
            await self._async_save_status_states()

        return MonitorData(
            threats=tuple(calculated),
            local_alert=local_alert,
            raion=self.raion,
            oblast=self.oblast,
            updated_at=now,
            status_since=self._status_state.since,
        )

    def calculate_for_point(
        self,
        point: GeoPoint,
    ) -> tuple[
        tuple[CalculatedThreat, ...],
        ActiveAlert | None,
        ResolvedArea | None,
        ResolvedArea | None,
    ]:
        """Recalculate the cached provider snapshot for one viewer location."""

        if self.data is None:
            return (), None, None, None

        threats = tuple(
            sorted(
                (
                    calculate_threat(item.threat, point)
                    for item in self.data.threats
                ),
                key=lambda item: item.distance_km,
            )
        )
        raion = resolve_area(
            point,
            self.raion_features,
            AlertScope.RAION,
        )
        oblast = resolve_area(
            point,
            self.oblast_features,
            AlertScope.OBLAST,
        )
        alert = find_local_alert(
            self.active_alerts,
            raion_key=raion.area_key if raion else None,
            oblast_key=oblast.area_key if oblast else None,
        )
        return threats, alert, raion, oblast

    def status_since_for_area(
        self,
        raion: ResolvedArea | None,
        oblast: ResolvedArea | None,
        alert: ActiveAlert | None,
    ) -> datetime | None:
        """Return and persist the observed status start for a dynamic area."""

        area_id = self._area_status_id(raion, oblast)
        if area_id is None:
            return None

        raion_key = raion.area_key if raion else None
        oblast_key = oblast.area_key if oblast else None
        is_new_area = area_id not in self._area_status_keys
        self._area_status_keys[area_id] = (raion_key, oblast_key)

        previous = self._area_status_states.get(area_id)
        if previous is None and self._matches_configured_area(raion, oblast):
            previous = self._status_state

        state, changed = update_alert_status(
            previous,
            active=alert is not None,
            provider_since=alert.since if alert else None,
            now=datetime.now(UTC),
            alert_level=alert.level.value if alert else None,
        )
        self._area_status_states[area_id] = state
        if is_new_area or changed:
            self.hass.async_create_task(self._async_save_status_states())
        return state.since

    @staticmethod
    def _area_status_id(
        raion: ResolvedArea | None,
        oblast: ResolvedArea | None,
    ) -> str | None:
        """Build a stable key for one resolved administrative area."""

        if raion is not None:
            return f"raion:{raion.area_key}"
        if oblast is not None:
            return f"oblast:{oblast.area_key}"
        return None

    def _matches_configured_area(
        self,
        raion: ResolvedArea | None,
        oblast: ResolvedArea | None,
    ) -> bool:
        """Return whether a dynamic point uses the configured status scope."""

        if raion is not None and self.raion is not None:
            return raion.area_key == self.raion.area_key
        return (
            raion is None
            and self.raion is None
            and oblast is not None
            and self.oblast is not None
            and oblast.area_key == self.oblast.area_key
        )

    def _status_store_payload(self) -> dict[str, Any]:
        """Serialize configured and dynamically observed status periods."""

        payload: dict[str, Any] = {
            "active": self._status_state.active if self._status_state else False,
            "since": (
                self._status_state.since.isoformat()
                if self._status_state
                else None
            ),
            "level": self._status_state.level if self._status_state else None,
            "areas": {},
        }
        areas: dict[str, Any] = payload["areas"]
        for area_id, state in self._area_status_states.items():
            raion_key, oblast_key = self._area_status_keys.get(
                area_id,
                (None, None),
            )
            areas[area_id] = {
                "raion_key": raion_key,
                "oblast_key": oblast_key,
                "active": state.active,
                "since": state.since.isoformat(),
                "level": state.level,
            }
        return payload

    async def _async_save_status_states(self) -> None:
        """Persist configured and dynamically observed status periods."""

        await self._status_store.async_save(self._status_store_payload())
