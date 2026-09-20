"""Constants for Air Threat Monitor."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN = "air_threat_monitor"
VERSION: Final = "0.4.1"
DEFAULT_ENTRY_TITLE: Final = "Air Threat Monitor"
PROJECT_URL: Final = "https://github.com/serg-ill/air-threat-monitor"
CONFIG_ENTRY_VERSION: Final = 2
CONFIG_ENTRY_MINOR_VERSION: Final = 1

CONF_LATITUDE: Final = "latitude"
CONF_LONGITUDE: Final = "longitude"

STATIC_URL: Final = "/air_threat_monitor/assets"
CARD_VERSION: Final = VERSION
CARD_MODULE_URL: Final = (
    f"{STATIC_URL}/air-threat-radar-card.js?v={CARD_VERSION}"
)


def asset_url(path: str) -> str:
    """Return a cache-busted URL for a bundled frontend asset."""

    return f"{STATIC_URL}/{path}?v={VERSION}"

ATTRIBUTION = "Data provided by NEPTUN (https://neptun.in.ua/)"
API_BASE_URL = "https://neptun.in.ua"
API_THREATS_PATH = "/api/v1/threats"
API_ALERTS_PATH = "/api/v1/alerts"
API_STREAM_PATH = "/api/v1/stream"
API_RAIONS_PATH = "/raions.geojson"
API_OBLASTS_PATH = "/oblasts.geojson"

DEFAULT_APPROACH_CONE_DEGREES = 45.0
DEFAULT_SCREEN_TOP_BEARING = 0.0
DEFAULT_RADII_KM = (20.0, 50.0, 100.0)
REST_MIN_INTERVAL_SECONDS = 5
DEFAULT_UPDATE_INTERVAL = timedelta(seconds=10)
