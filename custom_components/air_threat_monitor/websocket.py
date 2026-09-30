"""WebSocket API used by the bundled dashboard card."""

from __future__ import annotations

from collections import Counter
from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er

from .calculations import direction_arrow, direction_label, distance_km
from .const import ATTRIBUTION, DOMAIN, asset_url
from .coordinator import AirThreatCoordinator
from .models import (
    ActiveAlert,
    CalculatedThreat,
    GeoPoint,
    ResolvedArea,
    ThreatCategory,
)

_CATEGORY_IMAGE = {
    ThreatCategory.UAV: "shahed.png",
    ThreatCategory.FPV: "fpv.png",
    ThreatCategory.RECON: "recon.png",
    ThreatCategory.MISSILE: "rocket.png",
    ThreatCategory.BALLISTIC: "rocket.png",
    ThreatCategory.KAB: "kab.png",
    ThreatCategory.AIRCRAFT: "jet.png",
}

_CATEGORY_IMAGE_LIGHT = {
    ThreatCategory.UAV: "shahed-b.png",
    ThreatCategory.FPV: "fpv-b.png",
    ThreatCategory.RECON: "recon-b.png",
    ThreatCategory.MISSILE: "rocket-b.png",
    ThreatCategory.BALLISTIC: "rocket-b.png",
    ThreatCategory.KAB: "kab-b.png",
    ThreatCategory.AIRCRAFT: "jet-b.png",
}

_UNKNOWN_STATES = {"", "unknown", "unavailable", "none"}
_LIVE_PLACE_MAX_DISTANCE_KM = 5.0
_PLACE_ATTRIBUTE_PRIORITY = (
    "locality",
    "sub_locality",
    "sub_administrative_area",
    "administrative_area",
)


def _normalized_attributes(attributes: dict[str, Any]) -> dict[str, Any]:
    """Normalize Companion App geocoded attribute names."""

    return {
        str(key).strip().lower().replace(" ", "_").replace("-", "_"): value
        for key, value in attributes.items()
    }


def _place_name_from_geocoded_state(state: Any) -> str | None:
    """Extract a city, town, or village from a geocoded-location sensor."""

    attributes = _normalized_attributes(dict(state.attributes))
    for key in _PLACE_ATTRIBUTE_PRIORITY:
        raw_value = attributes.get(key)
        if raw_value is None:
            continue
        value = str(raw_value).strip()
        if value.lower() not in _UNKNOWN_STATES:
            return value
    return None


def _automatic_tracker_place_name(
    hass: HomeAssistant,
    tracker_entity: str,
) -> str | None:
    """Find the geocoded locality attached to the selected tracker's device."""

    selected_state = hass.states.get(tracker_entity)
    source_entity = tracker_entity
    if tracker_entity.startswith("person.") and selected_state is not None:
        source = selected_state.attributes.get("source")
        if isinstance(source, str) and source.startswith("device_tracker."):
            source_entity = source

    registry = er.async_get(hass)
    source_entry = registry.async_get(source_entity)
    if source_entry is None or source_entry.device_id is None:
        return None

    candidates: list[tuple[int, str]] = []
    for entity_entry in registry.entities.values():
        entity_id = entity_entry.entity_id
        if (
            entity_entry.device_id != source_entry.device_id
            or not entity_id.startswith("sensor.")
        ):
            continue

        state = hass.states.get(entity_id)
        if state is None or str(state.state).strip().lower() in _UNKNOWN_STATES:
            continue

        identity = " ".join(
            str(value or "").lower()
            for value in (
                entity_id,
                entity_entry.unique_id,
                getattr(entity_entry, "translation_key", None),
                getattr(entity_entry, "original_name", None),
            )
        )
        attributes = _normalized_attributes(dict(state.attributes))
        is_geocoded = (
            "geocoded_location" in identity
            or "geocoded location" in identity
            or (
                "locality" in attributes
                and (
                    "administrative_area" in attributes
                    or "iso_country_code" in attributes
                )
            )
        )
        if not is_geocoded:
            continue

        place_name = _place_name_from_geocoded_state(state)
        if place_name:
            priority = 0 if "geocoded" in identity else 1
            candidates.append((priority, place_name))

    return min(candidates)[1] if candidates else None


