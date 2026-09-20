"""Tests for release metadata and bundled frontend assets."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "air_threat_monitor"


def test_release_versions_match() -> None:
    manifest = json.loads(
        (INTEGRATION / "manifest.json").read_text(encoding="utf-8")
    )
    constants = (INTEGRATION / "const.py").read_text(encoding="utf-8")
    match = re.search(r'^VERSION: Final = "([^"]+)"$', constants, re.MULTILINE)
    card = (
        INTEGRATION / "assets" / "air-threat-radar-card.js"
    ).read_text(encoding="utf-8")
    card_match = re.search(
        r'^const ASSET_VERSION = "([^"]+)";$',
        card,
        re.MULTILINE,
    )

    assert match is not None
    assert card_match is not None
    assert match.group(1) == manifest["version"]
    assert card_match.group(1) == manifest["version"]


def test_hacs_release_metadata() -> None:
    hacs = json.loads((ROOT / "hacs.json").read_text(encoding="utf-8"))

    assert hacs["country"] == "UA"
    assert hacs["zip_release"] is True
    assert hacs["filename"] == "air-threat-monitor.zip"
    assert (ROOT / "brand" / "logo.png").is_file()
    assert (ROOT / "brand" / "icon.png").is_file()
    assert (INTEGRATION / "brand" / "icon.png").is_file()
    assert (INTEGRATION / "brand" / "icon@2x.png").is_file()
    assert (INTEGRATION / "brand" / "logo.png").is_file()
    assert (INTEGRATION / "brand" / "logo@2x.png").is_file()

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "![Air Threat Monitor](brand/logo.png)" in readme
    assert "![Alert signal-color demo](docs/images/demo-alert-signal.png)" in readme
    screenshots = (
        "demo-safe-signal.png",
        "demo-alert-signal.png",
        "demo-safe-theme-dark.png",
        "demo-safe-theme-light.png",
        "card-editor.png",
    )
    for filename in screenshots:
        assert (ROOT / "docs" / "images" / filename).is_file()
        assert f"docs/images/{filename}" in readme
    assert "### Custom local status images" in readme
    assert "artwork_style: custom" in readme
    assert "safe_image: /local/air-threat-custom/safe.png" in readme
    assert "danger_image: /local/air-threat-custom/danger.png" in readme


def test_device_branding_is_provider_independent() -> None:
    entity = (INTEGRATION / "entity.py").read_text(encoding="utf-8")

    assert 'manufacturer="Air Threat Monitor"' in entity
    assert 'model="Air threat location monitor"' in entity
    assert "configuration_url=PROJECT_URL" in entity
    assert "NEPTUN data monitor" not in entity


def test_card_is_picker_registered_and_contains_demo_mode() -> None:
    card = (
        INTEGRATION / "assets" / "air-threat-radar-card.js"
    ).read_text(encoding="utf-8")

    assert "window.customCards" in card
    assert "registerCardMetadata();" in card
    assert "AirThreatRadarCardBootstrap" not in card
    assert "Object.assign(existing, registration)" in card
    assert 'data_mode: "live"' in card
    assert 'mode === "demo_alert"' in card
    assert 'mode === "demo_warning"' in card
    assert 'alert_level: warning ? "yellow"' in card
    assert 'warning: "ЖОВТИЙ РІВЕНЬ"' in card
    assert "#ffd24a" in card
    assert 'warning\n      ? "#17130a"' in card
    assert ".warning-image" in card
    assert "Unofficial data" in card
    assert "preview: false" in card
    assert "DATA UNAVAILABLE" in card
    assert "window.clearInterval(this._timer)" in card
    assert card.startswith('(() => {\n"use strict";')
    assert "status_since" in card
    assert "alert_level" in card
    assert "const AUTOMATIC_TARGET_LIMIT = 5;" in card
    assert "function selectVisibleTargets(" in card
    assert 'max_targets: "auto"' in card
    assert 'valueOr(this._config.max_targets, "auto")' in card
    assert "Автоматично (рекомендовано)" in card
    assert "До 5 цілей у радіусі." in card
    assert "nearby.slice(0, AUTOMATIC_TARGET_LIMIT)" in card
    assert "ordered.slice(0, 1)" in card
    assert "function compactDistrictName(" in card
    assert '.replace(/\\s+район(?=\\s|,|·|$)/i, " р-н")' in card
    assert 'class="place place-full" title=' in card
    assert 'class="place place-compact"' in card
    assert 'class="clock-icon"' in card
    assert 'class="status-time"' in card
    assert 'icon="mdi:clock-outline"' in card
    assert ".place-full { display:none; }" in card
    assert (
        ".place-compact { display:block; max-width:100%; overflow:visible;"
        in card
    )
    assert (
        ".area { margin-top:5px; display:grid; "
        "grid-template-columns:minmax(0,1fr);"
        in card
    )
    assert (
        ".from.separated { margin-left:0; padding-left:0; border-left:0; }"
        in card
    )
    assert (
        ".area { margin-top:5px; min-width:0; max-width:100%; display:grid;"
        in card
    )
    assert "container:air-threat-card / inline-size" not in card
    assert "@container air-threat-card (max-width:380px)" not in card
    assert "@media (max-width:380px)" in card
    assert 'animation:sweep 8s linear infinite' in card
    assert 'position_mode: "configured"' in card
    assert '"device", "tracker", "auto"' in card
    assert "geolocation.watchPosition" in card
    assert "geolocation.getCurrentPosition" in card
    assert "geolocation.clearWatch" in card
    assert 'orientation_mode: "north_up"' in card
    assert 'card_style: "signal"' in card
    assert 'const VALID_CARD_STYLES = new Set(["signal", "theme"]);' in card
    assert 'artwork_style: "standard"' in card
    assert (
        'const VALID_ARTWORK_STYLES = new Set(["standard", "custom"]);'
        in card
    )
    assert 'safe_image: ""' in card
    assert 'danger_image: ""' in card
    assert 'this._config.artwork_style === "custom"' in card
    assert "customStatusImageUrl" in card
    assert ': "standard";' in card
    assert 'value === undefined || value === null' in card
    assert "const statusSince = this._statusSince(data);" in card
    assert "this._dynamicStatusState = undefined;" in card
    assert 'geocoded_entity: ""' in card
    assert 'id="geocoded"' not in card
    assert "_dynamicPlaceName" not in card
    assert (
        'const displayArea = data.place_name || data.area || data.oblast || "";'
        in card
    )
    assert 'this._config.card_style === "theme"' in card
    assert "const signalWarning = warning && !themeStyle;" in card
    assert "const cardBackground = themeStyle" in card
    assert "const cardColor = themeStyle" in card
    assert "const mutedColor = themeStyle" in card
    assert "const dividerColor = themeStyle" in card
    assert "const panelBackground = themeStyle" in card
    assert "const chipBackground = themeStyle" in card
    assert "var(--ha-card-background" in card
    assert "var(--primary-text-color" in card
    assert 'class="status-marker${warning ? " warning-image" : ""}"' in card
    assert "this._hass.themes.darkMode === false" in card
    assert "item.image_light_url" in card
    assert 'filter:${signalWarning || lightTheme ? "none"' in card
    assert '${signalWarning ? ".analytics b { color:#17130a; }" : ""}' in card
    assert "rgba(255,255,255,.075)" in card
    assert "min-height:28px" in card
    assert "За темою Home Assistant" in card
    assert "Живий GPS цього пристрою" in card
    assert "deviceorientationabsolute" in card
    assert "function isMobileClient()" in card
    assert "function isLinuxDesktopClient()" in card
    assert "function supportsMobileCompass()" in card
    assert "window.isSecureContext" in card
    assert "navigatorObject.maxTouchPoints" in card
    assert "iosDevice || androidDevice" in card
    assert "userAgentData.mobile === false" in card
    assert "chromiumReportsDesktop" in card
    assert "!chromiumReportsDesktop" in card
    assert "!linuxDesktop" in card
    assert 'if (isLinuxDesktopClient()) return "configured";' in card
    assert 'id="artwork-style"' not in card
    assert "SNAPSHOT_CACHE_MAX_AGE_MS = 30 * 60 * 1000" in card
    assert "DEGRADED_SNAPSHOT_GRACE_MS = 60 * 1000" in card
    assert "function degradedSnapshotWithinGrace(snapshot)" in card
    assert "const delayedData = degradedSnapshotWithinGrace(data);" in card
    assert "data.available === false && !delayedData" in card
    assert "dataDelayed" in card
    assert 'class="cache-state delayed"' in card
    assert "_snapshotCacheKey()" in card
    assert "_restoreSnapshotCache()" in card
    assert "_storeSnapshotCache(snapshot)" in card
    assert "this._snapshotFromCache = Boolean(this._snapshot);" in card
    assert "cachedUpdating" in card
    assert "safeErrorText(error)" in card
    assert 'const alertMarkerUrl = assetUrl("danger.png");' in card
    assert (
        'class="status-marker${warning ? " warning-image" : ""}" '
        'src="${escapeHtml(alertMarkerUrl)}"'
        in card
    )
    assert 'return isMobileClient() ? "device" : "configured";' in card
    assert 'id="position-source"' in card
    assert 'id="position-mode"' not in card
    assert 'id="location"' not in card
    assert 'selection.startsWith("configured:")' in card
    assert 'position_mode: "configured"' in card
    assert 'entry_id: selection.slice("configured:".length)' in card
    assert 'requestedMode === "north_up"' in card
    assert "|| !supportsMobileCompass()" in card
    assert 'this._compassState === "unavailable"' in card
    assert (
        '["idle", "prompt", "denied", "checking"].includes('
        "this._compassState)"
        in card
    )
    assert "position_accuracy_m" in card
    assert "message.use_current_user_tracker = true" in card
    assert "deviceLocationFallbackUnavailable" in card
    assert "automaticLocationFallback" in card
    assert "_automaticPositionStorageKey" in card
    assert 'window.localStorage.setItem(key, "configured")' in card
    assert "useFixedLocation" in card
    assert "retryGps" in card
    assert '"device_compass", "auto"' in card
    assert "_effectiveOrientationMode" in card
    assert "device_location_timeout" in card
    assert "message.tracker_entity = this._config.tracker_entity" in card
    assert "targetDisplayTitle(nearest, t)" in card
    assert 'noActiveTargets: "Активних цілей немає"' in card
    assert "totalTargets <= 0" in card
    assert 'class="chip nearest-chip more-info-zone"' in card
    assert (
        'nearest ? `<div class="chip nearest-chip more-info-zone"'
        in card
    )
    assert (
        "${escapeHtml(targetDisplayTitle(nearest, t))} "
        "≈${Math.round(nearest.distance_km)}"
        in card
    )
    assert (
        "${escapeHtml(targetDisplayTitle(nearest, t))} · "
        "≈${Math.round(nearest.distance_km)}"
        not in card
    )
    assert " : t.noTargets" not in card
    assert '_bindMoreInfo(".status-copy", entityIds.air_alert)' in card
    assert (
        '_bindMoreInfo(".nearest-chip, .visual", '
        "entityIds.nearest_threat)"
        in card
    )
    assert (
        '_bindMoreInfo(".list, .analytics", entityIds.active_threats)'
        in card
    )
    assert 'new CustomEvent("hass-more-info"' in card
    assert "detail: { entityId }" in card
    assert "compass-enable" in card
    assert "Доступ до компаса заборонено" in card
    assert "this._compassStarting = false;" in card
    assert 'this._compassState = "checking";' in card
    assert 'error.name === "NotAllowedError"' in card
    assert 'compassWaiting: "Очікування компаса"' in card
    assert "_waitForCompassReading()" in card
    assert "this._compassReadyTimer = window.setTimeout" in card
    assert "}, 3000);" in card
    assert 'this._compassState = "prompt";' in card
    assert 'this._compassState = "active";' in card
    assert 'document.addEventListener("visibilitychange"' in card
    assert 'document.removeEventListener("visibilitychange"' in card
    assert "_handleVisibilityChange()" in card
    assert "this._lastCompassUpdate = undefined;" in card
    assert 'if (!requestPermission) {' not in card
    assert (
        "linear-gradient(135deg, #3f0303 0%, #8b0000 50%, #c1121f 100%)"
        in card
    )
    assert (
        "linear-gradient(135deg, #1f6f2b 0%, #358d32 55%, #43a047 100%)"
        in card
    )
    assert "radar-world" in card
    assert "distanceUnit" in card
    assert "function targetIconRotation(target)" in card
    assert "const rotation = targetIconRotation(item);" in card
    assert "configuredLocationExists" in card
    assert "configuredLocation || locations[0]" in card
    assert "registerOrUpgradeElement" not in card
    assert card.index(
        "customElements.define(CARD_TYPE, AirThreatRadarCard);"
    ) < card.index(
        "customElements.define(EDITOR_TYPE, AirThreatRadarCardEditor);"
    )
    assert (
        'style="transform:rotate(calc(${rotation}deg - '
        'var(--atm-compass-heading, 0deg)))"' in card
    )
    grid_options = re.search(
        r"getGridOptions\(\)\s*\{\s*return\s*\{(?P<body>.*?)\};",
        card,
        re.DOTALL,
    )
    assert grid_options is not None
    assert "rows:" not in grid_options.group("body")


def test_tracker_coordinates_are_resolved_by_home_assistant() -> None:
    websocket = (
        INTEGRATION / "websocket.py"
    ).read_text(encoding="utf-8")

    assert 'vol.Optional("tracker_entity")' in websocket
    assert "hass.states.get(tracker_entity)" in websocket
    assert '"tracker_unavailable"' in websocket
    assert '"position_source": position_source' in websocket
    assert "_automatic_tracker_place_name(hass, tracker_entity)" in websocket
    assert "_live_device_place_name(hass, connection, point)" in websocket
    assert 'state.attributes.get("user_id")' in websocket
    assert "_LIVE_PLACE_MAX_DISTANCE_KM = 5.0" in websocket
    assert "distance_km(point, person_point)" in websocket
    assert 'vol.Optional("use_current_user_tracker", default=False)' in websocket
    assert "_person_entity_for_connection(hass, connection)" in websocket
    assert '"user_tracker_unavailable"' in websocket
    assert '"place_name": place_name' in websocket
    assert "source_entry.device_id" in websocket
    assert "coordinator.status_since_for_area(" in websocket
    assert "dynamic_status_since.isoformat()" in websocket
    assert "def _entry_entity_ids(" in websocket
    assert '"entity_ids": entity_ids or {}' in websocket
    assert 'f"{entry_id}_air_alert": "air_alert"' in websocket
    assert 'f"{entry_id}_nearest_threat": "nearest_threat"' in websocket
    assert 'f"{entry_id}_active_threats": "active_threats"' in websocket

    coordinator = (
        INTEGRATION / "coordinator.py"
    ).read_text(encoding="utf-8")
    assert "self._area_status_states" in coordinator
    assert "self._area_status_keys" in coordinator
    assert "def status_since_for_area(" in coordinator
    assert "area_alert = find_local_alert(" in coordinator
    assert '"areas": {}' in coordinator
    assert "await self._status_store.async_save(" in coordinator


def test_all_target_images_are_bundled() -> None:
    images = INTEGRATION / "assets" / "images"

    for filename in (
        "fpv.png",
        "fpv-b.png",
        "shahed.png",
        "shahed-b.png",
        "rocket.png",
        "rocket-b.png",
        "recon.png",
        "recon-b.png",
        "kab.png",
        "kab-b.png",
        "jet.png",
        "jet-b.png",
    ):
        assert (images / filename).stat().st_size > 0

    assert sorted(
        path.name
        for path in images.iterdir()
        if path.name.startswith(("safe-", "danger-"))
    ) == []


def test_light_theme_target_images_are_exposed() -> None:
    websocket = (
        INTEGRATION / "websocket.py"
    ).read_text(encoding="utf-8")

    assert "_CATEGORY_IMAGE_LIGHT" in websocket
    assert '"image_light_url"' in websocket
    for filename in (
        "fpv-b.png",
        "shahed-b.png",
        "rocket-b.png",
        "recon-b.png",
        "kab-b.png",
        "jet-b.png",
    ):
        assert filename in websocket


def test_card_resource_is_registered_in_lovelace_storage() -> None:
    setup = (INTEGRATION / "__init__.py").read_text(encoding="utf-8")
    manifest = json.loads(
        (INTEGRATION / "manifest.json").read_text(encoding="utf-8")
    )

    assert "lovelace" in manifest["dependencies"]
    assert "resources.async_create_item" in setup
    assert "resources.async_update_item" in setup
    assert '{"res_type": "module", "url": CARD_MODULE_URL}' in setup
    assert "add_extra_js_url" not in setup
