"""Tests for Air Threat Monitor response service actions."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import ServiceCall, SupportsResponse
from homeassistant.exceptions import ServiceValidationError

from custom_components.air_threat_monitor.const import (
    CONF_CONFIG_ENTRY_ID,
    DOMAIN,
    SERVICE_GET_TARGETS,
)
from custom_components.air_threat_monitor.models import (
    CalculatedThreat,
    GeoPoint,
    MonitorData,
    Threat,
    ThreatCategory,
)
from custom_components.air_threat_monitor.services import async_register_services


def _fake_hass() -> SimpleNamespace:
    return SimpleNamespace(
        services=MagicMock(),
        config_entries=MagicMock(),
    )


def _service_handler(hass: SimpleNamespace):
    async_register_services(hass)
    registration = hass.services.async_register.call_args
    assert registration.args[:2] == (DOMAIN, SERVICE_GET_TARGETS)
    assert registration.kwargs["supports_response"] is SupportsResponse.ONLY
    return registration.args[2]


def _monitor_data() -> MonitorData:
    threat = Threat(
        threat_id="target-1",
        position=GeoPoint(49.5, 34.5),
        category=ThreatCategory.UAV,
        title="БпЛА",
        locality="Полтава",
        district="Полтавський район",
        region="Полтавська область",
        heading=180.0,
        updated_at="2026-09-30T19:00:00Z",
        group_count=2,
    )
    calculated = CalculatedThreat(
        threat=threat,
        distance_km=42.4,
        bearing_from_home=90.0,
        bearing_to_home=270.0,
        screen_bearing=90.0,
        icon_rotation=180.0,
        approach_angle=90.0,
        is_approaching=False,
        risk_level="warning",
    )
    return MonitorData(
        threats=(calculated,),
        local_alert=None,
        raion=None,
        oblast=None,
        updated_at=datetime(2026, 9, 30, 19, 0, tzinfo=UTC),
    )


@pytest.mark.asyncio
async def test_get_targets_returns_complete_serialized_list() -> None:
    hass = _fake_hass()
    handler = _service_handler(hass)
    entry = SimpleNamespace(
        entry_id="entry-1",
        domain=DOMAIN,
        state=ConfigEntryState.LOADED,
        title="Полтава",
        runtime_data=SimpleNamespace(data=_monitor_data()),
    )
    hass.config_entries.async_get_entry.return_value = entry
    call = ServiceCall(
        hass,
        DOMAIN,
        SERVICE_GET_TARGETS,
        {CONF_CONFIG_ENTRY_ID: entry.entry_id},
        return_response=True,
    )

    response = await handler(call)

    assert response["config_entry_id"] == "entry-1"
    assert response["location"] == "Полтава"
    assert response["count"] == 1
    target = response["targets"][0]
    assert target["id"] == "target-1"
    assert target["distance_km"] == 42.4
    assert target["bearing_label"] == "Сх"
    assert target["bearing_arrow"] == "→"
    assert target["heading_arrow"] == "↓"
    assert target["bearing_to_home"] == 270.0
    assert "latitude" not in target
    assert "longitude" not in target


@pytest.mark.asyncio
async def test_get_targets_rejects_unknown_entry() -> None:
    hass = _fake_hass()
    handler = _service_handler(hass)
    hass.config_entries.async_get_entry.return_value = None
    call = ServiceCall(
        hass,
        DOMAIN,
        SERVICE_GET_TARGETS,
        {CONF_CONFIG_ENTRY_ID: "missing"},
        return_response=True,
    )

    with pytest.raises(ServiceValidationError):
        await handler(call)


@pytest.mark.asyncio
async def test_get_targets_rejects_unloaded_entry() -> None:
    hass = _fake_hass()
    handler = _service_handler(hass)
    hass.config_entries.async_get_entry.return_value = SimpleNamespace(
        domain=DOMAIN,
        state=ConfigEntryState.SETUP_ERROR,
    )
    call = ServiceCall(
        hass,
        DOMAIN,
        SERVICE_GET_TARGETS,
        {CONF_CONFIG_ENTRY_ID: "entry-1"},
        return_response=True,
    )

    with pytest.raises(ServiceValidationError):
        await handler(call)