def _person_entity_for_connection(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
) -> str | None:
    """Find the person entity linked to the authenticated Home Assistant user."""

    user_id = str(getattr(getattr(connection, "user", None), "id", "") or "")
    if not user_id:
        return None

    for state in hass.states.async_all():
        if (
            state.entity_id.startswith("person.")
            and str(state.attributes.get("user_id") or "") == user_id
        ):
            return state.entity_id
    return None


def _state_point(state: Any) -> GeoPoint | None:
    """Read valid coordinates from a Home Assistant state."""

    attributes = state.attributes if state is not None else {}
    try:
        latitude = float(attributes["latitude"])
        longitude = float(attributes["longitude"])
    except (KeyError, TypeError, ValueError):
        return None
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        return None
    return GeoPoint(latitude=latitude, longitude=longitude)


def _live_device_place_name(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    point: GeoPoint,
) -> str | None:
    """Resolve the viewing user's locality without external geocoding."""

    person_entity = _person_entity_for_connection(hass, connection)
    if person_entity is None:
        return None

    person_state = hass.states.get(person_entity)
    person_point = _state_point(person_state)
    if (
        person_point is None
        or distance_km(point, person_point) > _LIVE_PLACE_MAX_DISTANCE_KM
    ):
        return None
    return _automatic_tracker_place_name(hass, person_entity)


def serialize_threat(item: CalculatedThreat) -> dict[str, Any]:
    """Convert a calculated threat to frontend-safe data."""

    threat = item.threat
    image = _CATEGORY_IMAGE.get(threat.category)
    light_image = _CATEGORY_IMAGE_LIGHT.get(threat.category)
    return {
        "id": threat.threat_id,
        "category": threat.category.value,
        "title": threat.title,
        "locality": threat.locality,
        "district": threat.district,
        "region": threat.region,
        "distance_km": round(item.distance_km, 1),
        "bearing": round(item.bearing_from_home, 1),
        "bearing_from_home": round(item.bearing_from_home, 1),
        "bearing_to_home": round(item.bearing_to_home, 1),
        "bearing_label": direction_label(item.bearing_from_home),
        "bearing_arrow": direction_arrow(item.bearing_from_home),
        "heading": round(threat.heading, 1) if threat.heading is not None else None,
        "heading_arrow": (
            direction_arrow(threat.heading)
            if threat.heading is not None
            else None
        ),
        "screen_bearing": round(item.screen_bearing, 1),
        "icon_rotation": (
            round(item.icon_rotation, 1) if item.icon_rotation is not None else None
        ),
        "approach_angle": (
            round(item.approach_angle, 1)
            if item.approach_angle is not None
            else None
        ),
        "is_approaching": item.is_approaching,
        "risk_level": item.risk_level,
        "group_count": threat.group_count,
        "status": threat.status,
        "image_url": asset_url(f"images/{image}") if image else None,
        "image_light_url": (
            asset_url(f"images/{light_image}") if light_image else None
        ),
        "updated_at": threat.updated_at,
    }


def _entry_entity_ids(
    hass: HomeAssistant,
    entry_id: str,
) -> dict[str, str]:
    """Return current entity IDs even when a user renamed the entities."""

    expected = {
        f"{entry_id}_air_alert": "air_alert",
        f"{entry_id}_nearest_threat": "nearest_threat",
        f"{entry_id}_active_threats": "active_threats",
    }
    entity_ids: dict[str, str] = {}
    registry = er.async_get(hass)
    for entity_entry in registry.entities.values():
        key = expected.get(entity_entry.unique_id)
        if key and entity_entry.config_entry_id == entry_id:
            entity_ids[key] = entity_entry.entity_id
    return entity_ids


