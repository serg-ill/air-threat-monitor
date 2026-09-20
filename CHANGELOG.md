# Changelog

## 0.4.1

- Fixed the yellow warning state overriding the neutral Home Assistant theme
  card style. Theme-aware cards now keep their configured light or dark
  background, text, dividers, chips, and target icons for safe, yellow, and red
  states; the signal-color style remains green, amber, and red.

## 0.4.0

- Added support for NEPTUN's `yellow` warning level alongside red air alerts.
- Preserve the provider's alert level and reasons in the air-alert entity,
  card snapshot, and privacy-safe diagnostics.
- Added a distinct amber signal-card state and yellow warning artwork treatment.
- Added a yellow-level demonstration mode to the graphical card editor.
- Track yellow and red periods independently so their displayed duration resets
  when the provider changes level.
- Prefer any matching red alert over a narrower yellow warning to avoid
  understating the current local status.

## 0.3.3

- Added local Home Assistant brand logos alongside the bundled integration
  icons, following the custom-integration brand image format introduced in
  Home Assistant 2026.3.
- Added release validation for all standard and high-DPI integration brand
  images.

## 0.3.2

- Fixed the project logo and alert demonstration image in the HACS repository
  description by using HACS-compatible Markdown image links.
- Added the updated alert demonstration screenshot to the card-style comparison
  in the project documentation.

## 0.3.1

- Keep the last successful radar snapshot visible for up to 60 seconds after a
  transient provider update failure.
- Mark the retained snapshot with a visible `data delayed` status instead of
  immediately replacing the entire card with the unavailable-data screen.
- Continue to show the full unavailable-data warning when no valid snapshot
  exists or the last successful update is more than 60 seconds old.

## 0.3.0

- First public release of Air Threat Monitor and the bundled Air Threat Radar
  card.
- Replaced the provider-branded device model with the independent
  `Air threat location monitor` name and linked device details to the project
  documentation.

- Removed optional branded decorative artwork and its selector from the public
  integration, documentation, and release archives.
- Keep the standard shield artwork as the only public card-editor choice.
- Added a generic YAML-only `custom` artwork mode that loads user-owned local
  safe and alert images without distributing them with the integration.
- Documented the `/config/www/` location and YAML options for custom safe and
  alert artwork.
- Gracefully return old unsupported artwork settings to the standard shields
  instead of showing a card configuration error.
- Removed the decorative middle dot between the nearest target type and its
  distance in the top badge.

The entries below document private development builds that were not published
as public releases.

## 0.2.0-beta.27

- Keep the compass control visible in a waiting state until the card receives
  the first valid device-orientation reading.
- Return to an actionable compass button after three seconds when iOS grants
  permission but sends no orientation data.
- Reinitialize compass listeners after the Companion App or browser returns
  to the foreground.
- Mark compass tracking active only after a real heading arrives, preventing a
  silent north-up radar with a hidden enable button.

## 0.2.0-beta.26

- Replace the zero-value footer counter with the explicit
  `Активних цілей немає` message.
- Hide the nearby-target badge completely when no target matches the selected
  radar radius instead of displaying a redundant empty-state badge.
- Add independent tap zones for alert status, nearest threat, and active-target
  analytics that open the corresponding standard Home Assistant More Info
  dialog.
- Resolve entity IDs through the Home Assistant entity registry so More Info
  continues to work after users rename integration entities.

## 0.2.0-beta.25

- Place the compact district name and status time on two dedicated metadata
  rows in every layout so they no longer compete for limited horizontal space.
- Tightened only the metadata and badge spacing to offset the additional time
  row.
- Kept the beta.22 artwork, radar, heading, badge, target-row, and footer
  dimensions unchanged.

## 0.2.0-beta.24

- Restored the complete beta.22 sizing and viewport-responsive layout after
  the beta.23 container query made narrow dashboard cards overly compact.
- Use the shortened Ukrainian district form in the regular metadata row as
  well as the mobile row, keeping the district visible beside the status time.
- Keep the clock and time after the existing vertical metadata divider on
  desktop and Ubuntu kiosk layouts.

## 0.2.0-beta.23

- Switched compact-card styling from a viewport media query to an
  `air-threat-card` container query.
