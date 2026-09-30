"""Service actions provided by Air Threat Monitor."""

from __future__ import annotations

from typing import cast

import voluptuous as vol
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
    callback,
)
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .const import CONF_CONFIG_ENTRY_ID, DOMAIN, SERVICE_GET_TARGETS
from .coordinator import AirThreatCoordinator
from .websocket import serialize_threat

GET_TARGETS_SCHEMA = vol.Schema(
    {vol.Required(CONF_CONFIG_ENTRY_ID): cv.string}
)


@callback
def async_register_services(hass: HomeAssistant) -> None:
    """Register integration service actions."""

    async def async_get_targets(call: ServiceCall) -> ServiceResponse:
        """Return the complete current target list for one configured location."""

        entry_id = call.data[CONF_CONFIG_ENTRY_ID]
        entry = hass.config_entries.async_get_entry(entry_id)
        if entry is None or entry.domain != DOMAIN:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="config_entry_not_found",
            )
        if entry.state is not ConfigEntryState.LOADED:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="config_entry_not_loaded",
            )

        coordinator = cast(AirThreatCoordinator, entry.runtime_data)
        data = coordinator.data
        return {
            "config_entry_id": entry.entry_id,
            "location": entry.title,
            "count": len(data.threats),
            "updated_at": data.updated_at.isoformat(),
            "targets": [serialize_threat(item) for item in data.threats],
        }

    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_TARGETS,
        async_get_targets,
        schema=GET_TARGETS_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
