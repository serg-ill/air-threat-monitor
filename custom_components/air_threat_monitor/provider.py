"""Share one provider poll across all configured locations."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AirThreatApiClient, AirThreatApiError
from .const import DEFAULT_UPDATE_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)
_DATA_PROVIDER = f"{DOMAIN}_provider"


@dataclass(frozen=True)
class ProviderSnapshot:
    """One complete public snapshot; never includes configured coordinates."""

    threats: dict[str, Any]
    alerts: dict[str, Any]
    raions: dict[str, Any]
    oblasts: dict[str, Any]
    updated_at: datetime


class AirThreatProvider(DataUpdateCoordinator[ProviderSnapshot]):
    """Poll global endpoints once and notify every subscribed location."""

    def __init__(self, hass: HomeAssistant, client: AirThreatApiClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=None,
            name=f"{DOMAIN} provider",
            update_interval=DEFAULT_UPDATE_INTERVAL,
        )
        self.client = client
        self._boundaries: tuple[dict[str, Any], dict[str, Any]] | None = None
        self._initial_refresh_lock = asyncio.Lock()
        self._refresh_complete = asyncio.Event()
        self._refresh_complete.set()
        self._last_attempt: float | None = None

    async def async_ensure_ready(self) -> None:
        """Share startup work, including failures, across simultaneous setups."""

        async with self._initial_refresh_lock:
            await self._refresh_complete.wait()
            if (
                self._last_attempt is None
                or self.hass.loop.time() - self._last_attempt
                >= DEFAULT_UPDATE_INTERVAL.total_seconds()
            ):
                await self.async_refresh()
            self.snapshot()

    def snapshot(self) -> ProviderSnapshot:
        """Reject stale retained data after a failed provider update."""

        if not self.last_update_success or self.data is None:
            raise UpdateFailed("Provider update unavailable") from self.last_exception
        return self.data

    async def _async_update_data(self) -> ProviderSnapshot:
        self._refresh_complete.clear()
        try:
            if self._boundaries is None:
                raions, oblasts = await asyncio.gather(
                    self.client.async_get_raions(),
                    self.client.async_get_oblasts(),
                )
                self._boundaries = (raions, oblasts)
            threats, alerts = await asyncio.gather(
                self.client.async_get_threats(),
                self.client.async_get_alerts(),
            )
        except AirThreatApiError as error:
            raise UpdateFailed(str(error)) from error
        finally:
            self._last_attempt = self.hass.loop.time()
            self._refresh_complete.set()

        return ProviderSnapshot(
            threats=threats,
            alerts=alerts,
            raions=self._boundaries[0],
            oblasts=self._boundaries[1],
            updated_at=datetime.now(UTC),
        )


async def async_get_provider(hass: HomeAssistant) -> AirThreatProvider:
    """Keep the shared coordinator independent of any one config entry."""

    if (provider := hass.data.get(_DATA_PROVIDER)) is None:
        provider = AirThreatProvider(
            hass, AirThreatApiClient(async_get_clientsession(hass))
        )
        hass.data[_DATA_PROVIDER] = provider
        await provider.async_register_shutdown()
    return provider