- Narrow cards inside wide desktop and Ubuntu kiosk dashboards now use the
  same compact location-and-time layout as narrow mobile cards.
- Kept the beta.22 compact visual styling unchanged.

## 0.2.0-beta.22

- Stack the compact district name and status time on separate rows below
  380 px so neither item competes for the same narrow line.
- Removed the mobile divider from the stacked time row and tightened the
  surrounding spacing to avoid unnecessary card-height growth.
- Kept the wide-card metadata row and all status badges unchanged.

## 0.2.0-beta.21

- Made the mobile Ukrainian district abbreviation tolerant of trailing spaces
  and extra location suffixes, preventing `район` from being ellipsized.
- Wrapped the status clock in a fixed-size alignment box so its icon remains
  vertically centered in both Safari and Chromium kiosks.
- Kept the existing duration and nearest-target badges unchanged.

## 0.2.0-beta.20

- Reworked the top status metadata into one compact location-and-time row.
- Added a separate clock icon, stronger time contrast, tabular numerals, and
  a subtle divider so the status start time remains legible.
- Automatically abbreviate a trailing Ukrainian `район` to `р-н` below
  380 px while preserving the full location name on larger cards.
- Slightly reduced and right-aligned the mobile radar area to give location
  text more usable width without changing the card's badges.

## 0.2.0-beta.19

- Added a recommended automatic target-list mode for new cards.
- Automatic mode shows up to five nearest targets inside the selected radar
  radius and falls back to one nearest target when the radius is empty.
- Kept the existing manual limits from one to five targets for cards that need
  a fixed list size.
- Made card height follow the actual automatic target count without reserving
  empty rows.

## 0.2.0-beta.18

- Cache the last successful live snapshot locally for up to 30 minutes and
  render it immediately while Home Assistant, browser GPS, or the websocket
  connection resumes after an unlock or restart.
- Isolate cached snapshots by integration entry, position mode, and selected
  tracker so one family member or configured location cannot inherit another
  card's data.
- Keep the last rendered snapshot during transient refresh failures and mark
  it with a small `updating…` status until fresh data arrives.
- Prevent structured browser and websocket errors from appearing as
  `[object Object]` or a bare numeric error code.
- Always use the standard alert shield as the small neutral-theme radar status
  marker, while optional artwork remains the large safe-state illustration.

## 0.2.0-beta.17

- Identify legacy Ubuntu/Linux x86 Chromium kiosks as stationary clients even
  when they use a mobile-looking user agent and expose no `userAgentData`.
- Force fixed positioning and north-up orientation on those kiosks, preventing
  browser GPS prompts and persistent compass controls.
- Limit the visual editor on an Ubuntu/Linux kiosk to the configured fixed
  location list; mobile positioning and compass choices remain available on
  supported phones and tablets.
- Added an optional decorative artwork selector alongside the standard shield
  set. This bundled option was removed from later public releases.
- Kept standard shields as the default for all existing cards and YAML.

## 0.2.0-beta.16

- Unified the configured-location and position-source controls into one
  position selector in the visual card editor.
- Selecting a named location now activates fixed positioning and its matching
  integration entry in one step.
- Automatic mode now uses live GPS on supported iOS, iPadOS, and Android
  clients, with the existing person and configured-location fallbacks.
- Desktop browsers, macOS, and Ubuntu kiosks now skip browser GPS in automatic
  mode and immediately use the configured fixed location without permission
  prompts or unavailable-location controls.
- Explicit live-GPS and person/tracker modes remain available, and existing
  YAML card configurations remain compatible.

## 0.2.0-beta.15

- Treat a failed compass startup as a definitive north-up fallback for the
  current card instance.
- Hide the compass control entirely when the browser reports the compass as
  unavailable, regardless of its platform or user-agent claims.
- Keep retry controls only for meaningful mobile states: initial permission,
  permission prompt, and denied permission.
- Reset any stale compass rotation when falling back to north-up.

## 0.2.0-beta.14

- Hardened compass capability detection for touch-enabled Chromium kiosks
  whose user-agent string resembles a mobile browser.
- Chromium's platform and `userAgentData.mobile` signals now take precedence
  over a spoofed mobile user-agent.
