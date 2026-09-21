"""Air Threat Monitor integration."""

from __future__ import annotations

import logging
import re
import voluptuous as vol

from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace.const import LOVELACE_DATA, MODE_STORAGE
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AirThreatApiClient
from .const import (
    CARD_MODULE_URL,
    CONFIG_ENTRY_MINOR_VERSION,
    CONFIG_ENTRY_VERSION,
    DEFAULT_ENTRY_TITLE,
    SERVICE_GET_TARGETS,
    STATIC_URL,
)
from .const import DOMAIN as DOMAIN
from .coordinator import AirThreatCoordinator
from .websocket import async_register_websocket_api, _serialize_threat

PLATFORMS = (Platform.BINARY_SENSOR, Platform.SENSOR)

_LOGGER = logging.getLogger(__name__)

AirThreatConfigEntry = ConfigEntry[AirThreatCoordinator]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

_COORDINATE_TITLE = re.compile(
    r"^\s*[+-]?(?:\d+(?:\.\d+)?|\.\d+)\s*,\s*"
    r"[+-]?(?:\d+(?:\.\d+)?|\.\d+)\s*$"
)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up static integration resources."""

    assets_path = Path(__file__).parent / "assets"
    await hass.http.async_register_static_paths(
        [StaticPathConfig(STATIC_URL, str(assets_path), True)]
    )
    try:
        await _async_register_card_resource(hass)
    except Exception:  # noqa: BLE001
        _LOGGER.exception(
            "Failed to register the bundled Lovelace card resource"
        )
    async_register_websocket_api(hass)
    return True


async def _async_register_card_resource(hass: HomeAssistant) -> None:
    """Register or update the bundled card in Lovelace storage."""

    lovelace = hass.data.get(LOVELACE_DATA)
    if lovelace is None:
        _LOGGER.warning(
            "Lovelace is unavailable; the bundled card could not be registered"
        )
        return

    if lovelace.resource_mode != MODE_STORAGE:
        _LOGGER.info(
            "Lovelace resources use YAML mode; automatic card resource "
            "registration is unavailable"
        )
        return

    resources = lovelace.resources
    await resources.async_get_info()

    card_path = CARD_MODULE_URL.split("?", 1)[0]
    matches = [
        item
        for item in resources.async_items()
        if str(item.get("url", "")).split("?", 1)[0] == card_path
    ]

    if not matches:
        await resources.async_create_item(
            {"res_type": "module", "url": CARD_MODULE_URL}
        )
        _LOGGER.info("Registered bundled Lovelace card resource")
        return

    primary = matches[0]
    if primary.get("url") != CARD_MODULE_URL or primary.get("type") != "module":
        await resources.async_update_item(
            primary["id"],
            {"res_type": "module", "url": CARD_MODULE_URL},
        )
        _LOGGER.info("Updated bundled Lovelace card resource")

    for duplicate in matches[1:]:
        await resources.async_delete_item(duplicate["id"])
        _LOGGER.info("Removed duplicate bundled Lovelace card resource")


async def async_setup_entry(
    hass: HomeAssistant, entry: AirThreatConfigEntry
) -> bool:
    """Set up Air Threat Monitor from a config entry."""

    client = AirThreatApiClient(async_get_clientsession(hass))
    coordinator = AirThreatCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    async def async_handle_get_targets(call: ServiceCall) -> dict[str, any]:
        if not coordinator or not coordinator.data or not coordinator.data.threats:
            return {"targets": []}
        serialized_targets = [
            _serialize_threat(item) for item in coordinator.data.threats
        ]
        return {"targets": serialized_targets}
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_TARGETS,
        async_handle_get_targets,
        schema=vol.Schema({}),
        supports_response=SupportsResponse.ONLY,
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_migrate_entry(
    hass: HomeAssistant, entry: AirThreatConfigEntry
) -> bool:
    """Remove coordinate-based names created by the first beta."""

    if entry.version > CONFIG_ENTRY_VERSION:
        return False
    if (
        entry.version == CONFIG_ENTRY_VERSION
        and entry.minor_version >= CONFIG_ENTRY_MINOR_VERSION
    ):
        return True

    changes: dict[str, object] = {
        "version": CONFIG_ENTRY_VERSION,
        "minor_version": CONFIG_ENTRY_MINOR_VERSION,
    }
    if _COORDINATE_TITLE.fullmatch(entry.title):
        changes["title"] = DEFAULT_ENTRY_TITLE
    hass.config_entries.async_update_entry(entry, **changes)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: AirThreatConfigEntry
) -> bool:
    """Unload an Air Threat Monitor config entry."""

    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
