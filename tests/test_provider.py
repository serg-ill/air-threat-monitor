"""Shared polling, per-location behavior, and lifecycle regression tests."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.air_threat_monitor import async_setup_entry
from custom_components.air_threat_monitor.api import (
    AirThreatApiClient,
    AirThreatApiError,
)
from custom_components.air_threat_monitor.const import DOMAIN
from custom_components.air_threat_monitor.coordinator import AirThreatCoordinator
from custom_components.air_threat_monitor.models import AlertLevel, GeoPoint
from custom_components.air_threat_monitor.provider import (
    AirThreatProvider,
    async_get_provider,
)


def _boundaries():
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"key": f"test-{index}", "name": f"Test {index}"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [30 + index, 49],
                            [31 + index, 49],
                            [31 + index, 50],
                            [30 + index, 50],
                            [30 + index, 49],
                        ]
                    ],
                },
            }
            for index in range(3)
        ],
    }


@pytest.fixture
def client():
    client = AsyncMock(spec=AirThreatApiClient)
    client.async_get_raions.return_value = _boundaries()
    client.async_get_oblasts.return_value = {
        "type": "FeatureCollection",
        "features": [],
    }
    client.async_get_threats.return_value = {
        "threats": [
            {
                "id": "test-target",
                "type": "uav",
                "lat": 49.5,
                "lon": 30.6,
                "heading": 90,
                "count": 2,
                "status": "active",
            },
        ]
    }
    client.async_get_alerts.return_value = {
        "raions": [
            {"key": "test-0", "level": "yellow", "since": "2026-01-01T10:00:00Z"},
        ],
        "oblasts": [],
    }
    return client


async def _location(hass, provider, index=0, *, polling=True):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"latitude": 49.5, "longitude": 30.5 + index},
        pref_disable_polling=not polling,
    )
    entry.add_to_hass(hass)
    entry._async_set_state(hass, ConfigEntryState.SETUP_IN_PROGRESS, None)
    await provider.async_ensure_ready()
    coordinator = AirThreatCoordinator(hass, entry, provider)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    entry.async_on_unload(coordinator.async_connect_provider())
    entry._async_set_state(hass, ConfigEntryState.LOADED, None)
    return entry, coordinator


@pytest.fixture
async def provider(hass, client):
    provider = AirThreatProvider(hass, client)
    await provider.async_register_shutdown()
    yield provider
    await provider.async_shutdown()


@pytest.fixture(autouse=True)
async def unload_entries(hass):
    yield
    await hass.async_block_till_done(wait_background_tasks=True)
    for entry in hass.config_entries.async_entries(DOMAIN):
        await entry._async_process_on_unload(hass)


@pytest.mark.asyncio
async def test_three_locations_share_startup_and_each_poll(hass, client, provider):
    locations = await asyncio.gather(
        *(_location(hass, provider, index) for index in range(3))
    )
    assert client.async_get_threats.await_count == 1
    assert client.async_get_alerts.await_count == 1
    assert client.async_get_raions.await_count == 1
    assert client.async_get_oblasts.await_count == 1
    assert all(c.update_interval is None for _, c in locations)

    first, second, third = [c for _, c in locations]
    assert first.data.local_alert.level is AlertLevel.YELLOW
    assert first.data.status_since == datetime(2026, 1, 1, 10, tzinfo=UTC)
    assert second.data.local_alert is None
    assert third.data.local_alert is None
    assert (
        first.data.threats[0].distance_km
        < second.data.threats[0].distance_km
        < third.data.threats[0].distance_km
    )
    assert first.data.updated_at == second.data.updated_at == third.data.updated_at
    before = first.data.status_since
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=11))
    await hass.async_block_till_done(wait_background_tasks=True)
    assert client.async_get_threats.await_count == 2
    assert client.async_get_alerts.await_count == 2
    assert client.async_get_raions.await_count == 1
    assert first.data.status_since == before


@pytest.mark.asyncio
async def test_failures_retain_snapshot_mark_all_unavailable_then_recover(
    hass,
    client,
    provider,
):
    locations = [await _location(hass, provider, i) for i in range(3)]
    previous = [c.data for _, c in locations]
    client.async_get_alerts.side_effect = AirThreatApiError("test provider failure")
    await provider.async_refresh()
    await hass.async_block_till_done(wait_background_tasks=True)
    assert all(not c.last_update_success for _, c in locations)
    assert [c.data for _, c in locations] == previous
    assert all(
        c.data.updated_at == old.updated_at
        for (_, c), old in zip(locations, previous, strict=True)
    )
    client.async_get_alerts.side_effect = None
    client.async_get_alerts.return_value = {"raions": [], "oblasts": []}
    await provider.async_refresh()
    await hass.async_block_till_done(wait_background_tasks=True)
    assert all(c.last_update_success for _, c in locations)
    assert all(c.data.local_alert is None for _, c in locations)
    assert client.async_get_threats.await_count == 3
    assert client.async_get_alerts.await_count == 3


@pytest.mark.asyncio
async def test_unloading_first_entry_keeps_polling_for_second_then_stops(
    hass,
    client,
    provider,
):
    first, _ = await _location(hass, provider)
    second, coordinator = await _location(hass, provider, 1)
    await first._async_process_on_unload(hass)
    assert provider._unsub_refresh is not None
    assert len(provider._listeners) == 1
    client.async_get_threats.return_value = {"threats": []}
    await provider.async_refresh()
    await hass.async_block_till_done(wait_background_tasks=True)
    assert coordinator.data.threats == ()
    await second._async_process_on_unload(hass)
    assert provider._unsub_refresh is None
    assert not provider._listeners
    calls = client.async_get_threats.await_count
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=30))
    await hass.async_block_till_done(wait_background_tasks=True)
    assert client.async_get_threats.await_count == calls


@pytest.mark.asyncio
async def test_disabled_polling_and_manual_update(hass, client, provider):
    _, coordinator = await _location(hass, provider, polling=False)
    assert not provider._listeners
    assert provider._unsub_refresh is None
    client.async_get_threats.return_value = {"threats": []}
    await coordinator.async_request_refresh()
    assert coordinator.data.threats == ()
    assert client.async_get_threats.await_count == 2


@pytest.mark.asyncio
async def test_dynamic_location_and_alert_levels_are_unchanged(hass, client, provider):
    _, coordinator = await _location(hass, provider, 1)
    targets, alert, raion, oblast = coordinator.calculate_for_point(
        GeoPoint(49.5, 30.5)
    )
    assert targets[0].threat.group_count == 2
    assert alert.level is AlertLevel.YELLOW
    assert coordinator.status_since_for_area(raion, oblast, alert) == datetime(
        2026, 1, 1, 10, tzinfo=UTC
    )
    client.async_get_alerts.return_value = {
        "raions": [
            {"key": "test-0", "level": "red", "since": "2026-01-01T11:00:00Z"},
        ],
        "oblasts": [],
    }
    await provider.async_refresh()
    await hass.async_block_till_done(wait_background_tasks=True)
    _, alert, raion, oblast = coordinator.calculate_for_point(GeoPoint(49.5, 30.5))
    assert alert.level is AlertLevel.RED
    assert coordinator.status_since_for_area(raion, oblast, alert) == datetime(
        2026, 1, 1, 11, tzinfo=UTC
    )


@pytest.mark.asyncio
async def test_startup_failure_is_shared_and_can_retry(hass, client, provider):
    client.async_get_threats.side_effect = AirThreatApiError("test startup failure")
    results = await asyncio.gather(
        *(provider.async_ensure_ready() for _ in range(3)), return_exceptions=True
    )
    assert all(isinstance(result, UpdateFailed) for result in results)
    assert client.async_get_threats.await_count == 1
    assert provider.data is None
    assert provider._unsub_refresh is None
    client.async_get_threats.side_effect = None
    provider._last_attempt -= 11
    await provider.async_ensure_ready()
    assert provider.last_update_success
    assert client.async_get_threats.await_count == 2


@pytest.mark.asyncio
async def test_singleton_is_scoped_to_home_assistant_and_not_entry(hass, client):
    with patch(
        "custom_components.air_threat_monitor.provider.AirThreatApiClient",
        return_value=client,
    ):
        first, second = await asyncio.gather(
            async_get_provider(hass), async_get_provider(hass)
        )
    assert first is second
    assert first.config_entry is None
    assert first._unsub_shutdown is not None


@pytest.mark.asyncio
async def test_setup_entry_shares_provider_and_registers_cleanup(hass, client):
    with (
        patch(
            "custom_components.air_threat_monitor.provider.AirThreatApiClient",
            return_value=client,
        ),
        patch.object(
            hass.config_entries, "async_forward_entry_setups", new=AsyncMock()
        ),
    ):
        entries = []
        for i in range(3):
            entry = MockConfigEntry(
                domain=DOMAIN,
                data={
                    "latitude": 49.5,
                    "longitude": 30.5 + i,
                },
            )
            entry.add_to_hass(hass)
            entry._async_set_state(hass, ConfigEntryState.SETUP_IN_PROGRESS, None)
            assert await async_setup_entry(hass, entry)
            entries.append(entry)
        assert len({id(e.runtime_data.provider) for e in entries}) == 1
        assert client.async_get_threats.await_count == 1
        for entry in entries:
            await entry._async_process_on_unload(hass)
        assert not entries[0].runtime_data.provider._listeners


@pytest.mark.asyncio
async def test_setup_failure_is_retriable(hass, client):
    client.async_get_raions.side_effect = AirThreatApiError("test failure")
    entry = MockConfigEntry(domain=DOMAIN, data={"latitude": 49.5, "longitude": 30.5})
    entry.add_to_hass(hass)
    with (
        patch(
            "custom_components.air_threat_monitor.provider.AirThreatApiClient",
            return_value=client,
        ),
        pytest.raises(ConfigEntryNotReady),
    ):
        await async_setup_entry(hass, entry)


@pytest.mark.asyncio
async def test_setup_during_inflight_poll_waits_without_another_fetch(
    hass,
    client,
    provider,
):
    await provider.async_ensure_ready()
    provider._last_attempt -= 11
    started = asyncio.Event()
    release = asyncio.Event()

    async def delayed_threats():
        started.set()
        await release.wait()
        return {"threats": []}

    client.async_get_threats.side_effect = delayed_threats
    refresh = asyncio.create_task(provider.async_refresh())
    await started.wait()
    setup = asyncio.create_task(provider.async_ensure_ready())
    await asyncio.sleep(0)
    assert not setup.done()
    release.set()
    await asyncio.gather(refresh, setup)
    assert client.async_get_threats.await_count == 2
    assert provider.snapshot().threats == {"threats": []}


@pytest.mark.asyncio
async def test_reloading_location_preserves_observed_status_time(
    hass, client, provider
):
    client.async_get_alerts.return_value = {"raions": [], "oblasts": []}
    entry, original = await _location(hass, provider)
    since = original.data.status_since
    await entry._async_process_on_unload(hass)
    entry._async_set_state(hass, ConfigEntryState.SETUP_IN_PROGRESS, None)
    reloaded = AirThreatCoordinator(hass, entry, provider)
    await reloaded.async_config_entry_first_refresh()
    entry.async_on_unload(reloaded.async_connect_provider())
    assert reloaded.data.status_since == since
    assert reloaded.data.threats == original.data.threats
    assert client.async_get_threats.await_count == 1


@pytest.mark.asyncio
async def test_diagnostics_keep_interval_and_redact_location(hass, provider):
    from custom_components.air_threat_monitor.diagnostics import (
        async_get_config_entry_diagnostics,
    )

    entry, _ = await _location(hass, provider)
    result = await async_get_config_entry_diagnostics(hass, entry)
    assert result["coordinator"]["update_interval_seconds"] == 10
    assert result["entry"] == {"latitude": "**REDACTED**", "longitude": "**REDACTED**"}