- Ubuntu kiosks silently stay north-up without a compass warning or button,
  while supported iOS/iPadOS and Android clients retain compass controls.

## 0.2.0-beta.13

- Compass controls are now offered only to secure iOS/iPadOS or Android
  clients with touch input and the Device Orientation API.
- Desktop Chrome, macOS browsers, and Ubuntu kiosks automatically keep north
  at the top and no longer display an unusable compass confirmation button.
- Explicit device-compass mode also falls back safely on unsupported clients,
  allowing one shared card configuration across phones, desktops, and kiosks.

## 0.2.0-beta.12

- Added a persistent status journal for districts and oblasts visited through
  automatic, live-GPS, and person/tracker card modes.
- Dynamic coordinates are matched to stable GeoJSON district/oblast keys; the
  card can therefore display alert/safe start time and duration even when its
  visible heading is only a city, town, or village name.
- Once a dynamic area has been observed, its alert state continues to be
  checked on every provider refresh and survives Home Assistant restarts.
- Active alerts use the provider's start timestamp. A previously unseen safe
  area starts tracking when the integration first observes it because an
  earlier all-clear timestamp is not available from the live feed.
- District and oblast states remain isolated, preventing one location's
  duration from being displayed for another location.

## 0.2.0-beta.11

- Restored the alert/safe start time and duration for automatic, live-GPS, and
  person/tracker cards when their dynamic position resolves to the same
  monitored district as the configured integration location.
- Reuse the coordinator's persisted status transition time only for an exact
  district match, or an exact oblast match when district data is unavailable.
- Keep the duration hidden for a different dynamically selected area when no
  trustworthy end-of-alert timestamp is available, avoiding fabricated or
  Unix-epoch durations.

## 0.2.0-beta.10

- Added an opt-in **Automatic for this device** position mode for sharing one
  Lovelace card between phones, tablets, desktop browsers, and kiosks.
- Automatic mode first tries browser GPS, then the signed-in Home Assistant
  user's linked `person` entity.
- When neither dynamic source is available, the card explicitly offers the
  configured integration location instead of silently using it.
- The fixed-location choice is stored only in that browser and for that
  integration entry, allowing a kiosk to remember its choice without changing
  the same card on family phones.
- Added an **Automatic** radar orientation mode: supported mobile devices with
  live device positioning can use the compass, while fixed and non-mobile
  displays remain north-up.
- Existing cards keep their current position and orientation modes until the
  new automatic options are selected in the visual editor.

## 0.2.0-beta.9

- Added a visible **Detecting device location** state immediately after a
  live-GPS request starts.
- Retry browser geolocation automatically with a lower-accuracy request after
  a high-accuracy timeout or unavailable-position response.
- Fall back to the authenticated Home Assistant user's linked `person` entity
  only when both browser geolocation attempts fail.
- Added distinct messages for denied permission, timeout, unavailable device
  position, and unavailable user tracker instead of leaving an empty card.
- Keep successful phone GPS behavior unchanged and continue updating it through
  a live position watch.

## 0.2.0-beta.8

- Added automatic city, town, or village labels for **Live GPS of this
  device** cards.
- Match the active Home Assistant user to their linked `person` entity, then
  reuse only the Geocoded Location sensor attached to that person's active
  Companion App device.
- Accept the locality only when the person's Home Assistant coordinates are
  within 5 km of the browser GPS position, preventing stale or unrelated
  addresses from being displayed.
- Fall back to the dynamically resolved district or oblast when no safe
  locality match is available. No coordinates are sent to an external
  geocoding service.

## 0.2.0-beta.7

- Restore an already granted iOS compass permission automatically after a card
  or dashboard reload.
- Show the **Enable compass** button only when WebKit still requires a fresh
  user gesture, while preserving explicit denied and unavailable states.
- Cancel pending compass permission checks safely when the card disconnects or
  switches back to north-up mode.

## 0.2.0-beta.6

- Added automatic city, town, or village labels for person/tracker cards when
  the Home Assistant Companion App exposes a Geocoded Location sensor.
- The integration follows the selected person's active `device_tracker` and
  accepts a place name only from a geocoded sensor attached to that same Home
  Assistant device.
