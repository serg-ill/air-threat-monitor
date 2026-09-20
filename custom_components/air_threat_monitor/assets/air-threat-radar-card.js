(() => {
"use strict";

const CARD_TYPE = "air-threat-radar-card";
const EDITOR_TYPE = "air-threat-radar-card-editor";
const API_PREFIX = "air_threat_monitor";
const ASSET_VERSION = "0.4.1";
const SNAPSHOT_CACHE_PREFIX = `${API_PREFIX}:snapshot-cache:v1`;
const SNAPSHOT_CACHE_MAX_AGE_MS = 30 * 60 * 1000;
const DEGRADED_SNAPSHOT_GRACE_MS = 60 * 1000;
const AUTOMATIC_TARGET_LIMIT = 5;
const VALID_MODES = new Set(["live", "demo_safe", "demo_warning", "demo_alert"]);
const VALID_POSITION_MODES = new Set(["configured", "device", "tracker", "auto"]);
const VALID_ORIENTATION_MODES = new Set(["north_up", "device_compass", "auto"]);
const VALID_CARD_STYLES = new Set(["signal", "theme"]);
const VALID_ARTWORK_STYLES = new Set(["standard", "custom"]);

function registerCardMetadata() {
  window.customCards = window.customCards || [];
  const registration = {
    type: CARD_TYPE,
    name: "Air Threat Radar",
    preview: false,
    description: "Local air alert and nearby threat radar with a visual editor",
  };
  const existing = window.customCards.find((card) => card.type === CARD_TYPE);
  if (existing) Object.assign(existing, registration);
  else window.customCards.push(registration);
}

// Expose picker metadata immediately. The full card element is registered
// before the editor at the end of this synchronous module.
registerCardMetadata();

const TEXT = {
  uk: {
    location: "Локація",
    dataMode: "Дані картки",
    liveData: "Реальні дані",
    demoSafe: "Демо: безпечно",
    demoWarning: "Демо: жовтий рівень",
    demoAlert: "Демо: тривога",
    demo: "ДЕМО",
    radius: "Радіус радара",
    targets: "Цілей у списку",
    automaticTargets: "Автоматично (рекомендовано)",
    automaticTargetsHint: "До 5 цілей у радіусі. Якщо поруч немає — одна найближча.",
    showList: "Показувати список цілей",
    cardStyle: "Стиль картки",
    signalStyle: "Сигнальні кольори",
    themeStyle: "За темою Home Assistant",
    positionSource: "Позиція для розрахунків",
    configuredPosition: "Фіксована локація",
    currentDevicePosition: "Живий GPS цього пристрою",
    trackerPosition: "Персона або трекер Home Assistant",
    automaticPosition: "Автоматично для цього пристрою",
    fixedLocations: "Фіксовані локації",
    trackerEntity: "Персона або трекер",
    orientation: "Орієнтація радара",
    northUp: "Північ угорі",
    deviceCompass: "За компасом цього пристрою",
    automaticOrientation: "Автоматично",
    enableCompass: "Увімкнути компас",
    compassWaiting: "Очікування компаса",
    compassUnavailable: "Компас недоступний",
    compassDenied: "Доступ до компаса заборонено",
    trackerUnavailable: "Координати трекера недоступні",
    deviceLocationWaiting: "Визначаю геопозицію…",
    deviceLocationUnavailable: "Геолокація цього пристрою недоступна",
    deviceLocationDenied: "Доступ до геолокації заборонено",
    deviceLocationTimeout: "Не вдалося визначити геопозицію вчасно",
    deviceLocationPositionUnavailable: "Пристрій не зміг визначити геопозицію",
    deviceLocationFallbackUnavailable: "GPS і геопозиція вашої персони недоступні",
    automaticLocationFallback: "Не вдалося визначити вашу позицію. Використати фіксовану локацію «{location}»?",
    useFixedLocation: "Використати фіксовану",
    retryGps: "Повторити GPS",
    enableLocation: "Увімкнути геолокацію",
    dynamicLocationUnsupported: "Поточна позиція поза підтримуваною територією",
    noLocation: "Спочатку додайте інтеграцію Air Threat Monitor",
    loading: "Завантаження даних",
    cachedUpdating: "оновлення…",
    dataDelayed: "дані затримуються",
    unavailable: "ДАНІ НЕДОСТУПНІ",
    unavailableDetail: "Не вдалося отримати актуальні дані. Перевірте інтеграцію та офіційні канали оповіщення.",
    cardError: "Помилка картки",
    safe: "БЕЗПЕЧНО",
    warning: "ЖОВТИЙ РІВЕНЬ",
    alert: "ТРИВОГА",
    noTargets: "Цілей поруч немає",
    noActiveTargets: "Активних цілей немає",
    targetsLabel: "цілей",
    since: "з",
    alertDuration: "триває",
    warningDuration: "триває",
    safeDuration: "безпечно",
    stale: "застаріла",
    unknownDirection: "курс невідомий",
    categories: {
      uav: "БпЛА", fpv: "FPV-дрон", recon: "Розвідник",
      missile: "Ракета", ballistic: "Балістика", kab: "КАБ",
      aircraft: "Літак", unknown: "Ціль",
    },
    categoryCounts: {
      uav: "БпЛА", fpv: "FPV", recon: "розв.", missile: "ракет",
      ballistic: "баліст.", kab: "КАБ", aircraft: "літаків", unknown: "інших",
    },
    informational: "Неофіційні дані",
    north: "Пн",
    east: "Сх",
    south: "Пд",
    west: "Зх",
    distanceUnit: "км",
  },
  en: {
    location: "Location",
    dataMode: "Card data",
    liveData: "Live data",
    demoSafe: "Demo: safe",
    demoWarning: "Demo: yellow level",
    demoAlert: "Demo: alert",
    demo: "DEMO",
    radius: "Radar radius",
    targets: "Targets in list",
    automaticTargets: "Automatic (recommended)",
    automaticTargetsHint: "Up to 5 targets within the radar radius. If none are nearby, show the nearest one.",
    showList: "Show target list",
    cardStyle: "Card style",
    signalStyle: "Signal colors",
    themeStyle: "Follow Home Assistant theme",
    positionSource: "Position used for calculations",
    configuredPosition: "Fixed location",
    currentDevicePosition: "Live GPS of this device",
    trackerPosition: "Home Assistant person or tracker",
    automaticPosition: "Automatic for this device",
    fixedLocations: "Fixed locations",
    trackerEntity: "Person or tracker",
    orientation: "Radar orientation",
    northUp: "North up",
    deviceCompass: "Follow this device compass",
    automaticOrientation: "Automatic",
    enableCompass: "Enable compass",
    compassWaiting: "Waiting for compass",
    compassUnavailable: "Compass unavailable",
    compassDenied: "Compass access denied",
    trackerUnavailable: "Tracker coordinates unavailable",
    deviceLocationWaiting: "Detecting device location…",
    deviceLocationUnavailable: "This device location is unavailable",
    deviceLocationDenied: "Location access denied",
    deviceLocationTimeout: "Location request timed out",
    deviceLocationPositionUnavailable: "This device could not determine its location",
    deviceLocationFallbackUnavailable: "GPS and your person location are unavailable",
    automaticLocationFallback: "Your position could not be determined. Use the fixed location “{location}”?",
    useFixedLocation: "Use fixed location",
    retryGps: "Retry GPS",
    enableLocation: "Enable location",
    dynamicLocationUnsupported: "Current position is outside the supported area",
    noLocation: "Add the Air Threat Monitor integration first",
    loading: "Loading data",
    cachedUpdating: "updating…",
    dataDelayed: "data delayed",
    unavailable: "DATA UNAVAILABLE",
    unavailableDetail: "Current data could not be retrieved. Check the integration and official warning channels.",
    cardError: "Card error",
    safe: "SAFE",
    warning: "YELLOW LEVEL",
    alert: "AIR ALERT",
    noTargets: "No nearby targets",
    noActiveTargets: "No active targets",
    targetsLabel: "targets",
    since: "since",
    alertDuration: "active",
    warningDuration: "active",
    safeDuration: "safe",
    stale: "stale",
    unknownDirection: "heading unknown",
    categories: {
      uav: "UAV", fpv: "FPV drone", recon: "Recon aircraft",
      missile: "Missile", ballistic: "Ballistic missile", kab: "Guided bomb",
      aircraft: "Aircraft", unknown: "Target",
    },
    categoryCounts: {
      uav: "UAV", fpv: "FPV", recon: "recon", missile: "missiles",
      ballistic: "ballistic", kab: "bombs", aircraft: "aircraft", unknown: "other",
    },
    informational: "Unofficial data",
    north: "N",
    east: "E",
    south: "S",
    west: "W",
    distanceUnit: "km",
  },
};

function language(hass) {
  const value = hass && hass.language ? String(hass.language) : "";
  return value.toLowerCase().startsWith("uk") ? "uk" : "en";
}

function valueOr(value, fallback) {
  return value === undefined || value === null ? fallback : value;
}

function escapeHtml(value) {
  const replacements = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  };
  return String(valueOr(value, "")).replace(
    /[&<>"']/g,
    (character) => replacements[character],
  );
}

function safeErrorText(error) {
  const candidates = [
    error && error.message,
    error && error.code,
    error,
  ];
  for (const candidate of candidates) {
    if (
      typeof candidate !== "string"
      && typeof candidate !== "number"
      && typeof candidate !== "boolean"
    ) {
      continue;
    }
    const text = String(candidate).trim();
    if (text && text !== "[object Object]" && !/^\d+$/.test(text)) {
      return text;
    }
  }
  return "";
}

function degradedSnapshotWithinGrace(snapshot) {
  if (
    !snapshot
    || snapshot.available !== false
    || !Array.isArray(snapshot.targets)
  ) {
    return false;
  }
  const updatedAt = Date.parse(String(snapshot.updated_at || ""));
  if (!Number.isFinite(updatedAt)) return false;
  const age = Math.max(0, Date.now() - updatedAt);
  return age <= DEGRADED_SNAPSHOT_GRACE_MS;
}

function assetUrl(filename) {
  return `/air_threat_monitor/assets/images/${filename}?v=${ASSET_VERSION}`;
}

function isLinuxDesktopClient() {
  const navigatorObject = window.navigator || {};
  const userAgent = String(navigatorObject.userAgent || "");
  const userAgentData = navigatorObject.userAgentData;
  const userAgentPlatform = String(
    userAgentData && userAgentData.platform
      ? userAgentData.platform
      : "",
  );
  const legacyPlatform = String(navigatorObject.platform || "");
  return /Linux x86_64|Linux i[3-6]86|CrOS/i.test(
    `${userAgentPlatform} ${legacyPlatform} ${userAgent}`,
  );
}

function isMobileClient() {
  const navigatorObject = window.navigator || {};
  const userAgent = String(navigatorObject.userAgent || "");
  const userAgentData = navigatorObject.userAgentData;
  const userAgentPlatform = String(
    userAgentData && userAgentData.platform
      ? userAgentData.platform
      : "",
  );
  const legacyPlatform = String(navigatorObject.platform || "");
  const touchPoints = Number(navigatorObject.maxTouchPoints || 0);
  const iosDevice = /iPhone|iPad|iPod/i.test(userAgent)
    || (/Mac/i.test(legacyPlatform) && touchPoints > 1);
  const androidDevice = /Android/i.test(userAgent);
  const linuxDesktop = isLinuxDesktopClient();
  const chromiumReportsDesktop = Boolean(
    userAgentData
    && (
      userAgentData.mobile === false
      || /Windows|macOS|Linux|Chrome OS/i.test(userAgentPlatform)
    ),
  );
  return Boolean(
    touchPoints > 0
    && (iosDevice || androidDevice)
    && !linuxDesktop
    && !chromiumReportsDesktop
  );
}

function supportsMobileCompass() {
  return Boolean(
    isMobileClient()
    && window.isSecureContext
    && window.DeviceOrientationEvent
  );
}

function hasTargetHeading(target) {
  return Boolean(target)
    && target.heading !== null
    && target.heading !== undefined
    && target.icon_rotation !== null
    && target.icon_rotation !== undefined
    && Number.isFinite(Number(target.icon_rotation));
}

function targetIconRotation(target) {
  return hasTargetHeading(target) ? Number(target.icon_rotation) : 0;
}

function targetDisplayTitle(target, t) {
  if (!target) return t.categories.unknown;
  if (target.category === "kab" || target.category === "recon") {
    return t.categories[target.category];
  }
  return target.title || t.categories[target.category] || t.categories.unknown;
}

function compactDistrictName(value) {
  return String(value || "")
    .trim()
    .replace(/\s+район(?=\s|,|·|$)/i, " р-н");
}

function targetDistance(target) {
  const distance = Number(target && target.distance_km);
  return Number.isFinite(distance) ? distance : Number.POSITIVE_INFINITY;
}

function sortedTargets(targets) {
  return Array.isArray(targets)
    ? [...targets].sort(
      (first, second) => targetDistance(first) - targetDistance(second),
    )
    : [];
}

function selectVisibleTargets(targets, maxDistance, maxTargets) {
  const ordered = sortedTargets(targets);
  if (maxTargets !== "auto") {
    return ordered.slice(0, Number(maxTargets));
  }
  const nearby = ordered.filter(
    (target) => targetDistance(target) <= maxDistance,
  );
  return nearby.length
    ? nearby.slice(0, AUTOMATIC_TARGET_LIMIT)
    : ordered.slice(0, 1);
}

function formatStatusTime(value, lang) {
  if (value === undefined || value === null || String(value).trim() === "") {
    return "";
  }
  const date = new Date(value);
  if (!Number.isFinite(date.getTime())) return "";
  const now = new Date();
  const sameDay = date.getFullYear() === now.getFullYear()
    && date.getMonth() === now.getMonth()
    && date.getDate() === now.getDate();
  const time = date.toLocaleTimeString(lang === "uk" ? "uk-UA" : "en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
  if (sameDay) return time;
  const day = date.toLocaleDateString(lang === "uk" ? "uk-UA" : "en-GB", {
    day: "2-digit",
    month: "2-digit",
  });
  return `${day} ${time}`;
}

function formatDuration(value, lang) {
  if (value === undefined || value === null || String(value).trim() === "") {
    return "";
  }
  const since = new Date(value);
  if (!Number.isFinite(since.getTime())) return "";
  const minutesTotal = Math.max(0, Math.floor((Date.now() - since.getTime()) / 60000));
  const days = Math.floor(minutesTotal / 1440);
  const hours = Math.floor((minutesTotal % 1440) / 60);
  const minutes = minutesTotal % 60;
  if (lang === "uk") {
    if (days > 0) return `${days} дн ${hours} год`;
    if (hours > 0) return `${hours} год ${minutes} хв`;
    return `${minutes} хв`;
  }
  if (days > 0) return `${days} d ${hours} h`;
  if (hours > 0) return `${hours} h ${minutes} min`;
  return `${minutes} min`;
}

function entityLabel(stateObject) {
  if (!stateObject) return "";
  return String(
    valueOr(
      stateObject.attributes && stateObject.attributes.friendly_name,
      stateObject.entity_id,
    ),
  );
}

function entityOptions(hass, entityIds, selected) {
  const uniqueIds = Array.from(new Set(entityIds));
  if (
    selected
    && hass
    && hass.states
    && hass.states[selected]
    && !uniqueIds.includes(selected)
  ) {
    uniqueIds.push(selected);
  }
  return uniqueIds
    .sort((first, second) => entityLabel(hass.states[first]).localeCompare(
      entityLabel(hass.states[second]),
    ))
    .map((entityId) => {
      const stateObject = hass.states[entityId];
      const label = entityLabel(stateObject);
      return `<option value="${escapeHtml(entityId)}" ${entityId === selected ? "selected" : ""}>${escapeHtml(label)} · ${escapeHtml(entityId)}</option>`;
    })
    .join("");
}

function normalizeConfig(config = {}) {
  const mode = valueOr(config.data_mode, "live");
  if (!VALID_MODES.has(mode)) throw new Error(`Unsupported data_mode: ${mode}`);
  const positionMode = valueOr(config.position_mode, "configured");
  if (!VALID_POSITION_MODES.has(positionMode)) {
    throw new Error(`Unsupported position_mode: ${positionMode}`);
  }
  const orientationMode = valueOr(config.orientation_mode, "north_up");
  if (!VALID_ORIENTATION_MODES.has(orientationMode)) {
    throw new Error(`Unsupported orientation_mode: ${orientationMode}`);
  }
  const cardStyle = valueOr(config.card_style, "signal");
  if (!VALID_CARD_STYLES.has(cardStyle)) {
    throw new Error(`Unsupported card_style: ${cardStyle}`);
  }
  const requestedArtworkStyle = valueOr(config.artwork_style, "standard");
  const artworkStyle = VALID_ARTWORK_STYLES.has(requestedArtworkStyle)
    ? requestedArtworkStyle
    : "standard";
  const distance = Number(valueOr(config.max_distance, 100));
  const targetCountValue = valueOr(config.max_targets, "auto");
  const targetCount = Number(targetCountValue);
  const normalizedTargetCount = targetCountValue === "auto"
    ? "auto"
    : Number.isFinite(targetCount)
    ? Math.max(1, Math.min(5, Math.round(targetCount)))
    : "auto";
  return {
    ...config,
    data_mode: mode,
    position_mode: positionMode,
    tracker_entity: String(valueOr(config.tracker_entity, "")).trim(),
    geocoded_entity: "",
    orientation_mode: orientationMode,
    card_style: cardStyle,
    artwork_style: artworkStyle,
    safe_image: String(valueOr(config.safe_image, "")).trim(),
    danger_image: String(valueOr(config.danger_image, "")).trim(),
    max_distance: Number.isFinite(distance) ? Math.max(1, Math.min(500, distance)) : 100,
    max_targets: normalizedTargetCount,
    show_target_list: config.show_target_list !== false,
  };
}

class AirThreatRadarCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._locations = [];
    this._loaded = false;
  }

  setConfig(config) {
    this._config = normalizeConfig(config);
    this._render();
  }

  set hass(hass) {
    const oldLanguage = language(this._hass);
    this._hass = hass;
    if (!this._loaded && Date.now() >= valueOr(this._retryAfter, 0)) {
      this._loadLocations();
    }
    if (!this.shadowRoot.innerHTML || oldLanguage !== language(hass)) this._render();
  }

  async _loadLocations() {
    if (!this._hass || this._loading) return;
    this._loading = true;
    try {
      this._locations = await this._hass.callWS({ type: `${API_PREFIX}/locations` });
      this._loaded = this._locations.length > 0;
      this._retryAfter = this._loaded ? 0 : Date.now() + 30000;
      const configuredLocationExists = this._locations.some(
        (item) => item.entry_id === this._config.entry_id,
      );
      if (!configuredLocationExists && this._locations.length) {
        this._changed({ entry_id: this._locations[0].entry_id });
      }
      this._error = undefined;
    } catch (error) {
      this._error = safeErrorText(error);
      this._retryAfter = Date.now() + 30000;
    } finally {
      this._loading = false;
      this._render();
    }
  }

  _changed(change) {
    this._config = { ...this._config, ...change };
    this.dispatchEvent(
      new CustomEvent("config-changed", {
        detail: { config: this._config },
        bubbles: true,
        composed: true,
      }),
    );
    this._render();
  }

  _render() {
    try {
      this._renderContent();
    } catch (error) {
      console.error(`[Air Threat Radar ${ASSET_VERSION}] render failed`, error);
      if (!this.shadowRoot) return;
      const t = TEXT[language(this._hass)];
      const detail = safeErrorText(error) || "render_error";
      this.shadowRoot.innerHTML = `
        <style>
          :host{display:block}
          ha-card{box-sizing:border-box;min-height:96px;padding:14px;overflow:hidden;border-radius:20px;background:#3b4148;color:white}
          strong,span{display:block}
          span{margin-top:7px;font-size:11px;line-height:1.3;opacity:.78;overflow-wrap:anywhere}
        </style>
        <ha-card><strong>${t.cardError}</strong><span>${ASSET_VERSION} · ${escapeHtml(detail)}</span></ha-card>`;
    }
  }

  _renderContent() {
    if (!this.shadowRoot) return;
    const t = TEXT[language(this._hass)];
    const radius = Number(valueOr(this._config.max_distance, 100));
    const count = valueOr(this._config.max_targets, "auto");
    const showList = this._config.show_target_list !== false;
    const dataMode = valueOr(this._config.data_mode, "live");
    const positionMode = valueOr(this._config.position_mode, "configured");
    const orientationMode = valueOr(this._config.orientation_mode, "north_up");
    const cardStyle = valueOr(this._config.card_style, "signal");
    const linuxDesktop = isLinuxDesktopClient();
    const trackerIds = this._hass && this._hass.states
      ? Object.keys(this._hass.states).filter(
        (entityId) => entityId.startsWith("device_tracker.") || entityId.startsWith("person."),
      )
      : [];
    const configuredEntryId = this._config.entry_id
      || (this._locations[0] && this._locations[0].entry_id)
      || "";
    const configuredPositionSelection = `configured:${configuredEntryId}`;
    const positionSelection = linuxDesktop || positionMode === "configured"
      ? configuredPositionSelection
      : positionMode;
    const fixedPositionOptions = this._locations
      .map(
        (item) =>
          `<option value="configured:${escapeHtml(item.entry_id)}" ${
            positionSelection === `configured:${item.entry_id}` ? "selected" : ""
          }>${escapeHtml(item.label || item.title)}</option>`,
      )
      .join("");

    this.shadowRoot.innerHTML = `
      <style>
        :host { display:block; }
        .form { display:grid; gap:16px; padding:8px 0; }
        label { display:grid; gap:6px; color:var(--primary-text-color); font-size:14px; }
        label small { color:var(--secondary-text-color); font-size:11px; line-height:1.3; }
        select, input[type="number"] {
          box-sizing:border-box; width:100%; min-height:48px; padding:0 12px;
          color:var(--primary-text-color); background:var(--card-background-color);
          border:1px solid var(--divider-color); border-radius:6px; font:inherit;
        }
        .toggle { display:flex; align-items:center; justify-content:space-between; gap:12px; }
        .empty { padding:16px; border:1px solid var(--divider-color); border-radius:6px; }
      </style>
      <div class="form">
          <label>${t.dataMode}<select id="data-mode">
            <option value="live" ${dataMode === "live" ? "selected" : ""}>${t.liveData}</option>
            <option value="demo_safe" ${dataMode === "demo_safe" ? "selected" : ""}>${t.demoSafe}</option>
            <option value="demo_warning" ${dataMode === "demo_warning" ? "selected" : ""}>${t.demoWarning}</option>
            <option value="demo_alert" ${dataMode === "demo_alert" ? "selected" : ""}>${t.demoAlert}</option>
          </select></label>
          ${dataMode === "live" ? (this._locations.length ? `
            <label>${t.positionSource}<select id="position-source">
              ${linuxDesktop ? "" : `
                <option value="auto" ${positionSelection === "auto" ? "selected" : ""}>${t.automaticPosition}</option>
                <option value="device" ${positionSelection === "device" ? "selected" : ""}>${t.currentDevicePosition}</option>
                <option value="tracker" ${positionSelection === "tracker" ? "selected" : ""}>${t.trackerPosition}</option>
              `}
              <optgroup label="${escapeHtml(t.fixedLocations)}">
                ${fixedPositionOptions}
              </optgroup>
            </select></label>
            ${!linuxDesktop && positionMode === "tracker" ? `
              <label>${t.trackerEntity}<select id="tracker">
                <option value="">—</option>
                ${entityOptions(this._hass, trackerIds, this._config.tracker_entity)}
              </select></label>
            ` : ""}
          ` : `<div class="empty">${escapeHtml(this._error || t.noLocation)}</div>`) : ""}
          ${linuxDesktop ? "" : `
            <label>${t.orientation}<select id="orientation-mode">
              <option value="north_up" ${orientationMode === "north_up" ? "selected" : ""}>${t.northUp}</option>
              <option value="device_compass" ${orientationMode === "device_compass" ? "selected" : ""}>${t.deviceCompass}</option>
              <option value="auto" ${orientationMode === "auto" ? "selected" : ""}>${t.automaticOrientation}</option>
            </select></label>
          `}
          <label>${t.cardStyle}<select id="card-style">
            <option value="signal" ${cardStyle === "signal" ? "selected" : ""}>${t.signalStyle}</option>
            <option value="theme" ${cardStyle === "theme" ? "selected" : ""}>${t.themeStyle}</option>
          </select></label>
          <label>${t.radius}<select id="radius">
            ${[20, 50, 100].map((value) => `<option value="${value}" ${value === radius ? "selected" : ""}>${value} ${t.distanceUnit}</option>`).join("")}
          </select></label>
          <label>${t.targets}<select id="count">
            <option value="auto" ${count === "auto" ? "selected" : ""}>${t.automaticTargets}</option>
            ${[1, 2, 3, 4, 5].map((value) => `<option value="${value}" ${Number(count) === value ? "selected" : ""}>${value}</option>`).join("")}
          </select><small>${t.automaticTargetsHint}</small></label>
          <label class="toggle"><span>${t.showList}</span><input id="show-list" type="checkbox" ${showList ? "checked" : ""}></label>
        </div>
    `;

    const dataModeElement = this.shadowRoot.querySelector("#data-mode");
    if (dataModeElement) {
      dataModeElement.addEventListener("change", (event) => {
        this._changed({ data_mode: event.target.value });
      });
    }
    const positionSourceElement = this.shadowRoot.querySelector("#position-source");
    if (positionSourceElement) {
      positionSourceElement.addEventListener("change", (event) => {
        const selection = event.target.value;
        if (selection.startsWith("configured:")) {
          this._changed({
            position_mode: "configured",
            entry_id: selection.slice("configured:".length),
          });
          return;
        }
        const nextPositionMode = selection;
        if (nextPositionMode === "auto") {
          try {
            const entryId = this._config.entry_id || "default";
            window.localStorage.removeItem(
              `${API_PREFIX}:automatic-position:${entryId}`,
            );
          } catch (_error) {
            // Local storage may be unavailable in a hardened browser profile.
          }
        }
        this._changed(
          nextPositionMode === "auto"
            ? { position_mode: nextPositionMode, orientation_mode: "auto" }
            : { position_mode: nextPositionMode },
        );
      });
    }
    const trackerElement = this.shadowRoot.querySelector("#tracker");
    if (trackerElement) {
      trackerElement.addEventListener("change", (event) => {
        this._changed({ tracker_entity: event.target.value });
      });
    }
    const orientationModeElement = this.shadowRoot.querySelector("#orientation-mode");
    if (orientationModeElement) {
      orientationModeElement.addEventListener("change", (event) => {
        this._changed({ orientation_mode: event.target.value });
      });
    }
    const cardStyleElement = this.shadowRoot.querySelector("#card-style");
    if (cardStyleElement) {
      cardStyleElement.addEventListener("change", (event) => {
        this._changed({ card_style: event.target.value });
      });
    }
    const radiusElement = this.shadowRoot.querySelector("#radius");
    if (radiusElement) {
      radiusElement.addEventListener("change", (event) => {
        this._changed({ max_distance: Number(event.target.value) });
      });
    }
    const countElement = this.shadowRoot.querySelector("#count");
    if (countElement) {
      countElement.addEventListener("change", (event) => {
        const value = event.target.value === "auto"
          ? "auto"
          : Math.max(1, Math.min(5, Number(event.target.value) || 1));
        this._changed({ max_targets: value });
      });
    }
    const showListElement = this.shadowRoot.querySelector("#show-list");
    if (showListElement) {
      showListElement.addEventListener("change", (event) => {
        this._changed({ show_target_list: event.target.checked });
      });
    }
  }
}

class AirThreatRadarCard extends HTMLElement {
  static getConfigElement() {
    return document.createElement(EDITOR_TYPE);
  }

  static getStubConfig() {
    return {
      data_mode: "live",
      position_mode: "configured",
      tracker_entity: "",
      orientation_mode: "north_up",
      card_style: "signal",
      artwork_style: "standard",
      safe_image: "",
      danger_image: "",
      max_distance: 100,
      max_targets: "auto",
      show_target_list: true,
    };
  }

  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = AirThreatRadarCard.getStubConfig();
    this._compassHeading = 0;
    this._compassState = "idle";
    this._compassStarting = false;
    this._compassRequestToken = 0;
    this._compassReadyTimer = undefined;
    this._positionRequestToken = 0;
    this._positionFallback = false;
    this._snapshotFromCache = false;
    this._locations = [];
    this._orientationListener = (event) => this._handleOrientation(event);
    this._visibilityListener = () => this._handleVisibilityChange();
  }

  setConfig(config) {
    const previousConfig = this._config || {};
    const previousSnapshotKey = [
      previousConfig.data_mode,
      previousConfig.entry_id,
      previousConfig.position_mode,
      previousConfig.tracker_entity,
    ].join("|");
    const previousOrientation = previousConfig.orientation_mode;
    const previousPositionMode = previousConfig.position_mode;
    this._config = normalizeConfig({
      ...AirThreatRadarCard.getStubConfig(),
      ...config,
    });
    const snapshotKey = [
      this._config.data_mode,
      this._config.entry_id,
      this._config.position_mode,
      this._config.tracker_entity,
    ].join("|");
    if (previousSnapshotKey !== snapshotKey) {
      this._snapshot = undefined;
      this._snapshotFromCache = false;
      this._dynamicStatusState = undefined;
      this._lastRequest = undefined;
      this._activeRequest = Symbol("cancelled");
      this._loading = false;
      this._error = undefined;
      if (previousConfig.entry_id !== this._config.entry_id) {
        this._entryId = undefined;
        this._automaticFixedLocation = undefined;
      }
    }
    if (!this._snapshot) this._restoreSnapshotCache();
    if (previousOrientation !== this._config.orientation_mode) {
      this._stopCompass();
      if (this.isConnected) this._startCompass(false);
    }
    if (previousPositionMode !== this._config.position_mode) {
      if (this._config.position_mode === "auto") {
        this._automaticFixedLocation = undefined;
      }
      this._stopDeviceLocation();
      if (this.isConnected) this._startDeviceLocation();
      if (this._config.orientation_mode === "auto") {
        this._stopCompass();
        if (this.isConnected) this._startCompass(false);
      }
    }
    this._render();
    this._notifyCardSizeChanged();
    if (this._hass) this._refresh(true);
  }

  set hass(hass) {
    this._hass = hass;
    if (
      this._config.data_mode === "live" &&
      !this._entryId &&
      !this._discovering &&
      Date.now() >= valueOr(this._discoveryRetryAfter, 0)
    ) {
      this._discoverLocation();
    }
    this._refresh();
  }

  connectedCallback() {
    window.clearInterval(this._timer);
    this._timer = window.setInterval(() => this._refresh(true), 10000);
    document.removeEventListener("visibilitychange", this._visibilityListener);
    document.addEventListener("visibilitychange", this._visibilityListener);
    this._startDeviceLocation();
    this._startCompass(false);
    this._render();
  }

  disconnectedCallback() {
    window.clearInterval(this._timer);
    this._timer = undefined;
    document.removeEventListener("visibilitychange", this._visibilityListener);
    this._activeRequest = Symbol("disconnected");
    this._loading = false;
    this._stopDeviceLocation();
    this._stopCompass();
  }

  getCardSize() {
    const targetCount = this._config.show_target_list === false
      ? 0
      : selectVisibleTargets(
        this._snapshot && this._snapshot.targets,
        Number(valueOr(this._config.max_distance, 100)),
        valueOr(this._config.max_targets, "auto"),
      ).length;
    return 3 + Math.ceil((targetCount * 38) / 50);
  }

  getGridOptions() {
    return {
      columns: 12,
      min_columns: 6,
    };
  }

  _automaticPositionStorageKey() {
    const entryId = this._entryId || this._config.entry_id || "default";
    return `${API_PREFIX}:automatic-position:${entryId}`;
  }

  _snapshotCacheKey() {
    const entryId = this._entryId || this._config.entry_id || "default";
    const positionMode = valueOr(this._config.position_mode, "configured");
    const trackerEntity = String(
      valueOr(this._config.tracker_entity, ""),
    ).trim() || "none";
    return [
      SNAPSHOT_CACHE_PREFIX,
      entryId,
      positionMode,
      trackerEntity,
    ].join(":");
  }

  _restoreSnapshotCache() {
    if (this._config.data_mode !== "live" || this._snapshot) return false;
    try {
      const key = this._snapshotCacheKey();
      const stored = JSON.parse(window.localStorage.getItem(key) || "null");
      const savedAt = Number(stored && stored.saved_at);
      const snapshot = stored && stored.snapshot;
      const valid = (
        snapshot
        && typeof snapshot === "object"
        && snapshot.available !== false
        && Array.isArray(snapshot.targets)
        && Number.isFinite(savedAt)
        && Date.now() - savedAt <= SNAPSHOT_CACHE_MAX_AGE_MS
      );
      if (!valid) {
        if (stored) window.localStorage.removeItem(key);
        return false;
      }
      this._snapshot = snapshot;
      this._snapshotFromCache = true;
      this._error = undefined;
      this._errorCode = undefined;
      return true;
    } catch (_error) {
      return false;
    }
  }

  _storeSnapshotCache(snapshot) {
    if (
      this._config.data_mode !== "live"
      || !snapshot
      || typeof snapshot !== "object"
      || snapshot.available === false
      || !Array.isArray(snapshot.targets)
    ) {
      return;
    }
    try {
      window.localStorage.setItem(
        this._snapshotCacheKey(),
        JSON.stringify({
          saved_at: Date.now(),
          snapshot,
        }),
      );
    } catch (_error) {
      // Private browsing and hardened kiosk profiles may disable local storage.
    }
  }

  _automaticFixedLocationEnabled() {
    if (this._config.position_mode !== "auto") return false;
    if (this._automaticFixedLocation !== undefined) {
      return this._automaticFixedLocation;
    }
    try {
      this._automaticFixedLocation = (
        window.localStorage.getItem(this._automaticPositionStorageKey())
        === "configured"
      );
    } catch (_error) {
      this._automaticFixedLocation = false;
    }
    return this._automaticFixedLocation;
  }

  _setAutomaticFixedLocation(enabled) {
    this._automaticFixedLocation = Boolean(enabled);
    try {
      const key = this._automaticPositionStorageKey();
      if (enabled) window.localStorage.setItem(key, "configured");
      else window.localStorage.removeItem(key);
    } catch (_error) {
      // Private browsing and hardened kiosk profiles may disable local storage.
    }
  }

  _effectivePositionMode() {
    if (isLinuxDesktopClient()) return "configured";
    if (this._config.position_mode !== "auto") {
      return this._config.position_mode;
    }
    if (this._automaticFixedLocationEnabled()) return "configured";
    return isMobileClient() ? "device" : "configured";
  }

  _effectiveOrientationMode() {
    const requestedMode = this._config.orientation_mode;
    if (
      requestedMode === "north_up"
      || this._compassState === "unavailable"
      || !supportsMobileCompass()
    ) {
      return "north_up";
    }
    if (requestedMode === "device_compass") return "device_compass";
    return this._effectivePositionMode() === "device"
      ? "device_compass"
      : "north_up";
  }

  _configuredLocationLabel() {
    const entryId = this._entryId || this._config.entry_id;
    const location = this._locations.find((item) => item.entry_id === entryId);
    return location
      ? String(location.label || location.title || TEXT.uk.configuredPosition)
      : TEXT[language(this._hass)].configuredPosition;
  }

  _dynamicPosition() {
    return this._effectivePositionMode() === "device"
      ? this._devicePosition || null
      : null;
  }

  _startDeviceLocation() {
    if (
      !this._config
      || this._effectivePositionMode() !== "device"
      || this._positionWatchId !== undefined
      || this._positionLoading
    ) {
      return;
    }
    const geolocation = window.navigator && window.navigator.geolocation;
    if (!geolocation) {
      this._useCurrentUserPosition("device_location_unavailable");
      return;
    }

    const requestToken = ++this._positionRequestToken;
    this._positionLoading = true;
    this._positionFallback = false;
    this._positionError = undefined;
    this._errorCode = "device_location_waiting";
    this._render();
    this._notifyCardSizeChanged();

    const acceptPosition = (position) => {
      if (requestToken !== this._positionRequestToken) return;
      const coordinates = position.coords || {};
      const latitude = Number(coordinates.latitude);
      const longitude = Number(coordinates.longitude);
      if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
        this._useCurrentUserPosition("device_location_unavailable");
        return;
      }
      const accuracy = Number(coordinates.accuracy);
      this._devicePosition = {
        latitude,
        longitude,
        accuracy: Number.isFinite(accuracy) && accuracy >= 0 ? accuracy : null,
      };
      this._positionLoading = false;
      this._positionFallback = false;
      this._positionError = undefined;
      this._errorCode = undefined;
      this._lastRequest = undefined;
      this._refresh(true);
    };

    const locationErrorCode = (error) => {
      if (error && Number(error.code) === 1) return "device_location_denied";
      if (error && Number(error.code) === 3) return "device_location_timeout";
      return "device_location_position_unavailable";
    };

    const startWatch = () => {
      if (
        requestToken !== this._positionRequestToken
        || this._positionWatchId !== undefined
      ) {
        return;
      }
      this._positionWatchId = geolocation.watchPosition(
        acceptPosition,
        (error) => {
          if (requestToken !== this._positionRequestToken) return;
          this._positionError = locationErrorCode(error);
          if (!this._devicePosition) {
            this._useCurrentUserPosition(this._positionError);
          }
        },
        {
          enableHighAccuracy: true,
          maximumAge: 15000,
          timeout: 60000,
        },
      );
    };

    const requestPosition = (highAccuracy) => {
      geolocation.getCurrentPosition(
        (position) => {
          acceptPosition(position);
          startWatch();
        },
        (error) => {
          if (requestToken !== this._positionRequestToken) return;
          const errorCode = locationErrorCode(error);
          if (highAccuracy && Number(error && error.code) !== 1) {
            requestPosition(false);
            return;
          }
          this._useCurrentUserPosition(errorCode);
        },
        {
          enableHighAccuracy: highAccuracy,
          maximumAge: highAccuracy ? 15000 : 300000,
          timeout: highAccuracy ? 12000 : 20000,
        },
      );
    };

    try {
      requestPosition(true);
    } catch (_error) {
      this._useCurrentUserPosition("device_location_unavailable");
    }
  }

  _useCurrentUserPosition(errorCode) {
    this._positionLoading = false;
    this._positionError = errorCode;
    this._positionFallback = true;
    this._errorCode = "device_location_waiting";
    this._lastRequest = undefined;
    this._render();
    this._notifyCardSizeChanged();
    this._refresh(true);
  }

  _stopDeviceLocation() {
    this._positionRequestToken += 1;
    const geolocation = window.navigator && window.navigator.geolocation;
    if (
      geolocation
      && this._positionWatchId !== undefined
      && typeof geolocation.clearWatch === "function"
    ) {
      geolocation.clearWatch(this._positionWatchId);
    }
    this._positionWatchId = undefined;
    this._positionLoading = false;
    this._positionFallback = false;
    this._positionError = undefined;
    this._devicePosition = undefined;
  }

  _statusSince(data) {
    const directValue = data.status_since || data.alert_since;
    if (directValue !== undefined && directValue !== null) {
      const directText = String(directValue).trim();
      if (directText && Number.isFinite(new Date(directText).getTime())) {
        if (data.dynamic_position) {
          this._dynamicStatusState = {
            key: [
              valueOr(data.position_source, ""),
              valueOr(data.area, ""),
              valueOr(data.oblast, ""),
              valueOr(data.alert_level, ""),
            ].join("|"),
            active: Boolean(data.alert_active),
            since: directText,
          };
        }
        return directText;
      }
    }
    if (!data.dynamic_position) return "";

    const key = [
      valueOr(data.position_source, ""),
      valueOr(data.area, ""),
      valueOr(data.oblast, ""),
      valueOr(data.alert_level, ""),
    ].join("|");
    const active = Boolean(data.alert_active);
    const previous = this._dynamicStatusState;
    if (!previous || previous.key !== key) {
      this._dynamicStatusState = { key, active, since: "" };
      return "";
    }
    if (previous.active !== active) {
      const since = new Date().toISOString();
      this._dynamicStatusState = { key, active, since };
      return since;
    }
    return previous.since || "";
  }

  _stopCompass() {
    this._compassRequestToken += 1;
    this._compassStarting = false;
    window.clearTimeout(this._compassReadyTimer);
    this._compassReadyTimer = undefined;
    window.removeEventListener("deviceorientationabsolute", this._orientationListener);
    window.removeEventListener("deviceorientation", this._orientationListener);
    this._compassListening = false;
    this._compassHeading = 0;
    this._lastCompassUpdate = undefined;
    this.style.setProperty("--atm-compass-heading", "0deg");
    if (this._config && this._effectiveOrientationMode() !== "device_compass") {
      this._compassState = "idle";
    }
  }

  _handleVisibilityChange() {
    if (document.visibilityState !== "visible" || !this.isConnected) return;
    this._stopCompass();
    this._compassState = "idle";
    this._startCompass(false);
    this._render();
  }

  _waitForCompassReading() {
    window.clearTimeout(this._compassReadyTimer);
    this._compassReadyTimer = window.setTimeout(() => {
      this._compassReadyTimer = undefined;
      if (!this.isConnected || this._compassState === "active") return;
      window.removeEventListener(
        "deviceorientationabsolute",
        this._orientationListener,
      );
      window.removeEventListener(
        "deviceorientation",
        this._orientationListener,
      );
      this._compassListening = false;
      this._compassStarting = false;
      this._compassState = "prompt";
      this._compassHeading = 0;
      this.style.setProperty("--atm-compass-heading", "0deg");
      this._render();
    }, 3000);
  }

  async _startCompass(requestPermission) {
    if (
      !this._config
      || this._effectiveOrientationMode() !== "device_compass"
      || this._compassListening
      || this._compassStarting
    ) {
      return;
    }
    const orientationApi = window.DeviceOrientationEvent;
    if (!orientationApi) {
      this._compassState = "unavailable";
      this._compassHeading = 0;
      this.style.setProperty("--atm-compass-heading", "0deg");
      if (requestPermission) this._render();
      return;
    }
    if (typeof orientationApi.requestPermission === "function") {
      const requestToken = ++this._compassRequestToken;
      this._compassStarting = true;
      this._compassState = "checking";
      try {
        let permission;
        try {
          permission = await orientationApi.requestPermission(true);
        } catch (error) {
          if (!error || error.name !== "TypeError") throw error;
          permission = await orientationApi.requestPermission();
        }
        if (requestToken !== this._compassRequestToken) return;
        this._compassStarting = false;
        if (permission !== "granted") {
          this._compassState = "denied";
          this._render();
          return;
        }
      } catch (error) {
        if (requestToken !== this._compassRequestToken) return;
        this._compassStarting = false;
        this._compassState = !requestPermission && error && error.name === "NotAllowedError"
          ? "prompt"
          : "unavailable";
        if (this._compassState === "unavailable") {
          this._compassHeading = 0;
          this.style.setProperty("--atm-compass-heading", "0deg");
        }
        this._render();
        return;
      }
    }
    if (
      !this.isConnected
      || !this._config
      || this._effectiveOrientationMode() !== "device_compass"
    ) {
      return;
    }
    window.addEventListener(
      "deviceorientationabsolute",
      this._orientationListener,
      true,
    );
    window.addEventListener("deviceorientation", this._orientationListener, true);
    this._compassListening = true;
    this._compassState = "checking";
    this._waitForCompassReading();
    this._render();
  }

  _handleOrientation(event) {
    let heading = Number(event.webkitCompassHeading);
    if (!Number.isFinite(heading)) {
      const alpha = Number(event.alpha);
      if (!Number.isFinite(alpha) || event.absolute === false) return;
      heading = (360 - alpha) % 360;
    }
    const firstReading = this._compassState !== "active";
    window.clearTimeout(this._compassReadyTimer);
    this._compassReadyTimer = undefined;
    this._compassStarting = false;
    this._compassState = "active";
    const now = Date.now();
    if (this._lastCompassUpdate && now - this._lastCompassUpdate < 80) return;
    this._lastCompassUpdate = now;
    this._compassHeading = (heading + 360) % 360;
    this.style.setProperty(
      "--atm-compass-heading",
      `${this._compassHeading.toFixed(1)}deg`,
    );
    if (firstReading) this._render();
  }

  _notifyCardSizeChanged() {
    const size = this.getCardSize();
    if (size === this._reportedCardSize) return;
    this._reportedCardSize = size;
    this.dispatchEvent(
      new CustomEvent("card-size-changed", {
        bubbles: true,
        composed: true,
      }),
    );
  }

  async _discoverLocation() {
    if (!this._hass) return;
    this._discovering = true;
    try {
      const locations = await this._hass.callWS({ type: `${API_PREFIX}/locations` });
      this._locations = Array.isArray(locations) ? locations : [];
      if (locations.length) {
        const configuredLocation = locations.find(
          (item) => item.entry_id === this._config.entry_id,
        );
        this._entryId = (configuredLocation || locations[0]).entry_id;
        this._restoreSnapshotCache();
        this._discoveryRetryAfter = 0;
        this._error = undefined;
      } else {
        this._discoveryRetryAfter = Date.now() + 30000;
      }
    } catch (error) {
      this._error = safeErrorText(error);
      this._discoveryRetryAfter = Date.now() + 30000;
    } finally {
      this._discovering = false;
      this._refresh(true);
    }
  }

  async _refresh(force = false) {
    if (this._config.data_mode !== "live") {
      this._snapshot = this._demoSnapshot(this._config.data_mode);
      this._error = undefined;
      this._render();
      this._notifyCardSizeChanged();
      return;
    }
    if (this._discovering && !this._entryId) return;
    const entryId = this._entryId || this._config.entry_id;
    if (!this._hass || !entryId || this._loading) return;
    const positionMode = this._effectivePositionMode();
    const dynamicPosition = this._dynamicPosition();
    const useCurrentUserTracker = (
      positionMode === "device"
      && this._positionFallback
      && !dynamicPosition
    );
    if (
      positionMode === "device"
      && !dynamicPosition
      && !useCurrentUserTracker
    ) {
      this._error = undefined;
      this._errorCode = this._positionLoading
        ? "device_location_waiting"
        : "device_location_unavailable";
      this._render();
      this._notifyCardSizeChanged();
      return;
    }
    if (
      positionMode === "tracker"
      && !this._config.tracker_entity
    ) {
      this._error = undefined;
      this._errorCode = "tracker_unavailable";
      this._render();
      this._notifyCardSizeChanged();
      return;
    }
    const now = Date.now();
    if (!force && this._lastRequest && now - this._lastRequest < 9000) return;
    this._loading = true;
    this._lastRequest = now;
    const request = Symbol("snapshot");
    this._activeRequest = request;
    try {
      const message = {
        type: `${API_PREFIX}/snapshot`,
        entry_id: entryId,
      };
      if (positionMode === "tracker") {
        message.tracker_entity = this._config.tracker_entity;
      } else if (useCurrentUserTracker) {
        message.use_current_user_tracker = true;
      } else if (dynamicPosition) {
        message.latitude = dynamicPosition.latitude;
        message.longitude = dynamicPosition.longitude;
        if (dynamicPosition.accuracy !== null) {
          message.position_accuracy_m = dynamicPosition.accuracy;
        }
      }
      const snapshot = await this._hass.callWS(message);
      if (this._activeRequest === request && this._config.data_mode === "live") {
        this._snapshot = snapshot;
        this._snapshotFromCache = false;
        this._storeSnapshotCache(snapshot);
        this._error = undefined;
        this._errorCode = undefined;
      }
    } catch (error) {
      if (this._activeRequest === request && this._config.data_mode === "live") {
        this._error = safeErrorText(error);
        this._errorCode = error && error.code === "location_not_supported"
          ? "location_not_supported"
          : error && error.code === "tracker_unavailable"
          ? "tracker_unavailable"
          : error && error.code === "user_tracker_unavailable"
          ? "user_tracker_unavailable"
          : this._snapshot
          ? undefined
          : "snapshot_waiting";
        this._snapshotFromCache = Boolean(this._snapshot);
        if (error && error.code === "not_found") {
          this._entryId = undefined;
          this._discoveryRetryAfter = 0;
        }
      }
    } finally {
      if (this._activeRequest === request) {
        this._loading = false;
        this._activeRequest = undefined;
      }
      this._render();
      this._notifyCardSizeChanged();
      if (!this._entryId && !this._discovering) this._discoverLocation();
    }
  }

  _demoSnapshot(mode) {
    const alert = mode === "demo_alert";
    const warning = mode === "demo_warning";
    const active = alert || warning;
    const statusSince = new Date(Date.now() - (active ? 17 : 228) * 60000).toISOString();
    const targets = active
      ? [
          {
            id: "demo-uav",
            category: "uav",
            title: "БпЛА",
            locality: "Демо-локація",
            region: "",
            distance_km: 18,
            bearing: 318,
            heading: 136,
            icon_rotation: 136,
            is_approaching: true,
            status: "active",
            image_url: assetUrl("shahed.png"),
            image_light_url: assetUrl("shahed-b.png"),
          },
          {
            id: "demo-missile",
            category: "missile",
            title: "Ракета",
            locality: "Навчальна ціль",
            region: "",
            distance_km: 46,
            bearing: 72,
            heading: 248,
            icon_rotation: 248,
            is_approaching: true,
            status: "active",
            image_url: assetUrl("rocket.png"),
            image_light_url: assetUrl("rocket-b.png"),
          },
          {
            id: "demo-recon",
            category: "recon",
            title: "Розвідник",
            locality: "Тестовий сектор",
            region: "",
            distance_km: 82,
            bearing: 205,
            heading: 30,
            icon_rotation: 30,
            is_approaching: false,
            status: "active",
            image_url: assetUrl("recon.png"),
            image_light_url: assetUrl("recon-b.png"),
          },
          {
            id: "demo-kab",
            category: "kab",
            title: "КАБ",
            locality: "Поза радіусом радара",
            region: "",
            distance_km: 124,
            bearing: 110,
            heading: null,
            icon_rotation: null,
            is_approaching: null,
            status: "active",
            image_url: assetUrl("kab.png"),
            image_light_url: assetUrl("kab-b.png"),
          },
          {
            id: "demo-fpv",
            category: "fpv",
            title: "FPV-дрон",
            locality: "Дальня ціль",
            region: "",
            distance_km: 151,
            bearing: 255,
            heading: 75,
            icon_rotation: 75,
            is_approaching: false,
            status: "active",
            image_url: assetUrl("fpv.png"),
            image_light_url: assetUrl("fpv-b.png"),
          },
        ]
      : [];
    return {
      demo: true,
      alert_active: active,
      alert_level: warning ? "yellow" : alert ? "red" : null,
      alert_reasons: warning ? ["Дронова загроза (жовтий рівень)"] : [],
      area: warning
        ? "Демонстраційне попередження"
        : alert
        ? "Демонстраційна тривога"
        : "Демонстраційний режим",
      oblast: "",
      available: true,
      status_since: statusSince,
      alert_since: active ? statusSince : null,
      status_image_url: assetUrl(active ? "danger.png" : "safe.png"),
      targets,
      analytics: {
        total: targets.length,
        within_100_km: targets.length,
        within_50_km: targets.filter((item) => item.distance_km <= 50).length,
        within_20_km: targets.filter((item) => item.distance_km <= 20).length,
        approaching: targets.filter((item) => item.is_approaching).length,
        stale: targets.filter((item) => item.status === "stale").length,
        uav: targets.filter((item) => item.category === "uav").length,
        fpv: targets.filter((item) => item.category === "fpv").length,
        recon: targets.filter((item) => item.category === "recon").length,
        missile: targets.filter((item) => item.category === "missile").length,
        ballistic: targets.filter((item) => item.category === "ballistic").length,
        kab: targets.filter((item) => item.category === "kab").length,
        aircraft: targets.filter((item) => item.category === "aircraft").length,
        unknown: targets.filter((item) => item.category === "unknown").length,
      },
    };
  }

  _renderRadar(targets, maxDistance, t) {
    const sweepDelay = -((Date.now() % 8000) / 1000);
    const marks = targets
      .filter((item) => item.distance_km <= maxDistance)
      .map((item) => {
        const angle = (Number(item.bearing) * Math.PI) / 180;
        const radius = Math.min(Number(item.distance_km) / maxDistance, 1) * 42;
        const left = 50 + Math.sin(angle) * radius;
        const top = 50 - Math.cos(angle) * radius;
        const hasHeading = hasTargetHeading(item);
        const rotation = targetIconRotation(item);
        const title = targetDisplayTitle(item, t);
        const body = item.image_url
          ? `<img src="${escapeHtml(item.image_url)}" alt="">`
          : `<span></span>`;
        const classes = [
          "target",
          hasHeading ? "" : "unknown-heading",
          item.status === "stale" ? "stale" : "",
        ].filter(Boolean).join(" ");
        const hint = hasHeading ? "" : ` · ${t.unknownDirection}`;
        return `<div class="${classes}" title="${escapeHtml(title)} · ${Math.round(item.distance_km)} ${t.distanceUnit}${escapeHtml(hint)}" style="left:${left}%;top:${top}%;transform:translate(-50%,-50%) rotate(${rotation}deg)">${body}${hasHeading ? "" : `<i style="transform:rotate(calc(var(--atm-compass-heading, 0deg) - ${rotation}deg))">?</i>`}</div>`;
      })
      .join("");
    return `
      <div class="radar" aria-label="Radar">
        <div class="ring r1"></div><div class="ring r2"></div><div class="ring r3"></div>
        <div class="axis horizontal"></div><div class="axis vertical"></div>
        <div class="sweep" style="animation-delay:${sweepDelay}s"></div>
        <div class="radar-world">
          <b class="north"><span>${t.north}</span></b>
          <b class="east"><span>${t.east}</span></b>
          <b class="south"><span>${t.south}</span></b>
          <b class="west"><span>${t.west}</span></b>
          ${marks}
        </div>
        <div class="home"></div>
      </div>`;
  }

  _showMoreInfo(entityId) {
    if (!entityId || typeof entityId !== "string") return;
    this.dispatchEvent(new CustomEvent("hass-more-info", {
      bubbles: true,
      composed: true,
      detail: { entityId },
    }));
  }

  _bindMoreInfo(selector, entityId) {
    if (!entityId || !this.shadowRoot) return;
    this.shadowRoot.querySelectorAll(selector).forEach((element) => {
      element.addEventListener("click", (event) => {
        event.stopPropagation();
        this._showMoreInfo(entityId);
      });
      element.addEventListener("keydown", (event) => {
        if (event.key !== "Enter" && event.key !== " ") return;
        event.preventDefault();
        event.stopPropagation();
        this._showMoreInfo(entityId);
      });
    });
  }

  _render() {
    try {
      this._renderContent();
    } catch (error) {
      console.error(`[Air Threat Radar ${ASSET_VERSION}] render failed`, error);
      if (!this.shadowRoot) return;
      const t = TEXT[language(this._hass)];
      const detail = safeErrorText(error) || "render_error";
      this.shadowRoot.innerHTML = `
        <style>
          :host{display:block}
          ha-card{box-sizing:border-box;min-height:96px;padding:14px;overflow:hidden;border-radius:20px;background:#3b4148;color:white}
          strong,span{display:block}
          span{margin-top:7px;font-size:11px;line-height:1.3;opacity:.78;overflow-wrap:anywhere}
        </style>
        <ha-card><strong>${t.cardError}</strong><span>${ASSET_VERSION} · ${escapeHtml(detail)}</span></ha-card>`;
    }
  }

  _renderContent() {
    if (!this.shadowRoot) return;
    const t = TEXT[language(this._hass)];
    const data = this._snapshot;
    const maxDistance = Number(valueOr(this._config.max_distance, 100));
    if (!data) {
      const automaticFallback = (
        this._config.position_mode === "auto"
        && this._errorCode === "user_tracker_unavailable"
      );
      const configuredLocation = this._configuredLocationLabel();
      const automaticFallbackMessage = t.automaticLocationFallback.replace(
        "{location}",
        configuredLocation,
      );
      const message = automaticFallback
        ? automaticFallbackMessage
        : this._errorCode === "tracker_unavailable"
        ? t.trackerUnavailable
        : this._errorCode === "user_tracker_unavailable"
        ? t.deviceLocationFallbackUnavailable
        : this._errorCode === "device_location_waiting"
        ? t.deviceLocationWaiting
        : this._errorCode === "device_location_denied"
        ? t.deviceLocationDenied
        : this._errorCode === "device_location_timeout"
        ? t.deviceLocationTimeout
        : this._errorCode === "device_location_position_unavailable"
        ? t.deviceLocationPositionUnavailable
        : this._errorCode === "device_location_unavailable"
        ? t.deviceLocationUnavailable
        : this._errorCode === "location_not_supported"
        ? t.dynamicLocationUnsupported
        : this._errorCode === "snapshot_waiting"
        ? t.loading
        : this._error || (this._discovering ? t.loading : t.noLocation);
      const retry = !automaticFallback && [
        "user_tracker_unavailable",
        "device_location_denied",
        "device_location_timeout",
        "device_location_position_unavailable",
        "device_location_unavailable",
      ].includes(this._errorCode)
        ? `<button id="location-retry" type="button">${escapeHtml(t.enableLocation)}</button>`
        : "";
      const automaticActions = automaticFallback
        ? `<div class="actions"><button id="location-fixed" type="button">${escapeHtml(t.useFixedLocation)}</button><button id="location-retry" type="button">${escapeHtml(t.retryGps)}</button></div>`
        : retry;
      this.shadowRoot.innerHTML = `<style>:host{display:block}ha-card{overflow:hidden;border-radius:20px}.message{min-height:100px;display:grid;place-items:center;padding:16px;text-align:center}.message>div{display:grid;justify-items:center;gap:10px;max-width:440px}.actions{display:flex;justify-content:center;gap:8px;flex-wrap:wrap}.message button{min-height:36px;padding:0 13px;border:1px solid rgba(255,255,255,.18);border-radius:8px;background:rgba(255,255,255,.12);color:inherit;font-family:inherit;font-size:12px;font-weight:700;line-height:1;cursor:pointer}</style><ha-card><div class="message"><div><span>${escapeHtml(message)}</span>${automaticActions}</div></div></ha-card>`;
      const fixedButton = this.shadowRoot.querySelector("#location-fixed");
      if (fixedButton) {
        fixedButton.addEventListener("click", (event) => {
          event.stopPropagation();
          this._setAutomaticFixedLocation(true);
          this._stopDeviceLocation();
          this._stopCompass();
          this._snapshot = undefined;
          this._error = undefined;
          this._errorCode = undefined;
          this._lastRequest = undefined;
          this._startCompass(false);
          this._refresh(true);
        });
      }
      const retryButton = this.shadowRoot.querySelector("#location-retry");
      if (retryButton) {
        retryButton.addEventListener("click", (event) => {
          event.stopPropagation();
          this._setAutomaticFixedLocation(false);
          this._stopDeviceLocation();
          if (this._config.orientation_mode === "auto") {
            this._stopCompass();
            this._startCompass(false);
          }
          this._startDeviceLocation();
        });
      }
      return;
    }
    const delayedData = degradedSnapshotWithinGrace(data);
    if (data.available === false && !delayedData) {
      this.shadowRoot.innerHTML = `
        <style>
          :host { display:block; letter-spacing:0; }
          ha-card { overflow:hidden; color:white; background:#3b4148; border-radius:20px; border:0; }
          .unavailable { min-height:116px; padding:18px; display:grid; align-content:center; gap:8px; }
          .unavailable strong { font-size:20px; line-height:1; }
          .unavailable span { max-width:520px; font-size:12px; line-height:1.35; opacity:.78; }
          .source { color:inherit; }
        </style>
        <ha-card><div class="unavailable"><strong>${t.unavailable}</strong><span>${t.unavailableDetail} ${t.informational} · <a class="source" href="https://neptun.in.ua/" target="_blank" rel="noreferrer">NEPTUN</a></span></div></ha-card>`;
      return;
    }

    const themeStyle = this._config.card_style === "theme";
    const lightTheme = Boolean(
      themeStyle
      && this._hass
      && this._hass.themes
      && this._hass.themes.darkMode === false
    );
    const darkTheme = themeStyle && !lightTheme;
    const orderedTargets = sortedTargets(data.targets);
    const nearby = orderedTargets.filter(
      (item) => targetDistance(item) <= maxDistance,
    );
    const visible = selectVisibleTargets(
      orderedTargets,
      maxDistance,
      valueOr(this._config.max_targets, "auto"),
    );
    const showRadar = data.alert_active && nearby.length > 0;
    const alertLevel = data.alert_active
      ? data.alert_level === "yellow" ? "yellow" : "red"
      : "safe";
    const warning = alertLevel === "yellow";
    const signalWarning = warning && !themeStyle;
    const rows = visible
      .map((item) => {
        const title = targetDisplayTitle(item, t);
        const place = item.locality || item.region;
        const stale = item.status === "stale" ? `<em>${t.stale}</em>` : "";
        const rotation = targetIconRotation(item);
        const listImageUrl = (signalWarning || lightTheme) && item.image_light_url
          ? item.image_light_url
          : item.image_url;
        return `
        <div class="row">
          ${listImageUrl ? `<img src="${escapeHtml(listImageUrl)}" alt="" style="transform:rotate(calc(${rotation}deg - var(--atm-compass-heading, 0deg)))">` : ""}
          <div class="target-copy"><strong>${escapeHtml(title)}</strong>${place ? `<span> · ${escapeHtml(place)}</span>` : ""}${stale}</div>
          <b>≈${Math.round(item.distance_km)} ${t.distanceUnit}</b>
        </div>`;
      })
      .join("");
    const nearest = nearby[0];
    const lang = language(this._hass);
    const statusSince = this._statusSince(data);
    const statusTime = formatStatusTime(statusSince, lang);
    const statusDuration = formatDuration(statusSince, lang);
    const statusTitle = warning ? t.warning : data.alert_active ? t.alert : t.safe;
    const durationLabel = warning
      ? t.warningDuration
      : data.alert_active
      ? t.alertDuration
      : t.safeDuration;
    const displayArea = data.place_name || data.area || data.oblast || "";
    const analytics = data.analytics || {};
    const totalTargets = Number(analytics.total || 0);
    const metricItems = totalTargets <= 0
      ? [{ key: "none", label: t.noActiveTargets, value: null }]
      : [
      { key: "total", label: t.targetsLabel, value: Number(analytics.total || 0) },
      { key: "uav", label: t.categoryCounts.uav, value: Number(analytics.uav || 0) },
      { key: "fpv", label: t.categoryCounts.fpv, value: Number(analytics.fpv || 0) },
      { key: "recon", label: t.categoryCounts.recon, value: Number(analytics.recon || 0) },
      {
        key: "missile",
        label: t.categoryCounts.missile,
        value: Number(analytics.missile || 0) + Number(analytics.ballistic || 0),
      },
      { key: "kab", label: t.categoryCounts.kab, value: Number(analytics.kab || 0) },
      { key: "aircraft", label: t.categoryCounts.aircraft, value: Number(analytics.aircraft || 0) },
      { key: "unknown", label: t.categoryCounts.unknown, value: Number(analytics.unknown || 0) },
    ].filter((item, index) => index === 0 || item.value > 0);
    const metrics = metricItems
      .map((item) => item.value === null
        ? `<span class="metric-${item.key}">${escapeHtml(item.label)}</span>`
        : `<span class="metric-${item.key}"><b>${item.value}</b> ${escapeHtml(item.label)}</span>`)
      .join("");
    const analyticsClass = [
      "analytics",
      metricItems.length === 1 ? "single" : "",
      metricItems.length >= 7 ? "dense" : metricItems.length >= 5 ? "compact" : "",
    ].filter(Boolean).join(" ");
    const compassLabel = this._compassState === "checking"
      ? t.compassWaiting
      : this._compassState === "unavailable"
      ? t.compassUnavailable
      : this._compassState === "denied"
      ? t.compassDenied
      : t.enableCompass;
    const compassControl = (
      this._effectiveOrientationMode() === "device_compass"
      && ["idle", "prompt", "denied", "checking"].includes(this._compassState)
    )
      ? `<button class="chip compass-enable" type="button"${this._compassState === "checking" ? " disabled" : ""}><ha-icon icon="mdi:compass"></ha-icon><span>${escapeHtml(compassLabel)}</span></button>`
      : "";
    const cardBackground = themeStyle
      ? "var(--ha-card-background, var(--card-background-color, #111315))"
      : warning
      ? "linear-gradient(135deg, #ffe27a 0%, #ffd24a 52%, #f4b91f 100%)"
      : data.alert_active
      ? "linear-gradient(135deg, #3f0303 0%, #8b0000 50%, #c1121f 100%)"
      : "linear-gradient(135deg, #1f6f2b 0%, #358d32 55%, #43a047 100%)";
    const cardColor = themeStyle
      ? "var(--primary-text-color, #f5f5f5)"
      : warning
      ? "#17130a"
      : "white";
    const mutedColor = themeStyle
      ? "var(--secondary-text-color, rgba(255,255,255,.68))"
      : warning
      ? "rgba(23,19,10,.70)"
      : "rgba(255,255,255,.68)";
    const dividerColor = themeStyle
      ? "var(--divider-color, rgba(127,127,127,.24))"
      : warning
      ? "rgba(23,19,10,.17)"
      : "rgba(255,255,255,.18)";
    const panelBackground = themeStyle
      ? "var(--secondary-background-color, rgba(127,127,127,.10))"
      : warning
      ? "rgba(255,255,255,.18)"
      : "rgba(0,0,0,.10)";
    const chipBackground = themeStyle
      ? lightTheme
        ? "var(--secondary-background-color, rgba(127,127,127,.14))"
        : "rgba(255,255,255,.075)"
      : warning
      ? "rgba(255,255,255,.38)"
      : "rgba(0,0,0,.22)";
    const chipBorder = darkTheme
      ? "rgba(255,255,255,.15)"
      : signalWarning
      ? "rgba(23,19,10,.16)"
      : dividerColor;
    const chipShadow = darkTheme
      ? "inset 0 1px 0 rgba(255,255,255,.08), 0 0 10px rgba(255,255,255,.035)"
      : themeStyle
      ? "none"
      : warning
      ? "inset 0 1px 0 rgba(255,255,255,.42), 0 2px 7px rgba(72,48,0,.12)"
      : "inset 0 1px 0 rgba(255,255,255,.10), 0 2px 7px rgba(0,0,0,.18)";
    const chipTextShadow = darkTheme
      ? "0 1px 2px rgba(0,0,0,.58)"
      : themeStyle
      ? "none"
      : warning
      ? "none"
      : "0 1px 3px rgba(0,0,0,.32)";
    const customStatusImageUrl = data.alert_active
      ? this._config.danger_image
      : this._config.safe_image;
    const statusImageUrl = (
      this._config.artwork_style === "custom"
      && customStatusImageUrl
    )
      ? customStatusImageUrl
      : data.status_image_url;
    const statusImageClass = warning
      ? "status-image warning-image"
      : "status-image";
    const alertMarkerUrl = assetUrl("danger.png");
    const statusMarker = themeStyle && showRadar
      ? `<img class="status-marker${warning ? " warning-image" : ""}" src="${escapeHtml(alertMarkerUrl)}" alt="">`
      : "";
    const cacheState = delayedData
      ? `<b class="cache-state delayed">${escapeHtml(t.dataDelayed)}</b>`
      : this._snapshotFromCache
      ? `<b class="cache-state">${escapeHtml(t.cachedUpdating)}</b>`
      : "";
    const entityIds = data.entity_ids || {};

    this.shadowRoot.innerHTML = `
      <style>
        :host { display:block; letter-spacing:0; }
        ha-card { position:relative; overflow:hidden; color:${cardColor}; background:${cardBackground}; border-radius:20px; border:${themeStyle ? `1px solid ${dividerColor}` : "0"}; }
        .demo-badge { position:absolute; z-index:5; top:8px; right:8px; padding:4px 7px; border-radius:5px; background:#ffd60a; color:#171717; font-size:9px; font-weight:950; box-shadow:0 2px 8px rgba(0,0,0,.3); }
        .top { min-height:132px; padding:14px 16px; display:grid; grid-template-columns:minmax(0,1fr) 126px; gap:10px; align-items:center; }
        h2 { margin:0; font-size:28px; line-height:1; letter-spacing:0; color:${cardColor}; text-shadow:${warning || themeStyle ? "none" : "0 2px 5px rgba(0,0,0,.28)"}; }
        .area { margin-top:5px; min-width:0; max-width:100%; display:grid; grid-template-columns:minmax(0,1fr); justify-items:start; gap:2px; color:${mutedColor}; font-size:13px; font-weight:700; line-height:1; text-shadow:${warning || themeStyle ? "none" : "0 1px 3px rgba(0,0,0,.25)"}; white-space:nowrap; }
        .place { min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
        .place-compact { display:none; }
        .from { flex:none; min-height:12px; display:inline-flex; align-items:center; gap:3px; color:${cardColor}; font-weight:850; font-variant-numeric:tabular-nums; line-height:1; opacity:.96; text-shadow:${warning || themeStyle ? "none" : "0 1px 4px rgba(0,0,0,.42)"}; white-space:nowrap; }
        .from.separated { margin-left:0; padding-left:0; border-left:0; }
        .clock-icon { flex:0 0 12px; width:12px; height:12px; display:grid; place-items:center; line-height:0; }
        .clock-icon ha-icon { display:block; width:12px; height:12px; --mdc-icon-size:12px; line-height:0; transform:translateY(-.5px); }
        .status-time { display:block; line-height:12px; }
        .chips { margin-top:7px; display:flex; flex-wrap:wrap; gap:6px; min-width:0; }
        .chip { display:inline-flex; align-items:center; justify-content:center; box-sizing:border-box; min-width:0; min-height:28px; max-width:100%; padding:0 10px; border-radius:999px; background:${chipBackground}; border:1px solid ${chipBorder}; color:${cardColor}; box-shadow:${chipShadow}; font-family:inherit; font-size:12px; font-weight:850; line-height:1; text-shadow:${chipTextShadow}; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
        .chip.duration { flex:none; background:${signalWarning || themeStyle ? chipBackground : "rgba(255,255,255,.16)"}; border-color:${chipBorder}; }
        .compass-enable { gap:5px; cursor:pointer; }
        .compass-enable ha-icon { flex:none; width:15px; height:15px; --mdc-icon-size:15px; }
        .compass-enable span { overflow:hidden; text-overflow:ellipsis; }
        .visual { width:126px; height:126px; position:relative; display:grid; place-items:center; justify-self:end; }
        .status-image { max-width:126px; max-height:126px; object-fit:contain; }
        .status-marker { position:absolute; z-index:6; top:-2px; right:-2px; width:36px; height:36px; object-fit:contain; filter:drop-shadow(0 2px 4px rgba(0,0,0,.34)); }
        .warning-image { filter:hue-rotate(42deg) saturate(.95) brightness(1.08) drop-shadow(0 2px 4px rgba(0,0,0,.34)); }
        .radar { width:112px; height:112px; position:relative; border-radius:50%; background:rgba(4,10,14,.48); border:1px solid rgba(255,255,255,.35); overflow:visible; }
        .ring { position:absolute; border:1px solid rgba(255,255,255,.27); border-radius:50%; inset:16.66%; }
        .ring.r2 { inset:33.33%; } .ring.r3 { inset:46%; }
        .axis { position:absolute; background:rgba(255,255,255,.22); }
        .axis.horizontal { left:0; right:0; top:50%; height:1px; }
        .axis.vertical { top:0; bottom:0; left:50%; width:1px; }
        .sweep { position:absolute; inset:4px; z-index:1; border-radius:50%; background:conic-gradient(from -24deg, rgba(255,255,255,.02) 0deg, rgba(255,255,255,.06) 8deg, rgba(255,255,255,.18) 25deg, rgba(255,255,255,.52) 47deg, rgba(255,255,255,.14) 61deg, transparent 78deg, transparent 360deg); filter:blur(2.2px); opacity:.95; animation:sweep 8s linear infinite; will-change:transform; }
        .radar-world { position:absolute; z-index:2; inset:0; border-radius:50%; transform:rotate(calc(0deg - var(--atm-compass-heading, 0deg))); transform-origin:50% 50%; transition:transform .16s linear; }
        .home { position:absolute; z-index:4; left:50%; top:50%; width:5px; height:5px; transform:translate(-50%,-50%); border-radius:50%; background:white; box-shadow:0 0 8px white; }
        .radar-world > b { position:absolute; font-size:7px; line-height:1; color:rgba(255,255,255,.82); }
        .radar-world > b span { display:block; transform:rotate(var(--atm-compass-heading, 0deg)); transition:transform .16s linear; }
        .north { top:-10px; left:50%; transform:translateX(-50%); } .south { bottom:-10px; left:50%; transform:translateX(-50%); }
        .east { right:-9px; top:50%; transform:translateY(-50%); } .west { left:-10px; top:50%; transform:translateY(-50%); }
        .target { position:absolute; width:18px; height:18px; display:grid; place-items:center; transform-origin:center; filter:drop-shadow(0 0 4px rgba(255,255,255,.8)); }
        .target img { width:18px; height:18px; object-fit:contain; } .target span { width:7px; height:7px; border-radius:50%; background:white; }
        .target.stale { opacity:.48; filter:grayscale(.45) drop-shadow(0 0 3px rgba(255,255,255,.45)); }
        .target.unknown-heading { outline:1px dashed rgba(255,255,255,.7); outline-offset:2px; border-radius:50%; }
        .target i { position:absolute; right:-5px; bottom:-5px; width:9px; height:9px; display:grid; place-items:center; border-radius:50%; background:#17191c; color:white; font:700 7px/1 sans-serif; }
        .list { border-top:1px solid ${dividerColor}; background:${panelBackground}; }
        .row { min-height:38px; padding:0 14px; display:grid; grid-template-columns:28px minmax(0,1fr) auto; gap:8px; align-items:center; border-bottom:1px solid ${dividerColor}; font-size:12px; }
        .row img { width:24px; height:24px; object-fit:contain; transform-origin:center; filter:${signalWarning || lightTheme ? "none" : themeStyle ? "drop-shadow(0 0 2px rgba(0,0,0,.88))" : "drop-shadow(0 0 3px rgba(255,255,255,.36))"}; }
        .target-copy { min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
        .target-copy span { color:${mutedColor}; }
        .target-copy em { margin-left:6px; padding:2px 4px; border-radius:3px; background:rgba(127,127,127,.20); font-size:8px; font-style:normal; opacity:.82; }
        .footer { min-height:27px; padding:0 10px; display:grid; grid-template-columns:minmax(0,1fr) auto; align-items:center; gap:8px; background:${panelBackground}; }
        .analytics { min-width:0; display:flex; align-items:center; justify-content:space-between; gap:5px; font-size:9px; opacity:.82; }
        .analytics span { flex:0 1 auto; min-width:0; overflow:hidden; text-overflow:clip; white-space:nowrap; text-align:center; }
        .analytics.single { justify-content:flex-start; }
        .analytics.single span { text-align:left; }
        .analytics b { font-size:11px; }
        .metric-uav b { color:#74ddff; }
        .metric-fpv b { color:#c8b6ff; }
        .metric-recon b { color:#9ce5bd; }
        .metric-missile b { color:#ff8796; }
        .metric-kab b { color:#ffd166; }
        .metric-aircraft b { color:#ffb86b; }
        .metric-unknown b { color:#c8cdd3; }
        ${signalWarning ? ".analytics b { color:#17130a; }" : ""}
        .credit { font-size:8px; opacity:.58; white-space:nowrap; }
        .cache-state { margin-right:5px; color:#ffd166; font-size:8px; font-weight:800; opacity:1; }
        .cache-state.delayed { text-transform:uppercase; }
        .source { color:inherit; text-decoration:none; }
        .message { min-height:100px; display:grid; place-items:center; padding:16px; text-align:center; }
        .more-info-zone { cursor:pointer; }
        @keyframes sweep { to { transform:rotate(360deg); } }
        @media (max-width:380px) {
          .top { min-height:112px; grid-template-columns:minmax(0,1fr) 96px; gap:4px; padding:12px 10px 12px 12px; }
          h2 { font-size:23px; } .visual { width:96px; height:96px; }
          .area { margin-top:5px; display:grid; grid-template-columns:minmax(0,1fr); justify-items:start; gap:2px; font-size:11px; }
          .place-full { display:none; }
          .place-compact { display:block; max-width:100%; overflow:visible; text-overflow:clip; }
          .from.separated { margin-left:0; padding-left:0; border-left:0; }
          .clock-icon { flex-basis:11px; width:11px; height:11px; }
          .clock-icon ha-icon { width:11px; height:11px; --mdc-icon-size:11px; transform:translateY(-1px); }
          .status-time { line-height:11px; }
          .chips { margin-top:5px; gap:5px; }
          .chip { min-height:26px; padding:0 9px; font-size:10.5px; }
          .radar { width:84px; height:84px; } .status-image { max-width:96px; max-height:96px; }
          .status-marker { width:30px; height:30px; }
          .row { grid-template-columns:24px minmax(0,1fr) auto; padding:0 10px; gap:6px; font-size:11px; }
          .row img { width:20px; height:20px; }
          .footer { padding:0 7px; gap:4px; }
          .analytics { gap:4px; font-size:7.8px; }
          .analytics.compact { font-size:7.2px; }
          .analytics.dense { gap:3px; font-size:6.4px; }
          .analytics b { font-size:9px; }
          .credit > span { display:none; }
          .credit { font-size:6.5px; }
        }
      </style>
      <ha-card>
        ${data.demo ? `<div class="demo-badge">${t.demo}</div>` : ""}
        <div class="top">
          <div class="status-copy more-info-zone" role="button" tabindex="0"><h2>${statusTitle}</h2><div class="area">${displayArea ? `<span class="place place-full" title="${escapeHtml(displayArea)}">${escapeHtml(compactDistrictName(displayArea))}</span><span class="place place-compact" title="${escapeHtml(displayArea)}">${escapeHtml(compactDistrictName(displayArea))}</span>` : ""}${statusTime ? `<span class="from${displayArea ? " separated" : ""}"><span class="clock-icon"><ha-icon icon="mdi:clock-outline"></ha-icon></span><span class="status-time">${statusTime}</span></span>` : ""}</div>
          <div class="chips">${statusDuration ? `<div class="chip duration">${durationLabel} ${statusDuration}</div>` : ""}${nearest ? `<div class="chip nearest-chip more-info-zone" role="button" tabindex="0">${escapeHtml(targetDisplayTitle(nearest, t))} ≈${Math.round(nearest.distance_km)} ${t.distanceUnit}${nearest.status === "stale" ? ` · ${t.stale}` : ""}</div>` : ""}${compassControl}</div></div>
          <div class="visual more-info-zone" role="button" tabindex="0">${showRadar ? this._renderRadar(nearby, maxDistance, t) : `<img class="${statusImageClass}" src="${escapeHtml(statusImageUrl)}" alt="">`}${statusMarker}</div>
        </div>
        ${this._config.show_target_list !== false && rows ? `<div class="list more-info-zone" role="button" tabindex="0">${rows}</div>` : ""}
        <div class="footer"><div class="${analyticsClass} more-info-zone" role="button" tabindex="0">${metrics}</div><span class="credit">${cacheState}<span>${t.informational} · </span><a class="source" href="https://neptun.in.ua/" target="_blank" rel="noreferrer">NEPTUN</a></span></div>
      </ha-card>`;
    const compassButton = this.shadowRoot.querySelector(".compass-enable");
    if (compassButton) {
      compassButton.addEventListener("click", (event) => {
        event.stopPropagation();
        this._startCompass(true);
      });
    }
    this._bindMoreInfo(".status-copy", entityIds.air_alert);
    this._bindMoreInfo(".nearest-chip, .visual", entityIds.nearest_threat);
    this._bindMoreInfo(".list, .analytics", entityIds.active_threats);
  }
}

if (!customElements.get(CARD_TYPE)) {
  customElements.define(CARD_TYPE, AirThreatRadarCard);
}
if (!customElements.get(EDITOR_TYPE)) {
  customElements.define(EDITOR_TYPE, AirThreatRadarCardEditor);
}
registerCardMetadata();

})();
