# Release candidate testing checklist

Thank you for testing Air Threat Monitor.

## Before testing

- Keep an official air-alert application or notification channel enabled.
- Do not use this integration as the only source of safety information.
- Do not publish screenshots or diagnostics containing your exact coordinates.

## Installation

- [ ] Home Assistant starts without integration errors.
- [ ] Air Threat Monitor appears in **Add integration**.
- [ ] The form pre-fills the Home Assistant coordinates.
- [ ] A valid location creates exactly three entities.
- [ ] Reconfigure changes the monitored location and reloads the entry.
- [ ] **Developer tools > Actions** exposes
      `air_threat_monitor.get_targets` with a required location selector.
- [ ] Calling `air_threat_monitor.get_targets` with response data enabled
      returns `count`, `updated_at`, and the complete sorted `targets` list.
- [ ] Each returned target has distance, bearings, heading/direction,
      approach, risk, status, and image fields but no exact coordinates.

## Card

- [ ] Air Threat Radar appears in the standard **Add card** dialog.
- [ ] The graphical editor uses one position selector for automatic mode,
      live GPS, a person/tracker, and every configured fixed location.
- [ ] Selecting a named fixed location changes both the position mode and the
      integration entry without a second location selector.
- [ ] On Ubuntu/Linux x86, the editor offers only configured fixed locations
      and does not offer GPS, a person/tracker, or compass orientation.
- [ ] **Demo: safe** shows the safe image and a visible `DEMO` label.
- [ ] **Demo: yellow level** shows an amber signal card, the
      `ЖОВТИЙ РІВЕНЬ` heading, and amber warning artwork.
- [ ] **Demo: alert** shows sample targets on a north-up radar.
- [ ] **Standard** card height preserves the existing layout.
- [ ] **Compact** card height reduces the header, target rows, and footer
      without clipping headings, badges, radar marks, or analytics.
- [ ] Card corners follow `--ha-card-border-radius` in both visual styles.
- [ ] The radar sweep completes full turns without jumping back during refresh.
- [ ] **Automatic (recommended)** shows up to five targets inside the selected
      radar radius and no empty rows.
- [ ] When no target is inside the selected radar radius, automatic mode shows
      exactly one nearest active target.
- [ ] Manual limits from one to five still show that maximum number of nearest
      active targets even when they are outside the selected radar radius.
- [ ] Changing between automatic and manual limits adjusts card height to the
      number of rows actually displayed.
- [ ] On cards narrower than 380 px, `район` is displayed as `р-н` on one
      line even when the source name contains trailing spaces or a suffix;
      wider cards keep the full location name.
- [ ] On cards narrower than 380 px, the compact district and status time use
      separate tightly spaced rows without increasing the empty space around
      the existing badges.
- [ ] Wide desktop and Ubuntu kiosk layouts retain the established image,
      radar, heading, badge, target-row, and footer sizes.
- [ ] The regular desktop/kiosk metadata row abbreviates `район` to `р-н` and
      shows the status time on the next tightly spaced row without truncating
      the district name.
- [ ] The status start time has a clock icon, remains visually separate from
      the location, stays vertically centered in Safari and Chromium, and
      does not wrap or merge with the location.
- [ ] Existing duration and nearest-target badges are visually unchanged.
- [ ] Safe, yellow-level, and red-alert start times and durations are visible
      and continue correctly after a Home Assistant restart.
- [ ] A yellow-to-red or red-to-yellow transition starts a new level duration.
- [ ] The footer shows total and grouped target counts.
- [ ] When the active-target total is zero, the footer says
      `Активних цілей немає` instead of `0 цілей`.
- [ ] When no target matches the selected radar radius, the
      `Цілей поруч немає` badge is hidden while the duration badge remains.
- [ ] Tapping the alert heading/time opens More Info for the air-alert entity.
- [ ] Tapping the radar or nearest-target badge opens More Info for the
      nearest-threat entity.
- [ ] Tapping the target list or footer analytics opens More Info for the
      active-target count entity.
- [ ] More Info tap zones still work after any of the three entities are
      renamed in Home Assistant.
- [ ] The nearest-target badge has no decorative middle dot between its type
      and distance.
- [ ] YAML-only custom artwork loads `safe_image` and `danger_image` from
      `/local/` and falls back to the standard shield when a URL is empty.
- [ ] A selected `person` or `device_tracker` changes distances without
      changing another card's configured position.
- [ ] Tracker mode follows the selected entity after another configured
      integration location is added, removed, or reconfigured.
- [ ] **Live GPS of this device** makes the same shared card show different
      distances on two phones at different positions.
- [ ] For first-time live-GPS and compass setup, adding the card from the
      official Home Assistant Companion App requests precise-location and
      motion/orientation permissions on that phone.
- [ ] Opening the same shared card on hardware without GPS or a compass hides
      or disables unsupported controls without changing the mobile card
      configuration.
- [ ] Starting live GPS immediately shows a visible location-progress state.
- [ ] Desktop Chrome, macOS, and an Ubuntu kiosk skip browser GPS in automatic
      mode and immediately use the selected configured location without a
      permission prompt or unavailable-location control.
- [ ] A legacy Ubuntu kiosk with no `userAgentData` and a mobile-looking user
      agent is still treated as stationary through its x86 Linux platform.
- [ ] **Automatic for this device** uses live GPS on a phone, then the current
      user's linked person, without changing the shared card configuration.
- [ ] On a supported mobile client, when automatic positioning has neither GPS
      nor a linked person, the card
      asks before using the configured location and offers a separate GPS retry.