- Kept the automatically resolved district or oblast as a fallback when no
  matching geocoded sensor is available.
- No manual place sensor selector was reintroduced, preventing coordinates and
  place labels from different devices from being mixed.

## 0.2.0-beta.5

- Removed the separate geocoded-location selector from person/tracker mode.
- Person and tracker cards now always display the district or oblast resolved
  automatically from the same coordinates used for threat calculations.
- Existing cards silently ignore a previously saved `geocoded_entity`, so a
  manually selected place name can no longer disagree with the actual tracker
  position.
- Increased dark-theme status-chip contrast with a restrained translucent
  background, border, and inner highlight.
- Standardized chip height and vertical text alignment across desktop, mobile,
  and narrow kiosk layouts.

## 0.2.0-beta.4

- Added dedicated dark target artwork for light Home Assistant themes.
- The target list now switches automatically between white and dark artwork
  using Home Assistant's active light/dark theme state.
- Dark target artwork is used only in the lower target list. Radar markers
  retain the original white artwork for contrast against the dark radar.
- Removed glow and drop-shadow effects from the dark light-theme artwork.
- Included both artwork variants in live and demonstration snapshots.

## 0.2.0-beta.3

- Fixed dynamic safe-state timestamps being interpreted as the Unix epoch,
  which produced impossible dates and durations measured in tens of thousands
  of days.
- Dynamic cards now show provider alert time when available and start a local
  duration only after an actual state transition observed by the open card.
- Prevented a geocoded sensor selected for tracker mode from leaking a stale
  address into the live-GPS mode.
- Renamed the position choices to clearly distinguish a fixed integration
  location, live GPS of the viewing device, and a Home Assistant person or
  tracker.
- Added an optional theme-adaptive card style. It follows the active Home
  Assistant light or dark theme while retaining the bundled safe/alert artwork
  as a compact status marker.
- Kept the original red and green signal-card design as the default for all
  existing cards.

## 0.2.0-beta.2

- Resolve selected `person` and `device_tracker` coordinates inside Home
  Assistant for every card request, preventing calculations from silently
  falling back to another configured location.
- Return an explicit unavailable state when the selected tracker has no valid
  coordinates, plus non-sensitive position-source metadata for diagnostics.
- Added a prominent permission button for device-compass mode, including clear
  unavailable and denied states on iPhone.
- Restored the production red and green gradients, translucent status chips,
  subtle text shadows, and the softer radar sweep.
- Standardized long provider titles to the compact `КАБ` and `Розвідник`
  labels throughout the card.

## 0.2.0-beta.1

- Added a **This device location** mode. One shared card can now recalculate
  itself independently from the geolocation of each viewing phone or tablet.
- Added an explicit dynamic-position mode using a Home Assistant `person` or
  `device_tracker` entity.
- Recalculate distances, bearings, administrative area, and current alert for
  each card location without additional requests to NEPTUN.
- Added an optional geocoded-location sensor for displaying the viewer's
  current locality.
- Added an optional device-compass mode. The radar's world layer follows the
  viewing device while north-up remains the safe default.
- Kept location and compass state local to the viewing card so several family
  members can use one dashboard without overwriting the integration location.
- Reworked the radar sweep into a wider, softer beam and kept its animation
  independent from compass rotation.
- Changed status chips to white and localized distance units
  (`км` in Ukrainian, `km` in English).

## 0.1.0-beta.12

- Load the bundled Lovelace card through one resource path instead of injecting
  the same script globally and as a Lovelace module.
- Removed runtime prototype replacement of an already registered custom element,
  eliminating intermittent configuration errors after a full page reload.

## 0.1.0-beta.11

- Register the complete card class instead of upgrading an early placeholder,
  fixing configuration errors after a full browser reload.
- Keep card and editor registration independent, with the card registered first
  so an editor conflict cannot leave the card picker waiting.

## 0.1.0-beta.10

- Register a lightweight card shell before the full frontend module initializes,
  preventing the Home Assistant card picker from waiting indefinitely.
- Upgrade the card and editor independently so a cached editor definition cannot
  block the card tile or its visual editor.