def _snapshot(
    coordinator: AirThreatCoordinator,
    *,
    threats: tuple[CalculatedThreat, ...] | None = None,
    alert: ActiveAlert | None = None,
    raion: ResolvedArea | None = None,
    oblast: ResolvedArea | None = None,
    dynamic_position: bool = False,
    position_accuracy_m: float | None = None,
    position_source: str | None = None,
    place_name: str | None = None,
    entity_ids: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build the compact snapshot consumed by the card."""

    data = coordinator.data
    selected_threats = data.threats if threats is None else threats
    selected_alert = data.local_alert if not dynamic_position else alert
    selected_raion = data.raion if not dynamic_position else raion
    selected_oblast = data.oblast if not dynamic_position else oblast
    categories = Counter(item.threat.category.value for item in selected_threats)
    area = selected_raion or selected_oblast
    if dynamic_position:
        dynamic_status_since = coordinator.status_since_for_area(
            selected_raion,
            selected_oblast,
            selected_alert,
        )
        status_since = (
            dynamic_status_since.isoformat()
            if dynamic_status_since
            else None
        )
    else:
        status_since = (
            data.status_since.isoformat() if data.status_since else None
        )
    return {
        "available": coordinator.last_update_success,
        "alert_active": selected_alert is not None,
        "alert_since": selected_alert.since if selected_alert else None,
        "alert_level": selected_alert.level.value if selected_alert else None,
        "alert_reasons": list(selected_alert.reasons) if selected_alert else [],
        "status_since": status_since,
        "area": (
            selected_alert.name
            if selected_alert and selected_alert.name
            else area.name
            if area and area.name
            else None
        ),
        "oblast": (
            selected_alert.oblast
            if selected_alert and selected_alert.oblast
            else area.oblast
            if area and area.oblast
            else None
        ),
        "status_image_url": asset_url(
            f"images/{'danger.png' if selected_alert else 'safe.png'}"
        ),
        "updated_at": data.updated_at.isoformat(),
        "attribution": ATTRIBUTION,
        "entity_ids": entity_ids or {},
        "dynamic_position": dynamic_position,
        "position_source": position_source,
        "place_name": place_name,
        "position_accuracy_m": (
            round(position_accuracy_m)
            if position_accuracy_m is not None
            else None
        ),
        "targets": [serialize_threat(item) for item in selected_threats],
        "analytics": {
            "total": len(selected_threats),
            "within_100_km": sum(
                item.distance_km <= 100 for item in selected_threats
            ),
            "within_50_km": sum(
                item.distance_km <= 50 for item in selected_threats
            ),
            "within_20_km": sum(
                item.distance_km <= 20 for item in selected_threats
            ),
            "approaching": sum(
                item.is_approaching is True for item in selected_threats
            ),
            "stale": sum(
                item.threat.status == "stale" for item in selected_threats
            ),
            "uav": categories[ThreatCategory.UAV.value],
            "fpv": categories[ThreatCategory.FPV.value],
            "recon": categories[ThreatCategory.RECON.value],
            "missile": categories[ThreatCategory.MISSILE.value],
            "ballistic": categories[ThreatCategory.BALLISTIC.value],
            "kab": categories[ThreatCategory.KAB.value],
            "aircraft": categories[ThreatCategory.AIRCRAFT.value],
            "unknown": categories[ThreatCategory.UNKNOWN.value],
        },
    }


@callback
def async_register_websocket_api(hass: HomeAssistant) -> None:
    """Register card discovery and snapshot commands."""

    websocket_api.async_register_command(hass, websocket_locations)
    websocket_api.async_register_command(hass, websocket_snapshot)


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/locations"})
@callback
def websocket_locations(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """List configured locations for the visual card editor."""

    locations = []
    for entry in hass.config_entries.async_entries(DOMAIN):
        latitude = entry.data.get("latitude")
        longitude = entry.data.get("longitude")
        coordinates = (
            f"{float(latitude):.5f}, {float(longitude):.5f}"
            if latitude is not None and longitude is not None
            else ""
        )
        locations.append(
            {
                "entry_id": entry.entry_id,
                "title": entry.title,
                "coordinates": coordinates,
                "label": (
                    f"{entry.title} · {coordinates}"
                    if coordinates
                    else entry.title
                ),
            }
        )
    connection.send_result(msg["id"], locations)


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/snapshot",
        vol.Required("entry_id"): str,
        vol.Inclusive("latitude", "dynamic_position"): vol.All(
            vol.Coerce(float),
            vol.Range(min=-90, max=90),
        ),
        vol.Inclusive("longitude", "dynamic_position"): vol.All(
            vol.Coerce(float),
            vol.Range(min=-180, max=180),
        ),
        vol.Optional("position_accuracy_m"): vol.All(
            vol.Coerce(float),
            vol.Range(min=0, max=100000),
        ),
        vol.Optional("tracker_entity"): vol.Match(
            r"^(person|device_tracker)\.[a-z0-9_]+$"
        ),
        vol.Optional("use_current_user_tracker", default=False): bool,
    }
)
@callback
def websocket_snapshot(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return the current processed snapshot without Recorder-heavy attributes."""

    entry = hass.config_entries.async_get_entry(msg["entry_id"])
    if (
        entry is None
        or entry.domain != DOMAIN
        or entry.state is not ConfigEntryState.LOADED
    ):
        connection.send_error(msg["id"], "not_found", "Location not found")
        return

    coordinator = getattr(entry, "runtime_data", None)
    if not isinstance(coordinator, AirThreatCoordinator) or coordinator.data is None:
        connection.send_error(msg["id"], "not_ready", "Location is not loaded")
        return
    entity_ids = _entry_entity_ids(hass, entry.entry_id)

    tracker_entity = msg.get("tracker_entity")
    use_current_user_tracker = msg["use_current_user_tracker"]
    has_coordinates = "latitude" in msg and "longitude" in msg
    if sum((bool(tracker_entity), has_coordinates, use_current_user_tracker)) > 1:
        connection.send_error(
            msg["id"],
            "invalid_position",
            "Use one dynamic position source",
        )
        return

    point: GeoPoint | None = None
    position_accuracy_m = msg.get("position_accuracy_m")
    position_source: str | None = None
    place_name: str | None = None

    if use_current_user_tracker:
        tracker_entity = _person_entity_for_connection(hass, connection)
        if tracker_entity is None:
            connection.send_error(
                msg["id"],
                "user_tracker_unavailable",
                "The current Home Assistant user is not linked to a person",
            )
            return

    if tracker_entity:
        tracker_state = hass.states.get(tracker_entity)
        attributes = tracker_state.attributes if tracker_state else {}
        point = _state_point(tracker_state)
        if point is None:
            connection.send_error(
                msg["id"],
                (
                    "user_tracker_unavailable"
                    if use_current_user_tracker
                    else "tracker_unavailable"
                ),
                (
                    "The current user's person does not have valid coordinates"
                    if use_current_user_tracker
                    else "Selected tracker does not have valid coordinates"
                ),
            )
            return

        raw_accuracy = attributes.get(
            "gps_accuracy",
            attributes.get("accuracy"),
        )
        try:
            parsed_accuracy = float(raw_accuracy)
            position_accuracy_m = (
                parsed_accuracy if 0 <= parsed_accuracy <= 100000 else None
            )
        except (TypeError, ValueError):
            position_accuracy_m = None
        position_source = tracker_entity
        place_name = _automatic_tracker_place_name(hass, tracker_entity)
    elif has_coordinates:
        point = GeoPoint(
            latitude=msg["latitude"],
            longitude=msg["longitude"],
        )
        position_source = "device"
        place_name = _live_device_place_name(hass, connection, point)

    if point is not None:
        threats, alert, raion, oblast = coordinator.calculate_for_point(point)
        if raion is None and oblast is None:
            connection.send_error(
                msg["id"],
                "location_not_supported",
                "Dynamic location is outside the supported area",
            )
            return
        connection.send_result(
            msg["id"],
            _snapshot(
                coordinator,
                threats=threats,
                alert=alert,
                raion=raion,
                oblast=oblast,
                dynamic_position=True,
                position_accuracy_m=position_accuracy_m,
                position_source=position_source,
                place_name=place_name,
                entity_ids=entity_ids,
            ),
        )
        return

    connection.send_result(
        msg["id"],
        _snapshot(coordinator, entity_ids=entity_ids),
    )