- [ ] Confirming the configured fallback is remembered only in that browser;
      reloading the kiosk does not change the same card on a phone.
- [ ] Denied, timed-out, unavailable, and missing-person states show distinct
      messages instead of an empty card.
- [ ] Each signed-in family member sees their own city, town, or village in
      live-GPS mode when their Home Assistant user is linked to a `person`
      entity with a Companion App Geocoded Location sensor.
- [ ] Live GPS never displays another family member's place name; when the
      browser and person coordinates differ by more than 5 km, it falls back
      to the calculated district or oblast.
- [ ] A newly opened live-GPS card with no alert does not show a 1970 date or
      an impossible safe duration.
- [ ] Automatic, live-GPS, and person/tracker cards inside the configured
      district show the same alert/safe start time and duration as the fixed
      location card.
- [ ] A dynamic position in another district does not inherit the configured
      location's safe duration.
- [ ] After a dynamic position visits another district, its alert/safe time
      continues updating on provider refreshes and survives a Home Assistant
      restart.
- [ ] Returning to a previously observed district restores that district's own
      duration instead of starting over or showing another area's value.
- [ ] A newly observed safe district starts its timer at first observation;
      no earlier all-clear time is fabricated.
- [ ] Person/tracker mode has no separate place-name selector.
- [ ] The displayed district or oblast follows the selected tracker coordinates
      and cannot show a manually selected unrelated place.
- [ ] Denied device-location permission shows an explicit message and retry
      button instead of falling back to configured coordinates.
- [ ] Missing tracker coordinates show an explicit unavailable message.
- [ ] North-up mode keeps north at the top on desktop and mobile.
- [ ] On a supported iOS/iPadOS or Android client, device-compass mode shows
      an **Enable compass** button, asks for permission when tapped, and
      rotates the spatial radar layer without interrupting the sweep.
- [ ] Desktop Chrome, macOS browsers, and an Ubuntu kiosk remain north-up and
      do not display a compass button, even when the shared card explicitly
      requests device-compass mode.
- [ ] A touch-enabled Ubuntu Chromium kiosk with a mobile-looking user-agent
      is still identified as desktop through `userAgentData` and does not show
      **Compass unavailable**.
- [ ] If a browser nevertheless passes capability detection but compass
      startup fails, the card silently returns to north-up and displays no
      unavailable-compass chip.
- [ ] After compass permission is granted, reloading the dashboard restores
      compass tracking without showing the enable button again. If WebKit
      requires a new gesture, the button remains available.
- [ ] The compass control remains visible as `Очікування компаса` until the
      first valid heading is received.
- [ ] If no heading arrives within three seconds, the waiting state returns to
      an enabled compass button instead of silently remaining north-up.
- [ ] Returning to the Companion App after locking the phone or switching apps
      restarts compass listeners and restores rotation after a valid reading.
- [ ] Device-compass mode also works while **Demo: alert** is selected.
- [ ] Automatic orientation offers the compass on a supported mobile device
      with live positioning and remains north-up on a fixed kiosk.
- [ ] Denying or lacking compass access does not affect integration entities or
      the north-referenced calculations.
- [ ] With no displayed targets, the card does not reserve empty list space.
- [ ] Card corners and content remain aligned on narrow dashboard columns.
- [ ] **Signal colors** uses distinct green, amber, and red gradients.
- [ ] **Follow Home Assistant theme** follows light/dark theme colors and keeps
      the bundled safe/alert image as the status marker.
- [ ] The graphical editor uses the bundled standard shield artwork and offers
      no optional branded artwork.
- [ ] Updating a card that previously used a removed artwork option falls back
      to standard shields without a configuration error.
- [ ] Public manual and HACS archives contain no removed decorative images.
- [ ] After unlocking a phone or restarting Home Assistant, the last
      successful card state appears immediately with a small `updating…`
      marker and is replaced by fresh data when the websocket responds.
- [ ] A cached card never shows `[object Object]` or a bare numeric error while
      Home Assistant is reconnecting.
- [ ] Cached snapshots remain isolated by integration entry, position mode,
      and selected person/tracker.
- [ ] Snapshots older than 30 minutes are not restored.
- [ ] A light Home Assistant theme uses dark target artwork without glow in the
      lower list while radar markers remain white.
- [ ] A dark Home Assistant theme keeps the original white target artwork.
- [ ] Dark-theme chips have visible boundaries and vertically centred text on
      desktop, mobile, and a narrow kiosk column.
- [ ] Returning to **Live data** restores the real integration snapshot.
- [ ] No YAML, entity selection, or `/config/www` copy is required.
- [ ] The source link and unofficial-warning notice remain visible.

## Live data

- [ ] Local alert state agrees with official warning channels.
- [ ] The local `alert_level` and `alert_reasons` attributes agree with the
      current NEPTUN response.
- [ ] Target distances and compass positions are plausible.
- [ ] Targets with unknown heading are not labelled as approaching.
- [ ] Data returns after a temporary network interruption.
- [ ] A provider/network failure shows **Data unavailable**, never a false safe
      state.
- [ ] Targets marked `stale` or resolved by the provider are not displayed or
      included in active target totals.
- [ ] Changing the card location immediately replaces the previous snapshot.
- [ ] Narrow dashboard columns do not clip distance values or the attribution.

## Reporting a problem

Include:

- Home Assistant version and installation type.
- Air Threat Monitor version and installation method.
- The exact steps that reproduce the issue.
- Sanitized integration diagnostics.
- Relevant Home Assistant logs.

Remove exact coordinates, addresses, tokens, and unrelated personal data before
posting.