## 0.1.0-beta.9

- Recover cards automatically when a previously selected location was deleted.
- Refresh existing card-picker metadata instead of leaving a stale loading preview.
- Show coordinates in the visual editor so locations with the same district name
  can be distinguished.

## 0.1.0-beta.8

- Rotated target artwork in the target list from the same calculated heading
  used by the radar markers, keeping both views visually consistent.
- Kept icons upright only when the source does not provide a usable heading.

## 0.1.0-beta.7

- Replaced optional chaining and nullish coalescing in the bundled card for
  compatibility with older Chromium kiosk installations.
- Added safe in-place card/editor prototype upgrades when Home Assistant loads
  both a cached and a newly versioned frontend resource in one browser session.

## 0.1.0-beta.6

- Tightened wrapped area names and shortened the no-target message on narrow
  cards without changing the wide layout.
- Replaced equal-width analytics columns with a flexible single-row footer so
  totals are no longer truncated on small screens.
- Added distinct target-category colors and adaptive footer typography for
  crowded target summaries.

## 0.1.0-beta.5

- Matched the legacy monitor's counting rules by excluding provider-marked
  stale targets from the list, nearest target, entities, and grouped totals.
- Left-aligned the single zero-target footer value.
- Replaced `String.prototype.replaceAll` in the bundled card for compatibility
  with older Chromium kiosk builds.

## 0.1.0-beta.4

- Replaced all target silhouettes with the final user-supplied transparent PNG
  artwork for UAV, FPV, missile, recon, guided bomb, and aircraft targets.
- Fixed the radar sweep restarting before a full turn when the card refreshes.
- Decoupled the target list from the radar radius and increased the selectable
  list limit to 20 targets.
- Added persisted alert/safe start time and live duration to the card and air
  alert entity.
- Added compact grouped target counts for UAV, FPV, recon, missile, guided
  bomb, aircraft, and unknown targets.
- Let Home Assistant size the card directly from its rendered content instead
  of reserving fixed section rows, and aligned card rounding with the
  production dashboard style.
- Isolated the frontend module so fallback and Lovelace resource loading cannot
  conflict on kiosk browsers.

## 0.1.0-beta.3

- Fixed the bundled radar card not being loaded by the Home Assistant frontend.
- Added automatic Lovelace resource creation and version updates in storage
  mode, while retaining the frontend module loader as a fallback.
- Added duplicate-resource cleanup and regression coverage for card resource
  registration.

## 0.1.0-beta.2

- Fixed the card picker entry being stuck on an unselectable live preview.
- Added strict validation for threat, alert, and GeoJSON API responses so a
  malformed payload cannot be interpreted as a safe state.
- Added an explicit unavailable state and stopped the card from silently
  showing a stale snapshot after an update failure.
- Distinguished provider-marked stale targets in entities and the card.
- Fixed stale snapshots after changing location, duplicate refresh timers,
  request retry floods, and invalid card configuration values.
- Improved target rows and the footer on narrow dashboard columns.
- Prevented unchanged coordinator refresh timestamps from creating Recorder
  state writes every ten seconds and removed refresh-only timestamps from
  entity attributes.
- Added cache-busting to bundled images and reduced oversized image assets.
- Prevented monitored coordinates from appearing as the config entry and
  device name when GeoJSON does not provide a human-readable area name.
- Kept config-entry identity stable during location reconfiguration and added
  a separate duplicate-location check.
- Added automatic migration of coordinate-named entries created by beta.1.
- Expanded GeoJSON property matching for district and region names.
- Added integration-local brand assets for supported Home Assistant versions
  and retained repository brand assets for HACS.
- Added release tag validation and regression coverage for safety-critical
  payload handling and packaging.

## 0.1.0-beta.1

- Added UI-based setup with automatic use of the Home Assistant location.
- Added local air-alert, nearest-threat, and active-target entities.
- Added a bundled north-up radar card with a graphical editor and automatic
  registration in the Home Assistant card picker.
- Added bundled status and target images; no `/config/www` setup is required.
- Added live, safe-demo, and alert-demo card modes.
- Added privacy-safe integration diagnostics.
- Added HACS metadata, validation workflows, and reproducible release archives.
